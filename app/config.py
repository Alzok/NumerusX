import os

class Config:
    # Paramètres de sécurité
    JUPITER_STRICT_LIST = "https://token.jup.ag/strict"
    MIN_LIQUIDITY = 25000  # $25k
    VOLUME_ZSCORE_LIMIT = 2.5
    TRADE_THRESHOLD = 0.65
    SLIPPAGE = 0.015
    MAX_ORDER_SIZE = 1000  # USD
    
    # Paramètres de performance
    DB_PATH = os.getenv("DB_PATH", "/data/dex_data.db")
    MAX_POSITIONS = 5
    UPDATE_INTERVAL = 60  # Secondes
    GUI_REFRESH_RATE = 2.0  # Secondes
    INITIAL_BALANCE = 10000.0
    
    # Stratégie
    SCORE_WEIGHTS = (0.4, 0.3, 0.2, 0.1)  # Momentum, Volume, Structure, Risque
    
    # Solana
    SOLANA_RPC = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    BASE_ASSET = "So11111111111111111111111111111111111111112"
    JUPITER_SWAP_URL = "https://api.jup.ag/swap/v1"
    JUPITER_PRICE_URL = "https://api.jup.ag/price/v2"
    JUPITER_API_KEY = os.getenv("JUPITER_API_KEY", "")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")