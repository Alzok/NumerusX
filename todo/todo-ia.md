# NumerusX - IA TODO List 🤖

**Prompt pour l'IA**: Exécute les tâches une par une. Quand tu as terminé une tâche, vérifie la cohérence du code par rapport à l'ensemble du projet et au contexte fourni. Une fois la vérification terminée et la cohérence assurée, passe en autonomie à la tâche suivante.

## Phase 1: Stabilisation et Refactorisation Fondamentale 🧱

L'objectif de cette phase est de s'assurer que le cœur du système est robuste, fiable et exempt d'incohérences.

### 1.1. Gestion Centralisée de la Configuration
- [x] **Tâche**: Finaliser la classe `Config` dans `app/config.py`.
- [x] **Détails**:
    - [x] S'assurer que *tous* les paramètres de configuration (chemins de base de données, clés API, URL d'API, paramètres de trading comme `SLIPPAGE`, `BASE_ASSET`, `MAX_POSITIONS`, `MAX_ORDER_SIZE`, `UPDATE_INTERVAL`, `INITIAL_BALANCE`, `UI_UPDATE_INTERVAL`, etc.) y sont définis.
    - [x] Remplacer toutes les références codées en dur ou les variables d'environnement directes dans l'ensemble du code par des appels à la classe `Config`.
    - [x] Vérifier que le chargement des variables d'environnement via `.env` fonctionne correctement avec `python-dotenv`.
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
- [ ] **Tâche**: Assurer l'initialisation correcte et les migrations de la base de données.
- [ ] **Détails**:
    - [ ] Compléter la méthode `_init_db` pour vérifier l'existence des tables *avant* de tenter des migrations ou des créations.
        - [ ] Créer le répertoire `data/` si `Config.DB_PATH` le spécifie et qu'il n'existe pas.
        - [ ] Gérer la migration de la table `trades` pour ajouter la colonne `protocol` si elle n'existe pas.
        - [ ] S'assurer que toutes les tables (`blacklist`, `trades`, `security_incidents`) sont créées avec `IF NOT EXISTS`.
    - [ ] Utiliser des transactions SQL pour assurer l'atomicité des opérations complexes.
    - [ ] Valider les entrées avant l'insertion pour prévenir les erreurs SQL et les injections basiques.
- [ ] **Fichiers concernés**: `app/database.py`.

## Phase 2: Logique de Trading et Améliorations du Bot ⚙️

Avec une base stable, cette phase se concentre sur l'amélioration de la logique de trading et l'intégration des composants.

### 2.1. Intégration du Moteur de Prédiction (`app/dex_bot.py`, `app/prediction_engine.py`)
- [ ] **Tâche**: Intégrer le `prediction_engine.py` pour améliorer la prise de décision.
- [ ] **Détails**:
    - [ ] S'assurer que `prediction_engine` est correctement initialisé dans `DexBot`.
    - [ ] Dans `DexBot._analyze_pairs`:
        - [ ] Après l'analyse de base par la stratégie, appeler `self.prediction_engine.predict_price()`.
        - [ ] Combiner le signal de la stratégie avec la prédiction de l'IA. Par exemple, moduler la confiance du signal de la stratégie en fonction de la confiance et de la direction de la prédiction de l'IA.
        - [ ] Gérer les erreurs potentielles lors de l'appel au moteur de prédiction.
- [ ] **Fichiers concernés**: `app/dex_bot.py`, `app/prediction_engine.py`.

### 2.2. Intégration du Gestionnaire de Risques (`app/dex_bot.py`, `app/risk_manager.py`)
- [ ] **Tâche**: Utiliser `risk_manager.py` pour le dimensionnement des positions et les contrôles de risque.
- [ ] **Détails**:
    - [ ] S'assurer que `risk_manager` est correctement initialisé dans `DexBot`.
    - [ ] Dans `DexBot._execute_signals` (ou la méthode équivalente après refactorisation) :
        - [ ] Appeler `self.risk_manager.calculate_position_size()` pour déterminer le montant optimal de la transaction.
        - [ ] Vérifier les limites d'exposition et les contrôles de drawdown avant d'exécuter un trade.
        - [ ] Mettre à jour le `risk_manager` après chaque trade.
- [ ] **Fichiers concernés**: `app/dex_bot.py`, `app/risk_manager.py`.

