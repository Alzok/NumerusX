# 🎯 NumerusX - Documentation Centrale du Projet

## Mission de l'Application

**NumerusX est un bot de trading intelligent alimenté par l'IA, spécialement conçu pour automatiser les opérations de trading de cryptomonnaies sur l'écosystème Solana avec prise de décision basée sur le modèle Gemini 2.5 Flash.**

## Architecture Technique

### Stack Technologique Complet

**Backend:**
- **Framework Principal**: FastAPI 0.104+ (API REST haute performance)
- **Base de Données**: SQLite avec SQLAlchemy ORM
- **Cache & Message Queue**: Redis 7-alpine
- **WebSocket**: Socket.IO pour communication temps réel
- **IA**: Google Gemini 2.5 Flash (modèle décisionnel central)
- **Blockchain**: Solana (réseau principal) via Jupiter DEX v6
- **Authentification**: Auth0 RS256 JWT
- **Conteneurisation**: Docker + Docker Compose

**Frontend:**
- **Framework**: React 18 + TypeScript 5.2+
- **Build Tool**: Vite 6.3+ (développement et production)
- **UI Library**: shadcn/ui (42 composants) basé sur Radix UI
- **Styling**: Tailwind CSS 3.4+ avec design system zinc
- **State Management**: Redux Toolkit + TanStack React Query
- **Auth**: Auth0 React SDK (@auth0/auth0-react)
- **WebSocket**: Socket.IO Client
- **Charts**: Chart.js + React-Chartjs-2

**Infrastructure:**
- **Orchestration**: Docker Compose multi-services
- **Reverse Proxy**: Nginx (production)
- **Monitoring**: Health checks intégrés
- **Logs**: Structured logging avec rotation
- **Scripts**: 20+ commandes d'automatisation dev-tools

### Communication Inter-Services

**API REST**: Communication synchrone Frontend ↔ Backend via endpoints `/api/v1/`
**WebSocket**: Communication bidirectionnelle temps réel pour:
- Mises à jour portefeuille en direct
- Notifications de trades
- Statut bot en temps réel
- Logs de trading en continu

**Redis**: Cache partagé pour:
- Sessions utilisateur
- Données de marché temporaires
- Rate limiting API
- État application distribué

## Structure des Fichiers et Dossiers

### Backend (`/app/`)

```
app/
├── main.py                 # Point d'entrée FastAPI + WebSocket server
├── config.py              # Configuration centralisée (environnement, API keys)
├── database.py            # ORM SQLAlchemy + modèles données
├── socket_manager.py       # Gestionnaire WebSocket Socket.IO
│
├── api/v1/                # Routes API REST modulaires
│   ├── __init__.py        # Router principal
│   ├── auth_routes.py     # Authentification JWT
│   ├── bot_routes.py      # Contrôle bot (start/stop/status)
│   ├── config_routes.py   # Configuration système
│   ├── trades_routes.py   # Opérations trading
│   ├── portfolio_routes.py # Gestion portefeuille
│   ├── ai_decisions_routes.py # Historique décisions IA
│   ├── system_routes.py   # Monitoring système
│   └── onboarding_routes.py # Assistant configuration initiale
│
├── models/                # Modèles de données Pydantic
│   ├── ai_inputs.py       # Structures données pour l'agent IA
│   └── [autres_modeles].py
│
├── trading/               # Logique métier trading
│   ├── trading_engine.py  # Moteur exécution trades
│   ├── transaction_handler.py # Gestion transactions (test/prod)
│   └── jupiter_integration.py # Interface Jupiter DEX
│
├── ai_agent_package/      # Agent IA décisionnel
├── utils/                 # Utilitaires
│   ├── auth.py           # Validation JWT Auth0
│   ├── encryption.py     # Chiffrement clés API
│   └── jupiter_api_client.py # Client Jupiter API
│
├── security/             # Sécurité et validation
├── strategies/           # Stratégies de trading
├── market/              # Données de marché
└── middleware/          # Middlewares FastAPI
```

### Frontend (`/numerusx-ui/`)

