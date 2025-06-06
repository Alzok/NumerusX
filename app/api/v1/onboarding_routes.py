"""
Onboarding and dynamic configuration management routes for NumerusX API v1.
Handles initial setup wizard, configuration storage, and system status.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import logging
import os

from app.api.v1.auth_routes import require_auth, User, verify_token, TokenData
from app.database import EnhancedDatabase
from app.utils.encryption import EncryptionService
from app.utils.environment import should_show_onboarding, get_environment_config

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])
logger = logging.getLogger(__name__)

# Enums and Models
class OperatingMode(str, Enum):
    """Operating mode enumeration."""
    TEST = "test"
    PRODUCTION = "production"

class ThemePalette(str, Enum):
    """Available theme palettes from shadcn/ui."""
    SLATE = "slate"
    GRAY = "gray"
    ZINC = "zinc"
    NEUTRAL = "neutral"
    STONE = "stone"

class ConfigurationCategory(str, Enum):
    """Configuration categories."""
    API_KEYS = "api_keys"
    SECURITY = "security"
    TRADING = "trading"
    UI_PREFERENCES = "ui_preferences"
    SYSTEM = "system"

class OnboardingStep1Request(BaseModel):
    """Step 1: API Keys and Secrets configuration."""
    google_api_key: str = Field(..., description="Google AI API Key for Gemini")
    jupiter_api_key: Optional[str] = Field(None, description="Jupiter API Key (optional)")
    jupiter_pro_api_key: Optional[str] = Field(None, description="Jupiter Pro API Key (optional)")
    dexscreener_api_key: Optional[str] = Field(None, description="DexScreener API Key (optional)")
    solana_private_key_bs58: str = Field(..., description="Solana wallet private key in Base58 format")
    solana_rpc_url: str = Field(default="https://api.devnet.solana.com", description="Solana RPC URL")
    
    # Security keys
    jwt_secret_key: Optional[str] = Field(None, description="JWT secret key (auto-generated if not provided)")
    master_encryption_key: Optional[str] = Field(None, description="Master encryption key (auto-generated if not provided)")
    
    # Auth0 configuration
    auth0_domain: Optional[str] = Field(None, description="Auth0 domain")
    auth0_client_id: Optional[str] = Field(None, description="Auth0 client ID")
    auth0_audience: Optional[str] = Field(None, description="Auth0 API audience")

class OnboardingStep2Request(BaseModel):
    """Step 2: UI Preferences configuration."""
    theme_name: str = Field(default="default", description="Theme name (default, new-york)")
    theme_palette: ThemePalette = Field(default=ThemePalette.SLATE, description="Color palette")
    language: str = Field(default="en", description="Interface language")

class OnboardingStep3Request(BaseModel):
    """Step 3: Operating mode configuration."""
    operating_mode: OperatingMode = Field(..., description="Operating mode: test or production")
    initial_balance_usd: float = Field(default=1000.0, description="Initial portfolio balance in USD")
    max_trade_size_usd: float = Field(default=100.0, description="Maximum trade size in USD")
    risk_level: Literal["conservative", "moderate", "aggressive"] = Field(default="moderate", description="Risk tolerance level")

class OnboardingCompleteRequest(BaseModel):
    """Complete onboarding configuration."""
    step1: OnboardingStep1Request
    step2: OnboardingStep2Request
    step3: OnboardingStep3Request

class SystemStatusResponse(BaseModel):
    """System status response."""
    is_configured: bool
    operating_mode: OperatingMode
    theme_name: str
    theme_palette: ThemePalette
    last_configuration_update: Optional[datetime]
    configuration_version: int
    status_indicator: Literal["operational", "test", "error"]
    status_message: str

class ConfigurationValidationResponse(BaseModel):
    """Configuration validation response."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    missing_required: List[str] = []

# Utility Functions
def get_database() -> EnhancedDatabase:
    """Get database instance."""
    return EnhancedDatabase()