### 2.3. Refactorisation de `app/dex_bot.py`
- [ ] **Tâche**: Améliorer la structure et la lisibilité de `dex_bot.py`.
- [ ] **Détails**:
    - [ ] **`TradeExecutor`**: Envisager de créer une classe `TradeExecutor` distincte pour encapsuler la logique d'exécution des ordres (communication avec `trading_engine`, gestion des reintentions spécifiques aux trades). Actuellement, la logique est dans `_execute_signals`.
    - [ ] **Séparation Portfolio/Trading**: Mieux séparer la gestion du portefeuille (`PortfolioManager`) de la logique de décision et d'exécution des trades. `PortfolioManager` devrait se concentrer sur le suivi des actifs et de la valeur, tandis que `DexBot` ou `TradeExecutor` gère les opérations.
    - [ ] **Gestion des erreurs et reintentions**: Implémenter une gestion d'erreur plus spécifique pour les opérations de trading (ex: fonds insuffisants, slippage excessif, échec de la transaction Solana) avec des logiques de reintentions ciblées.
- [ ] **Fichiers concernés**: `app/dex_bot.py`, (potentiellement créer `app/trade_executor.py`).

### 2.4. Finalisation de `app/dex_api.py` (si non entièrement fusionné avec `market_data.py`)
- [ ] **Tâche**: Compléter les méthodes manquantes et assurer la robustesse.
- [ ] **Détails**:
    - [ ] Implémenter la méthode `get_price`.
        - [ ] Utiliser le cache.
        - [ ] Essayer Jupiter en premier, puis DexScreener en fallback.
        - [ ] Gérer les erreurs de manière propre et retourner `0.0` ou lever une exception spécifique si aucun prix n'est disponible.
- [ ] **Fichiers concernés**: `app/dex_api.py`, `app/market/market_data.py`.

## Phase 3: Interface Utilisateur et Fonctionnalités Avancées ✨

Cette phase vise à enrichir l'expérience utilisateur et à introduire des capacités de trading plus sophistiquées.

### 3.1. Amélioration de l'Interface Utilisateur (`app/dashboard.py`, `app/gui.py`)
- [ ] **Tâche**: Développer un tableau de bord complet et réactif.
- [ ] **Détails**:
    - [ ] S'inspirer de la structure proposée dans `todo.md` pour `dashboard.py` (Portfolio Overview, Trading Activity, Market Analysis, Control Center, System Monitoring, Settings).
    - [ ] Utiliser `asyncio` pour les mises à jour en temps réel des données (solde, positions, graphiques).
    - [ ] Afficher une estimation des frais de transaction avant l'exécution manuelle d'un trade.
    - [ ] Mettre en place un suivi en direct du statut des transactions (en attente, confirmée, échouée).
    - [ ] Visualiser les métriques de performance du bot (ROI, win rate, Sharpe, etc.).
    - [ ] Fournir une vue détaillée du portefeuille (actifs détenus, valeur actuelle, P&L non réalisé).
- [ ] **Fichiers concernés**: `app/dashboard.py` (à créer/améliorer), `app/gui.py`.

### 3.2. Implémentation de Stratégies de Trading Novatrices
- [ ] **Tâche**: Concevoir et implémenter de nouvelles stratégies de trading, en s'appuyant sur le `strategy_framework.py`.
- [ ] **Idées de Stratégies (exemples, à adapter et améliorer)**:
    - [ ] **Stratégie Hybride (Indicateurs + IA)**:
        - [ ] Utiliser des indicateurs techniques classiques (RSI, MACD, Bandes de Bollinger) pour générer des signaux préliminaires.
        - [ ] Soumettre ces signaux (avec contexte de marché: volatilité, volume, sentiment) au `prediction_engine.py` (Phase 4) pour confirmation ou ajustement de la confiance.
    - [ ] **Stratégie Basée sur les Flux On-Chain et le Sentiment**:
        - [ ] Analyser les mouvements de "whales" et "smart money" (si des API le permettent).
        - [ ] Intégrer l'analyse de sentiment de `prediction_engine.py` pour détecter des changements soudains dans l'intérêt pour un token.
        - [ ] Combiner avec l'analyse du carnet d'ordres (déséquilibres) si disponible via `market_data.py`.
    - [ ] **Stratégie d'Arbitrage Statistique sur les Pools de Liquidité**:
        - [ ] Identifier des déséquilibres temporaires de prix entre différents pools d'un même token sur Jupiter ou entre Jupiter et un autre DEX.
        - [ ] Nécessite une exécution très rapide et une gestion fine des frais.
    - [ ] **Stratégie de Trading sur Événements/Catalyseurs**:
        - [ ] Détecter des annonces importantes (listings, partenariats) via des API de news ou des flux sociaux (via `prediction_engine.py`).
        - [ ] Entrer en position en anticipation ou juste après l'annonce, avec des règles de sortie strictes.
    - [ ] **Stratégie de Volatilité Dynamique**:
        - [ ] Utiliser l'ATR ou les Bandes de Bollinger pour identifier les périodes de faible volatilité (consolidation).
        - [ ] Placer des ordres conditionnels (si supporté par `trading_engine.py`) pour capturer les breakouts.
        - [ ] Ajuster la taille des positions et les niveaux de stop-loss/take-profit en fonction de la volatilité actuelle.
