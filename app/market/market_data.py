import aiohttp
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import Config
from app.utils.jupiter_api_client import JupiterApiClient
from app.utils.exceptions import (
    JupiterAPIError, DexScreenerAPIError, SolanaTransactionError, 
    TransactionExpiredError, NumerusXBaseError
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("market_data")

class MarketDataProvider:
    """Classe centralisée pour la gestion des données de marché provenant de différentes sources."""
    
    def __init__(self):
        """
        Initialise le fournisseur de données de marché.
        Utilise les paramètres de cache et de rate limit depuis Config.
        """
        self.session = None
        self.config = Config() # Store config instance

        # Initialize JupiterApiClient
        # It's crucial that SOLANA_PRIVATE_KEY_BS58 and SOLANA_RPC_URL are correctly set in Config
        # The TODO suggests a WALLET_PRIVATE_KEY_BS58_FOR_DATA_API for data-only operations.
        # We'll use the general SOLANA_PRIVATE_KEY_BS58 for now, assuming it has sufficient permissions
        # or that a specific data API key will be added to Config later if needed.
        self.jupiter_client: Optional[JupiterApiClient] = None
        if self.config.SOLANA_PRIVATE_KEY_BS58 and self.config.SOLANA_RPC_URL:
            try:
                self.jupiter_client = JupiterApiClient(
                    private_key_bs58=self.config.SOLANA_PRIVATE_KEY_BS58, # Or a specific data API key from config
                    rpc_url=self.config.SOLANA_RPC_URL,
                    config=self.config
                )
                logger.info("JupiterApiClient initialized successfully in MarketDataProvider.")
            except Exception as e:
                logger.error(f"Failed to initialize JupiterApiClient in MarketDataProvider: {e}", exc_info=True)
                # Proceeding without jupiter_client, Jupiter-dependent methods will fail gracefully.
        else:
            logger.warning("JupiterApiClient cannot be initialized in MarketDataProvider: SOLANA_PRIVATE_KEY_BS58 or SOLANA_RPC_URL missing in Config.")

        # Cache pour les différents types de données
        self.price_cache = TTLCache(maxsize=Config.MARKET_DATA_CACHE_MAX_SIZE, ttl=Config.MARKET_DATA_CACHE_TTL_SECONDS)
        self.token_info_cache = TTLCache(maxsize=Config.MARKET_DATA_CACHE_MAX_SIZE, ttl=Config.MARKET_DATA_CACHE_TTL_SECONDS * 5)
        self.liquidity_cache = TTLCache(maxsize=Config.MARKET_DATA_CACHE_MAX_SIZE, ttl=Config.MARKET_DATA_CACHE_TTL_SECONDS // 2)
        self.pairs_cache = TTLCache(maxsize=Config.MARKET_DATA_CACHE_MAX_SIZE // 10, ttl=Config.MARKET_DATA_CACHE_TTL_SECONDS * 10) # Cache for pairs
        self.historical_data_cache = TTLCache(maxsize=Config.MARKET_DATA_CACHE_MAX_SIZE // 2, ttl=Config.MARKET_DATA_CACHE_TTL_SECONDS * 2) # Cache for historical data
        self.jupiter_quote_cache = TTLCache(maxsize=Config.MARKET_DATA_CACHE_MAX_SIZE // 5, ttl=Config.MARKET_DATA_CACHE_TTL_SECONDS // 4) # Cache for Jupiter quotes
        
        # Initialiser les limites de taux à partir de Config
        self.rate_limits = {}
        for api_name, limits in Config.API_RATE_LIMITS.items():
            self.rate_limits[api_name] = {
                "calls": 0,
                "last_reset": time.time(),
                "limit": limits.get("limit", 50), # Default limit if not specified
                "window_seconds": limits.get("window_seconds", 60), # Default window if not specified
                "wait_seconds": limits.get("default_wait", Config.DEFAULT_API_RATE_LIMIT_WAIT_SECONDS) # Default wait
            }

    async def __aenter__(self):
        """Initialisation du contexte asynchrone."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage du contexte asynchrone."""
        if self.session:
            await self.session.close()
            
    async def get_token_price(self, token_address: str, reference_token: str = "USDC") -> Dict[str, Any]:
        """
        Obtient le prix d'un token via plusieurs sources avec mécanisme de repli.
        Utilise le cache.
        
        Args:
            token_address: Adresse du token Solana
            reference_token: Token de référence pour le prix
            
        Returns:
            Dict contenant les informations de prix ou une erreur structurée.
            Exemple succès: {'success': True, 'error': None, 'data': {'price': 0.123, ...}}
            Exemple échec: {'success': False, 'error': 'Message d\'erreur', 'data': None}
        """
        cache_key = f"{token_address}_{reference_token}_price"
        cached_value = self.price_cache.get(cache_key)
        if cached_value:
            return {'success': True, 'error': None, 'data': cached_value}
            
        final_errors = [] # Collect error messages from different sources
        
        # Essayer Jupiter d'abord
        try:
            logger.debug(f"Fetching price for {token_address} from JupiterSDK")
            jupiter_result = await self._get_jupiter_price(token_address, reference_token)
            if jupiter_result.get('success'):
                self.price_cache[cache_key] = jupiter_result['data']
                return jupiter_result
            else:
                final_errors.append(f"JupiterSDK: {jupiter_result.get('error', 'Unknown error from JupiterSDK')}")
                logger.warning(f"Failed to get price from JupiterSDK for {token_address}: {jupiter_result.get('error')}")
        except JupiterAPIError as e:
            final_errors.append(f"JupiterSDK Error: {str(e)}")
            logger.warning(f"JupiterAPIError for {token_address} price: {e}")
        except Exception as e: # Catch any other unexpected error from _get_jupiter_price itself
            final_errors.append(f"JupiterSDK Unexpected Error: {str(e)}")
            logger.error(f"Unexpected error in _get_jupiter_price call for {token_address}: {e}", exc_info=True)

        # Fallback sur DexScreener
        try:
            logger.debug(f"Fetching price for {token_address} from DexScreener (fallback)")
            # _get_dexscreener_price now raises DexScreenerAPIError on failure
            dexscreener_result_data = await self._get_dexscreener_price(token_address)
            # If _get_dexscreener_price returns successfully, it implies success is True
            # and data is in dexscreener_result_data['data']
            if dexscreener_result_data.get('success'): # Check for safety, though it should raise on error
                self.price_cache[cache_key] = dexscreener_result_data['data']
                return dexscreener_result_data # This is already {'success': True, 'data': ...}
            else:
                # This path might not be hit if _get_dexscreener_price always raises on error
                final_errors.append(f"DexScreener: {dexscreener_result_data.get('error', 'Unknown error from DexScreener after successful call')}")
                logger.warning(f"_get_dexscreener_price returned success=false for {token_address}: {dexscreener_result_data.get('error')}")

        except DexScreenerAPIError as e:
            final_errors.append(f"DexScreener Error: {str(e)}")
            logger.warning(f"DexScreenerAPIError for {token_address} price: {e}")
        except Exception as e: # Catch any other unexpected error
            final_errors.append(f"DexScreener Unexpected Error: {str(e)}")
            logger.error(f"Unexpected error in _get_dexscreener_price call for {token_address}: {e}", exc_info=True)
            
        # If all sources failed
        full_error_message = f"Impossible d'obtenir le prix pour {token_address}. Erreurs: {'; '.join(final_errors) if final_errors else 'Aucune source n\'a pu fournir de prix.'}"
        logger.error(full_error_message)
        return {'success': False, 'error': full_error_message, 'data': None}
        
    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Obtient les informations d'un token via plusieurs sources (Jupiter, puis DexScreener).
        Utilise le cache.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Dict contenant les informations du token ou une erreur structurée.
            Exemple succès: {'success': True, 'error': None, 'data': {'address': '...', ...}}
            Exemple échec: {'success': False, 'error': 'Message d\'erreur', 'data': None}
        """
        cache_key = f"{token_address}_info"
        cached_value = self.token_info_cache.get(cache_key)
        if cached_value:
            return {'success': True, 'error': None, 'data': cached_value}
            
        final_errors = []

        # Try Jupiter first
        try:
            logger.debug(f"Fetching token info for {token_address} from JupiterSDK")
            jupiter_result = await self._get_jupiter_token_info(token_address)
            if jupiter_result.get('success'):
                self.token_info_cache[cache_key] = jupiter_result['data']
                return jupiter_result
            else:
                final_errors.append(f"JupiterSDK: {jupiter_result.get('error', 'Unknown error from JupiterSDK token info')}")
                logger.warning(f"Failed to get token info from JupiterSDK for {token_address}: {jupiter_result.get('error')}")
        except JupiterAPIError as e:
            final_errors.append(f"JupiterSDK Error: {str(e)}")
            logger.warning(f"JupiterAPIError for {token_address} token info: {e}")
        except Exception as e:
            final_errors.append(f"JupiterSDK Unexpected Error: {str(e)}")
            logger.error(f"Unexpected error in _get_jupiter_token_info call for {token_address}: {e}", exc_info=True)
        
        # Fallback to DexScreener (this part was previously making direct calls, now should rely on a refactored _get_dexscreener_token_info or adapt)
        # Assuming the DexScreener part of get_token_info was already refactored to use _get_dexscreener_info and raise DexScreenerAPIError
        # For now, I will adapt the existing DexScreener logic within get_token_info to raise/catch DexScreenerAPIError directly here.
        # This section previously contained direct aiohttp calls for DexScreener token info.
        # It needs to be refactored to use a helper that raises DexScreenerAPIError or handle it here.

        # Let's assume we make a call to a hypothetical _get_dexscreener_token_info_via_api that might raise DexScreenerAPIError
        # If such a helper doesn't exist, the direct DexScreener call logic within this method needs its try-except blocks updated.
        # The previous edit modified the DexScreener part within this function to raise DexScreenerAPIError.
        # So, we will add a try-except block for that.

        try:
            logger.debug(f"Fetching token info for {token_address} from DexScreener (fallback within get_token_info)")
            await self._check_rate_limit("dexscreener") # Keep rate limit for direct dexscreener calls if any
            if not self.session or self.session.closed: 
                self.session = aiohttp.ClientSession()
            
            ds_token_url = f"{self.config.DEXSCREENER_API_URL}/latest/dex/tokens/{token_address}"
            logger.debug(f"DexScreener token info request (direct): GET {ds_token_url}")

            async with self.session.get(ds_token_url, timeout=self.config.API_TIMEOUT_SECONDS) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        ds_api_data = json.loads(response_text)
                        if ds_api_data.get("pairs") and isinstance(ds_api_data["pairs"], list) and len(ds_api_data["pairs"]) > 0:
                            best_pair_for_info = sorted(
                                [p for p in ds_api_data["pairs"] if p.get("liquidity", {}).get("usd") is not None],
                                key=lambda x: float(x["liquidity"]["usd"]), 
                                reverse=True
                            )
                            if best_pair_for_info:
                                token_data = self._convert_dexscreener_format(best_pair_for_info[0], is_token_info=True)
                                if token_data and token_data.get("address"):
                                    self.token_info_cache[cache_key] = token_data
                                    return {'success': True, 'error': None, 'data': token_data, 'source': 'dexscreener'}
                                else:
                                    raise DexScreenerAPIError("Failed to convert DexScreener data or address missing (direct call)", original_exception=ValueError("Converted data invalid"))
                            else:
                                raise DexScreenerAPIError("No pairs with USD liquidity found on DexScreener for token info (direct call)")
                        else:
                            raise DexScreenerAPIError("No pairs array or empty pairs in DexScreener response (direct call)")
                    except json.JSONDecodeError as e:
                        raise DexScreenerAPIError(f"JSONDecodeError from DexScreener (direct call): {str(e)}", original_exception=e)
                else:
                    raise DexScreenerAPIError(f"DexScreener API returned status {response.status} (direct call)", status_code=response.status, original_exception=ValueError(response_text))
        except DexScreenerAPIError as e:
            final_errors.append(f"DexScreener Error: {str(e)}")
            logger.warning(f"DexScreenerAPIError for {token_address} token info (direct call): {e}")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            final_errors.append(f"DexScreener Network Error: {str(e)}")
            logger.warning(f"DexScreener network error for {token_address} token info (direct call): {e}")
        except Exception as e: # Catch any other unexpected errors from DexScreener direct call
            final_errors.append(f"DexScreener Unexpected Error: {str(e)}")
            logger.error(f"Unexpected error in DexScreener direct call for {token_address} token info: {e}", exc_info=True)
        
        full_error_message = f"Impossible d'obtenir les infos pour {token_address}. Erreurs: {'; '.join(final_errors) if final_errors else 'Aucune source n\'a pu fournir les infos.'}"
        logger.error(full_error_message)
        return {'success': False, 'error': full_error_message, 'data': None}

    async def get_liquidity_data(self, token_address: str, pool_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtient les données de liquidité pour un token.
        
        Args:
            token_address: Adresse du token
            pool_address: Adresse optionnelle du pool
            
        Returns:
            Données de liquidité normalisées ou une erreur structurée.
            Exemple succès: {'success': True, 'error': None, 'data': {'liquidity_usd': 100000, ...}}
            Exemple échec: {'success': False, 'error': 'Message d\'erreur', 'data': None}
        """
        cache_key = f"{token_address}_{pool_address}_liquidity" if pool_address else f"{token_address}_liquidity"
        
        cached_value = self.liquidity_cache.get(cache_key)
        if cached_value:
            return {'success': True, 'error': None, 'data': cached_value}
            
        liquidity_result = None
        error_message = "Failed to get liquidity data"

        try:
            if pool_address:
                logger.debug(f"Fetching specific pool liquidity for {token_address}, pool {pool_address}")
                liquidity_result = await self._get_specific_pool_liquidity(token_address, pool_address)
            else:
                logger.debug(f"Fetching best liquidity source for {token_address}")
                liquidity_result = await self._get_best_liquidity_source(token_address)
            
            if liquidity_result and liquidity_result.get('success'):
                self.liquidity_cache[cache_key] = liquidity_result['data']
                return liquidity_result
            else:
                error_message = liquidity_result.get('error', error_message) if liquidity_result else error_message
                logger.error(f"Échec de la récupération des données de liquidité pour {token_address}: {error_message}")
                return {'success': False, 'error': f"Liquidity fetch failed: {error_message}", 'data': None}

        except Exception as e:
            logger.error(f"Exception in get_liquidity_data for {token_address}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error fetching liquidity: {str(e)}", 'data': None}
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def _get_jupiter_price(self, token_address: str, reference_token: str) -> Dict[str, Any]:
        """
        Obtient le prix d'un token via JupiterApiClient.
        Returns a structured dict {'success': True/False, 'data': ..., 'error': ...}
        """
        if not self.jupiter_client:
            return {'success': False, 'error': "JupiterApiClient not initialized", 'data': None}

        logger.debug(f"Fetching price for {token_address} vs {reference_token} using JupiterApiClient")
        
        try:
            # JupiterApiClient.get_prices now returns data directly or raises JupiterAPIError.
            price_data_sdk = await self.jupiter_client.get_prices(token_ids_list=[token_address], vs_token_str=reference_token)
            
            if price_data_sdk: # price_data_sdk is the direct response from the SDK call
                token_price_info = price_data_sdk.get(token_address)
                if token_price_info and isinstance(token_price_info.get("price"), (float, int)):
                    price_info = {
                        'price': token_price_info["price"],
                        'token_address': token_address,
                        'reference_token': reference_token,
                        'source': 'jupiter_sdk',
                        'id': token_price_info.get('id'),
                        'mintSymbol': token_price_info.get('mintSymbol'),
                        'vsTokenSymbol': token_price_info.get('vsTokenSymbol'),
                        'raw_jupiter_data': token_price_info
                    }
                    logger.info(f"Price from Jupiter SDK for {token_address} vs {reference_token}: {price_info['price']}")
                    return {'success': True, 'error': None, 'data': price_info}
                else:
                    error_msg = f"Price data not found or invalid for {token_address} in Jupiter SDK response: {price_data_sdk}"
                    logger.warning(error_msg)
                    return {'success': False, 'error': error_msg, 'data': None}
            else:
                # This case should ideally not be hit if jupiter_client.get_prices raises on no data or error.
                error_msg = f"No data received from Jupiter SDK for {token_address} price."
                logger.warning(error_msg)
                return {'success': False, 'error': error_msg, 'data': None}
        except JupiterAPIError as e:
            error_msg = f"JupiterAPIError when fetching price for {token_address} vs {reference_token}: {e}"
            logger.warning(error_msg)
            return {'success': False, 'error': str(e), 'data': None, 'details': e} # Keep original exception detail
        except Exception as e: # Catch any other unexpected error from the call
            error_msg = f"Unexpected error fetching price from Jupiter SDK for {token_address}: {e}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': str(e), 'data': None, 'details': e}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def _get_dexscreener_price(self, token_address: str) -> Dict[str, Any]:
        """Récupère le prix d'un token depuis DexScreener API."""
        await self._check_rate_limit("dexscreener")
        
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
            
        # DexScreener API for token pairs
        url = f"{Config.DEXSCREENER_API_URL}/latest/dex/tokens/{token_address}/pools?include=dexId,baseToken,quoteToken,liquidity,priceUsd,volume" # More targeted query
        logger.debug(f"DexScreener price request: GET {url}")

        try:
            async with self.session.get(url, timeout=Config.API_TIMEOUT_SECONDS) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        logger.debug(f"DexScreener price response data: {data}")

                        if not data.get("pools") or not isinstance(data["pools"], list) or len(data["pools"]) == 0:
                            logger.warning(f"No pools found for token {token_address} on DexScreener: {data}")
                            return {'success': False, 'error': f"no_pools_found_for_token: {token_address}", 'data': None, 'source': 'dexscreener'}

                        # Select the best pool (e.g., highest liquidity USD)
                        # Note: Jupiter's /price is simpler as it resolves the best price across pools.
                        # DexScreener's /tokens/{token}/pools gives multiple options.
                        # We might want to refine this logic to iterate or pick the most liquid pool against USDC/SOL.
                        best_pool = None
                        highest_liquidity = -1

                        for pool in data["pools"]:
                            # Prefer pools against common quote tokens like USDC, USDT, SOL
                            # and ensure priceUsd and liquidity.usd are present
                            quote_symbol = pool.get("quoteToken", {}).get("symbol", "").upper()
                            liquidity_usd_str = pool.get("liquidity", {}).get("usd")
                            price_usd_str = pool.get("priceUsd")

                            if price_usd_str and liquidity_usd_str:
                                try:
                                    current_liquidity_usd = float(liquidity_usd_str)
                                    if quote_symbol in ["USDC", "USDT", "SOL", "RAY", "JUP", "WIF"] and current_liquidity_usd > highest_liquidity: # Added more common quote tokens
                                        highest_liquidity = current_liquidity_usd
                                        best_pool = pool
                                except ValueError:
                                    logger.warning(f"Could not parse liquidity or price for pool {pool.get('pairAddress')} for token {token_address}")
                                    continue
                        
                        if not best_pool: # If no preferred pool found, take the first one with priceUsd
                            for pool in data["pools"]:
                                if pool.get("priceUsd"):
                                    best_pool = pool
                                    logger.debug(f"No preferred quote token pool found for {token_address}, using first available pool: {best_pool.get('pairAddress')}")
                                    break
                            
                        if not best_pool:
                            logger.warning(f"No suitable pool with priceUsd found for token {token_address} on DexScreener after filtering.")
                            return {'success': False, 'error': f"no_suitable_pool_found_for_token: {token_address}", 'data': None, 'source': 'dexscreener'}


                        # Normalize DexScreener data (this might be a separate helper)
                        price_data = self._convert_dexscreener_format(best_pool, is_token_info=False) # is_token_info=False for price context
                        
                        if price_data.get("price") is None:
                            logger.warning(f"DexScreener returned null price for {token_address} from pool {best_pool.get('pairAddress')}")
                            return {'success': False, 'error': f"null_price_from_selected_pool: {token_address}", 'data': None, 'source': 'dexscreener'}

                        return {'success': True, 'error': None, 'data': price_data, 'source': 'dexscreener'}
                    except json.JSONDecodeError as e:
                        logger.error(f"DexScreener Price API JSONDecodeError for {token_address} at {url}: {str(e)}. Response: {response_text}")
                        raise DexScreenerAPIError(f"JSONDecodeError from DexScreener: {str(e)}", original_exception=e)
                else:
                    logger.warning(f"DexScreener Price API for {token_address} returned status {response.status}: {response_text} for URL {url}")
                    raise DexScreenerAPIError(f"DexScreener API returned status {response.status}", status_code=response.status, original_exception=ValueError(response_text))

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"DexScreener Price API ClientError for {token_address} at {url}: {str(e)}", exc_info=True)
            raise DexScreenerAPIError(f"Communication error with DexScreener: {str(e)}", original_exception=e)
        except DexScreenerAPIError: # Re-raise if already processed
            raise
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error in _get_dexscreener_price for {token_address} at {url}: {str(e)}", exc_info=True)
            raise DexScreenerAPIError(f"Unexpected error processing DexScreener price data: {str(e)}", original_exception=e)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def _get_jupiter_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Obtient les informations d'un token via JupiterApiClient.
        Returns a structured dict {'success': True/False, 'data': ..., 'error': ...}
        """
        if not self.jupiter_client:
            return {'success': False, 'error': "JupiterApiClient not initialized", 'data': None, 'source': 'jupiter_sdk'}

        logger.debug(f"Fetching token info for {token_address} using JupiterApiClient")
        
        try:
            # JupiterApiClient.get_token_info_list now returns data directly or raises JupiterAPIError.
            token_info_list_sdk = await self.jupiter_client.get_token_info_list(mint_address_list=[token_address])

            if token_info_list_sdk and isinstance(token_info_list_sdk, list) and len(token_info_list_sdk) > 0:
                token_info_sdk = token_info_list_sdk[0]
                if token_info_sdk.get("address") == token_address or token_info_sdk.get("mint") == token_address:
                    formatted_token_info = {
                        'address': token_info_sdk.get("address", token_address),
                        'name': token_info_sdk.get("name"),
                        'symbol': token_info_sdk.get("symbol"),
                        'decimals': token_info_sdk.get("decimals"),
                        'logoURI': token_info_sdk.get("logoURI"),
                        'tags': token_info_sdk.get("tags", []),
                        'source': 'jupiter_sdk',
                        'raw_jupiter_data': token_info_sdk
                    }
                    if formatted_token_info.get('decimals') is None:
                        error_msg = f"Crucial 'decimals' field missing in Jupiter SDK token info for {token_address}: {token_info_sdk}"
                        logger.warning(error_msg)
                        # Return error dict, as this method is expected to by its callers (get_token_info)
                        return {'success': False, 'error': error_msg, 'data': None, 'source': 'jupiter_sdk'}

                    logger.info(f"Token info from Jupiter SDK for {token_address}: Symbol={formatted_token_info['symbol']}, Decimals={formatted_token_info['decimals']}")
                    return {'success': True, 'error': None, 'data': formatted_token_info}
                else:
                    error_msg = f"Token info mismatch or not found for {token_address} in Jupiter SDK response: {token_info_list_sdk}"
                    logger.warning(error_msg)
                    return {'success': False, 'error': error_msg, 'data': None, 'source': 'jupiter_sdk'}
            elif token_info_list_sdk: # Success from SDK but data is not a list or is empty (or not as expected)
                error_msg = f"Jupiter SDK token info response for {token_address} was successful but data format unexpected: {token_info_list_sdk}"
                logger.warning(error_msg)
                return {'success': False, 'error': error_msg, 'data': None, 'source': 'jupiter_sdk'}
            else: # Should be caught by JupiterAPIError if SDK call fails
                 error_msg = f"No data received from Jupiter SDK for {token_address} token info."
                 logger.warning(error_msg)
                 return {'success': False, 'error': error_msg, 'data': None, 'source': 'jupiter_sdk'}
        except JupiterAPIError as e:
            error_msg = f"JupiterAPIError when fetching token info for {token_address}: {e}"
            logger.warning(error_msg)
            return {'success': False, 'error': str(e), 'data': None, 'source': 'jupiter_sdk', 'details': e}
        except Exception as e:
            error_msg = f"Unexpected error fetching token info from Jupiter SDK for {token_address}: {e}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': str(e), 'data': None, 'source': 'jupiter_sdk', 'details': e}

    async def _get_specific_pool_liquidity(self, token_address: str, pool_address: str) -> Dict[str, Any]:
        """
        (Placeholder) Récupère la liquidité d'un pool spécifique.
        Returns a structured response.
        """
        # TODO: Implement logic to get liquidity for a specific pool_address.
        # This would likely involve calling an API (e.g., DexScreener /pairs or a Jupiter equivalent if available for specific pools).
        logger.warning(f"_get_specific_pool_liquidity for {token_address} pool {pool_address} is not fully implemented.")
        # Example call to DexScreener for a specific pair (pool)
        await self._check_rate_limit("dexscreener")
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        url = f"{Config.DEXSCREENER_API_URL}/latest/dex/pairs/{Config.SOLANA_CHAIN_ID_DEXSCREENER}/{pool_address}" # Assuming Solana chain and pool address format
        logger.debug(f"DexScreener specific pool liquidity request: GET {url}")
        try:
            async with self.session.get(url, timeout=Config.API_TIMEOUT_SECONDS) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        if data.get("pair"):
                            pair_data = data["pair"]
                            # Convert this pair_data to your standardized liquidity format
                            converted_data = self._convert_dexscreener_format(pair_data, is_liquidity_info=True)
                            if converted_data.get('liquidity_usd') is not None: # Check if conversion was successful
                                return {'success': True, 'error': None, 'data': converted_data, 'source': 'dexscreener-pair'}
                            else:
                                return {'success': False, 'error': "Failed to convert DexScreener pair data for liquidity", 'data': None, 'source': 'dexscreener-pair'}
                        else:
                            return {'success': False, 'error': "No pair data in DexScreener response for pool", 'data': None, 'source': 'dexscreener-pair'}
                    except json.JSONDecodeError as e:
                        return {'success': False, 'error': f"JSONDecodeError: {str(e)}", 'data': None, 'source': 'dexscreener-pair'}
                else:
                    return {'success': False, 'error': f"DexScreener API status {response.status}: {response_text}", 'data': None, 'source': 'dexscreener-pair'}
        except aiohttp.ClientError as e:
            return {'success': False, 'error': f"ClientError: {str(e)}", 'data': None, 'source': 'dexscreener-pair'}
        except asyncio.TimeoutError:
            return {'success': False, 'error': "TimeoutError", 'data': None, 'source': 'dexscreener-pair'}
        except Exception as e:
            return {'success': False, 'error': f"UnexpectedError: {str(e)}", 'data': None, 'source': 'dexscreener-pair'}

    async def _get_best_liquidity_source(self, token_address: str) -> Dict[str, Any]:
        """
        (Placeholder) Trouve la meilleure source de liquidité pour un token et récupère les données.
        This would try multiple sources (e.g., Jupiter aggregate, DexScreener top pools).
        Returns a structured response.
        """
        # TODO: Implement logic to find the best liquidity source.
        # This could involve checking Jupiter's price/quote endpoints (which consider liquidity)
        # or iterating through DexScreener pools for the token and picking the best one.
        logger.warning(f"_get_best_liquidity_source for {token_address} is not fully implemented. Using DexScreener pools as a proxy.")
        
        # Fallback to trying DexScreener pools for the token
        await self._check_rate_limit("dexscreener")
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        url = f"{Config.DEXSCREENER_API_URL}/latest/dex/tokens/{token_address}/pools"
        logger.debug(f"DexScreener best liquidity (pools) request: GET {url}")
        try:
            async with self.session.get(url, timeout=Config.API_TIMEOUT_SECONDS) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        if data.get("pools") and len(data["pools"]) > 0:
                            # Select pool with highest USD liquidity
                            best_pool = max(data["pools"], key=lambda p: float(p.get("liquidity", {}).get("usd", 0)))
                            converted_data = self._convert_dexscreener_format(best_pool, is_liquidity_info=True)
                            if converted_data.get('liquidity_usd') is not None:
                                return {'success': True, 'error': None, 'data': converted_data, 'source': 'dexscreener-pools'}
                            else:
                                return {'success': False, 'error': "Failed to convert best DexScreener pool data for liquidity", 'data': None, 'source': 'dexscreener-pools'}
                        else:
                            return {'success': False, 'error': "No pools found on DexScreener for best liquidity", 'data': None, 'source': 'dexscreener-pools'}
                    except json.JSONDecodeError as e:
                        return {'success': False, 'error': f"JSONDecodeError: {str(e)}", 'data': None, 'source': 'dexscreener-pools'}
                    except (ValueError, TypeError) as e: # For float conversion or key errors
                        logger.error(f"Error processing pools for best liquidity {token_address}: {str(e)}")
                        return {'success': False, 'error': f"DataError processing pools: {str(e)}", 'data': None, 'source': 'dexscreener-pools'}
                else:
                    return {'success': False, 'error': f"DexScreener API status {response.status}: {response_text}", 'data': None, 'source': 'dexscreener-pools'}
        except aiohttp.ClientError as e:
            return {'success': False, 'error': f"ClientError: {str(e)}", 'data': None, 'source': 'dexscreener-pools'}
        except asyncio.TimeoutError:
            return {'success': False, 'error': "TimeoutError", 'data': None, 'source': 'dexscreener-pools'}
        except Exception as e:
            return {'success': False, 'error': f"UnexpectedError: {str(e)}", 'data': None, 'source': 'dexscreener-pools'}

    async def _check_rate_limit(self, api_name: str) -> None:
        """
        Vérifie et gère les limites de taux pour une API spécifique.
        Attend si nécessaire pour éviter de dépasser les limites.
        """
        current_time = time.time()
        rate_info = self.rate_limits[api_name]
        
        # Réinitialiser le compteur si la fenêtre de temps est passée
        if current_time - rate_info["last_reset"] > rate_info["window_seconds"]:
            rate_info["calls"] = 0
            rate_info["last_reset"] = current_time
            
        # Vérifier si nous approchons de la limite
        if rate_info["calls"] >= rate_info["limit"]:
            wait_time = rate_info["window_seconds"] - (current_time - rate_info["last_reset"]) + 1
            logger.warning(f"Limite de taux atteinte pour {api_name}. Attente de {wait_time:.2f} secondes.")
            await asyncio.sleep(wait_time)
            # Réinitialiser après avoir attendu
            rate_info["calls"] = 0
            rate_info["last_reset"] = time.time()
            
        # Incrémenter le compteur
        rate_info["calls"] += 1
        
    def get_supported_dexes(self) -> List[str]:
        """Renvoie la liste des DEX pris en charge par le fournisseur de données."""
        return ["Jupiter", "DexScreener", "Raydium", "Orca"] # Example
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def get_historical_prices(self, token_address: str, timeframe: str = "1h", limit: int = 100, exchange: str = "dexscreener") -> Dict[str, Any]:
        """
        Récupère les données de prix historiques. Pour l'instant, supporte DexScreener.
        Returns a structured response: {'success': True/False, 'error': 'message' or None, 'data': list_of_ohlcv_or_None}
        """
        cache_key = f"{token_address}_{timeframe}_{limit}_{exchange}_historical"
        cached_data = self.historical_data_cache.get(cache_key)
        if cached_data:
            return {'success': True, 'error': None, 'data': cached_data}

        if exchange.lower() == "dexscreener":
            # 1. Find the most liquid pair for the token_address on DexScreener
            pairs_info_url = f"{Config.DEXSCREENER_API_URL}/latest/dex/tokens/{token_address}"
            pairs_response = await self._make_api_request("GET", pairs_info_url, "dexscreener_pairs_for_historical")

            if not pairs_response['success'] or not pairs_response['data'].get("pairs"):
                logger.warning(f"Could not fetch pairs for {token_address} from DexScreener for historical data: {pairs_response.get('error', 'No pairs data')}")
                return {'success': False, 'error': f"Failed to get pairs for historical data: {pairs_response.get('error', 'No pairs data')}", 'data': None}

            sorted_pairs = sorted(
                [p for p in pairs_response['data']["pairs"] if p.get("liquidity", {}).get("usd") is not None],
                key=lambda x: float(x["liquidity"]["usd"]),
                reverse=True
            )
            if not sorted_pairs:
                logger.warning(f"No liquid pairs found for {token_address} on DexScreener for historical data.")
                return {'success': False, 'error': "No liquid pairs found for historical data", 'data': None}
            
            best_pair_address = sorted_pairs[0].get("pairAddress")
            if not best_pair_address: # This check was correctly in my full diff, ensuring it's here
                logger.warning(f"Best pair for {token_address} on DexScreener has no address.")
                return {'success': False, 'error': "Best pair has no address", 'data': None}

            # 2. Map timeframe to DexScreener resolution
            ds_resolution_map = {
                "1m": {"res": "1", "timeUnit": "minute"}, "5m": {"res": "5", "timeUnit": "minute"}, 
                "15m": {"res": "15", "timeUnit": "minute"}, "30m": {"res": "30", "timeUnit": "minute"},
                "1h": {"res": "60", "timeUnit": "minute"}, "4h": {"res": "240", "timeUnit": "minute"},
                "1d": {"res": "1D", "timeUnit": "day"} 
            }

            if timeframe not in ds_resolution_map:
                err_msg = f"Unsupported timeframe '{timeframe}' for DexScreener. Supported: {list(ds_resolution_map.keys())}"
                logger.error(err_msg)
                return {'success': False, 'error': err_msg, 'data': None}

            selected_res_info = ds_resolution_map[timeframe]
            
            # Use the token specific OHLCV endpoint
            ohlcv_url = f"{Config.DEXSCREENER_API_URL}/latest/dex/tokens/ohlcv/solana/{token_address}/{selected_res_info['res']}"
            params_ohlcv = {"limit_int": min(limit, 1000)} # Max limit 1000 for this endpoint
            
            # Make the API request using the corrected URL and parameters
            api_response = await self._make_api_request("GET", ohlcv_url, "dexscreener_historical_ohlcv", params=params_ohlcv)

            if api_response['success']:
                raw_data = api_response['data']
                # DexScreener OHLCV format: {"OHLCV": [{"T":timestamp_ms, "O":open, "H":high, "L":low, "C":close, "V":volume_native}, ...]}
                if raw_data and "OHLCV" in raw_data and isinstance(raw_data["OHLCV"], list):
                    formatted_candles = []
                    for candle in raw_data["OHLCV"]:
                        try:
                            # Ensure all necessary keys are present and values are convertible
                            ts = candle.get("T")
                            o = candle.get("O")
                            h = candle.get("H")
                            l = candle.get("L")
                            c = candle.get("C")
                            v = candle.get("V")
                            if all(x is not None for x in [ts, o, h, l, c, v]):
                                formatted_candles.append({
                                    "timestamp": ts // 1000, # Convert ms to s
                                    "open": float(o),
                                    "high": float(h),
                                    "low": float(l),
                                    "close": float(c),
                                    "volume": float(v) # Volume in token terms
                                })
                            else:
                                logger.warning(f"Skipping candle with missing data in historical OHLCV for {token_address}: {candle}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error converting candle data in historical OHLCV for {token_address}: {candle}. Error: {e}")
                    
                    # Sort by timestamp ascending if not already (DexScreener usually returns descending)
                    formatted_candles.sort(key=lambda x: x["timestamp"])
                    
                    # Trim to limit if more data than requested 
                    final_candles = formatted_candles[-limit:] if len(formatted_candles) > limit else formatted_candles

                    if final_candles:
                        self.historical_data_cache[cache_key] = final_candles
                        return {'success': True, 'error': None, 'data': final_candles}
                    else:
                        # This case could happen if all candles had missing data or limit was 0
                        err_msg = f"No valid OHLCV data processed from DexScreener for {token_address} with resolution {selected_res_info['res']}"
                        logger.warning(f"{err_msg}. Raw response OHLCV part: {raw_data.get('OHLCV')}")
                        return {'success': False, 'error': err_msg, 'data': None}
                else:
                    err_msg = f"Format de réponse OHLCV inattendu ou vide de DexScreener pour {token_address}"
                    logger.warning(f"{err_msg}. Raw response: {raw_data}")
                    return {'success': False, 'error': err_msg, 'data': None}
            else:
                # Error already logged by _make_api_request, propagate it
                # logger.error(f"API request failed for historical OHLCV for {token_address}: {api_response.get('error')}") # Redundant logging
                return api_response # Propagate the structured error from _make_api_request
        else:
            # Placeholder for other exchanges
            logger.warning(f"Historical price data for exchange '{exchange}' is not implemented.")
            return {'success': False, 'error': f"exchange_not_implemented: {exchange}", 'data': None}

    @retry(stop=stop_after_attempt(Config.DEFAULT_API_MAX_RETRIES), wait=wait_exponential(multiplier=1, min=1, max=10), 
           retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def get_jupiter_swap_quote(
        self, 
        input_mint_str: str, 
        output_mint_str: str, 
        amount_in_tokens: float, # Amount in human-readable token units (e.g., 0.1 SOL)
        slippage_bps: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtient un devis de swap de Jupiter en utilisant JupiterApiClient.
        Nécessite de récupérer les décimales du token d'entrée pour convertir le montant en lamports.
        """
        if not self.jupiter_client:
            return {'success': False, 'error': "JupiterApiClient not initialized", 'data': None, 'source': 'jupiter_sdk'}

        logger.info(f"Fetching Jupiter swap quote for {amount_in_tokens} {input_mint_str} -> {output_mint_str}")

        # 1. Get input token decimals
        token_info_response = await self.get_token_info(input_mint_str)
        if not token_info_response.get('success') or not token_info_response.get('data') or \
           token_info_response['data'].get('decimals') is None:
            error_msg = f"Failed to get token info (especially decimals) for input_mint {input_mint_str} to calculate lamports: {token_info_response.get('error')}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg, 'data': None, 'source': 'jupiter_sdk'}
        
        decimals = token_info_response['data']['decimals']
        try:
            amount_lamports = int(amount_in_tokens * (10**decimals))
        except Exception as e:
            error_msg = f"Error converting amount_in_tokens to lamports for {input_mint_str} (decimals: {decimals}): {e}"
            logger.error(error_msg, exc_info=True)
            # This is a local data processing error, not an API error from Jupiter yet.
            # Return the standard error dict for MarketDataProvider.
            return {'success': False, 'error': error_msg, 'data': None, 'source': 'internal_market_data'}

        logger.debug(f"Calculated amount in lamports: {amount_lamports} for {input_mint_str}")

        try:
            # 2. Call JupiterApiClient.get_quote
            # Slippage will be handled by JupiterApiClient using config default if not provided here.
            actual_slippage_bps = slippage_bps if slippage_bps is not None else self.config.JUPITER_DEFAULT_SLIPPAGE_BPS

            # JupiterApiClient.get_quote now returns data directly or raises JupiterAPIError.
            quote_data_sdk = await self.jupiter_client.get_quote(
                input_mint_str=input_mint_str,
                output_mint_str=output_mint_str,
                amount_lamports=amount_lamports,
                slippage_bps=actual_slippage_bps
            )

            if quote_data_sdk: # quote_data_sdk is the direct response from SDK
                logger.info(f"Jupiter SDK quote successful for {input_mint_str} -> {output_mint_str}.")
                return {
                    'success': True, 
                    'error': None, 
                    'data': quote_data_sdk, 
                    'source': 'jupiter_sdk'
                }
            else:
                # This case should ideally not be hit if jupiter_client.get_quote raises on no data or error.
                error_msg = f"No data received from Jupiter SDK for quote {input_mint_str} -> {output_mint_str}."
                logger.warning(error_msg)
                return {'success': False, 'error': error_msg, 'data': None, 'source': 'jupiter_sdk'}
        except JupiterAPIError as e:
            error_msg = f"JupiterAPIError when fetching quote for {input_mint_str} -> {output_mint_str}: {e}"
            logger.warning(error_msg)
            return {'success': False, 'error': str(e), 'data': None, 'source': 'jupiter_sdk', 'details': e}
        except Exception as e:
            error_msg = f"Unexpected error fetching quote from Jupiter SDK for {input_mint_str} -> {output_mint_str}: {e}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': str(e), 'data': None, 'source': 'jupiter_sdk', 'details': e}

    def _convert_dexscreener_format(self, data: Dict, is_token_info: bool = False, is_pair_list: bool = False) -> Dict:
        """Normalisation des données DexScreener vers un schéma standardisé."""
        # 'data' here is a single pair object from DexScreener response
        
        if is_token_info: # Extract info about the baseToken from a DexScreener pair
            base_token_ds = data.get('baseToken', {})
            return {
                'address': base_token_ds.get('address'),
                'symbol': base_token_ds.get('symbol'),
                'name': base_token_ds.get('name'),
                'decimals': None, # DexScreener pair data doesn't usually have decimals here
                'logoURI': data.get('info', {}).get('imageUrl'), # DexScreener might have imageUrl for pair
                'tags': [],
                'source': 'dexscreener_pair_as_info',
                'extensions': {'pairAddress': data.get('pairAddress')}
            }

        # Default conversion for a pair structure
        base_token = data.get('baseToken', {})
        quote_token = data.get('quoteToken', {})
        
        # DexScreener price is usually priceNative or priceUsd
        price_usd = data.get('priceUsd')
        if price_usd is None and data.get('priceNative') is not None:
            # If only priceNative is available, it might be against SOL or other native token.
            # For simplicity, if priceUsd is missing, we mark it as None. Accurate conversion needs quote token price.
            price_usd = None 
            
        return {
            'pairAddress': data.get('pairAddress'),
            'baseToken': {
                'address': base_token.get('address'),
                'symbol': base_token.get('symbol'),
                'name': base_token.get('name')
            },
            'quoteToken': {
                'address': quote_token.get('address'),
                'symbol': quote_token.get('symbol'),
                'name': quote_token.get('name')
            },
            'priceUsd': float(price_usd) if price_usd is not None else None,
            'priceNative': float(data.get('priceNative')) if data.get('priceNative') is not None else None,
            'liquidity_usd': float(data.get('liquidity', {}).get('usd', 0)),
            'volume_h24': float(data.get('volume', {}).get('h24', 0)),
            'fdv': float(data.get('fdv',0)), # Fully Diluted Valuation
            'marketCap': float(data.get('marketCap',0)), # Market Cap if available
            'dexId': data.get('dexId'),
            'url': data.get('url'),
            'source': 'dexscreener',
            'raw_data': data # Keep original for further details
        }

    async def get_token_transactions(self, token_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les transactions récentes pour un token (placeholder).
        Cette méthode nécessiterait une source de données comme Solscan, Birdeye, ou si DexScreener/Jupiter le fournit.
        Args:
            token_address: Adresse du token.
            limit: Nombre de transactions à retourner.
        Returns:
            Liste de dictionnaires de transactions.
        """
        logger.warning(f"get_token_transactions pour {token_address} est un placeholder et retourne des données vides.")
        # Exemple de structure attendue par SecurityChecker (simplifié):
        # return [{ "sender": "addr1", "recipient": "addr2", "amount": 100.0, "timestamp": time.time() }]
        return []

    async def get_token_holders(self, token_address: str, limit: int = 100) -> Dict[str, Any]:
        """Récupère les détenteurs d'un token (placeholder).
        Nécessite une API comme Solscan, Birdeye, ou si Jupiter/DexScreener a une fonctionnalité.
        Args:
            token_address: Adresse du token.
            limit: Nombre de détenteurs à retourner.
        Returns:
            Dictionnaire avec une clé 'holders' contenant une liste de détenteurs.
            Chaque détenteur: {"address": str, "percentage": float, "is_verified": bool}
        """
        logger.warning(f"get_token_holders pour {token_address} est un placeholder et retourne des données vides.")
        # Exemple de structure attendue par SecurityChecker (simplifié):
        # return {"holders": [{"address": "holder_addr", "percentage": 0.1, "is_verified": False}]}
        return {"holders": []}

    async def get_liquidity_history(self, token_address: str, timeframe: str = "15m", limit: int = 96) -> List[Dict[str, Any]]:
        """Récupère l'historique de liquidité pour un token (placeholder).
        Args:
            token_address: Adresse du token.
            timeframe: Intervalle de temps.
            limit: Nombre de points de données.
        Returns:
            Liste de dictionnaires avec {"timestamp": float, "liquidity_usd": float, "source": str}.
        """
        logger.warning(f"get_liquidity_history pour {token_address} est un placeholder et retourne des données vides.")
        # Exemple de structure attendue par SecurityChecker (simplifié):
        # return [{ "timestamp": time.time(), "liquidity_usd": 10000.0, "source": "dexscreener" }]
        return []
