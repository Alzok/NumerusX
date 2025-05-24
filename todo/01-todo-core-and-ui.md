# NumerusX - IA TODO List 🤖

**Prompt pour l'IA**: Exécute les tâches une par une. Quand tu as terminé une tâche, vérifie la cohérence du code par rapport à l'ensemble du projet et au contexte fourni. Une fois la vérification terminée et la cohérence assurée, passe en autonomie à la tâche suivante.

## Phase 1: Stabilisation et Refactorisation Fondamentale 🧱

L'objectif de cette phase est de s'assurer que le cœur du système est robuste, fiable et exempt d'incohérences.

### 1.1. Gestion Centralisée de la Configuration
- [x] **Tâche**: Finaliser la classe `Config` dans `app/config.py`.
- [x] **Détails**:
    - [x] S'assurer que *tous* les paramètres de configuration (chemins de base de données, clés API, URL d'API, paramètres de trading comme `SLIPPAGE`, `BASE_ASSET`, `MAX_POSITIONS`, `MAX_ORDER_SIZE`, `UPDATE_INTERVAL`, `INITIAL_BALANCE`, `UI_UPDATE_INTERVAL`, etc.) y sont définis.
    - [x] Remplacer toutes les références codées en dur ou les variables d'environnement directes dans l'ensemble du code par des appels à la classe `Config`.
    - [x] Vérifier que le chargement des variables d'environnement via `.env fonctionne correctement avec python-dotenv`.
- [x] **Fichiers concernés**: `app/config.py`, `app/dex_bot.py`, `app/analytics_engine.py`, `app/trading/trading_engine.py`, `app/database.py`, `app/main.py`, `app/api_routes.py`, `app/security/security.py`, `app/market/market_data.py`, `Docker/docker-compose.yml`.

### 1.2. Standardisation des Imports
- [x] **Tâche**: Convertir tous les imports relatifs en imports absolus.
- [x] **Détails**:
    - [x] Exemple: `from .dex_api import DexAPI` devient `from app.dex_api import DexAPI`.
    - [x] Assurer une structure d'import cohérente à travers tous les modules, en particulier dans `app/dex_bot.py` et `app/main.py`.
    - [x] **Note**: L'import `from app.database import db, User, Trade` dans `app/api_routes.py` est structurellement absolu mais les cibles (`db`, `User`, `Trade`) ne sont pas actuellement exportées par `app/database.py`. Cela sera traité dans la Tâche 1.7 ou lors du développement des fonctionnalités API.
- [x] **Fichiers concernés**: Tous les fichiers `.py` du projet.

### 1.3. Refactorisation des Appels API (`app/market/market_data.py`)
- [x] **Tâche**: Centraliser et robustifier la récupération des données de marché.
- [x] **Détails**:
    - [x] Consolider toutes les requêtes de données de marché (actuellement dispersées dans `app/dex_api.py` et potentiellement `app/security/security.py`) dans `app/market/market_data.py`.
    - [x] Implémenter des formats de données standardisés entre les différentes sources d'API (Jupiter, DexScreener).
    - [x] Mettre en place un système de cache robuste (ex: `TTLCache`) pour les réponses API afin de réduire la latence et le nombre d'appels.
    - [x] Développer des mécanismes de repli (fallback) : si une source de données échoue, tenter automatiquement avec une autre.
    - [x] Gérer les limites de taux (rate limiting) des API de manière proactive et gracieuse (ex: `tenacity` pour les reintentions avec backoff exponentiel).
    - [x] S'assurer que la méthode `_prepare_dataframe` dans `app/analytics_engine.py` est flexible et gère correctement les différents formats de réponse API.
- [x] **Fichiers concernés**: `app/market/market_data.py`, `app/dex_api.py`, `app/security/security.py`, `app/analytics_engine.py`.

