# NumerusX - Architecture Applicative Globale pour Trading Haute Performance et Intelligent 🎯

**Objectif de ce document**: Définir une architecture applicative cohérente pour NumerusX, intégrant tous les modules et fonctionnalités envisagés, avec un **noyau décisionnel centralisé autour d'un Agent IA**. Ce guide est destiné aux IA de développement pour assurer la cohésion, la performance, et l'évolutivité du système, en particulier pour des opérations de trading rapides et intelligentes sur la blockchain Solana.

## I. Principes Architecturaux Clés

L'architecture de NumerusX repose sur les principes fondamentaux suivants :

-   **Modularité et Couplage Faible**: Chaque composant majeur (Acquisition de Données, Génération de Features/Signaux Stratégiques, Moteurs de Prédiction IA, **Agent IA Décisionnel Central**, Gestion des Risques, Exécution des Trades, Sécurité, Interface Utilisateur) est conçu pour être aussi indépendant que possible, communiquant via des interfaces bien définies.
-   **Performance et Asynchronisme au Cœur**: L'utilisation intensive de `asyncio` est cruciale. La boucle de trading principale, centrée sur l'Agent IA, doit rester réactive.
-   **Robustesse et Résilience**: Gestion d'erreurs exhaustive, mécanismes de fallback, et logiques de reintentions intelligentes.
-   **Évolutivité et Extensibilité**: L'architecture doit permettre l'ajout aisé de nouvelles sources de données, de modules fournisseurs de signaux (stratégies), de modèles d'IA pour l'Agent, et de fonctionnalités.
-   **Configuration Centralisée et Flexible**: `app/config.py` reste la source de vérité.
-   **Journalisation Compréhensible et Structurée**: Crucial pour tracer les décisions de l'Agent IA et les inputs qui y ont mené.
-   **Sécurité Intégrée ("Security by Design")**: Reste une préoccupation transversale.

## II. Vue d'Ensemble de l'Architecture (Diagramme Global Centré sur l'Agent IA)

Ce diagramme illustre les principaux composants de NumerusX et leurs interactions, mettant en évidence le rôle central de l'Agent IA.

