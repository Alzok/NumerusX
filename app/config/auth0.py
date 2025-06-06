"""
Auth0 configuration for NumerusX
"""

import os
from typing import Dict, Any

# Auth0 Configuration
AUTH0_CONFIG = {
    "domain": "numerus.eu.auth0.com",
    "api_audience": "https://numerus.eu.auth0.com/api/v2/",
    "algorithms": ["RS256"],
    "grant_id": "cgr_iEa1mQA42Yuu0o4Y",
    
    # Localhost configuration  
    "client_id_dev": os.getenv("AUTH0_CLIENT_ID_DEV", ""),
    "client_secret_dev": os.getenv("AUTH0_CLIENT_SECRET_DEV", ""),
    
    # Production configuration
    "client_id_prod": os.getenv("AUTH0_CLIENT_ID_PROD", ""),
    "client_secret_prod": os.getenv("AUTH0_CLIENT_SECRET_PROD", ""),
    
    # Common settings
    "scope": "openid profile email",
    "response_type": "code",
    
    # URLs
    "callback_url_dev": "http://localhost:5173/callback",
    "logout_url_dev": "http://localhost:5173",
    "callback_url_prod": os.getenv("AUTH0_CALLBACK_URL_PROD", ""),
    "logout_url_prod": os.getenv("AUTH0_LOGOUT_URL_PROD", "")
}

def get_auth0_config(is_production: bool = False) -> Dict[str, Any]:
    """
    Get Auth0 configuration based on environment.
    
    Args:
        is_production: Whether running in production environment
        
    Returns:
        Dict with Auth0 configuration
    """
    base_config = {
        "domain": AUTH0_CONFIG["domain"],
        "api_audience": AUTH0_CONFIG["api_audience"],
        "algorithms": AUTH0_CONFIG["algorithms"],
        "scope": AUTH0_CONFIG["scope"],
        "response_type": AUTH0_CONFIG["response_type"],
    }
    
    if is_production:
        base_config.update({
            "client_id": AUTH0_CONFIG["client_id_prod"],
            "client_secret": AUTH0_CONFIG["client_secret_prod"],
            "callback_url": AUTH0_CONFIG["callback_url_prod"],
            "logout_url": AUTH0_CONFIG["logout_url_prod"],
        })
    else:
        base_config.update({
            "client_id": AUTH0_CONFIG["client_id_dev"],
            "client_secret": AUTH0_CONFIG["client_secret_dev"],
            "callback_url": AUTH0_CONFIG["callback_url_dev"],
            "logout_url": AUTH0_CONFIG["logout_url_dev"],
        })
    
    return base_config

# JWT Configuration
JWT_CONFIG = {
    "algorithm": "RS256",
    "audience": AUTH0_CONFIG["api_audience"],
    "issuer": f"https://{AUTH0_CONFIG['domain']}/",
} 