- [ ] **Fichiers concernés**: `app/strategy_framework.py`, créer de nouveaux fichiers de stratégies (ex: `app/strategies/hybrid_strategy.py`).

### 3.3. Boucle de Confirmation par IA pour les Trades
- [ ] **Tâche**: Intégrer une étape finale de validation par une IA rapide avant l'exécution d'un trade.
- [ ] **Détails**:
    - [ ] Avant qu'un signal généré par une stratégie algorithmique ne soit envoyé au `trading_engine`, le `DexBot` (ou `TradeExecutor`) doit préparer un résumé du trade potentiel (token, type d'ordre, prix d'entrée, stop-loss, take-profit, contexte de marché actuel, signaux de la stratégie principale).
    - [ ] Ce résumé est envoyé à un modèle d'IA (potentiellement un LLM léger et rapide, ou un classificateur entraîné spécifiquement) hébergé localement ou via une API à faible latence.
    - [ ] L'IA retourne une évaluation (ex: "Bon trade", "Mauvais trade", "Neutre" ou un score de confiance).
    - [ ] Le `DexBot` utilise cette évaluation comme un filtre final. Un "Mauvais trade" pourrait annuler l'ordre, ou un score de confiance faible de l'IA pourrait réduire la taille de la position.
    - [ ] **Important**: Cette IA doit être optimisée pour la vitesse afin de ne pas introduire de latence significative.
- [ ] **Fichiers concernés**: `app/dex_bot.py` (ou `app/trade_executor.py`), `app/prediction_engine.py`.

## Phase 4: Développement du Moteur de Prédiction Avancé (`prediction_engine.py`)

Cette phase se concentre sur la création d'un moteur de prédiction intelligent et adaptatif.

### 4.1. Classification des Régimes de Marché
- [ ] **Tâche**: Implémenter `MarketRegimeClassifier`.
- [ ] **Détails**:
    - [ ] Utiliser des indicateurs comme l'ADX (pour la force de la tendance), la largeur des Bandes de Bollinger (pour la volatilité) et le RSI (pour le momentum) pour classifier le marché en "trending", "ranging", ou "volatile".
    - [ ] Permettre au `PricePredictor` de sélectionner différents modèles ou stratégies en fonction du régime détecté.

### 4.2. Entraînement et Prédiction de Modèles ML
- [ ] **Tâche**: Implémenter `PricePredictor`.
- [ ] **Détails**:
    - [ ] **Caractéristiques (Features)**: Utiliser des données OHLCV historiques, des indicateurs techniques (RSI, MACD, BB, volume Z-score, changements de prix) et potentiellement des données de sentiment.
    - [ ] **Modèles**: Commencer avec `RandomForestRegressor` ou `GradientBoostingRegressor` de `scikit-learn`. Envisager `PyTorch` pour des modèles plus complexes (LSTM, Transformers) ultérieurement.
    - [ ] **Normalisation**: Utiliser `StandardScaler` pour normaliser les features.
    - [ ] **Entraînement**:
        - [ ] Implémenter `train_model` pour entraîner sur les données historiques.
        - [ ] Utiliser un découpage train/test (ex: 70/30) et envisager une validation croisée de type "walk-forward" pour les séries temporelles.
        - [ ] Sauvegarder les modèles entraînés (ex: avec `joblib`) et les scalers associés.
    - [ ] **Prédiction**: Implémenter `predict_price` pour faire des prédictions sur de nouvelles données.
    - [ ] **Gestion des modèles**: Charger les modèles existants au démarrage.