def generate_secure_key() -> str:
    """Generate a secure random key."""
    import secrets
    return secrets.token_hex(32)

def validate_api_keys(keys: Dict[str, str]) -> Dict[str, bool]:
    """Validate API keys format (not actual connectivity)."""
    validation_results = {}
    
    # Google API Key validation
    if google_key := keys.get("google_api_key"):
        validation_results["google_api_key"] = len(google_key) > 30 and google_key.startswith("AI")
    
    # Solana private key validation (Base58 format)
    if solana_key := keys.get("solana_private_key_bs58"):
        try:
            import base58
            decoded = base58.b58decode(solana_key)
            validation_results["solana_private_key_bs58"] = len(decoded) == 64
        except:
            validation_results["solana_private_key_bs58"] = False
    
    return validation_results

# Routes
@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(request: Request):
    """
    Get current system configuration status.
    Used by frontend to determine if onboarding is needed.
    """
    try:
        # Check if onboarding should be available
        if not should_show_onboarding(request):
            # In production, return configured status to hide onboarding
            return SystemStatusResponse(
                is_configured=True,
                operating_mode="production",
                theme_name="default",
                theme_palette="slate", 
                last_configuration_update=None,
                configuration_version=1,
                status_indicator="operational",
                status_message="System operational - production mode"
            )
        db = get_database()
        status_data = db.get_system_status()
        
        # Determine status indicator
        if not status_data.get('is_configured', False):
            status_indicator = "error"
            status_message = "System not configured - onboarding required"
        elif status_data.get('operating_mode') == 'test':
            status_indicator = "test"
            status_message = "Running in test mode"
        else:
            status_indicator = "operational"
            status_message = "System operational"
        
        return SystemStatusResponse(
            is_configured=status_data.get('is_configured', False),
            operating_mode=status_data.get('operating_mode', 'test'),
            theme_name=status_data.get('theme_name', 'default'),
            theme_palette=status_data.get('theme_palette', 'slate'),
            last_configuration_update=status_data.get('last_configuration_update'),
            configuration_version=status_data.get('configuration_version', 1),
            status_indicator=status_indicator,
            status_message=status_message
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )

@router.post("/validate-step1", response_model=ConfigurationValidationResponse)
async def validate_step1_configuration(
    request: OnboardingStep1Request, 
    http_request: Request,
    current_user: User = Depends(require_auth())
):
    """Validate Step 1 configuration before saving."""
    try:
        errors = []
        warnings = []
        missing_required = []
        
        # Validate required fields
        if not request.google_api_key:
            missing_required.append("google_api_key")
        if not request.solana_private_key_bs58:
            missing_required.append("solana_private_key_bs58")
        
        # Validate API key formats
        validation_results = validate_api_keys({
            "google_api_key": request.google_api_key,
            "solana_private_key_bs58": request.solana_private_key_bs58
        })
        
        for key, is_valid in validation_results.items():
            if not is_valid:
                errors.append(f"Invalid format for {key}")
        
        # Warnings for optional but recommended fields
        if not request.jupiter_api_key:
            warnings.append("Jupiter API key not provided - some trading features may be limited")
        if not request.auth0_domain:
            warnings.append("Auth0 not configured - authentication will be disabled")
        
        is_valid = len(errors) == 0 and len(missing_required) == 0
        
        return ConfigurationValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required
        )
        
    except Exception as e:
        logger.error(f"Error validating step 1 configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )

@router.post("/complete")
async def complete_onboarding(
    request: OnboardingCompleteRequest, 
    http_request: Request,
    current_user: User = Depends(require_auth())
):
    """
    Complete the onboarding process.
    Saves all configuration to database and marks system as configured.
    """
    try:
        db = get_database()
        
        # Generate missing security keys
        if not request.step1.jwt_secret_key:
            request.step1.jwt_secret_key = generate_secure_key()
        if not request.step1.master_encryption_key:
            request.step1.master_encryption_key = generate_secure_key()
        
        # Prepare configuration data
        config_data = {
            ConfigurationCategory.API_KEYS: {
                "google_api_key": request.step1.google_api_key,
                "jupiter_api_key": request.step1.jupiter_api_key,
                "jupiter_pro_api_key": request.step1.jupiter_pro_api_key,
                "dexscreener_api_key": request.step1.dexscreener_api_key,
                "solana_private_key_bs58": request.step1.solana_private_key_bs58,
                "solana_rpc_url": request.step1.solana_rpc_url,
            },
            ConfigurationCategory.SECURITY: {
                "jwt_secret_key": request.step1.jwt_secret_key,
                "master_encryption_key": request.step1.master_encryption_key,
                "auth0_domain": request.step1.auth0_domain,
                "auth0_client_id": request.step1.auth0_client_id,
                "auth0_audience": request.step1.auth0_audience,
            },
            ConfigurationCategory.UI_PREFERENCES: {
                "theme_name": request.step2.theme_name,
                "theme_palette": request.step2.theme_palette,
                "language": request.step2.language,
            },
            ConfigurationCategory.TRADING: {
                "operating_mode": request.step3.operating_mode,
                "initial_balance_usd": request.step3.initial_balance_usd,
                "max_trade_size_usd": request.step3.max_trade_size_usd,
                "risk_level": request.step3.risk_level,
            }
        }
        
        # Save configuration to database
        if not db.save_configuration(config_data):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save configuration to database"
            )
        
        # Update system status
        if not db.update_system_status(
            is_configured=True,
            operating_mode=request.step3.operating_mode,
            theme_name=request.step2.theme_name,
            theme_palette=request.step2.theme_palette
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update system status"
            )
        
        logger.info("Onboarding completed successfully")
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "operating_mode": request.step3.operating_mode,
            "redirect_url": "/dashboard"
        }
        
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )

