# NumerusX - Remaining Advanced Features & Specifics (from original todo.md)

**Prompt pour l'IA**: Ce fichier contient des spécifications détaillées pour des fonctionnalités avancées issues d'une version précédente de la todo list. Utilise ces détails pour enrichir l'implémentation des modules correspondants (`analytics_engine.py`, `risk_manager.py`, `trading_engine.py`, `strategy_framework.py`, `backtest_engine.py`, `market_maker.py`) comme spécifié dans `todo-ia.md` et `todo-features.md`. Ces tâches doivent être exécutées après la stabilisation de base du bot.

## 1. Dépendances à Vérifier/Ajouter (`requirements.txt`)
Lors de l'implémentation du moteur de prédiction, s'assurer que les dépendances suivantes (ou versions compatibles) sont présentes :
- [ ] `scikit-learn==1.0.2`
- [ ] `torch==1.13.1`
- [ ] `joblib==1.1.0`

## 2. Advanced Market Analysis Framework (`analytics_engine.py`)

-   [ ] **Analyse des flux On-Chain (Complément à `todo-features.md` I.1 & II.2)**:
    -   [ ] Implémenter `analyze_whale_activity(self, token_address: str) -> dict`:
        -   Analyse les grosses transactions (ex: >$10k) sur les dernières 24h.
        -   Utilise l'API Solana Explorer pour récupérer ces transactions.
        -   Calcule le ratio achat/vente et le flux net.
        -   Retourne `{'net_flow': float, 'whale_sentiment': str, 'risk_level': int}`.
-   [ ] **Analyse Multi-Timeframe**:
    -   [ ] Modifier la méthode `_momentum_score` (ou équivalent) pour considérer plusieurs timeframes (ex: 1m, 5m, 15m, 1h, 4h).
    -   [ ] Créer une matrice de corrélation entre les timeframes pour identifier les divergences.
    -   [ ] Pondérer les signaux des différents timeframes en fonction du régime de marché actuel (détecté par `prediction_engine.MarketRegimeClassifier`).
-   [ ] **Analyse Avancée de la Structure des Prix**:
    -   [ ] Implémenter `identify_support_resistance(self, price_data: pd.DataFrame) -> list`:
        -   Utiliser l'analyse du profil de volume pour trouver les nœuds à volume élevé.
        -   Identifier les fractales pour les points hauts/bas de swing.
        -   Calculer les niveaux de retracement de Fibonacci.
-   [ ] **Indicateurs d'Efficience du Marché**:
    -   [ ] Ajouter le calcul de l'Exposant de Hurst pour déterminer le caractère aléatoire ou tendanciel.
    -   [ ] Implémenter un ratio d'efficience du marché.
    -   [ ] Créer un classificateur momentum/retour à la moyenne.
-   [ ] **Système de Scoring Adaptatif**:
    -   [ ] Modifier la méthode `generate_signal` pour ajuster les poids des différents facteurs d'analyse en fonction du régime de marché.
    -   [ ] Augmenter les facteurs de momentum dans les marchés tendanciels.
    -   [ ] Favoriser le retour à la moyenne dans les marchés en range.

## 3. Sophisticated Risk Management System (`risk_manager.py`)

-   [ ] **Dimensionnement de Position Basé sur le Critère de Kelly**:
    -   [ ] Implémenter `calculate_position_size(self, win_rate: float, win_loss_ratio: float, account_size: float) -> float`:
        -   Prend en entrée : `win_rate` (taux de succès historique), `win_loss_ratio` (gain moyen / perte moyenne), `account_size`.
        -   Utilise la formule de Kelly : `f* = p - (1-p)/r`.
        -   Appliquer une fraction de Kelly (ex: demi-Kelly) pour la sécurité.
        -   Retourne la fraction du portefeuille à risquer, plafonnée par `Config.MAX_RISK_PER_TRADE`.
