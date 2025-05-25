# config.py
import os
from dotenv import load_dotenv
import json
from cryptography.fernet import Fernet, InvalidToken
import base64
import logging # Added for EncryptionUtil logging
from app.analytics_engine import AdvancedTradingStrategy # Import for default strategy name

# Charger les variables d'environnement depuis .env
load_dotenv()

# Setup logging for EncryptionUtil
encryption_logger = logging.getLogger("EncryptionUtil")
# Ensure a handler is configured if not already by global logging config
if not encryption_logger.hasHandlers():
    # Basic configuration if no handlers are set up for this logger
    # This might be redundant if global logging is already configured comprehensively
    # but ensures EncryptionUtil messages are seen.
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    encryption_logger.addHandler(handler)
    # Set a default level if needed, e.g., logging.INFO or logging.WARNING
    # encryption_logger.setLevel(logging.INFO)

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

# Clé principale pour le chiffrement/déchiffrement des secrets. DOIT être définie dans .env
# Exemple: MASTER_ENCRYPTION_KEY=... une clé générée par Fernet.generate_key().decode() ...
# Pour générer une clé:
# from cryptography.fernet import Fernet
# key = Fernet.generate_key()
# print(key.decode()) # Store this in your .env as MASTER_ENCRYPTION_KEY
MASTER_ENCRYPTION_KEY_ENV = os.getenv("MASTER_ENCRYPTION_KEY")

