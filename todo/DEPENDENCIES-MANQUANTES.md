# Dependencies Manquantes - NumerusX 📦

**Date :** 2024-12-19
**Status :** Action immédiate requise

## 🚨 Dependencies Critiques Manquantes

### Frontend React (numerusx-ui/) ✅ Excellent Stack Déjà Configuré

#### ✅ **Stack Déjà Parfait**
Votre setup Vite + React + Radix UI est excellent ! Vous avez :
```bash
# Composants UI - DÉJÀ INSTALLÉ ✅
@radix-ui/react-* (tous composants nécessaires)
tailwindcss + class-variance-authority 
lucide-react (icônes)
sonner (notifications)

# Fonctionnalités - DÉJÀ INSTALLÉ ✅  
react-hook-form + @hookform/resolvers
recharts (graphiques)
socket.io-client (temps réel)
@reduxjs/toolkit + react-redux
react-router-dom
zod (validation)

# Internationalization - DÉJÀ INSTALLÉ ✅
i18next + react-i18next
```

#### 📦 **Seulement 3 Packages Manquants**
```bash
# Tables avancées pour données de trading
npm install @tanstack/react-table@^8.10.7

# Cache intelligent et sync API  
npm install @tanstack/react-query@^5.8.4

# Client HTTP (optionnel - alternative à fetch)
npm install axios@^1.6.2
```

### Backend Python (/)
```bash
# Monitoring et observabilité
pip install prometheus-client>=0.17.0
pip install structlog>=23.1.0

# Validation et sérialisation avancée
pip install pydantic[email]>=2.0.0

# Performance et caching
pip install asyncpg>=0.28.0    # PostgreSQL async si migration
pip install aiocache>=0.12.0   # Cache avancé

# Security enhancements
pip install cryptography>=41.0.0
pip install argon2-cffi>=23.1.0  # Hash passwords plus sécurisé

# Testing avancé
pip install locust>=2.17.0     # Load testing
pip install faker>=19.0.0      # Test data generation
```

### DevOps et Infrastructure
```bash
# Docker optimizations
# Dans requirements.txt - versions optimisées
uvicorn[standard]==0.24.0     # Mise à jour
fastapi==0.104.1              # Mise à jour
pydantic==2.5.0               # Mise à jour v2

# CI/CD
# .github/workflows/test.yml à créer
# .github/workflows/deploy.yml à créer
```

## 📋 Commandes d'Installation Complètes

### 1. Frontend Setup
```bash
cd numerusx-ui/

# Core dependencies manquantes
npm install @tanstack/react-table@^8.10.7
npm install @tanstack/react-query@^5.8.4
npm install axios@^1.6.2
npm install react-toastify@^9.1.3
npm install framer-motion@^10.16.16

# Dev dependencies
npm install --save-dev jest@^29.7.0
npm install --save-dev @testing-library/react@^13.4.0
npm install --save-dev @testing-library/jest-dom@^6.1.5
npm install --save-dev @testing-library/user-event@^14.5.1
npm install --save-dev @types/jest@^29.5.8

# E2E testing (choisir un)
npm install --save-dev @playwright/test@^1.40.0
# OU
npm install --save-dev cypress@^13.6.0

# Build optimizations
npm install --save-dev @vitejs/plugin-react-swc@^3.5.0
npm install --save-dev vite-bundle-analyzer@^0.7.0

# Configuration files à créer
# jest.config.js
# playwright.config.ts OU cypress.config.ts
```

### 2. Backend Setup
```bash
# Depuis la racine du projet
pip install prometheus-client==0.17.1
pip install structlog==23.1.0
pip install aiocache==0.12.2
pip install argon2-cffi==23.1.0
pip install locust==2.17.0
pip install faker==20.1.0

# Mise à jour packages existants
pip install --upgrade uvicorn[standard]==0.24.0
pip install --upgrade fastapi==0.104.1
pip install --upgrade pydantic==2.5.0
```

### 3. Configuration Files Manquants

#### Frontend Jest Config
```javascript
// numerusx-ui/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

#### Frontend Setup Tests
```typescript
// numerusx-ui/src/setupTests.ts
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));
```

#### Backend Structured Logging
```python
# app/logging_config.py (à créer)
import structlog
import logging
import sys
from app.config import Config

def configure_structured_logging():
    """Configure structured logging with JSON output."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, Config.LOG_LEVEL.upper())
    )
```

## ⚠️ Dependencies Conflicts Potentiels

### Frontend
```json
// Vérifier compatibilité dans package.json
{
  "overrides": {
    "@types/react": "^18.2.56",
    "@types/react-dom": "^18.2.19"
  }
}
```

### Backend
```python
# Conflicts potentiels à surveiller
# pydantic v1 vs v2 (projet utilise v2)
# fastapi avec pydantic v2
# sqlalchemy 2.0 vs 1.x

# Vérifier avec:
pip check
```

## 🔧 Scripts d'Installation Automatisée

### Installation Frontend Complète
```bash
#!/bin/bash
# scripts/setup-frontend.sh

cd numerusx-ui/

echo "Installing core dependencies..."
npm install @tanstack/react-table @tanstack/react-query axios react-toastify framer-motion

echo "Installing dev dependencies..."
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event @types/jest

echo "Installing E2E testing..."
npm install --save-dev @playwright/test

echo "Installing build tools..."
npm install --save-dev @vitejs/plugin-react-swc vite-bundle-analyzer

echo "Creating config files..."
# Créer jest.config.js et setupTests.ts

echo "Frontend setup complete!"
```

### Installation Backend Complète
```bash
#!/bin/bash
# scripts/setup-backend.sh

echo "Installing monitoring dependencies..."
pip install prometheus-client==0.17.1 structlog==23.1.0

echo "Installing performance dependencies..."
pip install aiocache==0.12.2

echo "Installing security dependencies..."
pip install argon2-cffi==23.1.0

echo "Installing testing dependencies..."
pip install locust==2.17.0 faker==20.1.0

echo "Upgrading core packages..."
pip install --upgrade uvicorn[standard]==0.24.0 fastapi==0.104.1 pydantic==2.5.0

echo "Backend setup complete!"
```

## 📊 Verification Commands

### Frontend
```bash
cd numerusx-ui/
npm audit                    # Vérifier vulnérabilités
npm list @tanstack/react-table  # Vérifier installation
npm test                     # Lancer tests (après config)
npm run build               # Vérifier build
```

### Backend
```bash
pip check                   # Vérifier conflicts
python -m pytest tests/    # Lancer tests
python -c "import prometheus_client; print('OK')"  # Vérifier imports
```

## 🎯 Prochaines Actions

1. **Immédiat** (Aujourd'hui)
   - [ ] Installer dependencies frontend critiques
   - [ ] Configurer Jest pour tests
   - [ ] Installer monitoring backend basic

2. **Cette semaine**
   - [ ] Setup E2E testing (Playwright/Cypress)
   - [ ] Configurer structured logging
   - [ ] Créer scripts d'installation automatisée

3. **Prochaine semaine**
   - [ ] Load testing setup avec Locust
   - [ ] Performance monitoring complet
   - [ ] CI/CD pipeline avec nouvelles dependencies

---

**⚡ ACTION IMMEDIATE REQUISE** : Installer les dependencies frontend pour débloquer le développement UI 