### 1.4. Amélioration de la Gestion des Erreurs API
- [ ] **Tâche**: Implémenter une gestion des erreurs cohérente et structurée pour tous les appels API.
- [ ] **Détails**:
    - [ ] Chaque appel API doit avoir une gestion d'erreur qui capture les exceptions spécifiques (ex: `requests.RequestException`, erreurs HTTP) et les exceptions génériques.
    - [ ] Les erreurs doivent être journalisées avec suffisamment de contexte (endpoint, paramètres, message d'erreur).
    - [ ] Les réponses d'erreur des API doivent être analysées pour extraire des messages utiles.
    - [ ] Fournir des réponses structurées en cas d'échec (ex: `{'success': False, 'error': 'message', 'data': None}`).
- [ ] **Fichiers concernés**: `app/market/market_data.py`, `app/trading/trading_engine.py`, `app/security/security.py`.

### 1.5. Robustification du Moteur de Trading (`app/trading/trading_engine.py`)
- [ ] **Tâche**: Compléter et fiabiliser les fonctionnalités du moteur de trading.
- [ ] **Détails**:
    - [ ] **Initialisation sécurisée du portefeuille**:
        - [ ] Valider le `wallet_path` et le format de la clé privée.
        - [ ] Gérer les erreurs de chargement de clé de manière robuste (ex: fichier non trouvé, format incorrect).
        - [ ] Implémenter une stratégie de repli (ex: variable d'environnement pour la clé) en cas d'échec du chargement principal.
    - [ ] **Estimation des frais de transaction**:
        - [ ] Intégrer `get_fee_for_message` pour estimer les frais *avant* d'envoyer une transaction.
        - [ ] S'assurer que les frais sont pris en compte dans la logique de décision et de gestion des risques.
    - [ ] **Sélection de la meilleure route de swap**:
        - [ ] Améliorer `_select_best_quote` pour comparer les routes non seulement sur le prix de sortie mais aussi en intégrant les frais de transaction estimés.
    - [ ] **Complétion des méthodes placeholder**:
        - [ ] `_get_swap_routes`: Récupérer les routes de swap disponibles (ex: via Jupiter API).
        - [ ] `_build_swap_transaction`: Construire l'objet transaction Solana à partir de la route choisie.
        - [ ] `_execute_transaction`: Signer et envoyer la transaction au réseau Solana, gérer la confirmation et les erreurs.
        - [ ] `_execute_fallback_swap`: Implémenter un mécanisme de repli si la route principale échoue (ex: essayer une autre route ou un autre DEX).
    - [ ] **Gestion des transactions et erreurs**:
        - [ ] Implémenter une logique de reintentions intelligentes pour les transactions échouées (avec backoff exponentiel), en tenant compte des erreurs Solana spécifiques.
        - [ ] Journaliser en détail chaque étape de la transaction (création, signature, envoi, confirmation, erreur).
- [ ] **Fichiers concernés**: `app/trading/trading_engine.py`, `app/wallet.py`.

### 1.6. Renforcement de la Sécurité (`app/security/security.py`)
- [ ] **Tâche**: Améliorer les mécanismes de validation et de détection des risques.
- [ ] **Détails**:
    - [ ] **Validation d'adresse Solana**:
        - [ ] S'assurer que `validate_solana_address` utilise une regex robuste pour le format Base58 (longueur et caractères).
    - [ ] **Protection contre le rate limiting**:
        - [ ] Intégrer `tenacity` ou un mécanisme similaire pour les appels API externes effectués par ce module.
    - [ ] **Détection de Rug Pull**:
        - [ ] Étendre `_detect_rugpull_patterns` avec des heuristiques plus avancées (ex: analyse de la vélocité des transferts de tokens, comportement des développeurs/gros portefeuilles).
    - [ ] **Analyse de la profondeur de liquidité**:
        - [ ] Compléter `_analyze_liquidity_depth` dans `_get_onchain_metrics` pour évaluer l'impact sur les prix de transactions de différentes tailles et détecter les liquidités "fines" ou manipulées.
    - [ ] **Gestion des erreurs API**:
        - [ ] Robustifier la gestion des erreurs lors des appels API pour la récupération d'informations de sécurité.
    - [ ] **Sécurité des clés et données sensibles**:
        - [ ] Supprimer toute génération de clé de développeur du `Dockerfile`. Utiliser des configurations de développement séparées et des secrets Docker/variables d'environnement pour les clés en production.
        - [ ] S'assurer que la méthode `verify_token` (si elle concerne l'authentification API et non la validation de token crypto) retourne `Tuple[bool, str]` de manière cohérente.
        - [ ] Mettre en œuvre le chiffrement pour *toutes* les données sensibles stockées (clés API, clés privées de portefeuille), par exemple avec `cryptography`.
- [ ] **Fichiers concernés**: `app/security/security.py`, `app/market/market_data.py` (pour les appels sous-jacents), `Dockerfile`.

### 1.7. Fiabilisation de la Base de Données (`app/database.py`)
- [x] **Tâche**: Assurer l'initialisation correcte et les migrations de la base de données.
- [x] **Détails**:
    - [x] Compléter la méthode `_init_db` pour vérifier l'existence des tables *avant* de tenter des migrations ou des créations.
        - [x] Créer le répertoire `data/` si `Config.DB_PATH` le spécifie et qu'il n'existe pas.
        - [x] Gérer la migration de la table `trades` pour ajouter la colonne `protocol` si elle n'existe pas.
        - [x] S'assurer que toutes les tables (`blacklist`, `trades`, `security_incidents`) sont créées avec `IF NOT EXISTS`.
    - [x] Utiliser des transactions SQL pour assurer l'atomicité des opérations complexes.
    - [x] Valider les entrées avant l'insertion pour prévenir les erreurs SQL et les injections basiques.
    - [x] S'assurer que la base de données peut stocker les décisions et raisonnements de l'Agent IA.
- [x] **Fichiers concernés**: `app/database.py`.

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
- [ ] **Tâche**: Modifier `DexBot` pour qu'il collecte les données et les transmette à l'`AIAgent`, puis exécute la décision de l'Agent.
- [ ] **Détails**:
    - [ ] `DexBot` initialise `AIAgent`.
    - [ ] La méthode `_run_cycle` (ou équivalent) doit :
        - [ ] Collecter les données de `MarketDataProvider`.
        - [ ] Obtenir les analyses/signaux de `StrategySelector` (qui fournit les outputs des stratégies de `app/strategies/` et `app/analytics_engine.py`).
        - [ ] Obtenir les prédictions de `PredictionEngine`.
        - [ ] Obtenir les contraintes de `RiskManager`, `SecurityChecker`, et l'état de `PortfolioManager`.
        - [ ] Agréger tous ces inputs dans un format structuré.
        - [ ] Appeler `self.ai_agent.decide_trade(aggregated_inputs)`.
        - [ ] Si l'agent retourne un ordre, le transmettre à `TradeExecutor`.
        - [ ] Journaliser la décision et le raisonnement de l'agent.
    - [ ] Supprimer l'ancienne logique de `_analyze_and_generate_signals` et `_execute_signals` qui prenait des décisions directes.
- [ ] **Fichiers concernés**: `app/dex_bot.py`, `app/ai_agent.py`.

### 2.3. Adaptation des Modules Fournisseurs d'Inputs pour l'Agent IA
- [ ] **Tâche**: S'assurer que `StrategyFramework`, `PredictionEngine`, `RiskManager`, `SecurityChecker` et `PortfolioManager` fournissent leurs informations dans un format consommable par `DexBot` pour l'`AIAgent`.
- [ ] **Détails**:
    - [ ] **`StrategyFramework` et `app/strategies/*`, `app/analytics_engine.py`**: Leurs méthodes `analyze` et `generate_signal` retournent des données structurées (features, scores, indicateurs) plutôt que des décisions de trade directes. Ces données deviennent des inputs pour l'`AIAgent`.
    - [ ] **`PredictionEngine`**: Les prédictions (prix, régime, sentiment) sont formatées pour être facilement intégrées dans les `aggregated_inputs` de l'`AIAgent`.
    - [ ] **`RiskManager`**: Fournit des limites de risque, des calculs de taille de position potentielle maximale comme contraintes/informations.
    - [ ] **`SecurityChecker`**: Fournit des scores/alertes de sécurité.
    - [ ] **`PortfolioManager`**: Fournit l'état actuel du portefeuille.
- [ ] **Fichiers concernés**: `app/strategy_framework.py`, `app/strategies/*`, `app/analytics_engine.py`, `app/prediction_engine.py`, `app/risk_manager.py`, `app/security/security.py`, `app/portfolio_manager.py`.

### 2.4. Intégration du Raisonnement de l'Agent dans la Base de Données et l'UI
- [ ] **Tâche**: Stocker le "raisonnement" de l'Agent IA et l'afficher dans le dashboard.
- [ ] **Détails**:
    - [ ] Modifier `EnhancedDatabase` pour avoir une table ou une colonne pour stocker les logs de décision de l'Agent IA (inputs clés considérés, logique appliquée, score de confiance, décision finale).
    - [ ] `DexBot` enregistre ce raisonnement après chaque décision de l'`AIAgent`.
    - [ ] **`app/dashboard.py`**:
        - [ ] Ajouter une section dans la vue "Trading Activity" ou une nouvelle vue "AI Agent Insights" pour afficher le raisonnement derrière chaque trade (ou décision de ne pas trader).
        - [ ] Afficher l'état actuel de l'Agent IA (ex: "Monitoring", "Processing Inputs", "Decision Made").
- [ ] **Fichiers concernés**: `app/database.py`, `app/dex_bot.py`, `app/dashboard.py`.

## Phase 3: Logique de Trading Raffinée et Améliorations du Bot (Post-Agent IA) ⚙️

### 3.1. Amélioration des Inputs pour l'Agent IA (Anciennement Intégration Moteur Prédiction)
- [x] **Tâche**: Assurer que `prediction_engine.py` fournit des inputs de haute qualité à l'Agent IA. (Déjà marqué comme fait, mais vérifier pertinence/format pour l'Agent)
- [ ] **Détails**:
    - [ ] L'Agent IA consomme directement les outputs de `prediction_engine`.
