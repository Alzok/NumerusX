![Logo](logo.jpg)

# NumerusX: Your Intelligent Navigator for Cryptocurrency Trading

NumerusX is a sophisticated software platform designed to empower users in the complex world of cryptocurrency trading. Think of it as an **intelligent agent** that helps you make informed decisions, automate your trading strategies, and manage your digital assets on the Solana blockchain, a fast and efficient network for crypto transactions.

## What Can NumerusX Do For You?

At its core, NumerusX aims to make advanced trading techniques accessible and manageable. Here's how:

*   **AI-Driven Decision Making**: NumerusX places a powerful AI Agent at its core. This agent synthesizes a vast array of information – market data, technical analysis, AI predictions, risk parameters, and even social sentiment – to make the final trading decisions.
*   **Smart Input Strategies**: While the AI Agent makes the ultimate call, NumerusX allows you to define and plug in various "input strategies" or "signal generators." These can range from traditional technical indicator-based logic to more complex analytical modules. The AI Agent intelligently weighs these inputs.
*   **Comprehensive Market Analysis**: The system leverages multiple AI and analytical modules to understand market dynamics, predict potential price movements, and gauge sentiment. These insights become critical inputs for the central AI Agent.
*   **Risk Management First**: The cryptocurrency market can be volatile. NumerusX is built with a strong emphasis on managing risk. Risk parameters and portfolio status are key inputs to the AI Agent, ensuring decisions align with predefined safety nets.
*   **Security Shield**: NumerusX includes features to help identify potentially risky tokens or fraudulent schemes. Security assessments also feed into the AI Agent's decision process.
*   **Continuous Market Understanding**: The platform constantly gathers and processes market data, ensuring that the AI Agent's decisions are based on the latest information.
*   **Performance Tracking & Transparency**: Understand how well the AI Agent and its input strategies are performing. The system aims to provide clear logs of the AI Agent's reasoning.
*   **User-Friendly Dashboard**: A modern, responsive web application built with React, ShadCN/UI, and Tailwind CSS provides a central hub to monitor your trading bot, view your portfolio, analyze market trends, observe the AI Agent's decisions, and control its operations. It communicates with the backend via APIs and WebSockets for real-time data.

## How Does It Work? (An AI Agent-Centric View)

NumerusX operates with a central AI Agent that synthesizes information from a team of specialized modules:

1.  **The Data Gatherer (`MarketDataProvider`)**: Constantly watches the market, collecting price information, news, and other relevant data (Jupiter, DexScreener).
2.  **The Signal & Feature Generators (Formerly Analyst & Strategist - `AnalyticsEngine`, `PredictionEngine`, `StrategyFramework`, `app/strategies/*`)**: These modules now act as sophisticated input providers for the AI Agent:
    *   `AnalyticsEngine`: Performs technical analysis and feature engineering.
    *   `PredictionEngine`: Employs AI/ML for price predictions, market regime classification, and sentiment analysis.
    *   `StrategyFramework` & `app/strategies/*`: User-defined or pre-built logic modules that generate specific signals or analytical outputs based on market data and indicators.
