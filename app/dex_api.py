import requests
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from typing import Dict, List
from config import Config

class DexAPI:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=600)  # Cache augmenté
        self.logger = logging.getLogger('DexAPI')
        self.headers = {"Authorization": f"Bearer {Config.JUPITER_API_KEY}"} if Config.JUPITER_API_KEY else {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_solana_pairs(self) -> List[Dict]:
        """Récupération robuste des paires avec cache et fallback"""
        try:
            if 'solana_pairs' in self.cache:
                return self.cache['solana_pairs']

            # Essayer Jupiter d'abord
            jup_pairs = requests.get(
                f"{Config.JUPITER_SWAP_URL}/tokens",
                headers=self.headers,
                timeout=15
            ).json().get('tokens', [])
            
            if jup_pairs:
                self.cache['solana_pairs'] = jup_pairs
                return jup_pairs

            # Fallback sur DexScreener
            dex_data = requests.get("https://api.dexscreener.com/latest/dex/chains/solana", timeout=10).json()
            pairs = dex_data.get('pairs', [])
            self.cache['solana_pairs'] = pairs
            return pairs

        except Exception as e:
            self.logger.error(f"Erreur récupération paires: {str(e)}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def get_jupiter_quote(self, input_mint: str, output_mint: str, amount: int) -> Dict:
        """Gestion complète des erreurs Jupiter API v1"""
        try:
            response = requests.get(
                f"{Config.JUPITER_SWAP_URL}/quote",
                params={
                    "inputMint": input_mint,
                    "outputMint": output_mint,
                    "amount": str(amount),
                    "slippageBps": str(int(Config.SLIPPAGE * 10000)),
                    "onlyDirectRoutes": "false"
                },
                headers=self.headers,
                timeout=20
            )
            
            if response.status_code == 429:
                raise requests.exceptions.HTTPError("Rate limit dépassé")
                
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Erreur Jupiter API: {e.response.text if e.response else str(e)}")
            return {}

    def get_historical_data(self, pair_address: str) -> Dict:
        """Données hybrides avec conversion de format automatique"""
        try:
            # Priorité à Jupiter
            jup_data = requests.get(
                f"{Config.JUPITER_PRICE_URL}/id/{pair_address}",
                headers=self.headers,
                timeout=15
            ).json()
            
            if jup_data.get('data'):
                return self._convert_jupiter_format(jup_data['data'])
                
            # Fallback DexScreener
            dex_data = requests.get(
                f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}",
                timeout=10
            ).json()
            return self._convert_dexscreener_format(dex_data)
            
        except Exception as e:
            self.logger.error(f"Erreur données historiques: {str(e)}")
            return {}

    def _convert_jupiter_format(self, data: Dict) -> Dict:
        """Adaptation du format Jupiter au schéma standard"""
        return {
            'pairAddress': data.get('id'),
            'baseToken': {'address': data.get('mint')},
            'priceUsd': data.get('price'),
            'liquidity': {'usd': data.get('liquidity')},
            'volume': {'h24': data.get('volume24h')}
        }

    def _convert_dexscreener_format(self, data: Dict) -> Dict:
        """Normalisation des données DexScreener"""
        pair = data.get('pair', {})
        return {
            'pairAddress': pair.get('address'),
            'baseToken': {'address': pair.get('baseToken', {}).get('address')},
            'priceUsd': pair.get('priceUsd'),
            'liquidity': {'usd': pair.get('liquidity', {}).get('usd')},
            'volume': {'h24': pair.get('volume', {}).get('h24')}
        }