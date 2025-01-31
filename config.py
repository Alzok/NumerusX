import os
import dotenv
from enum import Enum

dotenv.load_dotenv()

class Config:
    # API Endpoints
    DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
    RUGCHECK_API = "https://api.rugcheck.xyz/v1"
    POCKET_UNIVERSE_API = "https://api.pocketuniverse.ai/v1"
    BANANA_GUN_API = "https://api.bananagun.io/v1"
    
    # API Keys
    RUGCHECK_KEY = os.getenv("RUGCHECK_KEY")
    POCKET_UNIVERSE_KEY = os.getenv("POCKET_UNIVERSE_KEY")
    BANANA_GUN_KEY = os.getenv("BANANA_GUN_KEY")
    ETHERSCAN_KEY = os.getenv("ETHERSCAN_KEY")
    
    # Telegram
    TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Trading Parameters
    SLIPPAGE = 0.8
    GAS_STRATEGY = "rapid"
    RISK_PER_TRADE = 0.02
    
    # Database
    DB_NAME = "dex_analytics.db"

class BLACKLIST_REASON(Enum):
    RUGCHECK_FAIL = "rugcheck_failed"
    BUNDLED_SUPPLY = "bundled_supply"
    FAKE_VOLUME = "fake_volume"