3.  **The Central AI Agent (`AIAgent`)**: This is the brain (initially leveraging **Google Gemini**). It receives and processes all the inputs from the Data Gatherer and the various Signal & Feature Generators. It also considers risk parameters from the Risk Manager and security inputs. Based on its internal logic (which could be a complex ML model, a meta-learner, or a Reinforcement Learning agent), it makes the final, holistic decision on whether to trade, what to trade, and how much.
4.  **The Risk Manager (`RiskManager`)**: Provides critical risk assessment data (e.g., current exposure, available capital, volatility-based limits) as direct input to the AI Agent, ensuring its decisions adhere to safety protocols.
5.  **The Security Guard (`Security`)**: Checks tokens for red flags. This security assessment is another input for the AI Agent.
6.  **The Orchestrator (`DexBot`)**: This component manages the flow of information. It gathers data from all provider modules, feeds it to the AI Agent, receives the final decision from the AI Agent, and then passes this decision to the Executor.
7.  **The Jupiter Maestro (`JupiterApiClient`)**: This new dedicated client handles all interactions with the Jupiter API v6 using the `jupiter-python-sdk`. It's utilized by the `MarketDataProvider` for fetching data and by the `TradingEngine` for executing swaps, limit orders, etc.
8.  **The Executor (`TradeExecutor` & `TradingEngine`)**: Once the AI Agent makes a decision (conveyed via `DexBot`), these components carry out the actual trades on the Solana network. The `TradingEngine` specifically uses the `JupiterApiClient` for optimal swap routing and other Jupiter-specific operations.
9.  **The Record Keeper (`Database`)**: All trades, AI Agent decisions (including key inputs and reasoning), and important events are logged.
10. **The Cache (`Redis`)**: Used for caching frequently accessed data, session management for the UI, and potentially as a message broker for inter-service communication or task queuing, enhancing performance and scalability.
11. **The Control Panel (`numerusx-ui/`)**: Your window into NumerusX, built as a React application. It allows you to monitor the AI Agent, its inputs, overall performance, and manage the bot. It interacts with the FastAPI backend.

## Visualizing NumerusX: Architecture and Flow (AI Agent Centric)

### High-Level Architecture (Centred on AI Agent)

```mermaid
graph TD
    A["User/Developer"] --> UI_REACT("numerusx-ui/ (React Frontend)");
    UI_REACT --- B_API("app/main.py (FastAPI Backend - API/WebSockets)");
    B_API --> C{"NumerusX Core Orchestrator (app/dex_bot.py)"};
    
    subgraph "Input & Data Providers"
        DATASRC("app/market/market_data.py");
        DATASRC --> EXTAPI{"External APIs: DexScreener, Social"};
        TECH_ANALYSIS("app/analytics_engine.py");
        PREDICT_AI("app/prediction_engine.py");
        STRAT_FRWK("app/strategy_framework.py");
        USER_STRATS("app/strategies/*");
        RISK_INFO("app/risk_manager.py");
        SEC_INFO("app/security/security.py");
        PORT_INFO("app/portfolio_manager.py");
        JUP_CLIENT_NODE["app/utils/jupiter_api_client.py<br>Jupiter SDK Client"];
    end

    subgraph "Central Decision Core"
        AI_AGENT_CORE["<<app/ai_agent.py>>\nAI Agent Décisionnel Central<br>(using Gemini)"];
    end

    subgraph "Execution & Persistence"
        EXEC_ENG("app/trade_executor.py");
        TRADE_SYS("app/trading/trading_engine.py");
        TRADE_SYS --> SOLANA("Solana Blockchain / DEXs");
        DB_STORE("app/database.py");
        DB_STORE --> SQLITEDB("SQLite Database");
        CACHE_SYS["Redis Cache"];
    end

    C --> DATASRC;
    C --> TECH_ANALYSIS;
    C --> PREDICT_AI;
    C --> STRAT_FRWK;
    STRAT_FRWK --> USER_STRATS;
    C --> RISK_INFO;
    C --> SEC_INFO;
    C --> PORT_INFO;
    C --> JUP_CLIENT_NODE;

    DATASRC --> AI_AGENT_CORE;
    DATASRC --> JUP_CLIENT_NODE;
    TECH_ANALYSIS --> AI_AGENT_CORE;
    PREDICT_AI --> AI_AGENT_CORE;
    USER_STRATS --> AI_AGENT_CORE;
    RISK_INFO --> AI_AGENT_CORE;
    SEC_INFO --> AI_AGENT_CORE;
    PORT_INFO --> AI_AGENT_CORE;
    
    AI_AGENT_CORE --> C;
    %% AI Agent returns decision to Orchestrator
    C --> EXEC_ENG;
    EXEC_ENG --> TRADE_SYS;
    TRADE_SYS --> JUP_CLIENT_NODE;
    JUP_CLIENT_NODE --> SOLANA;
    EXEC_ENG --> DB_STORE;
    %% For trade recording
    AI_AGENT_CORE --> DB_STORE;
    %% For decision logging
    B_API --> CACHE_SYS;
    C --> CACHE_SYS;

    D --> C;
    A --> F("app/config.py");
    C --> F;
```

