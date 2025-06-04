# 🔍 Analyse Détaillée Docker & Frontend

## Problèmes Critiques Identifiés

### 1. Frontend Docker Setup ❌

#### Problème avec init-frontend.sh
Le script crée un projet Vite basique mais :
- **N'installe PAS** les dépendances essentielles listées dans todo/01-todo-ui.md
- **Structure incorrecte** : `index.html` dans `public/` au lieu de la racine
- **Manque** toute la structure de dossiers (components/, features/, etc.)
- **Pas de package.json complet** avec les scripts nécessaires

#### Dépendances Manquantes
```json
// Actuellement installé par init-frontend.sh :
- vite, @vitejs/plugin-react, react, react-dom, typescript
- tailwindcss, postcss, autoprefixer

// MANQUANT :
- @radix-ui/react-* (pour ShadCN/UI)
- lucide-react (icônes)
- recharts (graphiques) 
- @reduxjs/toolkit react-redux
- socket.io-client
- i18next react-i18next
- react-router-dom
- axios
- class-variance-authority clsx tailwind-merge
- tailwindcss-animate
```

#### Structure de Dossiers Manquante
Le script ne crée PAS :
- src/app/ (Redux store)
- src/components/auth/, charts/, layout/, ui/
- src/features/
- src/hooks/
- src/lib/
- src/pages/ (avec les 5 pages)
- src/services/
- public/locales/en/, public/locales/fr/

### 2. Backend Docker Setup ❌

#### Problème .env
- Docker monte `../.env` mais si le fichier n'existe pas → ÉCHEC
- Pas de mécanisme pour créer `.env` depuis `.env.example`

#### Structure API Manquante
- app/api/ n'existe pas
- app/api/v1/ n'existe pas
- Tous les fichiers routes manquent

### 3. Package.json Incorrect ❌

Le package.json créé par init-frontend.sh est minimal :
```json
{
  "name": "numerusx-ui",
  "private": true,
  "version": "0.0.0",
  "type": "module"
}
```

Il manque :
- Scripts (dev, build, preview, lint)
- Toutes les dépendances
- Configuration ESLint/Prettier

## Corrections Nécessaires

### 1. Nouveau init-frontend.sh Complet

```bash
#!/bin/sh
set -e

APP_DIR="/app/numerusx-ui"

# Créer .env backend si n'existe pas
if [ ! -f "/app/.env" ] && [ -f "/app/.env.example" ]; then
  cp /app/.env.example /app/.env
  echo "Created .env from .env.example"
fi

cd $APP_DIR

if [ ! -f "package.json" ]; then
  echo "Initializing complete NumerusX UI..."
  
  # 1. Package.json complet
  cat > package.json << 'EOF'
{
  "name": "numerusx-ui",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.0.4",
    "react-router-dom": "^6.20.1",
    "socket.io-client": "^4.7.2",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "lucide-react": "^0.294.0",
    "i18next": "^23.7.8",
    "react-i18next": "^13.5.0",
    "i18next-browser-languagedetector": "^7.2.0",
    "i18next-http-backend": "^2.4.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "tailwindcss-animate": "^1.0.7",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
EOF

  # 2. Créer TOUTE la structure
  mkdir -p src/app src/assets src/components/auth src/components/charts \
           src/components/layout src/components/ui src/features/Portfolio/components \
           src/hooks src/lib src/pages src/services \
           public/locales/en public/locales/fr

  # 3. Fichiers de configuration (vite, ts, tailwind, etc.)
  # ... (configs existantes dans le script actuel)

  # 4. index.html à la RACINE (pas dans public/)
  cat > index.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/logo.jpg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NumerusX - AI Trading Bot</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

  # 5. Créer TOUS les fichiers de base
  # ... (créer store.ts, pages, components, etc.)

  # 6. Fichiers i18n
  echo '{"welcome": "Welcome to NumerusX"}' > public/locales/en/translation.json
  echo '{"welcome": "Bienvenue sur NumerusX"}' > public/locales/fr/translation.json

  # 7. Variables d'environnement frontend
  cat > .env << 'EOF'
VITE_API_URL=http://backend:8000
VITE_SOCKET_URL=http://backend:8000
EOF

fi

npm install
npm run dev -- --host 0.0.0.0
```

### 2. Docker-compose.yml Amélioré

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ../
      dockerfile: Docker/backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ../app:/app/app
      - ../data:/app/data
      - ../logs:/app/logs
      - ../keys:/app/keys
      - ../models:/app/models
    environment:
      - PYTHONUNBUFFERED=1
    env_file:
      - ../.env
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    # Créer .env si n'existe pas
    command: >
      sh -c "
        if [ ! -f /app/.env ]; then
          cp /app/.env.example /app/.env
        fi &&
        uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload
      "

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ../numerusx-ui:/app/numerusx-ui
      - ../logo.jpg:/app/logo.jpg
    environment:
      - NODE_ENV=development
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5173"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --save 60 1 --loglevel warning
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
```

### 3. Backend Dockerfile Amélioré

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier code
COPY . .

# Créer structure API si n'existe pas
RUN mkdir -p app/api/v1

# Healthcheck endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
```

## Actions Immédiates

### 1. Créer Structure API Backend
```bash
mkdir -p app/api/v1
touch app/api/__init__.py app/api/v1/__init__.py
```

### 2. Créer Fichiers Routes Vides
- app/api/v1/auth_routes.py
- app/api/v1/bot_routes.py
- app/api/v1/config_routes.py
- app/api/v1/trades_routes.py
- app/api/v1/portfolio_routes.py
- app/api/v1/ai_decisions_routes.py
- app/api/v1/system_routes.py

### 3. Mettre à Jour main.py
Ajouter l'import et le montage des routes API v1

### 4. Créer Healthcheck Endpoint
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "numerusx-backend"}
```

## Validation Docker Compose Up

Avec ces corrections, `docker compose up` devrait :
1. ✅ Créer .env depuis .env.example si nécessaire
2. ✅ Installer TOUTES les dépendances frontend
3. ✅ Créer la structure complète de dossiers
4. ✅ Démarrer backend + frontend + Redis
5. ✅ Avoir des healthchecks fonctionnels
6. ✅ Permettre le hot-reload en dev

## Ordre d'Implémentation Recommandé

1. **Immédiat (Mode Architect)** :
   - ✅ Créer ce document d'analyse
   - Mettre à jour init-frontend.sh
   - Mettre à jour docker-compose.yml

2. **Mode Code Requis** :
   - Créer structure app/api/v1/
   - Créer tous les fichiers routes
   - Implémenter healthcheck
   - Créer app/models/ai_inputs.py

3. **Tests** :
   - docker compose down -v
   - rm -rf numerusx-ui/node_modules
   - docker compose up --build
   - Vérifier http://localhost:5173
   - Vérifier http://localhost:8000/docs