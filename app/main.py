import asyncio
import logging
import signal
import sys
import os
# Removed nicegui imports
# from nicegui import ui
# from app.gui import TradingDashboard 
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Security, Request # Added Security, Request
import socketio # Added socketio
from fastapi.responses import JSONResponse # Added JSONResponse
from pydantic import BaseModel, Field # Added BaseModel, Field
from typing import List, Optional # Added List, Optional
from fastapi.staticfiles import StaticFiles # Added StaticFiles
from fastapi.templating import Jinja2Templates # Added Jinja2Templates (optional, for serving index.html)

from app.dex_bot import DexBot # Keep for now, might be used by API later
from app.config import Config
from app.logger import DexLogger # DexLogger might be obsolete if configure_logging is used
from app.utils.auth import VerifyToken, AuthError # Import VerifyToken and AuthError

# Global instances
app = FastAPI(title="NumerusX Backend", version="1.0.0")
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=Config.CORS_ALLOWED_ORIGINS if hasattr(Config, 'CORS_ALLOWED_ORIGINS') else ["*"]) # Adjust CORS as needed
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
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
    # This might need adjustment based on FastAPI app's direct needs vs. DexBot needs
    # For now, let's assume these are still critical if DexBot is to be managed.
    required_vars = ['ENCRYPTION_KEY', 'ENCRYPTED_SOLANA_PK'] 
    # If API keys for services are used directly by FastAPI endpoints, add them here.
    # e.g., JUPITER_API_KEY if used by some admin/manual trade endpoint.
    
    # Check against Config attributes
    missing = [var for var in required_vars if not hasattr(Config, var) or not getattr(Config, var)]
    
    if missing:
        logging.critical(f"Variables d'environnement critiques manquantes ou non définies: {', '.join(missing)}")
        # sys.exit(1) # Exit can be problematic for uvicorn reload, log critical and let app fail on use if needed
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

# Basic root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to NumerusX API"}

# Socket.IO example events (will be expanded)
@sio.event
async def connect(sid, environ, auth_data=None):
    logging.info(f"Socket.IO client connection attempt: {sid}, environ: {environ}")
    # auth_data is optionally passed by the client during connection:
    # client.connect(url, auth={'token': 'my_jwt_token'})
    if auth_data and 'token' in auth_data:
        token = auth_data['token']
        logging.debug(f"Auth data received from client {sid}: {auth_data}")
        try:
            # Use a non-Security wrapped version or adapt verify for this context
            # For simplicity, let's assume a synchronous check or a helper from auth_verifier
            # This is a simplified example. In a real scenario, you might need to adapt
            # the auth_verifier.verify method or create a specific one for socket auth
            # as it's not going through the standard FastAPI Depends/Security flow here.
            
            # Re-instantiate or use a method that doesn't rely on FastAPI's Depends for socket
            # For now, let's simulate a direct verification if possible or conceptualize it.
            # This is a conceptual placeholder for token validation.
            # payload = await auth_verifier.verify_socket_token(token) # Hypothetical method
            # For a quick test, one might decode it simply, but production needs full verification.
            
            # Placeholder: Simulate token validation for Socket.IO
            # In a real implementation, properly validate the token here using auth_verifier logic
            # This might involve creating a separate method in VerifyToken not reliant on FastAPI's `Depends`
            # or by adapting the existing one. For now, we assume if a token is present, it's valid for this example.
            if token.startswith("valid_jwt_prefix_"): # Replace with actual validation
                logging.info(f"Socket.IO client {sid} authenticated with token.")
                await sio.emit('message', {'data': 'Authenticated & Connected to NumerusX Socket.IO!'}, room=sid)
            else:
                logging.warning(f"Socket.IO client {sid} provided an invalid token. Disconnecting.")
                await sio.disconnect(sid)
                return False # Deny connection

        except AuthError as e: # Catch custom AuthError
            logging.warning(f"Socket.IO AuthError for {sid}: {e.error_detail}. Disconnecting.")
            # Optionally emit an error message to the client before disconnecting
            # await sio.emit('auth_error', {'error': e.error_detail}, room=sid)
            await sio.disconnect(sid)
            return False # Deny connection
        except Exception as e:
            logging.error(f"Socket.IO unexpected error during auth for {sid}: {e}. Disconnecting.", exc_info=True)
            await sio.disconnect(sid)
            return False # Deny connection
    else:
        logging.warning(f"Socket.IO client {sid} did not provide auth token. Disconnecting.")
        # Depending on policy, you might allow unauthenticated connections for certain namespaces/events
        # For now, strict: require token.
        await sio.disconnect(sid)
        return False # Deny connection
    
    logging.info(f"Socket.IO client connected and authenticated: {sid}")
    # Standard emit after successful connection and auth (if not done above)
    # await sio.emit('message', {'data': 'Connected to NumerusX Socket.IO!'}, room=sid)

