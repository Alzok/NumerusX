# NumerusX - Guide de Développement de l'Interface Utilisateur (UI) avec React et ShadCN/UI 🚀

**Prompt pour l'IA**: Ta mission est de concevoir et de développer une interface utilisateur (UI) **exceptionnelle** pour NumerusX en utilisant React, ShadCN/UI, Tailwind CSS, Recharts, Redux, Socket.io (ou Pusher), Clerk/Auth0, et i18next. L'UI doit être claire, moderne, minimaliste, hautement interactive, et permettre une gestion intuitive et puissante de l'application. Assure-toi de la cohérence avec les fonctionnalités existantes et prévues du bot, et vise une expérience utilisateur (UX) de premier ordre.

## Objectifs Généraux de l'UI:

-   **Contrôle Centralisé et Intuitif**: Démarrer, arrêter, configurer et surveiller le bot avec aisance.
-   **Feedback Dynamique et Compréhensible**: Afficher l'état du bot, les logs, les actions en cours et les "pensées" de l'IA de manière transparente.
-   **Visualisation de Données Avancée**: Présenter les performances, les trades, et l'analyse de marché via des graphiques interactifs (`Recharts`), des heatmaps, et des visualisations innovantes.
-   **Esthétique Moderne et Personnalisable**: Interface épurée, élégante (grâce à `ShadCN/UI` et `Tailwind CSS`), avec des options de personnalisation (thèmes, widgets).
-   **Réactivité et Performance**: L'interface doit être fluide, se mettre à jour dynamiquement (`Socket.io`/`Pusher` et `Redux`) sans latence perceptible, et optimisée pour les performances.
-   **Sécurité**: Authentification robuste avec `Clerk/Auth0`.
-   **Internationalisation (i18n)**: Prise en charge multilingue avec `i18next` et `react-i18next`.
-   **Accessibilité (A11y)**: Respecter les standards d'accessibilité (WCAG).

## Stack Technologique Frontend:

*   **Framework**: React.js (avec Vite.js pour le build)
*   **Composants UI**: ShadCN/UI
*   **Styling**: Tailwind CSS
*   **Graphiques**: Recharts (intégré avec ShadCN/UI)
*   **Gestion d'État**: Redux (avec Redux Toolkit)
*   **Communication Temps Réel**: Socket.io (préféré) ou Pusher
*   **Authentification**: Clerk ou Auth0
*   **Internationalisation**: i18next avec react-i18next
*   **Typage**: TypeScript

**Articulation des Technologies UI:**

L'interface utilisateur sera construite avec **React.js** comme bibliothèque fondamentale pour la création de composants interactifs. **ShadCN/UI** fournira une collection de composants d'interface utilisateur réutilisables et esthétiques, qui sont eux-mêmes construits sur Radix UI et stylisés avec **Tailwind CSS**. Tailwind CSS sera également utilisé pour tout stylage utilitaire personnalisé nécessaire au-delà des composants ShadCN/UI. Pour la visualisation de données, **Recharts** sera intégré dans les composants React pour créer des graphiques interactifs. L'état global de l'application, y compris les données temps réel provenant de Socket.io, les préférences utilisateur (comme le thème ou la langue via i18next), et l'état général de l'UI, sera géré par **Redux** (avec Redux Toolkit). Les composants React s'abonneront à l'état Redux (via `useSelector`) et dispatcheront des actions pour le modifier, et les données de cet état (par exemple, les performances du portefeuille) seront passées comme props aux composants Recharts pour affichage.

## Structure du Projet Frontend (Exemple):