```mermaid
graph TD
    subgraph "Utilisateur & Contrôle Externe"
        UI["Interface Utilisateur NiceGUI<br>(app/dashboard.py)"]
    end

    subgraph "Orchestration & Logique de Base"
        MAIN["Point d'Entrée<br>(app/main.py)"]
        BOT["Orchestrateur de Flux<br>(app/dex_bot.py)"]
        CONFIG["Configuration<br>(app/config.py)"]
        LOGGER["Journalisation<br>(app/logger.py)"]
        DB["Base de Données SQLite<br>(app/database.py)"]
    end

    subgraph "Fournisseurs de Données & Signaux"
        MDP["Fournisseur de Données de Marché<br>(app/market/market_data.py)"]
        EXT_JUP["API Jupiter"]
        EXT_DEX["API DexScreener"]
        EXT_SOCIAL["APIs Sociales/News (Future)"]
        
        SF["Cadre de Stratégies (Fournisseur de Signaux)<br>(app/strategy_framework.py)"]
        USER_STRATS["Stratégies Spécifiques (Input Sources)<br>(app/strategies/)"]
        STRAT_ADV["Analyse Technique Avancée (Input Source)<br>(app/analytics_engine.py)"]
        
        PE["Moteur de Prédiction IA (Input Source)<br>(app/prediction_engine.py)"]
        PP["Prédicteur de Prix (ML/DL)"]
        MRC["Classifier Régime Marché (Future)"]
        SP["Analyseur de Sentiment (Future)"]
        %% ADV_AI[Modules IA Avancés (GNN, TDA, Causal, etc.)]
    end

    subgraph "Noyau Décisionnel Intelligent"
        AI_AGENT["<<Agent IA Décisionnel Central>>\n(app/ai_agent.py)"]
    end
    
    subgraph "Contrôle & Validation Pré-Trade"
        RISK["Gestionnaire de Risques<br>(app/risk_manager.py)"]
        SEC["Vérificateur de Sécurité Token<br>(app/security/security.py)"]
        PORTFOLIO["Gestionnaire de Portefeuille<br>(app/portfolio_manager.py)"]
    end

    subgraph "Exécution & Interaction Blockchain"
        EXEC["Exécuteur de Trade<br>(app/trade_executor.py)"]
        TE["Moteur d'Exécution de Trades<br>(app/trading/trading_engine.py)"]
        SOL["Réseau Solana & DEXs"]
    end

    subgraph "Outils de Développement & Évaluation"
        BACKTEST["Moteur de Backtesting"]
    end

    %% Liaisons
    MAIN --> BOT
    UI --> BOT

    BOT --> CONFIG
    BOT --> LOGGER
    BOT --> DB

    BOT --> MDP
    MDP --> EXT_JUP
    MDP --> EXT_DEX
    MDP --> EXT_SOCIAL

    BOT --> SF
    SF --> USER_STRATS
    USER_STRATS --> AI_AGENT
    %% Stratégies fournissent des inputs à l'Agent
    STRAT_ADV --> AI_AGENT
    %% Analyse technique fournit inputs à l'Agent
    
    BOT --> PE
    PE --> PP
    PE --> MRC
    PE --> SP
    PE --> AI_AGENT
    %% Prédictions IA fournissent inputs à l'Agent
    %% ADV_AI --> AI_AGENT

    BOT --> RISK
    BOT --> SEC
    BOT --> PORTFOLIO

    RISK --> AI_AGENT
    %% Contraintes de risque pour l'Agent
    SEC --> AI_AGENT
    %% Contraintes de sécurité pour l'Agent
    PORTFOLIO --> AI_AGENT
    %% État du portefeuille pour l'Agent
    MDP --> AI_AGENT
    %% Données de marché directes pour l'Agent

    AI_AGENT --> BOT
    %% L'Agent retourne la décision finale au Bot orchestrateur
    BOT --> EXEC
    %% Le Bot transmet l'ordre de l'Agent à l'exécuteur

    EXEC --> TE
    EXEC --> PORTFOLIO
    %% Mise à jour post-trade
    EXEC --> RISK
    %% Mise à jour post-trade
    TE --> SOL

    BACKTEST --> MDP
    BACKTEST --> SF
    BACKTEST --> PE 
    BACKTEST --> AI_AGENT
    %% Backtesting de l'agent lui-même
```

**Boucles de Traitement Redéfinies**:

1.  **Boucle de Décision et Trading Temps Réel (Haute Fréquence / Faible Latence)**:
    `DexBot` (collecte inputs) -> `MarketDataProvider`, `StrategyFramework` (via `StrategySelector` & `app/strategies`), `PredictionEngine`, `RiskManager`, `SecurityChecker`, `PortfolioManager` (tous fournissent des données/signaux/contraintes) -> **`AIAgent`** (analyse l'ensemble des inputs, prend la décision finale de trade) -> `DexBot` (reçoit l'ordre) -> `TradeExecutor` -> `TradingEngine` -> Solana.

2.  **Boucle d'Analyse et Prédiction IA (Quasi Temps Réel / Latence Modérée)**:
    `MarketDataProvider` -> `PredictionEngine` (génère prédictions, classifications de régime, scores de sentiment) -> Ces outputs sont des inputs directs pour l'**`AIAgent`**.

