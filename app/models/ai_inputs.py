# app/models/ai_inputs.py
# Ce fichier contiendra les modèles Pydantic pour les inputs de l'AIAgent.

from typing import List, Optional, Dict, Any, Union, Tuple # Ajout de Tuple
from pydantic import BaseModel, confloat, constr, conint, Field # Ajout de Field
from datetime import datetime

# --- Modèles de base --- #

class OHLCV(BaseModel):
    t: int # Timestamp
    o: float
    h: float
    l: float
    c: float
    v: float

class KeySupportResistance(BaseModel):
    support_1: Optional[float] = None
    resistance_1: Optional[float] = None
    support_2: Optional[float] = None
    resistance_2: Optional[float] = None

# --- Inputs spécifiques par source --- #

class MarketDataInput(BaseModel):
    current_price: Optional[float] = None
    recent_ohlcv_1h: Optional[List[OHLCV]] = None
    liquidity_depth_usd: Optional[float] = None
    recent_trend_1h: Optional[constr(max_length=50)] = None # Ex: "UPWARD", "DOWNWARD", "SIDEWAYS"
    key_support_resistance: Optional[KeySupportResistance] = None
    volatility_1h_atr_percentage: Optional[confloat(ge=0)] = None
    trading_volume_24h_usd: Optional[float] = None # Ajouté pour correspondre au prompt Gemini

class SignalSourceInput(BaseModel):
    source_name: constr(max_length=100)
    signal: constr(max_length=50) # Ex: "STRONG_BUY", "NEUTRAL", "SELL"
    confidence: Optional[confloat(ge=0, le=1)] = None
    indicators: Optional[Dict[str, Any]] = None # Ex: {"rsi_14": 70, "macd_signal_strength": 0.8}
    reasoning_snippet: Optional[constr(max_length=255)] = None

class PricePrediction(BaseModel):
    target_price_min: Optional[float] = None
    target_price_max: Optional[float] = None
    prediction_period_hours: Optional[int] = None
    confidence: Optional[confloat(ge=0, le=1)] = None
    model_name: Optional[constr(max_length=100)] = None

class SentimentAnalysis(BaseModel):
    overall_score: Optional[confloat(ge=-1, le=1)] = None
    dominant_sentiment: Optional[constr(max_length=50)] = None # Ex: "POSITIVE", "NEGATIVE", "NEUTRAL"
    source_summary: Optional[constr(max_length=255)] = None
    volume_of_mentions: Optional[constr(max_length=50)] = None # Ex: "LOW", "MEDIUM", "HIGH"

class PredictionEngineInput(BaseModel):
    price_prediction_4h: Optional[PricePrediction] = None
    market_regime_1h: Optional[constr(max_length=100)] = None # Ex: "VOLATILE_TRENDING"
    sentiment_analysis: Optional[SentimentAnalysis] = None

class RiskManagerInput(BaseModel):
    max_exposure_per_trade_percentage: Optional[confloat(ge=0, le=1)] = None
    current_portfolio_value_usd: Optional[float] = None
    available_capital_usdc: Optional[float] = None
    max_trade_size_usd: Optional[float] = None
    overall_portfolio_risk_level: Optional[constr(max_length=50)] = None # Ex: "LOW", "MODERATE"

class PortfolioPositionInput(BaseModel):
    symbol: constr(max_length=30)
    amount_tokens: float
    entry_price_usd: float
    current_price_usd: Optional[float] = None
    current_value_usd: Optional[float] = None
    unrealized_pnl_usd: Optional[float] = None
    unrealized_pnl_percentage: Optional[float] = None

class PortfolioManagerInput(BaseModel):
    current_positions: Optional[List[PortfolioPositionInput]] = None
    total_pnl_realized_24h_usd: Optional[float] = None
    # total_portfolio_value_usd est déjà dans RiskManagerInput, éviter redondance si possible
    # available_cash_usdc est déjà dans RiskManagerInput

class TokenSecurityRisk(BaseModel):
    risk_type: str
    severity: conint(ge=0, le=10)
    description: str
    metadata: Optional[Dict[str, Any]] = None