```
numerusx-ui/
├── src/
│   ├── App.tsx                # Composant racine + routing
│   ├── main.tsx              # Point d'entrée React + providers
│   │
│   ├── components/           # Composants UI réutilisables
│   │   ├── ui/              # Composants shadcn/ui (42 composants)
│   │   ├── auth/            # Composants authentification
│   │   ├── dashboard/       # Composants tableau de bord
│   │   ├── onboarding/      # Assistant configuration
│   │   ├── system/          # Indicateurs système
│   │   └── layout/          # Layout et navigation
│   │
│   ├── pages/               # Pages principales
│   │   ├── DashboardPage.tsx # Tableau de bord principal
│   │   ├── TradingPage.tsx   # Interface trading
│   │   ├── SettingsPage.tsx  # Configuration
│   │   └── LoginPage.tsx     # Authentification
│   │
│   ├── hooks/               # Custom hooks React
│   │   ├── useBot.ts        # État et contrôle du bot
│   │   ├── usePortfolio.ts  # Données portefeuille
│   │   ├── useAuth.ts       # Gestion authentification
│   │   └── useOnboarding.ts # Configuration initiale
│   │
│   ├── services/            # Services externes
│   │   └── api.ts          # Client API REST
│   │
│   ├── lib/                 # Configuration librairies
│   │   ├── apiClient.ts     # Instance Axios configurée
│   │   ├── utils.ts         # Utilitaires généraux
│   │   └── i18n.ts         # Internationalisation
│   │
│   └── app/                # Store Redux
│       ├── store.ts        # Configuration store
│       └── slices/         # Slices Redux Toolkit
│
├── public/                 # Assets statiques
├── package.json           # Dépendances et scripts
└── vite.config.ts         # Configuration Vite
```

### Fichiers de Configuration Racine

- **docker-compose.yml**: Orchestration des 3 services (redis, backend, frontend)
- **start.sh**: Script de démarrage automatisé avec création `.env`
- **.env.example**: Template variables d'environnement
- **requirements.txt**: Dépendances Python backend
- **CHANGELOG.md**: Historique des changements
- **README.md**: Documentation utilisateur et installation

### Scripts d'Automatisation (`/scripts/`)

- **dev-tools.sh**: 20+ commandes développement (build, test, lint, format)
- **test-setup.sh**: Vérification rapide configuration
- **check-build-status.sh**: Monitoring build Docker

## Flux de Données et Logique Clé

### Flux Trading Principal

**1. Collecte de Données Multi-Sources**
```
MarketDataProvider → Données prix temps réel (Jupiter API)
StrategyFramework → Signaux techniques (RSI, MACD, Bollinger)
PredictionEngine → Prédictions IA (prix futurs, sentiment marché)
RiskManager → Contraintes risque et exposition
SecurityChecker → Validation sécurité tokens
PortfolioManager → État actuel portefeuille
```

**2. Décision Intelligente Centralisée**
```
Tous les inputs → AIAgent (Gemini 2.5 Flash)
AIAgent analyse l'ensemble des données et retourne:
- Décision: BUY/SELL/HOLD
- Taille position
- Prix cible
- Stop-loss
- Confidence score
- Justification textuelle
```

**3. Validation et Exécution**
```
AIAgent décision → RiskManager (validation limites)
→ SecurityChecker (vérification token sécurisé)
→ PortfolioManager (vérification fonds disponibles)
→ TradeExecutor → Jupiter DEX → Solana blockchain
```

### Flux Authentification

**1. Utilisateur se connecte**
```
Frontend → Auth0 → Token JWT RS256
Frontend stocke token → Requests API avec Bearer token
Backend valide token via JWKS Auth0
```

**2. Configuration Initiale (Onboarding)**
```
Utilisateur non configuré → OnboardingWizard forcé
Étape 1: Saisie clés API (Google, Jupiter, Solana)
Étape 2: Choix palette couleurs et style
Étape 3: Mode opérationnel (Test vs Production)
Chiffrement clés sensibles → Stockage sécurisé
```

### Flux WebSocket Temps Réel

**1. Connexion établie**
```
Frontend se connecte à Socket.IO backend
Backend authentifie la session
Souscription aux événements: portfolio, trades, logs, bot_status
```

**2. Émission d'événements**
```
Backend émet toutes les 30 secondes:
- portfolio_update: Valeur portfolio, P&L, positions
- bot_status: État bot, trades récents, erreurs
- real_time_logs: Logs trading en continu
```

## Concepts Fondamentaux

### Agent IA Décisionnel Central

