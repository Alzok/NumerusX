import requests
from cachetools import TTLCache
from config import Config
from tenacity import retry, wait_exponential, stop_after_attempt
import logging

class DexAPI:
    def __init__(self):
        self.cache = TTLCache(maxsize=500, ttl=300)
        self.logger = logging.getLogger('DexAPI')

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def get_solana_pairs(self):
        """Récupère les paires Solana avec cache et gestion d'erreurs améliorée"""
        try:
            if 'solana_pairs' in self.cache:
                return self.cache['solana_pairs']
            
            response = requests.get(
                "https://api.dexscreener.com/latest/dex/chains/solana",
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            pairs = data.get('pairs', [])
            
            self.cache['solana_pairs'] = pairs
            self.logger.info(f"Récupération réussie de {len(pairs)} paires")
            return pairs
            
        except requests.RequestException as e:
            self.logger.error(f"Échec API DexScreener: {str(e)}")
            raise
        except KeyError as e:
            self.logger.error("Structure de réponse API invalide")
            raise ValueError("Format de données inattendu") from e

    def get_historical_data(self, pair_address: str):
        """Récupère les données historiques avec cache"""
        cache_key = f"history_{pair_address}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            response = requests.get(
                f"https://api.dexscreener.com/solana/{pair_address}/24h",
                timeout=10
            )
            data = response.json()
            self.cache[cache_key] = data
            return data
        except Exception as e:
            self.logger.warning(f"Erreur historique pour {pair_address}: {str(e)}")
            return {}