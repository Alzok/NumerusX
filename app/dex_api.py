import requests
from cachetools import TTLCache
from tenacity import retry, wait_exponential, stop_after_attempt
import logging
from config import Config
import json

class DexAPI:
    def __init__(self):
        self.cache = TTLCache(maxsize=500, ttl=300)
        self.logger = logging.getLogger('DexAPI')
        self.headers = {
            "Authorization": f"Bearer {Config.JUPITER_API_KEY}",
            "Content-Type": "application/json"
        } if Config.JUPITER_API_KEY else {}

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def get_solana_pairs(self):
        """Récupère les paires Solana avec cache et gestion d'erreurs"""
        cache_key = 'solana_pairs'
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = requests.get(
                "https://api.jup.ag/tokens/v1/mints/tradable",
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            
            pairs = response.json()['mints']
            self.cache[cache_key] = pairs
            return pairs

        except requests.RequestException as e:
            self.logger.error(f"Erreur API: {str(e)}")
            return []

    def get_historical_data(self, pair_address: str):
        """Récupère les données historiques avec cache"""
        cache_key = f"history_{pair_address}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = requests.get(
                f"https://api.jup.ag/price/v2/{pair_address}",
                params={'range': '24H'},
                headers=self.headers,
                timeout=10
            )
            data = response.json()
            self.cache[cache_key] = data
            return data
        except Exception as e:
            self.logger.error(f"Erreur historique: {str(e)}")
            return {}

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=5),
        stop=stop_after_attempt(2)
    )
    def get_quote(self, mint_in: str, mint_out: str, amount: int):
        """Obtient un devis de swap avec gestion de rate limits"""
        try:
            response = requests.get(
                f"{Config.JUPITER_SWAP_URL}/quote",
                params={
                    "inputMint": mint_in,
                    "outputMint": mint_out,
                    "amount": amount,
                    "slippageBps": int(Config.SLIPPAGE * 100)
                },
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 429:
                raise requests.exceptions.HTTPError("Rate limit exceeded")
                
            response.raise_for_status()
            return response.json()
            
        except requests.HTTPError as e:
            self.logger.warning(f"Erreur API: {str(e)}")
            return None