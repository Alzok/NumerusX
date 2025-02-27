import os
import time
import requests
import json
from cachetools import TTLCache
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional, Tuple

from utils.logger import DexLogger

logger = DexLogger("MarketDataFetcher")

class MarketDataFetcher:
    """
    Classe centralisée pour récupérer toutes les données de marché depuis Jupiter API.
    Implémente des mécanismes de cache et de gestion d'erreurs.
    """
    def __init__(self):
        self.jupiter_api_key = os.getenv("JUPITER_API_KEY")
        self.base_url = "https://quote-api.jup.ag/v6"
        self.pairs_cache = TTLCache(maxsize=100, ttl=300)  # Cache de 5 minutes
        self.quotes_cache = TTLCache(maxsize=500, ttl=15)  # Cache de 15 secondes
        self.token_info_cache = TTLCache(maxsize=1000, ttl=3600)  # Cache d'1 heure
        self.last_etag = None
        self.last_pairs_fetch = None
        
    def _get_headers(self):
        """Retourne les en-têtes HTTP pour les requêtes à l'API Jupiter"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.jupiter_api_key:
            headers["Authorization"] = f"Bearer {self.jupiter_api_key}"
        if self.last_etag:
            headers["If-None-Match"] = self.last_etag
        return headers
        
    def get_solana_pairs(self, force_refresh=False) -> List[Dict]:
        """
        Récupère la liste des paires disponibles sur Jupiter avec mise en cache optimisée.
        Utilise If-Modified-Since pour minimiser les appels API.
        """
        cache_key = "all_pairs"
        
        # Retourne du cache si disponible et pas de rafraîchissement forcé
        if not force_refresh and cache_key in self.pairs_cache:
            return self.pairs_cache[cache_key]
            
        try:
            headers = self._get_headers()
            if self.last_pairs_fetch and not force_refresh:
                headers["If-Modified-Since"] = self.last_pairs_fetch.strftime("%a, %d %b %Y %H:%M:%S GMT")
                
            response = requests.get(f"{self.base_url}/pairs", headers=headers)
            
            # Si les données n'ont pas été modifiées, retourne le cache
            if response.status_code == 304:
                return self.pairs_cache.get(cache_key, [])
                
            if response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des paires: {response.status_code}, {response.text}")
                return self.pairs_cache.get(cache_key, [])
                
            # Mise à jour du cache et des métadonnées
            if "ETag" in response.headers:
                self.last_etag = response.headers["ETag"]
                
            self.last_pairs_fetch = datetime.utcnow()
            pairs_data = response.json()
            self.pairs_cache[cache_key] = pairs_data
            logger.info(f"Récupération de {len(pairs_data)} paires depuis Jupiter API")
            return pairs_data
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération des paires: {str(e)}")
            return self.pairs_cache.get(cache_key, [])
            
    def get_jupiter_quote(self, input_mint: str, output_mint: str, amount: int, 
                         slippage_bps: int = 50) -> Dict:
        """
        Récupère une cotation pour un swap depuis l'API Jupiter avec gestion de cache.
        Normalise les données de sortie pour une utilisation cohérente.
        """
        cache_key = f"{input_mint}_{output_mint}_{amount}_{slippage_bps}"
        
        if cache_key in self.quotes_cache:
            return self.quotes_cache[cache_key]
            
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps
            }
            
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/quote", params=params, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erreur lors de la récupération de la cotation: {response.status_code}, {response.text}")
                return None
                
            quote_data = response.json()
            
            # Normalisation des données pour une utilisation cohérente
            normalized_data = {
                "input_mint": input_mint,
                "output_mint": output_mint,
                "input_amount": amount,
                "output_amount": int(quote_data.get("outAmount", 0)),
                "price": float(quote_data.get("outAmount", 0)) / float(amount) if amount > 0 else 0,
                "fee": quote_data.get("otherAmountThreshold", 0),
                "slippage": slippage_bps / 10000,  # Conversion en pourcentage
                "routes": quote_data.get("routePlan", []),
                "timestamp": int(time.time()),
                "raw_data": quote_data
            }
            
            self.quotes_cache[cache_key] = normalized_data
            return normalized_data
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération de la cotation: {str(e)}")
            return None
            
    def get_historical_data(self, input_mint: str, output_mint: str, 
                           timeframe: str = "1d", limit: int = 100) -> Dict:
        """
        Récupère les données historiques pour une paire.
        Normalise les données pour être cohérent avec le reste de l'API.
        """
        try:
            # Utiliser l'endpoint Jupiter pour les données historiques
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "timeframe": timeframe,
                "limit": limit
            }
            
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/price-history", params=params, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des données historiques: {response.status_code}, {response.text}")
                return None
                
            history_data = response.json()
            
            # Normalisation du format pour être cohérent
            normalized_data = {
                "pair": f"{input_mint}/{output_mint}",
                "timeframe": timeframe,
                "data": [
                    {
                        "time": item.get("time", 0),
                        "price": item.get("price", 0),
                        "volume": item.get("volume", 0)
                    }
                    for item in history_data.get("data", [])
                ],
                "timestamp": int(time.time())
            }
            
            return normalized_data
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération des données historiques: {str(e)}")
            return None
            
    def check_token_liquidity(self, token_mint: str) -> Dict:
        """
        Vérifie la liquidité d'un token sur les différents pools.
        Retourne des informations sur la profondeur et les pools disponibles.
        """
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/token-info/{token_mint}", headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erreur lors de la vérification de liquidité: {response.status_code}, {response.text}")
                return None
                
            token_data = response.json()
            
            # Analyse de la liquidité en USD
            total_liquidity_usd = 0
            pools = token_data.get("pools", [])
            
            for pool in pools:
                total_liquidity_usd += pool.get("liquidityUsd", 0)
                
            return {
                "token_mint": token_mint,
                "total_liquidity_usd": total_liquidity_usd,
                "pool_count": len(pools),
                "pools": pools,
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Exception lors de la vérification de liquidité: {str(e)}")
            return None