@sio.event
async def disconnect(sid):
    logging.info(f"Socket.IO client disconnected: {sid}")

@sio.event
async def chat_message(sid, data):
    logging.info(f"Socket.IO message from {sid}: {data}")
    await sio.emit('chat_message', data, room=sid) # Echo back for now

# Protected API endpoint example
@app.get("/api/v1/private")
async def private_route(payload: dict = Security(auth_verifier.verify)):
    """A valid access token is required to access this route."""
    # The 'payload' here is the decoded JWT token claims
    return {"message": "Hello from a private endpoint! You are authenticated.", "user_info": payload}

# Public API endpoint example (no auth needed)
@app.get("/api/v1/public")
async def public_route():
    return {"message": "Hello from a public endpoint! No authentication required."}

# Configuration Endpoints
@app.get("/api/v1/config", response_model=GetConfigResponse, dependencies=[Security(auth_verifier.verify)])
async def get_bot_configuration():
    """Retrieve a list of user-configurable bot parameters."""
    # Expose only non-sensitive, configurable parameters
    # Values are read directly from the Config class (which loads from .env)
    configurable_params = [
        ConfigurableParameter(key="LOG_LEVEL", value=str(Config.LOG_LEVEL), description="Logging level (e.g., INFO, DEBUG)"),
        ConfigurableParameter(key="TRADING_UPDATE_INTERVAL_SECONDS", value=str(Config.TRADING_UPDATE_INTERVAL_SECONDS), description="Main trading cycle interval in seconds"),
        ConfigurableParameter(key="DEFAULT_STRATEGY_NAME", value=str(Config.DEFAULT_STRATEGY_NAME), description="Default trading strategy to use"),
        ConfigurableParameter(key="MAX_OPEN_POSITIONS", value=str(Config.MAX_OPEN_POSITIONS), description="Maximum number of concurrent open positions"),
        ConfigurableParameter(key="MAX_ORDER_SIZE_USD", value=str(Config.MAX_ORDER_SIZE_USD), description="Maximum size for a single order in USD"),
        # Add more configurable and non-sensitive parameters here
    ]
    return GetConfigResponse(
        configurable_parameters=configurable_params,
        info="These are some of the current bot configurations. Sensitive values are not exposed."
    )

@app.post("/api/v1/config", dependencies=[Security(auth_verifier.verify)])
async def update_bot_configuration(config_update: UpdateConfigRequest):
    """Update user-configurable bot parameters. Placeholder: Logs changes."""
    logging.info(f"Received request to update configuration: {config_update.model_dump_json(indent=2)}")
    
    # Placeholder for actual update logic
    # In a real application, you would:
    # 1. Validate each key and value.
    # 2. Update a user-specific config file (e.g., user_config.json) or .env (carefully!).
    # 3. Potentially signal the bot or relevant modules to reload their configuration.
    # For .env updates, libraries like `python-dotenv` (set_key, unset_key) can be used.
    # Be extremely cautious when writing to .env files, especially in a deployed environment.
    
    updated_params_log = []
    for param in config_update.parameters_to_update:
        logging.info(f"Attempting to update {param.key} to {param.value}")
        # Example: if param.key == "LOG_LEVEL": Config.LOG_LEVEL = param.value (this only changes in-memory)
        updated_params_log.append({"key": param.key, "new_value_attempted": param.value})

    # Note: Simply changing Config attributes here won't persist them unless Config class handles saving.
    # This is a simplified placeholder.
    return {"message": "Configuration update request received. See logs for details. Actual persistence not yet implemented.", "updated_parameters_logged": updated_params_log}

# Bot Control Endpoints
@app.post("/api/v1/bot/start", response_model=BotActionResponse, dependencies=[Security(auth_verifier.verify)])
async def start_bot_command():
    """Initiates the bot startup sequence."""
    logging.info("API endpoint /api/v1/bot/start called.")
    # Placeholder: Add logic to actually start the bot
    # e.g., if hasattr(app.state, 'dex_bot') and app.state.dex_bot: await app.state.dex_bot.start()
    # else: logging.error("DexBot not initialized in app.state")
    
    status_to_emit = "STARTING"
    await sio.emit('bot_status_update', {'status': status_to_emit, 'message': 'Bot startup initiated via API.'})
    # Simulate bot starting and then running - in real app, DexBot would manage its own status emits
    async def simulate_startup_and_run():
        await asyncio.sleep(2) 
        await sio.emit('bot_status_update', {'status': 'RUNNING', 'message': 'Bot is now running (simulated after API start).'})
    
    # Create a background task for simulation if not running in a test environment that handles this.
    # For now, direct emit then task.
    task = asyncio.create_task(simulate_startup_and_run())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    
    return BotActionResponse(message="Bot start command received. Emitting STARTING status.", status_sent=status_to_emit)

