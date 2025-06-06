"""
Portfolio routes for API v1.
Handles portfolio information, balances, and performance.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from .auth_routes import verify_token, TokenData

router = APIRouter()
logger = logging.getLogger(__name__)


class TokenBalance(BaseModel):
    symbol: str
    balance: float
    value_usd: float
    price_usd: float
    change_24h_percent: float


class PortfolioOverview(BaseModel):
    total_value_usd: float
    total_pnl_usd: float
    total_pnl_percent: float
    daily_pnl_usd: float
    available_balance_usd: float
    tokens: List[TokenBalance]


class PerformanceMetrics(BaseModel):
    sharpe_ratio: float
    max_drawdown_percent: float
    win_rate: float
    total_trades: int
    avg_trade_size_usd: float
    best_trade_usd: float
    worst_trade_usd: float


@router.get("/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(token_data: TokenData = Depends(verify_token)):
    """Get portfolio overview with current balances and performance."""
    try:
        # Mock portfolio data - in production, this would query real balances
        mock_tokens = [
            TokenBalance(
                symbol="SOL",
                balance=15.5,
                value_usd=892.35,
                price_usd=57.57,
                change_24h_percent=2.34
            ),
            TokenBalance(
                symbol="USDC",
                balance=1250.50,
                value_usd=1250.50,
                price_usd=1.00,
                change_24h_percent=0.0
            ),
            TokenBalance(
                symbol="BONK",
                balance=1000000,
                value_usd=234.67,
                price_usd=0.00023467,
                change_24h_percent=-5.67
            )
        ]
        
        total_value = sum(token.value_usd for token in mock_tokens)
        
        portfolio = PortfolioOverview(
            total_value_usd=total_value,
            total_pnl_usd=377.52,
            total_pnl_percent=18.94,
            daily_pnl_usd=45.23,
            available_balance_usd=1250.50,  # USDC balance
            tokens=mock_tokens
        )
        
        return portfolio
        
    except Exception as e:
        logger.error(f"Error getting portfolio overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio overview: {str(e)}"
        )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(token_data: TokenData = Depends(verify_token)):
    """Get portfolio performance metrics."""
    try:
        # Mock performance data
        metrics = PerformanceMetrics(
            sharpe_ratio=1.87,
            max_drawdown_percent=8.45,
            win_rate=0.72,
            total_trades=156,
            avg_trade_size_usd=423.67,
            best_trade_usd=234.56,
            worst_trade_usd=-89.34
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/history")
async def get_portfolio_history(
    days: int = 30,
    token_data: TokenData = Depends(verify_token)
):
    """Get portfolio value history."""
    try:
        # Mock historical data
        history = []
        base_value = 2000.0
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - i - 1)
            # Simulate some volatility
            daily_change = (i * 2.5) + (i % 7 * 10) - 50
            value = base_value + daily_change
            
            history.append({
                "date": date.date().isoformat(),
                "total_value_usd": value,
                "daily_pnl_usd": daily_change * 0.1,
                "daily_pnl_percent": (daily_change / base_value) * 100
            })
        
        return {
            "period_days": days,
            "start_value_usd": history[0]["total_value_usd"] if history else 0,
            "end_value_usd": history[-1]["total_value_usd"] if history else 0,
            "total_return_percent": ((history[-1]["total_value_usd"] - history[0]["total_value_usd"]) / history[0]["total_value_usd"] * 100) if history else 0,
            "data": history
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio history: {str(e)}"
        )


@router.get("/allocations")
async def get_portfolio_allocations(token_data: TokenData = Depends(verify_token)):
    """Get portfolio allocation breakdown."""
    try:
        # Mock allocation data
        allocations = [
            {
                "symbol": "SOL",
                "percentage": 41.2,
                "value_usd": 892.35,
                "target_percentage": 40.0,
                "deviation": 1.2
            },
            {
                "symbol": "USDC",
                "percentage": 57.8,
                "value_usd": 1250.50,
                "target_percentage": 50.0,
                "deviation": 7.8
            },
            {
                "symbol": "BONK",
                "percentage": 1.0,
                "value_usd": 234.67,
                "target_percentage": 10.0,
                "deviation": -9.0
            }
        ]
        
        return {
            "allocations": allocations,
            "rebalance_suggested": any(abs(alloc["deviation"]) > 5 for alloc in allocations),
            "total_value_usd": sum(alloc["value_usd"] for alloc in allocations)
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio allocations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio allocations: {str(e)}"
        )


@router.get("/balances")
async def get_wallet_balances(token_data: TokenData = Depends(verify_token)):
    """Get detailed wallet balances."""
    try:
        # Mock wallet balances
        balances = {
            "wallet_address": "DemoWallet123...456",
            "last_updated": datetime.utcnow().isoformat(),
            "tokens": [
                {
                    "mint": "So11111111111111111111111111111111111111112",
                    "symbol": "SOL",
                    "decimals": 9,
                    "balance": 15.5,
                    "ui_amount": "15.5",
                    "value_usd": 892.35,
                    "price_usd": 57.57
                },
                {
                    "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "symbol": "USDC",
                    "decimals": 6,
                    "balance": 1250500000,
                    "ui_amount": "1250.5",
                    "value_usd": 1250.50,
                    "price_usd": 1.00
                }
            ],
            "total_value_usd": 2142.85
        }
        
        return balances
        
    except Exception as e:
        logger.error(f"Error getting wallet balances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wallet balances: {str(e)}"
        )