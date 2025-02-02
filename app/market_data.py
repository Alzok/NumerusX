import requests
from cachetools import TTLCache
import logging
from config import Config
from typing import Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential

class MarketDataFetcher:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=600)  # Cache 10 minutes
        self.logger = logging.getLogger('MarketData')
        self.headers = {"Authorization": f"Bearer {Config.JUPITER_API_KEY}"} if Config.JUPITER_API_KEY else {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_solana_pairs(self) -> List[Dict]:
        """Récupère les paires Solana depuis Jupiter et DexScreener."""
        try:
            if 'solana_pairs' in self.cache:
                return self.cache['solana_pairs']

            # Essayer Jupiter API
            response = requests.get(f"{Config.JUPITER_SWAP_URL}/tokens", headers=self.headers, timeout=15)
            if response.status_code == 200:
                tokens = response.json().get('tokens', [])
                self.cache['solana_pairs'] = tokens
                return tokens

            # Fallback vers DexScreener
            dex_response = requests.get("https://api.dexscreener.com/latest/dex/chains/solana", timeout=10)
            pairs = dex_response.json().get('pairs', [])
            self.cache['solana_pairs'] = pairs
            return pairs
        except Exception as e:
            self.logger.error(f"Erreur récupération paires: {str(e)}")
            return []

    def get_historical_data(self, pair_address: str) -> Dict:
        """Récupère les données de prix et de volume sur Jupiter et DexScreener."""
        try:
            if pair_address in self.cache:
                return self.cache[pair_address]
            
            # Essayer Jupiter API
            jup_data = requests.get(f"{Config.JUPITER_PRICE_URL}/id/{pair_address}", headers=self.headers, timeout=10).json()
            if 'data' in jup_data:
                self.cache[pair_address] = jup_data['data']
                return jup_data['data']
            
            # Fallback DexScreener
            dex_data = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}", timeout=10).json()
            self.cache[pair_address] = dex_data
            return dex_data
        except Exception as e:
            self.logger.error(f"Erreur historique {pair_address}: {str(e)}")
            return {}
