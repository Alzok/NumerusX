import asyncio
import base64
from typing import Any, Dict, List, Optional, Callable

import solders
from solders.keypair import Keypair
from solders.pubkey import Pubkey
# # from solders.rpc.errors import TransactionExpiredBlockheightExceededError  # Import not available in current solders version  # This import might not exist
from solders.transaction import VersionedTransaction
# from solders.rpc.config import TxOpts  # Temporarily commented out due to import conflict

from solana.rpc.async_api import AsyncClient
# Import Config using alias to avoid naming conflicts with solders.rpc.config
from app.config import Config as AppConfig

# Assuming jupiter_python_sdk is installed and its structure is as expected.
# These imports might need adjustment based on the actual SDK structure.
# from jupiter_python_sdk.jupiter import Jupiter  # SDK not available - using stub below
# from jupiter_python_sdk.trigger import Trigger, OrderInfo # Example if these are separate
# from jupiter_python_sdk.dca import ... # Example for DCA

# Replace with temporary stub:
# from jupiter_python_sdk.jupiter import Jupiter  # Temporarily commented - SDK not available
# from jupiter_python_sdk.trigger import Trigger, OrderInfo # Example if these are separate  
# from jupiter_python_sdk.dca import ... # Example for DCA

# Temporary Jupiter stub class
class Jupiter:
    def __init__(self, *args, **kwargs):
        logger.warning("Using Jupiter stub - real SDK not available")
    
    async def quote(self, *args, **kwargs):
        raise JupiterAPIError("Jupiter SDK not available - stub implementation")
    
    async def swap(self, *args, **kwargs):
        raise JupiterAPIError("Jupiter SDK not available - stub implementation")

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, AsyncRetrying, RetryError

import logging

# Import custom exceptions
from .exceptions import (
    JupiterAPIError, SolanaTransactionError, TransactionExpiredError, 
    TransactionBroadcastError, TransactionConfirmationError
)

# Logger for this module
logger = logging.getLogger(__name__)


