import asyncio
import logging
import signal
import sys
import os
# Removed nicegui imports
# from nicegui import ui
# from app.gui import TradingDashboard 
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Security, Request, Depends # Added Security, Request, Depends
import socketio # Added socketio
from fastapi.responses import JSONResponse # Added JSONResponse
from pydantic import BaseModel, Field # Added BaseModel, Field
from typing import List, Optional # Added List, Optional
from fastapi.staticfiles import StaticFiles # Added StaticFiles
from fastapi.templating import Jinja2Templates # Added Jinja2Templates (optional, for serving index.html)
from fastapi.middleware.cors import CORSMiddleware # Added CORSMiddleware

from app.dex_bot import DexBot # Keep for now, might be used by API later
from app.config import Config
from app.logger import DexLogger # DexLogger might be obsolete if configure_logging is used
from app.utils.auth import VerifyToken, AuthError # Import VerifyToken and AuthError
from app.socket_manager import get_socket_manager # Import the new socket manager

from fastapi_limiter import FastAPILimiter # Import FastAPILimiter
from fastapi_limiter.depends import RateLimiter # Import RateLimiter dependency
import redis.asyncio as redis # Import async redis for limiter

# Import the main API router
from app.api.v1 import api_router

# Global instances
app = FastAPI(
    title="NumerusX Backend",
    version="1.0.0",
    description="AI-powered cryptocurrency trading bot for Solana",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORSMiddleware to the FastAPI app instance
# Ensure Config.CORS_ALLOWED_ORIGINS is defined and loaded correctly in your Config class.
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ALLOWED_ORIGINS if hasattr(Config, 'CORS_ALLOWED_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# Initialize SocketManager and get the app and server instance
cors_origins = Config.CORS_ALLOWED_ORIGINS if hasattr(Config, 'CORS_ALLOWED_ORIGINS') else ["*"]
socket_man = get_socket_manager(cors_allowed_origins=cors_origins)
sio = socket_man.sio # This is the socketio.AsyncServer instance
# Mount the Socket.IO app. The SocketManager's app is already configured.
# We need to ensure it's mounted correctly with the FastAPI app.
# The original socket_app = socketio.ASGIApp(sio, other_asgi_app=app) is effectively what socket_man.app should be, 
# but socket_man.app should already have `app` as its `other_asgi_app` if we make a small change to SocketManager or how it's used.
# For now, let's assume socket_man.app is the main ASGI app for Socket.IO and FastAPI is mounted as a sub-app or vice-versa.
# The simplest integration is to mount the SocketManager's ASGIApp (which includes the FastAPI app if designed that way).
# Let's adjust main.py to use the SocketManager's app as the primary entry for Uvicorn, or mount it under FastAPI.

# If SocketManager.app is just the socketio.ASGIApp without FastAPI, then:
# app.mount("/ws", socket_man.app) # Mounts socket.io at /ws path
# And uvicorn would run `app` (FastAPI instance).

# If SocketManager.app is socketio.ASGIApp(sio_server, other_asgi_app=fast_api_instance),
# then we need to ensure this is done correctly. The current SocketManager does:
# SocketManager._sio_app = socketio.ASGIApp(SocketManager._sio_server)
# This means it does NOT include FastAPI yet. We need to attach FastAPI to it.

# Integrate Socket.IO with FastAPI
if socket_man.app:
    # Re-wrap the SocketManager's pure ASGI app with FastAPI as the fallback
    # This makes FastAPI handle all non-Socket.IO requests.
    # The `app` (FastAPI instance) becomes the `other_asgi_app`.
    final_asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)
else:
    # Fallback if socket_man.app is None, though get_socket_manager should always return one.
    logging.critical("SocketManager app is None, WebSocket functionality will be unavailable.")
    final_asgi_app = app # Run FastAPI without Socket.IO

# Include API router
app.include_router(api_router, prefix="/api/v1")

auth_verifier = VerifyToken() # Initialize the token verifier

# Mount static files for React UI (conditional or for development)
# This assumes your React app is built into a directory named 'static/ui'
# at the root of where the FastAPI app is run, or you adjust the path.
# In a production Docker setup with Nginx, Nginx would typically serve these.
UI_BUILD_DIR = "static/ui" # This path needs to exist relative to where app/main.py is run or be an absolute path.

if os.path.exists(UI_BUILD_DIR) and os.path.isdir(UI_BUILD_DIR):
    app.mount("/static", StaticFiles(directory=UI_BUILD_DIR + "/static"), name="react_static")
    templates = Jinja2Templates(directory=UI_BUILD_DIR)

    @app.get("/{full_path:path}")
    async def serve_react_app(request: Request, full_path: str):
        """Serves the React app (index.html for all non-API/static routes)."""
        # This catch-all route is essential for client-side routing in React.
        # It should be one of the last routes defined.
        logging.debug(f"Attempting to serve React app for path: {full_path}")
        index_path = os.path.join(UI_BUILD_DIR, "index.html")
        if os.path.exists(index_path):
            return templates.TemplateResponse("index.html", {"request": request})
        else:
            logging.error(f"index.html not found in {UI_BUILD_DIR}")
            return JSONResponse(status_code=404, content={"detail": "React app index.html not found."})
else:
    logging.warning(f"React UI build directory not found at '{UI_BUILD_DIR}'. UI will not be served by FastAPI.")

# Pydantic models for API configuration
class ConfigurableParameter(BaseModel):
    key: str
    value: str # All values as strings for simplicity, cast as needed on backend
    description: Optional[str] = None

class GetConfigResponse(BaseModel):
    configurable_parameters: List[ConfigurableParameter]
    info: str

class UpdateConfigRequest(BaseModel):
    parameters_to_update: List[ConfigurableParameter]

# Pydantic models for Bot Control
class BotActionResponse(BaseModel):
    message: str
    status_sent: Optional[str] = None

# Pydantic models for Data Endpoints
class ManualTradeRequest(BaseModel):
    pair: str = Field(..., example="SOL/USDC")
    type: str = Field(..., example="BUY") # BUY or SELL
    amount_usd: float = Field(..., example=100.0)
    # Add other relevant fields like slippage, order_type (MARKET, LIMIT) if needed

class TradeEntry(BaseModel):
    trade_id: str
    pair: str
    type: str
    amount_tokens: float
    price_usd: float
    timestamp_utc: str
    status: str
    reason_source: str

class TradeHistoryResponse(BaseModel):
    trades: List[TradeEntry]
    total_trades: int
    limit: int
    offset: int

class AIDecisionEntry(BaseModel):
    decision_id: str
    decision: str # BUY, SELL, HOLD
    token_pair: str
    confidence: float
    reasoning_snippet: str
    timestamp_utc: str

class AIDecisionHistoryResponse(BaseModel):
    decisions: List[AIDecisionEntry]
    total_decisions: int
    limit: int
    offset: int

class PortfolioPosition(BaseModel):
    asset: str
    amount: float
    avg_buy_price: float
    current_price: float
    value_usd: float

class PortfolioSnapshotResponse(BaseModel):
    total_value_usd: float
    pnl_24h_usd: float
    positions: List[PortfolioPosition]
    available_cash_usdc: float
    timestamp_utc: str

# Pydantic models for System Info Endpoints
class LogEntry(BaseModel):
    timestamp_utc: str
    level: str
    module: str
    message: str

class LogsResponse(BaseModel):
    logs: List[LogEntry]
    service_name_filter: Optional[str] = None
    total_logs_returned: int
    limit: int

class ServiceHealth(BaseModel):
    service_name: str
    status: str # e.g., "OPERATIONAL", "DEGRADED", "ERROR"
    details: Optional[str] = None

class SystemHealthResponse(BaseModel):
    overall_status: str # e.g., "ALL_SYSTEMS_OPERATIONAL", "PARTIAL_OUTAGE", "CRITICAL_ERROR"
    services: List[ServiceHealth]
    timestamp_utc: str

# Store background tasks
background_tasks = set()

def configure_logging():
    """Configuration avancée du système de logging"""
    # Ensure Config.LOG_LEVEL and Config.get_log_file_path() are valid
    log_level_str = getattr(Config, 'LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    logger = logging.getLogger() # Get root logger
    # Clear existing handlers to avoid duplicate logs if this is called multiple times or by uvicorn
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    log_file_path = Config.get_log_file_path() if hasattr(Config, 'get_log_file_path') else "numerusx.log"

    # Handler pour fichiers logs
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout) # Explicitly use stdout
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logging.info(f"Logging configured. Level: {log_level_str}, File: {log_file_path}")


def check_environment():
    """Vérifie les variables d'environnement requises"""
    # Check for the essential encryption key
    missing = []
    
    # Check for MASTER_ENCRYPTION_KEY which is the current encryption system
    if not hasattr(Config, 'MASTER_ENCRYPTION_KEY_ENV') or not Config.MASTER_ENCRYPTION_KEY_ENV:
        missing.append('MASTER_ENCRYPTION_KEY')
    
    # Check for Solana private key (either plain or encrypted)
    has_solana_key = (
        (hasattr(Config, 'SOLANA_PRIVATE_KEY_BS58') and Config.SOLANA_PRIVATE_KEY_BS58) or
        (hasattr(Config, 'ENCRYPTED_SOLANA_PRIVATE_KEY_BS58') and Config.ENCRYPTED_SOLANA_PRIVATE_KEY_BS58) or
        (hasattr(Config, 'WALLET_PATH') and Config.WALLET_PATH and os.path.exists(Config.WALLET_PATH))
    )
    
    if not has_solana_key:
        missing.append('SOLANA_PRIVATE_KEY (any form: BS58, encrypted, or wallet file)')
    
    if missing:
        logging.critical(f"Variables d'environnement critiques manquantes ou non définies: {', '.join(missing)}")
        # In development mode, we can be more lenient
        if Config.DEV_MODE:
            logging.warning("Running in DEV_MODE - proceeding despite missing critical variables")
            return
        
        raise RuntimeError(f"Missing critical environment variables: {', '.join(missing)}")


async def startup_event():
    """Actions to perform on application startup."""
    configure_logging() # Configure logging at startup
    try:
        check_environment() # Check environment variables
    except RuntimeError as e:
        logging.critical(f"Application startup failed due to missing env vars: {e}")
        # Depending on deployment, may want to sys.exit or let it run to show error via API
        # For now, logging critical and continuing might be better for visibility if deployed.
        # raise # Re-raise to prevent app from starting if check_environment is critical path

    logging.info("NumerusX FastAPI application startup complete.")
    # Initialize DexBot or other services here if needed globally
    # Example:
    # global_dex_bot = DexBot()
    # app.state.dex_bot = global_dex_bot # Make it accessible in request handlers
    # logging.info("DexBot initialized and available at app.state.dex_bot")

    # Initialize Redis for FastAPI-Limiter
    try:
        # Use Config.REDIS_URL which should be correctly formatted
        redis_connection = redis.from_url(Config.REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)
        logging.info(f"FastAPI-Limiter initialized with Redis: {Config.REDIS_URL}")
    except Exception as e:
        logging.error(f"Failed to initialize FastAPI-Limiter with Redis: {e}. Rate limiting will not work.", exc_info=True)
    
    # Set socket manager for bot routes (for WebSocket notifications)
    from app.api.v1.bot_routes import set_bot_instance
    # set_bot_instance(global_dex_bot)  # This would be set when DexBot is initialized


async def shutdown_event():
    """Actions to perform on application shutdown."""
    logging.info("NumerusX FastAPI application shutting down...")
    # Perform cleanup tasks
    # e.g., close DexBot if it has an async close method
    # if hasattr(app.state, 'dex_bot') and hasattr(app.state.dex_bot, 'close'):
    #    await app.state.dex_bot.close()
    
    # Cancel all background tasks
    for task in list(background_tasks): # Iterate over a copy
        if not task.done():
            task.cancel()
            try:
                await task # Allow task to process cancellation
            except asyncio.CancelledError:
                logging.info(f"Task {task.get_name()} cancelled successfully.")
            except Exception as e:
                logging.error(f"Error during cancellation of task {task.get_name()}: {e}", exc_info=True)
        background_tasks.discard(task)

    logging.info("NumerusX FastAPI application shutdown complete.")

# Register startup and shutdown events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Add custom exception handler for AuthError
@app.exception_handler(AuthError)
async def auth_exception_handler(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.error_detail},
    )

