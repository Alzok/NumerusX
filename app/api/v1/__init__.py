"""
API v1 module for NumerusX.
Contains all version 1 endpoints.
"""

from fastapi import APIRouter
from . import (
    auth_routes,
    bot_routes, 
    config_routes,
    trades_routes,
    portfolio_routes,
    ai_decisions_routes,
    system_routes
)

# Main router for API v1
api_router = APIRouter(prefix="/api/v1")

# Include all route modules
api_router.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(bot_routes.router, prefix="/bot", tags=["Bot Control"])
api_router.include_router(config_routes.router, prefix="/config", tags=["Configuration"])
api_router.include_router(trades_routes.router, prefix="/trades", tags=["Trading"])
api_router.include_router(portfolio_routes.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(ai_decisions_routes.router, prefix="/ai", tags=["AI Decisions"])
api_router.include_router(system_routes.router, prefix="/system", tags=["System"])