class EncryptionUtil:
    """Utility class for encrypting and decrypting secrets."""
    _fernet_instance = None

    @classmethod
    def _get_fernet(cls):
        if not MASTER_ENCRYPTION_KEY_ENV:
            encryption_logger.critical("MASTER_ENCRYPTION_KEY is not set in the environment. Encryption/decryption will fail.")
            # Raising an error here might be too disruptive if some parts of the app don't need encryption.
            # Alternatively, allow operations to fail later when encrypt/decrypt is called.
            return None 
        
        if cls._fernet_instance is None:
            try:
                # Ensure the key is bytes
                key_bytes = MASTER_ENCRYPTION_KEY_ENV.encode()
                # Fernet keys must be 32 url-safe base64-encoded bytes.
                # If the key from env is already base64 encoded (e.g. from Fernet.generate_key()),
                # it might not need further base64 encoding here, but Fernet constructor expects bytes.
                # Let's assume MASTER_ENCRYPTION_KEY_ENV is the direct output of Fernet.generate_key().decode()
                # which needs to be re-encoded to bytes.
                cls._fernet_instance = Fernet(key_bytes)
            except Exception as e:
                encryption_logger.error(f"Failed to initialize Fernet with MASTER_ENCRYPTION_KEY: {e}. Ensure it's a valid Fernet key.", exc_info=True)
                return None
        return cls._fernet_instance

    @classmethod
    def encrypt(cls, plaintext: str) -> Optional[str]:
        """Encrypts a plaintext string. Returns base64 encoded encrypted string."""
        fernet = cls._get_fernet()
        if not fernet or not plaintext:
            return None
        try:
            encrypted_bytes = fernet.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode() # Return as string
        except Exception as e:
            encryption_logger.error(f"Encryption failed: {e}", exc_info=True)
            return None

    @classmethod
    def decrypt(cls, encrypted_text_b64: str) -> Optional[str]:
        """Decrypts a base64 encoded encrypted string."""
        fernet = cls._get_fernet()
        if not fernet or not encrypted_text_b64:
            return None
        try:
            # Ensure the input is bytes for b64decode, then Fernet decrypt
            encrypted_bytes_from_b64 = base64.urlsafe_b64decode(encrypted_text_b64.encode())
            decrypted_bytes = fernet.decrypt(encrypted_bytes_from_b64)
            return decrypted_bytes.decode()
        except InvalidToken:
            encryption_logger.error("Decryption failed: Invalid token (likely wrong key or corrupted data). Ensure MASTER_ENCRYPTION_KEY is correct.", exc_info=True)
            return None
        except Exception as e:
            encryption_logger.error(f"Decryption failed: {e}", exc_info=True)
            return None

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
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") # DEPRECATED in favor of MASTER_ENCRYPTION_KEY
    ENCRYPTED_SOLANA_PK_FILE = os.getenv("ENCRYPTED_SOLANA_PK_FILE") # Path to file containing encrypted PK
    
    # Variables for encrypted secrets (preferred way)
    ENCRYPTED_JUPITER_API_KEY = os.getenv("ENCRYPTED_JUPITER_API_KEY")
    ENCRYPTED_DEXSCREENER_API_KEY = os.getenv("ENCRYPTED_DEXSCREENER_API_KEY")
    ENCRYPTED_SOLANA_PRIVATE_KEY_BS58 = os.getenv("ENCRYPTED_SOLANA_PRIVATE_KEY_BS58") # Encrypted Base58 PK string

    # Fallback to plaintext environment variables if encrypted versions are not available or decryption fails
    _decrypted_jupiter_api_key = EncryptionUtil.decrypt(ENCRYPTED_JUPITER_API_KEY) if ENCRYPTED_JUPITER_API_KEY else None
    JUPITER_API_KEY = _decrypted_jupiter_api_key if _decrypted_jupiter_api_key else os.getenv("JUPITER_API_KEY")
    if ENCRYPTED_JUPITER_API_KEY and not _decrypted_jupiter_api_key:
        encryption_logger.warning("ENCRYPTED_JUPITER_API_KEY is set but decryption failed. Falling back to JUPITER_API_KEY if available.")

    _decrypted_dexscreener_api_key = EncryptionUtil.decrypt(ENCRYPTED_DEXSCREENER_API_KEY) if ENCRYPTED_DEXSCREENER_API_KEY else None
    DEXSCREENER_API_KEY = _decrypted_dexscreener_api_key if _decrypted_dexscreener_api_key else os.getenv("DEXSCREENER_API_KEY")
    if ENCRYPTED_DEXSCREENER_API_KEY and not _decrypted_dexscreener_api_key:
        encryption_logger.warning("ENCRYPTED_DEXSCREENER_API_KEY is set but decryption failed. Falling back to DEXSCREENER_API_KEY if available.")
    
    _decrypted_solana_pk_bs58 = EncryptionUtil.decrypt(ENCRYPTED_SOLANA_PRIVATE_KEY_BS58) if ENCRYPTED_SOLANA_PRIVATE_KEY_BS58 else None
    # This SOLANA_PRIVATE_KEY_BS58 will be used by TradingEngine's env var loading logic.
    # If ENCRYPTED_SOLANA_PRIVATE_KEY_BS58 is set and decryption fails, SOLANA_PRIVATE_KEY_BS58 will be None (unless plaintext os.getenv works)
    # This means TradingEngine's logic will naturally try other methods if this is None.
    SOLANA_PRIVATE_KEY_BS58 = _decrypted_solana_pk_bs58 if _decrypted_solana_pk_bs58 else os.getenv("SOLANA_PRIVATE_KEY_BS58")
    if ENCRYPTED_SOLANA_PRIVATE_KEY_BS58 and not _decrypted_solana_pk_bs58:
        encryption_logger.warning("ENCRYPTED_SOLANA_PRIVATE_KEY_BS58 is set but decryption failed. Wallet init might fail or use plaintext key if available.")

    # Configuration du SecurityChecker (Seuils et Limites)
    SECURITY_MAX_HOLDERS_TO_FETCH = int(os.getenv("SECURITY_MAX_HOLDERS_TO_FETCH", "200"))
    HOLDER_CONCENTRATION_THRESHOLD_HIGH = float(os.getenv("HOLDER_CONCENTRATION_THRESHOLD_HIGH", "0.5")) # 50%
    HOLDER_CONCENTRATION_THRESHOLD_MEDIUM = float(os.getenv("HOLDER_CONCENTRATION_THRESHOLD_MEDIUM", "0.3")) # 30%
    MIN_HOLDERS_COUNT_THRESHOLD = int(os.getenv("MIN_HOLDERS_COUNT_THRESHOLD", "10"))
    
    MIN_LIQUIDITY_THRESHOLD_ERROR = float(os.getenv("MIN_LIQUIDITY_THRESHOLD_ERROR", "1000.0")) # USD
    MIN_LIQUIDITY_THRESHOLD_WARNING = float(os.getenv("MIN_LIQUIDITY_THRESHOLD_WARNING", "5000.0")) # USD
    
    RUGPULL_PRICE_TIMEFRAME = os.getenv("RUGPULL_PRICE_TIMEFRAME", "15m")
    RUGPULL_PRICE_LIMIT = int(os.getenv("RUGPULL_PRICE_LIMIT", "96")) # Pour 24h avec timeframe 15m
    RUGPULL_TRANSACTION_LIMIT = int(os.getenv("RUGPULL_TRANSACTION_LIMIT", "200"))
    RUGPULL_LIQUIDITY_TIMEFRAME = os.getenv("RUGPULL_LIQUIDITY_TIMEFRAME", "15m")
    RUGPULL_LIQUIDITY_LIMIT = int(os.getenv("RUGPULL_LIQUIDITY_LIMIT", "96")) # Pour 24h avec timeframe 15m
    RUGPULL_PRICE_DROP_THRESHOLD = float(os.getenv("RUGPULL_PRICE_DROP_THRESHOLD", "-0.50")) # -50%
    RUGPULL_LIQUIDITY_DROP_THRESHOLD = float(os.getenv("RUGPULL_LIQUIDITY_DROP_THRESHOLD", "-0.30")) # -30%
    
    LIQUIDITY_ASYMMETRY_THRESHOLD_SEVERE = float(os.getenv("LIQUIDITY_ASYMMETRY_THRESHOLD_SEVERE", "0.8")) # 80%
    LIQUIDITY_ASYMMETRY_THRESHOLD_MODERATE = float(os.getenv("LIQUIDITY_ASYMMETRY_THRESHOLD_MODERATE", "0.5")) # 50%
    
    PRICE_IMPACT_USD_AMOUNT_1K = float(os.getenv("PRICE_IMPACT_USD_AMOUNT_1K", "1000.0"))
    PRICE_IMPACT_THRESHOLD_HIGH_1K = float(os.getenv("PRICE_IMPACT_THRESHOLD_HIGH_1K", "0.05")) # 5%
    PRICE_IMPACT_USD_AMOUNT_10K = float(os.getenv("PRICE_IMPACT_USD_AMOUNT_10K", "10000.0"))
    PRICE_IMPACT_THRESHOLD_HIGH_10K = float(os.getenv("PRICE_IMPACT_THRESHOLD_HIGH_10K", "0.10")) # 10%

    # Thresholds for advanced rugpull detection (SecurityChecker)
    HIGH_VELOCITY_TX_COUNT_THRESHOLD = int(os.getenv("HIGH_VELOCITY_TX_COUNT_THRESHOLD", "100")) # Num tx in last hour
    NUM_TOP_HOLDERS_TO_ANALYZE = int(os.getenv("NUM_TOP_HOLDERS_TO_ANALYZE", "5"))
    MIN_PCT_SALE_BY_TOP_HOLDER = float(os.getenv("MIN_PCT_SALE_BY_TOP_HOLDER", "0.50")) # 50% of their own holding sold
    
    # Configuration de base de données
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join('data', 'numerusx.db')}")
    DB_PATH = os.getenv("DB_PATH", os.path.join("data", "numerusx.db"))
    
    # Configuration Solana
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    SOLANA_NETWORK = os.getenv("SOLANA_NETWORK", "mainnet-beta")
    WALLET_PATH = os.getenv("WALLET_PATH", os.path.join("keys", "solana_wallet.json"))
    BACKUP_WALLET_PATH = os.getenv("BACKUP_WALLET_PATH") # Chemin vers un portefeuille de secours, optionnel
    DEFAULT_FEE_PER_SIGNATURE_LAMPORTS = int(os.getenv("DEFAULT_FEE_PER_SIGNATURE_LAMPORTS", "5000"))
    SOL_MINT_ADDRESS = "So11111111111111111111111111111111111111112" # Wrapped SOL
    USDC_MINT_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # USDC
    USDT_MINT_ADDRESS = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB" # USDT
    
    # Configuration Jupiter (Legacy - for reference or direct calls if SDK doesn't cover all needs)
    JUPITER_API_BASE_URL_LEGACY = os.getenv("JUPITER_API_BASE_URL", "https://quote-api.jup.ag") # DEPRECATED - See JUPITER_LITE_API_HOSTNAME
    JUPITER_QUOTE_URL_SUFFIX_LEGACY = "/v6/quote" # DEPRECATED
    JUPITER_PRICE_URL_SUFFIX_LEGACY = "/v4/price" # DEPRECATED
    
    # Jupiter API v6 Configuration (for use with jupiter-python-sdk)
    JUPITER_LITE_API_HOSTNAME = os.getenv("JUPITER_LITE_API_HOSTNAME", "https://lite-api.jup.ag")
    JUPITER_PRO_API_HOSTNAME = os.getenv("JUPITER_PRO_API_HOSTNAME", "https://api.jup.ag") # For paid plan with API key
    # Select hostname based on API key presence (or a specific config toggle)
    # For now, assuming JUPITER_LITE_API_HOSTNAME will be the default for JupiterApiClient
    
    JUPITER_SWAP_API_PATH = os.getenv("JUPITER_SWAP_API_PATH", "/swap/v1")
    JUPITER_PRICE_API_PATH = os.getenv("JUPITER_PRICE_API_PATH", "/price/v2")
    JUPITER_TOKEN_API_PATH = os.getenv("JUPITER_TOKEN_API_PATH", "/tokens/v1")
    JUPITER_TRIGGER_API_PATH = os.getenv("JUPITER_TRIGGER_API_PATH", "/trigger/v1") # For limit orders
    JUPITER_RECURRING_API_PATH = os.getenv("JUPITER_RECURRING_API_PATH", "/recurring/v1") # For DCA

    # Jupiter Transaction Parameters (for jupiter-python-sdk)
    JUPITER_DEFAULT_SLIPPAGE_BPS = int(os.getenv("JUPITER_DEFAULT_SLIPPAGE_BPS", "50")) # 0.5%
    JUPITER_DYNAMIC_COMPUTE_UNIT_LIMIT = os.getenv("JUPITER_DYNAMIC_COMPUTE_UNIT_LIMIT", "True").lower() == "true"
    JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS = os.getenv("JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS") # e.g., "100000". If None, SDK might use its default or require JUPITER_PRIORITY_FEE_LEVEL
    JUPITER_PRIORITY_FEE_LEVEL = os.getenv("JUPITER_PRIORITY_FEE_LEVEL", "Default") # Options: "Default", "Medium", "High", "VeryHigh", etc. (SDK specific)
    JUPITER_WRAP_AND_UNWRAP_SOL = os.getenv("JUPITER_WRAP_AND_UNWRAP_SOL", "True").lower() == "true"
    JUPITER_ONLY_DIRECT_ROUTES = os.getenv("JUPITER_ONLY_DIRECT_ROUTES", "False").lower() == "true"
    JUPITER_RESTRICT_INTERMEDIATE_TOKENS = os.getenv("JUPITER_RESTRICT_INTERMEDIATE_TOKENS", "True").lower() == "true"
    JUPITER_SWAP_MODE_EXACT_IN = "ExactIn" # Default for most swaps
    JUPITER_SWAP_MODE_EXACT_OUT = "ExactOut"
    JUPITER_SWAP_MODE = os.getenv("JUPITER_SWAP_MODE", JUPITER_SWAP_MODE_EXACT_IN) # Global default, can be overridden per call

    JUPITER_MAX_RETRIES = int(os.getenv("JUPITER_MAX_RETRIES", "3")) # For API call retries in JupiterApiClient

    # DexScreener
    DEXSCREENER_API_URL = os.getenv("DEXSCREENER_API_URL", "https://api.dexscreener.com/latest/dex")
    # DEXSCREENER_API_KEY is handled by EncryptionUtil logic if ENCRYPTED_DEXSCREENER_API_KEY is set

    # Paramètres trading (General - some may be superseded by Jupiter specific ones for Jupiter trades)
    BASE_ASSET = os.getenv("BASE_ASSET", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")  # USDC sur Solana
    SLIPPAGE_BPS = int(os.getenv("SLIPPAGE_BPS", "50")) # General slippage, JUPITER_DEFAULT_SLIPPAGE_BPS for Jupiter
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
    TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS = int(os.getenv("TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS", "120")) # Augmenté à 120s
    TRANSACTION_CONFIRMATION_POLL_INTERVAL_SECONDS = int(os.getenv("TRANSACTION_CONFIRMATION_POLL_INTERVAL_SECONDS", "5"))

    # Paramètres de retry pour l'envoi de transaction
    SEND_TRANSACTION_RETRY_ATTEMPTS = int(os.getenv("SEND_TRANSACTION_RETRY_ATTEMPTS", "3"))
    SEND_TRANSACTION_RETRY_MULTIPLIER = float(os.getenv("SEND_TRANSACTION_RETRY_MULTIPLIER", "1")) # Pour wait_exponential
    SEND_TRANSACTION_RETRY_MIN_WAIT = float(os.getenv("SEND_TRANSACTION_RETRY_MIN_WAIT", "1"))   # Secondes
    SEND_TRANSACTION_RETRY_MAX_WAIT = float(os.getenv("SEND_TRANSACTION_RETRY_MAX_WAIT", "5"))   # Secondes

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

    # Configuration du Moteur de Prédiction
    PREDICTION_MODEL_DIR = os.getenv("PREDICTION_MODEL_DIR", "models")
    PREDICTION_DATA_DIR = os.getenv("PREDICTION_DATA_DIR", "data/prediction_data")

    # Configuration Google Gemini API
    ENCRYPTED_GOOGLE_API_KEY = os.getenv("ENCRYPTED_GOOGLE_API_KEY")
    _decrypted_google_api_key = EncryptionUtil.decrypt(ENCRYPTED_GOOGLE_API_KEY) if ENCRYPTED_GOOGLE_API_KEY else None
    GOOGLE_API_KEY = _decrypted_google_api_key if _decrypted_google_api_key else os.getenv("GOOGLE_API_KEY")
    if ENCRYPTED_GOOGLE_API_KEY and not _decrypted_google_api_key:
        encryption_logger.warning("ENCRYPTED_GOOGLE_API_KEY is set but decryption failed. Falling back to GOOGLE_API_KEY if available.")
    
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")
    GEMINI_API_TIMEOUT_SECONDS = int(os.getenv("GEMINI_API_TIMEOUT_SECONDS", "30")) # Increased default
    GEMINI_MAX_TOKENS_INPUT = int(os.getenv("GEMINI_MAX_TOKENS_INPUT", "4096")) # Consider Gemini 2.5 Flash context window

    # Configuration des Stratégies
    DEFAULT_STRATEGY_NAME = os.getenv("DEFAULT_STRATEGY_NAME", AdvancedTradingStrategy().get_name()) # Default to AdvancedTradingStrategy

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
        # return f"{cls.JUPITER_API_BASE_URL.rstrip('/')}{cls.JUPITER_QUOTE_URL_SUFFIX}" # Old V4/V6 quote
        # This method is likely deprecated if using JupiterApiClient with the SDK, 
        # as the client will construct its own URLs from base hostnames and paths.
        # Retaining for now, but should be reviewed.
        return f"{cls.JUPITER_LITE_API_HOSTNAME.rstrip('/')}{cls.JUPITER_SWAP_API_PATH.rstrip('/')}/quote"

    @classmethod
    def get_jupiter_price_url(cls):
        # return f"{cls.JUPITER_API_BASE_URL.rstrip('/')}{cls.JUPITER_PRICE_URL_SUFFIX}" # Old V4 price
        # Similar to get_jupiter_quote_url, likely deprecated for SDK usage.
        return f"{cls.JUPITER_LITE_API_HOSTNAME.rstrip('/')}{cls.JUPITER_PRICE_API_PATH.rstrip('/')}"

    @classmethod
    def get_jupiter_swap_url(cls): # New method for the swap endpoint
        # Similar to get_jupiter_quote_url, likely deprecated for SDK usage.
        return f"{cls.JUPITER_LITE_API_HOSTNAME.rstrip('/')}{cls.JUPITER_SWAP_API_PATH.rstrip('/')}/swap"
    
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