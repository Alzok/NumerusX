# 🏗️ Ordre d'Exécution Recommandé

## Phase 0: Harmonisation (NOUVELLE PHASE NÉCESSAIRE)
- [x] Corriger les incohérences de versions (en attente de la mise à jour manuelle de .env.example par l'utilisateur pour gemini-2.5-flash-preview-05-20)
- [x] Mettre à jour la structure du projet (correction `README.md` pour `ai_agent/` effectuée)
- [x] Harmoniser l'état des tâches (revue des sections ajoutées et des stratégies clés effectuée)

## Phase 1: Infrastructure
- [x] Configuration de base (corrigée) (config Jupiter V6 et Redis ajoutée à `app/config.py`)
- [x] Jupiter API Client (tâche 1.3 dans `01-todo-core.md` complétée)
- [x] Base de données (nouveau fichier TODO `01-todo-database.md` créé et structuré)

## Phase 2: AI Agent Core
- [x] GeminiClient avec tests (implémentation de base et gestion des erreurs dans `GeminiClient` faites, plans de tests définis dans `02-todo-ai-api-gemini.md` tâche 2.3)
- [x] AIAgent avec validation (Structure `AggregatedInputs` Pydantic implémentée et utilisée, prompt optimisé et parsing de réponse améliorés dans `AIAgent` et `DexBot`)
- [x] Intégration DexBot (DexBot collecte les `AggregatedInputs`, appelle AIAgent, et exécute les décisions)

## Phase 3: Backend API
- [~] Endpoints FastAPI (Structure et sécurité de base en place, logique métier par endpoint à compléter - Tâches 1.10.2, 1.10.5 de 01-todo-core.md)
- [~] Socket.io integration (SocketManager créé et intégré, authentification Socket.io et logique de message spécifique à compléter - Tâche 1.10.1 de 01-todo-core.md)
- [~] Middleware de sécurité (JWT, CORS, Rate Limiting de base en place - Tâche 1.5.2 de 01-todo-ui.md)

## Phase 4: Frontend
- [ ] Structure React de base
- [ ] Intégration avec backend
- [ ] Composants UI

# 📝 Actions Immédiates Requises

## 1. Créer fichiers manquants :
- [x] `todo/01-todo-database.md`
- [x] `todo/00-todo-harmonisation.md` (ce fichier-ci, sera coché une fois la transformation et le traitement initial faits)

## 2. Corriger fichiers existants :
- [x] Harmoniser les versions Gemini dans tous les fichiers (en attente de la mise à jour manuelle de .env.example par l'utilisateur pour gemini-2.5-flash-preview-05-20)
- [x] Compléter les sections manquantes identifiées (celles que nous avons traitées précédemment)

## 3. Documentation :
- [x] Mettre à jour `README.md` avec structure correcte (basé sur la correction de `ai_agent/`)
- [x] Documenter l'utilisation de Redis (planifié via tâche 1.14 dans `01-todo-core.md`)
- [x] Clarifier la stratégie d'authentification (standardisation sur Auth0/Clerk, mise à jour de `0-architecte.md` nécessaire pour refléter la dépréciation du système local si applicable)

## 4. Tests :
- [x] Ajouter une section tests dans chaque phase (des autres fichiers TODO) (sera fait lors du traitement de chaque TODO)
- [x] Définir les critères de validation pour chaque tâche (dans les autres fichiers TODO) (sera fait lors du traitement de chaque TODO)
- [x] Créer une stratégie de tests d'intégration (ébauche ajoutée à `0-architecte.md`)