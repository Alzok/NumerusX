import requests
import re
from config import Config

class SecurityManager:
    @staticmethod
    def verify_contract(address: str) -> bool:
        if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
            return False
            
        try:
            response = requests.get(
                f"https://api.rugcheck.xyz/v1/contracts/{address}/score",
                headers={"x-api-key": os.getenv("RUGCHECK_API_KEY")},
                timeout=5
            )
            return response.json().get('score', 0) >= Config.RUGCHECK_THRESHOLD
        except Exception as e:
            logging.error(f"Verification failed: {str(e)}")
            return False