import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.signature import Signature
from solana.rpc.commitment import Confirmed, ConfirmationStatus
from solders.fee_calculator import FeeCalculator
import base58
import os
import json
import aiohttp
from solders.transaction import VersionedTransaction
from solders.message import Message
from solana.exceptions import SolanaRpcException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from solana.rpc.types import TxOpts

from app.market.market_data import MarketDataProvider
from app.config import Config, EncryptionUtil
from app.utils.jupiter_api_client import JupiterApiClient
from app.utils.exceptions import (
    JupiterAPIError, SolanaTransactionError, TransactionExpiredError, 
    TransactionSimulationError, TransactionBroadcastError, TransactionConfirmationError,
    NumerusXBaseError, TradingError
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger("trading_engine")

class TradingEngine:
    """
    Handles low-level trade execution via Jupiter, including swaps, limit orders, and DCA.
    It uses JupiterApiClient for all interactions with the Jupiter SDK and Solana blockchain.
    """
    def __init__(self, wallet_path: str, rpc_url: Optional[str] = None):
        """
        Initialise le moteur de trading.
        
        Args:
            wallet_path: Chemin vers le fichier de clé du portefeuille. Ce chemin est la source principale.
                         Si ce fichier n'est pas valide ou non trouvé, des fallbacks seront tentés.
            rpc_url: URL du point de terminaison RPC Solana. Utilise Config.SOLANA_RPC_URL par défaut.
        """
        self.config = Config() # Initialize Config instance
        self.rpc_url = rpc_url if rpc_url is not None else self.config.SOLANA_RPC_URL
        self.client = AsyncClient(self.rpc_url)
        self.wallet = self._initialize_wallet(wallet_path)
        self.market_data_provider = None
        self.last_transaction_signature = None
        self.transaction_history = []
        self._api_session = None
        
        # Initialize MarketDataProvider if not already done by __aenter__ strategy
        # For now, assume it will be available when needed or passed in.
        self.market_data_provider: Optional[MarketDataProvider] = None 
        
        self.jupiter_client: Optional[JupiterApiClient] = None
        if self.wallet and self.rpc_url:
            try:
                # JupiterApiClient needs the private key as a base58 string.
                # self.wallet is a Keypair object. self.wallet.secret_key() returns bytes.
                # We need to ensure the private key used for wallet init can be re-encoded to bs58 if needed,
                # or that JupiterApiClient can take a Keypair object directly (it expects bs58 string currently).
                # For now, we assume SOLANA_PRIVATE_KEY_BS58 from config is the one to use for Jupiter API calls.
                # This aligns with JupiterApiClient's current __init__ which expects a private_key_bs58 string.
                # If self.wallet is the sole source of truth for the key, JupiterApiClient init needs adjustment.
                # Based on current JupiterApiClient, it uses config.SOLANA_PRIVATE_KEY_BS58 if available.
                
                # Let's pass the loaded wallet's private key directly to JupiterApiClient.
                # The Keypair object stores the private key as the first 32 bytes of its 64-byte internal representation (_keypair).
                # Or, more simply, if we have the original bs58 string used to create self.wallet, we should use that.
                # The _initialize_wallet tries to load from file or env (SOLANA_PRIVATE_KEY_BS58).
                # So, SOLANA_PRIVATE_KEY_BS58 should be available in self.config if that was the source.
                
                private_key_for_jupiter = self.config.SOLANA_PRIVATE_KEY_BS58 
                if not private_key_for_jupiter:
                    # Fallback: If wallet was loaded from a file and not env var, we might need to derive bs58 from keypair if possible
                    # Or ensure that the primary_wallet_path content *is* the bs58 key if used for Jupiter.
                    # This part is tricky if the file was a JSON array.
                    # For simplicity, we rely on SOLANA_PRIVATE_KEY_BS58 being the definitive key for Jupiter ops.
                    logger.warning("SOLANA_PRIVATE_KEY_BS58 not found in Config for JupiterApiClient. Trading operations might fail.")
                    # raise ConfigurationError("SOLANA_PRIVATE_KEY_BS58 must be set in Config for JupiterApiClient operations in TradingEngine")
                
                if private_key_for_jupiter:
                    self.jupiter_client = JupiterApiClient(
                        private_key_bs58=private_key_for_jupiter,
                        rpc_url=self.rpc_url,
                        config=self.config
                    )
                    logger.info("JupiterApiClient initialized successfully in TradingEngine.")
                else:
                    logger.error("Failed to obtain private key for JupiterApiClient in TradingEngine.")

            except Exception as e:
                logger.error(f"Failed to initialize JupiterApiClient in TradingEngine: {e}", exc_info=True)
        else:
            logger.warning("TradingEngine: Wallet or RPC URL not available for JupiterApiClient initialization.")
        
    def _load_keypair_from_file(self, file_path: str) -> Optional[Keypair]:
        """
        Tente de charger une Keypair depuis un fichier.
        Supporte le format JSON de Solana CLI (liste de 64 int) ou un fichier texte brut contenant une clé privée base58.
        Tente également de déchiffrer le contenu du fichier si MASTER_ENCRYPTION_KEY est configuré.
        """
        if not os.path.exists(file_path):
            logger.debug(f"Wallet file not found at: {file_path}")
            raise FileNotFoundError(f"Wallet file not found: {file_path}")

        with open(file_path, 'r') as f:
            raw_content = f.read().strip()
        
        content_to_parse = raw_content
        decrypted_content = None

        # Attempt decryption if MASTER_ENCRYPTION_KEY is available in Config and usable
        if Config.MASTER_ENCRYPTION_KEY_ENV: # Check if key is set
            logger.debug(f"MASTER_ENCRYPTION_KEY is set. Attempting to decrypt content of {file_path}.")
            # EncryptionUtil.decrypt expects base64 encoded ciphertext.
            # We assume the file content *is* the base64 encoded ciphertext.
            decrypted_content = EncryptionUtil.decrypt(raw_content)
            if decrypted_content:
                logger.info(f"Successfully decrypted content from {file_path}.")
                content_to_parse = decrypted_content
            else:
                logger.warning(f"Failed to decrypt content from {file_path}. Proceeding with raw content. This might be expected if the file is not encrypted.")
                # Keep content_to_parse as raw_content
        
        # Try to parse the content (either original or decrypted)
        parsed_keypair = self._parse_keypair_content(content_to_parse, file_path, is_decrypted=(decrypted_content is not None))
        
        if parsed_keypair:
            return parsed_keypair
        
        # If decrypted content failed to parse, and original content was different, try parsing original content as a fallback.
        # This handles cases where a file might not be encrypted, and decryption attempt (which would fail) shouldn't prevent plaintext loading.
        if decrypted_content and raw_content != decrypted_content:
            logger.debug(f"Decrypted content from {file_path} failed to parse. Attempting to parse raw file content as fallback.")
            parsed_keypair_raw = self._parse_keypair_content(raw_content, file_path, is_decrypted=False)
            if parsed_keypair_raw:
                return parsed_keypair_raw

        # If all attempts fail (original, or decrypted if attempted)
        # The error from _parse_keypair_content for the last attempt (raw_content if decryption failed or wasn't attempted) will be the one raised.
        # If decryption was attempted and succeeded but parsing decrypted content failed, that specific error is lost unless _parse_keypair_content logs it.
        # Let's refine the error message if decryption was attempted.
        if decrypted_content is not None and parsed_keypair is None: # Decryption happened but parsing failed
             raise ValueError(f"File {file_path} (after attempted decryption) is not a valid Solana CLI JSON keypair or a raw Base58 private key file.")
        # else, the error from parsing raw_content will be implicitly raised by the logic below or if parsed_keypair_raw was None

        # Original logic if parsing (raw or decrypted) fails, to ensure an error is raised
        # This part might be redundant if _parse_keypair_content raises effectively
        if parsed_keypair is None: # This condition means all attempts including fallback to raw (if applicable) failed.
            raise ValueError(f"File {file_path} is not a valid Solana CLI JSON keypair or a raw Base58 private key file, even after attempting decryption (if configured).")
        
        return parsed_keypair # Should technically be unreachable if an error is always raised above on failure

    def _parse_keypair_content(self, content: str, file_path_for_log: str, is_decrypted: bool) -> Optional[Keypair]:
        """
        Helper function to parse keypair from string content (JSON or Base58).
        Logs context about whether the content was decrypted.
        """
        keypair = None
        log_prefix = f"(Decrypted content of {file_path_for_log})" if is_decrypted else f"(Raw content of {file_path_for_log})"

        # Attempt 1: Try parsing as Solana CLI JSON
        try:
            key_data_json = json.loads(content)
            if isinstance(key_data_json, list) and len(key_data_json) == 64 and all(isinstance(x, int) for x in key_data_json):
                private_key_bytes = bytes(key_data_json)
                keypair = Keypair.from_bytes(private_key_bytes)
                logger.debug(f"Successfully loaded Keypair from JSON. {log_prefix}")
                return keypair
            else:
                logger.debug(f"{log_prefix} is JSON but not in expected Solana CLI format.")
        except json.JSONDecodeError:
            logger.debug(f"{log_prefix} is not valid JSON. Attempting to load as raw Base58 private key.")
        except ValueError as ve:
            logger.debug(f"Error creating Keypair from JSON bytes. {log_prefix}: {ve}. Expected 64 bytes [secret+public].")

        # Attempt 2: Try parsing as raw Base58 private key string
        try:
            decoded_bs58_key = base58.b58decode(content)
            if len(decoded_bs58_key) == 32:
                keypair = Keypair.from_secret_key(decoded_bs58_key)
                logger.debug(f"Successfully loaded Keypair from Base58 private key. {log_prefix}")
                return keypair
            else:
                logger.debug(f"{log_prefix} decoded Base58 content has length {len(decoded_bs58_key)}, expected 32 bytes.")
        except Exception as e:
            logger.debug(f"Failed to decode Base58 content or create Keypair. {log_prefix}: {e}")
            
        if keypair is None:
            # Don't raise here, let the caller decide. This function just attempts parsing.
            logger.debug(f"Failed to parse content as Keypair. {log_prefix}")
        return keypair

    def _load_keypair_from_env_var(self, env_var_name: str) -> Optional[Keypair]:
        """
        Tente de charger une Keypair depuis une variable d'environnement contenant une clé privée base58.
        """
        private_key_bs58 = getattr(Config, env_var_name, None) # Use getattr for safety
        if not private_key_bs58:
            logger.debug(f"Environment variable {env_var_name} not set or empty.")
            return None
        
        try:
            private_key_bytes = base58.b58decode(private_key_bs58)
            if len(private_key_bytes) != 32:
                raise ValueError(f"Invalid private key length from {env_var_name}: {len(private_key_bytes)}, expected 32 bytes.")
            keypair = Keypair.from_secret_key(private_key_bytes)
            logger.debug(f"Successfully loaded Keypair from environment variable {env_var_name}.")
            return keypair
        except Exception as e:
            logger.error(f"Failed to initialize wallet from {env_var_name}: {e}")
            raise ValueError(f"Invalid private key in environment variable {env_var_name}: {e}")

    def _initialize_wallet(self, primary_wallet_path: str) -> Keypair:
        """
        Initialise le portefeuille de manière sécurisée avec validation et fallbacks.
        Ordre de tentative:
        1. Chemin principal fourni (`primary_wallet_path`).
        2. Chemin de secours (`Config.BACKUP_WALLET_PATH`).
        3. Variable d'environnement (`Config.SOLANA_PRIVATE_KEY_BS58`).
        
        Args:
            primary_wallet_path: Chemin principal vers le fichier de clé du portefeuille.
            
        Returns:
            Instance Keypair pour le portefeuille.
            
        Raises:
            ValueError: Si aucune méthode de chargement de portefeuille ne réussit ou si un chemin/clé est invalide.
        """
        error_messages = []

        # Attempt 1: Load from primary_wallet_path
        if primary_wallet_path:
            logger.info(f"Attempting to load wallet from primary path: {primary_wallet_path}")
            try:
                keypair = self._load_keypair_from_file(primary_wallet_path)
                if keypair:
                    logger.info(f"Wallet initialized successfully from primary path: {primary_wallet_path}. Address: {keypair.pubkey()}")
                    return keypair
            except Exception as e:
                msg = f"Failed to load wallet from primary path '{primary_wallet_path}': {e}"
                logger.warning(msg)
                error_messages.append(msg)
        else:
            logger.warning("Primary wallet path was not provided.")
            error_messages.append("Primary wallet path not provided.")


        # Attempt 2: Load from backup wallet_path
        if Config.BACKUP_WALLET_PATH:
            logger.info(f"Attempting to load wallet from backup path: {Config.BACKUP_WALLET_PATH}")
            try:
                keypair = self._load_keypair_from_file(Config.BACKUP_WALLET_PATH)
                if keypair:
                    logger.info(f"Wallet initialized successfully from backup path: {Config.BACKUP_WALLET_PATH}. Address: {keypair.pubkey()}")
                    return keypair
            except Exception as e:
                msg = f"Failed to load wallet from backup path '{Config.BACKUP_WALLET_PATH}': {e}"
                logger.warning(msg)
                error_messages.append(msg)
        else:
            logger.info("No backup wallet path configured (Config.BACKUP_WALLET_PATH is empty).")
            # No error_message append here as it's optional

        # Attempt 3: Load from environment variable
        # SOLANA_PRIVATE_KEY_BS58 is now expected to be in Config class
        if Config.SOLANA_PRIVATE_KEY_BS58: # Check if the attribute itself exists and is not None/empty
             logger.info(f"Attempting to load wallet from SOLANA_PRIVATE_KEY_BS58 environment variable.")
             try:
                 keypair = self._load_keypair_from_env_var("SOLANA_PRIVATE_KEY_BS58")
                 if keypair:
                     logger.info(f"Wallet initialized successfully from SOLANA_PRIVATE_KEY_BS58. Address: {keypair.pubkey()}")
                     return keypair
             except Exception as e: # ValueError is raised by _load_keypair_from_env_var on failure
                msg = f"Failed to load wallet from SOLANA_PRIVATE_KEY_BS58 environment variable: {e}"
                logger.warning(msg)
                error_messages.append(msg)
        else:
            logger.info("No SOLANA_PRIVATE_KEY_BS58 environment variable configured or Config.SOLANA_PRIVATE_KEY_BS58 is empty.")
            # No error_message append here as it's optional

        # If all attempts fail
        final_error_summary = "All wallet initialization methods failed. See warnings above for details on each attempt."
        logger.critical(final_error_summary)
        # Optionally, join error_messages for a more detailed exception:
        # detailed_errors = "\n".join(error_messages)
        # raise ValueError(f"{final_error_summary}\n{detailed_errors}")
        raise ValueError(final_error_summary)
            
    async def __aenter__(self):
        """Initialise les ressources asynchrones."""
        self._api_session = aiohttp.ClientSession() # For any direct HTTP calls if still needed (e.g. fallback Dexscreener)
        # Initialize MarketDataProvider here if it uses the session
        if not self.market_data_provider:
            self.market_data_provider = MarketDataProvider() # It will init its own session or we can pass one
            # If MarketDataProvider needs the session from TradingEngine:
            # self.market_data_provider.session = self._api_session 
            # Ensure MarketDataProvider also handles its session in its __aenter__/__aexit__ if shared.
            # For now, MarketDataProvider manages its own session internally.
        
        # Ensure JupiterApiClient's async_client is ready (it is initialized in __init__)
        # If JupiterApiClient also needed an __aenter__ for its client, call it here.
        # await self.jupiter_client.__aenter__() # If it had such a method

        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Libère les ressources asynchrones."""
        if self._api_session and not self._api_session.closed:
            await self._api_session.close()
        if self.market_data_provider and hasattr(self.market_data_provider, '__aexit__'):
            await self.market_data_provider.__aexit__(exc_type, exc_val, exc_tb)
        if self.jupiter_client and hasattr(self.jupiter_client, 'close_async_client'):
            await self.jupiter_client.close_async_client()
        await self.client.close() # Close the main Solana client

    async def get_fee_for_message(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Estime les frais pour une transaction avant exécution.
        
        Args:
            transaction: Transaction à analyser
            
        Returns:
            Frais estimés en lamports
        """
        # This method interacts with Solana RPC, not an external HTTP API in the same sense.
        # Error handling for RPC calls should be specific to solana-py library exceptions.
        # The return type should also be standardized to {'success': ..., 'error': ..., 'data': ...}
        try:
            recent_blockhash_response = await self.client.get_latest_blockhash(commitment=Confirmed)
            if not recent_blockhash_response.value or not recent_blockhash_response.value.blockhash:
                logger.error("Failed to get recent blockhash for fee estimation.")
                return {'success': False, 'error': "Failed to get recent blockhash", 'data': None}
            transaction.recent_blockhash = recent_blockhash_response.value.blockhash
            
            message_bytes = transaction.serialize_message()
            fee_response = await self.client.get_fee_for_message(message_bytes, commitment=Confirmed)
            
            if fee_response.value is None: # Check if fee value is None (can happen)
                logger.error(f"get_fee_for_message returned None for tx. Blockhash: {transaction.recent_blockhash}")
                return {'success': False, 'error': "Failed to estimate fee (RPC returned null)", 'data': None}
                
            logger.info(f"Estimated fee: {fee_response.value} lamports")
            return {'success': True, 'error': None, 'data': {'fee_lamports': fee_response.value}}
        except Exception as e:
            # Catching Solana-specific RPC exceptions would be more precise, e.g., RPCException
            # from solana.rpc.core import RPCException (or similar based on library version)
            logger.error(f"Error estimating transaction fee: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"Error estimating fee: {str(e)}", 'data': None}
            
    async def execute_swap(
        self,
        input_token_mint_str: str,
        output_token_mint_str: str,
        amount_in_tokens_float: Optional[float] = None,
        amount_in_usd: Optional[float] = None,
        slippage_bps: Optional[int] = None,
        swap_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a token swap.
        Either amount_in_tokens_float (for input token) or amount_in_usd must be provided.
        Returns a dictionary: {'success': bool, 'error': str, 'signature': str, 'details': dict}
        'details' will contain quote_response and last_valid_block_height on success.
        """
        if not (amount_in_tokens_float or amount_in_usd):
            return {'success': False, 'error': "Either amount_in_tokens_float or amount_in_usd must be provided.", 'signature': None, 'details': None}
        if amount_in_tokens_float and amount_in_usd:
            return {'success': False, 'error': "Provide either amount_in_tokens_float or amount_in_usd, not both.", 'signature': None, 'details': None}

        final_slippage_bps = slippage_bps if slippage_bps is not None else self.config.JUPITER_DEFAULT_SLIPPAGE_BPS
        final_swap_mode = swap_mode if swap_mode is not None else self.config.JUPITER_SWAP_MODE

        amount_lamports: Optional[int] = None

        try:
            market_data_provider = await self._get_market_data_provider()

            if amount_in_usd:
                if input_token_mint_str == self.config.USDC_MINT_ADDRESS: # Assuming USDC is the "USD" token
                    # If input is USDC, we need its decimals (usually 6 for USDC)
                    token_info_response = await market_data_provider.get_token_info(input_token_mint_str)
                    if not token_info_response['success'] or not token_info_response['data']:
                        raise TradingError(f"Failed to get token info for input USDC {input_token_mint_str}: {token_info_response.get('error')}")
                    decimals = token_info_response['data']['decimals']
                    amount_lamports = int(amount_in_usd * (10**decimals))
                else:
                    # If input is another token, convert USD value to token amount, then to lamports
                    price_response = await market_data_provider.get_token_price(input_token_mint_str, self.config.USDC_MINT_ADDRESS)
                    if not price_response['success'] or not price_response['data'] or price_response['data']['price'] == 0:
                        raise TradingError(f"Failed to get price for input token {input_token_mint_str} to calculate amount from USD: {price_response.get('error')}")
                    
                    token_price_usd = price_response['data']['price']
                    calculated_amount_tokens = amount_in_usd / token_price_usd
                    
                    token_info_response = await market_data_provider.get_token_info(input_token_mint_str)
                    if not token_info_response['success'] or not token_info_response['data']:
                         raise TradingError(f"Failed to get token info for input {input_token_mint_str}: {token_info_response.get('error')}")
                    decimals = token_info_response['data']['decimals']
                    amount_lamports = int(calculated_amount_tokens * (10**decimals))
            
            elif amount_in_tokens_float:
                token_info_response = await market_data_provider.get_token_info(input_token_mint_str)
                if not token_info_response['success'] or not token_info_response['data']:
                    raise TradingError(f"Failed to get token info for input {input_token_mint_str}: {token_info_response.get('error')}")
                decimals = token_info_response['data']['decimals']
                amount_lamports = int(amount_in_tokens_float * (10**decimals))

            if amount_lamports is None or amount_lamports <= 0:
                raise TradingError(f"Calculated amount_lamports is invalid: {amount_lamports}")

            logger.info(f"Executing swap: {amount_lamports} lamports of {input_token_mint_str} for {output_token_mint_str}")
            
            swap_result = await self._execute_swap_attempt(
                input_token_mint_str=input_token_mint_str,
                output_token_mint_str=output_token_mint_str,
                amount_lamports=amount_lamports,
                slippage_bps=final_slippage_bps,
                swap_mode=final_swap_mode
            )
            
            return {
                'success': True, 
                'signature': swap_result["signature"],
                'error': None,
                'details': {
                    # Convert SDK objects to dicts if they are not already serializable by default
                    # Assuming quote_response and transaction_data are dict-like or have simple structures.
                    # If they are complex Pydantic models from SDK, may need .model_dump() or similar.
                    'quote_response': swap_result["quote_response"], 
                    'transaction_data': swap_result["transaction_data"],
                    'last_valid_block_height': swap_result["last_valid_block_height"],
                    'input_token_mint': input_token_mint_str,
                    'output_token_mint': output_token_mint_str,
                    'amount_lamports_swapped': amount_lamports,
                    'slippage_bps_used': final_slippage_bps
                }
            }

        except TransactionExpiredError as e:
            logger.error(f"Swap failed after retries due to TransactionExpiredError: {e}", exc_info=True)
            return {'success': False, 'error': f"Transaction expired after retries: {e}", 'signature': None, 'details': {'original_exception': str(e)}}
        except (JupiterAPIError, SolanaTransactionError, TradingError, NumerusXBaseError) as e:
            logger.error(f"Swap execution failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'signature': None, 'details': {'original_exception': str(e)}}
        except Exception as e:
            logger.critical(f"Unexpected error during swap execution: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'signature': None, 'details': {'original_exception': str(e)}}

    async def _get_market_data_provider(self) -> MarketDataProvider:
        if self.market_data_provider is None:
            self.market_data_provider = MarketDataProvider(
                config=self.config,
                jupiter_client=self.jupiter_client # Share the client if MDP needs it
            )
            # Enter context if MDP supports it (assuming it does for session management)
            # This part might need adjustment based on MDP's __aenter__ signature
            # For now, assuming it's okay to call directly or that __aenter__ is simple.
            await self.market_data_provider.__aenter__() 
        return self.market_data_provider

    @retry(
        stop=stop_after_attempt(Config.JUPITER_MAX_RETRIES if hasattr(Config, 'JUPITER_MAX_RETRIES') else 3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(TransactionExpiredError),
        reraise=True # Reraise the exception if all retries fail
    )
    async def _execute_swap_attempt(
        self,
        input_token_mint_str: str,
        output_token_mint_str: str,
        amount_lamports: int,
        slippage_bps: int,
        swap_mode: str
    ) -> Dict[str, Any]:
        """
        Internal method to perform a single swap attempt.
        This method is decorated with tenacity.retry to handle TransactionExpiredError.
        Returns a dictionary with quote_response, transaction_data, and signature on success.
        Raises JupiterAPIError or SolanaTransactionError on failure.
        """
        logger.info(f"Attempting swap: {amount_lamports} lamports of {input_token_mint_str} for {output_token_mint_str}, slippage: {slippage_bps}bps, mode: {swap_mode}")
        
        # 1. Get Quote
        # Parameters for get_quote are passed directly.
        quote_response_dict = await self.jupiter_client.get_quote(
            input_mint_str=input_token_mint_str,
            output_mint_str=output_token_mint_str,
            amount_lamports=amount_lamports,
            slippage_bps=slippage_bps,
            swap_mode=swap_mode
            # Other params like compute_unit_price_micro_lamports, etc., are handled by JupiterApiClient using Config defaults
        )
        # JupiterApiClient.get_quote now returns the direct SDK response object, not a dict with 'success'.
        # We assume if no exception, it was successful. The response object is what we need.
        logger.debug(f"Quote received: {quote_response_dict}")

        # 2. Get Swap Transaction Data
        # Assuming quote_response_dict is the actual QuoteResponse object from the SDK
        transaction_data_dict = await self.jupiter_client.get_swap_transaction_data(
            quote_response=quote_response_dict 
            # payer_public_key is handled by jupiter_client
        )
        logger.debug(f"Swap transaction data obtained: {transaction_data_dict}")
        
        serialized_transaction_b64 = transaction_data_dict['swap_transaction'] # Key from SDK
        last_valid_block_height = transaction_data_dict['last_valid_block_height']

        # 3. Sign and Send Transaction
        signature = await self.jupiter_client.sign_and_send_transaction(
            serialized_transaction_b64=serialized_transaction_b64,
            last_valid_block_height=last_valid_block_height
        )
        logger.info(f"Swap transaction sent successfully. Signature: {signature}")
        
        return {
            "quote_response": quote_response_dict, # Keep the original quote response
            "transaction_data": transaction_data_dict, # Keep original transaction data
            "signature": signature,
            "last_valid_block_height": last_valid_block_height
        }

    def _record_transaction(self, result: Dict[str, Any], details: Dict[str, Any]) -> None:
        """Enregistre les détails d'une transaction dans l'historique."""
        transaction_record = {
            "signature": result.get("signature"),
            "timestamp": time.time(),
            "success": result.get("success", False),
            "details": details
        }
        
        self.transaction_history.append(transaction_record)
        self.last_transaction_signature = result.get("signature")

    # --- Limit Order (Trigger Order) Operations ---
    async def place_limit_order(
        self,
        input_token_mint_str: str, # Token you are selling
        output_token_mint_str: str, # Token you are buying
        amount_in_tokens_float: float, # Amount of input_token to sell
        target_price_float: float, # Target price: how many output_tokens per one input_token
        order_side: str # "BUY" or "SELL" - "BUY" means buying output_token with input_token.
                       # "SELL" means selling input_token for output_token.
                       # This is relative to the output_token. Example: BUY SOL/USDC means input_token=USDC, output_token=SOL
    ) -> Dict[str, Any]:
        logger.info(f"Placeholder: place_limit_order called for {order_side} {amount_in_tokens_float} of {input_token_mint_str} for {output_token_mint_str} at price {target_price_float}")
        # TODO: Implement logic using self.jupiter_client.create_trigger_order
        # 1. Determine base and quote mints for Jupiter based on order_side and target_price interpretation.
        #    Jupiter's trigger orders often require `base_mint_address` and `quote_mint_address`.
        #    If buying SOL (output) with USDC (input) at price P (USDC per SOL):
        #        base_mint = SOL, quote_mint = USDC, price = P
        #    If selling SOL (input) for USDC (output) at price P (USDC per SOL):
        #        base_mint = SOL, quote_mint = USDC, price = P (still price of base in terms of quote)
        # 2. Convert amount_in_tokens_float to lamports for the base token of the trigger order.
        # 3. Call self.jupiter_client.create_trigger_order with appropriate parameters.
        # 4. Handle response and errors.
        try:
            # Example call structure (needs actual implementation)
            # result = await self.jupiter_client.create_trigger_order(...)
            # return {'success': True, 'order_id': result.get('id'), 'details': result}
            raise NotImplementedError("place_limit_order is not yet implemented.")
        except (JupiterAPIError, SolanaTransactionError, NumerusXBaseError) as e:
            logger.error(f"Failed to place limit order: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'order_id': None, 'details': {'original_exception': str(e)}}
        except Exception as e:
            logger.critical(f"Unexpected error placing limit order: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'order_id': None, 'details': {'original_exception': str(e)}}


    async def cancel_limit_order(self, order_id: str) -> Dict[str, Any]:
        logger.info(f"Placeholder: cancel_limit_order called for order_id: {order_id}")
        # TODO: Implement logic using self.jupiter_client.cancel_trigger_order
        try:
            # result = await self.jupiter_client.cancel_trigger_order(order_id=order_id, ...)
            # return {'success': True, 'details': result}
             raise NotImplementedError("cancel_limit_order is not yet implemented.")
        except (JupiterAPIError, NumerusXBaseError) as e: # Assuming cancel might not involve on-chain tx errors directly
            logger.error(f"Failed to cancel limit order {order_id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'details': {'original_exception': str(e)}}
        except Exception as e:
            logger.critical(f"Unexpected error cancelling limit order {order_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'details': {'original_exception': str(e)}}

    async def get_open_limit_orders(
        self,
        owner_wallet_address: Optional[str] = None 
    ) -> Dict[str, Any]:
        logger.info(f"Placeholder: get_open_limit_orders called for owner: {owner_wallet_address or 'self'}")
        # TODO: Implement logic using self.jupiter_client.get_trigger_orders
        final_owner = owner_wallet_address if owner_wallet_address else str(self.jupiter_client.keypair.public_key)
        try:
            # orders = await self.jupiter_client.get_trigger_orders(owner_address=final_owner)
            # return {'success': True, 'orders': orders, 'details': None}
            raise NotImplementedError("get_open_limit_orders is not yet implemented.")
        except (JupiterAPIError, NumerusXBaseError) as e:
            logger.error(f"Failed to get open limit orders: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'orders': [], 'details': {'original_exception': str(e)}}
        except Exception as e:
            logger.critical(f"Unexpected error getting open limit orders: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'orders': [], 'details': {'original_exception': str(e)}}

    # --- DCA Operations ---
    async def create_dca_plan(
        self,
        input_token_mint_str: str,
        output_token_mint_str: str,
        total_amount_in_tokens_float: float, # Total amount of input_token for the DCA
        frequency_seconds: int, 
        num_orders: int
    ) -> Dict[str, Any]:
        logger.info("Placeholder: create_dca_plan called.")
        # TODO: Implement logic using self.jupiter_client.create_dca_plan
        try:
            raise NotImplementedError("create_dca_plan is not yet implemented.")
        except (JupiterAPIError, SolanaTransactionError, NumerusXBaseError) as e:
            logger.error(f"Failed to create DCA plan: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'dca_plan_id': None, 'details': {'original_exception': str(e)}}
        except Exception as e:
            logger.critical(f"Unexpected error creating DCA plan: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'dca_plan_id': None, 'details': {'original_exception': str(e)}}


    async def get_dca_plan_orders(self, dca_plan_id: str) -> Dict[str, Any]:
        logger.info(f"Placeholder: get_dca_plan_orders for ID: {dca_plan_id}")
        # TODO: Implement logic, possibly using self.jupiter_client.get_dca_orders
        try:
            raise NotImplementedError("get_dca_plan_orders is not yet implemented.")
        except (JupiterAPIError, NumerusXBaseError) as e:
            logger.error(f"Failed to get DCA plan orders for {dca_plan_id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'orders': [], 'details': {'original_exception': str(e)}}
        except Exception as e:
            logger.critical(f"Unexpected error getting DCA plan orders for {dca_plan_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'orders': [], 'details': {'original_exception': str(e)}}


    async def close_dca_plan(self, dca_plan_id: str) -> Dict[str, Any]:
        logger.info(f"Placeholder: close_dca_plan for ID: {dca_plan_id}")
        # TODO: Implement logic using self.jupiter_client.close_dca_order
        try:
            raise NotImplementedError("close_dca_plan is not yet implemented.")
        except (JupiterAPIError, SolanaTransactionError, NumerusXBaseError) as e:
            logger.error(f"Failed to close DCA plan {dca_plan_id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'details': {'original_exception': str(e)}}
        except Exception as e:
            logger.critical(f"Unexpected error closing DCA plan {dca_plan_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'details': {'original_exception': str(e)}}

    async def close_clients(self):
        """Closes any open client sessions, like MarketDataProvider's aiohttp session."""
        logger.info("Closing TradingEngine's internal clients...")
        if self.market_data_provider and hasattr(self.market_data_provider, '__aexit__'):
            try:
                # Assuming MarketDataProvider has an __aexit__ or close method
                await self.market_data_provider.__aexit__(None, None, None)
                logger.info("MarketDataProvider client closed by TradingEngine.")
            except Exception as e:
                logger.error(f"Error closing MarketDataProvider in TradingEngine: {e}", exc_info=True)
        # JupiterApiClient's AsyncClient is managed by its own __aenter__/__aexit__
        # or needs an explicit close if TradingEngine created it.
        # Based on current JupiterApiClient, it manages its own Solana AsyncClient session
        # if passed one, or creates one. If TradingEngine passes a shared JupiterApiClient,
        # the lifecycle of JupiterApiClient's internal Solana client is managed by JupiterApiClient itself.
        logger.info("TradingEngine clients (if any were exclusively owned) closed.")