# Mount the main API router
app.include_router(api_router)

# Basic root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to NumerusX Backend API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

# Health check endpoint (same as system/health but at root level for monitoring)
@app.get("/health")
async def health_check():
    """Simple health check for load balancers and monitoring."""
    try:
        return {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "version": "1.0.0",
            "api": "operational"
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": "2024-01-15T10:30:00Z",
            "error": str(e)
        }

# Default Socket.IO event handlers (can be moved to SocketManager or kept here if specific to main app logic)
# Note: SocketManager already registers connect and disconnect. If kept here, they might override or be duplicated.
# It's cleaner to have them in SocketManager. Removing from here if they are in SocketManager.

# @sio.event
# async def connect(sid, environ, auth_data=None):
#     logging.info(f'Socket.IO client connected: {sid}')
#     # TODO: Authentication logic for socket connection using auth_data (e.g., JWT token)
#     # if not auth_data or not auth_data.get('token') or not auth_verifier.verify_socket_token(auth_data.get('token')):
#     #     logging.warning(f"Socket.IO connection attempt by {sid} rejected due to invalid auth.")
#     #     raise socketio.exceptions.ConnectionRefusedError('Authentication failed!')
#     # logging.info(f"Socket.IO client {sid} authenticated successfully.")
#     await sio.emit('response', {'data': 'Connected to NumerusX Socket.IO'}, room=sid)