class JupiterApiClient:
    """
    Client for interacting with the Jupiter API using the jupiter-python-sdk.
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
        # Temporarily use stub implementation since jupiter_python_sdk not installed
        logger.warning("JupiterApiClient using stub implementation - jupiter_python_sdk not installed")
        
        self.config = config
        try:
            self.keypair = Keypair.from_base58_string(private_key_bs58)
        except Exception as e:
            logger.error(f"Failed to initialize Keypair from private key: {e}", exc_info=True)
            # Depending on application design, might want to raise this to prevent startup
            # if a valid keypair is essential for this client's operation.
            raise ValueError(f"Invalid private_key_bs58: {e}") from e

        self.async_client = AsyncClient(rpc_url)
        
        # Temporary stub since jupiter_python_sdk is not installed
        self.jupiter = None
        logger.warning("Jupiter SDK not available - using stub implementation")
        return  # Exit early to avoid Jupiter initialization
        
        # Construct base URLs for Jupiter SDK modules if it expects them this way.
        # The SDK documentation should clarify how base URLs for different API groups are handled.
        # If Jupiter() takes a single base_api_url and constructs paths internally, this will be simpler.
        # Assuming for now it needs specific base URLs for different parts of the API.
        
        # Example: Constructing URLs based on Config for different Jupiter API services
        # These might be passed to Jupiter() constructor or specific module constructors within the SDK.
        # The exact parameter names (quote_api_url, swap_api_url, etc.) depend on the SDK's Jupiter class.
        
        # Default to lite API hostname
        jup_hostname = self.config.JUPITER_LITE_API_HOSTNAME
        # Potentially switch to PRO_API_HOSTNAME if an API key is present and config allows
        if self.config.JUPITER_API_KEY and self.config.JUPITER_PRO_API_HOSTNAME:
             # This logic might be more complex: e.g., a separate config flag to use Pro API
            logger.info("Jupiter Pro API Key found, considering Pro Hostname. Ensure config directs usage.")
            # For now, let's assume a direct switch if a key is present for Pro hostname,
            # but typically an explicit setting to USE_PRO_API would be better.
            # jup_hostname = self.config.JUPITER_PRO_API_HOSTNAME # Uncomment if Pro API is to be used

        # try:
        #     self.jupiter = Jupiter(
        #         async_client=self.async_client,
        #         keypair=self.keypair, # The SDK might use this for signing some requests or for specific API endpoints
        #         # The SDK might abstract away the full URLs if it knows the paths for quote, swap, etc.
        #         # Or it might require the full base URLs for each service.
        #         # Referencing the SDK's expected parameters:
        #         quote_api_url=f"{jup_hostname.rstrip('/')}{self.config.JUPITER_SWAP_API_PATH.rstrip('/')}/quote",
        #         swap_api_url=f"{jup_hostname.rstrip('/')}{self.config.JUPITER_SWAP_API_PATH.rstrip('/')}/swap",
        #         price_api_url=f"{jup_hostname.rstrip('/')}{self.config.JUPITER_PRICE_API_PATH.rstrip('/')}", # Note: Path is /price, not /price/v2/price
        #         token_api_url=f"{jup_hostname.rstrip('/')}{self.config.JUPITER_TOKEN_API_PATH.rstrip('/')}",
        #         trigger_api_url=f"{jup_hostname.rstrip('/')}{self.config.JUPITER_TRIGGER_API_PATH.rstrip('/')}",
        #         recurring_api_url=f"{jup_hostname.rstrip('/')}{self.config.JUPITER_RECURRING_API_PATH.rstrip('/')}",
        #         # The SDK might also take an api_key parameter if using the pro version
        #         api_key=self.config.JUPITER_API_KEY if jup_hostname == self.config.JUPITER_PRO_API_HOSTNAME else None
        #     )
        #     # If DCA or Trigger modules are separate in the SDK and need their own init:
        #     # self.jupiter_trigger = JupiterTrigger(...)
        #     # self.jupiter_dca = JupiterDCA(...)
        #     logger.info("Jupiter SDK client initialized.")
        # except Exception as e:
        #     logger.error(f"Failed to initialize Jupiter SDK: {e}", exc_info=True)
        #     raise RuntimeError(f"Jupiter SDK initialization failed: {e}") from e
        
        # Temporary stub since jupiter_python_sdk is not installed
        self.jupiter = None
        logger.warning("Jupiter SDK not available - using stub implementation")

        self.http_headers = {'Accept': 'application/json'} # Default headers, SDK might handle this.

    async def _call_sdk_method(self, sdk_method_callable: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Wrapper for calling Jupiter SDK methods with tenacity retry logic.
        """
        # Define retry parameters from config or use defaults
        max_retries = self.config.JUPITER_MAX_RETRIES
        # Define specific exceptions from the SDK or Solana client that are worth retrying
        # This is a generic list, refine with actual SDK exceptions
        retryable_exceptions = (
            asyncio.TimeoutError, # General timeout
            # Comment out this line:
            # solders.rpc.errors.TransactionExpiredBlockheightExceededError, # Specific to Solana transactions
            # Replace with:
            # Exception,  # Generic exception handling since specific one not available
            # Add other specific exceptions from the SDK or Solana client that are transient
            # e.g., ConnectionError, HTTP 502/503/504 if the SDK surfaces them directly
        )

        retry_config = {
            'wait': wait_exponential(multiplier=1, min=1, max=10),
            'stop': stop_after_attempt(max_retries),
            'retry': retry_if_exception_type(retryable_exceptions),
            'reraise': True, # Reraise the exception if all retries fail
        }

        try:
            async for attempt in AsyncRetrying(**retry_config):
                with attempt:
                    logger.debug(f"Calling SDK method {sdk_method_callable.__name__}, attempt {attempt.retry_state.attempt_number}")
                    result = await sdk_method_callable(*args, **kwargs)
                    # Assuming successful SDK calls return the direct data object
                    # The design choice here is whether _call_sdk_method returns a dict or raises exceptions.
                    # Given the move to custom exceptions, it should raise on failure.
                    return result # Return direct result on success
        except RetryError as e: # This catches the exception after all retries fail
            error_message = f"SDK call {sdk_method_callable.__name__} failed after {max_retries} retries: {e.last_attempt.exception()}"
            logger.error(error_message, exc_info=True)
            # Raise a custom API error, wrapping the original exception from the last attempt
            raise JupiterAPIError(message=error_message, original_exception=e.last_attempt.exception()) from e
        except Exception as e: # Catch any other non-retryable exceptions from the SDK call itself
            error_message = f"SDK call {sdk_method_callable.__name__} failed: {e}"
            logger.error(error_message, exc_info=True)
            # Raise a custom API error, wrapping the original exception
            raise JupiterAPIError(message=error_message, original_exception=e) from e

    # --- Core Swap Methods ---
    async def get_quote(
        self, 
        input_mint_str: str, 
        output_mint_str: str, 
        amount_lamports: int, 
        slippage_bps: Optional[int] = None, # Will use config default if None
        swap_mode: Optional[str] = None # Will use config default if None
    ) -> Dict[str, Any]:
        """
        Fetches a swap quote from Jupiter API.
        """
        input_mint = Pubkey.from_string(input_mint_str)
        output_mint = Pubkey.from_string(output_mint_str)
        
        quote_params = {
            "input_mint": input_mint,
            "output_mint": output_mint,
            "amount": amount_lamports,
            "slippage_bps": slippage_bps if slippage_bps is not None else self.config.JUPITER_DEFAULT_SLIPPAGE_BPS,
            "only_direct_routes": self.config.JUPITER_ONLY_DIRECT_ROUTES,
            "swap_mode": swap_mode if swap_mode else self.config.JUPITER_SWAP_MODE,
            "as_legacy_transaction": False, # Prefer VersionedTransactions
            "dynamic_compute_unit_limit": self.config.JUPITER_DYNAMIC_COMPUTE_UNIT_LIMIT,
            # Add compute_unit_price_micro_lamports or priority_fee_level based on config
        }
        if self.config.JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS:
            quote_params["compute_unit_price_micro_lamports"] = int(self.config.JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS)
        elif self.config.JUPITER_PRIORITY_FEE_LEVEL:
             # The SDK should map this string to a specific lamport value or handle it directly
            quote_params["priority_fee_level"] = self.config.JUPITER_PRIORITY_FEE_LEVEL
        
        # The SDK's quote method might have slightly different param names or structure
        # return await self._call_sdk_method(self.jupiter.quote, **quote_params)
        # Now _call_sdk_method returns data directly or raises JupiterAPIError
        try:
            return await self._call_sdk_method(self.jupiter.quote, **quote_params)
        except JupiterAPIError as e:
            # Specific handling or re-raising if needed, for now, let it propagate
            # Or, if this layer must return a dict:
            # return {"success": False, "data": None, "error": str(e), "details": e}
            raise # Propagate the custom exception

    async def get_swap_transaction_data(self, quote_response: Any) -> Dict[str, Any]:
        """
        Gets the serialized swap transaction from Jupiter API using a quote response.
        The SDK's swap() method typically returns an object containing swap_transaction (base64) 
        and last_valid_block_height.
        This method will return a standardized dictionary or raise JupiterAPIError.
        """
        swap_params = {
            "quote_response": quote_response,
            "payer_public_key": self.keypair.public_key,
            "wrap_and_unwrap_sol": self.config.JUPITER_WRAP_AND_UNWRAP_SOL,
            "as_legacy_transaction": False, # Prefer VersionedTransactions
            # Add compute_unit_price_micro_lamports or priority_fee_level based on config, similar to get_quote
        }
        if self.config.JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS:
            swap_params["compute_unit_price_micro_lamports"] = int(self.config.JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS)
        elif self.config.JUPITER_PRIORITY_FEE_LEVEL:
            swap_params["priority_fee_level"] = self.config.JUPITER_PRIORITY_FEE_LEVEL

        # The SDK's swap method might have different param names or structure
        # It's crucial to pass the quote_response object obtained from the SDK's quote() method
        # result = await self._call_sdk_method(self.jupiter.swap, **swap_params)
        try:
            sdk_response_data = await self._call_sdk_method(self.jupiter.swap, **swap_params)
        except JupiterAPIError as e:
            # return {"success": False, "data": None, "error": str(e), "details": e}
            raise
        
        # Standardize the output structure if the SDK returns something slightly different
        # This part assumes sdk_response_data is the actual data object if successful
        if isinstance(sdk_response_data, dict):
            standardized_data = {
                "serialized_transaction_b64": sdk_response_data.get("swap_transaction") or sdk_response_data.get("transaction"),
                "last_valid_block_height": sdk_response_data.get("last_valid_block_height")
            }
            if not standardized_data["serialized_transaction_b64"] or standardized_data["last_valid_block_height"] is None:
                logger.warning(f"Jupiter swap SDK response missing expected fields: {sdk_response_data}")
                # Raise an error instead of returning a dict with success=False
                raise JupiterAPIError(message="Swap SDK response missing key fields after successful call", original_exception=ValueError(f"Missing fields in {sdk_response_data}"))
            return standardized_data # Return the standardized dict directly
        else: # If data is not a dict, it's unexpected for a successful swap call
             logger.warning(f"Jupiter swap SDK response was successful but data is not a dict: {sdk_response_data}")
             raise JupiterAPIError(message="Unexpected successful swap SDK response format", original_exception=TypeError(f"Expected dict, got {type(sdk_response_data)}"))

    async def sign_and_send_transaction(self, serialized_transaction_b64: str, last_valid_block_height: int) -> str:
        """
        Signs and sends a serialized versioned transaction to the Solana network.
        Returns the transaction signature on success, or raises a SolanaTransactionError subtype on failure.
        """
        try:
            tx_bytes = base64.b64decode(serialized_transaction_b64)
            tx = VersionedTransaction.from_bytes(tx_bytes)
            
            # Sign the transaction
            # For VersionedTransaction, the message is already serialized in a specific way.
            # The keypair signs the message bytes.
            signature = self.keypair.sign_message(tx.message.serialize())
            tx.add_signature(self.keypair.public_key, signature)
            
            serialized_signed_tx = tx.serialize()

            # Loop for retrying on blockhash expiration
            max_blockhash_retries = self.config.JUPITER_MAX_RETRIES # Reuse general retry config or define specific one
            
            for attempt_num in range(max_blockhash_retries):
                try:
                    # opts = TxOpts(
                    #     skip_preflight=True, # As recommended by Jupiter for best execution
                    #     preflight_commitment="confirmed", 
                    #     last_valid_block_height=last_valid_block_height
                    # )
                    # Send the transaction without TxOpts for now
                    resp = await self.async_client.send_transaction(serialized_signed_tx)
                    
                    # Confirm the transaction
                    # The SDK or Solana client library should provide a robust confirmation method.
                    # Using confirm_transaction which waits for confirmation.
                    await self.async_client.confirm_transaction(
                        signature=resp.value, # Assuming resp.value is the TxnSignature
                        commitment="confirmed",
                        last_valid_block_height=last_valid_block_height,
                        sleep_secs=5 # Polling interval
                    )
                    logger.info(f"Transaction confirmed: {resp.value}")
                    return str(resp.value) # Return signature string on success

                except Exception as e:  # Generic exception handling
                    logger.warning(f"Transaction {str(tx.signatures[0]) if tx.signatures else 'N/A'} expired (attempt {attempt_num + 1}/{max_blockhash_retries}): {e}. Refreshing blockhash.")
                    if attempt_num + 1 >= max_blockhash_retries:
                        # Raise custom error if max retries reached for this specific error
                        raise TransactionExpiredError(message="Transaction expired after multiple retries due to blockhash.", original_exception=e) from e
                    
                    # Logic to re-fetch from Jupiter is complex and should be handled by the caller (e.g. TradingEngine)
                    # Thus, we raise TransactionExpiredError immediately to signal this to the caller.
                    raise TransactionExpiredError(
                        message="Transaction expired, re-quote and re-swap needed to get new transaction with current blockhash.", 
                        original_exception=e
                    ) from e

                except solders.rpc.errors.SendTransactionPreflightFailureError as e:
                    logger.error(f"Transaction preflight simulation failed: {e}", exc_info=True)
                    # Example: extract simulation logs if available in e
                    # sim_logs = e.logs if hasattr(e, 'logs') else None
                    raise TransactionSimulationError(message=f"Preflight simulation failed: {e}", original_exception=e, signature=str(tx.signatures[0]) if tx.signatures else None) from e
                
                except asyncio.TimeoutError as e: # Specific timeout for confirm_transaction
                    logger.error(f"Transaction confirmation timed out for signature {str(resp.value if 'resp' in locals() else 'N/A')}", exc_info=True)
                    raise TransactionConfirmationError(message="Transaction confirmation timed out.", signature=str(resp.value if 'resp' in locals() else 'N/A'), original_exception=e) from e

                except Exception as e_inner: # Catch other errors during send/confirm
                    logger.error(f"Error sending/confirming transaction: {e_inner}", exc_info=True)
                    # Use a generic broadcast or confirmation error if unsure
                    # This could be TransactionBroadcastError or TransactionConfirmationError depending on when it happened.
                    # For simplicity, let's use a general SolanaTransactionError if it's not clearly one of the above.
                    raise SolanaTransactionError(message=f"Send/confirm failed: {e_inner}", signature=str(tx.signatures[0]) if tx.signatures else None, original_exception=e_inner) from e_inner

            # This part should ideally not be reached if exceptions are raised correctly in the loop.
            # If loop finishes, it implies retries for TransactionExpiredError were exhausted without re-raising correctly.
            # This indicates a logic flaw if this line is ever hit.
            raise SolanaTransactionError(message="Max blockhash retries exceeded logic error.")

        except ValueError as e: # E.g. from Keypair.from_base58_string or Pubkey.from_string if they were here
            logger.error(f"ValueError in sign_and_send_transaction: {e}", exc_info=True)
            raise SolanaTransactionError(message=f"Input validation error: {e}", original_exception=e) from e
        except Exception as e: # Catch errors from b64decode, VersionedTransaction.from_bytes, or signing
            logger.error(f"Error in sign_and_send_transaction before sending: {e}", exc_info=True)
            # This is likely a local setup or data issue, not a network/RPC issue.
            raise SolanaTransactionError(message=f"Local error preparing transaction: {e}", original_exception=e) from e

    # --- Other Jupiter API Methods ---

    async def get_prices(self, token_ids_list: List[str], vs_token_str: Optional[str] = "USDC") -> Dict[str, Any]:
        """
        Fetches token prices from Jupiter API.
        Jupiter's /price/v2 endpoint (or SDK equivalent) is expected.
        Params for SDK: ids (List[Pubkey]), vs_token (Optional[Pubkey]), show_extra_info (Optional[bool])
        """
        try:
            ids_pubkeys = [Pubkey.from_string(token_id) for token_id in token_ids_list]
            vs_token_pubkey = Pubkey.from_string(vs_token_str) if vs_token_str else None
            
            price_params = {"ids": ids_pubkeys}
            if vs_token_pubkey:
                price_params["vs_token"] = vs_token_pubkey
            # price_params["show_extra_info"] = True # Or some other default

            return await self._call_sdk_method(self.jupiter.get_price, **price_params)
        except ValueError as e: # Catch errors like invalid Pubkey strings
            logger.error(f"Error preparing params for get_prices: {e}", exc_info=True)
            raise JupiterAPIError(message=f"Invalid parameters for get_prices: {e}", original_exception=e) from e
        # JupiterAPIError from _call_sdk_method will propagate if SDK call fails

    async def get_token_info_list(
        self, 
        mint_address_list: Optional[List[str]] = None, 
        tag_list: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetches token information from Jupiter API (via /tokens/v1 or SDK equivalent).
        The SDK should handle filtering by mint_address or tag.
        SDK params might be: mint_addresses (Optional[List[Pubkey]]), tags (Optional[List[str]])
        """
        sdk_params = {}
        if mint_address_list:
            try:
                sdk_params["mint_addresses"] = [Pubkey.from_string(m) for m in mint_address_list]
            except ValueError as e:
                logger.error(f"Invalid mint address in get_token_info_list: {e}")
                raise JupiterAPIError(message=f"Invalid mint address: {e}", original_exception=e) from e
        if tag_list:
            sdk_params["tags"] = tag_list
        
        # Ensure self.jupiter.get_tokens exists and is the correct method name
        return await self._call_sdk_method(self.jupiter.get_tokens, **sdk_params)

    # --- Trigger Orders (Limit Orders) ---

    async def create_trigger_order(self, params_dict: Dict) -> Any:
        """
        Creates a trigger (limit) order using Jupiter API.
        Returns SDK response on success, raises JupiterAPIError on failure.
        """
        # Ensure critical params are present or defaulted (e.g., payer)
        if "payer" not in params_dict:
            params_dict["payer"] = self.keypair

        # Ensure self.jupiter.create_trigger_order exists
        return await self._call_sdk_method(self.jupiter.create_trigger_order, **params_dict)

    async def execute_trigger_order(self, order_id: str) -> Any: # Or whatever identifier is used
        """
        Executes a created trigger order (if required by the API flow).
        Returns SDK response on success, raises JupiterAPIError on failure.
        """
        # Ensure self.jupiter.execute_trigger_order exists
        # This method might not be standard. The create_trigger_order might be the only step.
        logger.warning("execute_trigger_order called, ensure this is part of Jupiter Trigger API v1 flow.")
        return await self._call_sdk_method(getattr(self.jupiter, "execute_trigger_order", self._unsupported_method), order_id=order_id)

    async def cancel_trigger_order(self, order_id: str) -> Any:
        """
        Cancels an existing trigger order.
        Returns SDK response on success, raises JupiterAPIError on failure.
        """
        # Ensure self.jupiter.cancel_trigger_order exists
        return await self._call_sdk_method(self.jupiter.cancel_trigger_order, order_id=order_id) # Or other identifying param

    async def get_trigger_orders(
        self, 
        owner_address_str: Optional[str] = None, 
        status: Optional[str] = None # e.g., "open", "filled", "cancelled"
    ) -> Dict[str, Any]:
        """
        Retrieves trigger orders, optionally filtered by owner and status.
        Owner address should typically be self.keypair.public_key if not specified.
        """
        try:
            owner_pubkey = Pubkey.from_string(owner_address_str) if owner_address_str else self.keypair.public_key
            
            sdk_params = {"owner": owner_pubkey} # SDK might use 'owner_address' or similar
            if status:
                sdk_params["status"] = status # SDK might use an Enum for status
            
            # Ensure self.jupiter.get_trigger_orders (or query_open_orders etc.) exists
            return await self._call_sdk_method(self.jupiter.get_trigger_orders, **sdk_params)
        except ValueError as e:
            logger.error(f"Error preparing params for get_trigger_orders: {e}", exc_info=True)
            raise JupiterAPIError(message=f"Invalid parameters for get_trigger_orders: {e}", original_exception=e) from e
            
    # --- DCA (Dollar Cost Averaging) Orders ---

    async def create_dca_plan(self, params_dict: Dict) -> Any:
        """
        Creates a DCA plan using Jupiter API.
        Returns SDK response on success, raises JupiterAPIError on failure.
        """
        if "payer" not in params_dict: # Or whatever the SDK calls the signing keypair
            params_dict["payer"] = self.keypair

        # Ensure self.jupiter.create_dca_plan (or create_dca / create_dca_order) exists
        # This might be part of a separate DCA module in the SDK, e.g., self.jupiter_dca.create_dca(...)
        dca_creation_method = getattr(self.jupiter, "create_dca_plan", getattr(self.jupiter, "create_dca", None))
        if not dca_creation_method:
             # return {"success": False, "data": None, "error": "DCA creation method not found in SDK"}
             raise JupiterAPIError(message="DCA creation method not found in SDK (e.g., create_dca_plan or create_dca)")
        return await self._call_sdk_method(dca_creation_method, **params_dict)

    async def get_dca_orders(self, owner_address_str: Optional[str] = None) -> Any:
        """
        Retrieves DCA orders/plans for a given owner.
        Returns SDK response on success, raises JupiterAPIError on failure.
        """
        try:
            owner_pubkey = Pubkey.from_string(owner_address_str) if owner_address_str else self.keypair.public_key
            # Ensure self.jupiter.get_dca_orders or similar exists
            dca_get_method = getattr(self.jupiter, "get_dca_orders", getattr(self.jupiter, "get_dcas", None))
            if not dca_get_method:
                # return {"success": False, "data": None, "error": "DCA retrieval method not found in SDK"}
                raise JupiterAPIError(message="DCA retrieval method not found in SDK (e.g., get_dca_orders or get_dcas)")
            return await self._call_sdk_method(dca_get_method, owner=owner_pubkey) # SDK might use 'owner_address'
        except ValueError as e:
            logger.error(f"Error preparing params for get_dca_orders: {e}", exc_info=True)
            # return {"success": False, "data": None, "error": f"Invalid parameters for get_dca_orders: {e}"}
            raise JupiterAPIError(message=f"Invalid parameters for get_dca_orders: {e}", original_exception=e) from e

    async def close_dca_order(self, dca_order_id: str) -> Any: # ID could be a Pubkey or string
        """
        Closes/cancels an active DCA plan.
        Returns SDK response on success, raises JupiterAPIError on failure.
        """
        # Ensure self.jupiter.close_dca_order or similar exists
        dca_close_method = getattr(self.jupiter, "close_dca_order", getattr(self.jupiter, "close_dca", None))
        if not dca_close_method:
            # return {"success": False, "data": None, "error": "DCA closing method not found in SDK"}
            raise JupiterAPIError(message="DCA closing method not found in SDK (e.g., close_dca_order or close_dca)")
        # The identifier might be a Pubkey object or a string depending on the SDK
        # params_dict = {"dca_pubkey": Pubkey.from_string(dca_order_id), "user_wallet": self.keypair} # Example
        # Need to confirm the exact parameters for the SDK's close DCA method.
        # Assuming it takes the order_id and the payer keypair.
        try:
            # Placeholder for actual parameter construction based on SDK specifics
            # Example: if dca_order_id is a pubkey string:
            # dca_pubkey = Pubkey.from_string(dca_order_id)
            # return await self._call_sdk_method(dca_close_method, dca_pubkey=dca_pubkey, user_wallet=self.keypair)
            # For now, passing as is, assuming SDK method handles it or it's a simple string ID:
            return await self._call_sdk_method(dca_close_method, order_id=dca_order_id, payer=self.keypair) # Adjust params as per SDK
        except ValueError as e: # If dca_order_id needs to be a Pubkey and conversion fails
            logger.error(f"Error with dca_order_id for close_dca_order: {e}", exc_info=True)
            raise JupiterAPIError(message=f"Invalid dca_order_id format: {e}", original_exception=e) from e

    async def _unsupported_method(self, *args, **kwargs):
        method_name = inspect.currentframe().f_back.f_code.co_name
        logger.warning(f"Method {method_name} called but may not be supported or correctly implemented for the current SDK version.")
        # return {"success": False, "data": None, "error": f"Method {method_name} not fully supported or implemented."}
        raise NotImplementedError(f"Method {method_name} not fully supported or implemented in JupiterApiClient.")

    async def close_async_client(self):
        """Closes the underlying Solana async client."""
        if self.async_client:
            await self.async_client.close()
            logger.info("Solana async client closed.")

# Example usage (for testing or direct script execution):
# async def main():
#     # Load config (ensure your .env has MASTER_ENCRYPTION_KEY, SOLANA_PRIVATE_KEY_BS58, SOLANA_RPC_URL)
#     app_config = Config()
#     if not app_config.SOLANA_PRIVATE_KEY_BS58 or not app_config.SOLANA_RPC_URL:
#         print("SOLANA_PRIVATE_KEY_BS58 and SOLANA_RPC_URL must be set in config (via .env or directly).")
#         return

#     jupiter_client = JupiterApiClient(
#         private_key_bs58=app_config.SOLANA_PRIVATE_KEY_BS58,
#         rpc_url=app_config.SOLANA_RPC_URL,
#         config=app_config
#     )

#     # Example: Get SOL to USDC quote for 0.1 SOL
#     sol_mint = "So11111111111111111111111111111111111111112"
#     usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
#     amount_lamports = int(0.1 * 10**9) # 0.1 SOL in lamports

#     print(f"Fetching quote for 0.1 SOL to USDC...")
#     quote_resp = await jupiter_client.get_quote(sol_mint, usdc_mint, amount_lamports)
#     print(f"Quote Response: {quote_resp}")

#     if quote_resp["success"]:
#         print("\nFetching swap transaction data...")
#         swap_tx_resp = await jupiter_client.get_swap_transaction_data(quote_resp["data"])
#         print(f"Swap Transaction Response: {swap_tx_resp}")

#         # DO NOT RUN THIS ON MAINNET WITH REAL FUNDS WITHOUT THOROUGH TESTING AND UNDERSTANDING
#         # if swap_tx_resp["success"]:
#         #     print("\nSigning and sending transaction (SIMULATED - DO NOT RUN ON MAINNET WITHOUT CARE!)...")
#         #     # signed_tx_resp = await jupiter_client.sign_and_send_transaction(
#         #     #     swap_tx_resp["data"]["serialized_transaction_b64"],
#         #     #     swap_tx_resp["data"]["last_valid_block_height"]
#         #     # )
#         #     # print(f"Signed Transaction Response: {signed_tx_resp}")
#         # else:
#         #     print(f"Could not get swap transaction data: {swap_tx_resp['error']}")
#     else:
#         print(f"Could not get quote: {quote_resp['error']}")
    
#     # Example: Get prices
#     print("\nFetching prices for SOL and USDC vs USDT...")
#     prices_resp = await jupiter_client.get_prices([sol_mint, usdc_mint], vs_token_str="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
#     print(f"Prices Response: {prices_resp}")

#     # Example: Get token info
#     print("\nFetching token info for SOL...")
#     token_info_resp = await jupiter_client.get_token_info_list(mint_address_list=[sol_mint])
#     print(f"Token Info Response: {token_info_resp}")


#     await jupiter_client.close_async_client()

# if __name__ == "__main__":
#     # This is for direct execution. If part of a larger asyncio app, integrate into its loop.
#     # For simple testing:
#     # try:
#     #     asyncio.run(main())
#     # except KeyboardInterrupt:
#     #     print("Test execution cancelled.")
#     pass 
#     #     print("Test execution cancelled.")
#     pass 