@router.get("/configuration")
async def get_current_configuration(current_user: User = Depends(require_auth())):
    """Get current configuration (for settings page)."""
    try:
        db = get_database()
        config = db.load_configuration()
        
        # Mask sensitive values
        if ConfigurationCategory.API_KEYS in config:
            for key, value in config[ConfigurationCategory.API_KEYS].items():
                if value and len(str(value)) > 8:
                    config[ConfigurationCategory.API_KEYS][key] = f"{str(value)[:4]}...{str(value)[-4:]}"
        
        if ConfigurationCategory.SECURITY in config:
            for key, value in config[ConfigurationCategory.SECURITY].items():
                if value and "key" in key.lower():
                    config[ConfigurationCategory.SECURITY][key] = "***configured***"
        
        return {
            "success": True,
            "configuration": config,
            "system_status": db.get_system_status()
        }
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )

@router.post("/update-mode")
async def update_operating_mode(
    mode: OperatingMode,
    current_user: User = Depends(require_auth())
):
    """Update operating mode (test/production)."""
    try:
        db = get_database()
        
        if not db.update_system_status(operating_mode=mode):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update operating mode"
            )
        
        logger.info(f"Operating mode updated to: {mode}")
        
        return {
            "success": True,
            "message": f"Operating mode updated to {mode}",
            "operating_mode": mode
        }
        
    except Exception as e:
        logger.error(f"Error updating operating mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update operating mode: {str(e)}"
        )

