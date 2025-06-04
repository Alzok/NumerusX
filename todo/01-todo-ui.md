# NumerusX - Guide de Développement de l'Interface Utilisateur (UI) avec React et ShadCN/UI 🚀

**Prompt pour l'IA**: Ta mission est de concevoir et de développer une interface utilisateur (UI) **exceptionnelle** pour NumerusX en utilisant React, ShadCN/UI, Tailwind CSS, Recharts, Redux, Socket.io, et i18next. L'UI doit être claire, moderne, minimaliste, hautement interactive, et permettre une gestion intuitive et puissante de l'application.

## Objectifs Généraux de l'UI

-   **Contrôle Centralisé**: Démarrer, arrêter, configurer et surveiller le bot
-   **Feedback Dynamique**: État du bot, logs, actions et décisions IA transparentes
-   **Visualisation Avancée**: Graphiques interactifs avec Recharts
-   **Esthétique Moderne**: Interface épurée avec ShadCN/UI et Tailwind CSS
-   **Réactivité**: Updates temps réel via Socket.io et Redux
-   **Sécurité**: Authentification JWT avec FastAPI backend
-   **Internationalisation**: Support multilingue avec i18next

## Stack Technologique Frontend

*   **Framework**: React.js avec Vite.js
*   **Composants UI**: ShadCN/UI
*   **Styling**: Tailwind CSS
*   **Graphiques**: Recharts
*   **État Global**: Redux Toolkit
*   **Temps Réel**: Socket.io-client
*   **Authentification**: JWT (géré par FastAPI backend)
*   **i18n**: i18next avec react-i18next
*   **TypeScript**: Pour le typage

## Structure du Projet Frontend ✅ CRÉÉE

```
numerusx-ui/
├── public/
│   └── locales/         # Fichiers de traduction i18next
│       ├── en/
│       │   └── translation.json
│       └── fr/
│           └── translation.json
├── src/
│   ├── app/            # Redux store ✅
│   │   └── store.ts
│   ├── assets/         # Images, polices ✅
│   ├── components/     # Composants réutilisables ✅
│   │   ├── auth/       # Composants authentification
│   │   │   └── AuthenticationGuard.tsx ✅
│   │   ├── charts/     # Graphiques Recharts ✅
│   │   ├── layout/     # Header, Sidebar, Footer ✅
│   │   └── ui/         # Composants UI génériques ✅
│   ├── features/       # Modules fonctionnels ✅
│   │   └── Portfolio/  ✅
│   │       └── components/ ✅
│   ├── hooks/          # Hooks custom ✅
│   ├── lib/            # Utilitaires ✅
│   │   ├── i18n.ts     ✅
│   │   └── socketClient.ts ✅
│   ├── pages/          # Pages principales ✅
│   │   ├── CommandPage.tsx ✅
│   │   ├── DashboardPage.tsx ✅
│   │   ├── LoginPage.tsx ✅
│   │   ├── SettingsPage.tsx ✅
│   │   └── TradingPage.tsx ✅
│   ├── services/       # Appels API
│   ├── App.tsx ✅
│   ├── App.css ✅
│   ├── index.css ✅
│   └── main.tsx ✅
├── .env ✅
├── .env.example ✅
├── index.html ✅
├── package.json ✅
├── postcss.config.js ✅
├── tailwind.config.js ✅
├── tsconfig.json ✅
├── tsconfig.node.json ✅
└── vite.config.ts ✅
```

## Phase 1: Initialisation et Configuration ⚠️ À COMPLÉTER

### 1.1. Projet React avec Vite ✅
-   [x] Projet créé avec TypeScript et Vite
-   [x] Structure de base en place

### 1.2. Installation Dépendances ⚠️ À FAIRE
```bash
cd numerusx-ui
npm install
```
Dépendances requises :
-   [ ] `tailwindcss postcss autoprefixer` (partiellement configuré)
-   [ ] `@radix-ui/react-*` (pour ShadCN/UI)
-   [ ] `lucide-react` (icônes)
-   [ ] `recharts` (graphiques)
-   [ ] `@reduxjs/toolkit react-redux` (état global)
-   [ ] `socket.io-client` (temps réel)
-   [ ] `i18next react-i18next i18next-http-backend i18next-browser-languagedetector`
-   [ ] `react-router-dom` (navigation)
-   [ ] `axios` (appels API)
-   [ ] `class-variance-authority clsx tailwind-merge` (utils ShadCN)

### 1.3. Configuration Tailwind ✅ PARTIELLEMENT
-   [x] `tailwind.config.js` créé
-   [x] `postcss.config.js` créé
-   [x] Directives dans `index.css`
-   [ ] Configurer pour ShadCN/UI

