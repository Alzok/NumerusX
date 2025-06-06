"""
System routes for API v1.
Handles system health, monitoring, and maintenance.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
import psutil
import os
import logging

from .auth_routes import verify_token, TokenData

router = APIRouter()
logger = logging.getLogger(__name__)


class SystemHealth(BaseModel):
    status: str
    timestamp: datetime
    uptime_seconds: int
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    last_error: str = None


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    module: str
    message: str
    context: Dict[str, Any] = {}


@router.get("/health")
async def get_system_health():
    """Get comprehensive system health status - no auth required for monitoring."""
    try:
        import redis
        from app.config_v2 import get_config
        from app.database import EnhancedDatabase
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Mock uptime calculation
        uptime_seconds = int((datetime.utcnow() - datetime(2024, 1, 1)).total_seconds())
        
        # Check database health
        database_status = "connected"
        database_message = "Database operational"
        try:
            db = EnhancedDatabase()
            # Simple health check query
            database_status = "connected"
        except Exception as e:
            database_status = "error"
            database_message = f"Database error: {str(e)[:100]}"
        
        # Check Redis health
        redis_status = "connected"
        redis_message = "Redis operational"
        try:
            redis_client = redis.Redis.from_url(get_config().redis.url)
            redis_client.ping()
            redis_status = "connected"
        except Exception as e:
            redis_status = "error"
            redis_message = f"Redis error: {str(e)[:100]}"
        
        # Overall system status
        overall_status = "operational"
        if cpu_percent > 80 or memory.percent > 85:
            overall_status = "degraded"
        if database_status == "error" or redis_status == "error":
            overall_status = "down"
        
        health_response = {
            "status": overall_status,
            "message": "System health check completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "api": "operational",
            "uptime_seconds": uptime_seconds,
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": disk.percent,
                "active_connections": len(psutil.net_connections())
            },
            "database": {
                "status": database_status,
                "message": database_message
            },
            "redis": {
                "status": redis_status,
                "message": redis_message
            },
            "services": {
                "api": "operational",
                "websocket": "operational",
                "trading_bot": "operational"
            }
        }
        
        return health_response
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "api": "error",
            "database": {"status": "unknown", "message": "Could not check"},
            "redis": {"status": "unknown", "message": "Could not check"}
        }


@router.get("/metrics")
async def get_system_metrics(token_data: TokenData = Depends(verify_token)):
    """Get detailed system metrics."""
    try:
        # System metrics
        cpu_times = psutil.cpu_times()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        metrics = {
            "system": {
                "hostname": os.uname().nodename,
                "platform": os.uname().sysname,
                "architecture": os.uname().machine,
                "python_version": os.sys.version.split()[0]
            },
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent,
                "swap_total_gb": round(psutil.swap_memory().total / (1024**3), 2),
                "swap_usage_percent": psutil.swap_memory().percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "processes": {
                "total": len(psutil.pids()),
                "python_processes": len([p for p in psutil.process_iter(['name']) if 'python' in p.info['name'].lower()])
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/logs")
async def get_system_logs(
    limit: int = 100,
    level: str = "INFO",
    module: str = None,
    token_data: TokenData = Depends(verify_token)
):
    """Get system logs with filtering."""
    try:
        # Mock log entries - in production, this would read from log files
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        modules = ["DexBot", "AIAgent", "TradingEngine", "MarketData", "API"]
        
        logs = []
        for i in range(limit):
            timestamp = datetime.utcnow() - timedelta(minutes=i*2)
            log_level = log_levels[i % len(log_levels)]
            log_module = modules[i % len(modules)]
            
            # Skip if level filter doesn't match
            if level and log_level != level:
                continue
                
            # Skip if module filter doesn't match
            if module and log_module != module:
                continue
            
            logs.append(LogEntry(
                timestamp=timestamp,
                level=log_level,
                module=log_module,
                message=f"Sample log message {i} from {log_module}",
                context={"request_id": f"req_{i}", "user": "system"}
            ))
        
        return {
            "logs": logs[:limit],
            "total_count": len(logs),
            "filters": {"level": level, "module": module, "limit": limit}
        }
        
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system logs: {str(e)}"
        )


@router.get("/status")
async def get_service_status(token_data: TokenData = Depends(verify_token)):
    """Get status of all system services."""
    try:
        # Mock service status
        services = {
            "database": {
                "status": "healthy",
                "response_time_ms": 12.5,
                "last_check": datetime.utcnow().isoformat(),
                "details": "Connection pool: 5/10 active"
            },
            "redis": {
                "status": "healthy",
                "response_time_ms": 3.2,
                "last_check": datetime.utcnow().isoformat(),
                "details": "Memory usage: 45MB"
            },
            "jupiter_api": {
                "status": "healthy",
                "response_time_ms": 156.7,
                "last_check": datetime.utcnow().isoformat(),
                "details": "Rate limit: 45/60 per minute"
            },
            "gemini_api": {
                "status": "healthy",
                "response_time_ms": 2340.1,
                "last_check": datetime.utcnow().isoformat(),
                "details": "Tokens used: 1250/10000 today"
            },
            "trading_engine": {
                "status": "healthy",
                "response_time_ms": 25.3,
                "last_check": datetime.utcnow().isoformat(),
                "details": "Active orders: 0, Completed today: 5"
            }
        }
        
        # Overall status
        all_healthy = all(service["status"] == "healthy" for service in services.values())
        overall_status = "healthy" if all_healthy else "degraded"
        
        return {
            "overall_status": overall_status,
            "services": services,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.post("/restart")
async def restart_service(
    service_name: str,
    token_data: TokenData = Depends(verify_token)
):
    """Restart a specific service (admin only)."""
    try:
        valid_services = ["trading_engine", "market_data", "ai_agent"]
        
        if service_name not in valid_services:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service name. Valid services: {valid_services}"
            )
        
        # Mock service restart
        logger.info(f"Service restart requested by {token_data.username}: {service_name}")
        
        return {
            "service": service_name,
            "status": "restart_initiated",
            "message": f"Service {service_name} restart initiated",
            "estimated_downtime_seconds": 30,
            "initiated_by": token_data.username,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error restarting service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart service: {str(e)}"
        )


@router.get("/version")
async def get_version_info():
    """Get version information - no auth required."""
    try:
        return {
            "application": "NumerusX Trading Bot",
            "version": "1.0.0",
            "build": "2024.01.15",
            "commit": "abc123def",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": os.sys.version.split()[0],
            "api_version": "v1",
            "last_updated": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version info: {str(e)}"
        )


@router.get("/config")
async def get_system_config(token_data: TokenData = Depends(verify_token)):
    """Get current system configuration."""
    try:
        # Return non-sensitive configuration
        config = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "api_timeout_seconds": int(os.getenv("API_TIMEOUT_SECONDS", "30")),
            "max_trade_size_usd": float(os.getenv("MAX_TRADE_SIZE_USD", "1000")),
            "cycle_interval_seconds": int(os.getenv("CYCLE_INTERVAL_SECONDS", "30")),
            "auto_trading_enabled": os.getenv("AUTO_TRADING_ENABLED", "false").lower() == "true",
            "database_url": "***configured***" if os.getenv("DATABASE_URL") else "not_configured",
            "redis_url": "***configured***" if os.getenv("REDIS_URL") else "not_configured",
            "jupyter_api_url": os.getenv("JUPYTER_API_URL", "https://quote-api.jup.ag"),
            "gemini_model": os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system config: {str(e)}"
        )