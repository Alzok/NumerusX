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

### 🆕 **Nouvelles Fonctionnalités Avancées** 
- **🔄 Cache Intelligent Multi-Niveau**: MarketDataCache avec TTL automatique et fallbacks
- **⚙️ Gestion Ressources**: ResourceManager pour isolation CPU et prévention surcharge
- **🌐 API REST Complète**: 9 endpoints market data avec documentation Swagger
- **🛡️ SecurityChecker Optimisé**: Analyses parallèles 3x plus rapides avec cache intelligent
- **📊 Métriques Performance**: Monitoring temps réel avec cache hit rate et statistiques

## 🏗️ Technical Architecture

### Backend (FastAPI + Python)
- **FastAPI**: High-performance web framework
- **Gemini 2.5 Flash**: AI decision-making engine
- **Jupiter SDK v6**: DEX integration for Solana
- **Socket.io**: Real-time communication
- **SQLite**: Local database storage with WAL optimization
- **JWT Authentication**: Secure API access
- **Redis Cache**: High-performance caching layer
- **MarketDataCache (C16)**: Cache intelligent avec TTL et fallbacks
- **ResourceManager (C17)**: Isolation CPU/mémoire pour analyses intensives
- **OptimizedSecurityChecker (C8)**: Analyses parallèles avec cache multi-niveau

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
- **Redis**: High-performance caching layer with TTL management
- **Development Scripts**: Automated setup and management tools
- **Environment Management**: Complete .env configuration
- **API Structure**: RESTful API with 41 endpoints across 8 modules
  - **Market Data API (C5)**: 9 nouveaux endpoints avec auth JWT
  - **Performance Monitoring**: Métriques temps réel et cache analytics
  - **Resource Management**: Quotas CPU et isolation des tâches intensives

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
- `AUTH_PROVIDER_AUDIENCE` - Auth0 API audience (obligatoire)  
- `AUTH_PROVIDER_ISSUER` - Auth0 domain issuer (obligatoire)
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

## 🧪 Testing

```bash
# Backend tests
python -m pytest tests/

# Frontend tests
cd numerusx-ui
npm run test
```

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
