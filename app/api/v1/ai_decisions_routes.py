"""
AI Decisions routes for API v1.
Handles AI agent decisions, reasoning, and analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from .auth_routes import verify_token, TokenData

router = APIRouter()
logger = logging.getLogger(__name__)


class AIDecision(BaseModel):
    id: str
    timestamp: datetime
    pair: str
    decision: str  # BUY, SELL, HOLD
    confidence: float
    amount_usd: Optional[float] = None
    reasoning: str
    market_conditions: Dict[str, Any]
    signals_used: List[Dict[str, Any]]
    execution_status: str  # PENDING, EXECUTED, CANCELLED, FAILED


class AIAnalysis(BaseModel):
    timestamp: datetime
    market_regime: str
    sentiment_score: float
    key_factors: List[str]
    risk_assessment: str
    recommendations: List[str]


@router.get("/history", response_model=List[AIDecision])
async def get_ai_decisions_history(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    decision_type: Optional[str] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    token_data: TokenData = Depends(verify_token)
):
    """Get AI decision history with filtering options."""
    try:
        # Mock AI decisions data
        mock_decisions = [
            AIDecision(
                id="ai_001",
                timestamp=datetime.utcnow() - timedelta(hours=1),
                pair="SOL/USDC",
                decision="BUY",
                confidence=0.87,
                amount_usd=500.0,
                reasoning="Strong momentum signals detected with bullish market regime. RSI oversold condition combined with volume spike indicates good entry point.",
                market_conditions={
                    "price": 57.65,
                    "volume_24h": 1250000,
                    "volatility": 0.089,
                    "trend": "UPWARD"
                },
                signals_used=[
                    {"source": "momentum_strategy", "signal": "BUY", "confidence": 0.92},
                    {"source": "rsi_strategy", "signal": "BUY", "confidence": 0.78}
                ],
                execution_status="EXECUTED"
            ),
            AIDecision(
                id="ai_002",
                timestamp=datetime.utcnow() - timedelta(hours=3),
                pair="SOL/USDC",
                decision="HOLD",
                confidence=0.65,
                amount_usd=None,
                reasoning="Mixed signals from different strategies. Market showing sideways movement with unclear direction. Waiting for clearer confirmation.",
                market_conditions={
                    "price": 56.89,
                    "volume_24h": 890000,
                    "volatility": 0.056,
                    "trend": "SIDEWAYS"
                },
                signals_used=[
                    {"source": "momentum_strategy", "signal": "NEUTRAL", "confidence": 0.55},
                    {"source": "mean_reversion", "signal": "SELL", "confidence": 0.62}
                ],
                execution_status="EXECUTED"
            )
        ]
        
        # Apply filters
        filtered_decisions = mock_decisions
        if decision_type:
            filtered_decisions = [d for d in filtered_decisions if d.decision == decision_type]
        if start_date:
            filtered_decisions = [d for d in filtered_decisions if d.timestamp >= start_date]
        if end_date:
            filtered_decisions = [d for d in filtered_decisions if d.timestamp <= end_date]
        
        # Apply pagination
        paginated_decisions = filtered_decisions[offset:offset + limit]
        
        return paginated_decisions
        
    except Exception as e:
        logger.error(f"Error getting AI decisions history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI decisions history: {str(e)}"
        )


@router.get("/latest")
async def get_latest_ai_decision(token_data: TokenData = Depends(verify_token)):
    """Get the latest AI decision."""
    try:
        # Mock latest decision
        latest_decision = {
            "id": "ai_latest",
            "timestamp": datetime.utcnow() - timedelta(minutes=5),
            "pair": "SOL/USDC",
            "decision": "BUY",
            "confidence": 0.87,
            "amount_usd": 500.0,
            "reasoning": "Strong momentum signals detected with bullish market regime.",
            "execution_status": "PENDING",
            "estimated_execution_time": "2-3 minutes"
        }
        
        return latest_decision
        
    except Exception as e:
        logger.error(f"Error getting latest AI decision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest AI decision: {str(e)}"
        )


@router.get("/analysis", response_model=AIAnalysis)
async def get_current_ai_analysis(token_data: TokenData = Depends(verify_token)):
    """Get current AI market analysis."""
    try:
        # Mock AI analysis
        analysis = AIAnalysis(
            timestamp=datetime.utcnow(),
            market_regime="BULLISH",
            sentiment_score=0.72,
            key_factors=[
                "Strong trading volume in SOL",
                "Positive momentum indicators",
                "Market showing upward trend",
                "Low volatility environment"
            ],
            risk_assessment="MODERATE",
            recommendations=[
                "Consider increasing SOL exposure",
                "Monitor for potential breakout above $60",
                "Set stop-loss at $52 level"
            ]
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI analysis: {str(e)}"
        )


@router.get("/stats")
async def get_ai_performance_stats(
    period_days: int = Query(default=30, ge=1, le=365),
    token_data: TokenData = Depends(verify_token)
):
    """Get AI agent performance statistics."""
    try:
        # Mock AI performance stats
        stats = {
            "period_days": period_days,
            "total_decisions": 145,
            "buy_decisions": 58,
            "sell_decisions": 42,
            "hold_decisions": 45,
            "avg_confidence": 0.78,
            "execution_rate": 0.92,
            "successful_trades": 89,
            "failed_trades": 12,
            "success_rate": 0.88,
            "avg_profit_per_trade": 23.45,
            "best_decision_profit": 156.78,
            "worst_decision_loss": -45.32,
            "decision_accuracy": 0.85,
            "confidence_calibration": 0.82,
            "daily_decisions": [
                {
                    "date": (datetime.utcnow() - timedelta(days=i)).date().isoformat(),
                    "decisions": max(0, 5 - (i % 3)),
                    "avg_confidence": 0.75 + (i % 7 * 0.02),
                    "successful": max(0, 4 - (i % 4))
                }
                for i in range(min(period_days, 30))
            ]
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting AI performance stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI performance stats: {str(e)}"
        )


@router.get("/{decision_id}")
async def get_ai_decision_details(
    decision_id: str,
    token_data: TokenData = Depends(verify_token)
):
    """Get detailed information about a specific AI decision."""
    try:
        # Mock decision details
        decision_details = {
            "id": decision_id,
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "pair": "SOL/USDC",
            "decision": "BUY",
            "confidence": 0.87,
            "amount_usd": 500.0,
            "reasoning": "Strong momentum signals detected with bullish market regime. RSI oversold condition combined with volume spike indicates good entry point.",
            "execution_status": "EXECUTED",
            "market_conditions_at_decision": {
                "price": 57.65,
                "volume_24h": 1250000,
                "volatility": 0.089,
                "trend": "UPWARD",
                "support_level": 55.20,
                "resistance_level": 59.80
            },
            "signals_analyzed": [
                {
                    "source": "momentum_strategy",
                    "signal": "BUY",
                    "confidence": 0.92,
                    "indicators": {
                        "rsi": 28.5,
                        "macd": 0.45,
                        "volume_ratio": 1.78
                    }
                },
                {
                    "source": "mean_reversion",
                    "signal": "NEUTRAL",
                    "confidence": 0.51,
                    "indicators": {
                        "bb_position": 0.25,
                        "price_deviation": -0.08
                    }
                }
            ],
            "risk_factors_considered": [
                "Market volatility within acceptable range",
                "Sufficient liquidity for execution",
                "Position size within risk limits"
            ],
            "execution_details": {
                "executed_at": (datetime.utcnow() - timedelta(minutes=118)).isoformat(),
                "executed_price": 57.72,
                "slippage": 0.12,
                "execution_time_ms": 1456
            },
            "outcome": {
                "current_pnl_usd": 12.34,
                "current_pnl_percent": 2.14,
                "max_profit_usd": 23.45,
                "max_loss_usd": -5.67
            }
        }
        
        return decision_details
        
    except Exception as e:
        logger.error(f"Error getting AI decision details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI decision details: {str(e)}"
        )


@router.get("/model/info")
async def get_ai_model_info(token_data: TokenData = Depends(verify_token)):
    """Get information about the AI model being used."""
    try:
        model_info = {
            "model_name": "Gemini 2.5 Flash Preview",
            "version": "05-20",
            "last_updated": "2024-05-20",
            "capabilities": [
                "Market analysis",
                "Signal interpretation",
                "Risk assessment",
                "Trading decision making"
            ],
            "training_data": {
                "last_training_date": "2024-04-15",
                "data_sources": ["Market data", "Technical indicators", "News sentiment"],
                "training_period": "2020-2024"
            },
            "performance_metrics": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85
            },
            "limitations": [
                "Decisions based on historical patterns",
                "Cannot predict black swan events",
                "Performance may vary in extreme market conditions"
            ]
        }
        
        return model_info
        
    except Exception as e:
        logger.error(f"Error getting AI model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI model info: {str(e)}"
        )