import requests
from tenacity import retry, stop_after_attempt, wait_exponential

class DexAPI:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_pairs(self, chain: str = 'ethereum'):
        response = requests.get(
            f"{Config.DEXSCREENER_API}/pairs/{chain}",
            timeout=10
        )
        response.raise_for_status()
        return self._filter_pairs(response.json()['pairs'])

    def _filter_pairs(self, pairs):
        return [p for p in pairs if p['liquidity']['usd'] > 10000]