L'**AIAgent** (`app/ai_agent.py`) est le cerveau de NumerusX. Il reçoit des inputs structurés de tous les modules et utilise Gemini 2.5 Flash pour:

- **Analyse Holistique**: Corrélation données marché + signaux techniques + prédictions
- **Gestion Contexte**: Mémorisation des décisions passées et apprentissage des erreurs
- **Explications**: Justification de chaque décision pour transparence
- **Risk-Awareness**: Intégration contraintes risque dans la prise de décision

### Système de Configuration Dynamique

Remplace les fichiers `.env` statiques par un système interactif:

- **OnboardingWizard**: Assistant première configuration
- **Mode Test vs Production**: Simulation réaliste vs vrais trades
- **Chiffrement Automatique**: Protection clés API sensibles
- **Configuration Temps Réel**: Modification paramètres sans redémarrage

### Pattern Strategy pour Transactions

```python
# Interface commune pour test et production
interface TransactionHandler:
    execute_swap(token_in, token_out, amount) -> TransactionResult

# Implémentations
LiveTransactionHandler -> Vraies transactions blockchain
MockTransactionHandler -> Simulation avec balances virtuelles

# Factory automatique basé sur configuration
handler = create_transaction_handler()  # Lit mode depuis DB
```

### Gestion Erreurs et Résilience

- **Retry Logic**: Tentatives multiples avec backoff exponentiel
- **Fallback Mechanisms**: Sources de données alternatives
- **Circuit Breaker**: Arrêt automatique en cas d'erreurs critiques
- **Health Monitoring**: Surveillance continue état services

### Sécurité Intégrée

- **Authentification Obligatoire**: Auth0 pour toutes fonctionnalités sensibles
- **Chiffrement Clés**: PBKDF2 + AES pour clés API
- **Validation Inputs**: Pydantic pour toutes données entrantes
- **Rate Limiting**: Protection contre abus API
- **Audit Trail**: Traçabilité complète actions utilisateur

### Performance et Scalabilité

- **Asynchrone Total**: `asyncio` pour toutes opérations I/O
- **Cache Redis**: Réduction latence données fréquentes
- **WebSocket**: Évite polling pour mises à jour temps réel
- **Connection Pooling**: Réutilisation connexions DB et HTTP
- **Optimistic UI**: Interface réactive avec mise à jour progressive

## Environnements et Déploiement

### Développement Local
```bash
# Démarrage une commande
./start.sh
# Services disponibles:
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# Redis: localhost:6379
```

### Production
- **Frontend**: Build static servi par Nginx
- **Backend**: Conteneur FastAPI avec Gunicorn
- **Base de Données**: Migration vers PostgreSQL
- **Cache**: Redis Cluster pour haute disponibilité
- **SSL**: Certificats automatiques Let's Encrypt
- **Monitoring**: Prometheus + Grafana

### Variables d'Environnement Critiques

**Backend:**
- `GOOGLE_API_KEY`: Clé Gemini 2.5 Flash (obligatoire)
- `SOLANA_PRIVATE_KEY_BS58`: Clé trading Solana (obligatoire)
- `AUTH_PROVIDER_JWKS_URI`: Auth0 JWKS (obligatoire)
- `JWT_SECRET_KEY`: Signature tokens (obligatoire)
- `MASTER_ENCRYPTION_KEY`: Chiffrement données (obligatoire)

**Frontend:**
- `VITE_APP_AUTH0_DOMAIN`: Domain Auth0 (obligatoire)
- `VITE_APP_AUTH0_CLIENT_ID`: Client ID Auth0 (obligatoire)
- `VITE_APP_AUTH0_AUDIENCE`: API Audience Auth0 (obligatoire)

## Métriques et Monitoring

### KPIs Business
- Portfolio total value (USD)
- PnL 24h/7d/30d
- Nombre trades réussis/échoués
- Win rate et average return
- Sharpe ratio et maximum drawdown

### Métriques Techniques
- Latence moyenne décision IA
- Temps exécution trades
- Uptime services
- Erreurs API par endpoint
- Utilisation mémoire/CPU

### Logs Structurés
- Décisions IA avec inputs et outputs
- Trades avec détails exécution
- Erreurs avec stack traces
- Performance avec métriques
- Sécurité avec tentatives accès 