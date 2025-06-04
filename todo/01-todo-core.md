# NumerusX - IA TODO List 🤖

**Prompt pour l'IA**: Exécute les tâches une par une. Quand tu as terminé une tâche, vérifie la cohérence du code par rapport à l'ensemble du projet et au contexte fourni. Une fois la vérification terminée et la cohérence assurée, passe en autonomie à la tâche suivante.

## Phase 1: Initialisation et Configuration de Base (Jupiter API v6) - FONDATIONS

**Objectif**: Configurer l'environnement, intégrer le SDK Jupiter, et établir les bases pour l'interaction avec l'API Jupiter v6.

- [x] **1.0.5. Création de la structure du sous-dossier ai_agent**
    - [x] ~~Créer le dossier `app/ai_agent/`~~ (Déjà créé)
    - [x] ~~Créer `app/ai_agent/__init__.py`~~ (Déjà créé)
    - [x] Structure confirmée et fonctionnelle

- [x] **1.0.6. Harmonisation des versions Gemini**
    - [x] Version finale confirmée : `gemini-2.5-flash-preview-05-20`
    - [x] `app/config.py` mis à jour avec `GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20"`
    - [x] `.env.example` doit être mis à jour manuellement par l'utilisateur
    - [x] Compatibilité `google-generativeai>=0.5.4` vérifiée dans `requirements.txt`

-   [x] **1.1.0 `app/config.py` (Jupiter API v6)** - Configuration complète implémentée

-   [x] **1.1.5. Configuration Redis**
    -   [x] REDIS_URL ajouté à app/config.py
    -   [x] REDIS_PASSWORD configuré
    -   [x] Documenter l'utilisation de Redis dans docs/redis_usage.md

-   [ ] **1.1.6. Installation Docker Simplifiée**
    -   [x] docker-compose.yml déplacé à la racine
    -   [x] README.md mis à jour avec installation Docker simple
    -   [x] Instructions `docker compose up` ajoutées
    -   [ ] Créer .env.example à la racine (globalIgnore bloqué)
    -   [ ] Créer numerusx-ui/.env.example (globalIgnore bloqué)
    -   [x] Section troubleshooting ajoutée

-   [x] **1.1.bis. `requirements.txt`**
    -   [x] `jupiter-python-sdk>=0.24.0` ajouté
    -   [x] `google-generativeai>=0.5.4` ajouté
    -   [x] `python-socketio` ajouté
    -   [x] Vérifier `python-jose[cryptography]` et `passlib[bcrypt]` pour JWT
    -   [x] Ajouter `fastapi-limiter` pour rate limiting

-   [x] **1.3. `app/utils/jupiter_api_client.py`** - Client Jupiter SDK complètement implémenté

-   [x] **1.4. `app/market/market_data.py`** - Refactorisé pour Jupiter SDK

-   [x] **1.5. Gestion des Erreurs** - Hiérarchie d'exceptions custom implémentée

-   [x] **1.6. `app/trading/trading_engine.py`** - Intégration Jupiter SDK complète

-   [x] **1.8. Fiabilisation de la Base de Données** - Nouveaux champs ajoutés

-   [ ] **1.9. Tests Unitaires et d'Intégration (Initiaux)**
    -   [ ] `tests/test_config.py`: Vérifier le chargement des nouvelles constantes
    -   [ ] `tests/test_jupiter_api_client.py`: Tests complets pour JupiterApiClient
    -   [ ] `tests/test_market_data.py`: Tests avec mocks JupiterApiClient
    -   [ ] `tests/test_trading_engine.py`: Tests execute_swap avec mocks
    -   [ ] `tests/test_database.py`: Tests nouveaux champs de trade

## Phase 1.bis: Configuration pour Nouvelle UI React et Backend

-   [ ] **1.10. `app/main.py` (Backend FastAPI - Modifications pour UI)**
    -   [x] **1.10.1. Intégration Socket.io (FastAPI)**:
        -   [x] `python-socketio` ajouté à requirements.txt
        -   [x] `app/socket_manager.py` créé avec classe `SocketManager`
        -   [x] Implémenter les événements Socket.io détaillés :
            -   [x] `connect` : Gestion connexion avec validation JWT
            -   [x] `disconnect` : Gestion déconnexion
            -   [x] `bot_status_update` : État du bot
            -   [x] `portfolio_update` : Mises à jour portfolio
            -   [x] `new_trade_executed` : Notification trades
            -   [x] `ai_agent_decision` : Décisions IA
            -   [x] `market_data_update` : Données marché
            -   [x] `system_health_update` : Santé système
            -   [x] `new_log_entry` : Streaming logs
        -   [x] Middleware d'authentification Socket.io JWT
    
    -   [x] **1.10.2. Structure API v1**:
        -   [x] Créer `app/api/` et `app/api/v1/`
        -   [x] Créer `app/api/v1/__init__.py`
        -   [x] Implémenter les modules routeurs :
            -   [x] `bot_routes.py` : Contrôle du bot
            -   [x] `config_routes.py` : Gestion configuration
            -   [x] `trades_routes.py` : Historique et trades manuels
            -   [x] `portfolio_routes.py` : Infos portfolio
            -   [x] `ai_decisions_routes.py` : Décisions IA
            -   [x] `system_routes.py` : Santé système et logs
        -   [x] Modèles Pydantic pour requêtes/réponses
        -   [x] Intégration dans `app/main.py`
    
    -   [x] **1.10.3. Middleware et Sécurité**:
        -   [x] Middleware JWT pour validation tokens
        -   [x] Rate limiting avec `fastapi-limiter` et Redis
        -   [x] Configuration CORS pour frontend React
        -   [x] Middleware logging des requêtes
        -   [x] Standardiser sur JWT (supprimer app/security/security.py)

