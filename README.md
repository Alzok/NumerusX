# 🚀 NumerusX - AI Trading Bot for Solana

NumerusX is an advanced AI-powered cryptocurrency trading bot specifically designed for the Solana ecosystem. It leverages Google's Gemini 2.5 Flash AI model and Jupiter DEX v6 for intelligent, automated trading operations.

## ✨ Key Features

- **🤖 AI-Powered Trading**: Utilizes Gemini 2.5 Flash for intelligent market analysis and decision-making
- **⚡ Solana Integration**: Native support for Solana blockchain with Jupiter DEX v6
- **📊 Real-time Dashboard**: Modern interface with live portfolio tracking and trade monitoring
- **🔐 Secure Authentication**: Auth0 integration with JWT token management
- **💬 Real-time Communication**: WebSocket integration for live updates
- **🎨 Modern UI**: Built with shadcn/ui components for professional appearance
- **📱 Responsive Design**: Mobile-first approach with desktop optimization
- **🚀 Production Ready**: Complete Docker setup with Redis caching and monitoring
- **📈 Advanced Analytics**: Comprehensive trading statistics and performance metrics
- **🛡️ Risk Management**: Built-in stop-loss, take-profit, and portfolio optimization
- **🔧 Development Tools**: Complete dev-tools script with 20+ commands for easy development

## 🏗️ Technical Architecture

### Backend (FastAPI + Python)
- **FastAPI**: High-performance web framework
- **Gemini 2.5 Flash**: AI decision-making engine
- **Jupiter SDK v6**: DEX integration for Solana
- **Socket.io**: Real-time communication
- **SQLite**: Local database storage
- **JWT Authentication**: Secure API access

### Frontend (React + TypeScript)
- **React 18**: Modern component-based UI
- **TypeScript**: Type-safe development
- **shadcn/ui**: Professional component library (42 components)
- **TanStack Query**: Efficient data fetching and caching
- **Auth0**: Authentication provider
- **Chart.js**: Data visualization
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast development and build tool
- **Socket.io Client**: Real-time WebSocket communication

### Infrastructure & DevOps
- **Docker Compose**: Multi-service orchestration
- **Redis**: High-performance caching layer
- **Development Scripts**: Automated setup and management tools
- **Environment Management**: Complete .env configuration
- **API Structure**: RESTful API with 32 endpoints across 7 modules

## 🎨 UI Components & Design System

### Modern Interface with shadcn/ui
- **Design Style**: New York theme with zinc base color
- **Components**: 42 shadcn/ui components integrated
  - Navigation: Sidebar, Navigation Menu, Breadcrumb
  - Display: Card, Badge, Progress, Chart, Skeleton
  - Forms: Input, Select, Button, Switch, Slider
  - Feedback: Alert, Toast (Sonner), Dialog, Sheet
  - Layout: Aspect Ratio, Separator, Resizable

### Key Pages
1. **Dashboard**: Real-time KPIs, portfolio evolution, recent activity
2. **Trading**: Trade execution interface with statistics
3. **Bot Control**: AI agent management and configuration
4. **Portfolio**: Asset management and position tracking
5. **Settings**: User preferences and bot configuration

## 🚀 Lancement Ultra-Simplifié 

Ce projet est entièrement conteneurisé et **100% automatisé**. La seule dépendance requise sur votre machine est **Docker**.

### Prerequisites
- Docker 20.10+ avec Docker Compose
- Clés API (optionnelles au début) - voir section Configuration ci-dessous

### Lancement en UNE commande

1. **Cloner et lancer :**
   ```bash
   git clone https://github.com/your-repo/numerusx.git
   cd numerusx
   ./start.sh
   ```

C'est tout ! 🎉

### Que fait le script `./start.sh` ?

1. ✅ **Vérifie** que Docker est installé
2. ✅ **Crée automatiquement** les fichiers `.env` s'ils n'existent pas
3. ✅ **Vous guide** pour la configuration (ou permet de continuer avec les valeurs par défaut)
4. ✅ **Lance tous les services** Docker automatiquement
5. ✅ **Affiche les URLs** d'accès

### Méthode alternative (Docker Compose)

Si vous préférez utiliser Docker Compose directement :

```bash
docker-compose up --build
```

### Accès aux services
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379

### Arrêt du système
```bash
# Méthode 1: Ctrl+C dans le terminal où ./start.sh tourne
# Méthode 2: Dans un autre terminal
docker-compose down
```

## 🔧 Configuration des Variables d'Environnement

### Variables Backend (fichier `.env` à la racine)

#### 🔑 APIs Externes (OBLIGATOIRES)

