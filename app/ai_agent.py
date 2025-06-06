import logging
from typing import Dict, Any, Optional, Literal, List
import json # Added for logging and example
import time # Added for example
import asyncio # Added for async decide_trade

from app.config import get_config
# Placeholder for other necessary imports, e.g., data providers, engines
# from app.market.market_data import MarketDataProvider
# from app.prediction_engine import PredictionEngine
# from app.risk_manager import RiskManager
# from app.security.security import SecurityChecker
# from app.portfolio_manager import PortfolioManager
# from app.strategy_framework import BaseStrategy
from app.ai_agent_package.gemini_client import GeminiClient # Import GeminiClient
from app.models.ai_inputs import AggregatedInputs, SignalSourceInput # Import AggregatedInputs, SignalSourceInput
from pydantic import BaseModel, ValidationError, confloat, constr # Added BaseModel, ValidationError, confloat, constr

logger = logging.getLogger(__name__)

# Pydantic model for TradeDecision (Task 3.3 from todo/02-todo-ai-api-gemini.md)
class TradeDecisionModel(BaseModel):
    decision: Literal["BUY", "SELL", "HOLD"]
    token_pair: str # e.g., "SOL/USDC"
    amount_usd: Optional[confloat(gt=0)] = None
    confidence: confloat(ge=0, le=1)
    stop_loss_price: Optional[confloat(gt=0)] = None
    take_profit_price: Optional[confloat(gt=0)] = None
    reasoning: constr(min_length=5, max_length=500) # Adjusted min_length

    # Ensure amount_usd is present for BUY/SELL decisions
    # This can be done with a root_validator if needed, or handled in parsing logic.
    # For now, we'll assume the LLM is prompted to provide it for BUY/SELL.