-   [x] **1.11. `requirements.txt` (Ajouts pour Backend UI)** - Voir 1.1.bis ci-dessus

-   [x] **1.12. `Docker/` (Mises à Jour pour UI React)**
    -   [x] `Docker/frontend/Dockerfile` créé
    -   [x] `Docker/frontend/init-frontend.sh` créé
    -   [x] `Docker/frontend/nginx.conf` créé
    -   [x] `docker-compose.yml` mis à jour avec service frontend
    -   [x] Variables d'environnement à documenter

-   [x] **1.13. Suppression de `app/dashboard.py` et `app/gui.py`** - Fichiers NiceGUI supprimés

-   [x] **1.14. Documentation Redis**
    -   [x] Configuration ajoutée dans `app/config.py`
    -   [x] Créer `docs/redis_usage.md` avec cas d'usage :
        -   [x] Cache MarketDataProvider
        -   [x] Cache JupiterApiClient
        -   [x] Sessions utilisateur
        -   [x] Rate limiting
        -   [x] Buffer logs

## Phase 2: Développement du Cœur Agentique IA et Intégrations 🧠🤖

### 2.1. Conception et Implémentation de l'Agent IA
-   [x] **Création de `app/ai_agent.py`** - Classe AIAgent implémentée
-   [x] Méthode `decide_trade` asynchrone créée
-   [x] **Créer `app/models/ai_inputs.py`** pour structure AggregatedInputs :
    -   [x] `MarketDataInput` : Données de marché
    -   [x] `SignalSourceInput` : Signaux stratégies
    -   [x] `PredictionEngineInput` : Prédictions IA
    -   [x] `RiskManagerInput` : Contraintes risque
    -   [x] `SecurityCheckerInput` : Sécurité tokens
    -   [x] `PortfolioManagerInput` : État portfolio
    -   [x] Classe principale `AggregatedInputs` avec validation Pydantic

### 2.2. Refactorisation de DexBot
-   [x] DexBot initialise AIAgent
-   [x] Méthode `_run_cycle` collecte les données
-   [x] Agrégation basique des inputs
-   [x] Appel à `ai_agent.decide_trade`
-   [ ] Validation complète avec modèles Pydantic `AggregatedInputs`
-   [ ] Gestion ordres avancés (limites, DCA) si AIAgent les demande

### 2.3. Adaptation des Modules Fournisseurs
-   [x] Modules configurés pour fournir des données structurées
-   [ ] Vérifier formats compatibles avec `AggregatedInputs` Pydantic
-   [ ] Tests de cohérence des données entre modules

### 2.4. Intégration Base de Données et UI
-   [x] Créer table `ai_decisions` dans EnhancedDatabase
-   [x] Stocker raisonnements et inputs clés
-   [x] API endpoints pour récupérer historique décisions
-   [ ] Composants React pour afficher décisions IA

## Phase 3: Logique de Trading Raffinée et Améliorations

### 3.1. Amélioration des Inputs pour l'Agent IA
-   [x] `prediction_engine.py` fournit des inputs
-   [ ] Valider format et pertinence pour AIAgent
-   [ ] Tests qualité des prédictions

### 3.2. Utilisation des Outputs du RiskManager
-   [x] RiskManager fournit limites et contraintes
-   [ ] Vérifier intégration dans `AggregatedInputs`
-   [ ] Tests respect des limites par AIAgent

### 3.3. Exécution et Suivi Post-Décision
-   [x] TradeExecutor compatible avec ordres AIAgent
-   [x] Support ordres limites et DCA via TradingEngine
-   [ ] Gestion erreurs et feedback vers AIAgent
-   [ ] Métriques de performance par décision IA

## Phase 4: Interface Utilisateur et Fonctionnalités Avancées

### 4.1. Développement UI React
-   [ ] Se référer à `todo/01-todo-ui.md` pour détails complets
-   [ ] Priorité : connexion Socket.io et affichage état bot

