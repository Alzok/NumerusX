# 🔧 Configuration Environnement NumerusX

## Variables d'Environnement Requises

### 1. Créer le fichier `.env`
```bash
cp .env.example .env
```

### 2. Configuration Minimale (Démarrage Rapide)
```env
# Sécurité (OBLIGATOIRE en production)
SECRET_KEY=your-super-secret-key-at-least-32-characters

# Base de données
DATABASE_URL=sqlite:///./numerusx.db

# Redis
REDIS_URL=redis://redis:6379

# Trading (valeurs par défaut sécurisées)
INITIAL_BALANCE=1000
MAX_TRADE_AMOUNT=50
RISK_PERCENTAGE=1.0

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 3. Configuration Complète (Production)

#### Sécurité
```env
SECRET_KEY=your-production-secret-key-very-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### Solana & Trading
```env
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_PRIVATE_KEY=your-actual-private-key
JUPITER_API_URL=https://quote-api.jup.ag/v6
```

#### AI Services
```env
GOOGLE_API_KEY=your-google-ai-studio-key
OPENAI_API_KEY=your-openai-api-key
MODEL_CONFIDENCE_THRESHOLD=0.75
```

#### Auth0 (Frontend)
```env
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=http://localhost:8000
```

## 🚀 Scripts de Configuration Automatique

### 1. Configuration Développement
```bash
# Script à créer : setup-dev.sh
#!/bin/bash
echo "🔧 Configuration développement NumerusX"

# Copier exemple si .env n'existe pas
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Fichier .env créé"
fi

# Générer une clé secrète sécurisée
SECRET_KEY=$(openssl rand -hex 32)
sed -i "s/your-secret-key-change-in-production/$SECRET_KEY/" .env
echo "✅ Clé secrète générée"

# Configuration développement
echo "DEBUG=true" >> .env
echo "ENVIRONMENT=development" >> .env
echo "✅ Configuration développement appliquée"
```

### 2. Vérification Configuration
```bash
# Script à créer : check-config.sh
#!/bin/bash
echo "🔍 Vérification configuration NumerusX"

# Vérifier variables critiques
if grep -q "your-secret-key" .env; then
    echo "❌ SECRET_KEY par défaut détectée"
    exit 1
fi

if grep -q "your-solana-private-key" .env; then
    echo "⚠️  Clé Solana par défaut (OK pour développement)"
fi

echo "✅ Configuration semble valide"
```

## 🐳 Configuration Docker

### Variables pour Docker Compose
```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - RELOAD=true
  
  frontend:
    environment:
      - VITE_DEV_MODE=true
      - VITE_DEBUG=true
```

### Secrets Production
```yaml
# docker-compose.prod.yml
services:
  backend:
    secrets:
      - solana_private_key
      - google_api_key
    environment:
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  solana_private_key:
    external: true
  google_api_key:
    external: true
```

## 🔒 Sécurité

### Variables Sensibles (NE JAMAIS COMMITER)
- `SECRET_KEY`
- `SOLANA_PRIVATE_KEY`  
- `GOOGLE_API_KEY`
- `OPENAI_API_KEY`
- Clés Auth0

### Vérification .gitignore
```bash
# Vérifier que .env est ignoré
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
```

## 🧪 Tests de Configuration

### Test Backend
```bash
curl -f http://localhost:8000/health
```

### Test Frontend  
```bash
curl -f http://localhost:5173
```

### Test WebSocket
```bash
# Avec wscat
wscat -c ws://localhost:8000/ws
```

## 📊 Monitoring Configuration

### Health Check Endpoints
- Backend: `GET /health`
- API: `GET /api/v1/system/health`
- Database: `GET /api/v1/system/database`
- Redis: `GET /api/v1/system/redis`

### Variables Monitoring
```env
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO
ACCESS_LOG=true
```

## 🔄 Mise à Jour Configuration

### 1. Nouvelle Variable Ajoutée
```bash
# Vérifier si nouvelle variable manque
grep -q "NEW_VARIABLE" .env || echo "NEW_VARIABLE=default_value" >> .env
```

### 2. Migration Automatique
```bash
# Script pour migrer anciennes configurations
python scripts/migrate_env.py
```

Cette configuration devrait permettre un démarrage rapide et sécurisé de NumerusX ! 🚀 