### Trading Decision Workflow (AI Agent Centric)

```mermaid
sequenceDiagram
    participant Orchestrator as DexBot (Orchestrator)
    participant DataProvider as Market Data Provider
    participant FeatureProviders as Signal/Feature Generators (Analytics, Predictions, Strategies)
    participant RiskSecPort as Risk/Security/Portfolio Modules
    participant AIAgent as AI Agent (app/ai_agent.py)
    participant Executor as Trade Executor
    participant Blockchain as Solana Network

    Orchestrator->>DataProvider: Request Market Data
    DataProvider-->>Orchestrator: Market Data
    Orchestrator->>FeatureProviders: Request Analyses/Signals/Predictions
    FeatureProviders-->>Orchestrator: Analytical Inputs
    Orchestrator->>RiskSecPort: Request Constraints/Status
    RiskSecPort-->>Orchestrator: Risk, Security, Portfolio Info

    Orchestrator->>AIAgent: Provide Aggregated Inputs
    AIAgent->>AIAgent: Process Inputs & Make Decision
    AIAgent-->>Orchestrator: Final Trade Order / No Action + Reasoning

    alt Trade Order Issued by AI Agent
        Orchestrator->>Executor: Execute Order
        Executor->>Blockchain: Submit Transaction
        Blockchain-->>Executor: Confirmation/Status
        Executor-->>Orchestrator: Trade Result
        Orchestrator->>Orchestrator: Log Trade & AI Reasoning
    else No Action by AI Agent
        Orchestrator->>Orchestrator: Log AI Reasoning (No Trade)
    end
```

## Project Structure

```
NumerusX/
├── app/                        # Python Backend (FastAPI, Bot Logic)
│   ├── __init__.py
│   ├── ai_agent.py           # NEW: Central AI Agent for decision making (using Gemini)
│   ├── ai_agent/             # NEW: Subdirectory for AI agent components
│   │   └── gemini_client.py  # NEW: Client for Google Gemini API
│   ├── api_routes.py         # FastAPI routes for UI interaction (API & WebSockets)
│   ├── analytics_engine.py     # Advanced market analysis and feature engineering (Input to AI Agent)
│   ├── config.py             # Centralized configuration management
│   ├── database.py           # SQLite database interaction and schema
│   ├── dex_bot.py            # Core bot logic, orchestrates data to AI Agent and executes its decisions
│   ├── logger.py             # Application-wide logging setup
│   ├── main.py               # Main entry point for the FastAPI backend application
│   ├── monitoring.py         # System monitoring and performance tracking
│   ├── portfolio_manager.py  # Manages portfolio state (Input to AI Agent, updated by Executor)
│   ├── prediction_engine.py  # AI/ML models for price/trend prediction & sentiment (Input to AI Agent)
│   ├── risk_manager.py       # Position sizing, portfolio risk controls (Input to AI Agent)
│   ├── strategy_debug.py     # Tools for debugging trading strategies
│   ├── strategy_evaluator.py # Performance evaluation of trading strategies
│   ├── strategy_framework.py # Base classes for creating signal/feature modules (Input to AI Agent)
│   ├── trade_executor.py     # Handles the execution of trades decided by the AI Agent
│   ├── wallet.py             # Solana wallet management and key handling
│   ├── examples/             # Example strategies and usage scenarios
│   │   └── simple_strategy_example.py
│   ├── market/               # Market data acquisition and management
│   │   └── market_data.py    # Unified provider for Jupiter, DexScreener, etc. (Input to AI Agent)
│   ├── security/             # Token security analysis and validation (Input to AI Agent)
│   │   └── security.py
│   ├── strategies/           # Specific strategy modules (Input to AI Agent)
│   │   └── momentum_strategy.py
│   │   └── mean_reversion_strategy.py
│   │   └── trend_following_strategy.py
│   ├── trading/              # Trading execution logic
│   │   └── trading_engine.py # Interface with Solana DEXs (via **JupiterApiClient** using Jupiter SDK v6) for swaps.
│   └── utils/                # Utility modules
│       └── jupiter_api_client.py # NEW: Client for Jupiter API v6 using jupiter-python-sdk
├── numerusx-ui/                # NEW: React Frontend Application
│   ├── public/
│   ├── src/
│   └── package.json            # (Structure as detailed in todo/01-todo-ui.md)
├── Docker/
│   ├── backend/              # Dockerfile for backend
│   ├── frontend/             # Dockerfile for frontend (React app)
│   └── docker-compose.yml    # Docker container orchestration
├── todo/                     # Task lists and planning documents
│   ├── TODO-MASTER-ANALYSE-2024.md  # 🆕 ROADMAP PRINCIPAL - Phases A, B, C structurées
│   ├── ISSUES-TECHNIQUES-CRITIQUES.md # 🆕 PROBLÈMES URGENTS - Solutions détaillées  
│   ├── DEPENDENCIES-MANQUANTES.md   # 🆕 PACKAGES à installer immédiatement
│   ├── DEPRECATED-OLD-TODOS.md      # 📚 Archive anciens TODOs (référence)
│   ├── 01-todo-core.md              # ✅ Largement complété (archived)
│   ├── 01-todo-database.md          # ✅ Implémentation terminée (archived)
│   └── [autres fichiers TODO...]    # 📚 Voir DEPRECATED-OLD-TODOS.md
├── .env.example              # Example environment variables (à créer)
├── .gitignore
├── logo.jpg
├── README.md
└── requirements.txt        # Python package dependencies (for backend)

## Installation

### Prérequis
- **Docker** et **Docker Compose**
- **Git**

### Installation Rapide
```bash
# 1. Cloner le projet
git clone <repository-url>
cd NumerusX