- [ ] **Fichiers concernés**: `app/dex_bot.py` (orchestration), `app/prediction_engine.py` (fournisseur), `app/ai_agent.py` (consommateur).

### 3.2. Utilisation des Outputs du `RiskManager` par l'Agent IA (Anciennement Intégration Gestionnaire Risques)
- [x] **Tâche**: S'assurer que l'Agent IA utilise les informations de `risk_manager.py`. (Déjà marqué comme fait, mais vérifier l'intégration avec l'Agent)
- [ ] **Détails**:
    - [ ] `RiskManager.calculate_position_size()` peut être appelé par l'Agent IA comme une heuristique ou une contrainte.
    - [ ] L'Agent IA reçoit les limites d'exposition, etc., comme inputs.
- [ ] **Fichiers concernés**: `app/dex_bot.py` (orchestration), `app/risk_manager.py` (fournisseur), `app/ai_agent.py` (consommateur).

### 3.3. Logique d'Exécution et Suivi Post-Décision de l'Agent IA (Anciennement Refactorisation `dex_bot.py`)
- [x] **Tâche**: Assurer une exécution et un suivi robustes des ordres de l'Agent IA.
- [ ] **Détails**:
    - [x] `TradeExecutor` gère l'exécution des ordres de l'Agent IA.
    - [x] `PortfolioManager` suit les positions résultantes.
    - [ ] La gestion des erreurs et reintentions spécifiques aux trades doit informer l'Agent IA pour d'éventuels ajustements futurs.
