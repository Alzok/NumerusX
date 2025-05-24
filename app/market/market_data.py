import aiohttp
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import Config

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
            # Assuming cached value is already in the final desired format {'price': ..., 'source': ...}
            return {'success': True, 'error': None, 'data': cached_value}
            
        final_error_message = "Impossible d'obtenir le prix pour {token_address} depuis toutes les sources."
        
        # Essayer Jupiter d'abord
        logger.debug(f"Fetching price for {token_address} from Jupiter")
        jupiter_result = await self._get_jupiter_price(token_address, reference_token)
        
        if jupiter_result.get('success'):
            self.price_cache[cache_key] = jupiter_result['data'] # Cache only the data part
            return jupiter_result
        else:
            logger.warning(f"Échec de la récupération du prix depuis Jupiter pour {token_address}: {jupiter_result.get('error')}")
            final_error_message += f" Jupiter: {jupiter_result.get('error')}"

        # Fallback sur DexScreener
        logger.debug(f"Fetching price for {token_address} from DexScreener (fallback)")
        dexscreener_result = await self._get_dexscreener_price(token_address) # DexScreener usually gives USD price
        
        if dexscreener_result.get('success'):
            # DexScreener might not know the reference_token, ensure data matches expectation or adapt
            # For now, assume _get_dexscreener_price returns data in the expected format if successful
            self.price_cache[cache_key] = dexscreener_result['data'] # Cache only the data part
            return dexscreener_result
        else:
            logger.warning(f"Échec de la récupération du prix depuis DexScreener pour {token_address}: {dexscreener_result.get('error')}")
            final_error_message += f" DexScreener: {dexscreener_result.get('error')}"
            
        logger.error(final_error_message.format(token_address=token_address))
        return {'success': False, 'error': final_error_message.format(token_address=token_address), 'data': None}
        
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
            
        final_error_message = f"Impossible d'obtenir les infos pour {token_address} depuis toutes les sources."

        # Try Jupiter first
        logger.debug(f"Fetching token info for {token_address} from Jupiter")
        jupiter_result = await self._get_jupiter_token_info(token_address)
        
        if jupiter_result.get('success'):
            self.token_info_cache[cache_key] = jupiter_result['data']
            return jupiter_result
        else:
            logger.warning(f"Échec de la récupération des infos token depuis Jupiter pour {token_address}: {jupiter_result.get('error')}")
            final_error_message += f" Jupiter: {jupiter_result.get('error')};"
        
        # Fallback to DexScreener
        logger.debug(f"Fetching token info for {token_address} from DexScreener (fallback)")
        await self._check_rate_limit("dexscreener")
        if not self.session or self.session.closed: 
            self.session = aiohttp.ClientSession()
        
        ds_token_url = f"{Config.DEXSCREENER_API_URL}/latest/dex/tokens/{token_address}"
        logger.debug(f"DexScreener token info request: GET {ds_token_url}")
        dexscreener_data = None
        dexscreener_error = "Unknown error"

        try:
            async with self.session.get(ds_token_url, timeout=Config.API_TIMEOUT_SECONDS) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        ds_api_data = json.loads(response_text)
                        logger.debug(f"DexScreener token info response data: {ds_api_data}")
                        if ds_api_data.get("pairs") and isinstance(ds_api_data["pairs"], list) and len(ds_api_data["pairs"]) > 0:
                            # Select the most relevant pair (e.g., highest liquidity or most traded against USD/SOL)
                            # This logic can be sophisticated. For now, take the one with highest USD liquidity if available.
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
                                    dexscreener_error = "Failed to convert DexScreener data or address missing"
                            else:
                                dexscreener_error = "No pairs with USD liquidity found on DexScreener for token info"
                        else:
                            dexscreener_error = "No pairs array or empty pairs in DexScreener response"
                    except json.JSONDecodeError as e:
                        logger.error(f"DexScreener token info API JSONDecodeError for URL {ds_token_url}: {str(e)}. Response: {response_text}")
                        dexscreener_error = f"JSONDecodeError: {str(e)}"
                else:
                    dexscreener_error = f"DexScreener token info API returned status {response.status}: {response_text}"
                    logger.warning(f"{dexscreener_error} for URL {ds_token_url}")

        except aiohttp.ClientError as e:
            logger.error(f"DexScreener token info API ClientError for URL {ds_token_url}: {str(e)}", exc_info=True)
            dexscreener_error = f"ClientError: {str(e)}"
        except asyncio.TimeoutError:
            logger.error(f"DexScreener token info API Timeout for URL {ds_token_url}", exc_info=True)
            dexscreener_error = "TimeoutError"
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error in get_token_info (DexScreener part) for URL {ds_token_url}: {str(e)}", exc_info=True)
            dexscreener_error = f"UnexpectedError: {str(e)}"

        logger.warning(f"Échec de la récupération des infos token depuis DexScreener pour {token_address}: {dexscreener_error}")
        final_error_message += f" DexScreener: {dexscreener_error}"
        
        logger.error(final_error_message)
        return {'success': False, 'error': final_error_message, 'data': None}
        
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
        """Récupère le prix d'un token depuis Jupiter API V6 /price endpoint.
        Returns a structured response: {'success': True/False, 'error': 'message' or None, 'data': price_data or None, 'source': 'jupiter'}
        """
        await self._check_rate_limit("jupiter")
        
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession() 
            
        url = f"{Config.get_jupiter_price_url()}?ids={token_address}&vsToken={reference_token}"
        headers = {}
        if Config.JUPITER_API_KEY:
            headers["Authorization"] = f"Bearer {Config.JUPITER_API_KEY}"

        logger.debug(f"Jupiter price request: GET {url}")
        try:
            async with self.session.get(url, headers=headers, timeout=Config.API_TIMEOUT_SECONDS) as response:
                response_text = await response.text() # Read text for better error inspection
                if response.status == 200:
                    try:
                        data = json.loads(response_text) # Parse JSON from text
                        logger.debug(f"Jupiter price response data: {data}")
                        
                        if token_address not in data.get("data", {}):
                            logger.warning(f"Token {token_address} not found in Jupiter price response: {data}")
                            return {'success': False, 'error': f"token_not_found_in_response: {token_address}", 'data': None, 'source': 'jupiter'}

                        price_info = data["data"][token_address]
                        price_data = {
                            "price": float(price_info["price"]) if price_info.get("price") is not None else None,
                            "source": "jupiter",
                            "timestamp": time.time(),
                            "reference_token": reference_token,
                            "vsTokenSymbol": price_info.get("vsTokenSymbol"), # Corrected based on typical Jupiter API
                            "vsAmount": price_info.get("vsAmount"),
                        }
                        if price_data["price"] is None:
                             logger.warning(f"Jupiter returned null price for {token_address} against {reference_token}")
                             return {'success': False, 'error': f"null_price_returned_for_token: {token_address}", 'data': None, 'source': 'jupiter'}
                        
                        return {'success': True, 'error': None, 'data': price_data, 'source': 'jupiter'}
                    except json.JSONDecodeError as e:
                        logger.error(f"Jupiter Price API JSONDecodeError for URL {url}: {str(e)}. Response text: {response_text}")
                        return {'success': False, 'error': f"JSONDecodeError: {str(e)}", 'data': None, 'source': 'jupiter'}
                else:
                    error_message = f"Jupiter Price API returned status {response.status}"
                    try:
                        error_payload = json.loads(response_text)
                        error_message += f": {error_payload.get('message', error_text)}"
                    except json.JSONDecodeError:
                        error_message += f": {response_text}"
                    logger.error(f"{error_message} for URL {url}")
                    return {'success': False, 'error': error_message, 'data': None, 'source': 'jupiter'}
        except aiohttp.ClientError as e:
            logger.error(f"Jupiter Price API ClientError for URL {url}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"ClientError: {str(e)}", 'data': None, 'source': 'jupiter'}
        except asyncio.TimeoutError:
            logger.error(f"Jupiter Price API Timeout for URL {url}", exc_info=True)
            return {'success': False, 'error': "TimeoutError", 'data': None, 'source': 'jupiter'}
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error in _get_jupiter_price for URL {url}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"UnexpectedError: {str(e)}", 'data': None, 'source': 'jupiter'}
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def _get_dexscreener_price(self, token_address: str) -> Dict[str, Any]:
        """Récupère le prix d'un token depuis DexScreener API.
        Returns a structured response: {'success': True/False, 'error': 'message' or None, 'data': price_data or None, 'source': 'dexscreener'}
        """
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
                        logger.error(f"DexScreener Price API JSONDecodeError for URL {url}: {str(e)}. Response text: {response_text}")
                        return {'success': False, 'error': f"JSONDecodeError: {str(e)}", 'data': None, 'source': 'dexscreener'}
                else:
                    error_message = f"DexScreener Price API returned status {response.status}"
                    try:
                        error_payload = json.loads(response_text) # DexScreener errors often have a JSON body
                        error_message += f": {error_payload.get('error', {}).get('message', response_text)}"
                    except json.JSONDecodeError:
                        error_message += f": {response_text}"
                    logger.error(f"{error_message} for URL {url}")
                    return {'success': False, 'error': error_message, 'data': None, 'source': 'dexscreener'}

        except aiohttp.ClientError as e:
            logger.error(f"DexScreener Price API ClientError for URL {url}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"ClientError: {str(e)}", 'data': None, 'source': 'dexscreener'}
        except asyncio.TimeoutError:
            logger.error(f"DexScreener Price API Timeout for URL {url}", exc_info=True)
            return {'success': False, 'error': "TimeoutError", 'data': None, 'source': 'dexscreener'}
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error in _get_dexscreener_price for URL {url}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"UnexpectedError: {str(e)}", 'data': None, 'source': 'dexscreener'}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def _get_jupiter_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        (Placeholder) Récupère les informations détaillées d'un token via Jupiter API.
        Should use a dedicated Jupiter endpoint if available, or parse from /price or other sources.
        Returns a structured response: {'success': True/False, 'error': 'message' or None, 'data': token_data or None, 'source': 'jupiter'}
        """
        # TODO: Implement actual Jupiter token info fetching logic if a suitable endpoint exists.
        # For now, this is a placeholder. Jupiter's /v6/price returns some info, 
        # but a dedicated token metadata endpoint or combining with other sources might be better.
        # Example: Jupiter Token List API: https://station.jup.ag/docs/token-list/token-list-api
        
        # Simulate checking Jupiter's strict token list first
        await self._check_rate_limit("jupiter_token_list") # Assuming a different rate limit category
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        
        token_list_url = "https://token.jup.ag/all"
        logger.debug(f"Fetching Jupiter token list for {token_address}: GET {token_list_url}")
        try:
            async with self.session.get(token_list_url, timeout=Config.API_TIMEOUT_SECONDS) as response:
                response_text = await response.text()
                if response.status == 200:
                    try:
                        tokens = json.loads(response_text)
                        for token in tokens:
                            if token.get("address") == token_address:
                                # Basic conversion, can be expanded
                                jupiter_token_data = {
                                    "address": token.get("address"),
                                    "name": token.get("name"),
                                    "symbol": token.get("symbol"),
                                    "decimals": token.get("decimals"),
                                    "logoURI": token.get("logoURI"),
                                    "tags": token.get("tags", []),
                                    "source": "jupiter-token-list"
                                }
                                return {'success': True, 'error': None, 'data': jupiter_token_data, 'source': 'jupiter-token-list'}
                        logger.warning(f"Token {token_address} not found in Jupiter token list.")
                        return {'success': False, 'error': f"token_not_found_in_jupiter_list: {token_address}", 'data': None, 'source': 'jupiter-token-list'}
                    except json.JSONDecodeError as e:
                        logger.error(f"Jupiter token list JSONDecodeError: {str(e)}. Response: {response_text}")
                        return {'success': False, 'error': f"JSONDecodeError: {str(e)}", 'data': None, 'source': 'jupiter-token-list'}
                else:
                    error_msg = f"Jupiter token list API failed with status {response.status}: {response_text}"
                    logger.error(error_msg)
                    return {'success': False, 'error': error_msg, 'data': None, 'source': 'jupiter-token-list'}
        except aiohttp.ClientError as e:
            logger.error(f"Jupiter token list ClientError: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"ClientError: {str(e)}", 'data': None, 'source': 'jupiter-token-list'}
        except asyncio.TimeoutError:
            logger.error(f"Jupiter token list Timeout", exc_info=True)
            return {'success': False, 'error': "TimeoutError", 'data': None, 'source': 'jupiter-token-list'}
        except Exception as e:
            logger.error(f"Unexpected error in _get_jupiter_token_info: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"UnexpectedError: {str(e)}", 'data': None, 'source': 'jupiter-token-list'}

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
            await self._check_rate_limit("dexscreener")
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            # Determine DexScreener resolution and time parameters
            # DexScreener resolutions: 1, 5, 15, 30, 60 (minutes), 240 (4h), 1D
            # Mapping our timeframe to DexScreener's resolution
            resolution_map = {
                "1m": "1", "5m": "5", "15m": "15", "30m": "30",
                "1h": "60", "4h": "240", "1d": "1D"
            }
            ds_resolution = resolution_map.get(timeframe.lower())
            if not ds_resolution:
                err_msg = f"Unsupported timeframe for DexScreener: {timeframe}. Supported: 1m,5m,15m,30m,1h,4h,1d"
                logger.error(err_msg)
                return {'success': False, 'error': err_msg, 'data': None}

            # DexScreener OHLCV endpoint needs a pair address. We need to find a suitable one first.
            # This part requires finding a representative pair for the token_address.
            logger.debug(f"Searching for a suitable pair for {token_address} on DexScreener for historical data.")
            
            # Try to get a good pair (e.g. highest liquidity vs USDC/SOL)
            token_pools_url = f"{Config.DEXSCREENER_API_URL}/latest/dex/tokens/{token_address}/pools"
            pair_address_to_query = None
            
            try:
                async with self.session.get(token_pools_url, timeout=Config.API_TIMEOUT_SECONDS) as pool_response:
                    pool_response_text = await pool_response.text()
                    if pool_response.status == 200:
                        try:
                            pools_data = json.loads(pool_response_text)
                            if pools_data.get("pools") and len(pools_data["pools"]) > 0:
                                suitable_pools = [
                                    p for p in pools_data["pools"]
                                    if p.get("quoteToken", {}).get("symbol", "").upper() in ["USDC", "SOL", "USDT"] and p.get("liquidity", {}).get("usd")
                                ]
                                if suitable_pools:
                                    best_pool = max(suitable_pools, key=lambda p: float(p["liquidity"]["usd"]))
                                    pair_address_to_query = best_pool.get("pairAddress")
                                else: # Fallback to just any pool with liquidity if no preferred quote token found
                                    pools_with_liquidity = [p for p in pools_data["pools"] if p.get("liquidity", {}).get("usd")]
                                    if pools_with_liquidity:
                                        best_pool = max(pools_with_liquidity, key=lambda p: float(p["liquidity"]["usd"]))
                                        pair_address_to_query = best_pool.get("pairAddress")
                                
                                if pair_address_to_query:
                                     logger.info(f"Using pair {pair_address_to_query} for historical data of {token_address} on DexScreener.")
                                else:
                                    logger.warning(f"No suitable pair found for {token_address} on DexScreener for OHLCV.")
                                    return {'success': False, 'error': f"no_suitable_pair_for_ohlcv: {token_address}", 'data': None}
                            else:
                                logger.warning(f"No pools found for {token_address} to determine pair for OHLCV. Response: {pools_data}")
                                return {'success': False, 'error': f"no_pools_to_determine_pair_for_ohlcv: {token_address}", 'data': None}
                        except json.JSONDecodeError as e_json:
                            logger.error(f"DexScreener pools JSONDecodeError for {token_address}: {str(e_json)}. Response: {pool_response_text}")
                            return {'success': False, 'error': f"JSONDecodeError_pools_ohlcv: {str(e_json)}", 'data': None}
                    else:
                        err_msg = f"DexScreener pools API for {token_address} returned {pool_response.status}: {pool_response_text}"
                        logger.error(err_msg)
                        return {'success': False, 'error': err_msg, 'data': None}
            except (aiohttp.ClientError, asyncio.TimeoutError) as e_http:
                logger.error(f"DexScreener pools API ClientError/Timeout for {token_address}: {str(e_http)}", exc_info=True)
                return {'success': False, 'error': f"ClientError_Timeout_pools_ohlcv: {str(e_http)}", 'data': None}


            if not pair_address_to_query:
                 return {'success': False, 'error': f"could_not_determine_pair_for_ohlcv: {token_address}", 'data': None}

            # Now fetch OHLCV data for the found pair_address_to_query
            # Calculate `to_time` (now) and `from_time` based on limit and resolution
            # DexScreener expects timestamps in milliseconds
            to_time_ms = int(time.time() * 1000)
            
            # Estimate duration based on timeframe (e.g., "1h" -> 3600 seconds)
            timeframe_seconds_map = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}
            duration_per_candle_seconds = timeframe_seconds_map.get(timeframe.lower(), 3600) # Default to 1h
            total_duration_seconds = limit * duration_per_candle_seconds
            from_time_ms = int((time.time() - total_duration_seconds) * 1000)

            ohlcv_url = (
                f"{Config.DEXSCREENER_API_URL}/latest/dex/pairs/{Config.SOLANA_CHAIN_ID_DEXSCREENER}/{pair_address_to_query}"
                f"/ohlcv?res={ds_resolution}& σειριακός αριθμός={limit}&from={from_time_ms}&to={to_time_ms}" # σειριακός αριθμός seems to be a typo in a previous version, should be count or limit
            )
            # Correcting the Dexscreener OHLCV endpoint, assuming it is 'count' or similar parameter, not 'σειριακός αριθμός'
            # A common pattern is `&limit={limit_count}` or using from/to with a specific bar count in mind.
            # Dexscreener's documentation should be checked. The given example from previous version used `σειριακός αριθμός` which is Greek for "serial number".
            # Based on typical API designs and some Dexscreener examples, it seems they might use `limit` directly or imply it from `from/to` and `res`.
            # For robustness, let's assume a 'limit' parameter if available, or rely on 'from'/'to' to bound the data.
            # The DexScreener /ohlcv endpoint typically does *not* use a direct `limit` or `count` param.
            # It expects `from` and `to` timestamps (in ms) and `res`. It returns up to 1000 bars.
            # We'll request a window and then take the last `limit` candles from the response.

            ohlcv_url = (
                f"{Config.DEXSCREENER_API_URL}/latest/dex/pairs/{Config.SOLANA_CHAIN_ID_DEXSCREENER}/{pair_address_to_query}"
                f"/ohlcv?res={ds_resolution}&from={from_time_ms}&to={to_time_ms}"
            )
            logger.debug(f"DexScreener OHLCV request: GET {ohlcv_url}")

            try:
                async with self.session.get(ohlcv_url, timeout=Config.API_TIMEOUT_SECONDS) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        try:
                            ohlcv_data = json.loads(response_text)
                            if ohlcv_data.get("ohlcv") and isinstance(ohlcv_data["ohlcv"], list):
                                # Convert DexScreener OHLCV to standard format:
                                # [{'timestamp': ts, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v}]
                                # DexScreener format: {"t": timestamp_ms, "o": open_usd, "h": high_usd, "l": low_usd, "c": close_usd, "v": volume_usd}
                                formatted_data = []
                                for entry in ohlcv_data["ohlcv"]:
                                    formatted_data.append({
                                        "timestamp": entry["t"] / 1000, # Convert ms to s
                                        "open": float(entry["o"]),
                                        "high": float(entry["h"]),
                                        "low": float(entry["l"]),
                                        "close": float(entry["c"]),
                                        "volume": float(entry["v"])
                                    })
                                
                                # Ensure we return at most `limit` candles, taking the most recent ones.
                                final_data = formatted_data[-limit:]
                                self.historical_data_cache[cache_key] = final_data
                                return {'success': True, 'error': None, 'data': final_data}
                            else:
                                logger.warning(f"DexScreener OHLCV data for {pair_address_to_query} is malformed or empty: {ohlcv_data}")
                                return {'success': False, 'error': f"malformed_ohlcv_data: {pair_address_to_query}", 'data': None}
                        except json.JSONDecodeError as e_json:
                            logger.error(f"DexScreener OHLCV JSONDecodeError for {pair_address_to_query}: {str(e_json)}. Response: {response_text}")
                            return {'success': False, 'error': f"JSONDecodeError_ohlcv: {str(e_json)}", 'data': None}
                        except (ValueError, TypeError) as e_conv:
                            logger.error(f"Error converting DexScreener OHLCV data for {pair_address_to_query}: {str(e_conv)}", exc_info=True)
                            return {'success': False, 'error': f"DataConversionError_ohlcv: {str(e_conv)}", 'data': None}
                    else:
                        err_msg = f"DexScreener OHLCV API for {pair_address_to_query} returned {response.status}: {response_text}"
                        logger.error(err_msg)
                        return {'success': False, 'error': err_msg, 'data': None}
            except (aiohttp.ClientError, asyncio.TimeoutError) as e_http:
                logger.error(f"DexScreener OHLCV API ClientError/Timeout for {pair_address_to_query}: {str(e_http)}", exc_info=True)
                return {'success': False, 'error': f"ClientError_Timeout_ohlcv: {str(e_http)}", 'data': None}
            except Exception as e_unexp:
                logger.error(f"Unexpected error in get_historical_prices (DexScreener OHLCV part) for {pair_address_to_query}: {str(e_unexp)}", exc_info=True)
                return {'success': False, 'error': f"UnexpectedError_ohlcv: {str(e_unexp)}", 'data': None}
        else:
            # Placeholder for other exchanges
            logger.warning(f"Historical price data for exchange '{exchange}' is not implemented.")
            return {'success': False, 'error': f"exchange_not_implemented: {exchange}", 'data': None}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def get_jupiter_swap_quote(self, input_mint: str, output_mint: str, amount_lamports: int, slippage_bps: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtient une cotation de swap depuis Jupiter API V6 /quote endpoint.
        Returns a structured response: {'success': True/False, 'error': 'message' or None, 'data': quote_data or None}
        """
        await self._check_rate_limit("jupiter_quote") # Assuming a 'jupiter_quote' category in rate limits
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        url = Config.get_jupiter_quote_url()
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_lamports,
            "slippageBps": slippage_bps if slippage_bps is not None else Config.SLIPPAGE_BPS, # Use configured default
            "onlyDirectRoutes": Config.JUPITER_ONLY_DIRECT_ROUTES, # From Config
            "asLegacyTransaction": False, # Prefer VersionedTransactions
        }
        # Filter out None params
        params = {k: v for k, v in params.items() if v is not None}
        
        headers = {}
        if Config.JUPITER_API_KEY:
            headers["Authorization"] = f"Bearer {Config.JUPITER_API_KEY}"

        logger.debug(f"Jupiter quote request: GET {url} with params {params}")
        cache_key = f"jupiter_quote_{input_mint}_{output_mint}_{amount_lamports}_{params.get('slippageBps', Config.SLIPPAGE_BPS)}"
        cached_quote = self.jupiter_quote_cache.get(cache_key)
        if cached_quote:
             return {'success': True, 'error': None, 'data': cached_quote}

        try:
            async with self.session.get(url, params=params, headers=headers, timeout=Config.API_TIMEOUT_SECONDS_JUPITER_QUOTE) as response: # Potentially longer timeout for quotes
                response_text = await response.text()
                if response.status == 200:
                    try:
                        quote_data = json.loads(response_text)
                        # Jupiter V6 quote response is directly the data object, not nested under "data": {}
                        logger.debug(f"Jupiter quote response data: {quote_data}")
                        if not quote_data.get("outAmount"): # A key indicator of a valid quote
                            logger.warning(f"Jupiter quote for {input_mint}->{output_mint} seems invalid (no outAmount): {quote_data}")
                            # It might be an error object from Jupiter like {"errorCode":"QUOTE_NOT_FOUND","message":"..."}
                            error_detail = quote_data.get("message", "Invalid quote data or no route found")
                            if quote_data.get("errorCode"):
                                error_detail = f"{quote_data['errorCode']}: {error_detail}"
                            return {'success': False, 'error': error_detail, 'data': quote_data} # return full quote for inspection

                        self.jupiter_quote_cache.put(cache_key, quote_data) # Use put for TTLCache with specific key
                        return {'success': True, 'error': None, 'data': quote_data}
                    except json.JSONDecodeError as e:
                        logger.error(f"Jupiter Quote API JSONDecodeError for URL {url}, params {params}: {str(e)}. Response: {response_text}")
                        return {'success': False, 'error': f"JSONDecodeError: {str(e)}", 'data': None}
                else:
                    error_message = f"Jupiter Quote API returned status {response.status}"
                    try:
                        error_payload = json.loads(response_text)
                        error_message += f": {error_payload.get('message', error_payload.get('error', {}).get('message', response_text))}" # Try to get nested error
                    except json.JSONDecodeError:
                        error_message += f": {response_text}"
                    logger.error(f"{error_message} for URL {url}, params {params}")
                    return {'success': False, 'error': error_message, 'data': None}
        except aiohttp.ClientError as e:
            logger.error(f"Jupiter Quote API ClientError for URL {url}, params {params}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"ClientError: {str(e)}", 'data': None}
        except asyncio.TimeoutError:
            logger.error(f"Jupiter Quote API Timeout for URL {url}, params {params}", exc_info=True)
            return {'success': False, 'error': "TimeoutError", 'data': None}
        except Exception as e:
            logger.error(f"Unexpected error in get_jupiter_swap_quote for URL {url}, params {params}: {str(e)}", exc_info=True)
            return {'success': False, 'error': f"UnexpectedError: {str(e)}", 'data': None}

    def _convert_jupiter_format(self, data: Dict, is_token_info: bool = False, is_pair_list: bool = False) -> Dict:
        """Adaptation du format Jupiter au schéma standardisé.
        This might be for a specific Jupiter endpoint. The structure of 'data' needs to be known.
        Assuming 'data' is from an endpoint that gives token/pair like info.
        """
        if is_token_info: # If we specifically want token info structure
            return {
                'address': data.get('address') or data.get('id'), # Jupiter uses 'address' or 'id'
                'symbol': data.get('symbol'),
                'name': data.get('name'),
                'decimals': data.get('decimals'),
                'logoURI': data.get('logoURI'),
                'tags': data.get('tags', []),
                'source': 'jupiter',
                'extensions': data.get('extensions')
            }
        # Default conversion for a pair-like structure (similar to old DexAPI)
        return {
            'pairAddress': data.get('id'), # Assuming 'id' is the pair identifier for Jupiter context
            'baseToken': { # Assuming 'mint' or 'address' refers to the base token in this Jupiter context
                'address': data.get('mint') or data.get('address'), 
                'symbol': data.get('symbol'),
                'name': data.get('name')
            },
            'quoteToken': None, # Jupiter responses might not always explicitly list quote token this way
            'priceUsd': data.get('price'), # Assuming 'price' is in USD or the vsToken
            'liquidity_usd': data.get('liquidity') or data.get('liquidity_usd'),
            'volume_h24': data.get('volume24h') or data.get('volume', {}).get('h24'),
            'source': 'jupiter',
            'raw_data': data # Keep original for further details
        }

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
