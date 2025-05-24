import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.signature import Signature
from solana.rpc.commitment import Confirmed
from solders.fee_calculator import FeeCalculator
import base58
import os
import json
import aiohttp

from app.market.market_data import MarketDataProvider
from app.config import Config

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger("trading_engine")

class TradingEngine:
    """Moteur de trading optimisé pour exécuter des opérations sur les DEX Solana."""
    
    def __init__(self, wallet_path: str, rpc_url: Optional[str] = None):
        """
        Initialise le moteur de trading.
        
        Args:
            wallet_path: Chemin vers le fichier de clé du portefeuille
            rpc_url: URL du point de terminaison RPC Solana. Utilise Config.SOLANA_RPC_URL par défaut.
        """
        self.rpc_url = rpc_url if rpc_url is not None else Config.SOLANA_RPC_URL
        self.client = AsyncClient(self.rpc_url)
        self.wallet = self._initialize_wallet(wallet_path)
        self.market_data_provider = None
        self.last_transaction_signature = None
        self.transaction_history = []
        
    def _initialize_wallet(self, wallet_path: str) -> Keypair:
        """
        Initialise le portefeuille de manière sécurisée avec validation.
        Tente de charger depuis wallet_path, puis Config.BACKUP_WALLET_PATH, 
        puis Config.SOLANA_PRIVATE_KEY_BS58 (variable d'environnement).
        
        Args:
            wallet_path: Chemin principal vers le fichier de clé du portefeuille.
            
        Returns:
            Instance Keypair pour le portefeuille.
            
        Raises:
            ValueError: Si aucune méthode de chargement de portefeuille ne réussit.
        """
        primary_error = None
        # Attempt 1: Load from primary wallet_path
        try:
            logger.info(f"Attempting to load wallet from primary path: {wallet_path}")
            if not os.path.exists(wallet_path):
                raise FileNotFoundError(f"Primary wallet file not found: {wallet_path}")
            
            with open(wallet_path, 'r') as f:
                try: # JSON format (Solana CLI)
                    key_data = json.load(f)
                    if isinstance(key_data, list):
                        private_key_bytes = bytes(key_data)
                    else:
                        raise ValueError("Unrecognized key format in JSON file")
                except json.JSONDecodeError: # Try raw base58
                    f.seek(0) # Reset file pointer after failed json.load
                    content = f.read().strip()
                    try:
                        private_key_bytes = base58.b58decode(content)
                    except Exception as b58_e:
                        raise ValueError(f"Not a valid JSON or Base58 key file: {b58_e}")
            
            if len(private_key_bytes) != 64: # Solana private keys are typically 32 bytes, Keypair expects 64 (seed)
                                          # Keypair.from_secret_key expects 32 bytes or 64 for seed.
                                          # Solana CLI JSON is usually a list of 64 numbers (uint8 array for seed).
                                          # Raw base58 key is usually the 32-byte secret key.
                                          # Keypair.from_bytes() expects 64 bytes (private key + public key, or seed)
                                          # Let's clarify based on typical usage.
                                          # If it's a 32-byte secret, use Keypair.from_secret_key.
                                          # If it's from Solana CLI JSON (often 64 bytes), Keypair.from_seed_phrase_and_passphrase or from_seed may apply if it's a seed.
                                          # For now, assuming the loaded `private_key_bytes` are the 64-byte representation expected by Keypair.from_bytes or a 32-byte secret key.
                # If we have 32 bytes, it's likely the secret key part. Keypair.from_secret_key() handles this.
                # If we have 64 bytes from JSON, it's usually the full keypair bytes [secret_key (32) + public_key (32)] or a seed (64).
                # Keypair.from_bytes expects 64 bytes which are [secret_key (32 bytes) + public_key (32 bytes)].
                # Or it could be a 64-byte seed. For Solana CLI json, it's usually the 64-byte array representing the keypair.

                # Let's assume if it's 64 bytes it's the full keypair data as bytes
                # If it's 32 bytes it's the secret_key component
                if len(private_key_bytes) == 32: # This would be a raw secret key
                    keypair = Keypair.from_secret_key(private_key_bytes)
                elif len(private_key_bytes) == 64: # This could be seed or [secret+public]
                    # Solana CLI JSON format is typically the 64-byte array [secret_key + public_key]
                    # Keypair.from_bytes can take this.
                    keypair = Keypair.from_bytes(private_key_bytes) # This is likely if loading from JSON array of 64 numbers
                else:
                    raise ValueError(f"Invalid private key length: {len(private_key_bytes)}, expected 32 or 64 bytes")

            logger.info(f"Wallet initialized successfully from {wallet_path}. Address: {keypair.pubkey()}")
            return keypair
        except Exception as e:
            logger.error(f"Failed to initialize wallet from primary path {wallet_path}: {e}")
            primary_error = e

        # Attempt 2: Load from backup wallet_path if primary failed
        if Config.BACKUP_WALLET_PATH:
            try:
                logger.warning(f"Attempting to load wallet from backup path: {Config.BACKUP_WALLET_PATH}")
                if not os.path.exists(Config.BACKUP_WALLET_PATH):
                    raise FileNotFoundError(f"Backup wallet file not found: {Config.BACKUP_WALLET_PATH}")
                
                with open(Config.BACKUP_WALLET_PATH, 'r') as f:
                    try: # JSON format
                        key_data = json.load(f)
                        if isinstance(key_data, list):
                            private_key_bytes = bytes(key_data)
                        else: raise ValueError("Unrecognized key format in backup JSON")
                    except json.JSONDecodeError: # Raw base58
                        f.seek(0)
                        content = f.read().strip()
                        try: private_key_bytes = base58.b58decode(content)
                        except Exception as b58_e: raise ValueError(f"Backup not valid JSON or B58: {b58_e}")

                if len(private_key_bytes) == 32:
                    keypair = Keypair.from_secret_key(private_key_bytes)
                elif len(private_key_bytes) == 64:
                    keypair = Keypair.from_bytes(private_key_bytes)
                else:
                    raise ValueError(f"Invalid backup private key length: {len(private_key_bytes)}")
                
                logger.info(f"Wallet initialized successfully from backup {Config.BACKUP_WALLET_PATH}. Address: {keypair.pubkey()}")
                return keypair
            except Exception as backup_e:
                logger.error(f"Failed to initialize wallet from backup path {Config.BACKUP_WALLET_PATH}: {backup_e}")
        else:
            logger.info("No backup wallet path configured.")

        # Attempt 3: Load from environment variable (SOLANA_PRIVATE_KEY_BS58)
        if Config.SOLANA_PRIVATE_KEY_BS58:
            try:
                logger.warning("Attempting to load wallet from SOLANA_PRIVATE_KEY_BS58 environment variable.")
                private_key_bs58 = Config.SOLANA_PRIVATE_KEY_BS58
                private_key_bytes = base58.b58decode(private_key_bs58)
                
                # Solana private keys are 32 bytes. Keypair.from_secret_key takes these 32 bytes.
                if len(private_key_bytes) != 32: 
                    raise ValueError(f"Invalid private key length from env var: {len(private_key_bytes)}, expected 32 bytes for a Base58 secret key string.")
                
                keypair = Keypair.from_secret_key(private_key_bytes)
                logger.info(f"Wallet initialized successfully from SOLANA_PRIVATE_KEY_BS58. Address: {keypair.pubkey()}")
                return keypair
            except Exception as env_e:
                logger.error(f"Failed to initialize wallet from SOLANA_PRIVATE_KEY_BS58: {env_e}")
        else:
            logger.info("No SOLANA_PRIVATE_KEY_BS58 environment variable configured.")

        # If all attempts fail, raise a comprehensive error
        final_error_message = "All wallet initialization methods failed."
        if primary_error:
            final_error_message += f" Primary error: {str(primary_error)}."
        # Could add details about backup/env errors too if needed, but might be too verbose.
        logger.critical(final_error_message)
        raise ValueError(final_error_message)
            
    async def __aenter__(self):
        """Initialise les ressources asynchrones."""
        self.market_data_provider = MarketDataProvider()
        await self.market_data_provider.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Libère les ressources asynchrones."""
        if self.market_data_provider:
            await self.market_data_provider.__aexit__(exc_type, exc_val, exc_tb)
        await self.client.close()
            
    async def get_fee_for_message(self, transaction: Transaction) -> int:
        """
        Estime les frais pour une transaction avant exécution.
        
        Args:
            transaction: Transaction à analyser
            
        Returns:
            Frais estimés en lamports
        """
        try:
            # Convertir la transaction en message
            recent_blockhash = await self.client.get_latest_blockhash()
            transaction.recent_blockhash = recent_blockhash.value.blockhash
            
            # Obtenir l'estimation des frais
            fee_response = await self.client.get_fee_for_message(
                transaction.serialize_message()
            )
            
            if fee_response.value is None:
                # Utiliser une estimation de repli
                fee_calculator = FeeCalculator(Config.DEFAULT_FEE_PER_SIGNATURE_LAMPORTS)
                signatures_count = len(transaction.signatures)
                estimated_fee = fee_calculator.calculate_fee(transaction.serialize_message()) 
                logger.warning(f"Utilisation de l'estimation de repli des frais: {estimated_fee} lamports")
                return estimated_fee
                
            return fee_response.value
            
        except Exception as e:
            logger.error(f"Erreur lors de l'estimation des frais: {e}")
            # Valeur par défaut sécuritaire
            return Config.DEFAULT_FEE_PER_SIGNATURE_LAMPORTS * len(transaction.signatures)
            
    async def execute_swap(self, input_token_mint: str, output_token_mint: str, 
                           amount_in_usd: Optional[float] = None, 
                           amount_in_tokens: Optional[float] = None, 
                           slippage_bps: Optional[int] = None) -> Dict[str, Any]:
        """
        Exécute un swap entre deux tokens.
        Prioritise amount_in_tokens si fourni, sinon calcule à partir de amount_in_usd.
        
        Args:
            input_token_mint: Adresse du token d'entrée (e.g., USDC mint address).
            output_token_mint: Adresse du token de sortie.
            amount_in_usd: Montant à échanger, exprimé en USD. Sera converti en montant de token d'entrée.
            amount_in_tokens: Montant du token d'entrée à échanger. Prioritaire sur amount_in_usd.
            slippage_bps: Tolérance de slippage en points de base (BPS). Utilise Config.SLIPPAGE_BPS par défaut.
            
        Returns:
            Dictionnaire structuré: {'success': True/False, 'data': ..., 'error': ...}
        """
        current_slippage_bps = slippage_bps if slippage_bps is not None else Config.SLIPPAGE_BPS

        if amount_in_tokens is None and amount_in_usd is None:
            return {'success': False, 'error': "amount_in_tokens ou amount_in_usd doit être fourni.", 'data': None}
        
        if amount_in_tokens is not None and amount_in_tokens <= 0:
            return {'success': False, 'error': "amount_in_tokens doit être positif.", 'data': None}
        if amount_in_usd is not None and amount_in_usd <= 0:
             return {'success': False, 'error': "amount_in_usd doit être positif.", 'data': None}

        final_amount_in_tokens: float

        if amount_in_tokens is not None:
            final_amount_in_tokens = amount_in_tokens
            logger.info(f"Initiating swap: {final_amount_in_tokens} {input_token_mint} -> {output_token_mint} with slippage: {current_slippage_bps} BPS (using provided token amount)")
        elif amount_in_usd is not None:
            if not self.market_data_provider:
                return {'success': False, 'error': "MarketDataProvider non initialisé pour convertir USD en tokens.", 'data': None}
            
            # Obtenir le prix du token d'entrée pour calculer le montant en tokens
            price_response = await self.market_data_provider.get_token_price(input_token_mint)
            if not price_response['success'] or price_response['data'] is None or price_response['data'] <= 0:
                error_msg = f"Impossible d'obtenir le prix pour {input_token_mint} afin de convertir USD. Erreur: {price_response.get('error', 'Prix non disponible ou invalide')}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg, 'data': None}
            
            input_token_price_usd = price_response['data']
            final_amount_in_tokens = amount_in_usd / input_token_price_usd
            logger.info(f"Initiating swap: {amount_in_usd:.2f} USD ({final_amount_in_tokens:.6f} {input_token_mint} @ ${input_token_price_usd:.6f}/token) -> {output_token_mint} with slippage: {current_slippage_bps} BPS")
        else:
            # This case should be caught by the initial check, but as a safeguard:
            return {'success': False, 'error': "Logique de montant invalide.", 'data': None}

        try:
            # _get_swap_routes prend le montant en tokens du token d'entrée
            routes_response = await self._get_swap_routes(input_token_mint, output_token_mint, final_amount_in_tokens, current_slippage_bps)
            
            if not routes_response['success']:
                error_msg = f"Failed to get swap routes: {routes_response.get('error', 'Unknown error from _get_swap_routes')}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg, 'data': routes_response.get('data')} # Pass along partial data like the quote response itself

            routes = routes_response['data'] # This is now a list containing one route object from Jupiter /quote
            if not routes or not isinstance(routes, list) or len(routes) == 0:
                error_msg = f"No routes found in successful response from _get_swap_routes. Data: {routes}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg, 'data': None}

            # _select_best_quote expects a list of routes. Jupiter /quote gives one best route.
            # Our _get_swap_routes wraps it in a list.
            best_route = await self._select_best_quote(routes, final_amount_in_tokens) # _select_best_quote raises ValueError if no viable route
            
            # Construire la transaction de swap
            # This will be updated to return a structured response in the next step
            build_tx_response = await self._build_swap_transaction(best_route)
            # TODO: Adapt to structured response from _build_swap_transaction once implemented
            # For now, assume it returns transaction_bytes directly or raises an error.
            # transaction_bytes = build_tx_response['data']["serialized_transaction"]
            # transaction = Transaction.deserialize(transaction_bytes)
            
            # Placeholder for _build_swap_transaction structure until it's refactored
            if not build_tx_response or not build_tx_response.get("swapTransaction"):
                 error_msg = f"Failed to build swap transaction or invalid response: {build_tx_response}"
                 logger.error(error_msg)
                 return {'success': False, 'error': error_msg, 'data': build_tx_response}
            
            transaction_bytes_b64 = build_tx_response["swapTransaction"]
            transaction_bytes = base58.b58decode(transaction_bytes_b64) # Jupiter returns base64 encoded string
            transaction = Transaction.deserialize(transaction_bytes)
            
            estimated_fee = await self.get_fee_for_message(transaction)
            logger.info(f"Estimated fee for this transaction: {estimated_fee / 1_000_000_000:.6f} SOL")
            
            # Exécuter la transaction
            # This will be updated to return a structured response in the next step
            exec_tx_response = await self._execute_transaction(transaction_bytes_b64, build_tx_response.get("last_valid_block_height", 0))
            # TODO: Adapt to structured response from _execute_transaction once implemented
            
            # Placeholder for _execute_transaction structure until it's refactored
            if not exec_tx_response or not exec_tx_response.get("signature"): # Assuming simple dict with signature
                error_msg = f"Swap execution failed or invalid response: {exec_tx_response}"
                logger.error(error_msg)
                # Propagate the error if exec_tx_response itself is a structured error from a future refactor
                if isinstance(exec_tx_response, dict) and 'success' in exec_tx_response and not exec_tx_response['success']:
                    return exec_tx_response
                return {'success': False, 'error': error_msg, 'data': exec_tx_response}
            
            # Assuming exec_tx_response on success is like: {'signature': str, 'confirmation': ...}
            # For now, let's make it a structured success
            final_success_data = {
                'signature': exec_tx_response.get("signature"),
                'confirmation_details': exec_tx_response.get("confirmation_status"),
                'input_token': input_token_mint,
                'output_token': output_token_mint,
                'amount_in': final_amount_in_tokens,
                'route_info': best_route,
                'expected_amount_out': best_route.get("outAmount"),
                'fee_lamports': estimated_fee,
                'slippage_bps': current_slippage_bps
            }
            self._record_transaction(exec_tx_response, final_success_data) # _record_transaction needs to be adapted
            
            return {'success': True, 'data': final_success_data, 'error': None}
            
        except ValueError as ve: # Catch specific errors like from _select_best_quote
            logger.error(f"Swap execution failed due to ValueError: {str(ve)}", exc_info=True)
            return {'success': False, 'error': f"ValueError: {str(ve)}", 'data': None}
        except Exception as e:
            logger.error(f"Generic swap execution failed: {str(e)}", exc_info=True)
            try:
                logger.warning("Attempting fallback swap mechanism...")
                # Ensure _execute_fallback_swap also returns a structured response
                fallback_result = await self._execute_fallback_swap(input_token_mint, output_token_mint, final_amount_in_tokens, current_slippage_bps)
                if fallback_result['success']:
                    logger.info("Fallback swap successful.")
                else:
                    logger.error(f"Fallback swap also failed: {fallback_result.get('error')}")
                return fallback_result
            except Exception as fallback_e:
                logger.critical(f"Fallback swap mechanism itself failed: {fallback_e}", exc_info=True)
                return {'success': False, 'error': f"Primary swap failed ({type(e).__name__}): {str(e)}. Fallback failed ({type(fallback_e).__name__}): {str(fallback_e)}", 'data': None}
                
    async def _select_best_quote(self, routes: List[Dict[str, Any]], amount_in: float) -> Dict[str, Any]:
        """
        Sélectionne la meilleure offre en tenant compte du prix et des frais.
        
        Args:
            routes: Liste des routes disponibles
            amount_in: Montant d'entrée
            
        Returns:
            Meilleure route pour l'échange
        """
        if not routes:
            raise ValueError("Aucune route disponible pour cet échange")
            
        best_route = None
        best_effective_price = 0
        
        for route in routes:
            # Calculer le prix effectif (montant sortant moins frais estimés)
            out_amount = float(route["outAmount"])
            
            # Estimer les frais pour cette route
            try:
                tx_data = await self._build_swap_transaction(route)
                tx = Transaction.deserialize(tx_data["transaction"])
                estimated_fee = await self.get_fee_for_message(tx)
                
                # Convertir les frais dans la même unité que le montant sortant
                # (ceci est une simplification, nécessiterait normalement une conversion de devise)
                fee_adjustment = estimated_fee / 1_000_000  # Ajustement approximatif
                
                effective_price = out_amount - fee_adjustment
                
                if best_route is None or effective_price > best_effective_price:
                    best_route = route
                    best_effective_price = effective_price
                    
            except Exception as e:
                logger.warning(f"Erreur lors de l'évaluation de la route {route.get('market', 'inconnue')}: {e}")
                # Continuer avec la route suivante
                continue
                
        if best_route is None:
            raise ValueError("Impossible de trouver une route viable pour cet échange")
            
        return best_route
        
    async def _get_swap_routes(self, input_token_mint: str, output_token_mint: str, amount_in_tokens: float, slippage_bps: int) -> Dict[str, Any]:
        """
        Récupère les routes de swap de Jupiter.
        Args:
            input_token_mint: Adresse du token d'entrée.
            output_token_mint: Adresse du token de sortie.
            amount_in_tokens: Montant du token d'entrée à échanger (pas en USD).
            slippage_bps: Slippage en BPS.
        Returns:
            Réponse structurée de l'API Jupiter /quote.
        """
        if not self.market_data_provider:
             # Should not happen if TradingEngine is used via async with
            logger.error("MarketDataProvider not available in _get_swap_routes")
            return {'success': False, 'error': 'MarketDataProvider not available', 'data': None}

        # Obtenir les décimales du token d'entrée pour calculer amount_lamports
        token_info_response = await self.market_data_provider.get_token_info(input_token_mint)
        if not token_info_response['success'] or not token_info_response['data'] or 'decimals' not in token_info_response['data']:
            error_msg = f"Impossible d'obtenir les décimales pour {input_token_mint}. Erreur: {token_info_response.get('error', 'Informations sur le token non disponibles')}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg, 'data': None}
        
        input_decimals = token_info_response['data']['decimals']
        amount_lamports = int(amount_in_tokens * (10**input_decimals))

        logger.debug(f"Fetching swap routes for: {amount_in_tokens} ({amount_lamports} lamports) of {input_token_mint} to {output_token_mint}, slippage: {slippage_bps} BPS")

        # Appel à MarketDataProvider pour obtenir la quote de Jupiter
        # MarketDataProvider.get_jupiter_swap_quote gère la construction de l'URL et l'appel API
        quote_response = await self.market_data_provider.get_jupiter_swap_quote(
            input_mint=input_token_mint,
            output_mint=output_token_mint,
            amount_lamports=amount_lamports, # amount is in lamports
            slippage_bps=slippage_bps
        )

        if not quote_response['success']:
            logger.error(f"Échec de l'obtention de la quote Jupiter: {quote_response.get('error', 'Erreur inconnue')}")
            return {
                'success': False, 
                'error': f"Jupiter quote API error: {quote_response.get('error', 'Erreur inconnue')}", 
                'data': quote_response.get('data') # Pass along the raw response from Jupiter if available
            }
        
        # La réponse de get_jupiter_swap_quote contient déjà la structure de données de la route Jupiter
        # On l'enveloppe dans une liste car _select_best_quote s'attendait historiquement à une liste de routes.
        # Jupiter v6 /quote API retourne directement la meilleure route, donc on a une liste d'un élément.
        # Ensure routes_response['data'] is not None before wrapping in a list
        if quote_response['data'] is None:
            logger.error("Aucune donnée de route reçue de Jupiter malgré une réponse réussie.")
            return {'success': False, 'error': 'No route data from Jupiter despite success response', 'data': None}

        return {
            'success': True, 
            'data': [quote_response['data']], # Wrap the single Jupiter quote in a list
            'error': None
        }

    async def _build_swap_transaction(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construit la transaction de swap en utilisant l'API /swap de Jupiter.
        Args:
            route: La route de swap obtenue de l'API /quote (quoteResponse).
        Returns:
            Dictionnaire structuré: {'success': True/False, 'data': {'serialized_transaction_b64': str, 'last_valid_block_height': int}, 'error': 'message'}
        """
        logger.info(f"Building swap transaction for quote: {route.get('inputMint')}->{route.get('outputMint')}, outAmount: {route.get('outAmount')}")
        if not self.wallet:
            logger.error("Wallet not initialized for _build_swap_transaction.")
            return {'success': False, 'error': "Wallet not initialized", 'data': None}

        swap_api_url = Config.JUPITER_SWAP_URL
        
        payload = {
            "userPublicKey": str(self.wallet.pubkey()),
            "wrapAndUnwrapSol": True, # Default, can be configurable
            "quoteResponse": route, 
            "asLegacyTransaction": False, # Prefer versioned transactions
            # Optional: Add dynamicComputeUnitLimit, prioritizationFeeLamports from Config or dynamically
            # "dynamicComputeUnitLimit": True, 
            # "prioritizationFeeLamports": "auto" # or a specific value Config.JUPITER_PRIORITY_FEE_LAMPORTS
        }
        if Config.JUPITER_COMPUTE_UNIT_LIMIT_ENABLED:
            payload["dynamicComputeUnitLimit"] = True
        if Config.JUPITER_PRIORITY_FEE_LAMPORTS: # Can be "auto" or a number
            payload["prioritizationFeeLamports"] = Config.JUPITER_PRIORITY_FEE_LAMPORTS


        headers = {"Content-Type": "application/json"}
        if Config.JUPITER_API_KEY:
            headers["Authorization"] = f"Bearer {Config.JUPITER_API_KEY}"

        # Using MarketDataProvider's session if available and open, otherwise a new one
        session_to_use = None
        close_session_after = False
        if self.market_data_provider and self.market_data_provider.session and not self.market_data_provider.session.closed:
            session_to_use = self.market_data_provider.session
        else:
            session_to_use = aiohttp.ClientSession()
            close_session_after = True
            logger.debug("Created temporary ClientSession for Jupiter /swap call.")

        try:
            await self.market_data_provider._check_rate_limit("jupiter_swap") # Assume new category for swap
            
            logger.debug(f"Jupiter /swap request: POST {swap_api_url}, payload: {json.dumps(payload)[:200]}...") # Log partial payload
            async with session_to_use.post(swap_api_url, json=payload, headers=headers, timeout=Config.API_TIMEOUT_SECONDS_JUPITER_SWAP) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        swap_data = json.loads(response_text)
                        # Jupiter /swap returns: { swapTransaction: "base64_encoded_transaction", lastValidBlockHeight: number }
                        if "swapTransaction" not in swap_data or "lastValidBlockHeight" not in swap_data:
                            err_msg = f"Jupiter Swap API response missing 'swapTransaction' or 'lastValidBlockHeight'. Response: {swap_data}"
                            logger.error(err_msg)
                            return {'success': False, 'error': err_msg, 'data': swap_data}
                        
                        logger.info(f"Successfully built swap transaction. LastValidBlockHeight: {swap_data.get('lastValidBlockHeight')}")
                        return {
                            'success': True, 
                            'data': {
                                'serialized_transaction_b64': swap_data["swapTransaction"], 
                                'last_valid_block_height': swap_data["lastValidBlockHeight"],
                                'raw_response': swap_data
                            }, 
                            'error': None
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Jupiter Swap API JSONDecodeError. URL: {swap_api_url}. Error: {str(e)}. Response: {response_text}", exc_info=True)
                        return {'success': False, 'error': f"JSONDecodeError: {str(e)}", 'data': {'response_text': response_text}}
                else:
                    error_message = f"Jupiter Swap API returned status {response.status}"
                    try: # Try to parse error from Jupiter
                        error_payload = json.loads(response_text)
                        error_detail = error_payload.get('message', error_payload.get('error', response_text))
                        if isinstance(error_detail, dict) and 'message' in error_detail: # Nested error
                           error_detail = error_detail['message']
                        error_message += f": {error_detail}"
                    except json.JSONDecodeError:
                        error_message += f": {response_text}"
                    logger.error(f"{error_message}. URL: {swap_api_url}.") # Payload logging can be verbose, logged above partially
                    return {'success': False, 'error': error_message, 'data': {'response_text': response_text}}

        except aiohttp.ClientError as e:
            logger.error(f"Jupiter Swap API ClientError. URL: {swap_api_url}. Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"ClientError: {str(e)}", 'data': None}
        except asyncio.TimeoutError:
            logger.error(f"Jupiter Swap API Timeout. URL: {swap_api_url}", exc_info=True)
            return {'success': False, 'error': "TimeoutError", 'data': None}
        except Exception as e:
            logger.error(f"Unexpected error in _build_swap_transaction. URL: {swap_api_url}. Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"UnexpectedError: {str(e)}", 'data': None}
        finally:
            if close_session_after and session_to_use:
                await session_to_use.close()
                logger.debug("Closed temporary ClientSession for Jupiter /swap call.")

    async def _execute_transaction(self, serialized_transaction_b64: str, last_valid_block_height: int) -> Dict[str, Any]:
        """
        Signe, envoie la transaction VersionedTransaction au réseau Solana, et attend la confirmation.
        Args:
            serialized_transaction_b64: La transaction sérialisée en base64 obtenue de Jupiter /swap.
            last_valid_block_height: La dernière hauteur de bloc valide pour la transaction.
        Returns:
            Dictionnaire structuré: {'success': True/False, 'data': {'signature': str, 'confirmation_response': ...}, 'error': 'message'}
        """
        if not self.wallet:
            logger.error("Wallet not initialized for _execute_transaction.")
            return {'success': False, 'error': "Wallet not initialized", 'data': None}
        
        # Ensure AsyncClient is healthy
        if not self.client or not hasattr(self.client, 'http_client') or (hasattr(self.client, 'http_client') and self.client.http_client and self.client.http_client.closed):
            logger.warning("AsyncClient was closed or not initialized. Recreating for _execute_transaction.")
            if hasattr(self.client, 'http_client') and self.client.http_client: # Ensure client has http_client attribute
                 await self.client.close() 
            self.client = AsyncClient(self.rpc_url)

        try:
            # Deserialize the VersionedTransaction
            try:
                tx_bytes = base58.b58decode(serialized_transaction_b64)
                transaction = Transaction.deserialize(tx_bytes)
            except (TypeError, ValueError) as e_b64:
                logger.error(f"Error decoding/deserializing base64 swapTransaction: {str(e_b64)}", exc_info=True)
                return {'success': False, 'error': f"TransactionDeserializeError: {str(e_b64)}", 'data': None}

            # Sign the VersionedTransaction with our wallet
            # Jupiter /swap endpoint returns a transaction that needs to be signed by the user.
            transaction.sign([self.wallet]) # VersionedTransaction.sign takes a list of signers

            # Send the transaction
            logger.info(f"Sending signed VersionedTransaction to Solana network...")
            # The `send_transaction` method of AsyncClient handles both Transaction and VersionedTransaction.
            send_tx_resp = await self.client.send_transaction(transaction, opts=self.client.commitment_opts(skip_preflight=Config.SOLANA_SKIP_PREFLIGHT))
            signature_obj = send_tx_resp.value 
            signature_str = str(signature_obj)
            logger.info(f"Transaction sent. Signature: {signature_str}")
            self.last_transaction_signature = signature_str
            self.transaction_history.append(signature_str) # Keep track

            # Confirm the transaction
            logger.info(f"Waiting for transaction confirmation for {signature_str} (LastValidBlockHeight: {last_valid_block_height})...")
            
            # Using confirm_transaction with last_valid_block_height for versioned transactions
            confirmation_resp = await self.client.confirm_transaction(
                signature_obj,
                commitment=Config.SOLANA_COMMITMENT, 
                last_valid_block_height=last_valid_block_height,
                sleep_seconds=Config.SOLANA_CONFIRMATION_SLEEP_SECONDS 
            )
            
            # confirmation_resp.value is a list of RpcResponseContext(RpcSimulateTransactionResult)
            # We are interested in confirmation_resp.value[0].err
            if confirmation_resp.value and confirmation_resp.value[0].err is None:
                logger.info(f"Transaction confirmed successfully: {signature_str}")
                return {'success': True, 'data': {'signature': signature_str, 'confirmation_status': confirmation_resp.value[0]}, 'error': None}
            elif confirmation_resp.value and confirmation_resp.value[0].err:
                error_detail = f"Transaction failed confirmation: {confirmation_resp.value[0].err}"
                logger.error(f"{error_detail}. Signature: {signature_str}. Logs: {confirmation_resp.value[0].logs}")
                return {'success': False, 'error': error_detail, 'data': {'signature': signature_str, 'confirmation_response': confirmation_resp.value[0]}}
            else: 
                # This case means the confirmation response itself was unusual or empty.
                logger.error(f"Transaction confirmation unclear for {signature_str}. Raw response: {confirmation_resp}")
                return {'success': False, 'error': "Transaction confirmation unclear or timed out waiting for block height.", 
                        'data': {'signature': signature_str, 'raw_response': confirmation_resp.to_json() if confirmation_resp else None}}

        except solana.rpc.core.RPCException as rpc_e: # Catch specific Solana RPC errors
            logger.error(f"Solana RPCException during transaction execution: {str(rpc_e)}", exc_info=True)
            # Try to extract more details if possible, e.g. from rpc_e.args or specific RPC error codes
            error_message = f"Solana RPCException: {str(rpc_e)}"
            # Example: if "BlockhashNotFound" in str(rpc_e): ...
            return {'success': False, 'error': error_message, 'data': None}
        except (aiohttp.ClientError, ConnectionRefusedError, aiohttp.ClientConnectorError) as conn_e:
            error_type = type(conn_e).__name__
            logger.error(f"Solana RPC {error_type}: {str(conn_e)}. URL: {self.rpc_url}", exc_info=True)
            return {'success': False, 'error': f"Solana RPC {error_type}: {str(conn_e)}", 'data': None}
        except asyncio.TimeoutError: 
            logger.error(f"Solana RPC Timeout while executing transaction. URL: {self.rpc_url}", exc_info=True)
            return {'success': False, 'error': "Solana RPC Timeout", 'data': None}
        except Exception as e: 
            error_type = type(e).__name__
            logger.error(f"Unexpected error during Solana transaction execution ({error_type}): {str(e)}", exc_info=True)
            return {'success': False, 'error': f"Solana transaction execution error ({error_type}): {str(e)}", 'data': None}

    async def _execute_fallback_swap(self, input_token: str, output_token: str, 
                                   amount_in: float, slippage_bps: int) -> Dict[str, Any]:
        """
        Implémente un mécanisme de repli si le swap principal échoue.
        Actuellement, cela pourrait tenter une route de Jupiter différente si l'API en fournissait plusieurs,
        ou utiliser un autre DEX (non implémenté). Pour l'instant, c'est un placeholder.
        Returns a structured response.
        """
        logger.warning(f"Fallback swap for {amount_in} {input_token} to {output_token} initiated.")
        # TODO: Implement actual fallback logic.
        # This might involve:
        # 1. Trying a different quote from Jupiter if multiple were fetched (not current design of _get_swap_routes).
        # 2. Trying a different DEX (e.g., Raydium, Orca) via a different adapter if available.
        # 3. Adjusting slippage or amount slightly.
        
        # For now, simply log and return failure.
        error_message = "Fallback swap mechanism not fully implemented."
        logger.error(error_message)
        return {'success': False, 'error': error_message, 'data': None}

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