-   [ ] **Stop-Loss Dynamique Basé sur la Volatilité**:
    -   [ ] Calculer l'Average True Range (ATR) pour l'actif.
    -   [ ] Définir le stop-loss à un multiple de l'ATR par rapport au prix d'entrée.
    -   [ ] Ajuster en fonction des patterns de volatilité historiques.
-   [ ] **Contrôles de Risque au Niveau du Portefeuille**:
    -   [ ] Implémenter `check_correlation_risk(self, proposed_asset: str) -> bool`:
        -   Évalue si l'ajout d'un nouvel actif augmente le risque de corrélation du portefeuille.
        -   Calcule la corrélation entre l'actif proposé et les positions existantes.
        -   Retourne `False` si l'ajout dépasse un seuil de corrélation défini.
    -   [ ] Envisager l'optimisation de portefeuille via la Théorie Moderne du Portefeuille (MPT) (comme mentionné dans `todo-features.md` III.2, mais `todo.md` le liste ici).
-   [ ] **Protection contre le Drawdown**:
    -   [ ] Implémenter un mécanisme de disjoncteur (circuit breaker) qui met en pause le trading après un drawdown de X%.
    -   [ ] Définir des règles basées sur le temps pour la reprise du trading après des pertes.
-   [ ] **Dimensionnement de Position Ajusté à la Volatilité (généralisation du stop-loss dynamique)**.
-   [ ] **Intégration avec `EnhancedDatabase`**:
    -   [ ] Enregistrer tous les calculs de risque dans la base de données pour analyse.
    -   [ ] Suivre les métriques de risque dans le temps pour identifier les tendances.
    -   [ ] Stocker les données de validation pour le backtesting.

## 4. High-Performance Execution Engine (`trading_engine.py`)

-   [ ] **Récupération Parallèle de Cotations**:
    -   [ ] Implémenter `async def get_quotes(self, mint_in: str, mint_out: str, amount: int) -> dict`:
        -   Récupère les cotations de plusieurs sources en parallèle (ex: Jupiter API principale, Raydium pour comparaison, Openbook en fallback).
        -   Utiliser `asyncio.gather`.
        -   Retourne la meilleure cotation basée sur le montant de sortie et la fiabilité.
-   [ ] **Optimisation des Frais de Transaction (Spécifique Solana)**:
    -   [ ] Implémenter `def estimate_fees(self, tx_data: dict) -> int` (peut être intégré à `get_fee_for_message` de `todo-ia.md` 1.5):
        -   Utilise la congestion actuelle du réseau (via `getPrioritizationFees`).
        -   Estime la taille de la transaction.
        -   Considère les données de frais récents historiques.
        -   Retourne le niveau de frais optimal en lamports.
    -   [ ] Ajouter des instructions de "compute budget" aux transactions.
    -   [ ] Inclure le calcul des "priority fees".
    -   [ ] Ajouter la compensation du "clock skew".
-   [ ] **Sélection d'Algorithmes d'Exécution (TWAP, VWAP, etc.)** (si pertinent pour les swaps simples sur Jupiter).
-   [ ] **Mesure et Optimisation de la Latence**.
-   [ ] **Batching de Transactions** (si applicable et bénéfique sur Solana pour les types de transactions effectuées).
-   [ ] **Mécanisme de Réessai Intelligent (détail pour `todo-ia.md` 1.5)**:
    -   [ ] Utiliser `@retry` de `tenacity` avec `wait_exponential`, `stop_after_attempt`, et `retry_if_exception_type((TimeoutError, ConnectionError))` pour `execute_transaction`.
-   [ ] **Stratégies de Protection MEV (détail pour `todo-features.md` III.1)**:
    -   [ ] Soumission de transactions privées via RPC (si disponible/efficace).
    -   [ ] Monitoring du slippage en temps réel pendant l'exécution.
    -   [ ] Timing d'exécution randomisé (petite variance).