- `GOOGLE_API_KEY`
  - **Description :** Clé API Google pour accéder au modèle Gemini 2.5 Flash AI
  - **Obligatoire :** Oui
  - **Où la trouver :** Allez sur [Google AI Studio](https://aistudio.google.com/app/apikey), connectez-vous et créez une nouvelle clé API

- `JUPITER_API_KEY`
  - **Description :** Clé API pour Jupiter Aggregator (DEX Solana)
  - **Obligatoire :** Optionnel pour les fonctionnalités de base
  - **Où la trouver :** Inscrivez-vous sur [Jupiter](https://jup.ag) et demandez une clé API

- `JUPITER_PRO_API_KEY`
  - **Description :** Clé API Pro pour Jupiter avec plus de fonctionnalités
  - **Obligatoire :** Optionnel
  - **Où la trouver :** Version premium de Jupiter API

- `DEXSCREENER_API_KEY`
  - **Description :** Clé API pour DexScreener (données de marché)
  - **Obligatoire :** Optionnel
  - **Où la trouver :** Contactez [DexScreener](https://dexscreener.com) pour une clé API

- `SOLANA_PRIVATE_KEY_BS58`
  - **Description :** Clé privée Solana en format Base58 pour les transactions
  - **Obligatoire :** Oui pour le trading réel
  - **Où la trouver :** Générez avec `solana-keygen new` ou exportez depuis Phantom/Solflare

- `SOLANA_RPC_URL`
  - **Description :** URL du nœud RPC Solana
  - **Obligatoire :** Oui
  - **Où la trouver :** Utilisez `https://api.mainnet-beta.solana.com` pour mainnet ou `https://api.devnet.solana.com` pour devnet

#### 🔐 Sécurité (OBLIGATOIRES)

- `JWT_SECRET_KEY`
  - **Description :** Clé secrète pour signer les tokens JWT
  - **Obligatoire :** Oui
  - **Où la trouver :** Générez une chaîne aléatoire de 32+ caractères : `openssl rand -hex 32`

- `MASTER_ENCRYPTION_KEY`
  - **Description :** Clé maître pour chiffrer les données sensibles
  - **Obligatoire :** Oui
  - **Où la trouver :** Générez une chaîne aléatoire de 32+ caractères : `openssl rand -hex 32`

#### 🔑 Auth0 Backend (OBLIGATOIRES pour l'authentification)

- `AUTH_PROVIDER_JWKS_URI`
  - **Description :** URI des clés publiques JWT de votre tenant Auth0
  - **Obligatoire :** Oui
  - **Où la trouver :** Dashboard Auth0 → Applications → [Votre App] → Settings → Advanced → Endpoints → JSON Web Key Set : `https://YOUR-DOMAIN.auth0.com/.well-known/jwks.json`

- `AUTH_PROVIDER_ISSUER`
  - **Description :** Domaine émetteur des tokens Auth0
  - **Obligatoire :** Oui
  - **Où la trouver :** Dashboard Auth0 → Applications → [Votre App] → Settings : `https://YOUR-DOMAIN.auth0.com/`

- `AUTH_PROVIDER_AUDIENCE`
  - **Description :** Identifiant unique de votre API dans Auth0
  - **Obligatoire :** Oui
  - **Où la trouver :** Dashboard Auth0 → APIs → [Votre API] → Settings → Identifier

#### ⚙️ Configuration Application (optionnelles avec valeurs par défaut)

- `APP_NAME`
  - **Description :** Nom de l'application
  - **Obligatoire :** Non (défaut: "NumerusX")

- `DEBUG`
  - **Description :** Active les logs de débogage
  - **Obligatoire :** Non (défaut: "False")

- `DEV_MODE`
  - **Description :** Mode développement (authentification optionnelle)
  - **Obligatoire :** Non (défaut: "False")

#### 💾 Base de Données (optionnelles)

- `DATABASE_URL`
  - **Description :** URL de connexion à la base de données SQLite
  - **Obligatoire :** Non (défaut: "sqlite:///data/numerusx.db")

#### 📦 Redis (optionnelles)

- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB`
  - **Description :** Configuration Redis pour le cache et rate limiting
  - **Obligatoire :** Non (défaut: localhost:6379)

### Variables Frontend (fichier `numerusx-ui/.env`)

#### 🔑 Auth0 Frontend (OBLIGATOIRES)

- `VITE_APP_AUTH0_DOMAIN`
  - **Description :** Domaine de votre tenant Auth0 pour le frontend
  - **Obligatoire :** Oui
  - **Où la trouver :** Dashboard Auth0 → Applications → [Votre App] → Settings → Domain : `your-domain.auth0.com`

- `VITE_APP_AUTH0_CLIENT_ID`
  - **Description :** ID client de votre application Auth0
  - **Obligatoire :** Oui
  - **Où la trouver :** Dashboard Auth0 → Applications → [Votre App] → Settings → Client ID

- `VITE_APP_AUTH0_AUDIENCE`
  - **Description :** Audience API pour les tokens (même que backend)
  - **Obligatoire :** Oui
  - **Où la trouver :** Dashboard Auth0 → APIs → [Votre API] → Settings → Identifier

#### 🌐 URLs Backend (optionnelles)

- `VITE_APP_BACKEND_URL`
  - **Description :** URL du backend API
  - **Obligatoire :** Non (défaut: "http://localhost:8000")

- `VITE_APP_SOCKET_URL`
  - **Description :** URL WebSocket pour les mises à jour temps réel
  - **Obligatoire :** Non (défaut: "http://localhost:8000")

### 🔑 Guide Configuration Auth0

1. **Créer un compte Auth0** (gratuit) : https://auth0.com
2. **Créer une nouvelle Application** :
   - Type : "Single Page Application"
   - Technology : "React"
3. **Configurer l'Application** :
   - Allowed Callback URLs : `http://localhost:5173`
   - Allowed Web Origins : `http://localhost:5173`
   - Allowed Logout URLs : `http://localhost:5173`
4. **Créer une API** :
   - Identifier : `https://numerusx-api` (ou votre choix)
   - Signing Algorithm : "RS256"
5. **Copier les valeurs** dans vos fichiers `.env`

## 🎯 Avantages de l'Approche Conteneurisée

### ✅ Simplicité Maximale
- **Une seule commande** : `./start.sh` et c'est parti !
- **Aucune installation manuelle** de Python, Node.js, dépendances
- **Configuration automatique** des fichiers d'environnement
- **Gestion intelligente** des erreurs et warnings

### ✅ Consistency Garantie
- **Environnement identique** sur toutes les machines (Windows, macOS, Linux)
- **Versions figées** des dépendances et services
- **Isolation complète** des dépendances système
- **Reproductibilité** parfaite des bugs et tests

### ✅ Développement Efficace
- **Hot-reload** automatique pour le backend et frontend
- **Logs centralisés** et structurés
- **Debug facile** avec Docker logs
- **Arrêt/redémarrage rapide** des services

### ✅ Production Ready
- **Même configuration** en dev et production
- **Monitoring intégré** avec health checks
- **Scalabilité** facile avec Docker Swarm/Kubernetes
- **Sécurité** avec isolation des conteneurs

## 📊 API Documentation

### Available Endpoints
- **GET /api/v1/bot/status** - Bot status and statistics
- **POST /api/v1/bot/start** - Start the trading bot
- **POST /api/v1/bot/stop** - Stop the trading bot
- **GET /api/v1/portfolio/snapshot** - Current portfolio state
- **GET /api/v1/trades** - Trading history
- **POST /api/v1/trades/manual** - Execute manual trade

### WebSocket Events
- `bot_status_update` - Real-time bot status changes
- `portfolio_update` - Portfolio value updates
- `new_trade_executed` - Trade execution notifications
- `ai_decision_update` - AI decision explanations
- `market_data_update` - Market data updates

## 🔐 Security Features

- **JWT Authentication**: Secure API access with Auth0
- **Token Validation**: RS256 verification with PyJWKClient
- **API Rate Limiting**: Built-in request throttling
- **Secure Headers**: CORS and security headers configured
- **Environment Isolation**: Separate development/production configs

## 📈 Trading Features

### AI Decision Making
- Market trend analysis using Gemini 2.5 Flash
- Risk assessment and position sizing
- Entry and exit point optimization
- Portfolio rebalancing strategies

### Jupiter DEX Integration
- Real-time price fetching
- Slippage protection
- Transaction optimization
- Multi-hop routing support

## 🧪 Testing

```bash
# Backend tests
python -m pytest tests/

# Frontend tests
cd numerusx-ui
npm run test
```

## 📦 Deployment

### Production Deployment
1. Configure production environment variables
2. Build frontend: `npm run build`
3. Deploy using Docker: `docker-compose -f docker-compose.prod.yml up`

### Environment Configuration
- Development: Auto-reload enabled, debug logs
- Production: Optimized builds, error monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the API documentation at `/docs` endpoint

---

**⚠️ Disclaimer**: This trading bot is for educational and experimental purposes. Always test thoroughly before using with real funds. Cryptocurrency trading involves significant risk.

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the API documentation at `/docs` endpoint

---

**⚠️ Disclaimer**: This trading bot is for educational and experimental purposes. Always test thoroughly before using with real funds. Cryptocurrency trading involves significant risk.