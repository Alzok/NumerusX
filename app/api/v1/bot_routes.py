"""
Bot control routes for API v1.
Handles bot start/stop, status, and configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from .auth_routes import verify_token, TokenData

router = APIRouter()
logger = logging.getLogger(__name__)

# Global bot instance (will be injected from main.py)
bot_instance = None


class BotStatus(BaseModel):
    is_running: bool
    start_time: Optional[datetime] = None
    uptime_seconds: Optional[int] = None
    current_cycle: Optional[int] = None
    last_trade_time: Optional[datetime] = None
    trades_today: int = 0
    pnl_today_usd: float = 0.0
    errors_count: int = 0
    last_error: Optional[str] = None


class BotConfig(BaseModel):
    cycle_interval_seconds: int = Field(default=30, ge=5, le=3600)
    max_trades_per_day: int = Field(default=10, ge=1, le=100)
    daily_loss_limit_usd: float = Field(default=1000, gt=0)
    enabled_strategies: list[str] = Field(default_factory=list)
    risk_level: str = Field(default="MODERATE")
    auto_start: bool = Field(default=False)


class BotCommand(BaseModel):
    action: str = Field(..., description="Action to perform: start, stop, restart")
    config: Optional[BotConfig] = None


def get_bot_instance():
    """Get the current bot instance."""
    global bot_instance
    if bot_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot instance not available"
        )
    return bot_instance


@router.get("/status", response_model=BotStatus)
async def get_bot_status(token_data: TokenData = Depends(verify_token)):
    """
    Get current bot status and statistics.
    """
    try:
        bot = get_bot_instance()
        
        # Calculate uptime
        uptime_seconds = None
        if bot.start_time:
            uptime_seconds = int((datetime.utcnow() - bot.start_time).total_seconds())
        
        return BotStatus(
            is_running=bot.is_running,
            start_time=bot.start_time,
            uptime_seconds=uptime_seconds,
            current_cycle=getattr(bot, 'cycle_count', 0),
            last_trade_time=getattr(bot, 'last_trade_time', None),
            trades_today=getattr(bot, 'trades_today', 0),
            pnl_today_usd=getattr(bot, 'pnl_today_usd', 0.0),
            errors_count=getattr(bot, 'errors_count', 0),
            last_error=getattr(bot, 'last_error', None)
        )
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot status: {str(e)}"
        )


@router.post("/control")
async def control_bot(command: BotCommand, token_data: TokenData = Depends(verify_token)):
    """
    Control bot operations (start, stop, restart).
    """
    try:
        bot = get_bot_instance()
        
        if command.action == "start":
            if bot.is_running:
                return {"message": "Bot is already running", "status": "running"}
            
            # Apply config if provided
            if command.config:
                await update_bot_config(command.config)
            
            await bot.start()
            return {"message": "Bot started successfully", "status": "running"}
            
        elif command.action == "stop":
            if not bot.is_running:
                return {"message": "Bot is already stopped", "status": "stopped"}
            
            await bot.stop()
            return {"message": "Bot stopped successfully", "status": "stopped"}
            
        elif command.action == "restart":
            if bot.is_running:
                await bot.stop()
                await asyncio.sleep(2)  # Brief pause between stop and start
            
            # Apply config if provided
            if command.config:
                await update_bot_config(command.config)
                
            await bot.start()
            return {"message": "Bot restarted successfully", "status": "running"}
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {command.action}. Valid actions: start, stop, restart"
            )
            
    except Exception as e:
        logger.error(f"Error controlling bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {command.action} bot: {str(e)}"
        )


@router.get("/config", response_model=BotConfig)
async def get_bot_config(token_data: TokenData = Depends(verify_token)):
    """
    Get current bot configuration.
    """
    try:
        bot = get_bot_instance()
        
        # Extract config from bot instance
        config = BotConfig(
            cycle_interval_seconds=getattr(bot, 'cycle_interval', 30),
            max_trades_per_day=getattr(bot, 'max_trades_per_day', 10),
            daily_loss_limit_usd=getattr(bot, 'daily_loss_limit_usd', 1000),
            enabled_strategies=getattr(bot, 'enabled_strategies', []),
            risk_level=getattr(bot, 'risk_level', 'MODERATE'),
            auto_start=getattr(bot, 'auto_start', False)
        )
        
        return config
        
    except Exception as e:
        logger.error(f"Error getting bot config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot config: {str(e)}"
        )


@router.put("/config")
async def update_bot_config(config: BotConfig, token_data: TokenData = Depends(verify_token)):
    """
    Update bot configuration.
    """
    try:
        bot = get_bot_instance()
        
        # Apply configuration to bot
        bot.cycle_interval = config.cycle_interval_seconds
        bot.max_trades_per_day = config.max_trades_per_day
        bot.daily_loss_limit_usd = config.daily_loss_limit_usd
        bot.enabled_strategies = config.enabled_strategies
        bot.risk_level = config.risk_level
        bot.auto_start = config.auto_start
        
        logger.info(f"Bot configuration updated by user {token_data.username}")
        
        return {"message": "Bot configuration updated successfully", "config": config}
        
    except Exception as e:
        logger.error(f"Error updating bot config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bot config: {str(e)}"
        )


@router.get("/logs")
async def get_bot_logs(
    limit: int = 100,
    level: str = "INFO",
    token_data: TokenData = Depends(verify_token)
):
    """
    Get recent bot logs.
    """
    try:
        # This would typically read from a log file or database
        # For now, return a placeholder response
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Bot is running normally",
                "module": "DexBot"
            },
            {
                "timestamp": (datetime.utcnow()).isoformat(),
                "level": "DEBUG", 
                "message": "Market data fetched successfully",
                "module": "MarketDataProvider"
            }
        ]
        
        return {
            "logs": logs[:limit],
            "total_count": len(logs),
            "filters": {"level": level, "limit": limit}
        }
        
    except Exception as e:
        logger.error(f"Error getting bot logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot logs: {str(e)}"
        )


@router.post("/emergency-stop")
async def emergency_stop(token_data: TokenData = Depends(verify_token)):
    """
    Emergency stop the bot immediately.
    """
    try:
        bot = get_bot_instance()
        
        if not bot.is_running:
            return {"message": "Bot is not running", "status": "stopped"}
        
        # Force stop without graceful shutdown
        await bot.emergency_stop()
        
        logger.warning(f"Emergency stop triggered by user {token_data.username}")
        
        return {"message": "Bot emergency stopped", "status": "stopped"}
        
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to emergency stop bot: {str(e)}"
        )


def set_bot_instance(bot):
    """Set the bot instance for route handlers."""
    global bot_instance
    bot_instance = bot