## 5. Strategy Framework (`strategy_framework.py`)
En complément de `todo-ia.md` (Tâche 3.2):
-   [ ] **Définir l'Interface de Base de Stratégie (`BaseStrategy`)**:
    -   [ ] `analyze(self, market_data: pd.DataFrame) -> dict`: Analyse les données de marché et retourne les résultats.
    -   [ ] `generate_signal(self, analysis: dict) -> dict`: Génère un signal de trading à partir de l'analyse.
    -   [ ] `get_parameters(self) -> dict`: Retourne les paramètres de la stratégie.
-   [ ] **Implémenter des Exemples de Stratégies Concrètes**:
    -   [ ] `MomentumStrategy(BaseStrategy)`:
        -   Paramètres: `rsi_period=14`, `rsi_threshold=70`.
        -   `analyze`: Implémente l'analyse de momentum avec RSI, MACD, action des prix.
-   [ ] **Créer un Sélecteur de Stratégie (`StrategySelector`)**:
    -   [ ] `select_strategy(self, market_data: pd.DataFrame) -> BaseStrategy`:
        -   Détermine la meilleure stratégie pour les conditions actuelles.
        -   Utilise la détection de régime de marché (`prediction_engine`).
        -   Considère la performance historique des stratégies.
        -   Retourne une instance de la stratégie sélectionnée.
