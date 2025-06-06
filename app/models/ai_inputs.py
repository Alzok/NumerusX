"""
Pydantic models for AI Agent inputs.
Defines structured data models for aggregating all inputs to the AI trading agent.
"""

from pydantic import BaseModel, Field, confloat, constr
from datetime import datetime
from enum import Enum


class TrendDirection(str, Enum):
    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"
    SIDEWAYS = "SIDEWAYS"


class SignalType(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class MarketRegime(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class MarketDataInput(BaseModel):
    """Market data for the target trading pair."""
    current_price: float = Field(..., gt=0, description="Current price of the token")
    recent_ohlcv_1h: List[Dict[str, float]] = Field(
        ..., description="Recent OHLCV data for 1h periods"
    )
    liquidity_depth_usd: float = Field(
        ..., gt=0, description="Available liquidity depth in USD"
    )
    recent_trend_1h: TrendDirection = Field(
        ..., description="Recent 1h trend direction"
    )
    key_support_resistance: Dict[str, float] = Field(
        default_factory=dict, description="Key support and resistance levels"
    )
    volatility_1h_atr_percentage: float = Field(
        ..., ge=0, le=1, description="1h ATR volatility as percentage"
    )
    volume_24h_usd: float = Field(
        default=0, ge=0, description="24h trading volume in USD"
    )
    market_cap_usd: Optional[float] = Field(
        default=None, ge=0, description="Market cap in USD if available"
    )


class SignalSourceInput(BaseModel):
    """Signal from a trading strategy or indicator."""
    source_name: str = Field(..., description="Name of the signal source")
    signal: SignalType = Field(..., description="Trading signal type")
    confidence: confloat(ge=0, le=1) = Field(
        ..., description="Confidence level of the signal (0-1)"
    )
    indicators: Dict[str, Any] = Field(
        default_factory=dict, description="Technical indicators data"
    )
    reasoning_snippet: constr(max_length=200) = Field(
        ..., description="Brief reasoning for the signal"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Signal generation timestamp"
    )


class PredictionEngineInput(BaseModel):
    """Outputs from the prediction engine."""
    price_prediction_4h: Dict[str, float] = Field(
        ..., description="Price predictions for next 4 hours"
    )
    market_regime_1h: MarketRegime = Field(
        ..., description="Current market regime classification"
    )
    sentiment_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Sentiment analysis data"
    )
    confidence_score: confloat(ge=0, le=1) = Field(
        default=0.5, description="Overall prediction confidence"
    )
    key_factors: List[str] = Field(
        default_factory=list, description="Key factors influencing prediction"
    )


class RiskManagerInput(BaseModel):
    """Risk management constraints and parameters."""
    max_exposure_per_trade_percentage: float = Field(
        ..., gt=0, le=100, description="Max exposure per trade as percentage"
    )
    current_portfolio_value_usd: float = Field(
        ..., ge=0, description="Current total portfolio value in USD"
    )
    available_capital_usdc: float = Field(
        ..., ge=0, description="Available USDC capital for trading"
    )
    max_trade_size_usd: float = Field(
        ..., gt=0, description="Maximum allowed trade size in USD"
    )
    overall_portfolio_risk_level: RiskLevel = Field(
        ..., description="Current overall portfolio risk level"
    )
    daily_loss_limit_usd: float = Field(
        default=1000, gt=0, description="Daily loss limit in USD"
    )
    current_daily_pnl_usd: float = Field(
        default=0, description="Current daily PnL in USD"
    )
    stop_loss_percentage: float = Field(
        default=5.0, gt=0, le=100, description="Default stop loss percentage"
    )


class SecurityCheckerInput(BaseModel):
    """Security analysis for the target token."""
    token_security_score: confloat(ge=0, le=1) = Field(
        ..., description="Token security score (0-1, 1 being safest)"
    )
    recent_security_alerts: List[str] = Field(
        default_factory=list, description="Recent security alerts for this token"
    )
    liquidity_locked_percentage: Optional[float] = Field(
        default=None, ge=0, le=100, description="Percentage of liquidity locked"
    )
    contract_verified: bool = Field(
        default=False, description="Whether the contract is verified"
    )
    honeypot_risk: bool = Field(
        default=False, description="Whether there's honeypot risk detected"
    )


class PortfolioManagerInput(BaseModel):
    """Current portfolio state and management data."""
    current_positions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Current open positions"
    )
    total_pnl_realized_24h_usd: float = Field(
        default=0, description="Total realized PnL in last 24h (USD)"
    )
    total_pnl_unrealized_usd: float = Field(
        default=0, description="Total unrealized PnL (USD)"
    )
    position_count: int = Field(
        default=0, ge=0, description="Number of current positions"
    )
    portfolio_diversification_score: confloat(ge=0, le=1) = Field(
        default=0.5, description="Portfolio diversification score"
    )
    largest_position_percentage: float = Field(
        default=0, ge=0, le=100, description="Largest position as % of portfolio"
    )