### 1.4. ShadCN/UI Setup ⚠️ À FAIRE
```bash
npx shadcn-ui@latest init
```
Composants prioritaires :
-   [ ] Button, Card, Input, Dialog
-   [ ] DropdownMenu, Tooltip, Badge
-   [ ] Table, Tabs, Switch
-   [ ] Toast, Alert, Progress

### 1.5. Redux Store ✅ STRUCTURE
-   [x] `src/app/store.ts` créé
-   [ ] Slices à implémenter :
    -   [ ] `systemSlice` : État bot, connexion Socket.io
    -   [ ] `portfolioSlice` : Données portfolio
    -   [ ] `tradesSlice` : Historique trades
    -   [ ] `aiAgentSlice` : Décisions IA
    -   [ ] `marketSlice` : Données marché
    -   [ ] `logsSlice` : Logs système
    -   [ ] `uiSlice` : Thème, langue, préférences

### 1.6. React Router ⚠️ À FAIRE
Routes à configurer :
-   [ ] `/` → Redirect vers `/dashboard`
-   [ ] `/login` → LoginPage (publique)
-   [ ] `/dashboard` → DashboardPage (protégée)
-   [ ] `/trading` → TradingPage (protégée)
-   [ ] `/command` → CommandPage (protégée)
-   [ ] `/settings` → SettingsPage (protégée)
-   [ ] AuthenticationGuard pour routes protégées

### 1.7. Layout Principal ⚠️ À FAIRE
-   [x] Fichiers créés : Header.tsx, Sidebar.tsx, Footer.tsx
-   [ ] Implémenter Header :
    -   [ ] Logo et titre
    -   [ ] Indicateur statut bot (via Redux)
    -   [ ] Menu utilisateur
    -   [ ] Sélecteur thème
-   [ ] Implémenter Sidebar :
    -   [ ] Navigation avec icônes Lucide
    -   [ ] État actif des liens
    -   [ ] Collapsible/responsive
-   [ ] Layout responsive mobile

### 1.8. i18n Configuration ✅ PARTIELLEMENT
-   [x] `src/lib/i18n.ts` créé
-   [x] Fichiers traduction créés (en/fr)
-   [ ] Configurer i18next correctement
-   [ ] Ajouter traductions de base
-   [ ] Hook `useTranslation` dans composants

### 1.9. Authentification JWT ⚠️ À FAIRE
**Note**: Pas de Clerk/Auth0, utilisation de JWT FastAPI
-   [ ] Service `authService.ts` :
    -   [ ] Login avec email/password
    -   [ ] Stockage token localStorage
    -   [ ] Refresh token si nécessaire
    -   [ ] Logout et cleanup
-   [ ] AuthenticationGuard :
    -   [ ] Vérifier token valide
    -   [ ] Redirect si non authentifié
    -   [ ] Passer user context
-   [ ] Intercepteur Axios pour JWT

### 1.10. Socket.io Client ✅ STRUCTURE
-   [x] `src/lib/socketClient.ts` créé
-   [ ] Configuration complète :
    -   [ ] URL backend depuis .env
    -   [ ] Auth avec token JWT
    -   [ ] Reconnexion automatique
-   [ ] Listeners pour events :
    -   [ ] `bot_status_update`
    -   [ ] `portfolio_update`
    -   [ ] `new_trade_executed`
    -   [ ] `ai_agent_decision`
    -   [ ] `market_data_update`
    -   [ ] `system_health_update`
    -   [ ] `new_log_entry`
-   [ ] Dispatch actions Redux

## Phase 1.5: Intégration Backend ⚠️ DÉPENDANCES

### Prérequis Backend (voir todo/01-todo-core.md)
Les endpoints suivants doivent être implémentés côté backend :

#### API REST (FastAPI)
- [ ] **Auth** : POST `/api/v1/auth/login`
- [ ] **Bot** : `/api/v1/bot/start`, `/stop`, `/pause`, `/status`
- [ ] **Config** : GET/POST `/api/v1/config`
- [ ] **Trades** : GET `/api/v1/trades/history`, POST `/manual`
- [ ] **Portfolio** : GET `/api/v1/portfolio/snapshot`
- [ ] **AI** : GET `/api/v1/ai/decisions/history`
- [ ] **System** : GET `/api/v1/system/health`, `/logs`

#### Socket.io Events
Backend doit émettre :
- [ ] `bot_status_update` : État bot temps réel
- [ ] `portfolio_update` : Updates portfolio
- [ ] `new_trade_executed` : Notifications trades
- [ ] `ai_agent_decision` : Décisions IA
- [ ] Autres events définis

### Configuration Environnement
Variables `.env` requises :
```env
VITE_API_URL=http://localhost:8000
VITE_SOCKET_URL=http://localhost:8000
```

## Phase 2: Développement des Panneaux ⚠️ À FAIRE

