# NumerusX - IA TODO List 🤖

**Prompt pour l'IA**: Exécute les tâches une par une. Quand tu as terminé une tâche, vérifie la cohérence du code par rapport à l'ensemble du projet et au contexte fourni. Une fois la vérification terminée et la cohérence assurée, passe en autonomie à la tâche suivante.

## Phase 1: Initialisation et Configuration de Base (Jupiter API v6) - FONDATIONS

**Objectif**: Configurer l'environnement, intégrer le SDK Jupiter, et établir les bases pour l'interaction avec l'API Jupiter v6.

-   [x] **1.1. `app/config.py` (Jupiter API v6)**
    -   [x] Ajouter les nouveaux hostnames de l'API Jupiter v6 (`JUPITER_LITE_API_HOSTNAME`, `JUPITER_PRO_API_HOSTNAME`).
    -   [x] Ajouter les nouveaux chemins d'API pour `swap`, `price`, `tokens`, `trigger`, `recurring` (`JUPITER_SWAP_API_PATH`, etc.).
    -   [x] Ajouter les paramètres de transaction Jupiter (slippage, compute units, priority fees, etc. : `JUPITER_DEFAULT_SLIPPAGE_BPS`, `JUPITER_DYNAMIC_COMPUTE_UNIT_LIMIT`, `JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS`, `JUPITER_PRIORITY_FEE_LEVEL`, `JUPITER_WRAP_AND_UNWRAP_SOL`, `JUPITER_ONLY_DIRECT_ROUTES`, `JUPITER_RESTRICT_INTERMEDIATE_TOKENS`, `JUPITER_SWAP_MODE`).
    -   [x] Marquer les anciennes constantes Jupiter V4/V6 (ex: `JUPITER_API_BASE_URL_LEGACY`, `JUPITER_QUOTE_URL_SUFFIX_LEGACY`) comme "DEPRECATED" ou les commenter.
    -   [x] Revoir et potentiellement marquer comme obsolètes les getters de `Config` pour les URLs Jupiter (ex: `get_jupiter_quote_url`) si `JupiterApiClient` gère la construction des URLs.
    -   [x] `JUPITER_MAX_RETRIES` pour `JupiterApiClient`.
-   [x] **1.1.bis. `requirements.txt`**
    -   [x] Ajouter `jupiter-python-sdk>=0.24.0`.
-   [ ] **1.2. `app/logger.py` (Optionnel - si des configurations spécifiques sont nécessaires pour Jupiter)**
    -   [ ] (À déterminer si des ajustements sont nécessaires)
