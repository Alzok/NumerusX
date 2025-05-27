import logging
from typing import Dict, Any, Optional, Literal
import json # Added for logging and example
import time # Added for example
import asyncio # Added for async decide_trade

from app.config import Config
# Placeholder for other necessary imports, e.g., data providers, engines
# from app.market.market_data import MarketDataProvider
# from app.prediction_engine import PredictionEngine
# from app.risk_manager import RiskManager
# from app.security.security import SecurityChecker
# from app.portfolio_manager import PortfolioManager
# from app.strategy_framework import BaseStrategy
from app.ai_agent.gemini_client import GeminiClient # Import GeminiClient
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

    async def decide_trade(self, aggregated_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prend une décision de trading basée sur les inputs agrégés en utilisant Gemini.
        Retourne un dictionnaire structuré compatible avec TradeExecutor.execute_agent_order
        """
        # Default 'HOLD' decision in case of errors
        default_hold_decision = {
            "decision": "HOLD",
            "token_pair": aggregated_inputs.get("target_pair_info", {}).get("target_token_symbol", "N/A") + "/" + aggregated_inputs.get("target_pair_info", {}).get("base_token_symbol_for_pair", "N/A"),
            "amount_usd": None,
            "confidence": 0.1,
            "stop_loss_price": None,
            "take_profit_price": None,
            "reasoning": "Default HOLD due to an internal error or failure in AI decision process."
        }

        # 1. Prepare prompt for Gemini
        prompt_for_gemini: Optional[str] = None
        try:
            # Log a snippet of inputs (or full if debug enabled later)
            inputs_for_log = {k: v for k, v in aggregated_inputs.items() if k not in ['market_data']} # Avoid logging large market data
            inputs_snippet_log = json.dumps(inputs_for_log, default=str, indent=2)
            if len(inputs_snippet_log) > (self.config.LOG_MAX_MSG_LENGTH // 2): # Use a config for max log length
                inputs_snippet_log = inputs_snippet_log[:(self.config.LOG_MAX_MSG_LENGTH // 2)] + "... (inputs truncated for log)"
            logger.debug(f"AIAgent.decide_trade called with inputs (snippet): {inputs_snippet_log}")

            # Serialize full aggregated_inputs for the prompt itself
            # Handled by _construct_gemini_prompt
            
        except Exception as e:
            logger.error(f"Erreur lors de la préparation du snippet de log des inputs pour AIAgent: {e}", exc_info=True)
            # Continue, as logging failure here isn't critical for decision making

        try:
            prompt_for_gemini = self._construct_gemini_prompt(aggregated_inputs)
            if self.config.DEBUG_PROMPTS: # Instruction 5 from review
                logger.debug(f"Full prompt for Gemini:\n{prompt_for_gemini}")
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

    def _construct_gemini_prompt(self, aggregated_inputs: Dict[str, Any]) -> str:
        """
        Constructs the full prompt for Gemini based on aggregated_inputs.
        (Corresponds to todo/02-todo-ai-api-gemini.md Tâche 3.2)
        """
        # Extract target pair info for clarity in prompt
        target_pair_info = aggregated_inputs.get("target_pair_info", {})
        target_symbol = target_pair_info.get("target_token_symbol", "N/A")
        base_symbol = target_pair_info.get("base_token_symbol_for_pair", "N/A")
        current_pair_str = f"{target_symbol}/{base_symbol}"

        # Serialize inputs for the prompt (can be selective to reduce token count)
        # Example: Exclude very verbose fields or summarize them if necessary
        prompt_payload_data = {}
        for key, value in aggregated_inputs.items():
            if key == "market_data" and value and "ohlcv_data" in value and value["ohlcv_data"]:
                # Summarize OHLCV if too long, or just pass recent N candles
                # For now, let's ensure it's serializable and not excessively long
                # A better summarization or feature extraction should happen before this point if needed.
                prompt_payload_data[key] = value # Pass as is for now, assuming it's managed
            elif key == "signal_sources" and value and "strategy_analysis" in value:
                # Ensure strategy analysis is concise
                prompt_payload_data[key] = value
            else:
                prompt_payload_data[key] = value
        
        try:
            prompt_payload_json = json.dumps(prompt_payload_data, default=str, indent=2)
        except Exception as e:
            logger.error(f"Error serializing aggregated_inputs for prompt construction: {e}", exc_info=True)
            raise ValueError(f"Could not serialize inputs for Gemini prompt: {e}")

        # Structure from todo/02-todo-ai-api-gemini.md - Tâche 3.2
        prompt = f"""ROLE: NumerusX Solana Trading Agent (using {self.config.GEMINI_MODEL_NAME} model).
Analyze the following data for {current_pair_str} and provide a trading decision.

INSTRUCTIONS:
Based ONLY on the provided data, decide to BUY, SELL, or HOLD {current_pair_str}.
If BUY or SELL:
  - Specify amount_usd to trade (consider risk parameters and available capital). This field is MANDATORY for BUY/SELL.
  - Suggest stop_loss_price and take_profit_price.
Output your decision and reasoning STRICTLY in the following JSON format:
{{
  "decision": "BUY" | "SELL" | "HOLD",
  "token_pair": "{current_pair_str}",
  "amount_usd": float | null,
  "confidence": float,
  "stop_loss_price": float | null,
  "take_profit_price": float | null,
  "reasoning": "Concise explanation based on synthesized data points (max 500 chars)."
}}
Prioritize capital preservation. If data is conflicting or insufficient for a high-confidence trade, prefer HOLD.
Be concise in your reasoning.
Ensure your output strictly follows the JSON format specified. Do not include any text before or after the JSON object.

PROVIDED DATA:
{prompt_payload_json}

JSON RESPONSE:"""
        return prompt

    # D'autres méthodes pourraient être ajoutées ici pour:
    # - Le chargement/entraînement de modèles spécifiques à l'agent.
    # - Des logiques d'adaptation ou d'apprentissage.
    # - Des fonctions utilitaires pour l'analyse des inputs.

async def main_test_agent():
    class MockConfig(Config):
        pass
    mock_config = MockConfig()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Assurez-vous que GOOGLE_API_KEY est dans votre .env pour que GeminiClient s'initialise
    if not mock_config.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY non trouvé dans les variables d'env. Test de AIAgent annulé.")
        return

    ai_agent = AIAgent(config=mock_config)
    if not ai_agent.gemini_client.model:
        logger.error("Initialisation du modèle GeminiClient échouée. Test de AIAgent annulé.")
        return

    sample_inputs = {
        "timestamp_utc": "2023-10-27T10:30:00Z",
        "target_pair": { "symbol": "SOL/USDC", "input_mint": "So11111111111111111111111111111111111111112", "output_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"},
        "market_data": { "current_price": 165.30, "recent_trend_1h": "UPWARD"},
        "signal_sources": [{"source_name": "MomentumStrategy_1h_RSI_MACD", "signal": "STRONG_BUY", "confidence": 0.85}],
        "risk_manager_inputs": { "max_trade_size_usd": 200.00},
        "portfolio_manager_inputs": { "available_capital_usdc": 4000.00},
    }

    decision = await ai_agent.decide_trade(sample_inputs)
    print(f"\n--- Décision Finale de l'Agent IA ---\n{json.dumps(decision, indent=2)}\n----------------------------------")

if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main_test_agent())
    # More robust way to run asyncio for scripts:
    asyncio.run(main_test_agent())

    # Example of how an encrypted value from config might be used by the agent if needed
    # (though API keys are usually used by data providers, not directly by the agent core logic)
    # if mock_config.JUPITER_API_KEY:
    #     logger.info(f"Agent has access to JUPITER_API_KEY (example): {mock_config.JUPITER_API_KEY[:5]}...")
    # else:
    #     logger.warning("JUPITER_API_KEY not available to agent in this example.") 