3.  **Boucle d'Apprentissage et Optimisation (Hors Ligne / Arrière-Plan / Différée)**:
    `Database` (données historiques) -> `PredictionEngine` (réentraînement des modèles fournisseurs d'inputs) -> **`AIAgent`** (apprentissage/optimisation de sa propre logique de décision, potentiellement via RL ou meta-learning sur les performances passées et les inputs reçus) -> `BacktestEngine` (pour évaluer l'Agent et les modèles d'input).

## III. Flux de Décision et d'Exécution d'un Trade (Centré sur l'Agent IA)

Ce diagramme illustre le nouveau chemin critique d'une décision de trading.

```mermaid
sequenceDiagram
    participant UI as Dashboard
    participant DexBot as OrchestrateurDeFlux
    participant MDP as MarketDataProvider
    participant StratInputs as FournisseursSignauxStratégie (SF, strategies/)
    participant PredEng as PredictionEngine
    participant RiskMgr as RiskManager
    participant SecChk as SecurityChecker
    participant PortMgr as PortfolioManager
    participant AIAgent as Agent IA Décisionnel
    participant TradeExec as TradeExecutor
    participant TradingEng as TradingEngine
    participant Solana as Réseau Solana
    participant DB as Database

    Note over DexBot: Cycle de Décision Initié (périodique)
    DexBot->>MDP: Demande Données Marché Actuelles
    MDP-->>DexBot: Données Marché (Prix, Volume...)
    
    DexBot->>StratInputs: Demande Signaux/Analyses Stratégiques
    StratInputs-->>DexBot: Signaux (ex: RSI, MACD, BB scores)
    
    DexBot->>PredEng: Demande Prédictions IA
    PredEng-->>DexBot: Prédictions (Prix, Régime, Sentiment)

    DexBot->>RiskMgr: Demande État Risque Actuel
    RiskMgr-->>DexBot: Limites de Risque, Exposition
    
    DexBot->>SecChk: Demande Statut Sécurité Token
    SecChk-->>DexBot: Info Sécurité
    
    DexBot->>PortMgr: Demande État Portefeuille
    PortMgr-->>DexBot: Soldes, Positions

    Note over DexBot: Agrège tous les inputs pour l'Agent IA
    DexBot->>AIAgent: Fournit {DonnéesMarché, SignauxStrat, PrédictionsIA, ContraintesRisque, InfoSécu, ÉtatPortefeuille}
    
    AIAgent->>AIAgent: Processus de Décision Interne (analyse, pondération, synthèse)
    
    AIAgent-->>DexBot: Ordre de Trade Final (Action, Paire, Montant, Type, SL/TP) OU Pas d'Action + Raisonnement
    
    alt Ordre de Trade Actif
        DexBot->>TradeExec: execute_trade_order(ordre_agent_ia)
        TradeExec->>TradingEng: execute_swap_from_order(ordre_agent_ia)
        TradingEng->>Solana: Soumettre Transaction
        Solana-->>TradingEng: Statut Transaction
        TradingEng-->>TradeExec: Résultat Exécution
        alt Trade Réussi
            TradeExec->>PortMgr: record_trade_executed(details)
            TradeExec->>RiskMgr: add_position(details)
            TradeExec->>DB: record_trade(details), record_agent_decision(raisonnement)
            DexBot->>UI: (Mise à jour via polling/WebSocket)
        else Trade Échoué
            DexBot->>DB: log_trade_failure(details, error), record_agent_decision(raisonnement)
            DexBot->>UI: (Notification d'erreur)
        end
    else Pas d'Action de l'Agent IA
        DexBot->>DB: log_agent_no_action(raisonnement)
    end
    DexBot->>UI: (Mise à jour générale du dashboard)
```

## IV. Décomposition des Modules et Leurs Rôles Clés (avec Agent IA)

### A. Couche d'Acquisition et de Gestion des Données (Globalement Inchangée)
-   `app/market/market_data.py` (`MarketDataProvider`)
-   `app/database.py` (`EnhancedDatabase`): Stockera aussi les décisions et raisonnements de l'Agent IA.

### B. Couche de Génération de Features et Signaux (Anciennement Analyse et IA)

-   **`app/analytics_engine.py` (`AdvancedTradingStrategy` en tant que fournisseur de features TA)**:
    -   **Rôle Redéfini**: Génère des indicateurs techniques avancés et des analyses de structure de marché comme *input* pour l'Agent IA. Ne prend plus de décision de trade finale.
-   **`app/prediction_engine.py` (`PricePredictor`, `MarketRegimeClassifier`, `SentimentAnalyzer`)**:
    -   **Rôle Redéfini**: Fournit des prédictions, classifications et scores de sentiment comme *inputs* pour l'Agent IA.
-   **`app/strategy_framework.py` (`BaseStrategy`) et `app/strategies/`**:
    -   **Rôle Redéfini**: Les stratégies deviennent des "modules de signaux" ou "extracteurs de features". Leur output (`analyze`, `generate_signal`) est un *input* pour l'Agent IA.
-   **`app/strategy_selector.py` (`StrategySelector`)**:
    -   **Rôle Redéfini**: Pourrait être utilisé par l'Agent IA pour dynamiquement choisir quels "modules de signaux" (stratégies) écouter ou pondérer plus fortement, ou par `DexBot` pour préparer le set d'inputs pour l'agent.

### C. Couche Noyau Décisionnel Intelligent (Nouveau)

-   **`app/ai_agent.py` (`AIAgent`)**:
    -   **Rôle**: Le nouveau cœur décisionnel. Reçoit tous les inputs pertinents (données de marché, signaux des stratégies, prédictions IA, contraintes de risque/sécurité, état du portefeuille).
    -   **Logique Interne**: Contient la logique (ML, RL, ensemble de modèles, heuristiques avancées) pour synthétiser ces inputs et générer un ordre de trade final et optimal.
    -   **Output**: Ordre de trade précis ou décision de ne pas trader, accompagné d'un "raisonnement" loggable.
    -   **Interactions**: Reçoit des données de multiples modules via `DexBot`. Retourne sa décision à `DexBot`.

### D. Couche de Contrôle et Validation Pré-Décision (Alimente l'Agent IA)

-   **`app/dex_bot.py` (`DexBot` en tant qu'Orchestrateur de Flux)**:
    -   **Rôle Redéfini**: Orchestre la collecte de tous les inputs nécessaires depuis les divers modules. Transmet ces inputs à l'`AIAgent`. Reçoit l'ordre final de l'`AIAgent` et le transmet à `TradeExecutor`.
-   **`app/portfolio_manager.py` (`PortfolioManager`)**:
    -   **Rôle**: Fournit l'état actuel du portefeuille (cash, positions) comme *input* à l'`AIAgent`. Toujours mis à jour par `TradeExecutor` post-trade.
-   **`app/risk_manager.py` (`RiskManager`)**:
    -   **Rôle**: Calcule les limites de risque, la taille de position potentielle maximale, etc., comme *contraintes* ou *inputs* pour l'`AIAgent`.
-   **`app/security/security.py` (`SecurityChecker`)**:
    -   **Rôle**: Fournit des informations sur la sécurité des tokens comme *input* à l'`AIAgent`.

### E. Couche d'Exécution (Globalement Inchangée)
-   `app/trade_executor.py` (`TradeExecutor`): Exécute l'ordre spécifique fourni par `DexBot` (qui vient de l'`AIAgent`).
-   `app/trading/trading_engine.py` (`TradingEngine`)

### F. Couche de Présentation et Contrôle (UI)
-   **`app/dashboard.py` (`NumerusXDashboard`)**: Devra être adapté pour afficher :
    -   Le raisonnement de l'Agent IA pour chaque trade.
    -   L'état de l'Agent IA.
    -   Potentiellement des visualisations des inputs clés que l'Agent a considérés.

### G. Utilitaires et Monitoring (Globalement Inchangés)
-   `app/config.py` (`Config`)
-   `app/logger.py` (`DexLogger`)

## V. Stratégies de Performance et de Coordination

-   **Latence de Décision de l'Agent IA**: Le design de l'`AIAgent` doit être optimisé pour une prise de décision rapide.
-   **Qualité et Pertinence des Inputs**: L'efficacité de l'Agent dépendra de la qualité des données et signaux qu'il reçoit.

## VI. Intégration des Fonctionnalités Avancées (Revu avec Agent IA)

-   Toutes les fonctionnalités avancées (MAC-MM, GNN Liquidité, TDA, Swarm Intelligence, etc.) de `02-todo-advanced-features.md` deviennent des sources d'input potentielles ou des méthodes d'amélioration pour l'`AIAgent` lui-même.
-   "Shadow Trading", "Deep RL Portfolio Management" pourraient être des modes de fonctionnement ou des logiques internes de l'`AIAgent`.
-   "Rapports de Décision LLM" devient le "raisonnement" de l'`AIAgent`.