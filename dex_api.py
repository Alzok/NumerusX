import requests
from tenacity import retry, wait_exponential

class DexAPI:
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_pair_data(self, chain='eth'):
        response = requests.get(
            f"{Config.DEXSCREENER_API}/pairs/{chain}",
            headers={'Accept': 'application/json'},
            timeout=5
        )
        return response.json()['pairs']