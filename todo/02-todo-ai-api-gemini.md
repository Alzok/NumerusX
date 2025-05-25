# NumerusX - AI Agent API Integration (Google Gemini 2.5 Flash Preview) 🧠⚡

**Objectif**: Intégrer l'API Google Gemini 2.5 Flash Preview comme moteur de décision principal pour l'`AIAgent` de NumerusX. Ce plan met l'accent sur une intégration efficace, une optimisation des coûts en minimisant les appels API par une préparation minutieuse des données, et une interaction utilisateur claire concernant les décisions de l'IA.

## Prérequis

* Un compte Google Cloud avec l'API Gemini activée (via Vertex AI ou Google AI Studio) et une clé API.
* Compréhension de l'architecture de NumerusX, notamment le rôle de `AIAgent` et `DexBot` tels que définis dans `0-architecte.md`.

## Modèle d'IA Sélectionné

* **API**: Google AI (via Vertex AI ou Google AI Studio)
* **Modèle Cible Primaire**: Un modèle de la famille Gemini Flash (ex: `gemini-1.5-flash-latest` ou l'équivalent spécifique via Vertex AI). Le nom exact sera défini dans `Config.GEMINI_MODEL_NAME`.

## Phase 1: Configuration et Installation Initiale

### Tâche 1.1: Mise à Jour de la Configuration
-   **Objectif**: Ajouter les configurations nécessaires pour l'API Gemini.
-   **Fichier Concerné**: `app/config.py`
-   **Détails**:
    -   [x] Ajouter `GOOGLE_API_KEY` à la classe `Config`. Charger depuis les variables d'environnement (avec chiffrement).
    -   [x] Ajouter `GEMINI_MODEL_NAME` (valeur: "gemini-2.5-flash-preview-05-20") à `Config`. Ce sera le nom exact passé à l'API.
    -   [x] Ajouter `GEMINI_API_TIMEOUT_SECONDS` (défaut 30s) à `Config`.
    -   [x] Ajouter `GEMINI_MAX_TOKENS_INPUT` (défaut 4096) à `Config`.
    -   [x] S'assurer que la clé API n'est pas commitée (utilisation de `.env`, `python-dotenv` et `EncryptionUtil`).

### Tâche 1.2: Ajout de la Dépendance
-   **Objectif**: Inclure la bibliothèque Python de Google pour Gemini.
-   **Fichier Concerné**: `requirements.txt`
-   **Détails**:
    -   [x] Ajouter `google-generativeai>=0.5.4` à `requirements.txt`.

## Phase 2: Client API Gemini

### Tâche 2.1: Création du Client API Gemini [Initialisation]
    -   [🚧] **Objectif**: Mettre en place la structure initiale de `GeminiClient` avec initialisation et une méthode `get_decision` de base.
    -   [x] **Fichier Concerné**: `app/ai_agent/gemini_client.py` (Créé)
    -   **Détails complétés dans cette étape**:
        -   [x] Classe `GeminiClient` créée.
        -   [x] `__init__` avec `Config`, initialisation `genai.GenerativeModel`, `safety_settings`, `generation_config`.
        -   [x] Méthode `get_decision` asynchrone avec gestion de timeout, extraction de texte et `usage_metadata`, et gestion d'erreurs de base.
        -   [x] Section `if __name__ == "__main__":` pour tests locaux.
    -   **Prochaine étape (Tâche 2.2)**: Raffiner la gestion des erreurs spécifiques à l'API Gemini.

### Tâche 2.2: Gestion des Erreurs API dans le Client Gemini
-   **Objectif**: Gérer les erreurs spécifiques à l'API Gemini.
-   **Fichier Concerné**: `app/ai_agent/gemini_client.py`
-   **Détails**:
    -   [x] **Objectif**: Gérer les erreurs spécifiques à l'API Gemini.
    -   [x] **Fichier Concerné**: `app/ai_agent/gemini_client.py`
    -   [x] **Détails**:
        -   [x] Importé `google.api_core.exceptions as google_exceptions`.
        -   [x] Dans `get_decision`, intercepté `asyncio.TimeoutError` et des exceptions Google spécifiques: `google_exceptions.InvalidArgument`, `google_exceptions.ResourceExhausted`, `google_exceptions.PermissionDenied`, `google_exceptions.ServiceUnavailable`, `google_exceptions.InternalServerError`.
        -   [x] Intercepté également `genai.types.BlockedPromptException` et `genai.types.generation_types.StopCandidateException`.
        -   [x] Ajout d'une vérification de `response.prompt_feedback.block_reason` et `response.candidates` pour détecter les blocages de contenu ou réponses vides, même sans exception levée.
        -   [x] Chaque cas d'erreur retourne un dictionnaire `{'success': False, 'error': 'Message spécifique...', 'data': ...}` avec des détails pertinents.
        -   [x] Les erreurs API sont journalisées avec `logger.error()` ou `logger.warning()` et `exc_info=True` pour la trace.
        -   [x] Amélioration de la gestion des erreurs dans `__init__` également.

## Phase 3: Intégration avec `AIAgent` et Optimisation du Prompt

### Tâche 3.1: Modification de `AIAgent` pour Utiliser `GeminiClient`
-   **Objectif**: Adapter `AIAgent` pour qu'il utilise `GeminiClient` pour prendre ses décisions.
-   **Fichier Concerné**: `app/ai_agent.py`
-   **Détails**:
    -   [🚧] **Objectif**: Adapter `AIAgent` pour qu'il utilise `GeminiClient` pour prendre ses décisions.
    -   [x] **Fichier Concerné**: `app/ai_agent.py`
    -   [x] **Détails**:
        -   [x] Importé et initialisé `GeminiClient` dans le constructeur de `AIAgent`.
        -   [x] La méthode `decide_trade(self, aggregated_inputs: Dict)` de `AIAgent` est maintenant `async`.
        -   [ ] **Préparer un prompt unique et complet** à partir des `aggregated_inputs` (Placeholder ajouté, Tâche 3.2 pour détails).
        -   [x] Appelle `await self.gemini_client.get_decision(prompt_text)`.
        -   [x] Gère la réponse de `GeminiClient` (succès/échec). En cas d'échec, retourne un `HOLD` avec l'erreur.
        -   [ ] Parser la réponse texte du LLM (Placeholder ajouté, Tâche 3.3 pour parsing robuste avec Pydantic).

    - [ ] **Gestion des Erreurs et Continuité du Cycle par `DexBot`**:
        - `GeminiClient` intercepte les erreurs API brutes (timeouts, rate limits, erreurs de contenu Gemini) et les encapsule en erreurs structurées (ex: `GeminiAPIError` avec des détails) ou retourne un objet de décision indiquant l'échec.
        - `AIAgent` reçoit cette erreur structurée ou l'objet d'échec. Il peut tenter une logique de fallback interne simple (ex: HOLD par défaut) ou propager l'échec.
        - `DexBot` reçoit la décision finale de `AIAgent` (succès ou échec avec détails). En cas d'échec persistant de l'IA, `DexBot` doit journaliser l'erreur de manière critique et peut décider de :
            - Sauter le cycle de trading actuel.
            - Augmenter l'intervalle entre les cycles.
            - Entrer dans un mode "dégradé" en attendant la résolution du problème avec l'API Gemini. Ce mode dégradé consistera à **ne pas initier de nouveaux trades** et à uniquement gérer les positions existantes (ex: suivre les stop-loss / take-profit s'ils ont été définis lors d'une décision IA précédente valide).
            - Envoyer une alerte à l'utilisateur via l'UI et potentiellement d'autres canaux (email, etc.).
        - La priorité est d'assurer la continuité des opérations du bot et la préservation du capital, même si le module IA est temporairement indisponible.

### Tâche 3.2: Conception du Prompt Optimisé pour Gemini 2.5 Flash (Coût et Efficacité)
-   **Objectif**: Créer un prompt très structuré et concis pour le modèle `gemini-2.5-flash-preview-05-20` (tel que défini dans `Config.GEMINI_MODEL_NAME`), afin d'obtenir des réponses précises tout en minimisant le nombre de tokens d'entrée et de sortie.
-   **Fichier Concerné**: Logique de construction du prompt dans `app/ai_agent.py`.
-   **Détails**:
    -   [ ] **Rôle et Contexte Principal**: Définir clairement que l'IA est un agent de trading pour NumerusX sur Solana, spécialisé dans l'analyse de multiples sources de données pour prendre des décisions d'achat, de vente ou de conservation.
    -   [ ] **Formatage des Données d'Entrée**:
        -   Fournir les `aggregated_inputs` sous forme de JSON stringifié ou d'une structure textuelle très claire et compacte.
        -   Exemple de structure d'input (à adapter et rendre concise) :
            ```text
            ROLE: NumerusX Solana Trading Agent (using gemini-2.5-flash-preview-05-20 model). Analyze the following data for SOL/USDC and provide a trading decision.

            CURRENT MARKET DATA (SOL/USDC):
            - Price: $165.30
            - 24h Volume: $1.2B
            - Liquidity: $25M
            - Recent Trend (1h): Upward
            - Key Support: $160.00
            - Key Resistance: $170.00

            TECHNICAL INDICATORS (1h):
            - RSI: 68 (Approaching Overbought)
            - MACD: Bullish Crossover (Signal Strength: 0.7/1.0)
            - Bollinger Bands: Price near Upper Band (Width: 5%)

            AI PREDICTIONS (for SOL):
            - Price Prediction (next 4h): $168.00 - $172.00 (Confidence: 0.75)
            - Market Regime: Volatile-Trending
            - Sentiment Score (Social Media): 0.6 (Positive, Volume: High)

            RISK PARAMETERS:
            - Max Portfolio Exposure per Trade: 2%
            - Current Portfolio Value: $10,000 USD
            - Available Capital: $4,000 USDC
            - Current Open Positions (SOL/USDC): None (or details if any)

            TOKEN SECURITY (SOL):
            - Security Score: 0.9/1.0 (Low Risk)
            - Recent Alerts: None

            INSTRUCTIONS:
            Based ONLY on the provided data, decide to BUY, SELL, or HOLD SOL/USDC.
            If BUY or SELL:
              - Specify amount_usd to trade (consider risk parameters and available capital).
              - Suggest stop_loss_price and take_profit_price.
            Output your decision and reasoning STRICTLY in the following JSON format:
            {
              "decision": "BUY" | "SELL" | "HOLD",
              "token_pair": "SOL/USDC",
              "amount_usd": float | null, // Amount in USDC for the trade
              "confidence": float, // Your confidence in this decision (0.0 to 1.0)
              "stop_loss_price": float | null,
              "take_profit_price": float | null,
              "reasoning": " concise explanation based on synthesized data points."
            }
            Prioritize capital preservation. If data is conflicting or insufficient for a high-confidence trade, prefer HOLD.
            Be concise in your reasoning.
            Ensure your output strictly follows the JSON format specified.
            ```
    -   [ ] **Structure Détaillée des `aggregated_inputs` (Exemple)**:
        -   L'objet `aggregated_inputs` transmis à `AIAgent.decide_trade()` sera un dictionnaire Python. Pour la construction du prompt Gemini, ce dictionnaire sera sérialisé en JSON (ou formaté en une chaîne de caractères structurée similaire).
        -   Voici une proposition de structure (à affiner) :
            ```python
            # Exemple de structure pour aggregated_inputs
            aggregated_inputs = {
                "timestamp_utc": "2023-10-27T10:30:00Z",
                "target_pair": { # Informations spécifiques à la paire envisagée
                    "symbol": "SOL/USDC",
                    "input_mint": "So11111111111111111111111111111111111111112",
                    "output_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                },
                "market_data": { # Fourni par MarketDataProvider
                    "current_price": 165.30,
                    "recent_ohlcv_1h": [ # Liste d'objets OHLCV pour la dernière heure
                        {"t": 1698397200, "o": 165.0, "h": 165.5, "l": 164.8, "c": 165.3, "v": 10000},
                        # ... autres bougies ...
                    ],
                    "liquidity_depth_usd": 25000000, # Profondeur du carnet d'ordres ou du pool LP
                    "recent_trend_1h": "UPWARD", # Peut être calculé ou issu d'une analyse
                    "key_support_resistance": {
                        "support_1": 160.00,
                        "resistance_1": 170.00
                    },
                    "volatility_1h_atr_percentage": 0.015 # 1.5% ATR sur 1h
                },
                "signal_sources": [ # Liste des outputs des stratégies/analytics_engine
                    {
                        "source_name": "MomentumStrategy_1h_RSI_MACD",
                        "signal": "STRONG_BUY", # Ou "NEUTRAL", "SELL", etc.
                        "confidence": 0.85,
                        "indicators": {
                            "rsi_14": 68,
                            "macd_signal_strength": 0.7,
                            "bollinger_position": "NEAR_UPPER_BAND" # Ex: "NEAR_UPPER", "MIDDLE", "NEAR_LOWER"
                        },
                        "reasoning_snippet": "RSI bullish, MACD crossover positive."
                    },
                    {
                        "source_name": "AdvancedAnalytics_VolumeSpike",
                        "signal": "POTENTIAL_REVERSAL_SOON",
                        "confidence": 0.60,
                        "details": {"volume_zscore_5m": 3.5},
                        "reasoning_snippet": "Recent 5m volume spike suggests exhaustion."
                    }
                    # ... autres sources de signaux ...
                ],
                "prediction_engine_outputs": { # Fourni par PredictionEngine
                    "price_prediction_4h": {
                        "target_price_min": 168.00,
                        "target_price_max": 172.00,
                        "confidence": 0.75,
                        "model_name": "RandomForest_v2"
                    },
                    "market_regime_1h": "VOLATILE_TRENDING", # Ex: "TRENDING_UP", "TRENDING_DOWN", "RANGING", "VOLATILE"
                    "sentiment_analysis": {
                        "overall_score": 0.6, # Sur une échelle de -1 (très négatif) à 1 (très positif)
                        "dominant_sentiment": "POSITIVE",
                        "source_summary": "Twitter positive, Reddit neutral",
                        "volume_of_mentions": "HIGH"
                    }
                },
                "risk_manager_inputs": { # Fourni par RiskManager
                    "max_exposure_per_trade_percentage": 0.02, # 2%
                    "current_portfolio_value_usd": 10000.00,
                    "available_capital_usdc": 4000.00,
                    "max_trade_size_usd": 200.00, # Calculé: 2% de 10000
                    "overall_portfolio_risk_level": "MODERATE" # Ex: "LOW", "MODERATE", "HIGH"
                },
                "portfolio_manager_inputs": { # Fourni par PortfolioManager
                    "current_positions": [
                        # {"symbol": "BTC/USDC", "amount": 0.1, "entry_price": 30000, "current_pnl_usd": 500},
                    ],
                    "total_pnl_realized_24h_usd": 150.00
                },
                "security_checker_inputs": { # Fourni par SecurityChecker
                    "token_security_score_sol": 0.9, # Score pour SOL (0 à 1)
                    "recent_security_alerts_sol": [] # Liste d'alertes
                }
            }
            ```

    -   [ ] **Format de Sortie de l'AIAgent (Confirmation)**:
        -   Il est confirmé que le format de sortie JSON pour Gemini défini précédemment dans cette tâche (avec les champs `decision`, `token_pair`, `amount_usd`, `confidence`, `stop_loss_price`, `take_profit_price`, `reasoning`) est bien le format définitif que `AIAgent` s'attend à recevoir et à parser. `DexBot` utilisera ensuite cette structure pour initier des actions via le `TradeExecutor`.

### Tâche 3.3: Parsing Robuste et Validation de la Réponse JSON de Gemini
-   **Objectif**: Extraire de manière fiable la décision structurée de la réponse texte de Gemini.
-   **Fichier Concerné**: `app/ai_agent.py`
-   **Détails**:
    -   [ ] Dans `AIAgent.decide_trade`, après avoir reçu la réponse de `GeminiClient`:
        -   [ ] Vérifier le succès de l'appel.
        -   [ ] Extraire le contenu textuel de la réponse.
        -   [ ] Tenter de parser ce texte comme un JSON.
        -   [ ] Valider rigoureusement la structure du JSON par rapport au format attendu (champs, types).
            - [ ] Implémenter la validation de la structure JSON de sortie avec `pydantic` en utilisant un modèle comme suit (à adapter si nécessaire) :
              ```python
              from pydantic import BaseModel, confloat, conlist, constr # Ajouter Optional, Literal
              from typing import Optional, Literal # Importer Optional et Literal

              class TradeDecision(BaseModel):
                  decision: Literal["BUY", "SELL", "HOLD"]
                  token_pair: str # ex: "SOL/USDC"
                  amount_usd: Optional[confloat(gt=0)] = None
                  confidence: confloat(ge=0, le=1)
                  stop_loss_price: Optional[confloat(gt=0)] = None
                  take_profit_price: Optional[confloat(gt=0)] = None
                  reasoning: constr(min_length=10, max_length=500) # Raisonnement concis
              ```
        -   [ ] Gérer les cas où le LLM retourne un JSON malformé ou incomplet. Implémenter des reintentions avec un prompt légèrement modifié (ex: "Please ensure output is valid JSON.") si cela arrive occasionnellement, ou un fallback sûr (HOLD).
        -   [ ] Convertir la décision parsée en l'objet `Ordre de Trade Final` utilisé par `DexBot`.

## Phase 4: Journalisation, Mécanismes de Fallback et Tests

### Tâche 4.1: Journalisation Détaillée des Interactions avec Gemini
-   **Objectif**: Assurer une traçabilité complète pour le débogage, l'audit et l'amélioration des prompts.
-   **Fichiers Concernés**: `app/ai_agent/gemini_client.py`, `app/ai_agent.py`, `app/logger.py`
-   **Détails**:
    -   [ ] Journaliser le prompt complet envoyé à l'API Gemini.
    -   [ ] Journaliser la réponse brute (texte) reçue de l'API.
    -   [ ] Journaliser la décision structurée parsée et le raisonnement.
    -   [ ] Journaliser les métadonnées d'utilisation (nombre de tokens d'entrée/sortie si l'API les fournit) pour chaque appel.
    -   [ ] Mesurer et journaliser le temps de réponse de l'API.

### Tâche 4.2: Mécanismes de Reintentions et Fallback pour l'API Gemini
-   **Objectif**: Augmenter la résilience du système face aux échecs ou latences de l'API Gemini.
-   **Fichier Concerné**: `app/ai_agent/gemini_client.py`, `app/ai_agent.py`
-   **Détails**:
    -   [ ] Utiliser `tenacity` pour implémenter des reintentions avec backoff exponentiel pour les appels à `gemini_client.get_decision` en cas d'erreurs réseau, de `DeadlineExceeded`, ou `ResourceExhausted`.
    -   [ ] Si l'API Gemini retourne une erreur indiquant un problème avec le prompt (ex: contenu bloqué malgré les `safety_settings`), `AIAgent` pourrait tenter de reformuler légèrement le prompt ou de réduire la quantité de données textuelles sensibles.
    -   [ ] En cas d'échecs répétés ou si la réponse n'est pas parsable après reintentions, `AIAgent` doit déclencher une stratégie de fallback :
        -   **Stratégie de Fallback Principale et Explicite**: 
            -   `AIAgent` émettra une décision `{"decision": "HOLD", "token_pair": "<TARGET_PAIR>", "amount_usd": null, "confidence": 0.1, "stop_loss_price": null, "take_profit_price": null, "reasoning": "AIAgent (Gemini API) failed to provide a decision after multiple attempts or response was unparsable. Defaulting to HOLD to ensure safety. Manual review advised."}`.
            -   Cette décision "HOLD" sera journalisée de manière critique.
            -   `DexBot` traitera cette décision HOLD comme une absence d'opportunité de trade pour le cycle actuel.
        -   **Pas de Fallback vers une Stratégie Secondaire Automatisée Initialement**: Pour éviter une complexité additionnelle et des comportements imprévus, le système ne basculera pas automatiquement vers une stratégie de trading algorithmique alternative (ex: `MomentumStrategy`) si Gemini échoue. La priorité est la sécurité et l'alerte pour une intervention humaine ou une résolution du problème API. Une telle bascule pourrait être envisagée dans une phase ultérieure avec des tests rigoureux.
        -   L'objectif est que `DexBot` continue son cycle de vie (collecte de données, etc.) mais s'abstienne de trader activement si l'IA n'est pas fiable, tout en informant l'utilisateur.

### Tâche 4.3: Tests d'Intégration et de Robustesse
-   **Objectif**: Valider l'intégration de l'API Gemini et la fiabilité des décisions.
-   **Détails**:
    -   [ ] Tests unitaires pour `GeminiClient` en simulant (mocking) les réponses de l'API Gemini (succès, erreurs, contenu bloqué).
    -   [ ] Tests d'intégration pour `AIAgent` vérifiant la construction du prompt, l'appel au `GeminiClient`, le parsing de la réponse JSON, et la gestion des erreurs/fallback.
    -   [ ] Créer des scénarios de test avec divers `aggregated_inputs` (y compris des données manquantes ou contradictoires) pour observer le comportement de l'IA et la robustesse du parsing.
    -   [ ] Évaluer la latence de bout en bout du cycle de décision incluant l'appel à l'API Gemini.
    -   [ ] Inclure un cas de test comme `async def test_decision_parsing(mocker)` pour valider le parsing des décisions simulées du `GeminiClient` par `AIAgent` (ex: vérifier que `decision.action == "BUY"` pour une réponse mockée appropriée).

## Phase 5: Intégration UI et Monitoring des Coûts

### Tâche 5.1: Affichage des Décisions et Raisonnements IA dans le Dashboard (`numerusx-ui/`)
-   **Objectif**: Fournir à l'utilisateur une transparence sur les décisions prises par l'agent IA.
-   **Fichier Concerné**: `numerusx-ui/` (et ses composants, en s'appuyant sur `todo/01-todo-ui.md`)
-   **Détails**:
    -   [ ] Modifier `EnhancedDatabase` pour stocker le raisonnement de l'IA et les principaux inputs qui ont mené à la décision.
    -   [ ] Dans l'application React `numerusx-ui/` (conformément à `todo/01-todo-ui.md`), implémenter les vues nécessaires (ex: section "Trading Activity", "AI Agent Insights") pour afficher :
        -   La décision prise (BUY/SELL/HOLD).
        -   Le token concerné.
        -   La confiance de l'IA.
        -   Le raisonnement textuel fourni par Gemini.
        -   Un résumé des indicateurs clés que l'IA a mentionnés ou qui étaient prédominants dans le prompt.
    -   [ ] Permettre de visualiser le prompt envoyé à l'IA (peut-être dans une vue "détails avancés" pour le débogage), via l'UI React.

### Tâche 5.2: Suivi Actif des Coûts de l'API Gemini
-   **Objectif**: Surveiller et gérer les coûts associés à l'utilisation de l'API Gemini.
-   **Fichiers Concernés**: `app/ai_agent/gemini_client.py`, `app/logger.py`, potentiellement un nouveau module de monitoring.
-   **Détails**:
    -   [ ] Si l'API Gemini fournit des informations sur l'utilisation des tokens dans sa réponse (`usage_metadata`), les extraire et les journaliser.
    -   [ ] Calculer une estimation du coût par appel basé sur la tarification de `gemini-2.5-flash-preview-05-20` (tel que configuré dans `Config.GEMINI_MODEL_NAME`).
        - [ ] Implémenter une fonction `_calculate_cost(self, usage_metadata)` dans `GeminiClient` basée sur les tarifs indicatifs pour `gemini-1.5-flash-latest` (ces tarifs sont sujets à changement et doivent être vérifiés sur la documentation officielle de Google Cloud au moment de l'implémentation):
            - Entrée: Exemple $0.35 par million de tokens (pour les premiers 128k tokens de contexte, puis $0.70 au-delà, à simplifier ou à rendre configurable si besoin).
            - Sortie: Exemple $1.05 par million de tokens (pour les premiers 128k tokens de contexte, puis $2.10 au-delà).
            - Pour une estimation simplifiée initiale, on peut utiliser les tarifs de base.
          ```python
          # Dans GeminiClient
          # Exemple de tarification pour gemini-1.5-flash-latest (tarifs à confirmer et adapter):
          # INPUT_COST_PER_MILLION_TOKENS = 0.35 # Pour contexte <= 128K
          # OUTPUT_COST_PER_MILLION_TOKENS = 1.05 # Pour contexte <= 128K

          # def _calculate_cost(self, usage_metadata): # Ou usage_metadata.get('input_tokens', 0)
          #     input_tokens = usage_metadata.get('prompt_token_count', 0)
          #     output_tokens = usage_metadata.get('candidates_token_count', 0)
          #     input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_MILLION_TOKENS 
          #     output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION_TOKENS
          #     return input_cost + output_cost
          ```
    -   [ ] Journaliser le coût estimé par décision.
    -   [ ] Mettre en place des seuils d'alerte dans le système de monitoring (ou via logs) si le coût journalier/hebdomadaire dépasse un budget prédéfini dans `Config`.

En suivant ces étapes, NumerusX pourra exploiter la vitesse et l'intelligence de Gemini 2.5 Flash pour prendre des décisions de trading éclairées, tout en gardant un contrôle sur les coûts et la robustesse du système.