-   [x] **1.3. `app/utils/jupiter_api_client.py` (Nouveau Client API Jupiter SDK)**
    -   [x] Créer le fichier.
    -   [x] Implémenter `JupiterApiClient` en utilisant `jupiter-python-sdk`.
        -   [x] `__init__`:
            -   [x] Initialiser `Keypair` à partir de `SOLANA_PRIVATE_KEY_BS58` (ou une clé dédiée si configurée).
            -   [x] Initialiser `AsyncClient` de `solana.rpc.async_api`.
            -   [x] Initialiser l'instance `Jupiter` du SDK (`jupiter_python_sdk.jupiter.Jupiter`) avec les URLs de base construites à partir des nouvelles constantes de `Config` (`JUPITER_LITE_API_HOSTNAME`, `JUPITER_PRO_API_HOSTNAME` si clé API Pro).
            -   [x] Gérer la logique pour `JUPITER_PRO_API_HOSTNAME` et la clé API Jupiter si elle est fournie dans `Config`.
        -   [x] `_call_sdk_method(sdk_method_callable, *args, **kwargs)`: Wrapper interne pour les appels SDK avec `tenacity.retry` (utilisant `JUPITER_MAX_RETRIES`). Doit lever `JupiterAPIError` en cas d'échec après les reintentions.
        -   [x] `get_quote(...)`: Implémenter la méthode pour obtenir une quote via le SDK.
            -   [x] Paramètres : `input_mint_str`, `output_mint_str`, `amount_lamports`, `slippage_bps` (optionnel, défaut `Config.JUPITER_DEFAULT_SLIPPAGE_BPS`), `swap_mode` (optionnel, défaut `Config.JUPITER_SWAP_MODE`).
            -   [x] Utiliser les constantes de `Config` pour les paramètres de la requête (`only_direct_routes`, `dynamic_compute_unit_limit`, `compute_unit_price_micro_lamports` / `priority_fee_level`).
            -   [x] Retourner la réponse brute du SDK ou un `Dict` standardisé. Lever `JupiterAPIError` en cas d'échec.
        -   [x] `get_swap_transaction_data(quote_response)`: Implémenter la méthode pour obtenir les données de transaction de swap via le SDK.
            -   [x] Paramètres : `quote_response` (la réponse de `get_quote`), `payer_public_key` (automatiquement `self.keypair.public_key`).
            -   [x] Utiliser les constantes de `Config` pour les paramètres (`wrap_and_unwrap_sol`, etc.).
            -   [x] Retourner un `Dict` standardisé avec `serialized_transaction_b64` et `last_valid_block_height`. Lever `JupiterAPIError` en cas d'échec.
        -   [x] `sign_and_send_transaction(serialized_transaction_b64, last_valid_block_height)`: Implémenter la signature et l'envoi de la transaction.
            -   [x] Décoder `serialized_transaction_b64`.
            -   [x] Désérialiser en `VersionedTransaction`.
            -   [x] Signer la transaction avec `self.keypair`.
            -   [x] Envoyer la transaction via `AsyncClient.send_transaction` avec `TxOpts(skip_preflight=True, last_valid_block_height=...)`.
            -   [x] Confirmer la transaction avec `AsyncClient.confirm_transaction`.
            -   [x] Gérer `TransactionExpiredBlockheightExceededError` (lever `TransactionExpiredError` pour que l'appelant (ex: `TradingEngine`) puisse rafraîchir la quote et la tx).
            -   [x] Gérer les autres erreurs (`SendTransactionPreflightFailureError` -> `TransactionSimulationError`, `TimeoutError` -> `TransactionConfirmationError`).
            -   [x] Lever des sous-types de `SolanaTransactionError` appropriés.
            -   [x] Retourner la signature de la transaction (string) en cas de succès.
        -   [x] `get_prices(token_ids_list, vs_token_str)`: Implémenter la récupération des prix. Lever `JupiterAPIError`.
        -   [x] `get_token_info_list(mint_address_list, tag_list)`: Implémenter la récupération des infos de tokens. Lever `JupiterAPIError`.
        -   [x] Méthodes pour les ordres Trigger (Limit Orders) : `create_trigger_order`, `execute_trigger_order` (si applicable), `cancel_trigger_order`, `get_trigger_orders`. Lever `JupiterAPIError`.
        -   [x] Méthodes pour les ordres DCA : `create_dca_plan`, `get_dca_orders`, `close_dca_order`. Lever `JupiterAPIError`.
        -   [x] `close_async_client()`: Pour fermer la session `AsyncClient`.
-   [x] **1.4. `app/market/market_data.py` (Refactor pour Jupiter SDK)**
    -   [x] `MarketDataProvider.__init__`:
        -   [x] Initialiser `JupiterApiClient` (passer la clé privée de `Config`, l'URL RPC, et l'instance `Config`).
    -   [x] Refactoriser `_get_jupiter_price`:
        -   [x] Utiliser `self.jupiter_client.get_prices()`.
        -   [x] Adapter la réponse du SDK au format attendu par `get_token_price`.
        -   [x] Gérer `JupiterAPIError` et retourner le dict `{'success': False, ...}`.
    -   [x] Refactoriser `_get_jupiter_token_info`:
        -   [x] Utiliser `self.jupiter_client.get_token_info_list()`.
        -   [x] Adapter la réponse du SDK, s'assurer que les `decimals` sont prioritaires.
        -   [x] Gérer `JupiterAPIError` et retourner le dict `{'success': False, ...}`.
    -   [x] Refactoriser `get_jupiter_swap_quote`:
        -   [x] Doit accepter `amount_in_tokens` (float, ex: 0.1 SOL) au lieu de `amount_lamports`.
        -   [x] Appeler `self.get_token_info()` pour obtenir les décimales du token d'entrée.
        -   [x] Calculer `amount_lamports` à partir de `amount_in_tokens` et des décimales.
        -   [x] Appeler `self.jupiter_client.get_quote()` avec les paramètres corrects.
        -   [x] Retourner la réponse brute du SDK dans le champ `data` du dictionnaire standard.
        -   [x] Gérer `JupiterAPIError` et retourner le dict `{'success': False, ...}`.
    -   [ ] Supprimer les anciennes méthodes `_fetch_jupiter_quote_v6`, `_fetch_jupiter_price_v4`, `_convert_jupiter_format` (basées sur `aiohttp`).
-   [x] **1.5. Gestion des Erreurs (Améliorations Initiales)**
    -   [x] `app/utils/exceptions.py`:
        -   [x] Définir une hiérarchie d'exceptions custom: `NumerusXBaseError`, `APIError` (avec `api_name`, `status_code`), `JupiterAPIError`, `DexScreenerAPIError`, `GeminiAPIError`.
        -   [x] Définir `TradingError`, `SwapExecutionError`, `OrderPlacementError`.
        -   [x] Définir `SolanaTransactionError` (avec `signature`), et ses sous-types : `TransactionSimulationError`, `TransactionBroadcastError`, `TransactionConfirmationError`, `TransactionExpiredError`.
    -   [x] `app/utils/jupiter_api_client.py`:
        -   [x] `_call_sdk_method`: Doit attraper les exceptions du SDK et les encapsuler dans `JupiterAPIError` (avec `original_exception`).
        -   [x] `sign_and_send_transaction`: Doit lever `TransactionExpiredError`, `TransactionSimulationError`, `TransactionBroadcastError`, `TransactionConfirmationError` (avec la signature si disponible).
        -   [x] Les autres méthodes (`get_quote`, `get_swap_transaction_data`, `get_prices`, etc.) doivent propager ou lever `JupiterAPIError`.
        -   [x] Mettre à jour les types de retour des méthodes pour refléter qu'elles retournent directement les données du SDK ou lèvent des exceptions (plutôt que des dicts `{'success': ...}`).
    -   [x] `app/market/market_data.py`:
        -   [x] Les méthodes appelant `JupiterApiClient` (ex: `_get_jupiter_price`, `get_jupiter_swap_quote`) doivent attraper `JupiterAPIError` et retourner le dictionnaire standard `{'success': False, 'error': str(e), 'data': None, 'details': e}`.
        -   [x] Les appels `aiohttp` directs (ex: pour DexScreener) doivent lever `DexScreenerAPIError` en cas d'échec.
        -   [x] `get_token_price` et `get_token_info`: Mettre à jour pour attraper ces nouvelles exceptions custom et agréger les messages d'erreur de manière appropriée.
-   [🚧] **1.6. `app/trading/trading_engine.py` (Robustification et Intégration Jupiter SDK)**
    -   [🚧] `TradingEngine.__init__`:
        -   [🚧] Initialiser `Config`.
        -   [🚧] Initialiser `JupiterApiClient` (passer la clé privée `config.SOLANA_PRIVATE_KEY_BS58`, l'URL RPC, et `config`).
        -   [🚧] `MarketDataProvider` peut être initialisé à `None` ici et instancié dans `__aenter__`.
    -   [🚧] `TradingEngine.__aenter__` / `__aexit__`:
        -   [🚧] Gérer l'instanciation de `MarketDataProvider` dans `__aenter__`.
        -   [🚧] Gérer l'appel à `self.jupiter_client.close_async_client()` dans `__aexit__`.
    -   [🚧] Nouvelle méthode privée `_execute_swap_attempt(input_token_mint, output_token_mint, amount_in_tokens_float, slippage_bps)`:
        -   [🚧] Contient la logique de base du swap : `market_data_provider.get_jupiter_swap_quote`, `jupiter_client.get_swap_transaction_data`, `jupiter_client.sign_and_send_transaction`.
        -   [🚧] Doit retourner la signature de la transaction (string) ou lever des exceptions (`JupiterAPIError`, `SolanaTransactionError` sous-types).
        -   [🚧] Décorer avec `tenacity.retry` pour réessayer spécifiquement en cas de `TransactionExpiredError` (en utilisant `Config.JUPITER_MAX_RETRIES`).
    -   [🚧] `TradingEngine.execute_swap` (méthode publique):
        -   [🚧] Gérer la conversion USD -> montant en tokens si `amount_in_usd` est fourni (utiliser `MarketDataProvider.get_token_price`).
        -   [🚧] Appeler `_execute_swap_attempt` dans un bloc `try...except`.
        -   [🚧] Attraper `TransactionExpiredError` (après les reintentions de `_execute_swap_attempt`), `JupiterAPIError`, `SolanaTransactionError` (et ses sous-types), et d'autres `NumerusXBaseError` ou exceptions génériques.
        -   [🚧] Formater le dictionnaire final `{'success': ..., 'error': ..., 'signature': ..., 'details': ...}`.
        -   [🚧] Appeler `_record_transaction` avec le résultat.
    -   [🚧] Revoir et marquer comme obsolètes les anciennes méthodes `_get_swap_routes`, `_select_best_quote`, `_build_swap_transaction`, `_execute_transaction`, `_execute_fallback_swap`, `_make_jupiter_api_request` qui effectuaient des appels `aiohttp` directs à l'API Jupiter. Certaines logiques de sélection ou de préparation pourraient être réutilisées ou adaptées si le SDK ne les couvre pas entièrement. *(Note: Tooling issues prevented direct commenting/removal of these methods. They have been identified as obsolete.)*
-   [x] **1.7. `app/dex_bot.py` (Ajustements Initiaux)**
    -   [x] (À déterminer si des ajustements sont nécessaires à ce stade, probablement minimes. La logique principale de trading sera revue en Phase 4). *(Note: Initial review suggests minimal changes currently needed due to existing abstractions. Deeper integration testing may reveal further needs.)*
-   [x] **1.8. Fiabilisation de la Base de Données (`app/database.py`)**
    -   [x] Ajouter les champs suivants à la table `trades` (avec migration pour tables existantes) :
        -   [x] `jupiter_quote_response` (TEXT, stockera la réponse JSON de la quote)
        -   [x] `jupiter_transaction_data` (TEXT, stockera la réponse JSON de la transaction de swap avant envoi)
        -   [x] `slippage_bps` (INTEGER)
        -   [x] `transaction_signature` (TEXT, explicite pour la signature on-chain)
        -   [x] `last_valid_block_height` (INTEGER)
    -   [x] Mettre à jour `EnhancedDatabase.record_trade` pour accepter et stocker ces nouveaux champs.
    -   [x] Mettre à jour `EnhancedDatabase.get_active_trades` (et autres méthodes de lecture si nécessaire) pour inclure ces champs.
-   [ ] **1.9. Tests Unitaires et d'Intégration (Initiaux)**
    -   [ ] `tests/test_config.py`: Vérifier le chargement des nouvelles constantes Jupiter.
    -   [ ] `tests/test_jupiter_api_client.py`: (Nouveau) Tests pour `JupiterApiClient` (mock des appels SDK et RPC).
        -   [ ] Tester `get_quote`, `get_swap_transaction_data`, `sign_and_send_transaction` (cas succès et erreurs).
        -   [ ] Tester la gestion des erreurs et la levée des exceptions custom.
    -   [ ] `tests/test_market_data.py`: Mettre à jour pour mocker `JupiterApiClient` et tester les méthodes refactorisées.
    -   [ ] `tests/test_trading_engine.py`: Mettre à jour pour mocker `JupiterApiClient` et `MarketDataProvider`, tester `execute_swap` (succès, erreurs API, erreurs de transaction).
    -   [ ] `tests/test_database.py`: Vérifier l'enregistrement et la lecture des nouveaux champs de trade.

## Phase 1.bis: Configuration pour Nouvelle UI React et Backend

- [ ] **1.10. `app/main.py` (Backend FastAPI - Modifications pour UI)**
    - [ ] **1.10.1. Intégration Socket.io (FastAPI)**:
        - [ ] Ajouter `python-socketio` et `uvicorn[standard]` (si pas déjà là pour WebSockets) à `requirements.txt`.
        - [ ] Configurer `SocketManager` dans FastAPI.
        - [ ] Implémenter des namespaces et événements Socket.io de base pour envoyer des données en temps réel à l'UI React (ex: mises à jour de l'état du bot, P&L, logs, décisions IA, santé des systèmes).
        - [ ] Définir des événements pour recevoir des commandes de l'UI (ex: Start/Stop Bot, ajustement des paramètres de stratégie).
    - [ ] **1.10.2. Endpoints API pour Authentification (Clerk/Auth0)**:
        - [ ] Si Clerk/Auth0 nécessite des endpoints backend pour la validation de token ou la synchronisation des utilisateurs, les implémenter.
        - [ ] Sécuriser les endpoints FastAPI et les connexions Socket.io en utilisant les tokens JWT de Clerk/Auth0.
    - [ ] **1.10.3. Endpoints API pour Configuration UI**:
        - [ ] Créer des endpoints pour que l'UI React puisse lire/écrire les configurations du bot stockées dans `app/config.py` (via des méthodes de `Config` qui lisent/écrivent dans un fichier de config utilisateur ou `.env`).
    - [ ] **1.10.4. Servir l'Application React (Optionnel, si pas géré par Nginx dans Docker)**:
        - [ ] Configurer FastAPI pour servir les fichiers statiques de l'application React buildée si une solution Nginx dédiée n'est pas utilisée en production.
- [ ] **1.11. `requirements.txt` (Ajouts pour Backend UI)**
    - [ ] Ajouter `python-socketio`.
    - [ ] Ajouter `python-jose[cryptography]` et `passlib[bcrypt]` pour la gestion JWT si Clerk/Auth0 en a besoin côté backend ou si une authentification locale est envisagée en complément.
    - [ ] Ajouter `fastapi-limiter` pour la limitation de taux sur les API.
- [ ] **1.12. `Docker/` (Mises à Jour pour UI React)**
    - [ ] **1.12.1. `Docker/frontend/Dockerfile` (Nouveau)**:
        - [ ] Créer un `Dockerfile` pour l'application React (`numerusx-ui/`).
        - [ ] Utiliser une multi-stage build:
            -   Stage 1: Node.js pour installer les dépendances (`npm install`) et builder l'application React (`npm run build`).
            -   Stage 2: Nginx (ou un autre serveur web léger) pour servir les fichiers statiques générés par le build React.
        - [ ] S'assurer que les variables d'environnement nécessaires à l'UI React (ex: URL du backend API/Socket.io) peuvent être configurées au moment du build ou du run.
    - [ ] **1.12.2. `docker-compose.yml` (Mise à Jour)**:
        - [ ] Ajouter un nouveau service `frontend` basé sur `Docker/frontend/Dockerfile`.
        - [ ] Configurer le port mapping pour le service frontend (ex: `80:80` ou `3000:80`).
        - [ ] S'assurer que le service backend (`app`) est accessible depuis le service frontend (gestion des réseaux Docker).
        - [ ] Mettre en place des volumes pour le développement local si nécessaire (ex: monter le code source de React pour le hot-reloading avec Vite pendant le dev, différent du build de prod).
    - [ ] **1.12.3. `Docker/backend/Dockerfile` ou `Dockerfile` racine (Ajustements)**:
        - [ ] Vérifier que le backend FastAPI expose correctement le port pour l'API et Socket.io.
        - [ ] S'assurer que les variables d'environnement pour la communication avec le frontend sont gérées.
- [ ] **1.13. Suppression de `app/dashboard.py` et `app/gui.py`**
    - [ ] Supprimer ces fichiers car l'UI est maintenant gérée par l'application React externe.

## Phase 2: Développement du Cœur Agentique IA et Intégrations 🧠🤖

L'objectif principal de cette phase est de construire l'Agent IA central et de réorienter les modules existants pour l'alimenter.

### 2.1. Conception et Implémentation de l'Agent IA (`app/ai_agent.py`)
- [ ] **Tâche**: Créer la classe `AIAgent` dans `app/ai_agent.py`.
- [ ] **Détails**:
    - [ ] Définir la structure de base de `AIAgent`.
    - [ ] Implémenter la méthode principale de prise de décision (ex: `decide_trade(self, aggregated_inputs: Dict) -> Dict`).
        - [ ] `aggregated_inputs` contiendra toutes les données de `MarketDataProvider`, `PredictionEngine`, signaux des stratégies, `RiskManager`, `SecurityChecker`, `PortfolioManager`.
        - [ ] L'output sera un dictionnaire structuré représentant l'ordre final (action, paire, montant, SL/TP, type d'ordre) ou une décision de non-action, incluant un "raisonnement".
    - [ ] Initialiser avec `Config`.
    - [ ] Mettre en place une journalisation détaillée des inputs reçus et des décisions prises par l'agent.
- [ ] **Fichiers concernés**: `app/ai_agent.py` (nouveau), `app/config.py`.

### 2.2. Refactorisation de `app/dex_bot.py` en Orchestrateur de Flux pour l'Agent IA
- [🚧] **Tâche**: Modifier `DexBot` pour qu'il collecte les données et les transmette à l'`AIAgent`, puis exécute la décision de l'Agent.
- [x] **Détails**:
    - [x] `DexBot` initialise `AIAgent`.
    - [x] La méthode `_run_cycle` (ou équivalent) doit :
        - [x] Collecter les données de `MarketDataProvider`.
        - [x] Obtenir les analyses/signaux de `StrategySelector` (qui fournit les outputs des stratégies de `app/strategies/` et `app/analytics_engine.py`).
        - [x] Obtenir les prédictions de `PredictionEngine`.
        - [x] Obtenir les contraintes de `RiskManager`, `SecurityChecker`, et l'état de `PortfolioManager`.
        - [x] Agréger tous ces inputs dans un format structuré.
        - [x] Appeler `self.ai_agent.decide_trade(aggregated_inputs)`.
        - [x] Si l'agent retourne un ordre, le transmettre à `TradeExecutor` (qui utilisera `TradingEngine` avec le nouveau `JupiterApiClient`).
        - [x] Journaliser la décision et le raisonnement de l'agent.
    - [x] Supprimer l'ancienne logique de `_analyze_and_generate_signals` et `_execute_signals` qui prenait des décisions directes.
- [ ] **Détails (Jupiter Ordres Avancés)**:
    - [ ] Si l'Agent IA décide de placer des ordres limités ou DCA, `DexBot` (ou `AIAgent` lui-même) doit pouvoir construire les `params_dict` nécessaires et initier ces actions via les nouvelles méthodes de `TradingEngine` (ex: `place_limit_order`, `create_dca_plan`).
- [x] **Fichiers concernés**: `app/dex_bot.py`, `app/ai_agent.py`.

### 2.3. Adaptation des Modules Fournisseurs d'Inputs pour l'Agent IA
- [🚧] **Tâche**: S'assurer que `StrategyFramework`, `PredictionEngine`, `RiskManager`, `SecurityChecker` et `PortfolioManager` fournissent leurs informations dans un format consommable par `DexBot` pour l'`AIAgent`.
- [x] **Détails**:
    - [x] **`StrategyFramework` et `app/strategies/*`, `app/analytics_engine.py`**: Leurs méthodes `analyze` et `generate_signal` retournent des données structurées (features, scores, indicateurs) plutôt que des décisions de trade directes. Ces données deviennent des inputs pour l'`AIAgent`.
    - [x] **`PredictionEngine`**: Les prédictions (prix, régime, sentiment) sont formatées pour être facilement intégrées dans les `aggregated_inputs` de l'`AIAgent`.
    - [x] **`RiskManager`**: Fournit des limites de risque, des calculs de taille de position potentielle maximale comme contraintes/informations.
    - [x] **`SecurityChecker`**: Fournit des scores/alertes de sécurité.
    - [x] **`PortfolioManager`**: Fournit l'état actuel du portefeuille.
- [ ] **Détails (Compatibilité Jupiter)**:
    - [ ] Vérifier la compatibilité des formats de données retournés par `MarketDataProvider` (maintenant enrichi par `JupiterApiClient` pour les prix, infos tokens, quotes) avec les modules d'analyse (`analytics_engine.py`, stratégies) et l'Agent IA. Les décimales des tokens, par exemple, sont cruciales.
- [x] **Fichiers concernés**: `app/strategy_framework.py`, `app/strategies/*`, `app/analytics_engine.py`, `app/prediction_engine.py`, `app/risk_manager.py`, `app/security/security.py`, `app/portfolio_manager.py`.

### 2.4. Intégration du Raisonnement de l'Agent dans la Base de Données et l'UI
- [ ] **Tâche**: Stocker le "raisonnement" de l'Agent IA et l'afficher dans le dashboard.
- [ ] **Détails**:
    - [ ] Modifier `EnhancedDatabase` pour avoir une table ou une colonne pour stocker les logs de décision de l'Agent IA (inputs clés considérés, logique appliquée, score de confiance, décision finale).
    - [ ] `DexBot` enregistre ce raisonnement après chaque décision de l'`AIAgent`.
    - [ ] **`app/dashboard.py`**: (Toutes les fonctionnalités UI sont détaillées dans `todo/01-todo-ui.md`)
        - [ ] ~~Ajouter une section dans la vue "Trading Activity" ou une nouvelle vue "AI Agent Insights" pour afficher le raisonnement derrière chaque trade (ou décision de ne pas trader).~~ (Voir `todo/01-todo-ui.md`)
        - [ ] ~~Afficher l'état actuel de l'Agent IA (ex: "Monitoring", "Processing Inputs", "Decision Made").~~ (Voir `todo/01-todo-ui.md`)
- [ ] **Fichiers concernés**: `app/database.py`, `app/dex_bot.py`, `app/dashboard.py`, `todo/01-todo-ui.md`.

## Phase 3: Logique de Trading Raffinée et Améliorations du Bot (Post-Agent IA) ⚙️

### 3.1. Amélioration des Inputs pour l'Agent IA (Anciennement Intégration Moteur Prédiction)
- [🚧] **Tâche**: Assurer que `prediction_engine.py` fournit des inputs de haute qualité à l'Agent IA. (Déjà marqué comme fait, mais vérifier pertinence/format pour l'Agent)
- [ ] **Détails**:
    - [ ] L'Agent IA consomme directement les outputs de `prediction_engine`.
- [ ] **Fichiers concernés**: `app/dex_bot.py` (orchestration), `app/prediction_engine.py` (fournisseur), `app/ai_agent.py` (consommateur).

### 3.2. Utilisation des Outputs du `RiskManager` par l'Agent IA (Anciennement Intégration Gestionnaire Risques)
- [🚧] **Tâche**: S'assurer que l'Agent IA utilise les informations de `risk_manager.py`. (Déjà marqué comme fait, mais vérifier l'intégration avec l'Agent)
- [ ] **Détails**:
    - [ ] `RiskManager.calculate_position_size()` peut être appelé par l'Agent IA comme une heuristique ou une contrainte.
    - [ ] L'Agent IA reçoit les limites d'exposition, etc., comme inputs.
- [ ] **Fichiers concernés**: `app/dex_bot.py` (orchestration), `app/risk_manager.py` (fournisseur), `app/ai_agent.py` (consommateur).

### 3.3. Logique d'Exécution et Suivi Post-Décision de l'Agent IA (`app/trade_executor.py`)
- [🚧] **Tâche**: Assurer une exécution et un suivi robustes des ordres de l'Agent IA via `TradingEngine` (utilisant `JupiterApiClient`).
- [x] **Détails**:
    - [x] `TradeExecutor` gère l'exécution des ordres de l'Agent IA, en appelant les méthodes appropriées de `TradingEngine` (ex: `execute_swap`, et les nouvelles `place_limit_order`, `create_dca_plan`).
    - [x] S'assurer que `TradeExecutor.execute_agent_order` est compatible avec les signatures de méthodes mises à jour de `TradingEngine` et peut passer les `params_dict` pour les ordres limités/DCA.
    - [x] `PortfolioManager` suit les positions résultantes.
    - [ ] La gestion des erreurs et reintentions spécifiques aux trades doit informer l'Agent IA pour d'éventuels ajustements futurs.
- [x] **Fichiers concernés**: `app/trade_executor.py`, `app/portfolio_manager.py`, `app/ai_agent.py`, `app/trading/trading_engine.py`.

## Phase 4: Interface Utilisateur et Fonctionnalités Avancées (Post-Agent IA) ✨

Cette phase vise à enrichir l'expérience utilisateur et à introduire des capacités de trading plus sophistiquées.

### 4.1. Amélioration de l'Interface Utilisateur (`app/dashboard.py`, `app/gui.py`)
- [ ] **Tâche**: Développer un tableau de bord complet et réactif. (Détails complets et suivi dans `todo/01-todo-ui.md`)
- [x] **Détails**:
    - [x] S'inspirer de la structure proposée dans `todo.md` (et `todo-front.md`) pour `dashboard.py` (Portfolio Overview, Trading Activity, Market Analysis, Control Center, System Monitoring, Settings).
    - [x] Utiliser `asyncio` pour les mises à jour en temps réel des données (solde, positions, graphiques).
    - [x] Afficher une estimation des frais de transaction avant l'exécution manuelle d'un trade (UI placeholder).
    - [x] Mettre en place un suivi en direct du statut des transactions (UI placeholder pour détails, trades table montre statut BD).
    - [x] Visualiser les métriques de performance du bot (ROI, win rate, Sharpe, etc.) (Partiellement via graphiques et stats).
    - [x] Fournir une vue détaillée du portefeuille (actifs détenus, valeur actuelle, P&L non réalisé) (Partiellement via graphiques et tables placeholders).
- [ ] **Détails (Jupiter Ordres Avancés)**: (Couvert dans `todo/01-todo-ui.md`)
    - [ ] ~~Ajouter des sections à l'UI pour afficher, créer, et gérer (annuler) les ordres limités et les plans DCA.~~
    - [ ] ~~Visualiser le statut des ordres limités et des plans DCA actifs (ex: prochain cycle DCA, ordres limités en attente).~~
- [x] **Fichiers concernés**: `app/dashboard.py` (amélioré), `app/gui.py` (considéré comme base ou obsolète si `dashboard.py` est principal), `todo/01-todo-ui.md`.

### 4.2. Implémentation de Stratégies de Trading Novatrices
- [x] **Tâche**: Développer et intégrer plusieurs archétypes de stratégies.
- [x] **Détails**:
    - [x] **Framework de Stratégie (`BaseStrategy`)**: Définir une classe `BaseStrategy` dans `app/strategy_framework.py` avec des méthodes communes (`analyze`, `generate_signal`, `get_parameters`, `get_name`).
    - [x] **Stratégie de Momentum (`MomentumStrategy`)**: Créer `app/strategies/momentum_strategy.py`. Implémenter une stratégie basée sur RSI et MACD.
    - [x] **Stratégie de Mean Reversion (`MeanReversionStrategy`)**: Créer `app/strategies/mean_reversion_strategy.py`. Implémenter une stratégie basée sur les Bandes de Bollinger.
    - [x] **Système de sélection de stratégie (`StrategySelector`)**: Développer une classe `StrategySelector` dans `app/strategy_selector.py`. Permettre à `DexBot` d'utiliser différentes stratégies (via `StrategySelector`) en fonction des conditions de marché ou d'une configuration. Initialement, implémenter une sélection simple (ex: par défaut ou via `Config`). (DONE: Selector created, DexBot uses it for default strategy from Config)
    - [x] **Stratégie de Suivi de Tendance (`TrendFollowingStrategy`)**: Créer `app/strategies/trend_following_strategy.py`. Utiliser des moyennes mobiles (EMA, SMA) et potentiellement ADX.
    - [x] **Intégration et tests initiaux**: S'assurer que `DexBot` peut charger et exécuter ces stratégies. Mettre à jour `AdvancedTradingStrategy` pour qu'elle hérite de `BaseStrategy` et s'intègre dans ce framework. (DONE for Advanced, Momentum, MeanReversion, TrendFollowing; DexBot loads default via Selector)
- [x] **Fichiers concernés**: `app/strategy_framework.py`, `app/strategies/`, `app/dex_bot.py`, `app/config.py`, `app/strategy_selector.py`.

### 4.3. Boucle de Confirmation par IA pour les Trades (OBSOLETE/REMPLACÉ PAR AGENT IA CENTRAL)
- [ ] **Tâche**: ~~Intégrer une étape finale de validation par une IA rapide avant l'exécution d'un trade.~~
- [ ] **Détails**: L'Agent IA est maintenant le décideur central. Ce concept est fusionné dans la logique de l'`AIAgent`.

## Phase 5: Développement du Moteur de Prédiction Avancé (`prediction_engine.py` en tant que Fournisseur pour l'Agent IA)

Cette phase se concentre sur la création d'un moteur de prédiction intelligent et adaptatif.

### 5.1. Classification des Régimes de Marché
- [ ] **Tâche**: Implémenter `MarketRegimeClassifier`.
- [ ] **Détails**:
    - [ ] Utiliser des indicateurs comme l'ADX (pour la force de la tendance), la largeur des Bandes de Bollinger (pour la volatilité) et le RSI (pour le momentum) pour classifier le marché en "trending", "ranging", ou "volatile".
    - [ ] Permettre au `PricePredictor` de sélectionner différents modèles ou stratégies en fonction du régime détecté.

### 5.2. Entraînement et Prédiction de Modèles ML
- [ ] **Tâche**: Implémenter `PricePredictor`.
- [ ] **Détails**:
    - [ ] **Caractéristiques (Features)**: Utiliser des données OHLCV historiques, des indicateurs techniques (RSI, MACD, BB, volume Z-score, changements de prix) et potentiellement des données de sentiment.
    - [ ] **Modèles**: Commencer avec `RandomForestRegressor` ou `GradientBoostingRegressor` de `scikit-learn`. Envisager `PyTorch` pour des modèles plus complexes (LSTM, Transformers) ultérieurement.
    - [ ] **Normalisation**: Utiliser `StandardScaler` pour normaliser les features.
    - [ ] **Entraînement**:\
        - [ ] Implémenter `train_model` pour entraîner sur les données historiques.\
        - [ ] Utiliser un découpage train/test (ex: 70/30) et envisager une validation croisée de type "walk-forward" pour les séries temporelles.\
        - [ ] Sauvegarder les modèles entraînés (ex: avec `joblib`) et les scalers associés.
    - [ ] **Prédiction**: Implémenter `predict_price` pour faire des prédictions sur de nouvelles données.
    - [ ] **Gestion des modèles**: Charger les modèles existants au démarrage.

### 5.3. Analyse de Sentiment
- [ ] **Tâche**: Implémenter `SentimentAnalyzer`.
- [ ] **Détails**:
    - [ ] Intégrer des API pour récupérer des données de Twitter, Discord, Reddit (peut nécessiter des packages/API externes).
    - [ ] Utiliser des techniques NLP basiques (ex: VADER, TextBlob) ou des modèles de sentiment plus avancés si possible.
    - [ ] Agréger les scores de sentiment des différentes sources, en pondérant potentiellement par le volume de mentions ou la crédibilité de la source.
    - [ ] Mettre en cache les résultats de sentiment pour éviter des appels API excessifs.

### 5.4. Apprentissage par Renforcement (RL)
- [ ] **Tâche**: Implémenter `ReinforcementLearner`.
- [ ] **Détails**:
    - [ ] Définir l'espace d'états (ex: métriques de performance récentes, volatilité du marché).
    - [ ] Définir l'espace d'actions (ex: ajustements des paramètres de la stratégie principale ou des seuils de risque).
    - [ ] Concevoir une fonction de récompense (ex: basée sur le ROI, le Sharpe ratio, la réduction du drawdown).
    - [ ] Utiliser un algorithme RL simple (ex: Q-learning pour des espaces discrets) ou une librairie RL (ex: Stable Baselines3) pour des optimisations plus complexes.
    - [ ] Mettre à jour périodiquement les paramètres de la stratégie en fonction des "actions" suggérées par l'agent RL.

### 5.5. Réentraînement Automatique
- [ ] **Tâche**: Mettre en place un mécanisme de réentraînement périodique des modèles ML.
- [ ] **Détails**:
    - [ ] Déclencher le réentraînement en fonction de métriques de performance (ex: si le win rate d'un modèle chute sous un seuil) ou sur une base temporelle (ex: chaque semaine).
    - [ ] Utiliser les données de trading les plus récentes pour affiner les modèles.
    - [ ] Journaliser les performances des modèles avant et après réentraînement.

## Phase 6: Tests, Déploiement et Monitoring Continus (Centré sur l'Agent IA) 🚀

### 6.1. Tests Unitaires et d'Intégration Approfondis
- [ ] **Tâche**: Écrire des tests pour chaque module et pour les interactions entre modules.
- [ ] **Détails**:
    - [ ] Utiliser `pytest` ou `unittest`.
    - [ ] Simuler les réponses API pour tester la logique de `market_data.py` et `trading_engine.py`.
    - [ ] Tester les cas limites et les scénarios d'erreur.

### 6.2. Configuration du Déploiement Docker
- [ ] **Tâche**: Optimiser et sécuriser la configuration Docker.
- [ ] **Détails**:
    - [ ] S'assurer que `docker-compose.yml` est configuré pour différents environnements (dev, prod) si nécessaire.
    - [ ] Gérer les secrets (clés API, clés de portefeuille) de manière sécurisée en production (ex: via les secrets Docker ou des variables d'environnement injectées).
    - [ ] Optimiser la taille de l'image Docker.

### 6.3. Monitoring et Alerting
- [ ] **Tâche**: Mettre en place un système de monitoring et d'alerting.
- [ ] **Détails**:
    - [ ] Journaliser les métriques clés de performance (ROI, erreurs, latence des transactions) dans un format structuré.
    - [ ] Configurer des alertes (ex: via email, Telegram, Discord) pour les erreurs critiques, les drawdowns importants, ou les échecs de transaction répétés.

### 6.4. Centralisation de l'État des Erreurs des Services (Nouveau)
- [ ] **Tâche**: Mettre en place un mécanisme pour centraliser et exposer l'état de santé et les erreurs des services clés.
- [ ] **Objectif**: Permettre à l'UI et à d'autres systèmes de monitoring d'obtenir une vue claire et actualisée des erreurs par composant.
- [ ] **Détails**:
    - [ ] Définir une structure standard pour les rapports d'état des services (ex: `{'service_name': 'MarketDataProvider', 'status': 'ERROR', 'last_error_message': 'API rate limit exceeded', 'timestamp': ...}`).
    - [ ] Chaque service majeur (`MarketDataProvider`, `TradingEngine`, `AIAgent`, `Database`, `JupiterApiClient`) devra pouvoir rapporter son état et ses erreurs récentes à un point central.
    - [ ] Ce point central (potentiellement une nouvelle classe `ServiceHealthMonitor` ou une responsabilité de `DexBot`) agrégera ces informations.
    - [ ] Exposer ces informations agrégées (par exemple, via une méthode que `DexBot` rend accessible ou un simple état interne) pour que l'UI puisse les interroger et alimenter le panneau "System Health & Operations".
- [ ] **Fichiers concernés**: `app/dex_bot.py` (potentiellement), `app/market/market_data.py`, `app/trading/trading_engine.py`, `app/ai_agent.py`, `app/utils/jupiter_api_client.py`, `app/database.py`, (potentiellement nouveau `app/service_health_monitor.py`).

Rappels pour l'IA:
- **Prioriser la robustesse**: L'Agent IA doit gérer des inputs variés et potentiellement manquants.
- **Modularité**: L'Agent IA doit pouvoir intégrer de nouvelles sources d'input facilement.
- **Journalisation Détaillée**: Les décisions de l'Agent IA DOIVENT être traçables.
- **Sécurité Avant Tout**: Protéger les clés API et les fonds.
- **Tests Continus**: Tester l'Agent IA avec des scénarios d'inputs variés.

## Phase 7: Intégration Jupiter API v6 (Détaillée)

Cette phase détaille l'intégration spécifique de l'API Jupiter V6 en utilisant le `jupiter-python-sdk`. Plusieurs tâches ci-dessus ont été marquées pour cette intégration, cette section sert de référence consolidée et de guide pour ces modifications.

### 7.1. Configuration (`app/config.py` et `requirements.txt`)
- [ ] **Référence**: Tâches 1.1 (Jupiter API v6) et 1.1.bis.
- [ ] **Objectif**: S'assurer que toutes les constantes d'URL, les paramètres de transaction pour Jupiter, et la dépendance SDK sont correctement définis.

### 7.2. Client API Jupiter (`app/utils/jupiter_api_client.py`)
- [ ] **Référence**: Tâche 1.3.
- [ ] **Objectif**: Implémenter intégralement `JupiterApiClient` avec toutes les méthodes listées (get_quote, get_swap_transaction_data, sign_and_send_transaction, get_prices, get_token_info_list, create/execute/cancel/get_trigger_order, create/get/close_dca_plan).
- [ ] **Points Clés**:
    - [ ] Utilisation correcte du `jupiter-python-sdk`.
    - [ ] Gestion robuste des erreurs et `tenacity` pour les reintentions (via `_call_sdk_method` wrapper).
    - [ ] Logique de signature correcte pour `VersionedTransaction` avec `solders` et `Keypair`.
    - [ ] Clarification du flux `create_trigger_order` + `execute` pour l'API Trigger v1, et comment le SDK le gère.

### 7.3. Orchestration des Données de Marché (`app/market/market_data.py`)
- [ ] **Référence**: Tâche 1.4 (Jupiter API v6).
- [ ] **Objectif**: Intégrer `JupiterApiClient` dans `MarketDataProvider` pour toutes les opérations liées à Jupiter (prix, infos token, quotes).
- [ ] **Points Clés**:
    - [ ] `MarketDataProvider` initialise et utilise une instance de `JupiterApiClient`.
    - [ ] Les méthodes existantes sont refactorisées pour appeler le client Jupiter.
    - [ ] La conversion `amount_in_tokens` <-> `amount_lamports` est gérée (nécessite les décimales du token, obtenues via `JupiterApiClient`).
    - [ ] Maintien du cache et des mécanismes de fallback.

### 7.4. Moteur d'Exécution des Trades (`app/trading/trading_engine.py`)
- [ ] **Référence**: Tâche 1.6 (Jupiter API v6).
- [ ] **Objectif**: Intégrer `JupiterApiClient` dans `TradingEngine` pour l'exécution des swaps, la gestion des ordres limités et des plans DCA.
- [ ] **Points Clés**:
    - [ ] `TradingEngine` initialise et utilise une instance de `JupiterApiClient`.
    - [ ] Les méthodes de swap (`_get_jupiter_quote`, `_get_jupiter_swap_tx_data`, `_execute_jupiter_transaction`) sont refactorisées et orchestrées par `execute_swap`.
    - [ ] Implémentation des nouvelles méthodes pour les ordres limités et DCA (`place_limit_order`, `create_dca_plan`, etc.).
    - [ ] La gestion des frais de transaction et des paramètres de priorité est conforme aux options du SDK/API v6.

### 7.5. Adaptation des Modules Consommateurs
- [ ] **Référence**: Tâches 2.2 (Jupiter Ordres Avancés), 2.3 (Compatibilité Jupiter), 3.3 (Logique d'Exécution).
- [ ] **Objectif**: S'assurer que `DexBot`, `AIAgent`, `TradeExecutor`, et les modules d'analyse sont compatibles avec les changements introduits par le nouveau client Jupiter.
- [ ] **Points Clés**:
    - [ ] L'Agent IA peut initier des ordres limités/DCA en construisant les `params_dict` pour `TradingEngine`.
    - [ ] `TradeExecutor` interagit correctement avec les nouvelles méthodes de `TradingEngine`.
    - [ ] Les formats de données (notamment prix, décimales) sont cohérents à travers les modules.

### 7.6. Base de Données (`app/database.py`)
- [🚧] **Référence**: Tâche 1.8 (Jupiter Ordres Avancés).
- [x] **Objectif**: Mettre à jour le schéma de la base de données pour stocker les informations relatives aux ordres limités et plans DCA (statut, ID Jupiter, etc.).

### 7.7. Interface Utilisateur (`app/dashboard.py`)
- [ ] **Référence**: Tâche 4.1 (Jupiter Ordres Avancés).
- [ ] **Objectif**: Ajouter des fonctionnalités à l'UI pour créer, afficher et gérer les ordres limités et les plans DCA. (Détails complets et suivi dans `todo/01-todo-ui.md`)

**Considérations Importantes (Rappel de `02-todo-ai-jupiter.md`)**:
* **Signature `VersionedTransaction`**: Crucial. Utiliser `solders`. Référencer les exemples du SDK.
* **API Trigger `createOrder` + `execute`**: Clarifier le flux exact (si la création d'ordre est une tx à signer/envoyer avant l'exécution) basé sur la documentation SDK/API.
* **Documentation SDK**: Se référer constamment à la documentation et aux exemples du `jupiter-python-sdk` pour l'utilisation correcte de ses méthodes et des paramètres attendus.
* **Rate Limits sur `lite-api.jup.ag`**: Bien que non explicitement détaillées partout, supposer des limites plus strictes. Implémenter une gestion d'erreur robuste pour `HTTP 429` (via `tenacity` dans `JupiterApiClient`).
