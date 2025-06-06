"""
Configuration management routes for NumerusX API v1.
Handles bot configuration, trading pairs, and risk parameters.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import os
import logging

from app.api.v1.auth_routes import require_auth, User, verify_token, TokenData
from app.config import get_config

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])
logger = logging.getLogger(__name__)

# Enums
class RiskLevel(str, Enum):
    """Risk level enumeration."""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    CUSTOM = "CUSTOM"

# Pydantic models
class TradingPairConfig(BaseModel):
    """Trading pair configuration."""
    base_token: str = Field(..., description="Base token address")
    quote_token: str = Field(default="So11111111111111111111111111111111111111112", description="Quote token (default: SOL)")
    enabled: bool = True
    max_position_size_usd: float = Field(default=100.0, ge=0)
    min_position_size_usd: float = Field(default=10.0, ge=0)
    priority: int = Field(default=1, ge=1, le=10)
    
    @validator('max_position_size_usd')
    def validate_position_sizes(cls, max_size, values):
        min_size = values.get('min_position_size_usd', 0)
        if max_size < min_size:
            raise ValueError("Max position size must be >= min position size")
        return max_size

class RiskParameters(BaseModel):
    """Risk management parameters."""
    risk_level: RiskLevel = RiskLevel.MODERATE
    max_daily_loss_usd: float = Field(default=100.0, ge=0)
    max_position_size_percent: float = Field(default=10.0, ge=0, le=100)
    stop_loss_percent: float = Field(default=5.0, ge=0, le=100)
    take_profit_percent: float = Field(default=10.0, ge=0, le=100)
    max_slippage_percent: float = Field(default=1.0, ge=0, le=10)
    enable_trailing_stop: bool = False
    trailing_stop_percent: Optional[float] = Field(default=3.0, ge=0, le=100)

class AIParameters(BaseModel):
    """AI Agent configuration parameters."""
    model_name: str = Field(default="gemini-1.5-flash", description="Gemini model name")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1000, ge=100, le=8192)
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    analysis_depth: str = Field(default="STANDARD", pattern="^(QUICK|STANDARD|DEEP)$")
    enable_reasoning_trace: bool = True

class TradingParameters(BaseModel):
    """General trading parameters."""
    enable_auto_trading: bool = True
    trading_hours_utc: Optional[Dict[str, str]] = Field(
        default={"start": "00:00", "end": "23:59"},
        description="Trading hours in UTC"
    )
    cycle_interval_minutes: int = Field(default=15, ge=1, le=1440)
    min_profit_threshold_usd: float = Field(default=1.0, ge=0)
    gas_limit_sol: float = Field(default=0.01, ge=0.001)
    priority_fee_lamports: int = Field(default=10000, ge=0)

class BotConfiguration(BaseModel):
    """Complete bot configuration."""
    trading_pairs: List[TradingPairConfig]
    risk_parameters: RiskParameters
    ai_parameters: AIParameters
    trading_parameters: TradingParameters
    updated_at: Optional[datetime] = None
    version: str = "1.0.0"

class ConfigUpdateRequest(BaseModel):
    """Configuration update request."""
    section: str = Field(..., pattern="^(trading_pairs|risk|ai|trading|full)$")
    data: Dict[str, Any]

# Global config instance (in production, use database)
current_config: Optional[BotConfiguration] = None

def get_current_config() -> BotConfiguration:
    """Get current configuration."""
    global current_config
    if current_config is None:
        # Load default configuration
        current_config = BotConfiguration(
            trading_pairs=[
                TradingPairConfig(
                    base_token="JUPyiwrYJFskUPiHa7hkeR8VUtAeFfgoV8QnqY7bRxG6",  # JUP
                    quote_token="So11111111111111111111111111111111111111112",  # SOL
                    max_position_size_usd=100.0,
                    min_position_size_usd=10.0
                )
            ],
            risk_parameters=RiskParameters(),
            ai_parameters=AIParameters(),
            trading_parameters=TradingParameters()
        )
    return current_config

# Routes
@router.get("/current", response_model=BotConfiguration)
async def get_configuration(
    current_user: User = Depends(require_auth())
):
    """
    Get current bot configuration.
    
    Returns the complete configuration including trading pairs, risk parameters, and AI settings.
    """
    config = get_current_config()
    config.updated_at = datetime.utcnow()
    return config

@router.get("/trading-pairs", response_model=List[TradingPairConfig])
async def get_trading_pairs(
    current_user: User = Depends(require_auth())
):
    """Get configured trading pairs."""
    config = get_current_config()
    return config.trading_pairs

@router.post("/trading-pairs", response_model=TradingPairConfig)
async def add_trading_pair(
    pair: TradingPairConfig,
    current_user: User = Depends(require_auth())
):
    """Add a new trading pair."""
    config = get_current_config()
    
    # Check if pair already exists
    for existing in config.trading_pairs:
        if existing.base_token == pair.base_token and existing.quote_token == pair.quote_token:
            raise HTTPException(status_code=400, detail="Trading pair already exists")
    
    config.trading_pairs.append(pair)
    config.updated_at = datetime.utcnow()
    
    return pair

@router.delete("/trading-pairs/{base_token}")
async def remove_trading_pair(
    base_token: str,
    current_user: User = Depends(require_auth())
):
    """Remove a trading pair."""
    config = get_current_config()
    
    # Find and remove the pair
    removed = False
    config.trading_pairs = [
        p for p in config.trading_pairs 
        if p.base_token != base_token
    ]
    
    if len(config.trading_pairs) == 0:
        raise HTTPException(status_code=400, detail="Cannot remove all trading pairs")
    
    config.updated_at = datetime.utcnow()
    
    return {"success": True, "message": "Trading pair removed"}

@router.get("/risk", response_model=RiskParameters)
async def get_risk_parameters(
    current_user: User = Depends(require_auth())
):
    """Get current risk management parameters."""
    config = get_current_config()
    return config.risk_parameters

@router.put("/risk", response_model=RiskParameters)
async def update_risk_parameters(
    params: RiskParameters,
    current_user: User = Depends(require_auth())
):
    """Update risk management parameters."""
    config = get_current_config()
    config.risk_parameters = params
    config.updated_at = datetime.utcnow()
    
    return params

@router.get("/ai", response_model=AIParameters)
async def get_ai_parameters(
    current_user: User = Depends(require_auth())
):
    """Get AI Agent configuration parameters."""
    config = get_current_config()
    return config.ai_parameters

@router.put("/ai", response_model=AIParameters)
async def update_ai_parameters(
    params: AIParameters,
    current_user: User = Depends(require_auth())
):
    """Update AI Agent configuration parameters."""
    config = get_current_config()
    config.ai_parameters = params
    config.updated_at = datetime.utcnow()
    
    return params

@router.get("/trading", response_model=TradingParameters)
async def get_trading_parameters(
    current_user: User = Depends(require_auth())
):
    """Get general trading parameters."""
    config = get_current_config()
    return config.trading_parameters

@router.put("/trading", response_model=TradingParameters)
async def update_trading_parameters(
    params: TradingParameters,
    current_user: User = Depends(require_auth())
):
    """Update general trading parameters."""
    config = get_current_config()
    config.trading_parameters = params
    config.updated_at = datetime.utcnow()
    
    return params

@router.post("/validate")
async def validate_configuration(
    config: BotConfiguration,
    current_user: User = Depends(require_auth())
):
    """
    Validate a configuration without applying it.
    
    Checks for logical errors and inconsistencies.
    """
    errors = []
    warnings = []
    
    # Validate trading pairs
    if len(config.trading_pairs) == 0:
        errors.append("At least one trading pair must be configured")
    
    total_max_position = sum(p.max_position_size_usd for p in config.trading_pairs if p.enabled)
    if total_max_position > config.risk_parameters.max_daily_loss_usd * 2:
        warnings.append("Total max position size exceeds 2x daily loss limit")
    
    # Validate risk parameters
    if config.risk_parameters.stop_loss_percent >= config.risk_parameters.take_profit_percent:
        warnings.append("Stop loss is greater than or equal to take profit")
    
    if config.risk_parameters.enable_trailing_stop and not config.risk_parameters.trailing_stop_percent:
        errors.append("Trailing stop enabled but percentage not set")
    
    # Validate AI parameters
    if config.ai_parameters.confidence_threshold < 0.5:
        warnings.append("Low confidence threshold may result in poor trades")
    
    # Validate trading parameters
    if config.trading_parameters.cycle_interval_minutes < 5:
        warnings.append("Very short cycle interval may cause excessive API calls")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

@router.post("/export")
async def export_configuration(
    current_user: User = Depends(require_auth())
):
    """Export current configuration as JSON."""
    config = get_current_config()
    return config.dict()

@router.post("/import")
async def import_configuration(
    config: BotConfiguration,
    current_user: User = Depends(require_auth())
):
    """Import configuration from JSON."""
    global current_config
    
    # Validate the configuration first
    validation = await validate_configuration(config, current_user)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid configuration: {', '.join(validation['errors'])}"
        )
    
    current_config = config
    current_config.updated_at = datetime.utcnow()
    
    return {"success": True, "message": "Configuration imported successfully"}

@router.get("/presets")
async def get_configuration_presets(
    current_user: User = Depends(require_auth())
):
    """Get available configuration presets."""
    return {
        "conservative": {
            "name": "Conservative",
            "description": "Low risk, stable returns",
            "risk_level": "CONSERVATIVE",
            "max_daily_loss_usd": 50,
            "max_position_size_percent": 5,
            "stop_loss_percent": 3,
            "take_profit_percent": 5
        },
        "moderate": {
            "name": "Moderate",
            "description": "Balanced risk and returns",
            "risk_level": "MODERATE",
            "max_daily_loss_usd": 100,
            "max_position_size_percent": 10,
            "stop_loss_percent": 5,
            "take_profit_percent": 10
        },
        "aggressive": {
            "name": "Aggressive",
            "description": "Higher risk, higher potential returns",
            "risk_level": "AGGRESSIVE",
            "max_daily_loss_usd": 200,
            "max_position_size_percent": 20,
            "stop_loss_percent": 7,
            "take_profit_percent": 15
        }
    }

class ConfigItem(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    is_sensitive: bool = False

class ConfigUpdate(BaseModel):
    updates: Dict[str, Any]

@router.get("/trading")
async def get_trading_config(token_data: TokenData = Depends(verify_token)):
    """Get trading configuration."""
    return {
        "default_slippage_bps": int(os.getenv("DEFAULT_SLIPPAGE_BPS", "100")),
        "max_trade_size_usd": float(os.getenv("MAX_TRADE_SIZE_USD", "1000")),
        "risk_level": os.getenv("RISK_LEVEL", "MODERATE"),
        "enabled_strategies": os.getenv("ENABLED_STRATEGIES", "momentum,mean_reversion").split(","),
        "auto_trading": os.getenv("AUTO_TRADING", "false").lower() == "true"
    }

@router.put("/trading")
async def update_trading_config(config: ConfigUpdate, token_data: TokenData = Depends(verify_token)):
    """Update trading configuration."""
    # In production, this would update a database or config file
    logger.info(f"Trading config updated by {token_data.username}: {config.updates}")
    return {"message": "Trading configuration updated successfully", "updates": config.updates}

@router.get("/api")
async def get_api_config(token_data: TokenData = Depends(verify_token)):
    """Get API configuration."""
    return {
        "jupiter_api_url": os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag"),
        "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        "timeout_seconds": int(os.getenv("API_TIMEOUT_SECONDS", "30")),
        "retry_attempts": int(os.getenv("API_RETRY_ATTEMPTS", "3"))
    }

@router.get("/system")
async def get_system_config(token_data: TokenData = Depends(verify_token)):
    """Get system configuration."""
    return {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "data_retention_days": int(os.getenv("DATA_RETENTION_DAYS", "30")),
        "backup_enabled": os.getenv("BACKUP_ENABLED", "true").lower() == "true",
        "monitoring_enabled": os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    }