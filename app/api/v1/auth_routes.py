"""
Authentication routes for API v1.
Handles user login, logout, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Default credentials (to be replaced with proper user management)
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "admin")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "password")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    """User model for authenticated users."""
    username: str
    role: str = "admin"


def require_auth():
    """Dependency factory for requiring authentication."""
    def get_current_user(token_data: TokenData = Depends(verify_token)) -> User:
        """Get current authenticated user."""
        return User(username=token_data.username, role="admin")
    return get_current_user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify and decode JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user credentials."""
    # Simple authentication - replace with proper user management
    return username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Login endpoint to get access token.
    """
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"sub": credentials.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600  # seconds
    }


@router.post("/logout")
async def logout(token_data: TokenData = Depends(verify_token)):
    """
    Logout endpoint (token invalidation would be handled by client).
    """
    return {"message": "Successfully logged out"}


@router.get("/verify")
async def verify(token_data: TokenData = Depends(verify_token)):
    """
    Verify token validity.
    """
    return {"valid": True, "username": token_data.username}


@router.get("/profile")
async def get_profile(token_data: TokenData = Depends(verify_token)):
    """
    Get user profile information.
    """
    return {
        "username": token_data.username,
        "role": "admin",  # Default role
        "created_at": datetime.utcnow().isoformat()
    }
