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

## 🚀 Démarrage Rapide

Ce projet est entièrement conteneurisé et **100% automatisé**. La seule dépendance requise est **Docker**.

### Lancement en UNE commande

```bash
git clone https://github.com/your-repo/numerusx.git
cd numerusx
./start.sh
```

Le script `./start.sh` :
- ✅ Vérifie Docker et crée les fichiers `.env` automatiquement
- ✅ Vous guide pour la configuration ou utilise les valeurs par défaut
- ✅ Lance tous les services et affiche les URLs d'accès

### Services Disponibles
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs

### Documentation Complète
- **Démarrage** → [docs/QUICK-START.md](./docs/QUICK-START.md)
- **Architecture** → [todo/PROJECT_OVERVIEW.md](./todo/PROJECT_OVERVIEW.md)
- **Configuration** → [docs/environment-setup.md](./docs/environment-setup.md)

### Arrêt
```bash
docker-compose down
```

## 🔧 Configuration

### Variables d'Environnement Essentielles

**Backend (`.env` à la racine):**
- `GOOGLE_API_KEY` - Clé Gemini 2.5 Flash (obligatoire)
- `SOLANA_PRIVATE_KEY_BS58` - Clé Solana pour trading (obligatoire pour prod)
- `AUTH_PROVIDER_JWKS_URI` - Auth0 JWKS URI (obligatoire)
- `JWT_SECRET_KEY` - Signature tokens (obligatoire)

**Frontend (`numerusx-ui/.env`):**
- `VITE_APP_AUTH0_DOMAIN` - Domaine Auth0 (obligatoire)
- `VITE_APP_AUTH0_CLIENT_ID` - Client ID Auth0 (obligatoire)
- `VITE_APP_AUTH0_AUDIENCE` - API Audience (obligatoire)

### Guide Configuration Complet
Consultez [docs/environment-setup.md](./docs/environment-setup.md) pour :
- Liste complète des variables avec descriptions
- Guide Auth0 step-by-step  
- Configuration production vs développement
- Génération de clés sécurisées

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