```
numerusx-ui/
├── public/
│   └── locales/      # Pour les fichiers de traduction i18next
├── src/
│   ├── app/          # Logique Redux (store, reducers, actions)
│   ├── assets/       # Images, polices, etc.
│   ├── components/   # Composants React réutilisables (ShadCN/UI customisés)
│   │   ├── charts/   # Composants graphiques spécifiques basés sur Recharts
│   │   ├── layout/   # Composants de structure (Header, Sidebar, Footer)
│   │   └── ui/       # Petits composants UI génériques
│   ├── features/     # Modules fonctionnels (Portfolio, Trading, AI Insights, etc.)
│   │   └── Portfolio/
│   │       ├── components/
│   │       ├── PortfolioSlice.ts  # Redux slice
│   │       └── PortfolioView.tsx
│   ├── hooks/        # Hooks React customisés
│   ├── lib/          # Utilitaires, helpers, config i18n, client Socket.io
│   ├── pages/        # Composants de page principaux (Dashboard, Settings, Login)
│   ├── services/     # Logique d'appel API backend (hors Socket.io)
│   ├── styles/       # Styles globaux, config Tailwind
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .env
├── .eslintrc.cjs
├── .gitignore
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
└── tsconfig.json
```

## Phase 1: Initialisation du Projet Frontend et Structure de Base

-   [ ] **1.1. Création du Projet React avec Vite.js**:
    -   [ ] Initialiser un nouveau projet React avec TypeScript en utilisant Vite.
    -   [ ] `npm create vite@latest numerusx-ui -- --template react-ts`
-   [ ] **1.2. Installation des Dépendances Initiales**:
    -   [ ] `tailwindcss`, `postcss`, `autoprefixer`
    -   [ ] `shadcn-ui` (et ses dépendances: `lucide-react`, etc.)
    -   [ ] `recharts`
    -   [ ] `redux`, `react-redux`, `@reduxjs/toolkit`
    -   [ ] `socket.io-client`
    -   [ ] `clerk-react` ou `@auth0/auth0-react`
    -   [ ] `i18next`, `react-i18next`, `i18next-http-backend`, `i18next-browser-languagedetector`
    -   [ ] `react-router-dom` pour la navigation.
-   [ ] **1.3. Configuration de Tailwind CSS**:
    -   [ ] Initialiser Tailwind CSS (`npx tailwindcss init -p`).
    -   [ ] Configurer `tailwind.config.js` et `postcss.config.js`.
    -   [ ] Importer les directives Tailwind dans `src/index.css` (ou équivalent).
-   [ ] **1.4. Initialisation de ShadCN/UI**:
    -   [ ] `npx shadcn-ui@latest init`
    -   [ ] Choisir les options de configuration (CSS variables, etc.).
    -   [ ] Ajouter quelques composants de base (`button`, `card`, `input`, `dialog`, `dropdown-menu`, `tooltip`).
-   [ ] **1.5. Configuration de Redux Store**:
    -   [ ] Créer le store Redux (`src/app/store.ts`).
    -   [ ] Mettre en place un slice initial (ex: `uiSlice` pour gérer l'état de l'UI comme le thème).
    -   [ ] Envelopper l'application avec le `Provider` Redux.
-   [ ] **1.6. Mise en Place de la Navigation (React Router)**:
    -   [ ] Définir les routes principales (ex: `/login`, `/dashboard`, `/settings`).
    -   [ ] Créer des composants de page placeholder pour ces routes.
    -   [ ] Implémenter la logique de routes protégées après l'intégration de l'authentification.
-   [ ] **1.7. Layout Principal (Composants `Header`, `Sidebar`, `Footer`)**:
    -   [ ] Créer les composants de layout en utilisant `ShadCN/UI`.
    -   [ ] Header: Logo, titre, indicateur de statut global du bot (connecté via Redux/Socket.io), menu utilisateur (accès profil, déconnexion), sélecteur de thème.
    -   [ ] Sidebar: Navigation principale avec icônes (`lucide-react`) et labels. Collapsible.
    -   [ ] S'assurer que le layout est responsive.
-   [ ] **1.8. Internationalisation (i18n) avec i18next**:
    -   [ ] Configurer `i18next` (`src/lib/i18n.ts`).
    -   [ ] Mettre en place la détection de langue et le chargement des traductions (ex: `en.json`, `fr.json` dans `public/locales`).
    -   [ ] Utiliser `useTranslation` hook dans quelques composants pour tester.
    -   [ ] Ajouter un sélecteur de langue dans le Header ou les Settings.