# @sio.event
# async def disconnect(sid):
#     logging.info(f'Socket.IO client disconnected: {sid}')

@sio.event
async def chat_message(sid, data):
    logging.info(f'Socket.IO message from {sid}: {data}')
    await sio.emit('chat_message', data, room=sid) # Echo back for now

# Keep these example endpoints for backward compatibility
@app.get("/api/v1/private")
async def private_route(payload: dict = Security(auth_verifier.verify)):
    """A valid access token is required to access this route."""
    # The 'payload' here is the decoded JWT token claims
    return {"message": "Hello from a private endpoint! You are authenticated.", "user_info": payload}

# Public API endpoint example (no auth needed)
@app.get("/api/v1/public", dependencies=[Depends(RateLimiter(times=10, seconds=60))]) # Example global limit
async def public_route():
    return {"message": "This is a public route!"}

# NOTE: These old endpoints are now replaced by the new API routes
# They are kept here temporarily for backward compatibility but should be removed
# once the frontend is updated to use the new endpoints

# NumerusX specific Socket.IO events
@sio.on('start_bot')
async def handle_start_bot(sid, data):
    """Handles the start_bot command from the UI."""
    logging.info(f"Received start_bot command from {sid} with data: {data}")
    # Placeholder: Add logic to actually start the bot
    # This would typically involve calling a method on the DexBot instance
    # e.g., if app.state.dex_bot: await app.state.dex_bot.start()
    await sio.emit('bot_status_update', {'status': 'STARTING', 'message': 'Bot startup initiated.'}, room=sid)
    # Simulate bot starting and then running
    await asyncio.sleep(2) # Simulate startup delay
    await sio.emit('bot_status_update', {'status': 'RUNNING', 'message': 'Bot is now running.'}) # Broadcast to all or room

