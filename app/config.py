# config.py
import os

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