### 4.2. Stratégies de Trading
-   [x] Framework BaseStrategy créé
-   [x] MomentumStrategy implémentée
-   [x] MeanReversionStrategy implémentée
-   [x] TrendFollowingStrategy implémentée
-   [x] StrategySelector créé
-   [ ] Tests de performance des stratégies
-   [ ] Intégration complète dans `AggregatedInputs`

## Phase 1.5: Tests et Validation (NOUVEAU) ✅

### 1.5.1. Tests d'Intégration
-   [x] **Suite de tests complète API + Socket.io**
    -   [x] Tests d'authentification JWT end-to-end
    -   [x] Tests de flux complet trading (Login → API → Database → Socket.io)
    -   [x] Tests de gestion des erreurs et validation des données
    -   [x] Tests concurrents et de performance
    -   [x] Tests de rooms Socket.io et événements spécialisés

### 1.5.2. Script de Validation Automatique
-   [x] **Script `test_api_imports.py`**
    -   [x] Test d'imports de tous les modules
    -   [x] Test de création et opérations database
    -   [x] Test d'initialisation Socket.io manager
    -   [x] Diagnostics et conseils de dépannage

### 1.5.3. Corrections de Cohérence du Projet
-   [x] **Incohérences résolues**
    -   [x] PortfolioManager avec signature cohérente
    -   [x] EnhancedDatabase avec `row_factory` pour accès dict-like
    -   [x] Imports manquants ajoutés dans requirements.txt
    -   [x] DexBot intégré avec Socket.io manager
    -   [x] Flux AI decision → Database → Socket.io complet

## Phase 1.6: Nouvelles Tâches Identifiées (NOUVEAU)

### 1.6.1. Optimisations à Implémenter
-   [ ] **Rate Limiting Avancé**
    -   [ ] Configuration Redis pour rate limiting
    -   [ ] Rate limiting par utilisateur et par endpoint
    -   [ ] Rate limiting adaptatif selon la charge

-   [ ] **Logging Avancé**
    -   [ ] Intégration logs dans database via `system_logs`
    -   [ ] Streaming logs en temps réel via Socket.io
    -   [ ] Rotation et archivage automatique des logs

-   [ ] **Monitoring et Métriques**
    -   [ ] Métriques de performance des API endpoints
    -   [ ] Monitoring des connexions Socket.io
    -   [ ] Alertes pour erreurs critiques

### 1.6.2. Sécurité Renforcée
-   [ ] **JWT Avancé**
    -   [ ] Refresh tokens
    -   [ ] Révocation de tokens
    -   [ ] Limitation de sessions simultanées

-   [ ] **Validation Renforcée**
    -   [ ] Validation des données de trading plus stricte
    -   [ ] Sanitisation des inputs utilisateur
    -   [ ] Protection contre les attaques de timing

### 1.6.3. Base de Données Avancée
-   [ ] **Optimisations Performance**
    -   [ ] Index composites pour requêtes fréquentes
    -   [ ] Partitioning des tables par date
    -   [ ] Archivage automatique des données anciennes

-   [ ] **Analytics et Reporting**
    -   [ ] Tables d'agrégation pour statistiques
    -   [ ] Views matérialisées pour dashboards
    -   [ ] Export automatique de rapports

## Points d'Attention Critiques

### Sécurité et Authentification
* **Action Requise** : Standardiser sur JWT FastAPI
* Supprimer `app/security/security.py` (système local obsolète)
* Implémenter validation JWT dans middleware FastAPI
* Sécuriser Socket.io avec tokens JWT

### Structure API
* **Action Requise** : Consolider dans `app/api/v1/`
* Supprimer duplication entre `app/main.py` et `app/api_routes.py`
* Créer structure modulaire par domaine (bot, config, trades, etc.)

### Tests Prioritaires
1. GeminiClient : Mocking API et gestion erreurs
2. AIAgent : Construction prompt et parsing JSON
3. Flux complet : DexBot -> AIAgent -> TradeExecutor
4. API endpoints avec authentification JWT
5. Events Socket.io avec et sans auth

### Documentation Urgente
1. `docs/redis_usage.md` : Cas d'usage et configuration
2. Guide authentification JWT pour développeurs
3. Architecture API v1 avec exemples
4. Flow de données Socket.io

## Ordre d'Exécution Recommandé

1. **Immédiat** :
   - Créer `app/models/ai_inputs.py`
   - Créer structure `app/api/v1/`
   - Documenter Redis dans `docs/redis_usage.md`

2. **Court terme** :
   - Implémenter endpoints API v1
   - Ajouter middleware JWT
   - Créer tests GeminiClient et AIAgent

3. **Moyen terme** :
   - Compléter events Socket.io
   - Créer table ai_decisions
   - Développer composants React de base

4. **Long terme** :
   - Optimiser prompts Gemini
   - Implémenter ordres avancés (limites, DCA)
   - Dashboard React complet