# 🏗️ Ordre d'Exécution Recommandé

## Phase 0: Harmonisation (NOUVELLE PHASE NÉCESSAIRE)
- [x] Corriger les incohérences de versions (en attente de la mise à jour manuelle de .env.example par l'utilisateur pour gemini-2.5-flash-preview-05-20)
- [x] Mettre à jour la structure du projet (correction `README.md` pour `ai_agent/` effectuée)
- [x] Harmoniser l'état des tâches (revue des sections ajoutées et des stratégies clés effectuée)

## Phase 1: Infrastructure
- [ ] Configuration de base (corrigée)
- [ ] Jupiter API Client
- [ ] Base de données (nouveau fichier TODO)

## Phase 2: AI Agent Core
- [ ] GeminiClient avec tests
- [ ] AIAgent avec validation
- [ ] Intégration DexBot

## Phase 3: Backend API
- [ ] Endpoints FastAPI
- [ ] Socket.io integration
- [ ] Middleware de sécurité

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