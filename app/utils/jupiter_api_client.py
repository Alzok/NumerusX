import asyncio
import base64
import json
from typing import Any, Dict, List, Optional, Callable

import aiohttp
import solders
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import to_bytes_versioned

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Processed

from tenacity import AsyncRetrying, wait_exponential, stop_after_attempt, retry_if_exception_type, RetryError

# Import Config using alias to avoid naming conflicts with solders.rpc.config
from app.config import get_config as AppConfig

import logging

# Import custom exceptions
from app.utils.exceptions import (
    JupiterAPIError, SolanaTransactionError, TransactionExpiredError, 
    TransactionBroadcastError, TransactionConfirmationError
)

# Logger for this module
logger = logging.getLogger(__name__)


class JupiterApiClient:
    """
    Client for interacting with the Jupiter API v6 using direct HTTP REST calls.
    Handles API calls for quotes, swaps, limit orders, DCA, prices, and token info.
    Includes error handling and retry mechanisms.
    """

    def __init__(self, private_key_bs58: str, rpc_url: str, config: AppConfig):
        """
        Initializes the JupiterApiClient.

        Args:
            private_key_bs58: The trader's wallet private key in base58 string format.
            rpc_url: The Solana RPC URL.
            config: The application's Config object.
        """
        logger.info("JupiterApiClient initializing with HTTP REST implementation")
        
        self.config = config
        try:
            self.keypair = Keypair.from_base58_string(private_key_bs58)
        except Exception as e:
            logger.error(f"Failed to initialize Keypair from private key: {e}", exc_info=True)
            raise ValueError(f"Invalid private_key_bs58: {e}") from e

        self.async_client = AsyncClient(rpc_url)
        
        # Jupiter API v6 URLs
        self.base_url = config.jupiter.lite_api_hostname
        self.quote_url = f"{self.base_url}/v6/quote"
        self.swap_url = f"{self.base_url}/v6/swap"
        self.price_url = f"{self.base_url}/price/v2"
        
        # HTTP session
        self.http_session = None
        self.http_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'NumerusX-Jupiter-Client/1.0'
        }
        
        logger.info(f"Jupiter API client initialized with base URL: {self.base_url}")

    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.http_session is None or self.http_session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.http_session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.http_headers
            )
        return self.http_session

    async def _make_http_request(
        self, 
        method: str, 
        url: str, 
        params: Optional[Dict] = None, 
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling
        """
        session = await self._get_http_session()
        
        # Define retry configuration
        max_retries = getattr(self.config.jupiter, 'max_retries', 3)
        retryable_exceptions = (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            aiohttp.ServerTimeoutError
        )

        retry_config = {
            'wait': wait_exponential(multiplier=1, min=1, max=10),
            'stop': stop_after_attempt(max_retries),
            'retry': retry_if_exception_type(retryable_exceptions),
            'reraise': True,
        }

        try:
            async for attempt in AsyncRetrying(**retry_config):
                with attempt:
                    logger.debug(f"Making {method} request to {url}, attempt {attempt.retry_state.attempt_number}")
                    
                    async with session.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data
                    ) as response:
                        
                        if response.status >= 400:
                            error_text = await response.text()
                            logger.error(f"HTTP {response.status} error: {error_text}")
                            
                            if response.status >= 500:
                                # Server error - retryable
                                raise aiohttp.ClientError(f"Server error {response.status}: {error_text}")
                            else:
                                # Client error - not retryable
                                raise JupiterAPIError(f"HTTP {response.status}: {error_text}")
                        
                        try:
                            result = await response.json()
                            logger.debug(f"Successful response from {url}")
                            return result
                        except json.JSONDecodeError as e:
                            raise JupiterAPIError(f"Invalid JSON response: {e}")
                            
        except RetryError as e:
            error_message = f"HTTP request to {url} failed after {max_retries} retries: {e.last_attempt.exception()}"
            logger.error(error_message, exc_info=True)
            raise JupiterAPIError(message=error_message, original_exception=e.last_attempt.exception()) from e
        except Exception as e:
            error_message = f"HTTP request to {url} failed: {e}"
            logger.error(error_message, exc_info=True)
            raise JupiterAPIError(message=error_message, original_exception=e) from e

    # --- Core Swap Methods ---
    async def get_quote(
        self, 
        input_mint_str: str, 
        output_mint_str: str, 
        amount_lamports: int, 
        slippage_bps: Optional[int] = None,
        swap_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetches a swap quote from Jupiter API v6.
        
        Args:
            input_mint_str: Input token mint address
            output_mint_str: Output token mint address  
            amount_lamports: Amount in lamports
            slippage_bps: Slippage in basis points (default from config)
            swap_mode: Swap mode (default from config)
            
        Returns:
            Quote response from Jupiter API
        """
        logger.info(f"Getting quote: {amount_lamports} {input_mint_str} -> {output_mint_str}")
        
        params = {
            "inputMint": input_mint_str,
            "outputMint": output_mint_str,
            "amount": str(amount_lamports),
            "slippageBps": slippage_bps or getattr(self.config.jupiter, 'default_slippage_bps', 50),
            "onlyDirectRoutes": getattr(self.config.jupiter, 'only_direct_routes', False),
            "swapMode": swap_mode or getattr(self.config.jupiter, 'swap_mode', 'ExactIn')
        }
        
        # Add API key if available for Pro tier
        if hasattr(self.config.jupiter, 'api_key') and self.config.jupiter.api_key:
            params["apiKey"] = self.config.jupiter.api_key
        
        result = await self._make_http_request("GET", self.quote_url, params=params)
        
        logger.info(f"Quote successful: {result.get('outAmount', 'N/A')} output tokens")
        return result

    async def get_swap_transaction_data(self, quote_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get swap transaction data from Jupiter API v6.
        
        Args:
            quote_response: Response from get_quote()
            
        Returns:
            Swap transaction data including serialized transaction
        """
        logger.info("Getting swap transaction data")
        
        swap_request = {
            "quoteResponse": quote_response,
            "userPublicKey": str(self.keypair.pubkey()),
            "wrapAndUnwrapSol": getattr(self.config.jupiter, 'wrap_and_unwrap_sol', True),
            "dynamicComputeUnitLimit": getattr(self.config.jupiter, 'dynamic_compute_unit_limit', True),
        }
        
        # Add compute unit price if configured
        if hasattr(self.config.jupiter, 'compute_unit_price_micro_lamports'):
            if self.config.jupiter.compute_unit_price_micro_lamports:
                swap_request["computeUnitPriceMicroLamports"] = self.config.jupiter.compute_unit_price_micro_lamports
        
        # Add priority fee level if configured
        if hasattr(self.config.jupiter, 'priority_fee_level'):
            swap_request["priorityFeeLevel"] = self.config.jupiter.priority_fee_level
        
        result = await self._make_http_request("POST", self.swap_url, json_data=swap_request)
        
        logger.info("Swap transaction data retrieved successfully")
        return result

    async def sign_and_send_transaction(self, serialized_transaction_b64: str, last_valid_block_height: int) -> str:
        """
        Sign and send transaction to Solana network.
        
        Args:
            serialized_transaction_b64: Base64 encoded transaction
            last_valid_block_height: Last valid block height
            
        Returns:
            Transaction signature
        """
        logger.info("Signing and sending transaction")
        
        try:
            # Decode transaction
            transaction_bytes = base64.b64decode(serialized_transaction_b64)
            transaction = VersionedTransaction.from_bytes(transaction_bytes)
            
            # Sign transaction
            message_bytes = to_bytes_versioned(transaction.message)
            signature = self.keypair.sign_message(message_bytes)
            signed_transaction = VersionedTransaction.populate(transaction.message, [signature])
            
            # Send transaction
            opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
            result = await self.async_client.send_raw_transaction(
                txn=bytes(signed_transaction), 
                opts=opts
            )
            
            if result.value:
                signature_str = str(result.value)
                logger.info(f"Transaction sent successfully: {signature_str}")
                return signature_str
            else:
                raise SolanaTransactionError("Failed to send transaction - no signature returned")
                
        except Exception as e:
            logger.error(f"Failed to sign and send transaction: {e}", exc_info=True)
            raise SolanaTransactionError(f"Transaction failed: {e}") from e

    async def execute_swap(
        self, 
        input_mint_str: str, 
        output_mint_str: str, 
        amount_lamports: int, 
        slippage_bps: Optional[int] = None
    ) -> str:
        """
        Execute a complete swap: quote -> transaction -> sign -> send.
        
        Args:
            input_mint_str: Input token mint address
            output_mint_str: Output token mint address
            amount_lamports: Amount to swap in lamports
            slippage_bps: Slippage tolerance in basis points
            
        Returns:
            Transaction signature
        """
        logger.info(f"Executing swap: {amount_lamports} {input_mint_str} -> {output_mint_str}")
        
        try:
            # Step 1: Get quote
            quote = await self.get_quote(input_mint_str, output_mint_str, amount_lamports, slippage_bps)
            
            # Step 2: Get swap transaction
            swap_data = await self.get_swap_transaction_data(quote)
            
            # Step 3: Sign and send
            signature = await self.sign_and_send_transaction(
                swap_data['swapTransaction'], 
                swap_data.get('lastValidBlockHeight', 0)
            )
            
            logger.info(f"Swap executed successfully: {signature}")
            return signature
            
        except Exception as e:
            logger.error(f"Swap execution failed: {e}", exc_info=True)
            raise JupiterAPIError(f"Swap execution failed: {e}") from e

    async def get_prices(self, token_ids_list: List[str], vs_token_str: Optional[str] = "USDC") -> Dict[str, Any]:
        """
        Get token prices from Jupiter API.
        
        Args:
            token_ids_list: List of token mint addresses
            vs_token_str: Base token to price against
            
        Returns:
            Price data from Jupiter API
        """
        logger.debug(f"Getting prices for {len(token_ids_list)} tokens vs {vs_token_str}")
        
        params = {
            "ids": ",".join(token_ids_list),
        }
        if vs_token_str:
            params["vsToken"] = vs_token_str
        
        result = await self._make_http_request("GET", self.price_url, params=params)
        
        logger.debug("Price data retrieved successfully")
        return result

    async def get_token_info_list(
        self, 
        mint_address_list: Optional[List[str]] = None, 
        tag_list: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get token information from Jupiter API.
        
        Args:
            mint_address_list: List of mint addresses to get info for
            tag_list: List of tags to filter by
            
        Returns:
            Token information from Jupiter API
        """
        logger.debug("Getting token information")
        
        params = {}
        if mint_address_list:
            params["mints"] = ",".join(mint_address_list)
        if tag_list:
            params["tags"] = ",".join(tag_list)
        
        token_list_url = f"{self.base_url}/tokens"
        result = await self._make_http_request("GET", token_list_url, params=params)
        
        logger.debug("Token information retrieved successfully")
        return result

    # --- Limit Orders (Advanced Features) ---
    async def create_trigger_order(self, params_dict: Dict) -> Any:
        """
        Create limit/trigger order (requires Jupiter Pro API).
        """
        logger.warning("Limit orders require Jupiter Pro API - feature not fully implemented")
        raise JupiterAPIError("Limit orders not implemented - requires Jupiter Pro subscription")

    async def execute_trigger_order(self, order_id: str) -> Any:
        """
        Execute trigger order (requires Jupiter Pro API).
        """
        logger.warning("Limit orders require Jupiter Pro API - feature not fully implemented")
        raise JupiterAPIError("Limit orders not implemented - requires Jupiter Pro subscription")

    async def cancel_trigger_order(self, order_id: str) -> Any:
        """
        Cancel trigger order (requires Jupiter Pro API).
        """
        logger.warning("Limit orders require Jupiter Pro API - feature not fully implemented")
        raise JupiterAPIError("Limit orders not implemented - requires Jupiter Pro subscription")

    async def get_trigger_orders(
        self, 
        owner_address_str: Optional[str] = None, 
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get trigger orders (requires Jupiter Pro API).
        """
        logger.warning("Limit orders require Jupiter Pro API - feature not fully implemented")
        raise JupiterAPIError("Limit orders not implemented - requires Jupiter Pro subscription")

    # --- DCA (Dollar Cost Averaging) ---
    async def create_dca_plan(self, params_dict: Dict) -> Any:
        """
        Create DCA plan (requires Jupiter Pro API).
        """
        logger.warning("DCA requires Jupiter Pro API - feature not fully implemented")
        raise JupiterAPIError("DCA not implemented - requires Jupiter Pro subscription")

    async def get_dca_orders(self, owner_address_str: Optional[str] = None) -> Any:
        """
        Get DCA orders (requires Jupiter Pro API).
        """
        logger.warning("DCA requires Jupiter Pro API - feature not fully implemented")
        raise JupiterAPIError("DCA not implemented - requires Jupiter Pro subscription")

    async def close_dca_order(self, dca_order_id: str) -> Any:
        """
        Close DCA order (requires Jupiter Pro API).
        """
        logger.warning("DCA requires Jupiter Pro API - feature not fully implemented")
        raise JupiterAPIError("DCA not implemented - requires Jupiter Pro subscription")

    async def close_async_client(self):
        """
        Close HTTP session and Solana client.
        """
        logger.info("Closing Jupiter API client")
        
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
            
        if self.async_client:
            await self.async_client.close()
            
        logger.info("Jupiter API client closed successfully")

    # --- Utility Methods ---
    async def health_check(self) -> bool:
        """
        Check if Jupiter API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Test with a simple quote request
            await self.get_quote(
                "So11111111111111111111111111111111111111112",  # SOL
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                1000000  # 0.001 SOL
            )
            logger.info("Jupiter API health check passed")
            return True
        except Exception as e:
            logger.error(f"Jupiter API health check failed: {e}")
            return False

    def get_config(self):
        """Get config reference for compatibility"""
        return self.config