-   [ ] **1.9. Authentification (Clerk/Auth0)**:
    -   [ ] Configurer le provider Clerk/Auth0 dans `App.tsx`.
    -   [ ] Créer les pages de Login, Signup, et potentiellement un callback.
    -   [ ] Implémenter les routes protégées qui nécessitent une authentification.
    -   [ ] Gérer l'état de l'utilisateur (via Clerk/Auth0 hooks et potentiellement synchronisé avec Redux).
-   [ ] **1.10. Connexion Socket.io Client**:
    -   [ ] Initialiser le client Socket.io (`src/lib/socketClient.ts`).
    -   [ ] Établir la connexion avec le backend FastAPI (l'URL du backend sera configurable via `.env`).
    -   [ ] Mettre en place des listeners pour des événements de test et dispatcher des actions Redux.

## Phase 1.5: Intégration Backend-Frontend (MANQUANTE)

- [ ] **1.5.1. API Endpoints Backend (FastAPI)**
    - [ ] **Objectif**: Implémenter les routes API REST nécessaires dans le backend FastAPI pour supporter les fonctionnalités de l'UI React.
    - [ ] **Structure des Fichiers API (Suggestion)**:
        - [ ] Créer le dossier `app/api/v1/` pour regrouper les routeurs de l'API v1.
        - [ ] Créer `app/api/v1/__init__.py`.
        - [ ] Implémenter des modules routeurs spécifiques dans `app/api/v1/`:
            - [ ] `bot_routes.py`: Endpoints pour contrôler le bot (`/start`, `/stop`, `/pause`, `/status`).
            - [ ] `config_routes.py`: Endpoints pour la gestion de la configuration (`/config` GET et POST).
            - [ ] `trades_routes.py`: Endpoints pour l'historique des trades et la soumission de trades manuels (`/trades/history`, `/trades/manual`).
            - [ ] `portfolio_routes.py`: Endpoints pour les informations du portefeuille (`/portfolio/snapshot`, `/portfolio/positions`).
            - [ ] `ai_decisions_routes.py`: Endpoints pour l'historique des décisions de l'IA et leur raisonnement (`/ai/decisions/history`, `/ai/decisions/{decision_id}/reasoning`).
            - [ ] `system_routes.py`: Endpoints pour la santé du système et les logs (`/system/health`, `/system/logs`).
    - [ ] **Intégration dans `app/main.py`**: Inclure ces routeurs dans l'application FastAPI principale.
    - [ ] **Modèles Pydantic**: Définir des modèles Pydantic pour les requêtes et les réponses de ces endpoints pour assurer la validation et la documentation automatique (Swagger/OpenAPI).

- [ ] **1.5.2. Middleware et Sécurité Backend (FastAPI)**
    - [ ] **Objectif**: Mettre en place les middlewares FastAPI nécessaires pour la sécurité, la journalisation et la gestion des requêtes.
    - [ ] **Détails**:
        - [ ] **Middleware JWT**: Créer un middleware FastAPI (ou utiliser des dépendances FastAPI) pour valider les tokens JWT (provenant de Clerk/Auth0) sur les endpoints API protégés et sur la connexion Socket.io (lors du handshake initial).
        - [ ] **Rate Limiting**: Implémenter un rate limiter (ex: avec `fastapi-limiter` et Redis) sur les endpoints API pour prévenir les abus.
        - [ ] **CORS**: Configurer le middleware CORS (`CORSMiddleware`) dans FastAPI pour autoriser les requêtes provenant du domaine du frontend React.
        - [ ] **Middleware de Logging des Requêtes**: Mettre en place un middleware pour journaliser les détails de chaque requête API reçue (méthode, chemin, statut, temps de réponse).

## Phase 1.6: Configuration Build et Déploiement

- [ ] **1.6.1. Configuration Vite pour production**
    - [ ] Configurer vite.config.ts pour optimisation build
    - [ ] Ajouter variables d'environnement pour différents environnements
    - [ ] Configurer proxy pour développement local
    - [ ] Optimiser les imports pour réduire bundle size

- [ ] **1.6.2. Scripts NPM**
    - [ ] Script dev pour développement avec HMR
    - [ ] Script build pour production
    - [ ] Script preview pour test build local
    - [ ] Script type-check pour validation TypeScript

## Phase 2: Développement des Fonctionnalités de l'UI par Panneau

*Pour chaque panneau, créer un répertoire dédié dans `src/features/` avec ses propres composants, slice Redux si nécessaire, et vue principale.*

### Étape 2.1: Panneau "Portfolio Overview"
-   [ ] **Affichage de la Valeur Totale du Portefeuille**:
    -   [ ] Label principal clair et visible, mis à jour en temps réel via Redux/Socket.io.
    -   [ ] "Sparkline" (`Recharts`) à côté de la valeur totale montrant la tendance récente.
    -   [ ] Variation sur 24h, 7j, 30j (avec sélecteur `Tabs` de ShadCN/UI).
-   [ ] **Graphique d'Allocation d'Actifs Interactif (`Recharts`)**:
    -   [ ] `PieChart` (Donut) ou `Treemap` (si Recharts le supporte bien, sinon simuler avec des `div`s).
    -   [ ] Afficher les allocations par actif, avec tooltips interactifs.
-   [ ] **Graphique de Performance du Portefeuille (`Recharts`)**:
    -   [ ] `LineChart` ou `AreaChart` pour l'évolution de la valeur du portefeuille.
    -   [ ] Sélecteur de période.
    -   [ ] Superposition d'événements clés (via Redux).
-   [ ] **Tableau des Positions ("Holdings") (`ShadCN/UI Table`)**:
    -   [ ] Colonnes: Actif (logo + symbole), Quantité, Prix d'Achat Moyen, Prix Actuel, Valeur Totale, P&L Non Réalisé (montant et %), Variation 24h (%).
    -   [ ] Données mises à jour en temps réel.
    -   [ ] Actions par ligne (menu contextuel `DropdownMenu`).
-   [ ] **Indicateurs de Risque du Portefeuille**:
    -   [ ] Afficher Sharpe Ratio, Sortino Ratio (calculés côté backend, transmis via API/Socket).

### Étape 2.2: Panneau "Trading Activity Center"
-   [ ] **Tableau des Trades Récents (`ShadCN/UI Table`)**:
    -   [ ] Colonnes: Paire, Type (Achat/Vente), Montant, Prix, Slippage, Frais, Statut, Raison du Trade (IA/Manuel), Timestamp.
    -   [ ] Cliquer pour voir détails (`Dialog` ShadCN/UI) avec snapshot des indicateurs et raisonnement IA.
-   [ ] **Analyse de Performance des Trades**:
    -   [ ] Affichage: Taux de réussite, Profit Factor.
    -   [ ] `BarChart` (`Recharts`) pour la distribution des P&L.
-   [ ] **Visualisation des Ordres Actifs (Limites, DCA)**:
    -   [ ] Tableau des ordres ouverts avec possibilité d'annulation.

### Étape 2.3: Panneau "Market Intelligence Hub"
-   [ ] **Indicateur Global de Sentiment de Marché**:
    -   [ ] Visualisation type "gauge" (peut être custom avec `Recharts` ou un composant SVG) ou `Progress` ShadCN/UI.
-   [ ] **Watchlist Dynamique et Interactive (`ShadCN/UI Card`s ou `Table`)**:
    -   [ ] Tokens avec signaux forts (BUY/SELL) de l'IA.
    -   [ ] Raisons du signal, mini-graphiques (`Recharts Sparklines`).
-   [ ] **Graphiques de Prix Interactifs (`Recharts`)**:
    -   [ ] `LineChart` ou `AreaChart` pour les prix, chandeliers si Recharts le permet facilement (sinon, une bibliothèque plus spécialisée pourrait être envisagée pour les chandeliers).
    -   [ ] Superposition des prédictions de prix de l'IA.
    -   [ ] Annotations pour les décisions IA.
-   [ ] **Section "AI Insights"**:
    -   [ ] Flux de "pensées" ou d'observations clés de l'IA, reçues via Socket.io.

### Étape 2.4: Panneau "Command & Control Center"
-   [ ] **Contrôle du Bot**:
    -   [ ] Boutons Start/Stop/Pause (`Button` ShadCN/UI) envoyant des commandes via Socket.io.
    -   [ ] Mode "Safe" (Paper Trading) vs "Live" (Sélecteur `Switch` ou `RadioGroup`).
    -   [ ] Indicateur visuel du cycle du bot.
-   [ ] **Gestion Fine des Stratégies**:
    -   [ ] Sélecteur de stratégie active (`Select` ShadCN/UI).
    -   [ ] Affichage des paramètres de la stratégie.
    -   [ ] Interface pour ajuster les paramètres (avec `Input`, `Slider`).
-   [ ] **Formulaire d'Entrée Manuelle de Trade**:
    -   [ ] Inputs pour paire, montant, type d'ordre.
    -   [ ] Affichage du solde disponible, estimation des frais.
    -   [ ] Bouton d'exécution.

### Étape 2.5: Panneau "System Health & Operations"
-   [ ] **Santé des Composants et Connexions**:
    -   [ ] Indicateurs (`Badge` ShadCN/UI avec couleurs) pour Backend API, WebSocket, `MarketDataProvider`, `TradingEngine`, `Database`, `JupiterApiClient`, `GeminiClient`.
    -   [ ] Données reçues via Socket.io.
-   [ ] **Métriques d'Utilisation des Ressources du Backend**:
    -   [ ] CPU, RAM (si le backend les expose).
-   [ ] **Visualisation des Logs Intégrée**:
    -   [ ] Panneau affichant les logs en temps réel (Socket.io).
    -   [ ] Filtres (niveau, module), recherche.

### Étape 2.6: Panneau "Settings & Customization"
-   [ ] **Éditeur des Paramètres de `Config` du Bot**:
    -   [ ] Formulaire groupé par catégorie (Trading, API, AI, Notifications).
    -   [ ] Sauvegarde via appel API au backend.
-   [ ] **Paramètres de Notification UI**:
    -   [ ] Activer/désactiver les notifications de l'UI.
-   [ ] **Gestion du Profil Utilisateur (via Clerk/Auth0)**.
-   [ ] **Sélecteur de Langue (i18next)**.
-   [ ] **Sélecteur de Thème (Light/Dark/System)**:
    -   [ ] Utiliser le support de thème de Tailwind/ShadCN/UI.
    -   [ ] Stocker la préférence dans `localStorage` et Redux.

## Phase 3: Améliorations Générales, Tests et Déploiement

-   [ ] **3.1. Réactivité Mobile et Tablette (Optimisation Finale)**.
-   [ ] **3.2. Tests**:
    -   [ ] Tests unitaires pour les composants critiques et la logique Redux (avec Jest/React Testing Library).
    -   [ ] Tests d'intégration pour les flux utilisateurs clés.
    -   [ ] Tests E2E (optionnel, avec Playwright ou Cypress).
-   [ ] **3.3. Optimisation des Performances**:
    -   [ ] `React.memo`, `useCallback`, `useMemo`.
    -   [ ] Code splitting (Vite gère cela en partie).
    -   [ ] Optimisation des rendus Redux.
-   [ ] **3.4. Gestion des Erreurs dans l'UI**:
    -   [ ] Composant `ErrorBoundary` global.
    -   [ ] Notifications `Toast` (ShadCN/UI) pour les erreurs.
-   [ ] **3.5. Accessibilité (A11y Review)**.
-   [ ] **3.6. Documentation Frontend**:
    -   [ ] Documenter la structure du projet, les décisions d'architecture clés, et comment lancer/développer l'UI.
-   [ ] **3.7. Build de Production**:
    -   [ ] Configurer le script `build` dans `package.json` (`vite build`).
-   [ ] **3.8. Dockerisation de l'UI**:
    -   [ ] Créer un `Dockerfile` pour l'application React (multi-stage build avec Nginx pour servir les fichiers statiques).
    -   [ ] Mettre à jour `docker-compose.yml` pour inclure le service frontend.

## Phase 4: Interaction Backend (FastAPI) <-> Frontend (React)

Cette section détaille la communication entre le backend FastAPI et le frontend React, principalement via Socket.io pour les données temps réel et les API REST pour les actions initiées par l'utilisateur.

### 4.1. Communication via Socket.io

Le client Socket.io dans React (`src/lib/socketClient.ts`) se connectera au serveur Socket.io géré par FastAPI.

-   **Événements Émis par le Backend (Exemples) et Gestion par Redux (Frontend)**:
    -   `connect`: Émis lors de la connexion initiale. Le frontend peut mettre à jour un état `isConnected` dans un slice Redux (ex: `systemSlice`).
    -   `disconnect`: Émis lors de la déconnexion. Mettre à jour `isConnected`.
    -   `bot_status_update`:
        -   **Payload**: `{ "status": "RUNNING" | "STOPPED" | "PAUSED" | "ERROR", "current_cycle": 123, "next_cycle_in_sec": 60, "error_message": "Optional error string" }`
        -   **Action Redux**: `dispatch(systemSlice.actions.setBotStatus(payload))`
        -   **Impact UI**: Mise à jour des indicateurs de statut dans le Header et le "Command & Control Center".
    -   `portfolio_update`:
        -   **Payload**: `{ "total_value_usd": 12345.67, "pnl_24h_usd": 150.0, "positions": [{"asset": "SOL", "amount": 10.5, "avg_buy_price": 150.0, "current_price": 165.0, "value_usd": 1732.5}], "available_cash_usdc": 4000.0 }`
        -   **Action Redux**: `dispatch(portfolioSlice.actions.updatePortfolio(payload))`
        -   **Impact UI**: Mise à jour des graphiques Recharts et des tableaux dans "Portfolio Overview".
    -   `new_trade_executed`:
        -   **Payload**: `{ "trade_id": "uuid", "pair": "SOL/USDC", "type": "BUY", "amount_tokens": 1.0, "price_usd": 165.0, "timestamp_utc": "...", "status": "FILLED", "reason_source": "AI_AGENT" | "MANUAL", "ai_reasoning_id": "optional_uuid_to_fetch_reasoning" }`
        -   **Action Redux**: `dispatch(tradesSlice.actions.addRecentTrade(payload))`
        -   **Impact UI**: Ajout à la table des trades dans "Trading Activity Center".
    -   `ai_agent_decision`:
        -   **Payload**: `{ "decision_id": "uuid", "decision": "BUY" | "SELL" | "HOLD", "token_pair": "SOL/USDC", "confidence": 0.85, "reasoning_snippet": "RSI bullish, MACD crossover.", "timestamp_utc": "...", "full_prompt_id": "optional_uuid_to_fetch_prompt", "key_inputs_summary": { ... } }`
        -   **Action Redux**: `dispatch(aiAgentSlice.actions.newAiDecision(payload))`
        -   **Impact UI**: Affichage dans le flux "AI Insights" ou mise à jour d'un log de décisions.
    -   `market_data_update`:
        -   **Payload**: `{ "pair": "SOL/USDC", "current_price": 165.30, "volume_24h_usd": 1200000000, "sentiment_score": 0.65 }` (peut être plus granulaire par token ou global)
        -   **Action Redux**: `dispatch(marketSlice.actions.updateMarketData(payload))`
        -   **Impact UI**: Mise à jour des graphiques de prix, indicateurs de sentiment dans "Market Intelligence Hub".
    -   `system_health_update`:
        -   **Payload**: `{ "service_name": "JupiterApiClient", "status": "OPERATIONAL" | "DEGRADED" | "ERROR", "last_error": "Optional error message"}` (un événement par service ou un snapshot global)
        -   **Action Redux**: `dispatch(systemSlice.actions.updateServiceHealth(payload))`
        -   **Impact UI**: Mise à jour des badges de statut dans "System Health & Operations".
    -   `new_log_entry`:
        -   **Payload**: `{ "level": "INFO" | "WARNING" | "ERROR", "module": "TradingEngine", "message": "Swap executed successfully.", "timestamp_utc": "..." }`
        -   **Action Redux**: `dispatch(logsSlice.actions.addLogEntry(payload))`
        -   **Impact UI**: Ajout à la visualisation des logs.
-   **Actions Initiées par le Frontend (Exemples)**:
    -   L'UI peut émettre des événements Socket.io vers le backend pour des actions de contrôle directes (ex: `start_bot`, `stop_bot`, `adjust_strategy_params`). Le backend confirmera ces actions via un événement de retour ou un `bot_status_update`.

### 4.2. Communication via API REST (pour actions et configurations)

Les API REST seront utilisées pour les actions qui ne nécessitent pas une communication bidirectionnelle constante ou pour récupérer des ensembles de données initiaux.

-   **Sécurisation**: Tous les endpoints API et la connexion Socket.io (via le handshake initial) seront sécurisés en utilisant des tokens JWT fournis par Clerk/Auth0. Le backend validera ces tokens.
-   **Exemples d'Endpoints FastAPI (et Actions Redux correspondantes si nécessaire)**:
    -   `POST /api/v1/bot/start`: Démarre le bot.
        -   **Action Redux (Optimiste)**: `dispatch(systemSlice.actions.setBotStatus({ status: "STARTING" }))` en attendant la confirmation via Socket.io.
    -   `POST /api/v1/bot/stop`: Arrête le bot.
    -   `POST /api/v1/bot/pause`: Met le bot en pause.
    -   `GET /api/v1/config`: Récupère la configuration actuelle du bot pour affichage/édition dans le panneau "Settings".
    -   `POST /api/v1/config`: Met à jour la configuration du bot.
        -   Nécessite une validation rigoureuse côté backend.
    -   `POST /api/v1/trades/manual`: Permet à l'utilisateur de soumettre un ordre manuel.
        -   Le backend valide et transmet au `TradeExecutor`.
    -   `GET /api/v1/trades/history?limit=50&offset=0`: Récupère l'historique des trades pour affichage paginé.
    -   `GET /api/v1/ai/decisions/history?limit=50&offset=0`: Récupère l'historique des décisions de l'IA.
    -   `GET /api/v1/portfolio/snapshot`: Récupère un snapshot complet du portefeuille (utile pour le chargement initial de l'UI).

### 4.3. Structure des Slices Redux (Exemple `portfolioSlice.ts`)

Basé sur la structure suggérée dans `src/features/Portfolio/PortfolioSlice.ts`:

```typescript
// src/features/Portfolio/PortfolioSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Position {
  asset: string;
  amount: number;
  avg_buy_price: number;
  current_price: number;
  value_usd: number;
}

interface PortfolioState {
  total_value_usd: number;
  pnl_24h_usd: number;
  positions: Position[];
  available_cash_usdc: number;
  isLoading: boolean;
  lastUpdated: string | null;
}

const initialState: PortfolioState = {
  total_value_usd: 0,
  pnl_24h_usd: 0,
  positions: [],
  available_cash_usdc: 0,
  isLoading: true,
  lastUpdated: null,
};

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setPortfolioLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    updatePortfolio: (state, action: PayloadAction<Partial<PortfolioState>>) => {
      // Merge new data with existing state
      Object.assign(state, action.payload);
      state.isLoading = false;
      state.lastUpdated = new Date().toISOString();
    },
    // Potentially actions for optimistic updates or specific position changes
  },
});

export const { setPortfolioLoading, updatePortfolio } = portfolioSlice.actions;
export default portfolioSlice.reducer;
```

Des slices similaires seraient créés pour `tradesSlice`, `aiAgentSlice`, `marketSlice`, `systemSlice`, `logsSlice`, etc., chacun gérant sa partie de l'état global de l'application et répondant aux événements Socket.io ou aux résultats d'appels API.

Les composants React (notamment ceux utilisant `Recharts`) s'abonneraient à ces slices Redux via le hook `useSelector` pour obtenir les données nécessaires et se réafficher lorsque l'état change.

## Sources de Données pour l'UI (via API Backend FastAPI & Socket.io):

Le frontend communiquera avec le backend FastAPI :
1.  **API RESTful**: Pour les actions (ex: sauvegarder les settings, initier un trade manuel) et la récupération de données initiales/historiques.
2.  **Socket.io**: Pour les mises à jour en temps réel (prix, état du bot, P&L, logs, décisions IA, santé des systèmes).

Ce guide est un point de départ. L'IA devra faire preuve d'initiative pour proposer des solutions élégantes et efficaces pour chaque fonctionnalité, en tirant parti au mieux de la stack technologique choisie. 