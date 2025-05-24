# config.py
import os
from dotenv import load_dotenv
import json

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la persistance de Chroma
CHROMA_DB_DIR = "./db"
os.environ["CHROMA_DB_DIRECTORY"] = CHROMA_DB_DIR

# Paramètres par défaut
DEFAULT_OLLAMA_URL = "http://localhost:11434/v1/completions"
DEFAULT_MODEL = "deepseek-r1:1.5b"

# Variables Globales de Configuration
CURRENT_MODE = "Local"         # "Local" ou "Distant"
CURRENT_MODEL = DEFAULT_MODEL  # Utilisé en mode Local
DATA_LANGUAGE = "Python"       # Langage de programmation

# Pour le mode Distant
REMOTE_API = ""                # Endpoint API pour le mode distant (optionnel)
REMOTE_API_KEY_DEEPSEEK = ""   # Clé API pour Deepseek
REMOTE_API_KEY_OPENAI = ""     # Clé API pour OpenAI
REMOTE_API_OPTION = "Deepseek" # Options possibles : "Deepseek" ou "OpenAI"
REMOTE_API_VARIANT = ""        # Pour Deepseek, forcé à "deepseek-reasoner (r1)"; pour OpenAI, options : "o3", "mini", "hgig", "o1"

# Indicateur pour le modèle local
LOCAL_MODEL_READY = False      # Indique si le modèle local a été téléchargé

# Dictionnaire des coûts par token (en dollars)
COSTS = {
    "OpenAI": {
         "o3": 0.00003,
         "mini": 0.00002,
         "hgig": 0.00004,
         "o1": 0.00002
    },
    "Deepseek": {
         "deepseek-reasoner (r1)": 0.00001
    }
}

class Config:
    # Configuration de l'application
    APP_NAME = os.getenv("APP_NAME", "NumerusX")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    DEV_MODE = os.getenv("DEV_MODE", "False").lower() == "true" # Mode développement
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*") # Comma-separated list or * for all
    
    # Configuration de sécurité
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key_change_in_production")
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))  # En secondes (1 heure par défaut)
    # Clés pour le chiffrement des données sensibles (ex: clé privée Solana)
    # Ces clés DOIVENT être définies dans l'environnement en production et ne pas avoir de défauts ici.
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") 
    ENCRYPTED_SOLANA_PK = os.getenv("ENCRYPTED_SOLANA_PK") # Chemin vers la clé privée chiffrée ou la clé elle-même
    
    # Configuration de base de données
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join('data', 'numerusx.db')}")
    DB_PATH = os.getenv("DB_PATH", os.path.join("data", "numerusx.db"))
    
    # Configuration Solana
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    SOLANA_NETWORK = os.getenv("SOLANA_NETWORK", "mainnet-beta")
    WALLET_PATH = os.getenv("WALLET_PATH", os.path.join("keys", "solana_wallet.json"))
    BACKUP_WALLET_PATH = os.getenv("BACKUP_WALLET_PATH") # Chemin vers un portefeuille de secours, optionnel
    DEFAULT_FEE_PER_SIGNATURE_LAMPORTS = int(os.getenv("DEFAULT_FEE_PER_SIGNATURE_LAMPORTS", "5000"))
    
    # Configuration Jupiter
    JUPITER_API_BASE_URL = os.getenv("JUPITER_API_BASE_URL", "https://quote-api.jup.ag")
    JUPITER_QUOTE_URL_SUFFIX = "/v6/quote"
    JUPITER_PRICE_URL_SUFFIX = "/v4/price"
    JUPITER_API_KEY = os.getenv("JUPITER_API_KEY")
    
    # DexScreener (placeholder, comme mentionné dans la tâche 1.3)
    DEXSCREENER_API_URL = os.getenv("DEXSCREENER_API_URL", "https://api.dexscreener.com/latest/dex")
    DEXSCREENER_API_KEY = os.getenv("DEXSCREENER_API_KEY")
    
    # Paramètres trading
    BASE_ASSET = os.getenv("BASE_ASSET", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")  # USDC sur Solana
    SLIPPAGE_BPS = int(os.getenv("SLIPPAGE_BPS", "50")) # Slippage en points de base (50bps = 0.5%)
    MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "10000"))  # Liquidité minimale en USD
    MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
    MAX_ORDER_SIZE_USD = float(os.getenv("MAX_ORDER_SIZE_USD", "1000.0"))
    TRADE_CONFIDENCE_THRESHOLD = float(os.getenv("TRADE_CONFIDENCE_THRESHOLD", "0.65"))
    TRADING_UPDATE_INTERVAL_SECONDS = int(os.getenv("TRADING_UPDATE_INTERVAL_SECONDS", "60"))
    INITIAL_PORTFOLIO_BALANCE_USD = float(os.getenv("INITIAL_PORTFOLIO_BALANCE_USD", "1000.0"))
    MIN_ORDER_VALUE_USD = float(os.getenv("MIN_ORDER_VALUE_USD", "10.0"))

    # Paramètres spécifiques au moteur de trading (pour le second TradingEngine)
    SIGNAL_EXPIRY_SECONDS = int(os.getenv("SIGNAL_EXPIRY_SECONDS", "300")) # 5 minutes
    PRICE_CHECK_INTERVAL_SECONDS = int(os.getenv("PRICE_CHECK_INTERVAL_SECONDS", "30"))
    ORDER_UPDATE_INTERVAL_SECONDS = int(os.getenv("ORDER_UPDATE_INTERVAL_SECONDS", "15"))
    EXECUTE_MARKET_ORDERS = os.getenv("EXECUTE_MARKET_ORDERS", "True").lower() == "true"
    AUTO_CLOSE_POSITIONS = os.getenv("AUTO_CLOSE_POSITIONS", "True").lower() == "true"

    # Configuration UI
    UI_UPDATE_INTERVAL_SECONDS = int(os.getenv("UI_UPDATE_INTERVAL_SECONDS", "2"))
    
    # Configuration API générique
    DEFAULT_API_RATE_LIMIT_WAIT_SECONDS = float(os.getenv("DEFAULT_API_RATE_LIMIT_WAIT_SECONDS", "0.2"))
    API_RATE_LIMITS = json.loads(os.getenv("API_RATE_LIMITS", '''{
        "jupiter": {"limit": 100, "window_seconds": 60, "default_wait": 0.2},
        "dexscreener": {"limit": 120, "window_seconds": 60, "default_wait": 0.5},
        "raydium": {"limit": 100, "window_seconds": 60, "default_wait": 0.2}
    }'''))

    # Configuration du Cache pour MarketData
    MARKET_DATA_CACHE_TTL_SECONDS = int(os.getenv("MARKET_DATA_CACHE_TTL_SECONDS", "60"))
    MARKET_DATA_CACHE_MAX_SIZE = int(os.getenv("MARKET_DATA_CACHE_MAX_SIZE", "1000"))

    # Chemins et Logs
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "numerusx.log") # Nom du fichier de log
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    @classmethod
    def get_db_path(cls):
        """Renvoie le chemin complet de la base de données, en créant le répertoire parent si nécessaire."""
        db_dir = os.path.dirname(cls.DB_PATH)
        if db_dir: # S'assurer que db_dir n'est pas une chaîne vide si DB_PATH est juste un nom de fichier
            os.makedirs(db_dir, exist_ok=True)
        return cls.DB_PATH

    @classmethod
    def get_jupiter_quote_url(cls):
        return f"{cls.JUPITER_API_BASE_URL.rstrip('/')}{cls.JUPITER_QUOTE_URL_SUFFIX}"

    @classmethod
    def get_jupiter_price_url(cls):
        return f"{cls.JUPITER_API_BASE_URL.rstrip('/')}{cls.JUPITER_PRICE_URL_SUFFIX}"
    
    @classmethod
    def get_log_dir(cls):
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        return cls.LOG_DIR

    @classmethod
    def get_log_file_path(cls):
        """Renvoie le chemin complet du fichier de log."""
        return os.path.join(cls.get_log_dir(), cls.LOG_FILE_NAME)

