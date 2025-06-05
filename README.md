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

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn
- Auth0 account (for authentication)

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd numerusx-ui

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your Auth0 configuration

# Run the frontend
npm run dev
```

### Docker Setup
```bash
# Build and run both services
docker-compose up --build
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Jupiter DEX
JUPITER_API_URL=https://quote-api.jup.ag/v6

# Authentication
AUTH0_DOMAIN=your_auth0_domain
AUTH0_API_AUDIENCE=your_api_identifier

# Database
DATABASE_URL=sqlite:///./numerusx.db
```

#### Frontend (numerusx-ui/.env)
```bash
VITE_AUTH0_DOMAIN=your_auth0_domain
VITE_AUTH0_CLIENT_ID=your_client_id
VITE_AUTH0_AUDIENCE=your_api_identifier
VITE_API_BASE_URL=http://localhost:8000
```

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