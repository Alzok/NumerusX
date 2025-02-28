# config.py
import os
from dotenv import load_dotenv

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
    APP_NAME = "NumerusX"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configuration de sécurité
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key_change_in_production")
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))  # En secondes (1 heure par défaut)
    
    # Configuration de base de données
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///numerusx.db")
    
    # Configuration Solana
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    SOLANA_NETWORK = os.getenv("SOLANA_NETWORK", "mainnet-beta")
    
    # Configuration Jupiter
    JUPITER_SWAP_URL = os.getenv("JUPITER_SWAP_URL", "https://quote-api.jup.ag/v4/quote")
    JUPITER_API_KEY = os.getenv("JUPITER_API_KEY", None)
    
    # Paramètres trading
    SLIPPAGE = float(os.getenv("SLIPPAGE", "0.5"))  # 0.5%
    MIN_LIQUIDITY = float(os.getenv("MIN_LIQUIDITY", "10000"))  # Volume minimum en $
    
    # Chemins
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    
    # Configuration base de données
    DB_PATH = "data/numerusx.db"
    
    # Configuration API
    JUPITER_API_KEY = ""  # À définir via variable d'environnement en production
    JUPITER_SWAP_URL = "https://quote-api.jup.ag/v6/quote"
    JUPITER_PRICE_URL = "https://price.jup.ag/v4/price"
    
    # Paramètres de trading
    SLIPPAGE = 0.01  # 1% de slippage par défaut
    BASE_ASSET = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC sur Solana
    MAX_POSITIONS = 5
    MAX_ORDER_SIZE = 1000.0  # Taille maximale des ordres en USD
    UPDATE_INTERVAL = 60  # Intervalle de mise à jour en secondes
    INITIAL_BALANCE = 1000.0  # Solde initial du portefeuille en USD
    
    # Configuration UI
    UI_UPDATE_INTERVAL = 2  # Intervalle de mise à jour de l'UI en secondes
    
    # Mode développement (doit être False en production)
    DEV_MODE = False
    
    @classmethod
    def get_db_path(cls):
        """Renvoie le chemin complet de la base de données, en créant le répertoire si nécessaire"""
        import os
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        return cls.DB_PATH

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