### 2.1. Portfolio Overview
Composants à créer :
-   [ ] `PortfolioValue.tsx` : Valeur totale + sparkline
-   [ ] `AssetAllocation.tsx` : PieChart Recharts
-   [ ] `PortfolioChart.tsx` : LineChart performance
-   [ ] `HoldingsTable.tsx` : Table positions
-   [ ] `RiskIndicators.tsx` : Sharpe, Sortino

### 2.2. Trading Activity
-   [ ] `RecentTradesTable.tsx` : Historique trades
-   [ ] `TradeDetails.tsx` : Dialog détails trade
-   [ ] `PerformanceMetrics.tsx` : Taux succès, P&L
-   [ ] `ActiveOrders.tsx` : Ordres ouverts

### 2.3. Market Intelligence
-   [ ] `MarketSentiment.tsx` : Gauge sentiment
-   [ ] `Watchlist.tsx` : Tokens avec signaux
-   [ ] `PriceChart.tsx` : Graphique prix + prédictions
-   [ ] `AIInsights.tsx` : Flux décisions IA

### 2.4. Command & Control
-   [ ] `BotControls.tsx` : Start/Stop/Pause
-   [ ] `StrategySelector.tsx` : Choix stratégie
-   [ ] `ManualTradeForm.tsx` : Trade manuel
-   [ ] `BotStatus.tsx` : État cycle bot

### 2.5. System Health
-   [ ] `ServiceStatus.tsx` : Badges santé services
-   [ ] `ResourceMetrics.tsx` : CPU/RAM si disponible
-   [ ] `LogViewer.tsx` : Logs temps réel filtrables

### 2.6. Settings
-   [ ] `ConfigEditor.tsx` : Formulaire config bot
-   [ ] `NotificationSettings.tsx` : Préférences notifs
-   [ ] `ThemeSelector.tsx` : Light/Dark/System
-   [ ] `LanguageSelector.tsx` : Choix langue

## Phase 3: Finalisation ⚠️ À FAIRE

### 3.1. Responsive Design
-   [ ] Breakpoints Tailwind
-   [ ] Navigation mobile
-   [ ] Graphiques adaptables

### 3.2. Tests
-   [ ] Tests unitaires composants (Vitest)
-   [ ] Tests Redux slices
-   [ ] Tests Socket.io mocks
-   [ ] Tests E2E si temps

### 3.3. Optimisations
-   [ ] Code splitting routes
-   [ ] Lazy loading composants
-   [ ] Memo composants lourds
-   [ ] Debounce Socket.io

### 3.4. Gestion Erreurs
-   [ ] ErrorBoundary global
-   [ ] Toast notifications (ShadCN)
-   [ ] Retry failed requests
-   [ ] Offline handling

### 3.5. Build Production
-   [ ] Variables env production
-   [ ] Optimisation bundle
-   [ ] PWA manifest (optionnel)
-   [ ] Docker nginx config

## Communication Backend-Frontend

### Flux Authentification
1. Login : POST `/api/v1/auth/login` → Token JWT
2. Store token localStorage
3. Axios interceptor ajoute `Authorization: Bearer <token>`
4. Socket.io auth avec token dans handshake

### Flux Données Temps Réel
1. Connect Socket.io avec JWT
2. Backend émet events
3. Client dispatch Redux actions
4. Composants React re-render

### Gestion État Global (Redux)
```typescript
// Exemple portfolioSlice
interface PortfolioState {
  total_value_usd: number;
  pnl_24h_usd: number;
  positions: Position[];
  isLoading: boolean;
  lastUpdated: string | null;
}

// Socket.io listener
socket.on('portfolio_update', (data) => {
  dispatch(updatePortfolio(data));
});
```

## Ordre de Développement Recommandé

1. **Setup de base** :
   - [ ] Installer toutes dépendances
   - [ ] Configurer ShadCN/UI
   - [ ] Setup Redux store de base
   - [ ] Router avec auth guard

2. **Authentification** :
   - [ ] Page login fonctionnelle
   - [ ] Service auth avec JWT
   - [ ] Protection routes

3. **Layout & Navigation** :
   - [ ] Header avec statut bot
   - [ ] Sidebar navigation
   - [ ] Layout responsive

4. **Socket.io & État** :
   - [ ] Connexion Socket.io
   - [ ] Redux slices principales
   - [ ] Listeners events

5. **Dashboard de base** :
   - [ ] Portfolio overview
   - [ ] Bot status
   - [ ] Trades récents

6. **Fonctionnalités avancées** :
   - [ ] Graphiques interactifs
   - [ ] Trading manuel
   - [ ] Logs temps réel

## Métriques de Succès
- [ ] Temps chargement initial < 3s
- [ ] Updates Socket.io < 100ms latence
- [ ] Score Lighthouse > 90
- [ ] Zero erreurs console production
- [ ] Responsive tous devices