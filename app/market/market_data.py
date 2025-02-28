import aiohttp
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("market_data")

class MarketDataProvider:
    """Classe centralisée pour la gestion des données de marché provenant de différentes sources."""
    
    def __init__(self, cache_ttl: int = 60, cache_max_size: int = 1000):
        """
        Initialise le fournisseur de données de marché.
        
        Args:
            cache_ttl: Durée de vie du cache en secondes
            cache_max_size: Taille maximale du cache
        """
        self.session = None
        # Cache pour les différents types de données
        self.price_cache = TTLCache(maxsize=cache_max_size, ttl=cache_ttl)
        self.token_info_cache = TTLCache(maxsize=cache_max_size, ttl=cache_ttl * 5)  # Données de token moins volatiles
        self.liquidity_cache = TTLCache(maxsize=cache_max_size, ttl=cache_ttl // 2)  # Données de liquidité plus volatiles
        
        # Limites de taux pour différentes API
        self.rate_limits = {
            "jupiter": {"calls": 0, "last_reset": time.time(), "limit": 50, "window": 60},
            "dexscreener": {"calls": 0, "last_reset": time.time(), "limit": 30, "window": 60},
            "raydium": {"calls": 0, "last_reset": time.time(), "limit": 40, "window": 60},
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
        
        Args:
            token_address: Adresse du token Solana
            reference_token: Token de référence pour le prix
            
        Returns:
            Dict contenant les informations de prix
        """
        cache_key = f"{token_address}_{reference_token}_price"
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]
            
        # Essayer Jupiter d'abord, puis DexScreener comme fallback
        try:
            price_data = await self._get_jupiter_price(token_address, reference_token)
        except Exception as e:
            logger.warning(f"Échec de la récupération du prix depuis Jupiter: {e}")
            try:
                price_data = await self._get_dexscreener_price(token_address)
            except Exception as inner_e:
                logger.error(f"Échec de la récupération du prix depuis DexScreener: {inner_e}")
                raise Exception(f"Impossible d'obtenir le prix pour {token_address} depuis toutes les sources")
                
        # Stocker dans le cache
        self.price_cache[cache_key] = price_data
        return price_data
        
    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Obtient les informations d'un token via plusieurs sources.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Dict contenant les informations du token
        """
        if token_address in self.token_info_cache:
            return self.token_info_cache[token_address]
            
        # Essayer Jupiter d'abord, puis DexScreener comme fallback
        try:
            token_data = await self._get_jupiter_token_info(token_address)
        except Exception as e:
            logger.warning(f"Échec de la récupération des infos depuis Jupiter: {e}")
            try:
                token_data = await self._get_dexscreener_token_info(token_address)
            except Exception as inner_e:
                logger.error(f"Échec de la récupération des infos depuis DexScreener: {inner_e}")
                raise Exception(f"Impossible d'obtenir les infos pour {token_address}")
                
        self.token_info_cache[token_address] = token_data
        return token_data
        
    async def get_liquidity_data(self, token_address: str, pool_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtient les données de liquidité pour un token.
        
        Args:
            token_address: Adresse du token
            pool_address: Adresse optionnelle du pool
            
        Returns:
            Données de liquidité normalisées
        """
        cache_key = f"{token_address}_{pool_address}_liquidity" if pool_address else f"{token_address}_liquidity"
        
        if cache_key in self.liquidity_cache:
            return self.liquidity_cache[cache_key]
            
        try:
            if pool_address:
                liquidity_data = await self._get_specific_pool_liquidity(token_address, pool_address)
            else:
                # Obtenir la meilleure source de liquidité disponible
                liquidity_data = await self._get_best_liquidity_source(token_address)
                
            self.liquidity_cache[cache_key] = liquidity_data
            return liquidity_data
        except Exception as e:
            logger.error(f"Échec de la récupération des données de liquidité: {e}")
            raise
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _get_jupiter_price(self, token_address: str, reference_token: str) -> Dict[str, Any]:
        """Récupère le prix d'un token depuis Jupiter API."""
        await self._check_rate_limit("jupiter")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"https://price.jup.ag/v4/price?ids={token_address}&vsToken={reference_token}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Jupiter API a retourné un code d'état {response.status}")
                
            data = await response.json()
            
            # Normaliser le format de données
            price_data = {
                "price": float(data["data"][token_address]["price"]) if token_address in data["data"] else None,
                "source": "jupiter",
                "timestamp": time.time(),
                "reference_token": reference_token
            }
            
            return price_data
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _get_dexscreener_price(self, token_address: str) -> Dict[str, Any]:
        """Récupère le prix d'un token depuis DexScreener API."""
        await self._check_rate_limit("dexscreener")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"DexScreener API a retourné un code d'état {response.status}")
                
            data = await response.json()
            
            # Normaliser le format de données
            if not data.get("pairs") or len(data["pairs"]) == 0:
                raise Exception(f"Aucune paire trouvée pour {token_address}")
                
            # Prendre la première paire avec le plus de liquidité
            pairs = sorted(data["pairs"], key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
            best_pair = pairs[0]
            
            price_data = {
                "price": float(best_pair["priceUsd"]),
                "source": "dexscreener",
                "timestamp": time.time(),
                "reference_token": "USD",
                "volume24h": float(best_pair.get("volume", {}).get("h24", 0)),
                "liquidity": float(best_pair.get("liquidity", {}).get("usd", 0))
            }
            
            return price_data
            
    async def _get_jupiter_token_info(self, token_address: str) -> Dict[str, Any]:
        """Récupère les informations d'un token depuis Jupiter."""
        # Implémentation similaire à _get_jupiter_price mais pour les infos token
        pass
        
    async def _get_dexscreener_token_info(self, token_address: str) -> Dict[str, Any]:
        """Récupère les informations d'un token depuis DexScreener."""
        # Implémentation similaire à _get_dexscreener_price mais pour les infos token
        pass
        
    async def _get_specific_pool_liquidity(self, token_address: str, pool_address: str) -> Dict[str, Any]:
        """Récupère les données de liquidité pour un pool spécifique."""
        # Implémentation pour récupérer les données de liquidité d'un pool spécifique
        pass
        
    async def _get_best_liquidity_source(self, token_address: str) -> Dict[str, Any]:
        """Détermine et récupère la meilleure source de liquidité pour un token."""
        # Logique pour obtenir la meilleure source de liquidité
        pass
        
    async def _check_rate_limit(self, api_name: str) -> None:
        """
        Vérifie et gère les limites de taux pour une API spécifique.
        Attend si nécessaire pour éviter de dépasser les limites.
        """
        current_time = time.time()
        rate_info = self.rate_limits[api_name]
        
        # Réinitialiser le compteur si la fenêtre de temps est passée
        if current_time - rate_info["last_reset"] > rate_info["window"]:
            rate_info["calls"] = 0
            rate_info["last_reset"] = current_time
            
        # Vérifier si nous approchons de la limite
        if rate_info["calls"] >= rate_info["limit"]:
            wait_time = rate_info["window"] - (current_time - rate_info["last_reset"]) + 1
            logger.warning(f"Limite de taux atteinte pour {api_name}. Attente de {wait_time:.2f} secondes.")
            await asyncio.sleep(wait_time)
            # Réinitialiser après avoir attendu
            rate_info["calls"] = 0
            rate_info["last_reset"] = time.time()
            
        # Incrémenter le compteur
        rate_info["calls"] += 1
        
    def get_supported_dexes(self) -> List[str]:
        """Renvoie la liste des DEX pris en charge par le fournisseur de données."""
        return ["Jupiter", "Raydium", "Orca"]
        
    async def get_historical_prices(self, token_address: str, timeframe: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les données historiques de prix pour un token.
        
        Args:
            token_address: Adresse du token
            timeframe: Intervalle de temps (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Nombre de points de données
            
        Returns:
            Liste de dictionnaires contenant les données historiques
        """
        # Implémentation pour récupérer les données historiques
        pass
