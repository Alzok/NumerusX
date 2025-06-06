"""
Service de cache de données de marché indépendant.
Résout la dépendance circulaire entre SecurityChecker, MarketDataProvider et TradingEngine.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime, timedelta
import redis
import json
from dataclasses import dataclass, asdict

from app.config import get_config

logger = logging.getLogger(__name__)

@dataclass
class CachedTokenInfo:
    """Structure de données token mise en cache."""
    address: str
    symbol: str
    name: str
    decimals: int
    price_usd: float
    market_cap_usd: Optional[float]
    volume_24h_usd: Optional[float]
    created_at: Optional[float]
    liquidity_usd: Optional[float]
    timestamp: float
    source: str

@dataclass
class CachedPriceData:
    """Structure de données prix mise en cache."""
    address: str
    price_usd: float
    change_24h: Optional[float]
    volume_24h_usd: Optional[float]
    timestamp: float
    source: str

class MarketDataCache:
    """
    Service de cache de données de marché indépendant.
    
    Fonctionnalités:
    - Cache unifié Redis pour toutes les données de marché
    - Sources multiples: DexScreener, CoinGecko, Jupiter
    - Pas de dépendances circulaires
    - API simple pour tous les composants
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.redis_client = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configuration cache
        self.cache_ttl = {
            'token_info': 300,  # 5 minutes
            'price_data': 60,   # 1 minute
            'liquidity': 120,   # 2 minutes
            'holders': 900,     # 15 minutes
            'transactions': 180, # 3 minutes
        }
        
        # Sources API prioritaires
        self.api_sources = {
            'dexscreener': 'https://api.dexscreener.com/latest',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'jupiter': 'https://price.jup.ag/v6'
        }
        
        logger.info("MarketDataCache service initialized")

    async def __aenter__(self):
        """Initialise les connexions asynchrones."""
        try:
            # Redis connection
            self.redis_client = redis.asyncio.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established for MarketDataCache")
            
            # HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'NumerusX-Bot/1.0'}
            )
            logger.info("HTTP session created for MarketDataCache")
            
        except Exception as e:
            logger.error(f"Failed to initialize MarketDataCache connections: {e}")
            raise
            
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme les connexions."""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.aclose()
        logger.info("MarketDataCache connections closed")

    # =================================
    # API PUBLIQUE - UTILISÉE PAR TOUS LES COMPOSANTS
    # =================================

    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Récupère les informations complètes d'un token.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Dict standardisé: {'success': bool, 'data': CachedTokenInfo|None, 'error': str|None}
        """
        cache_key = f"token_info:{token_address}"
        
        try:
            # Check cache first
            cached = await self._get_from_cache(cache_key)
            if cached:
                return {'success': True, 'data': cached, 'error': None}
            
            # Fetch from external sources
            token_data = await self._fetch_token_info_external(token_address)
            if token_data:
                # Cache result
                await self._set_cache(cache_key, asdict(token_data), self.cache_ttl['token_info'])
                return {'success': True, 'data': asdict(token_data), 'error': None}
            else:
                return {'success': False, 'data': None, 'error': 'Token information not found'}
                
        except Exception as e:
            logger.error(f"Error getting token info for {token_address}: {e}")
            return {'success': False, 'data': None, 'error': str(e)}

    async def get_token_price(self, token_address: str) -> Dict[str, Any]:
        """
        Récupère le prix actuel d'un token.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Dict: {'success': bool, 'data': CachedPriceData|None, 'error': str|None}
        """
        cache_key = f"price:{token_address}"
        
        try:
            # Check cache first (shorter TTL for prices)
            cached = await self._get_from_cache(cache_key)
            if cached:
                return {'success': True, 'data': cached, 'error': None}
            
            # Fetch from external sources
            price_data = await self._fetch_price_external(token_address)
            if price_data:
                # Cache result
                await self._set_cache(cache_key, asdict(price_data), self.cache_ttl['price_data'])
                return {'success': True, 'data': asdict(price_data), 'error': None}
            else:
                return {'success': False, 'data': None, 'error': 'Price data not found'}
                
        except Exception as e:
            logger.error(f"Error getting price for {token_address}: {e}")
            return {'success': False, 'data': None, 'error': str(e)}

    async def get_liquidity_data(self, token_address: str) -> Dict[str, Any]:
        """
        Récupère les données de liquidité d'un token.
        
        Returns:
            Dict: {'success': bool, 'data': dict|None, 'error': str|None}
        """
        cache_key = f"liquidity:{token_address}"
        
        try:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return {'success': True, 'data': cached, 'error': None}
            
            # Fetch liquidity from DexScreener
            liquidity_data = await self._fetch_liquidity_external(token_address)
            if liquidity_data:
                await self._set_cache(cache_key, liquidity_data, self.cache_ttl['liquidity'])
                return {'success': True, 'data': liquidity_data, 'error': None}
            else:
                return {'success': False, 'data': None, 'error': 'Liquidity data not found'}
                
        except Exception as e:
            logger.error(f"Error getting liquidity for {token_address}: {e}")
            return {'success': False, 'data': None, 'error': str(e)}

    async def get_token_holders(self, token_address: str, limit: int = 100) -> Dict[str, Any]:
        """
        Récupère les détenteurs d'un token (placeholder - nécessite API spécialisée).
        
        Returns:
            Dict: {'success': bool, 'data': {'holders': list}|None, 'error': str|None}
        """
        cache_key = f"holders:{token_address}:{limit}"
        
        try:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return {'success': True, 'data': cached, 'error': None}
            
            # TODO: Intégrer API réelle (Solscan, Helius, etc.)
            logger.warning(f"Token holders API not yet implemented for {token_address}")
            placeholder_data = {"holders": []}
            
            await self._set_cache(cache_key, placeholder_data, self.cache_ttl['holders'])
            return {'success': True, 'data': placeholder_data, 'error': None}
            
        except Exception as e:
            logger.error(f"Error getting holders for {token_address}: {e}")
            return {'success': False, 'data': None, 'error': str(e)}

    async def get_token_transactions(self, token_address: str, limit: int = 100) -> Dict[str, Any]:
        """
        Récupère les transactions récentes d'un token (placeholder).
        
        Returns:
            Dict: {'success': bool, 'data': list|None, 'error': str|None}
        """
        cache_key = f"transactions:{token_address}:{limit}"
        
        try:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return {'success': True, 'data': cached, 'error': None}
            
            # TODO: Intégrer API réelle
            logger.warning(f"Token transactions API not yet implemented for {token_address}")
            placeholder_data = []
            
            await self._set_cache(cache_key, placeholder_data, self.cache_ttl['transactions'])
            return {'success': True, 'data': placeholder_data, 'error': None}
            
        except Exception as e:
            logger.error(f"Error getting transactions for {token_address}: {e}")
            return {'success': False, 'data': None, 'error': str(e)}

    async def get_historical_prices(self, token_address: str, timeframe: str = "1h", limit: int = 24) -> Dict[str, Any]:
        """
        Récupère l'historique des prix (via DexScreener).
        
        Returns:
            Dict: {'success': bool, 'data': list|None, 'error': str|None}
        """
        cache_key = f"history:{token_address}:{timeframe}:{limit}"
        
        try:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return {'success': True, 'data': cached, 'error': None}
            
            # Fetch from DexScreener
            history_data = await self._fetch_price_history_external(token_address, timeframe, limit)
            if history_data:
                await self._set_cache(cache_key, history_data, 300)  # 5 min cache
                return {'success': True, 'data': history_data, 'error': None}
            else:
                return {'success': False, 'data': None, 'error': 'Price history not found'}
                
        except Exception as e:
            logger.error(f"Error getting price history for {token_address}: {e}")
            return {'success': False, 'data': None, 'error': str(e)}

    # =================================
    # MÉTHODES PRIVÉES - SOURCES EXTERNES
    # =================================

    async def _fetch_token_info_external(self, token_address: str) -> Optional[CachedTokenInfo]:
        """Récupère info token depuis sources externes."""
        # Essayer DexScreener en premier
        try:
            url = f"{self.api_sources['dexscreener']}/dex/tokens/{token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('pairs'):
                        pair = data['pairs'][0]  # Premier pair trouvé
                        return CachedTokenInfo(
                            address=token_address,
                            symbol=pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                            name=pair.get('baseToken', {}).get('name', 'Unknown Token'),
                            decimals=int(pair.get('baseToken', {}).get('decimals', 9)),
                            price_usd=float(pair.get('priceUsd', 0)),
                            market_cap_usd=pair.get('marketCap'),
                            volume_24h_usd=pair.get('volume', {}).get('h24'),
                            created_at=None,  # DexScreener ne fournit pas cette info
                            liquidity_usd=pair.get('liquidity', {}).get('usd'),
                            timestamp=time.time(),
                            source='dexscreener'
                        )
        except Exception as e:
            logger.warning(f"DexScreener failed for {token_address}: {e}")

        # Fallback Jupiter
        try:
            url = f"{self.api_sources['jupiter']}/price?ids={token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    token_data = data.get('data', {}).get(token_address)
                    if token_data:
                        return CachedTokenInfo(
                            address=token_address,
                            symbol='UNKNOWN',  # Jupiter ne fournit que le prix
                            name='Unknown Token',
                            decimals=9,  # Default Solana
                            price_usd=float(token_data.get('price', 0)),
                            market_cap_usd=None,
                            volume_24h_usd=None,
                            created_at=None,
                            liquidity_usd=None,
                            timestamp=time.time(),
                            source='jupiter'
                        )
        except Exception as e:
            logger.warning(f"Jupiter failed for {token_address}: {e}")

        return None

    async def _fetch_price_external(self, token_address: str) -> Optional[CachedPriceData]:
        """Récupère prix depuis Jupiter API (le plus rapide)."""
        try:
            url = f"{self.api_sources['jupiter']}/price?ids={token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    token_data = data.get('data', {}).get(token_address)
                    if token_data:
                        return CachedPriceData(
                            address=token_address,
                            price_usd=float(token_data.get('price', 0)),
                            change_24h=None,  # Jupiter ne fournit pas le changement
                            volume_24h_usd=None,
                            timestamp=time.time(),
                            source='jupiter'
                        )
        except Exception as e:
            logger.warning(f"Jupiter price fetch failed for {token_address}: {e}")

        return None

    async def _fetch_liquidity_external(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Récupère liquidité depuis DexScreener."""
        try:
            url = f"{self.api_sources['dexscreener']}/dex/tokens/{token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('pairs'):
                        pair = data['pairs'][0]
                        return {
                            'liquidity_usd': pair.get('liquidity', {}).get('usd'),
                            'pool_address': pair.get('pairAddress'),
                            'dex': pair.get('dexId'),
                            'timestamp': time.time(),
                            'source': 'dexscreener',
                            'raw_data': pair  # Raw data pour analyses avancées
                        }
        except Exception as e:
            logger.warning(f"DexScreener liquidity fetch failed for {token_address}: {e}")

        return None

    async def _fetch_price_history_external(self, token_address: str, timeframe: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Récupère historique prix (placeholder - nécessite API premium)."""
        logger.warning(f"Price history API not yet implemented for {token_address}")
        return []

    # =================================
    # MÉTHODES CACHE REDIS
    # =================================

    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Récupère depuis le cache Redis."""
        try:
            if not self.redis_client:
                return None
            
            cached_data = await self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
        
        return None

    async def _set_cache(self, key: str, data: Dict[str, Any], ttl: int):
        """Stocke dans le cache Redis."""
        try:
            if not self.redis_client:
                return
            
            await self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")

    # =================================
    # MÉTRIQUES ET MONITORING
    # =================================

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        try:
            if not self.redis_client:
                return {'error': 'Redis not connected'}

            info = await self.redis_client.info('memory')
            keyspace = await self.redis_client.info('keyspace')
            
            return {
                'memory_used': info.get('used_memory_human'),
                'keys_total': sum(db.get('keys', 0) for db in keyspace.values()),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'connected': True
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e), 'connected': False}

    async def clear_cache_for_token(self, token_address: str):
        """Vide le cache pour un token spécifique."""
        try:
            if not self.redis_client:
                return
            
            patterns = [
                f"token_info:{token_address}",
                f"price:{token_address}",
                f"liquidity:{token_address}",
                f"holders:{token_address}:*",
                f"transactions:{token_address}:*",
                f"history:{token_address}:*"
            ]
            
            for pattern in patterns:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            logger.info(f"Cache cleared for token {token_address}")
        except Exception as e:
            logger.error(f"Error clearing cache for {token_address}: {e}")


# Factory function pour simplicité d'utilisation
async def create_market_data_cache(config=None) -> MarketDataCache:
    """Crée et initialise un MarketDataCache."""
    cache = MarketDataCache(config)
    await cache.__aenter__()
    return cache 