class AIAgent:
    """
    Agent IA Décisionnel Central pour NumerusX.
    Ce composant est responsable de la prise de décision finale de trading en agrégeant
    les informations de divers modules (données de marché, prédictions, signaux de stratégie,
    risques, sécurité, portefeuille).
    """

    def __init__(self, config: Config):
        """
        Initialise l'Agent IA.

        Args:
            config: L'objet de configuration global.
        """
        self.config = config
        self.gemini_client = GeminiClient(config=self.config)
        # self.market_data_provider: Optional[MarketDataProvider] = None # Will be set by DexBot or passed in decide_trade
        # self.prediction_engine: Optional[PredictionEngine] = None
        # self.risk_manager: Optional[RiskManager] = None
        # self.security_checker: Optional[SecurityChecker] = None
        # self.portfolio_manager: Optional[PortfolioManager] = None
        # self.strategies: Dict[str, BaseStrategy] = {} # To hold available strategy signal generators

        logger.info("AIAgent initialisé avec GeminiClient.")

    async def decide_trade(self, aggregated_inputs_model: AggregatedInputs) -> Dict[str, Any]:
        """
        Prend une décision de trading basée sur les inputs agrégés en utilisant Gemini.
        Retourne un dictionnaire structuré compatible avec TradeExecutor.execute_agent_order
        """
        # Default 'HOLD' decision in case of errors
        default_hold_decision = {
            "decision": "HOLD",
            "token_pair": f"{aggregated_inputs_model.target_pair.symbol if aggregated_inputs_model.target_pair else 'N/A'}",
            "amount_usd": None,
            "confidence": 0.1,
            "stop_loss_price": None,
            "take_profit_price": None,
            "reasoning": "Default HOLD due to an internal error or failure in AI decision process."
        }

        # Validate aggregated_inputs_model (already an instance, Pydantic did its job on creation)
        # For extra safety or if it were a dict, we'd do:
        # try:
        #     validated_inputs = AggregatedInputs(**aggregated_inputs_dict)
        # except ValidationError as e:
        #     logger.error(f"Validation error for aggregated_inputs: {e.errors()}", exc_info=True)
        #     default_hold_decision['reasoning'] = f"AIAgent internal error: Invalid aggregated inputs. Details: {e.errors()}"
        #     return default_hold_decision

        # 1. Prepare prompt for Gemini
        prompt_for_gemini: Optional[str] = None
        try:
            # Log a snippet of inputs (or full if debug enabled later)
            inputs_for_log_dict = aggregated_inputs_model.model_dump(exclude_none=True, exclude={'market_data': {'recent_ohlcv_1h'}}) # Example exclusion for brevity
            inputs_snippet_log = json.dumps(inputs_for_log_dict, default=str, indent=2)

            if len(inputs_snippet_log) > (self.config.LOG_MAX_MSG_LENGTH // 2): # Use a config for max log length
                inputs_snippet_log = inputs_snippet_log[:(self.config.LOG_MAX_MSG_LENGTH // 2)] + "... (inputs truncated for log)"
            logger.debug(f"AIAgent.decide_trade called with inputs (snippet): {inputs_snippet_log}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la préparation du snippet de log des inputs pour AIAgent: {e}", exc_info=True)
            # Continue, as logging failure here isn't critical for decision making

        try:
            prompt_for_gemini = self._construct_gemini_prompt(aggregated_inputs_model)
            if self.get_config().app.debug_PROMPTS: # Instruction 5 from review
                logger.debug(f"Full prompt for Gemini:\\n{prompt_for_gemini}")
            elif len(prompt_for_gemini) > 2000 : # Log snippet if too long and not debug
                 logger.debug(f"Prompt for Gemini (snippet):\n{prompt_for_gemini[:1000]}\\n...\\n{prompt_for_gemini[-1000:]}")

        except Exception as e:
            logger.error(f"Erreur lors de la construction du prompt pour Gemini: {e}", exc_info=True)
            default_hold_decision['reasoning'] = f"AIAgent internal error: Could not construct prompt for AI. Details: {str(e)}"
            return default_hold_decision
        
        # Determine max_output_tokens based on config (Instruction 6 from review)
        max_output_tokens = self.config.GEMINI_MAX_TOKENS_OUTPUT

        # 2. Call GeminiClient
        gemini_response = await self.gemini_client.get_decision(prompt_for_gemini, max_output_tokens=max_output_tokens)

        # 3. Handle GeminiClient response
        if not gemini_response['success']:
            logger.error(f"GeminiClient error: {gemini_response['error']}")
            default_hold_decision['reasoning'] = f"AIAgent (Gemini API) failed to provide a decision. Error: {gemini_response['error']}"
            return default_hold_decision

        # 4. Parse and validate Gemini's text response (Task 3.3 with Pydantic)
        try:
            raw_decision_text = gemini_response['decision_text']
            # Attempt to extract JSON if it's embedded in other text (common for some models)
            # Basic extraction: look for '{' and '}'
            json_start_index = raw_decision_text.find('{')
            json_end_index = raw_decision_text.rfind('}')
            
            if json_start_index != -1 and json_end_index != -1 and json_end_index > json_start_index:
                json_str_to_parse = raw_decision_text[json_start_index : json_end_index + 1]
            else:
                json_str_to_parse = raw_decision_text # Assume it's a direct JSON string

            parsed_json_data = json.loads(json_str_to_parse)
            
            # Validate with Pydantic model (Instruction 3 from review)
            validated_decision = TradeDecisionModel(**parsed_json_data)
            
            # Check if BUY/SELL has amount_usd
            if validated_decision.decision in ["BUY", "SELL"] and validated_decision.amount_usd is None:
                logger.warning(f"Gemini returned {validated_decision.decision} without amount_usd. Invalidating. Raw: {parsed_json_data}")
                raise ValidationError("BUY/SELL decision must include amount_usd.", TradeDecisionModel)

            logger.info(f"Validated AI Decision: {validated_decision.model_dump_json(indent=2)}")
            
            # Convert Pydantic model to dict for TradeExecutor
            # This is already the format expected by execute_agent_order
            final_decision_for_executor = validated_decision.model_dump()

        except json.JSONDecodeError as e:
            logger.error(f"Cannot parse JSON response from Gemini: '{raw_decision_text}'. Error: {e}", exc_info=True)
            default_hold_decision['reasoning'] = f"AIAgent (Gemini) returned a non-JSON response. Response: {raw_decision_text[:200]}..."
            return default_hold_decision
        except ValidationError as e:
            logger.error(f"Gemini response failed Pydantic validation: '{parsed_json_data if 'parsed_json_data' in locals() else raw_decision_text}'. Errors: {e.errors()}", exc_info=True)
            # Log the full text that caused validation error for debugging
            if 'raw_decision_text' in locals():
                 logger.debug(f"Raw text from Gemini causing validation error: {raw_decision_text}")
            default_hold_decision['reasoning'] = f"AIAgent (Gemini) response failed validation. Details: {e.errors()}"
            return default_hold_decision
        except Exception as e:
            logger.error(f"Unexpected error processing Gemini response: {e}", exc_info=True)
            default_hold_decision['reasoning'] = f"AIAgent internal error processing AI response. Details: {str(e)}"
            return default_hold_decision

        logger.info(f"AIAgent final decision for TradeExecutor: {final_decision_for_executor}")
        return final_decision_for_executor

    def _summarize_ohlcv(self, ohlcv_list: List[Dict], max_candles: int = 12) -> List[Dict]:
        """Summarizes OHLCV data to include max_candles most recent ones."""
        if len(ohlcv_list) > max_candles:
            logger.debug(f"Summarizing OHLCV data from {len(ohlcv_list)} to {max_candles} candles.")
            return ohlcv_list[-max_candles:]
        return ohlcv_list

    def _summarize_signal_sources(self, signal_sources: List[SignalSourceInput], max_signals: int = 3) -> List[SignalSourceInput]:
        """Summarizes signal sources, prioritizing higher confidence and non-neutral signals."""
        if not signal_sources or len(signal_sources) <= max_signals:
            return signal_sources

        # Sort by confidence (desc) and then by whether it's neutral (False first)
        sorted_signals = sorted(
            signal_sources, 
            key=lambda s: (s.signal not in ["NEUTRAL", "HOLD"], s.confidence or 0), 
            reverse=True
        )
        logger.debug(f"Summarizing signal sources from {len(signal_sources)} to {max_signals} based on confidence/type.")
        return sorted_signals[:max_signals]

    def _construct_gemini_prompt(self, aggregated_inputs_model: AggregatedInputs) -> str:
        """
        Constructs the full prompt for Gemini based on aggregated_inputs.
        Includes token optimization strategies.
        (Corresponds to todo/02-todo-ai-api-gemini.md Tâche 3.2 & 3.2.5)
        """
        current_pair_str = "N/A"
        if aggregated_inputs_model.target_pair:
            current_pair_str = aggregated_inputs_model.target_pair.symbol

        # Create a mutable copy for summarization
        summarized_inputs_dict = aggregated_inputs_model.model_dump(exclude_none=True)

        # Summarize market_data.recent_ohlcv_1h
        if summarized_inputs_dict.get('market_data') and summarized_inputs_dict['market_data'].get('recent_ohlcv_1h'):
            original_ohlcv = summarized_inputs_dict['market_data']['recent_ohlcv_1h']
            summarized_ohlcv = self._summarize_ohlcv(original_ohlcv, max_candles=self.config.GEMINI_PROMPT_MAX_OHLCV_CANDLES)
            summarized_inputs_dict['market_data']['recent_ohlcv_1h'] = summarized_ohlcv

        # Summarize signal_sources
        if summarized_inputs_dict.get('signal_sources'):
            original_signals = [SignalSourceInput(**s) for s in summarized_inputs_dict['signal_sources']]
            summarized_signals = self._summarize_signal_sources(original_signals, max_signals=self.config.GEMINI_PROMPT_MAX_SIGNAL_SOURCES)
            summarized_inputs_dict['signal_sources'] = [s.model_dump() for s in summarized_signals]
        
        # TODO: Add more summarizations for other potentially verbose fields if necessary
        # e.g., long reasoning snippets in signals, news summaries in sentiment_analysis, etc.

        try:
            prompt_payload_json = json.dumps(summarized_inputs_dict, default=str, indent=2)
        except Exception as e:
            logger.error(f"Error serializing summarized AggregatedInputs for prompt construction: {e}", exc_info=True)
            raise ValueError(f"Could not serialize summarized AggregatedInputs for Gemini prompt: {e}")

        # Estimate token count (very rough estimate, actual tokenization is complex)
        # A simple proxy: character count / 4 (average characters per token)
        estimated_tokens = len(prompt_payload_json) // 4 
        if estimated_tokens > self.config.GEMINI_MAX_TOKENS_INPUT * 0.9: # If > 90% of limit
            logger.warning(
                f"Estimated prompt token count ({estimated_tokens}) is high, close to limit ({self.config.GEMINI_MAX_TOKENS_INPUT}). "
                f"Consider more aggressive summarization. Payload length: {len(prompt_payload_json)} chars."
            )
        elif estimated_tokens > self.config.GEMINI_MAX_TOKENS_INPUT:
            logger.error(
                f"Estimated prompt token count ({estimated_tokens}) EXCEEDS limit ({self.config.GEMINI_MAX_TOKENS_INPUT}). "
                f"Prompt will likely be rejected. Payload length: {len(prompt_payload_json)} chars."
            )
            # In a production system, we might truncate more aggressively here or raise an error to prevent API call
            # For now, just log error.

        prompt = f"""ROLE: NumerusX Solana Trading Agent (using {self.config.GEMINI_MODEL_NAME} model).
Analyze the following data for {current_pair_str} and provide a trading decision.

DATA:
{prompt_payload_json}

INSTRUCTIONS:
Based ONLY on the provided data, decide to BUY, SELL, or HOLD {current_pair_str}.
If BUY or SELL:
  - Specify amount_usd to trade (consider risk parameters and available capital).
  - Suggest stop_loss_price and take_profit_price.
Output your decision and reasoning STRICTLY in the following JSON format:
{{
  "decision": "BUY" | "SELL" | "HOLD",
  "token_pair": "{current_pair_str}",
  "amount_usd": float | null,
  "confidence": float,
  "stop_loss_price": float | null,
  "take_profit_price": float | null,
  "reasoning": "concise explanation based on synthesized data points."
}}
Prioritize capital preservation. If data is conflicting or insufficient for a high-confidence trade, prefer HOLD.
Be concise in your reasoning. Max 2-3 sentences.
Ensure your output strictly follows the JSON format specified, with no extra text before or after the JSON block.
"""
        return prompt

    # D'autres méthodes pourraient être ajoutées ici pour:
    # - Le chargement/entraînement de modèles spécifiques à l'agent.
    # - Des logiques d'adaptation ou d'apprentissage.
    # - Des fonctions utilitaires pour l'analyse des inputs.

async def main_test_agent():
    class MockConfig(Config):
        def __init__(self):
            super().__init__() # Initialize base Config to load .env etc.
            # Override specific values for testing if needed
            self.GOOGLE_API_KEY = self.get_env_variable("GOOGLE_API_KEY_TEST", self.GOOGLE_API_KEY) # Example of override
            self.GEMINI_MODEL_NAME = "gemini-1.5-flash-latest" # Use a known model for testing
            self.DEBUG_PROMPTS = True
            self.LOG_MAX_MSG_LENGTH = 2048


    mock_config = Mockget_config()
    ai_agent = AIAgent(config=mock_config)

    # Construct a sample AggregatedInputs object for testing
    # This would normally be built by DexBot
    from datetime import datetime
    from app.models.ai_inputs import (
        TargetPairInfo, MarketDataInput, SignalSourceInput, PredictionEngineInput,
        RiskManagerInput, PortfolioManagerInput, SecurityCheckerInput, KeySupportResistance,
        PricePrediction, SentimentAnalysis
    )
    
    sample_aggregated_inputs = AggregatedInputs(
        request_id="test-req-001",
        timestamp_utc=datetime.utcnow(),
        target_pair=TargetPairInfo(symbol="SOL/USDC", input_mint="So11111111111111111111111111111111111111112", output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
        market_data=MarketDataInput(
            current_price=170.50,
            recent_ohlcv_1h=[{"t": int(time.time()) - 3600, "o": 169.0, "h": 171.0, "l": 168.5, "c": 170.5, "v": 1000}],
            liquidity_depth_usd=10000000,
            recent_trend_1h="UPWARD",
            key_support_resistance=KeySupportResistance(support_1=165.0, resistance_1=175.0),
            trading_volume_24h_usd=500000000
        ),
        signal_sources=[
            SignalSourceInput(source_name="TestStrategy", signal="BUY", confidence=0.7, reasoning_snippet="Test signal shows buy.")
        ],
        prediction_engine_outputs=PredictionEngineInput(
            price_prediction_4h=PricePrediction(target_price_min=172.0, target_price_max=178.0, confidence=0.65),
            market_regime_1h="VOLATILE_TRENDING",
            sentiment_analysis=SentimentAnalysis(overall_score=0.5, dominant_sentiment="NEUTRAL")
        ),
        risk_manager_inputs=RiskManagerInput(
            max_exposure_per_trade_percentage=0.01, # 1%
            current_portfolio_value_usd=5000.0,
            available_capital_usdc=2000.0,
            max_trade_size_usd=50.0 # 1% of 5000
        ),
        portfolio_manager_inputs=PortfolioManagerInput(
            current_positions=[]
        ),
        security_checker_inputs=SecurityCheckerInput(
            target_token_symbol="SOL",
            target_token_security_score=0.85
        )
    )

    print("\n--- Testing AIAgent with Gemini ---")
    if not mock_config.GOOGLE_API_KEY or "YOUR_API_KEY" in mock_config.GOOGLE_API_KEY:
        print("GOOGLE_API_KEY not found or is a placeholder in .env or config. Skipping live API call.")
        print("Please set a valid GOOGLE_API_KEY (e.g., GOOGLE_API_KEY_TEST in .env) to run this test.")
        # Simulate a HOLD response if API key is missing
        decision = {
            "decision": "HOLD", "token_pair": "SOL/USDC", "amount_usd": None, 
            "confidence": 0.1, "reasoning": "Skipped live API call due to missing API key."
        }
    else:
        decision = await ai_agent.decide_trade(sample_aggregated_inputs)
    
    print("\n--- AI Agent Decision ---")
    print(json.dumps(decision, indent=2))
    print("------------------------")

if __name__ == "__main__":
    # Setup basic logging for the test
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main_test_agent())

    # Example of how an encrypted value from config might be used by the agent if needed
    # (though API keys are usually used by data providers, not directly by the agent core logic)
    # if mock_get_config().jupiter.api_key:
    #     logger.info(f"Agent has access to JUPITER_API_KEY (example): {mock_get_config().jupiter.api_key[:5]}...")
    # else:
    #     logger.warning("JUPITER_API_KEY not available to agent in this example.") 