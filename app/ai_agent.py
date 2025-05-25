import logging
from typing import Dict, Any, Optional
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
# Placeholder for pydantic model for TradeDecision (Task 3.3)
# from pydantic import BaseModel, ValidationError # Example

logger = logging.getLogger(__name__)

# Placeholder for TradeDecision Pydantic model (Task 3.3)
# class TradeDecisionModel(BaseModel):
#     decision: str
#     token_pair: Optional[str] = None
#     amount_usd: Optional[float] = None
#     confidence: float
#     stop_loss_price: Optional[float] = None
#     take_profit_price: Optional[float] = None
#     reasoning: str

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
        """
        try:
            inputs_snippet = json.dumps(aggregated_inputs, default=str, indent=2)
            if len(inputs_snippet) > 1000: # Increased snippet size for better debugging
                inputs_snippet = inputs_snippet[:1000] + "... (truncated)"
        except TypeError:
            inputs_snippet = "Inputs contain non-serializable data."
        logger.debug(f"AIAgent.decide_trade appelé avec les inputs: {inputs_snippet}")

        # 1. Préparer le prompt pour Gemini (Tâche 3.2)
        # This is a critical step. The prompt must be carefully constructed based on aggregated_inputs
        # and the expected JSON output format.
        # For now, a placeholder. Actual prompt construction will be more complex.
        try:
            # Attempt to serialize the entire aggregated_inputs as part of the prompt
            # This will need significant refinement in Task 3.2 for conciseness and clarity for the LLM
            prompt_payload_json = json.dumps(aggregated_inputs, default=str) 
        except Exception as e:
            logger.error(f"Erreur lors de la sérialisation des aggregated_inputs pour le prompt: {e}", exc_info=True)
            return {
                'action': 'HOLD',
                'reasoning': f"Erreur interne de l'AIAgent: Impossible de préparer les données pour l'IA. Détails: {str(e)}",
                'confidence_score': 0.0
            }

        # TODO: Placeholder pour la construction du prompt final (Tâche 3.2)
        # Le prompt devra inclure des instructions claires, le format de sortie JSON attendu, etc.
        # et intégrer `prompt_payload_json` de manière structurée.
        # Exemple simplifié (sera étendu en Tâche 3.2):
        prompt_for_gemini = (
            "Vous êtes un agent de trading expert pour NumerusX opérant sur Solana.\n"
            "Analysez les données suivantes et fournissez une décision de trading (BUY, SELL, ou HOLD) pour la paire spécifiée.\n"
            "Votre réponse DOIT être un JSON valide respectant le format suivant:\n"
            "{\n"
            "  \"decision\": \"BUY\" | \"SELL\" | \"HOLD\",\n"
            "  \"token_pair\": \"SOL/USDC\",\n"
            "  \"amount_usd\": float | null, \n"
            "  \"confidence\": float, \n"
            "  \"stop_loss_price\": float | null,\n"
            "  \"take_profit_price\": float | null,\n"
            "  \"reasoning\": \"Explication concise.\"\n"
            "}\n\n"
            "Voici les données à analyser:\n"
            f"{prompt_payload_json}\n\n"
            "Fournissez UNIQUEMENT le JSON comme réponse."
        )

        max_output_tokens = self.config.GEMINI_MAX_TOKENS_INPUT // 4 # Arbitrary, ensure output is much smaller than input limit
        if max_output_tokens < 256: max_output_tokens = 256 # Minimum sensible value
        if max_output_tokens > 2048: max_output_tokens = 2048 # Maximum sensible value

        # 2. Appeler GeminiClient
        gemini_response = await self.gemini_client.get_decision(prompt_for_gemini, max_output_tokens=max_output_tokens)

        # 3. Gérer la réponse du GeminiClient
        if not gemini_response['success']:
            logger.error(f"Erreur de GeminiClient: {gemini_response['error']}")
            return {
                'action': 'HOLD',
                'reasoning': f"L'Agent IA (Gemini) n'a pas pu fournir de décision. Erreur: {gemini_response['error']}",
                'confidence_score': 0.1 # Low confidence due to error
            }

        # 4. Parser la réponse texte de Gemini (Tâche 3.3)
        # Placeholder pour le parsing et la validation. 
        # La Tâche 3.3 implémentera un parsing robuste avec Pydantic.
        try:
            decision_data = json.loads(gemini_response['decision_text'])
            logger.info(f"Décision brute de Gemini (parsée): {decision_data}")
            
            # TODO: Valider avec Pydantic (TradeDecisionModel) ici (Tâche 3.3)
            # Exemple de ce que Pydantic ferait:
            # validated_decision = TradeDecisionModel(**decision_data)
            # decision_to_return = validated_decision.dict()
            
            # Pour l'instant, on retourne les données parsées directement, en s'assurant que les clés attendues existent.
            # This is a temporary measure and not robust.
            action = decision_data.get('decision', 'HOLD').upper()
            reasoning = decision_data.get('reasoning', 'Raisonnement manquant de la part de Gemini.')
            confidence = decision_data.get('confidence', 0.5)
            token_pair = decision_data.get('token_pair')
            amount_usd = decision_data.get('amount_usd')
            stop_loss = decision_data.get('stop_loss_price')
            take_profit = decision_data.get('take_profit_price')

            # Convertir au format attendu par le reste du système (si différent)
            # Le format de sortie de Gemini est déjà proche de ce qui est attendu.
            final_decision = {
                'action': action,
                'pair': token_pair, # Assumer que Gemini le fournit
                'amount': amount_usd, # Sera interprété comme amount_usd
                'amount_is_quote': True if amount_usd is not None else None, # Si amount_usd, c'est en quote
                'order_type': 'MARKET', # Gemini ne spécifie pas le type d'ordre, MARKET par défaut
                'limit_price': None, 
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reasoning': reasoning,
                'confidence_score': confidence
            }
            if action not in ["BUY", "SELL", "HOLD"]:
                 logger.warning(f"Décision invalide de Gemini: {action}. Forçage à HOLD.")
                 final_decision['action'] = 'HOLD'
                 final_decision['reasoning'] += " (Action invalide reçue, forcée à HOLD)"

        except json.JSONDecodeError as e:
            logger.error(f"Impossible de parser la réponse JSON de Gemini: {gemini_response['decision_text']}. Erreur: {e}", exc_info=True)
            return {
                'action': 'HOLD',
                'reasoning': f"L'Agent IA (Gemini) a retourné une réponse non-JSON. Réponse: {gemini_response['decision_text'][:200]}...",
                'confidence_score': 0.1
            }
        except Exception as e:
            logger.error(f"Erreur inattendue lors du traitement de la réponse de Gemini: {e}", exc_info=True)
            return {
                'action': 'HOLD',
                'reasoning': f"Erreur interne de l'AIAgent lors du traitement de la réponse de l'IA. Détails: {str(e)}",
                'confidence_score': 0.0
            }

        logger.info(f"AIAgent decision: {final_decision['action']} pour {final_decision.get('pair', 'N/A')}, Confidence: {final_decision['confidence_score']}, Reason: {final_decision['reasoning']}")
        return final_decision

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