# 2. Configurer les variables d'environnement  
cp .env .env.local

# Créer le fichier frontend .env (copier le contenu depuis la section Configuration)
touch numerusx-ui/.env

# 3. Éditer vos clés API dans .env.local et numerusx-ui/.env
# (Voir section Configuration ci-dessous)

# 4. Démarrer l'application
docker compose up
```

### Configuration

#### Backend (.env)
```bash
# APIs externes (OBLIGATOIRE)
GOOGLE_API_KEY=your-google-gemini-api-key
JUPITER_API_KEY=your-jupiter-api-key  
SOLANA_PRIVATE_KEY_BS58=your-solana-private-key

# Auth0 Backend (OBLIGATOIRE)
AUTH_PROVIDER_JWKS_URI=https://your-domain.auth0.com/.well-known/jwks.json
AUTH_PROVIDER_ISSUER=https://your-domain.auth0.com/
AUTH_PROVIDER_AUDIENCE=your-api-identifier

# Sécurité
JWT_SECRET_KEY=your-jwt-secret-key
MASTER_ENCRYPTION_KEY=your-32-char-encryption-key
```

#### Frontend (numerusx-ui/.env)
```bash
VITE_APP_AUTH0_DOMAIN=your-domain.auth0.com
VITE_APP_AUTH0_CLIENT_ID=your-auth0-client-id
VITE_APP_AUTH0_AUDIENCE=your-api-identifier
VITE_APP_SOCKET_URL=http://localhost:8000
```

### URLs
- **Interface**: http://localhost:5173
- **API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs

### Problèmes Fréquents

#### Erreur "File .env not found"
```bash
# Copier le fichier .env existant
cp .env .env.local

# Ou créer depuis zero avec vos clés
touch .env.local
```

#### Frontend ne démarre pas
```bash
# Créer le fichier .env frontend manquant
touch numerusx-ui/.env
# Puis éditer avec la configuration Auth0 (voir section Configuration)
```

#### Docker permission denied
```bash
sudo chmod +x Docker/backend/Dockerfile Docker/frontend/Dockerfile
sudo docker compose up
```
```

## Core Components In-Depth (Reflecting AI Agent Architecture)

1.  **`