def update_configuration(mode, model, language, api_option, remote_api, key_deepseek, key_openai, remote_token_limit, api_variant):
    """
    Met à jour la configuration globale.
    
    Args:
        mode (str): "Local" ou "Distant".
        model (str): Le modèle utilisé en mode Local.
        language (str): Langage de programmation.
        api_option (str): Fournisseur d'API distante ("Deepseek" ou "OpenAI").
        remote_api (str): Endpoint API distant (optionnel).
        key_deepseek (str): Clé API pour Deepseek.
        key_openai (str): Clé API pour OpenAI.
        remote_token_limit (int): Limite de tokens (utilisé pour le calcul du coût).
        api_variant (str): Variante du modèle distant sélectionné.
    
    Returns:
        str: Un message de confirmation de mise à jour de la configuration.
    """
    global CURRENT_MODE, CURRENT_MODEL, DATA_LANGUAGE, REMOTE_API, REMOTE_API_KEY_DEEPSEEK, REMOTE_API_KEY_OPENAI, REMOTE_API_OPTION, REMOTE_API_VARIANT
    CURRENT_MODE = mode
    # En mode distant, le modèle local n'est pas utilisé
    CURRENT_MODEL = model if mode == "Local" else ""
    DATA_LANGUAGE = language
    if mode == "Distant":
        REMOTE_API = remote_api  # Si vide, l'appel utilisera l'endpoint par défaut
        REMOTE_API_OPTION = api_option
        REMOTE_API_KEY_DEEPSEEK = key_deepseek
        REMOTE_API_KEY_OPENAI = key_openai
        REMOTE_API_VARIANT = api_variant
    else:
        REMOTE_API = ""
        REMOTE_API_OPTION = ""
        REMOTE_API_KEY_DEEPSEEK = ""
        REMOTE_API_KEY_OPENAI = ""
        REMOTE_API_VARIANT = ""
    return f"Configuration mise à jour : Mode={mode}, Langage={language}, API distante={api_option}, Variante={REMOTE_API_VARIANT}"

def update_cost_estimate(token_limit, api_option, api_variant):
    """
    Calcule le coût estimé pour le mode distant.
    
    Args:
        token_limit (int): Nombre de tokens.
        api_option (str): Fournisseur d'API ("Deepseek" ou "OpenAI").
        api_variant (str): Variante du modèle distant.
    
    Returns:
        str: Un message indiquant le coût estimé.
    """
    if api_option in COSTS and api_variant in COSTS[api_option]:
        cost = token_limit * COSTS[api_option][api_variant]
        return f"Coût estimé : {cost:.4f} $ pour {token_limit} tokens."
    else:
        return "Coût estimé indisponible."

# Pour s'assurer que les getters peuvent être appelés pour initialiser des chemins au démarrage si besoin
Config.get_db_path()
# Config.get_log_dir() # Déjà appelé dans get_log_file_path implicitement si on l'utilise globalement
# ou explicitement si on veut juste le dir. get_log_file_path() est plus complet pour le handler.
# Assurons nous que le log dir est créé au cas où get_log_file_path n'est pas appelé immédiatement.
if not os.path.exists(Config.LOG_DIR):
    Config.get_log_dir()