@app.post("/api/v1/bot/stop", response_model=BotActionResponse, dependencies=[Security(auth_verifier.verify)])
async def stop_bot_command():
    """Initiates the bot stop sequence."""
    logging.info("API endpoint /api/v1/bot/stop called.")
    # Placeholder: Add logic to actually stop the bot
    # e.g., if hasattr(app.state, 'dex_bot') and app.state.dex_bot: await app.state.dex_bot.stop()

    status_to_emit = "STOPPED"
    await sio.emit('bot_status_update', {'status': status_to_emit, 'message': 'Bot stop initiated via API.'})
    return BotActionResponse(message="Bot stop command received. Emitting STOPPED status.", status_sent=status_to_emit)

@app.post("/api/v1/bot/pause", response_model=BotActionResponse, dependencies=[Security(auth_verifier.verify)])
async def pause_bot_command():
    """Initiates the bot pause sequence."""
    logging.info("API endpoint /api/v1/bot/pause called.")
    # Placeholder: Add logic to actually pause the bot
    # e.g., if hasattr(app.state, 'dex_bot') and app.state.dex_bot: await app.state.dex_bot.pause()
    
    status_to_emit = "PAUSED"
    await sio.emit('bot_status_update', {'status': status_to_emit, 'message': 'Bot pause initiated via API.'})
    return BotActionResponse(message="Bot pause command received. Emitting PAUSED status.", status_sent=status_to_emit)

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

# Data Retrieval and Action Endpoints
@app.post("/api/v1/trades/manual", response_model=BotActionResponse, dependencies=[Security(auth_verifier.verify)])
async def manual_trade_command(trade_request: ManualTradeRequest):
    """Accepts a manual trade order from the user."""
    logging.info(f"API endpoint /api/v1/trades/manual called with: {trade_request.model_dump_json(indent=2)}")
    # Placeholder: Add logic to validate the trade_request
    # Then, pass it to TradeExecutor, e.g.:
    # success, result = await app.state.trade_executor.execute_manual_trade(trade_request)
    # For now, just log and return a success message
    await sio.emit('new_log_entry', {
        "level": "INFO", 
        "module": "API", 
        "message": f"Manual trade requested: {trade_request.pair}, {trade_request.type}, ${trade_request.amount_usd}"
    })
    return BotActionResponse(message=f"Manual trade request for {trade_request.pair} received and logged.")

@app.get("/api/v1/trades/history", response_model=TradeHistoryResponse, dependencies=[Security(auth_verifier.verify)])
async def get_trades_history(limit: int = 50, offset: int = 0):
    """Retrieves the history of executed trades."""
    logging.info(f"API endpoint /api/v1/trades/history called with limit={limit}, offset={offset}")
    # Placeholder: Fetch actual trade history from EnhancedDatabase
    dummy_trades = [
        TradeEntry(trade_id="t123", pair="SOL/USDC", type="BUY", amount_tokens=1.5, price_usd=160.0, timestamp_utc="2023-10-27T10:00:00Z", status="FILLED", reason_source="AI_AGENT"),
        TradeEntry(trade_id="t124", pair="BTC/USDC", type="SELL", amount_tokens=0.01, price_usd=34000.0, timestamp_utc="2023-10-27T11:00:00Z", status="FILLED", reason_source="MANUAL"),
    ]
    return TradeHistoryResponse(trades=dummy_trades, total_trades=len(dummy_trades), limit=limit, offset=offset)

@app.get("/api/v1/ai/decisions/history", response_model=AIDecisionHistoryResponse, dependencies=[Security(auth_verifier.verify)])
async def get_ai_decisions_history(limit: int = 50, offset: int = 0):
    """Retrieves the history of AI agent decisions."""
    logging.info(f"API endpoint /api/v1/ai/decisions/history called with limit={limit}, offset={offset}")
    # Placeholder: Fetch actual AI decision history from EnhancedDatabase
    dummy_decisions = [
        AIDecisionEntry(decision_id="d100", decision="BUY", token_pair="SOL/USDC", confidence=0.85, reasoning_snippet="RSI bullish, MACD crossover positive.", timestamp_utc="2023-10-27T09:55:00Z"),
        AIDecisionEntry(decision_id="d101", decision="HOLD", token_pair="ETH/USDC", confidence=0.50, reasoning_snippet="Market consolidating, waiting for clearer signal.", timestamp_utc="2023-10-27T10:55:00Z"),
    ]
    return AIDecisionHistoryResponse(decisions=dummy_decisions, total_decisions=len(dummy_decisions), limit=limit, offset=offset)

