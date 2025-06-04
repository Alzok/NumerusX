# NumerusX - AI Agent API Integration (Google Gemini 2.5 Flash Preview) 🧠⚡

**Objectif**: Intégrer l'API Google Gemini 2.5 Flash Preview comme moteur de décision principal pour l'`AIAgent` de NumerusX. Ce plan met l'accent sur une intégration efficace, une optimisation des coûts en minimisant les appels API par une préparation minutieuse des données, et une interaction utilisateur claire concernant les décisions de l'IA.

## Prérequis
* Un compte Google Cloud avec l'API Gemini activée et une clé API
* Compréhension de l'architecture de NumerusX et du rôle de `AIAgent`

## Modèle d'IA Sélectionné
* **API**: Google AI (via google-generativeai)
* **Modèle**: `gemini-2.5-flash-preview-05-20` (défini dans `Config.GEMINI_MODEL_NAME`)

## Phase 1: Configuration et Installation ✅ COMPLÉTÉ

### Tâche 1.1: Configuration ✅
-   [x] `GOOGLE_API_KEY` ajouté à `Config` avec chiffrement
-   [x] `GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20"` dans `Config`
-   [x] `GEMINI_API_TIMEOUT_SECONDS = 30` dans `Config`
-   [x] `GEMINI_MAX_TOKENS_INPUT = 4096` dans `Config`
-   [x] Clé API protégée via `.env` et `EncryptionUtil`

### Tâche 1.2: Dépendances ✅
-   [x] `google-generativeai>=0.5.4` ajouté à `requirements.txt`

## Phase 2: Client API Gemini ✅ COMPLÉTÉ

### Tâche 2.1: GeminiClient ✅
-   [x] Fichier `app/ai_agent/gemini_client.py` créé
-   [x] Classe `GeminiClient` implémentée avec :
    -   [x] Initialisation avec `GenerativeModel`
    -   [x] Configuration `safety_settings` et `generation_config`
    -   [x] Méthode `get_decision` asynchrone
    -   [x] Gestion timeout et extraction metadata
    -   [x] Section test `__main__`

### Tâche 2.2: Gestion des Erreurs ✅
-   [x] Import `google.api_core.exceptions`
-   [x] Gestion exceptions spécifiques :
    -   [x] `asyncio.TimeoutError`
    -   [x] `InvalidArgument`, `ResourceExhausted`, `PermissionDenied`
    -   [x] `ServiceUnavailable`, `InternalServerError`
    -   [x] `BlockedPromptException`, `StopCandidateException`
-   [x] Vérification `prompt_feedback.block_reason`
-   [x] Format retour `{'success': False, 'error': ..., 'data': ...}`
-   [x] Logging approprié des erreurs

### Tâche 2.3: Tests GeminiClient ⚠️ À FAIRE
- [ ] Créer `tests/test_gemini_client.py` :
    - [ ] Test initialisation avec clé valide/invalide
    - [ ] Test appel `get_decision` avec prompt simple
    - [ ] Test gestion timeout (mock asyncio.sleep)
    - [ ] Test erreurs API (mock exceptions Google)
    - [ ] Test calcul coût avec `usage_metadata`
    - [ ] Validation format réponse `{'success': ..., 'data': ...}`
    - [ ] Test blocage contenu (mock BlockedPromptException)

## Phase 3: Intégration AIAgent et Optimisation ⚠️ EN COURS

### Tâche 3.1: Intégration AIAgent ✅ PARTIELLEMENT
-   [x] `GeminiClient` importé et initialisé dans `AIAgent`
-   [x] Méthode `decide_trade` devenue asynchrone
-   [x] Appel `await self.gemini_client.get_decision(prompt_text)`
-   [x] Gestion échec API -> retour HOLD par défaut
-   [ ] Construction prompt optimisé (placeholder actuel)
-   [ ] Parsing robuste réponse JSON (placeholder actuel)

