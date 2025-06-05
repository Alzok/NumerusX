"""
Auth0 RS256 JWT middleware for FastAPI.
Compatible with Auth0 tokens using RS256 algorithm.
"""

import os
import jwt
import requests
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
from datetime import datetime
import json

security = HTTPBearer()

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-domain.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "numerusx-api")
AUTH0_ALGORITHMS = ["RS256"]

class Auth0Token:
    """Auth0 token data container."""
    def __init__(self, token_data: Dict[str, Any]):
        self.sub = token_data.get("sub")
        self.email = token_data.get("email")
        self.nickname = token_data.get("nickname")
        self.name = token_data.get("name")
        self.picture = token_data.get("picture")
        self.permissions = token_data.get("permissions", [])
        self.scopes = token_data.get("scope", "").split(" ")
        self.exp = token_data.get("exp")
        self.iat = token_data.get("iat")
        self.aud = token_data.get("aud")
        self.iss = token_data.get("iss")
        self.raw_token = token_data

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions

    def has_scope(self, scope: str) -> bool:
        """Check if token has specific scope."""
        return scope in self.scopes

    @property
    def user_id(self) -> str:
        """Get user ID from sub claim."""
        return self.sub

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.exp:
            return True
        return datetime.utcnow().timestamp() > self.exp


@lru_cache(maxsize=1)
def get_auth0_public_key():
    """
    Get Auth0 public key for JWT verification.
    Cached for performance.
    """
    try:
        response = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        response.raise_for_status()
        jwks = response.json()
        
        # Return the first key (Auth0 typically has one)
        if jwks.get("keys"):
            return jwks["keys"][0]
        else:
            raise Exception("No keys found in JWKS")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Auth0 public key: {str(e)}"
        )


def verify_auth0_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Auth0Token:
    """
    Verify Auth0 JWT token with RS256 algorithm.
    """
    token = credentials.credentials
    
    try:
        # Get the unverified header to extract kid
        unverified_header = jwt.get_unverified_header(token)
        
        # Get Auth0 public key
        jwks_key = get_auth0_public_key()
        
        # Construct the public key
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwks_key)
        
        # Verify and decode the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        # Create Auth0Token object
        auth_token = Auth0Token(payload)
        
        # Check if token is expired
        if auth_token.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return auth_token
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_admin_token(auth_token: Auth0Token = Depends(verify_auth0_token)) -> Auth0Token:
    """
    Verify token has admin permissions.
    """
    required_permissions = ["read:admin", "write:admin"]
    
    if not any(auth_token.has_permission(perm) for perm in required_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required."
        )
    
    return auth_token


def verify_bot_control_token(auth_token: Auth0Token = Depends(verify_auth0_token)) -> Auth0Token:
    """
    Verify token has bot control permissions.
    """
    required_permissions = ["control:bot", "read:bot"]
    
    if not any(auth_token.has_permission(perm) for perm in required_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Bot control access required."
        )
    
    return auth_token


def verify_read_only_token(auth_token: Auth0Token = Depends(verify_auth0_token)) -> Auth0Token:
    """
    Verify token has at least read permissions.
    """
    # Any authenticated user can read
    return auth_token


# Fallback to simple JWT for development
def verify_simple_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fallback simple JWT verification for development.
    Uses HS256 algorithm with shared secret.
    """
    from app.api.v1.auth_routes import verify_token
    return verify_token(credentials)


def get_current_user(request: Request = None):
    """
    Get current user based on environment configuration.
    Uses Auth0 in production, simple JWT in development.
    """
    use_auth0 = os.getenv("USE_AUTH0", "false").lower() == "true"
    
    if use_auth0:
        return Depends(verify_auth0_token)
    else:
        return Depends(verify_simple_jwt)


# Export the main authentication dependency
authenticate_user = get_current_user() 