- [ ] **Fichiers concernés**: `app/trade_executor.py`, `app/portfolio_manager.py`, `app/ai_agent.py`.

## Phase 4: Interface Utilisateur et Fonctionnalités Avancées (Post-Agent IA) ✨

Cette phase vise à enrichir l'expérience utilisateur et à introduire des capacités de trading plus sophistiquées.

### 4.1. Amélioration de l'Interface Utilisateur (`app/dashboard.py`, `app/gui.py`)
- [x] **Tâche**: Développer un tableau de bord complet et réactif.
- [x] **Détails**:
    - [x] S'inspirer de la structure proposée dans `todo.md` (et `todo-front.md`) pour `dashboard.py` (Portfolio Overview, Trading Activity, Market Analysis, Control Center, System Monitoring, Settings).
    - [x] Utiliser `asyncio` pour les mises à jour en temps réel des données (solde, positions, graphiques).
    - [x] Afficher une estimation des frais de transaction avant l'exécution manuelle d'un trade (UI placeholder).
    - [x] Mettre en place un suivi en direct du statut des transactions (UI placeholder pour détails, trades table montre statut BD).
    - [x] Visualiser les métriques de performance du bot (ROI, win rate, Sharpe, etc.) (Partiellement via graphiques et stats).
    - [x] Fournir une vue détaillée du portefeuille (actifs détenus, valeur actuelle, P&L non réalisé) (Partiellement via graphiques et tables placeholders).
- [x] **Fichiers concernés**: `app/dashboard.py` (amélioré), `app/gui.py` (considéré comme base ou obsolète si `dashboard.py` est principal).

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