@router.get("/theme-palettes")
async def get_available_theme_palettes():
    """Get available theme palettes from shadcn/ui."""
    palettes = [
        {
            "name": "slate",
            "displayName": "Slate",
            "description": "Cool gray with blue undertones",
            "primaryColor": "#334155",
            "preview": ["#f8fafc", "#e2e8f0", "#cbd5e1", "#94a3b8", "#64748b"]
        },
        {
            "name": "gray", 
            "displayName": "Gray",
            "description": "Neutral gray",
            "primaryColor": "#374151",
            "preview": ["#f9fafb", "#e5e7eb", "#d1d5db", "#9ca3af", "#6b7280"]
        },
        {
            "name": "zinc",
            "displayName": "Zinc", 
            "description": "Warm gray",
            "primaryColor": "#3f3f46",
            "preview": ["#fafafa", "#e4e4e7", "#d4d4d8", "#a1a1aa", "#71717a"]
        },
        {
            "name": "neutral",
            "displayName": "Neutral",
            "description": "Pure gray",
            "primaryColor": "#404040", 
            "preview": ["#fafafa", "#e5e5e5", "#d4d4d4", "#a3a3a3", "#737373"]
        },
        {
            "name": "stone",
            "displayName": "Stone",
            "description": "Warm beige gray",
            "primaryColor": "#44403c",
            "preview": ["#fafaf9", "#e7e5e4", "#d6d3d1", "#a8a29e", "#78716c"]
        }
    ]
    
    return {
        "success": True,
        "palettes": palettes,
        "default": "slate"
    }

@router.post("/debug/init-db")
async def init_database_tables(request: Request):
    """Debug endpoint to manually initialize database tables."""
    try:
        # Only allow in localhost environment
        if not should_show_onboarding(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debug endpoints not available in production environment"
            )
        db = get_database()
        
        # Force initialization of missing tables
        with db.conn:
            db.conn.executescript('''
                -- App configuration table
                CREATE TABLE IF NOT EXISTS app_configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    value_type TEXT NOT NULL CHECK (value_type IN ('string', 'integer', 'float', 'boolean', 'json', 'encrypted')),
                    description TEXT,
                    category TEXT NOT NULL,
                    is_required BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- User preferences table
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    value_type TEXT NOT NULL CHECK (value_type IN ('string', 'integer', 'float', 'boolean', 'json')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, preference_key)
                );

                -- System status table for application state
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY,
                    is_configured BOOLEAN DEFAULT FALSE,
                    operating_mode TEXT DEFAULT 'test' CHECK (operating_mode IN ('test', 'production')),
                    theme_name TEXT DEFAULT 'default',
                    theme_palette TEXT DEFAULT 'slate',
                    last_configuration_update DATETIME,
                    configuration_version INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
        
        # Initialize system status record
        db.initialize_system_status()
        
        logger.info("Database tables initialized successfully")
        return {"success": True, "message": "Database tables initialized"}
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return {"success": False, "error": str(e)}

@router.get("/debug/db-status")
async def check_database_status(request: Request):
    """Debug endpoint to check database status directly."""
    try:
        # Only allow in localhost environment
        if not should_show_onboarding(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debug endpoints not available in production environment"
            )
        db = get_database()
        
        # Check tables
        cursor = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Check system_status data
        try:
            cursor = db.conn.execute("SELECT * FROM system_status WHERE id = 1")
            system_status_data = cursor.fetchone()
        except Exception as e:
            system_status_data = f"Error: {e}"
        
        # Check app_configuration data
        try:
            cursor = db.conn.execute("SELECT COUNT(*) FROM app_configuration")
            config_count = cursor.fetchone()[0]
        except Exception as e:
            config_count = f"Error: {e}"
        
        return {
            "tables": tables,
            "system_status_record": system_status_data,
            "config_count": config_count,
            "db_path": db.db_path
        }
        
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return {"error": str(e)}

@router.post("/debug/force-init-status")
async def force_init_system_status(request: Request):
    """Debug endpoint to force initialize system status."""
    try:
        # Only allow in localhost environment
        if not should_show_onboarding(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debug endpoints not available in production environment"
            )
        db = get_database()
        
        # Force insert system status
        with db.conn:
            db.conn.execute("""
                INSERT OR REPLACE INTO system_status 
                (id, is_configured, operating_mode, theme_name, theme_palette, created_at, updated_at)
                VALUES (1, 0, 'test', 'default', 'slate', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
        
        logger.info("System status forced initialization")
        return {"success": True, "message": "System status initialized"}
        
    except Exception as e:
        logger.error(f"Error forcing system status init: {e}")
        return {"success": False, "error": str(e)} 