## Variables d'Environnement Requises

### 1. Créer le fichier `.env`
```bash
cp .env.example .env
```

### 2. Configuration Minimale (Démarrage Rapide)
```env
# Sécurité (OBLIGATOIRE en production)
SECRET_KEY=your-super-secret-key-at-least-32-characters

# Base de données
DATABASE_URL=sqlite:///./numerusx.db

# Redis
REDIS_URL=redis://redis:6379

# Trading (valeurs par défaut sécurisées)
INITIAL_BALANCE=1000
MAX_TRADE_AMOUNT=50
RISK_PERCENTAGE=1.0

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 3. Configuration Complète (Production)

#### Sécurité
```env
SECRET_KEY=your-production-secret-key-very-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### Solana & Trading
```env
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_PRIVATE_KEY=your-actual-private-key
JUPITER_API_URL=https://quote-api.jup.ag/v6
```

#### AI Services
```env
GOOGLE_API_KEY=your-google-ai-studio-key
OPENAI_API_KEY=your-openai-api-key
MODEL_CONFIDENCE_THRESHOLD=0.75
```

#### Auth0 (Frontend)
```env
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=http://localhost:8000
```

## 🚀 Scripts de Configuration Automatique

### 1. Configuration Développement
```bash
# Script à créer : setup-dev.sh
#!/bin/bash
echo "🔧 Configuration développement NumerusX"

# Copier exemple si .env n'existe pas
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Fichier .env créé"
fi

# Générer une clé secrète sécurisée
SECRET_KEY=$(openssl rand -hex 32)
sed -i "s/your-secret-key-change-in-production/$SECRET_KEY/" .env
echo "✅ Clé secrète générée"

# Configuration développement
echo "DEBUG=true" >> .env
echo "ENVIRONMENT=development" >> .env
echo "✅ Configuration développement appliquée"
```

### 2. Vérification Configuration
```bash
# Script à créer : check-config.sh
#!/bin/bash
echo "🔍 Vérification configuration NumerusX"

# Vérifier variables critiques
if grep -q "your-secret-key" .env; then
    echo "❌ SECRET_KEY par défaut détectée"
    exit 1
fi

if grep -q "your-solana-private-key" .env; then
    echo "⚠️  Clé Solana par défaut (OK pour développement)"
fi

echo "✅ Configuration semble valide"
```

## 🐳 Configuration Docker

### Variables pour Docker Compose
```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - RELOAD=true
  
  frontend:
    environment:
      - VITE_DEV_MODE=true
      - VITE_DEBUG=true
```

### Secrets Production
```yaml
# docker-compose.prod.yml
services:
  backend:
    secrets:
      - solana_private_key
      - google_api_key
    environment:
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  solana_private_key:
    external: true
  google_api_key:
    external: true
```

## 🔒 Sécurité

### Variables Sensibles (NE JAMAIS COMMITER)
- `SECRET_KEY`
- `SOLANA_PRIVATE_KEY`  
- `GOOGLE_API_KEY`
- `OPENAI_API_KEY`
- Clés Auth0

### Vérification .gitignore
```bash
# Vérifier que .env est ignoré
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
```

## 🧪 Tests de Configuration

### Test Backend
```bash
curl -f http://localhost:8000/health
```

### Test Frontend  
```bash
curl -f http://localhost:5173
```

### Test WebSocket
```bash
# Avec wscat
wscat -c ws://localhost:8000/ws
```

## 📊 Monitoring Configuration

### Health Check Endpoints
- Backend: `GET /health`
- API: `GET /api/v1/system/health`
- Database: `GET /api/v1/system/database`
- Redis: `GET /api/v1/system/redis`

### Variables Monitoring
```env
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO
ACCESS_LOG=true
```

## 🔄 Mise à Jour Configuration

### 1. Nouvelle Variable Ajoutée
```bash
# Vérifier si nouvelle variable manque
grep -q "NEW_VARIABLE" .env || echo "NEW_VARIABLE=default_value" >> .env
```

### 2. Migration Automatique
```bash
# Script pour migrer anciennes configurations
python scripts/migrate_env.py
```

Cette configuration devrait permettre un démarrage rapide et sécurisé de NumerusX ! 🚀 