### Tâche 3.1.5: Structure AggregatedInputs ⚠️ URGENT
- [ ] **Créer `app/models/ai_inputs.py`** :
    - [ ] Modèles Pydantic pour chaque source :
        ```python
        from pydantic import BaseModel, Field, confloat, constr
        from typing import List, Optional, Dict, Literal
        from datetime import datetime
        
        class MarketDataInput(BaseModel):
            current_price: float
            recent_ohlcv_1h: List[Dict]
            liquidity_depth_usd: float
            recent_trend_1h: Literal["UPWARD", "DOWNWARD", "SIDEWAYS"]
            key_support_resistance: Dict[str, float]
            volatility_1h_atr_percentage: float
        
        class SignalSourceInput(BaseModel):
            source_name: str
            signal: Literal["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]
            confidence: confloat(ge=0, le=1)
            indicators: Dict[str, Any]
            reasoning_snippet: constr(max_length=200)
        
        class PredictionEngineInput(BaseModel):
            price_prediction_4h: Dict
            market_regime_1h: str
            sentiment_analysis: Dict
        
        class RiskManagerInput(BaseModel):
            max_exposure_per_trade_percentage: float
            current_portfolio_value_usd: float
            available_capital_usdc: float
            max_trade_size_usd: float
            overall_portfolio_risk_level: Literal["LOW", "MODERATE", "HIGH"]
        
        class SecurityCheckerInput(BaseModel):
            token_security_score: confloat(ge=0, le=1)
            recent_security_alerts: List[str]
        
        class PortfolioManagerInput(BaseModel):
            current_positions: List[Dict]
            total_pnl_realized_24h_usd: float
        
        class AggregatedInputs(BaseModel):
            timestamp_utc: datetime
            target_pair: Dict[str, str]
            market_data: MarketDataInput
            signal_sources: List[SignalSourceInput]
            prediction_engine_outputs: PredictionEngineInput
            risk_manager_inputs: RiskManagerInput
            portfolio_manager_inputs: PortfolioManagerInput
            security_checker_inputs: SecurityCheckerInput
        ```
    - [ ] Méthodes de validation custom si nécessaire
    - [ ] Documentation des champs

### Tâche 3.2: Prompt Optimisé ⚠️ À FAIRE
- [ ] Construire prompt structuré dans `AIAgent._build_prompt()` :
    - [ ] Section ROLE (agent trading Solana)
    - [ ] Section MARKET DATA (prix, volume, liquidité)
    - [ ] Section TECHNICAL INDICATORS (RSI, MACD, etc.)
    - [ ] Section AI PREDICTIONS (prix, régime, sentiment)
    - [ ] Section RISK PARAMETERS (limites, capital)
    - [ ] Section TOKEN SECURITY (score, alertes)
    - [ ] Instructions format JSON output
    - [ ] Limite tokens avec troncature intelligente

### Tâche 3.2.5: Optimisation Tokens ⚠️ À FAIRE
- [ ] Implémenter compression `aggregated_inputs` :
    - [ ] Fonction `_compress_market_data()` :
        - [ ] OHLCV : garder seulement N dernières bougies
        - [ ] Ou calculer stats (min, max, moyenne)
    - [ ] Fonction `_filter_signal_sources()` :
        - [ ] Prioriser par confiance
        - [ ] Limiter à top N signaux
        - [ ] Concaténer reasoning_snippets
    - [ ] Validation taille finale < `GEMINI_MAX_TOKENS_INPUT`
    - [ ] Fallback si trop grand : sections moins prioritaires

### Tâche 3.3: Parsing Réponse ⚠️ À FAIRE
- [ ] Implémenter parsing robuste dans `AIAgent` :
    - [ ] Modèle Pydantic `TradeDecision` :
        ```python
        class TradeDecision(BaseModel):
            decision: Literal["BUY", "SELL", "HOLD"]
            token_pair: str
            amount_usd: Optional[confloat(gt=0)] = None
            confidence: confloat(ge=0, le=1)
            stop_loss_price: Optional[confloat(gt=0)] = None
            take_profit_price: Optional[confloat(gt=0)] = None
            reasoning: constr(min_length=10, max_length=500)
        ```
    - [ ] Try/except pour JSON malformé
    - [ ] Retry avec prompt modifié si échec
    - [ ] Fallback HOLD si parsing impossible

## Phase 4: Journalisation et Robustesse ⚠️ À FAIRE

### Tâche 4.1: Journalisation Complète
- [ ] Logger dans `GeminiClient` :
    - [ ] Prompt complet (si mode debug)
    - [ ] Réponse brute Gemini
    - [ ] Metadata utilisation (tokens in/out)
    - [ ] Temps de réponse API
- [ ] Logger dans `AIAgent` :
    - [ ] Décision structurée finale
    - [ ] Raisonnement parsé
    - [ ] Erreurs parsing