Rappels pour l'IA:
- **Prioriser la robustesse**: L'Agent IA doit gérer des inputs variés et potentiellement manquants.
- **Modularité**: L'Agent IA doit pouvoir intégrer de nouvelles sources d'input facilement.
- **Journalisation Détaillée**: Les décisions de l'Agent IA DOIVENT être traçables.
- **Sécurité Avant Tout**: Protéger les clés API et les fonds.
- **Tests Continus**: Tester l'Agent IA avec des scénarios d'inputs variés.

---

# NumerusX - Guide de Développement de l'Interface Utilisateur (UI) pour IA 🎨✨

**Prompt pour l'IA**: En tant qu'IA spécialisée dans le développement d'interfaces, ta mission est de créer une interface utilisateur (UI) **exceptionnelle**, claire, moderne, et minimaliste pour NumerusX. L'UI doit suivre les principes du Material Design (ou un design system moderne équivalent), être hautement interactive, et permettre une gestion intuitive et puissante de l'application. Implémente les fonctionnalités étape par étape en te basant sur le fichier `app/dashboard.py` et `app/gui.py` comme point de départ, et en respectant les besoins définis ci-dessous. Assure-toi de la cohérence avec les fonctionnalités existantes et prévues du bot, et vise une expérience utilisateur (UX) de premier ordre.

## Objectifs Généraux de l'UI:

-   **Contrôle Centralisé et Intuitif**: Démarrer, arrêter, configurer et surveiller le bot avec aisance.
-   **Feedback Dynamique et Compréhensible**: Afficher l'état du bot, les logs, les actions en cours et les "pensées" de l'IA de manière transparente.
-   **Visualisation de Données Avancée**: Présenter les performances, les trades, et l'analyse de marché via des graphiques interactifs, des heatmaps, et des visualisations innovantes.
-   **Esthétique Moderne et Personnalisable**: Interface épurée, élégante, avec des options de personnalisation (thèmes, widgets).
-   **Réactivité et Performance**: L'interface doit être fluide, se mettre à jour dynamiquement sans latence perceptible, et optimisée pour les performances.
-   **Accessibilité (A11y)**: Respecter les standards d'accessibilité (WCAG) pour une utilisation par tous.

## Structure de l'Interface (Basée sur `app/dashboard.py`)

Utiliser `nicegui` comme framework. Le fichier `app/dashboard.py` (`NumerusXDashboard` class) servira de base pour l'implémentation.

### Étape 1: Initialisation et Structure Globale de l'UI (Évolutions)

