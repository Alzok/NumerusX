import os
from enum import Enum

class Config:
    # API Endpoints
    DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
    BANANA_GUN_API = "https://pro.bananagun.io/v3"
    RUGCHECK_API = "https://api.rugcheck.xyz/v2"
    
    # Paramètres de Sécurité
    BUNDLED_THRESHOLD = 0.25  # 25%+ = supply suspecte
    SAFETY_SCORE_MIN = 82
    
    # Trading
    RISK_PER_TRADE = 0.03  # 3% du capital
    SLIPPAGE_AUTO = True
    
    # Base de Données
    DB_NAME = "dex_analytics.db"

class BLACKLIST_REASON(Enum):
    RUG_PULL = "rug_pull_detected"
    FAKE_VOLUME = "fake_volume"
    BUNDLED = "bundled_supply"