### Tâche 4.2: Mécanismes Fallback
- [ ] Configurer `tenacity` pour retry :
    - [ ] Retry sur `ResourceExhausted`
    - [ ] Retry sur `ServiceUnavailable`
    - [ ] Backoff exponentiel
    - [ ] Max 3 tentatives
- [ ] Stratégie fallback principale :
    - [ ] Si échec API -> décision HOLD
    - [ ] Raisonnement : "API unavailable, defaulting to safety"
    - [ ] Log critique pour alerte
    - [ ] Pas de fallback vers stratégie algo

### Tâche 4.3: Tests Intégration
- [ ] Créer `tests/test_ai_agent_integration.py` :
    - [ ] Test construction prompt complet
    - [ ] Test appel GeminiClient (mock)
    - [ ] Test parsing décisions variées
    - [ ] Test gestion erreurs API
    - [ ] Test fallback HOLD
    - [ ] Test performance (latence)
    - [ ] Scénarios avec données manquantes

## Phase 5: UI et Monitoring ⚠️ À FAIRE

### Tâche 5.1: Affichage Décisions UI
- [ ] Modifier `EnhancedDatabase` :
    - [ ] Utiliser table `ai_decisions` (voir todo/01-todo-database.md)
    - [ ] Stocker prompt, réponse, raisonnement
- [ ] API endpoints (dans `app/api/v1/ai_decisions_routes.py`) :
    - [ ] GET `/api/v1/ai/decisions/history`
    - [ ] GET `/api/v1/ai/decisions/{id}/details`
    - [ ] GET `/api/v1/ai/decisions/stats`
- [ ] Composants React :
    - [ ] Liste décisions avec filtres
    - [ ] Détail décision avec inputs/outputs
    - [ ] Graphiques confiance vs performance

### Tâche 5.2: Monitoring Coûts
- [ ] Implémenter `_calculate_cost()` dans `GeminiClient` :
    ```python
    # Tarifs indicatifs gemini-2.5-flash (à vérifier)
    INPUT_COST_PER_1K_TOKENS = 0.00035  # $0.35/1M tokens
    OUTPUT_COST_PER_1K_TOKENS = 0.00105  # $1.05/1M tokens
    
    def _calculate_cost(self, usage_metadata):
        input_tokens = usage_metadata.get('prompt_token_count', 0)
        output_tokens = usage_metadata.get('candidates_token_count', 0)
        input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K_TOKENS
        output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K_TOKENS
        return input_cost + output_cost
    ```
- [ ] Stocker coûts dans `ai_decisions` table
- [ ] Dashboard métriques :
    - [ ] Coût par jour/semaine/mois
    - [ ] Tokens moyens par décision
    - [ ] Alertes budget dépassé
- [ ] Config `GEMINI_DAILY_BUDGET_USD` dans Config

## Points d'Attention Critiques

### Gestion Erreurs
* **GeminiClient** retourne `{'success': False, ...}` en cas d'erreur
* **AIAgent** doit gérer ce format et fallback HOLD
* **DexBot** doit continuer même si IA échoue

### Optimisation Prompts
* Respecter limite `GEMINI_MAX_TOKENS_INPUT = 4096`
* Compression intelligente des données
* Prioriser infos critiques

### Sécurité
* Clé API jamais dans les logs
* Prompt complet seulement en mode debug
* Sanitizer les inputs utilisateur

### Tests Prioritaires
1. Mock complet API Gemini
2. Scénarios edge cases (timeout, blocage)
3. Validation format décisions
4. Performance avec gros inputs

## Ordre d'Implémentation

1. **Immédiat** :
   - [ ] Créer `app/models/ai_inputs.py`
   - [ ] Créer `tests/test_gemini_client.py`
   - [ ] Implémenter `_build_prompt()` dans AIAgent

2. **Court terme** :
   - [ ] Parser robuste avec Pydantic
   - [ ] Optimisation compression tokens
   - [ ] Tests intégration complets

3. **Moyen terme** :
   - [ ] API endpoints décisions
   - [ ] Monitoring coûts
   - [ ] Dashboard UI React

## Métriques de Succès
- [ ] Latence décision < 2s (95 percentile)
- [ ] Taux parsing réussi > 99%
- [ ] Coût par décision < $0.001
- [ ] Uptime API > 99.9%