class SecurityCheckerInput(BaseModel):
    # Pour le token cible du trade potentiel (ex: SOL dans SOL/USDC)
    target_token_symbol: Optional[str] = None # e.g., "SOL"
    target_token_security_score: Optional[confloat(ge=0, le=1)] = None
    target_token_recent_security_alerts: Optional[List[TokenSecurityRisk]] = None
    # Si l'autre token est pertinent (ex: USDC), des infos pourraient aussi être ajoutées
    # quote_token_symbol: Optional[str] = None # e.g., "USDC"
    # quote_token_security_score: Optional[confloat(ge=0, le=1)] = None

class TargetPairInfo(BaseModel):
    symbol: constr(max_length=30) # Ex: "SOL/USDC"
    input_mint: Optional[constr(max_length=45)] = None
    output_mint: Optional[constr(max_length=45)] = None

# --- Modèle Agrégé --- #

class AggregatedInputs(BaseModel):
    request_id: str # Pour le suivi
    timestamp_utc: datetime
    target_pair: TargetPairInfo
    market_data: MarketDataInput
    signal_sources: List[SignalSourceInput] = Field(default_factory=list)
    prediction_engine_outputs: Optional[PredictionEngineInput] = None
    risk_manager_inputs: RiskManagerInput
    portfolio_manager_inputs: PortfolioManagerInput
    security_checker_inputs: Optional[SecurityCheckerInput] = None # Pour le token cible (ex: SOL)

    class Config:
        anystr_strip_whitespace = True
        validate_assignment = True # Valide les champs lors de l'assignation après l'initialisation

# Exemple d'utilisation (pourrait être dans un test ou une section __main__)
if __name__ == "__main__":
    sample_market_data = MarketDataInput(
        current_price=165.30,
        recent_ohlcv_1h=[
            OHLCV(t=1698397200, o=165.0, h=165.5, l=164.8, c=165.3, v=10000)
        ],
        liquidity_depth_usd=25000000,
        recent_trend_1h="UPWARD",
        key_support_resistance=KeySupportResistance(support_1=160.00, resistance_1=170.00),
        volatility_1h_atr_percentage=0.015,
        trading_volume_24h_usd=1.2e9
    )

    sample_signal = SignalSourceInput(
        source_name="MomentumStrategy_1h_RSI_MACD",
        signal="STRONG_BUY",
        confidence=0.85,
        indicators={"rsi_14": 68, "macd_signal_strength": 0.7},
        reasoning_snippet="RSI bullish, MACD crossover positive."
    )

    sample_predictions = PredictionEngineInput(
        price_prediction_4h=PricePrediction(
            target_price_min=168.00,
            target_price_max=172.00,
            prediction_period_hours=4,
            confidence=0.75,
            model_name="RandomForest_v2"
        ),
        market_regime_1h="VOLATILE_TRENDING",
        sentiment_analysis=SentimentAnalysis(
            overall_score=0.6,
            dominant_sentiment="POSITIVE",
            source_summary="Twitter positive, Reddit neutral",
            volume_of_mentions="HIGH"
        )
    )

    sample_risk = RiskManagerInput(
        max_exposure_per_trade_percentage=0.02,
        current_portfolio_value_usd=10000.00,
        available_capital_usdc=4000.00,
        max_trade_size_usd=200.00,
        overall_portfolio_risk_level="MODERATE"
    )

    sample_portfolio = PortfolioManagerInput(
        current_positions=[],
        total_pnl_realized_24h_usd=150.00
    )
    
    sample_security = SecurityCheckerInput(
        target_token_symbol="SOL",
        target_token_security_score=0.9,
        target_token_recent_security_alerts=[]
    )

    aggregated_data = AggregatedInputs(
        request_id="test-001",
        timestamp_utc=datetime.utcnow(),
        target_pair=TargetPairInfo(symbol="SOL/USDC"),
        market_data=sample_market_data,
        signal_sources=[sample_signal],
        prediction_engine_outputs=sample_predictions,
        risk_manager_inputs=sample_risk,
        portfolio_manager_inputs=sample_portfolio,
        security_checker_inputs=sample_security
    )

    print(aggregated_data.model_dump_json(indent=2)) 