-   [ ] **Suivi de Performance par Stratégie**:
    -   [ ] Suivre le ratio gain/perte pour chaque stratégie.
    -   [ ] Calculer le facteur de profit et le ratio de Sharpe pour chaque stratégie.
    -   [ ] Implémenter une rotation automatique des stratégies basée sur la performance (si `StrategySelector` n'est pas suffisant).
-   [ ] **Framework pour Indicateurs Personnalisés**.
-   [ ] **Capacités de Combinaison de Stratégies**.
-   [ ] **Intégration avec `dex_bot.py`**:
    -   [ ] Remplacer l'analytique codée en dur par le framework de stratégie.
    -   [ ] Ajouter une étape de sélection de stratégie à la boucle principale.

## 6. Advanced Order Types (`trading_engine.py`)

-   [ ] **Ordres Limites via API Jupiter**:
    -   [ ] `async def place_limit_order(self, mint_in: str, mint_out: str, amount: int, price_limit: float) -> dict`:
        -   Place un ordre limite en utilisant l'API d'ordres limites de Jupiter.
        -   Définit le prix max pour achat ou min pour vente.
        -   Retourne l'ID de l'ordre et son statut.
        -   Stocke l'ordre dans la DB pour suivi.
-   [ ] **Fonctionnalité d'Ordres DCA (Dollar Cost Averaging)**:
    -   [ ] `async def setup_dca_orders(self, mint_in: str, mint_out: str, total_amount: int, num_orders: int, interval_seconds: int) -> dict`:
        -   Divise `total_amount` en `num_orders` parts égales.
        -   Planifie l'exécution à des intervalles spécifiés.
-   [ ] **Système de Take-Profit en Échelle (Laddering)**:
    -   [ ] `def create_tp_ladder(self, entry_price: float, position_size: float, levels: list, percentages: list) -> list`:
        -   `levels`: liste de cibles de prix en pourcentages (ex: `[1.05, 1.10, 1.20]`).
        -   `percentages`: pourcentage de la position à vendre à chaque niveau (ex: `[0.3, 0.3, 0.4]`).
        -   Retourne une liste d'ordres à exécuter.
-   [ ] **Fonctionnalité de Trailing Stops**:
    -   [ ] Créer une tâche de fond pour surveiller les mouvements de prix.
    -   [ ] Ajuster le stop-loss à mesure que le prix évolue favorablement.
    -   [ ] Implémenter avec une distance en pourcentage ou basée sur l'ATR.
-   [ ] **Ordres Basés sur le Temps (GTD - Good Till Date)**.
-   [ ] **Ordres Conditionnels**.
-   [ ] **Gestionnaire d'Ordres (`OrderManager` classe)**:
    -   [ ] Suivre tous les ordres ouverts.
    -   [ ] Implémenter l'annulation/modification d'ordres.
    -   [ ] Gérer les timeouts pour les ordres limites.

## 7. Robust Backtesting Engine (`backtest_engine.py`)
En complément de `todo-features.md` (IV.2 - Jumeau Numérique), un moteur de backtest plus classique :
-   [ ] **Chargement de Données Historiques**:
    -   [ ] `async def load_historical_data(self, token_address: str, timeframe: str, days: int) -> pd.DataFrame`:
        -   Charge les données OHLCV (depuis Coingecko, DexScreener, ou `market_data.py`).
        -   Nettoie et normalise le format des données.
-   [ ] **Simulation de Backtesting**:
    -   [ ] `def run_backtest(self, strategy: BaseStrategy, historical_data: pd.DataFrame, initial_capital: float) -> dict`:
        -   Traite les données chronologiquement pour éviter le biais de lookahead.
        -   Applique les signaux de la stratégie pour générer des trades.
        -   Suit la valeur du portefeuille, les drawdowns, et les statistiques de trades.
-   [ ] **Calcul de Métriques de Performance**:
    -   [ ] `def calculate_metrics(self, backtest_results: dict) -> dict`:
        -   Ratio de Sharpe, Ratio de Sortino, Ratio de Calmar.
        -   Max Drawdown, Taux de Réussite, Facteur de Profit.
-   [ ] **Optimisation des Paramètres de Stratégie**:
    -   [ ] Recherche par grille (grid search) et/ou aléatoire.
    -   [ ] Optimisation par validation progressive (walk-forward optimization).
-   [ ] **Simulation de Monte Carlo pour l'Évaluation des Risques**.
-   [ ] **Modèles Réalistes de Frais et de Slippage pour le Backtesting**.
-   [ ] **Composants de Visualisation**:
    -   [ ] Courbe des capitaux (Equity curve).
    -   [ ] Visualisation du drawdown.
    -   [ ] Graphiques de comparaison de stratégies.
    -   [ ] Marqueurs d'entrée/sortie de trade sur les graphiques.

## 8. Market-Making Capabilities (`market_maker.py`)

-   [ ] **Définition du Market Maker de Base**:
    -   [ ] `MarketMaker` classe:
        -   Paramètres: `trading_engine`, `pair_address`, `base_spread` (%), `inventory_target` (ratio).
-   [ ] **Logique de Génération de Cotations**:
    -   [ ] `generate_quotes(self, mid_price: float, volatility: float) -> dict`:
        -   Basé sur le prix médian du carnet d'ordres, la volatilité (pour ajustement du spread), et la position d'inventaire (pour skewing).
-   [ ] **Gestion de l'Inventaire**:
    -   [ ] `adjust_for_inventory(self, bid_size: float, ask_size: float, current_inventory: float) -> tuple`:
        -   Ajuste la taille des ordres pour cibler `inventory_target`.
        -   Réduit la taille du bid si inventaire > cible, réduit la taille du ask si inventaire < cible.
-   [ ] **Gestion du Spread Basée sur la Volatilité**:
    -   [ ] Calculer la volatilité historique.
    -   [ ] Élargir le spread en période de haute volatilité, le resserrer en période de faible volatilité.
-   [ ] **Détection de Flux Toxique**:
    -   [ ] `detect_toxic_flow(self, recent_trades: list) -> bool`:
        -   Analyse les trades récents pour des patterns de sélection adverse.
        -   Identifie les flux de trades unilatéraux.
-   [ ] **Logique de Rafraîchissement des Cotations**:
    -   [ ] Tâche de fond pour rafraîchir périodiquement les cotations.
    -   [ ] Logique pour annuler et remplacer les cotations après un mouvement de prix.
    -   [ ] Disjoncteurs en cas de volatilité extrême.
-   [ ] **Laddering de Cotations Sophistiqué**.
-   [ ] **Monitoring des Positions de Fournisseur de Liquidité (LP)** (si le bot fournit activement de la liquidité à des pools).