class AggregatedInputs(BaseModel):
    """Complete aggregated inputs for the AI trading agent."""
    timestamp_utc: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of data aggregation"
    )
    target_pair: Dict[str, str] = Field(
        ..., description="Target trading pair information (base/quote)"
    )
    market_data: MarketDataInput = Field(
        ..., description="Market data for the target pair"
    )
    signal_sources: List[SignalSourceInput] = Field(
        default_factory=list, description="Signals from various trading strategies"
    )
    prediction_engine_outputs: Optional[PredictionEngineInput] = Field(
        default=None, description="Prediction engine outputs"
    )
    risk_manager_inputs: RiskManagerInput = Field(
        ..., description="Risk management constraints"
    )
    portfolio_manager_inputs: PortfolioManagerInput = Field(
        ..., description="Current portfolio state"
    )
    security_checker_inputs: Optional[SecurityCheckerInput] = Field(
        default=None, description="Security analysis for the target token"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        validate_assignment = True
        
    def to_compressed_dict(self) -> Dict[str, Any]:
        """Convert to a compressed dictionary suitable for AI prompt."""
        return {
            "timestamp": self.timestamp_utc.isoformat(),
            "pair": self.target_pair,
            "price": self.market_data.current_price,
            "trend": self.market_data.recent_trend_1h,
            "volatility": self.market_data.volatility_1h_atr_percentage,
            "liquidity": self.market_data.liquidity_depth_usd,
            "signals": [
                {
                    "source": s.source_name,
                    "signal": s.signal,
                    "confidence": s.confidence,
                    "reason": s.reasoning_snippet
                }
                for s in self.signal_sources
            ],
            "predictions": (
                {
                    "price_4h": self.prediction_engine_outputs.price_prediction_4h,
                    "regime": self.prediction_engine_outputs.market_regime_1h,
                    "confidence": self.prediction_engine_outputs.confidence_score
                }
                if self.prediction_engine_outputs
                else None
            ),
            "risk": {
                "max_exposure": self.risk_manager_inputs.max_exposure_per_trade_percentage,
                "available_capital": self.risk_manager_inputs.available_capital_usdc,
                "max_trade_size": self.risk_manager_inputs.max_trade_size_usd,
                "risk_level": self.risk_manager_inputs.overall_portfolio_risk_level,
                "daily_pnl": self.risk_manager_inputs.current_daily_pnl_usd
            },
            "portfolio": {
                "value": self.portfolio_manager_inputs.total_pnl_unrealized_usd,
                "pnl_24h": self.portfolio_manager_inputs.total_pnl_realized_24h_usd,
                "positions": self.portfolio_manager_inputs.position_count,
                "diversification": self.portfolio_manager_inputs.portfolio_diversification_score
            },
            "security": (
                {
                    "score": self.security_checker_inputs.token_security_score,
                    "alerts": len(self.security_checker_inputs.recent_security_alerts),
                    "verified": self.security_checker_inputs.contract_verified,
                    "honeypot": self.security_checker_inputs.honeypot_risk
                }
                if self.security_checker_inputs
                else None
            )
        }