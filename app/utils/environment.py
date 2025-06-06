"""
Environment detection utilities for NumerusX
"""

import os
from typing import Dict, Any
from fastapi import Request

def is_localhost_environment(request: Request = None, host: str = None) -> bool:
    """
    Determine if the application is running in localhost environment.
    
    Args:
        request: FastAPI request object (optional)
        host: Host string to check (optional)
    
    Returns:
        bool: True if running on localhost, False if in production
    """
    
    # Method 1: Check via request host
    if request:
        host = request.headers.get("host", "")
    
    if host:
        localhost_patterns = [
            "localhost",
            "127.0.0.1", 
            "0.0.0.0",
            "::1"
        ]
        return any(pattern in host.lower() for pattern in localhost_patterns)
    
    # Method 2: Check environment variables
    env_indicators = [
        os.getenv("ENVIRONMENT", "").lower() == "development",
        os.getenv("DEBUG", "").lower() == "true",
        os.getenv("NODE_ENV", "").lower() == "development",
        "localhost" in os.getenv("API_URL", "").lower(),
        "localhost" in os.getenv("FRONTEND_URL", "").lower()
    ]
    
    if any(env_indicators):
        return True
    
    # Method 3: Check deployment context 
    deployment_indicators = [
        os.getenv("DOCKER_ENV") == "development",
        not os.getenv("PRODUCTION"),  # No PRODUCTION flag set
        os.path.exists("/app/development.flag")  # Development flag file
    ]
    
    return any(deployment_indicators)

def get_environment_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration.
    
    Returns:
        Dict with environment settings
    """
    is_local = is_localhost_environment()
    
    return {
        "is_localhost": is_local,
        "is_production": not is_local,
        "enable_onboarding": True,      # Enable onboarding everywhere (with auth)
        "enable_auth0": True,           # Always enable Auth0 authentication
        "enable_debug_endpoints": is_local,  # Debug endpoints only in localhost
        "cors_origins": ["http://localhost:3000", "http://localhost:5173"] if is_local else [],
        "log_level": "DEBUG" if is_local else "INFO"
    }

def should_show_onboarding(request: Request = None) -> bool:
    """
    Determine if onboarding interface should be shown.
    Available everywhere but requires authentication.
    """
    return True

def should_enable_auth0(request: Request = None) -> bool:
    """
    Determine if Auth0 authentication should be enabled.
    Always enabled for security.
    """
    return True 