@app.get("/api/v1/portfolio/snapshot", response_model=PortfolioSnapshotResponse, dependencies=[Security(auth_verifier.verify)])
async def get_portfolio_snapshot():
    """Retrieves a snapshot of the current portfolio."""
    logging.info("API endpoint /api/v1/portfolio/snapshot called.")
    # Placeholder: Fetch actual portfolio data from PortfolioManager
    dummy_snapshot = PortfolioSnapshotResponse(
        total_value_usd=12550.75,
        pnl_24h_usd=120.25,
        positions=[
            PortfolioPosition(asset="SOL", amount=50.0, avg_buy_price=155.0, current_price=165.30, value_usd=8265.0),
            PortfolioPosition(asset="USDC", amount=4285.75, avg_buy_price=1.0, current_price=1.0, value_usd=4285.75),
        ],
        available_cash_usdc=4285.75, # Assuming USDC is the cash asset here
        timestamp_utc="2023-10-27T12:00:00Z"
    )
    return dummy_snapshot

# System Information Endpoints
@app.get("/api/v1/logs", response_model=LogsResponse, dependencies=[Security(auth_verifier.verify)])
async def get_system_logs(service_name: Optional[str] = None, limit: int = 100):
    """Retrieves system logs, optionally filtered by service name."""
    logging.info(f"API endpoint /api/v1/logs called. Service: {service_name}, Limit: {limit}")
    # Placeholder: Fetch actual logs from a centralized logging system or parse log files.
    # This is a very simplified example.
    dummy_logs = [
        LogEntry(timestamp_utc="2023-10-27T12:00:00Z", level="INFO", module="TradingEngine", message="Swap successful for SOL/USDC."),
        LogEntry(timestamp_utc="2023-10-27T12:01:00Z", level="WARNING", module="MarketDataProvider", message="DexScreener API latency high."),
    ]
    if service_name:
        filtered_logs = [log for log in dummy_logs if log.module.lower() == service_name.lower()]
    else:
        filtered_logs = dummy_logs
    
    return LogsResponse(
        logs=filtered_logs[:limit],
        service_name_filter=service_name,
        total_logs_returned=len(filtered_logs[:limit]),
        limit=limit
    )

@app.get("/api/v1/system/health", response_model=SystemHealthResponse, dependencies=[Security(auth_verifier.verify)])
async def get_system_health():
    """Retrieves the health status of various bot components."""
    logging.info("API endpoint /api/v1/system/health called.")
    # Placeholder: Implement actual health checks for each service.
    # This would involve pinging services, checking DB connections, API statuses, etc.
    dummy_services = [
        ServiceHealth(service_name="FastAPI Backend", status="OPERATIONAL"),
        ServiceHealth(service_name="SocketIO", status="OPERATIONAL"),
        ServiceHealth(service_name="DexBot Core", status="RUNNING"), # Would need actual status from DexBot
        ServiceHealth(service_name="JupiterApiClient", status="OPERATIONAL"),
        ServiceHealth(service_name="MarketDataProvider", status="OPERATIONAL"),
        ServiceHealth(service_name="TradingEngine", status="IDLE"),
        ServiceHealth(service_name="Database (SQLite)", status="OPERATIONAL"),
        ServiceHealth(service_name="GeminiClient", status="OPERATIONAL"),
        ServiceHealth(service_name="AuthenticationService", status="OPERATIONAL"),
    ]
    # Determine overall_status based on individual service statuses
    overall = "ALL_SYSTEMS_OPERATIONAL"
    if any(s.status == "ERROR" for s in dummy_services):
        overall = "CRITICAL_ERROR"
    elif any(s.status == "DEGRADED" for s in dummy_services):
        overall = "PARTIAL_OUTAGE"
        
    return SystemHealthResponse(
        overall_status=overall,
        services=dummy_services,
        timestamp_utc="2023-10-27T12:05:00Z" # Should be current time
    )

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
    
    # Note: Using socket_app here, which wraps the FastAPI app with Socket.IO
    uvicorn.run(socket_app, host=Config.API_HOST if hasattr(Config, 'API_HOST') else "0.0.0.0", 
                port=int(Config.API_PORT) if hasattr(Config, 'API_PORT') else 8000, 
                log_level=getattr(Config, 'LOG_LEVEL', 'info').lower())
    # The log_level here for uvicorn might be redundant if configure_logging() sets root logger level.
    # Uvicorn's access logs are separate.