@sio.on('stop_bot')
async def handle_stop_bot(sid, data):
    """Handles the stop_bot command from the UI."""
    logging.info(f"Received stop_bot command from {sid} with data: {data}")
    # Placeholder: Add logic to actually stop the bot
    await sio.emit('bot_status_update', {'status': 'STOPPING', 'message': 'Bot shutdown initiated.'}, room=sid)
    await asyncio.sleep(1)
    await sio.emit('bot_status_update', {'status': 'STOPPED', 'message': 'Bot has been stopped.'})

async def emit_portfolio_update():
    """Placeholder function to periodically emit portfolio updates."""
    # In a real application, this would fetch actual portfolio data
    dummy_portfolio_data = {
        "total_value_usd": 12345.67,
        "pnl_24h_usd": 150.0,
        "positions": [{"asset": "SOL", "amount": 10.5, "avg_buy_price": 150.0, "current_price": 165.0, "value_usd": 1732.5}],
        "available_cash_usdc": 4000.0
    }
    logging.info("Emitting portfolio_update")
    await sio.emit('portfolio_update', dummy_portfolio_data)

async def emit_bot_status():
    """Placeholder function to periodically emit bot status."""
    # In a real app, this would fetch actual bot status
    # For now, just an example
    # This could be integrated with the actual DexBot's status
    logging.info("Emitting bot_status_update (periodic)")
    await sio.emit('bot_status_update', {'status': 'RUNNING', 'current_cycle': 123, 'next_cycle_in_sec': 55})


# Example of a background task that could emit regular updates
async def periodic_updates_emitter():
    while True:
        await asyncio.sleep(10) # Emit updates every 10 seconds
        await emit_portfolio_update()
        await emit_bot_status()
        # Add more periodic updates here (e.g., market_data_update, system_health_update)

# In startup_event, you can create and store the background task
# async def startup_event():
# ...
#     if Config.RUN_PERIODIC_SOCKET_UPDATES: # Add a config flag for this
#         emitter_task = asyncio.create_task(periodic_updates_emitter())
#         background_tasks.add(emitter_task)
#         emitter_task.add_done_callback(background_tasks.discard)
#         logging.info("Periodic Socket.IO emitter task started.")
# ...

# NOTE: The old data retrieval and system endpoints have been replaced by the new API routes
# They are temporarily kept above for backward compatibility

# The main execution block is typically handled by Uvicorn directly pointing to app.main:socket_app
# For example: uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
# No explicit asyncio.run(main()) or ui.run_until_disconnected() here for FastAPI.

# The old signal handling might conflict with Uvicorn's. Uvicorn handles SIGINT/SIGTERM.
# Removing old handle_signals() and direct signal.signal calls.
# Uvicorn will call the shutdown_event handler.

# If you need to run this file directly for simple testing (though uvicorn is preferred):
if __name__ == "__main__":
    import uvicorn
    # Call configure_logging here if running directly for uvicorn to pick up initial logs
    # However, uvicorn has its own logging config. Best to let startup_event handle it.
    # configure_logging()
    
    # Note: Using final_asgi_app here, which wraps the FastAPI app with Socket.IO
    uvicorn.run(final_asgi_app, host=Config.API_HOST if hasattr(Config, 'API_HOST') else "0.0.0.0",
                port=int(Config.API_PORT) if hasattr(Config, 'API_PORT') else 8000,
                log_level=getattr(Config, 'LOG_LEVEL', 'info').lower())
    # The log_level here for uvicorn might be redundant if configure_logging() sets root logger level.
    # Uvicorn's access logs are separate.