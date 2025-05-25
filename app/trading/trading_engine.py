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
    NumerusXBaseError
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger("trading_engine")

class TradingEngine:
    """Moteur de trading optimisé pour exécuter des opérations sur les DEX Solana."""
    
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
        input_token_mint: str, 
        output_token_mint: str, 
        amount_in_usd: Optional[float] = None, 
        amount_in_tokens_float: Optional[float] = None, 
        slippage_bps: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Exécute un swap en utilisant JupiterApiClient via MarketDataProvider et JupiterApiClient directement.
        Gère la conversion USD -> tokens si nécessaire, obtient la quote, récupère les données de transaction,
        signe et envoie la transaction. Inclut la logique de retry pour TransactionExpiredError.
        """
        start_time = time.time()
        self.last_transaction_signature = None # Reset before new attempt

        if not self.market_data_provider:
            logger.error("MarketDataProvider not initialized in TradingEngine for execute_swap.")
            return {"success": False, "error": "MarketDataProvider not initialized", "signature": None, "details": None}
        if not self.jupiter_client:
            logger.error("JupiterApiClient not initialized in TradingEngine for execute_swap.")
            return {"success": False, "error": "JupiterApiClient not initialized", "signature": None, "details": None}

        actual_slippage_bps = slippage_bps if slippage_bps is not None else self.config.JUPITER_DEFAULT_SLIPPAGE_BPS

        # Validate and determine amount_in_tokens_float
        if amount_in_tokens_float is None and amount_in_usd is not None:
            logger.info(f"Amount in USD provided: {amount_in_usd}. Converting to token amount for {input_token_mint}.")
            price_response = await self.market_data_provider.get_token_price(input_token_mint)
            if not price_response.get("success") or not price_response.get("data") or not price_response["data"].get("price"):
                error_msg = f"Failed to get price for input token {input_token_mint} to convert USD amount: {price_response.get('error')}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "signature": None, "details": None}
            token_price_usd = price_response["data"]["price"]
            if token_price_usd <= 0:
                error_msg = f"Invalid price ({token_price_usd}) for input token {input_token_mint}. Cannot convert USD amount."
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "signature": None, "details": None}
            amount_in_tokens_float = amount_in_usd / token_price_usd
            logger.info(f"Converted {amount_in_usd} USD to {amount_in_tokens_float} of {input_token_mint} at price {token_price_usd} USD.")
        elif amount_in_tokens_float is None and amount_in_usd is None:
            error_msg = "Either amount_in_usd or amount_in_tokens_float must be provided for execute_swap."
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "signature": None, "details": None}
        elif amount_in_tokens_float is not None:
            logger.info(f"Amount in tokens provided: {amount_in_tokens_float} {input_token_mint}")
        # If both are provided, amount_in_tokens_float takes precedence as per original logic, though this should be clarified.

        if amount_in_tokens_float <= 0:
            error_msg = f"Amount to swap must be positive. Provided: {amount_in_tokens_float} {input_token_mint}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "signature": None, "details": None}

        try:
            tx_signature = await self._execute_swap_attempt(
                input_token_mint=input_token_mint,
                output_token_mint=output_token_mint,
                amount_in_tokens_float=amount_in_tokens_float,
                slippage_bps=actual_slippage_bps
            )
            self.last_transaction_signature = tx_signature
            duration = time.time() - start_time
            logger.info(f"Swap successful for {input_token_mint} -> {output_token_mint}. Signature: {tx_signature}. Duration: {duration:.2f}s")
            result = {
                "success": True, 
                "signature": tx_signature, 
                "error": None, 
                "duration_seconds": duration,
                "details": {
                    "input_token": input_token_mint,
                    "output_token": output_token_mint,
                    "amount_swapped_tokens": amount_in_tokens_float,
                    # More details can be added here from quote_data if needed
                }
            }
        except TransactionExpiredError as e:
            # This is after retries by _execute_swap_attempt have failed.
            duration = time.time() - start_time
            logger.error(f"Swap failed after retries due to TransactionExpiredError: {e}. Duration: {duration:.2f}s", exc_info=True)
            result = {"success": False, "error": f"Swap failed: Transaction expired after retries - {e}", "signature": e.signature, "duration_seconds": duration, "details": e}
        except JupiterAPIError as e:
            duration = time.time() - start_time
            logger.error(f"Swap failed due to JupiterAPIError: {e}. Duration: {duration:.2f}s", exc_info=True)
            result = {"success": False, "error": f"Swap failed: Jupiter API Error - {e}", "signature": None, "duration_seconds": duration, "details": e}
        except SolanaTransactionError as e: # Covers Simulation, Broadcast, Confirmation errors
            duration = time.time() - start_time
            logger.error(f"Swap failed due to SolanaTransactionError: {e}. Duration: {duration:.2f}s", exc_info=True)
            result = {"success": False, "error": f"Swap failed: Solana Transaction Error - {e}", "signature": e.signature, "duration_seconds": duration, "details": e}
        except NumerusXBaseError as e: # Catch other app-specific errors
            duration = time.time() - start_time
            logger.error(f"Swap failed due to NumerusXBaseError: {e}. Duration: {duration:.2f}s", exc_info=True)
            result = {"success": False, "error": f"Swap failed: Application Error - {e}", "signature": None, "duration_seconds": duration, "details": e}
        except Exception as e:
            duration = time.time() - start_time
            logger.critical(f"Unexpected critical error during swap: {e}. Duration: {duration:.2f}s", exc_info=True)
            result = {"success": False, "error": f"Swap failed: Unexpected critical error - {e}", "signature": None, "duration_seconds": duration, "details": None}

        self._record_transaction(result, {
            "input_token_mint": input_token_mint,
            "output_token_mint": output_token_mint,
            "amount_in_tokens_float": amount_in_tokens_float,
            "slippage_bps": actual_slippage_bps,
            "attempted_amount_usd": amount_in_usd
        })
        return result

    # Add tenacity retry for TransactionExpiredError around the core swap logic
    @retry(
        retry=retry_if_exception_type(TransactionExpiredError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(Config.JUPITER_MAX_RETRIES if hasattr(Config, 'JUPITER_MAX_RETRIES') else 3),
        reraise=True # Reraise TransactionExpiredError if all retries fail, to be caught by outer layer if needed
    )
    async def _execute_swap_attempt(
        self, 
        input_token_mint: str, 
        output_token_mint: str, 
        amount_in_tokens_float: float,
        slippage_bps: int
    ) -> str: # Returns transaction signature on success
        """One attempt to perform the full quote -> get_tx_data -> sign_and_send flow."""
        if not self.market_data_provider:
            logger.error("MarketDataProvider not initialized in TradingEngine.")
            raise RuntimeError("MarketDataProvider not initialized") # Or return error dict if preferred by execute_swap
        if not self.jupiter_client:
            logger.error("JupiterApiClient not initialized in TradingEngine.")
            raise RuntimeError("JupiterApiClient not initialized")

        # 1. Get quote from MarketDataProvider (which uses JupiterApiClient)
        logger.info(f"Attempting to get swap quote: {amount_in_tokens_float} {input_token_mint} -> {output_token_mint}")
        quote_response_dict = await self.market_data_provider.get_jupiter_swap_quote(
            input_mint_str=input_token_mint,
            output_mint_str=output_token_mint,
            amount_in_tokens=amount_in_tokens_float,
            slippage_bps=slippage_bps
        )

        if not quote_response_dict.get("success") or not quote_response_dict.get("data"):
            error_msg = f"Failed to get swap quote: {quote_response_dict.get('error', 'No quote data returned')}"
            logger.error(error_msg)
            # Decide if this should raise a specific error or be handled by the caller execute_swap to return a dict
            raise JupiterAPIError(message=error_msg) # Propagate as JupiterAPIError to be caught by execute_swap
        
        quote_data_from_sdk = quote_response_dict["data"] # This is the raw quote response from SDK
        logger.info(f"Successfully obtained swap quote. Out amount: {quote_data_from_sdk.get('outAmount')} lamports.")

        # 2. Get swap transaction data from JupiterApiClient
        logger.info("Fetching swap transaction data from JupiterApiClient...")
        # get_swap_transaction_data expects the raw quote response object from the SDK's quote call.
        swap_tx_data_dict = await self.jupiter_client.get_swap_transaction_data(quote_data_from_sdk)
        
        # get_swap_transaction_data now returns a dict {"serialized_transaction_b64": ..., "last_valid_block_height": ...} or raises
        serialized_transaction_b64 = swap_tx_data_dict["serialized_transaction_b64"]
        last_valid_block_height = swap_tx_data_dict["last_valid_block_height"]
        logger.info(f"Successfully obtained swap transaction data. Last valid block height: {last_valid_block_height}")

        # 3. Sign and send transaction using JupiterApiClient
        logger.info("Signing and sending transaction...")
        # sign_and_send_transaction now returns signature string or raises SolanaTransactionError subtypes
        tx_signature_str = await self.jupiter_client.sign_and_send_transaction(
            serialized_transaction_b64=serialized_transaction_b64,
            last_valid_block_height=last_valid_block_height
        )
        logger.info(f"Swap transaction successfully sent and confirmed. Signature: {tx_signature_str}")
        return tx_signature_str

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

    # async def _get_api_session(self) -> aiohttp.ClientSession:
    #     """Crée et retourne une session aiohttp."""
    #     if self._api_session is None or self._api_session.closed:
    #         self._api_session = aiohttp.ClientSession()
    #     return self._api_session
    #
    # async def _close_api_session(self):
    #     """Ferme la session aiohttp si elle est ouverte."""
    #     if self._api_session and not self._api_session.closed:
    #         await self._api_session.close()
    #         logger.info("aiohttp session closed.")
    #
    # async def _make_jupiter_api_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
    #     """
    #     Effectue une requête HTTP à l'API Jupiter V6 en utilisant aiohttp.
    #     DEPRECATED: Should use JupiterApiClient with the SDK.
    #     Args:
    #         method: Méthode HTTP (GET, POST).
    #         endpoint: Le chemin de l'API (ex: /quote).
    #         params: Dictionnaire de paramètres d'URL pour les requêtes GET.
    #         data: Dictionnaire de données JSON pour les requêtes POST.
    #
    #     Returns:
    #         La réponse JSON de l'API sous forme de dictionnaire.
    #
    #     Raises:
    #         JupiterAPIError: Si la requête échoue ou retourne un statut d'erreur.
    #     """
    #     session = await self._get_api_session()
    #     # Note: Config.JUPITER_API_BASE_URL_V6 should be the correct base for v6 direct calls if any were needed.
    #     # However, JupiterApiClient handles URL construction now. This method is purely for legacy/direct aiohttp example.
    #     # This method is marked as DEPRECATED.
    #     base_url = self.config.JUPITER_API_BASE_URL_V6 # Example if it were used
    #     if not base_url:
    #         logger.error("JUPITER_API_BASE_URL_V6 not configured.")
    #         raise JupiterAPIError("Jupiter API base URL not configured.", api_name="JupiterV6_Direct")
    #     
    #     url = f"{base_url}{endpoint}"
    #     
    #     headers = {"Accept": "application/json"}
    #     if self.config.JUPITER_V6_API_KEY: # Example if a key was needed for direct calls
    #         headers["Authorization"] = f"Bearer {self.config.JUPITER_V6_API_KEY}"
    #
    #     try:
    #         logger.debug(f"Making {method} request to {url} with params={params}, data={data}")
    #         async with session.request(method, url, params=params, json=data, headers=headers, timeout=self.config.JUPITER_REQUEST_TIMEOUT) as response:
    #             response_text = await response.text() # Read text first for better error logging
    #             logger.debug(f"Jupiter V6 API raw response ({response.status}): {response_text[:500]}") # Log snippet
    #             if response.status == 200:
    #                 try:
    #                     return await response.json()
    #                 except aiohttp.ContentTypeError:
    #                     logger.error(f"Jupiter API V6 content type error. Response: {response_text}")
    #                     raise JupiterAPIError(f"Invalid JSON response from Jupiter V6 API. Status: {response.status}. Response: {response_text[:200]}", status_code=response.status, api_name="JupiterV6_Direct")
    #             else:
    #                 logger.error(f"Jupiter API V6 request failed with status {response.status}: {response_text}")
    #                 raise JupiterAPIError(f"Jupiter V6 API error. Status: {response.status}. Response: {response_text[:200]}", status_code=response.status, api_name="JupiterV6_Direct")
    #     except aiohttp.ClientError as e: # Handles timeouts, connection errors etc.
    #         logger.error(f"aiohttp client error during Jupiter V6 API request: {e}")
    #         raise JupiterAPIError(f"Network or client error during Jupiter V6 API request: {e}", api_name="JupiterV6_Direct")
    #     except asyncio.TimeoutError:
    #         logger.error(f"Timeout during Jupiter V6 API request to {url}")
    #         raise JupiterAPIError(f"Timeout during Jupiter V6 API request to {url}", api_name="JupiterV6_Direct")
    #     except Exception as e:
    #         logger.error(f"Unexpected error during Jupiter V6 API request: {e}", exc_info=True)
    #         raise JupiterAPIError(f"Unexpected error: {e}", api_name="JupiterV6_Direct")
    #
    #
    #    # Example usage of how record_transaction might be called internally if there were other trade types.
    #    # This is not directly related to Jupiter swap but general structure.
    #    # def record_manual_trade(self, pair_address: str, trade_type: str, amount: float, price: float, reason: str):
    #        details = {
    #            "pair_address": pair_address,
    #            "trade_type": trade_type,
    #            "amount": amount,
    #            "price": price,
    #            "reason": reason,
    #            "timestamp": time.time(),
    #            "source": "manual"
    #        }
    #        # Simplified result for manual trade logging
    #        result = {
    #            "success": True, 
    #            "signature": None, # No on-chain signature for purely manual log
    #            "message": f"Manual trade logged for {pair_address}."
    #        }
    #        self._record_transaction(result, details)
    #        logger.info(f"Manual trade for {pair_address} recorded.")

    # --- Methods for advanced order types (Limit, DCA) ---
    # These would use self.jupiter_client for interaction with Jupiter API
    # Placeholders for now, to be implemented based on todo/01-todo-core.md (Phase 3-4) or 03-todo-advanced-features.md