-   [ ] **Layout Principal Amélioré**:
    -   [ ] Utiliser un layout adaptable (responsive) qui fonctionne bien sur desktop et tablettes.
    -   [ ] Header persistant avec logo, titre, indicateur de statut global du bot (couleur + icône + texte: Ex: "Running Smoothly", "Error Detected", "Paused"), et accès rapide aux notifications et paramètres.
    -   [ ] Barre latérale de navigation principale (collapsible pour gagner de l'espace) avec des icônes claires et des labels pour chaque section.
-   [ ] **Thématisation Dynamique et Personnalisée**:
    -   [ ] Implémenter le sélecteur de thème Light/Dark (déjà listé).
    -   [ ] **Nouveau**: Thème "Accent Performance": La couleur d'accentuation principale de l'UI change subtilement en fonction de la performance récente du bot (ex: vert pour profits, orange pour stagnation, rouge pour pertes).
    -   [ ] **Nouveau**: Permettre à l'utilisateur de choisir une couleur d'accentuation personnalisée.
-   [ ] **Centre de Notifications Amélioré**:
    -   [ ] Un panneau de notifications accessible depuis le header, listant les événements importants (trades, erreurs, alertes de sécurité, complétion de tâches IA) avec timestamps et niveaux de sévérité.
    -   [ ] Possibilité de filtrer les notifications et de les marquer comme lues.
-   [ ] **Mécanisme de Mise à Jour en Temps Réel Optimisé**:
    -   [ ] Utiliser `ui.timer` pour les mises à jour régulières.
    -   [ ] **Nouveau**: Explorer l'utilisation de WebSockets (si `nicegui` le supporte facilement ou via intégration externe) pour des mises à jour instantanées sur certains événements critiques.
-   [ ] **Micro-interactions et Feedback Visuel**:
    -   [ ] Ajouter des indicateurs de chargement subtils pour les sections de données.
    -   [ ] Effets de survol (hover) et animations de transition légères pour une UX plus soignée.

### Étape 2: Panneau "Portfolio Overview" (Refonte et Enrichissement)

-   [ ] **Affichage de la Valeur Totale du Portefeuille (Évolué)**:
    -   [ ] Label principal clair et visible.
    -   [ ] **Nouveau**: "Sparkline" (mini-graphique linéaire) à côté de la valeur totale montrant la tendance sur les dernières heures.
    -   [ ] Variation sur 24h, 7j, 30j (avec sélecteur).
-   [ ] **Graphique d'Allocation d'Actifs Interactif**:
    -   [ ] Utiliser un graphique Plotly de type "Sunburst" ou "Treemap" pour une meilleure visualisation des allocations et sous-allocations (si pertinent).
    -   [ ] Cliquer sur un segment pour voir plus de détails ou filtrer d'autres vues.
    -   [ ] **Nouveau**: "Treemap" avec la taille des tuiles représentant la valeur et la couleur l'intensité du P&L.
-   [ ] **Graphique de Performance du Portefeuille Avancé**:
    -   [ ] Graphique Plotly ligne/aire.
    -   [ ] **Nouveau**: Superposer des événements clés (ex: gros trades, changements de stratégie) sur le graphique.
    -   [ ] **Nouveau**: Comparaison avec un benchmark (ex: BTC/SOL price) ou un portefeuille modèle.
    -   [ ] **Nouveau**: Affichage du "Max Drawdown" et de la "Underwater Equity Curve" (temps passé sous le plus haut historique).
-   [ ] **Tableau des Positions ("Holdings") Détaillé et Interactif**:
    -   [ ] Colonnes: Actif (logo + symbole), Quantité, Prix d'Achat Moyen, Prix Actuel, Valeur Totale, P&L Non Réalisé (montant et %), Variation 24h (%).
    -   [ ] **Nouveau**: Actions par ligne (ex: "Analyser", "Vendre Partiellement", "Définir Alerte de Prix").
-   [ ] **Nouveau: Indicateurs de Risque du Portefeuille**:
    -   [ ] Afficher le Sharpe Ratio, Sortino Ratio, Calmar Ratio calculés.
    -   [ ] Visualisation de la volatilité actuelle du portefeuille.
-   [ ] **Nouveau: Simulateur "What If" Basique**:
    -   [ ] Inputs simples (ex: "Si SOL atteint $X") pour voir l'impact estimé sur la valeur totale du portefeuille.

### Étape 3: Panneau "Trading Activity Center" (Plus Analytique)

-   [ ] **Tableau des Trades Récents Amélioré**:
    -   [ ] **Nouveau**: Inclure le "Slippage" (différence entre prix attendu et exécuté), les "Frais de Transaction", et la "Raison du Trade" (ex: signal de stratégie X, décision IA Y).
    -   [ ] **Nouveau**: Cliquer sur un trade pour ouvrir une vue détaillée (snapshot des indicateurs au moment du trade, rapport de décision LLM si disponible).
-   [ ] **Visualisation du Flux de Trading**:
    -   [ ] **Nouveau**: Graphique Sankey montrant le flux de capital entre différents actifs ou stratégies sur une période.
-   [ ] **Analyse de Performance des Trades**:
    -   [ ] Taux de réussite global et par stratégie/paire.
    -   [ ] Profit Factor.
    -   [ ] Distribution des P&L (histogramme).
    -   [ ] **Nouveau**: Graphique de la durée moyenne des trades gagnants vs perdants.
-   [ ] **Nouveau: "Trade Autopsy" (Analyse Post-Mortem)**:
    -   [ ] Pour les trades perdants significatifs, un bouton "Analyser la Perte" qui pourrait afficher:
        -   Les conditions de marché au moment du trade.
        -   Les signaux des indicateurs et de l'IA.
        -   Les nouvelles ou événements pertinents.
        -   Une évaluation de la décision par l'IA (si le LLM de rapport est en place).

### Étape 4: Panneau "Market Intelligence Hub" (Au-delà de l'Analyse Basique)

-   [ ] **Indicateur Global de Sentiment de Marché**:
    -   [ ] Basé sur l'analyse de `SentimentAnalyzer` (Twitter, etc.) et/ou les prédictions du `MarketRegimeClassifier`.
    -   [ ] Visualisation type "compteur de vitesse" ou barre de progression colorée.
-   [ ] **Watchlist Dynamique et Interactive**:
    -   [ ] Tokens avec signaux forts (BUY/SELL) issus des stratégies et de l'IA.
    -   [ ] **Nouveau**: Afficher les raisons principales du signal (ex: "RSI Survente + Prédiction IA Haussière").
    -   [ ] **Nouveau**: Mini-graphiques de tendance (sparklines) pour chaque token de la watchlist.
    -   [ ] Boutons d'action rapide (ex: "Analyser en Profondeur", "Trader").
-   [ ] **Graphiques de Prix Interactifs avec Superposition d'IA**:
    -   [ ] Graphiques Candlestick (Plotly).
    -   [ ] **Nouveau**: Superposer les prédictions de prix de l'IA (ex: zone de prix future probable).
    -   [ ] **Nouveau**: Afficher les "Rapports de Décision LLM" (feature 4.1 de `02-todo-advanced-features.md`) comme annotations ou pop-ups sur le graphique lorsque l'IA a pris une décision concernant cet actif.
    -   [ ] Outils de dessin basiques (lignes de tendance, supports/résistances).
-   [ ] **Nouveau: Heatmaps de Marché**:
    -   [ ] Heatmap de performance des tokens (ex: Top 20 par volume sur Solana) sur différentes périodes (1h, 24h, 7j).
    -   [ ] Heatmap de corrélation entre les actifs du portefeuille ou de la watchlist.
-   [ ] **Nouveau: Section "AI Insights"**:
    -   [ ] Un flux de "pensées" ou d'observations clés de l'IA (ex: "Détection d'une augmentation anormale du volume sur XYZ", "Le sentiment pour ABC devient fortement positif", "Le modèle de prédiction pour JKL est actuellement peu fiable en raison de la faible liquidité").
    -   [ ] Peut intégrer les sorties des modules IA avancés (MAC-MM, GNN Liquidité de `02-todo-advanced-features.md`).

### Étape 5: Panneau "Command & Control Center" (Plus Granulaire)

-   [ ] **Contrôle du Bot Amélioré**:
    -   [ ] Boutons Start/Stop/Pause clairs.
    -   [ ] **Nouveau**: Mode "Safe" (Trading sur papier uniquement) vs "Live".
    -   [ ] Indicateur visuel du cycle de traitement du bot (ex: une petite barre de progression qui se remplit et se réinitialise à chaque cycle `_run_cycle`).
-   [ ] **Gestion Fine des Stratégies**:
    -   [ ] Sélecteur de stratégie active.
    -   [ ] **Nouveau**: Affichage des paramètres actuels de la stratégie active.
    -   [ ] **Nouveau**: Interface pour ajuster les paramètres clés de la stratégie active *en temps réel* (avec avertissements sur les implications). Les modifications sont envoyées à l'instance de la stratégie via `DexBot`.
    -   [ ] **Nouveau**: Accès rapide pour lancer un backtest de la stratégie active avec les paramètres modifiés (via `BacktestEngine`).
-   [ ] **Formulaire d'Entrée Manuelle de Trade avec Aide à la Décision**:
    -   [ ] **Nouveau**: Affichage du solde disponible pour le token d'entrée.
    -   [ ] **Nouveau**: Estimation de l'impact sur le portefeuille avant exécution.
    -   [ ] **Nouveau**: Indicateur de risque pour le trade manuel proposé (basé sur `RiskManager`).
    -   [ ] Affichage des frais estimés dynamiquement.
-   [ ] **Nouveau: Gestion des Tâches de Fond de l'IA**:
    -   [ ] Visualiser l'état des tâches longues (ex: entraînement de modèles ML, backtests approfondis).
    -   [ ] Boutons pour (si applicable) mettre en pause ou annuler ces tâches.

### Étape 6: Panneau "System Health & Operations" (Plus Détaillé)

-   [ ] **Indicateurs d'État du Bot et Uptime (comme avant).**
-   [ ] **Santé des Composants et Connexions**:
    -   [ ] Indicateurs pour `MarketDataProvider` (statut API Jupiter/DexScreener, latence moyenne), `TradingEngine` (connexion RPC Solana), `Database`.
    -   [ ] **Nouveau**: Cliquer sur un composant pour voir des métriques détaillées (ex: nombre d'appels API récents, temps de réponse moyen, erreurs récentes).
-   [ ] **Métriques d'Utilisation des Ressources (comme avant, `psutil`).**
-   [ ] **Visualisation des Logs Intégrée**:
    -   [ ] Un panneau affichant les logs en temps réel.
    -   [ ] **Nouveau**: Filtres par niveau (INFO, DEBUG, WARNING, ERROR), par module (`DexBot`, `TradingEngine`, etc.), et recherche par mot-clé.
    -   [ ] **Nouveau**: Bouton pour télécharger les logs.

### Étape 7: Panneau "Settings & Customization" (Plus Complet)

-   [ ] **Éditeur des Paramètres de `Config` (comme avant, mais plus sécurisé)**:
    -   [ ] **Nouveau**: Grouper les paramètres par catégorie (Trading, API, UI, Sécurité).
    -   [ ] Validation en temps réel des entrées.
    -   [ ] Indication des paramètres nécessitant un redémarrage du bot.
-   [ ] **Paramètres de Notification (comme avant, mais plus granulaires)**:
    -   [ ] Choisir le canal de notification (UI, email, Telegram - futures intégrations) pour différents types d'événements.
-   [ ] **Sélecteur de Thème et Accentuation (comme décrit en Étape 1).**
-   [ ] **Contrôle du Taux de Rafraîchissement (comme avant).**
-   [ ] **Nouveau: Gestion des Clés API**:
    -   [ ] Interface sécurisée pour mettre à jour les clés API (nécessite un backend sécurisé pour le stockage si les clés ne sont pas uniquement dans `.env`). Avertir des risques.
-   [ ] **Nouveau: Configuration des Sources de Données**:
    -   [ ] Permettre d'activer/désactiver ou de prioriser certaines sources de données dans `MarketDataProvider` (ex: préférer DexScreener à Jupiter pour certaines paires).
-   [ ] **Nouveau: Export/Import de la Configuration du Bot**:
    -   [ ] Sauvegarder/charger l'ensemble des paramètres de `Config` et potentiellement des préférences UI dans un fichier.
-   [ ] **Nouveau: Gestion des Widgets du Dashboard**:
    -   [ ] Permettre à l'utilisateur de choisir quels widgets afficher/masquer sur chaque panneau.
    -   [ ] (Plus avancé) Permettre de réorganiser les widgets par glisser-déposer.

### Étape 8: Améliorations Générales et Finitions (Focus UX)

-   [ ] **Réactivité Mobile et Tablette (Priorité Haute)**.
-   [ ] **Cohérence Visuelle et Composants Material Design (ou équivalent)**.
-   [ ] **Optimisation des Performances de l'UI (Crucial)**.
-   [ ] **Gestion des Erreurs dans l'UI Claire et Constructive**:
    -   [ ] Messages d'erreur spécifiques avec suggestions d'actions si possible.
    -   [ ] Indicateur global si une erreur majeure affecte le bot.
-   [ ] **Aide Intégrée et Tooltips**:
    -   [ ] Icônes d'aide (?) à côté des paramètres ou sections complexes, affichant des tooltips ou des modales explicatives.
-   [ ] **Internationalisation (i18n) (Préparation)**:
    -   [ ] Utiliser des chaînes de caractères externalisées pour faciliter la traduction future.

**Sources de Données pour l'UI (Rappel et Extensions avec Agent IA):**
-   `EnhancedDatabase` pour les données historiques de trades, logs de décision IA.
-   `MarketDataProvider` pour les informations de marché, données on-chain basiques.
-   `PortfolioManager` pour les données de portefeuille.
-   `PerformanceMonitor` (potentiellement à étendre ou renommer en `SystemMonitorService`) pour les métriques système.
-   `PredictionEngine` pour les prédictions, classifications de régime, analyses de sentiment, rapports LLM.
-   `StrategySelector` et instances de `BaseStrategy` pour les paramètres et la logique de stratégie active.
-   `RiskManager` pour les calculs de risque en temps réel.
-   `DexBot` pour l'état général et la coordination.
-   `AIAgent` (nouveau): Pour l'état de l'agent, le raisonnement derrière les décisions.

Ce guide amélioré vise une UI non seulement fonctionnelle mais aussi engageante, informative et qui donne réellement l'impression d'interagir avec un système de trading intelligent.
L'IA devra consulter les fichiers existants (`app/gui.py`, `app/dashboard.py`) pour voir ce qui est déjà en place et l'étendre ou le modifier en conséquence.
N'hésite pas à proposer des visualisations ou des interactions encore plus innovantes si elles servent l'objectif principal de clarté et de contrôle. 