import os
from enum import Enum

class Config:
    # Core
    DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
    UPDATE_INTERVAL = 60  # Seconds
    
    # Security
    RUGCHECK_THRESHOLD = 85
    BUNDLED_SUPPLY_LIMIT = 0.25
    
    # Trading
    RISK_PER_TRADE = 0.02  # 2%
    MAX_SLIPPAGE = 0.005  # 0.5%

class BLACKLIST_REASON(Enum):
    RUG_PULL = "rug_pull"
    FAKE_VOLUME = "fake_volume"
    SUSPECT_DEV = "suspicious_developer"