### 4.3. Analyse de Sentiment
- [ ] **Tâche**: Implémenter `SentimentAnalyzer`.
- [ ] **Détails**:
    - [ ] Intégrer des API pour récupérer des données de Twitter, Discord, Reddit (peut nécessiter des packages/API externes).
    - [ ] Utiliser des techniques NLP basiques (ex: VADER, TextBlob) ou des modèles de sentiment plus avancés si possible.
    - [ ] Agréger les scores de sentiment des différentes sources, en pondérant potentiellement par le volume de mentions ou la crédibilité de la source.
    - [ ] Mettre en cache les résultats de sentiment pour éviter des appels API excessifs.

### 4.4. Apprentissage par Renforcement (RL)
- [ ] **Tâche**: Implémenter `ReinforcementLearner`.
- [ ] **Détails**:
    - [ ] Définir l'espace d'états (ex: métriques de performance récentes, volatilité du marché).
    - [ ] Définir l'espace d'actions (ex: ajustements des paramètres de la stratégie principale ou des seuils de risque).
    - [ ] Concevoir une fonction de récompense (ex: basée sur le ROI, le Sharpe ratio, la réduction du drawdown).
    - [ ] Utiliser un algorithme RL simple (ex: Q-learning pour des espaces discrets) ou une librairie RL (ex: Stable Baselines3) pour des optimisations plus complexes.
    - [ ] Mettre à jour périodiquement les paramètres de la stratégie en fonction des "actions" suggérées par l'agent RL.

### 4.5. Réentraînement Automatique
- [ ] **Tâche**: Mettre en place un mécanisme de réentraînement périodique des modèles ML.
- [ ] **Détails**:
    - [ ] Déclencher le réentraînement en fonction de métriques de performance (ex: si le win rate d'un modèle chute sous un seuil) ou sur une base temporelle (ex: chaque semaine).
    - [ ] Utiliser les données de trading les plus récentes pour affiner les modèles.
    - [ ] Journaliser les performances des modèles avant et après réentraînement.

## Phase 5: Tests, Déploiement et Monitoring Continus 🚀

### 5.1. Tests Unitaires et d'Intégration Approfondis
- [ ] **Tâche**: Écrire des tests pour chaque module et pour les interactions entre modules.
- [ ] **Détails**:
    - [ ] Utiliser `pytest` ou `unittest`.
    - [ ] Simuler les réponses API pour tester la logique de `market_data.py` et `trading_engine.py`.
    - [ ] Tester les cas limites et les scénarios d'erreur.

### 5.2. Configuration du Déploiement Docker
- [ ] **Tâche**: Optimiser et sécuriser la configuration Docker.
- [ ] **Détails**:
    - [ ] S'assurer que `docker-compose.yml` est configuré pour différents environnements (dev, prod) si nécessaire.
    - [ ] Gérer les secrets (clés API, clés de portefeuille) de manière sécurisée en production (ex: via les secrets Docker ou des variables d'environnement injectées).
    - [ ] Optimiser la taille de l'image Docker.

### 5.3. Monitoring et Alerting
- [ ] **Tâche**: Mettre en place un système de monitoring et d'alerting.
- [ ] **Détails**:
    - [ ] Journaliser les métriques clés de performance (ROI, erreurs, latence des transactions) dans un format structuré.
    - [ ] Configurer des alertes (ex: via email, Telegram, Discord) pour les erreurs critiques, les drawdowns importants, ou les échecs de transaction répétés.

Rappels pour l'IA:
- **Prioriser la robustesse**: Une gestion d'erreur solide et des mécanismes de repli sont cruciaux.
- **Modularité**: Concevoir des composants indépendants et bien interfacés.
- **Journalisation Détaillée**: Chaque décision, action, erreur doit être journalisée.
- **Sécurité Avant Tout**: Protéger les clés API et les fonds.
- **Tests Continus**: Valider chaque changement avec des tests.