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

## Sources de Données pour l'UI (via API Backend FastAPI & Socket.io):

Le frontend communiquera avec le backend FastAPI :
1.  **API RESTful**: Pour les actions (ex: sauvegarder les settings, initier un trade manuel) et la récupération de données initiales/historiques.
2.  **Socket.io**: Pour les mises à jour en temps réel (prix, état du bot, P&L, logs, décisions IA, santé des systèmes).

Ce guide est un point de départ. L'IA devra faire preuve d'initiative pour proposer des solutions élégantes et efficaces pour chaque fonctionnalité, en tirant parti au mieux de la stack technologique choisie. 