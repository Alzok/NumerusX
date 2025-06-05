# 👩‍💻 Guide de Développement NumerusX

## Démarrage Rapide

### 1. Prérequis
- Docker & Docker Compose
- Git
- IDE recommandé: VSCode avec extensions TypeScript/Python

### 2. Installation Ultra-Rapide
```bash
git clone https://github.com/votre-repo/numerusx.git
cd numerusx
./scripts/dev-tools.sh setup
./scripts/dev-tools.sh start
```

🎉 L'application sera disponible sur:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Structure du Projet

```
NumerusX/
├── 📱 numerusx-ui/              # Frontend React + TypeScript
│   ├── src/
│   │   ├── components/          # Composants réutilisables
│   │   ├── pages/              # Pages principales
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utilitaires & API client
│   │   └── store/              # State management
│   ├── public/                 # Assets statiques
│   └── package.json
│
├── 🐍 app/                      # Backend Python FastAPI
│   ├── api/                    # API routes
│   │   └── v1/                 # API version 1
│   ├── models/                 # Modèles de données
│   ├── trading/                # Logique de trading
│   ├── ai_agent/               # Agent IA central
│   ├── strategies/             # Stratégies de trading
│   ├── market/                 # Données de marché
│   ├── security/               # Sécurité & validation
│   └── utils/                  # Utilitaires
│
├── 🐳 Docker/                   # Configuration Docker
│   ├── backend/                # Dockerfile backend
│   └── frontend/               # Dockerfile frontend
│
├── 📋 todo/                     # Documentation TODO
├── 🧪 tests/                    # Tests automatisés
├── 📚 docs/                     # Documentation
└── 📝 scripts/                  # Scripts de développement
```

## Conventions de Code

### Python (Backend)

**Style**: Black + Flake8
```python
# Imports organization
from typing import List, Optional
import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models import Trade
from app.utils import logger

# Classes avec docstrings
class TradeDecision(BaseModel):
    """Décision de trading de l'Agent IA."""
    
    action: str  # BUY/SELL/HOLD
    confidence: float  # 0.0 - 1.0
    reasoning: str
    
# Functions avec type hints
async def execute_trade(
    trade: Trade,
    confidence: float = 0.8
) -> TradeResult:
    """Execute un trade avec validation."""
    pass
```

**Naming Conventions**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### TypeScript (Frontend)

**Style**: Prettier + ESLint
```typescript
// Interfaces avec documentation
interface TradeData {
  /** Identifiant unique du trade */
  id: string;
  /** Montant en USD */
  amount: number;
  /** Timestamp d'exécution */
  timestamp: Date;
}

// Components fonctionnels avec types
interface TradingPanelProps {
  trades: TradeData[];
  onExecuteTrade: (trade: TradeData) => void;
}

const TradingPanel: React.FC<TradingPanelProps> = ({ 
  trades, 
  onExecuteTrade 
}) => {
  // Hook state avec types
  const [selectedTrade, setSelectedTrade] = useState<TradeData | null>(null);
  
  return (
    <div className="trading-panel">
      {/* JSX content */}
    </div>
  );
};
```

**Naming Conventions**:
- Files: `PascalCase.tsx` (components), `camelCase.ts` (utils)
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

## Développement Local

### Mode Développement
```bash
# Démarrage avec hot reload
./scripts/dev-tools.sh dev

# Logs en temps réel
./scripts/dev-tools.sh logs backend  # Backend only
./scripts/dev-tools.sh logs frontend # Frontend only
./scripts/dev-tools.sh logs all      # Tous les services
```

### Variables d'Environnement
```bash
# Copier et modifier .env
cp .env.example .env

# Variables importantes pour dev
DEBUG=true
LOG_LEVEL=DEBUG
RELOAD=true
VITE_DEV_MODE=true
```

### Base de Données
```bash
# Voir les données
./scripts/dev-tools.sh exec backend python -c "
from app.database import get_db
# Inspect database
"

# Reset complet (ATTENTION: perte données)
./scripts/dev-tools.sh reset
```

## Workflow de Développement

### 1. Nouvelle Fonctionnalité

#### Backend (API)
```bash
# 1. Créer le modèle Pydantic
# app/models/new_feature.py
class NewFeature(BaseModel):
    name: str
    value: float

# 2. Créer les routes API
# app/api/v1/new_feature_routes.py
@router.post("/new-feature")
async def create_feature(feature: NewFeature):
    return {"status": "created"}

# 3. Ajouter au router principal
# app/api/v1/__init__.py
from .new_feature_routes import router as new_feature_router
api_router.include_router(new_feature_router)

# 4. Tests
# tests/api/v1/test_new_feature.py
def test_create_feature():
    response = client.post("/api/v1/new-feature", json={...})
    assert response.status_code == 200
```

#### Frontend (React)
```bash
# 1. Créer le hook
# numerusx-ui/src/hooks/useNewFeature.ts
export const useNewFeature = () => {
  return useQuery({
    queryKey: ['new-feature'],
    queryFn: () => apiClient.get('/new-feature')
  });
};

# 2. Créer le composant
# numerusx-ui/src/components/NewFeaturePanel.tsx
export const NewFeaturePanel = () => {
  const { data, isLoading } = useNewFeature();
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>New Feature</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Content */}
      </CardContent>
    </Card>
  );
};

# 3. Intégrer dans la page
# numerusx-ui/src/pages/DashboardPage.tsx
import { NewFeaturePanel } from '../components/NewFeaturePanel';
```

### 2. Git Workflow

```bash
# Nouvelle branche
git checkout -b feature/nouvelle-fonctionnalite

# Commits atomiques
git add .
git commit -m "feat: ajouter nouvelle fonctionnalité"

# Types de commits (Conventional Commits)
# feat: nouvelle fonctionnalité
# fix: correction de bug
# docs: documentation
# style: formatage, style
# refactor: refactoring
# test: ajout/modification tests
# chore: tâches maintenance

# Push et Pull Request
git push origin feature/nouvelle-fonctionnalite
# Créer PR sur GitHub
```

### 3. Tests

#### Backend Tests
```bash
# Lancer tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/api/v1/test_trades.py -v

# Coverage
pytest --cov=app tests/

# Tests avec base de données test
pytest tests/ --db-test
```

#### Frontend Tests
```bash
cd numerusx-ui

# Tests unitaires
npm test

# Tests E2E (si configurés)
npm run test:e2e

# Coverage
npm run test:coverage
```

## Debugging

### Backend Debug
```bash
# Logs détaillés
./scripts/dev-tools.sh logs backend

# Debug en container
docker compose exec backend python -c "
from app.main import app
# Debug code here
"

# Accès shell container
docker compose exec backend bash
```

### Frontend Debug
```bash
# React DevTools dans le navigateur
# Chrome: https://chrome.google.com/webstore/detail/react-developer-tools

# Console browser avec:
console.log('Debug:', data);

# Network tab pour voir les API calls
```

### AI Agent Debug
```python
# Ajouter logs dans l'agent
from app.utils.logger import logger

class AIAgent:
    async def analyze_market_decision(self, inputs: AggregatedInputs):
        logger.debug(f"AI Agent inputs: {inputs}")
        
        decision = await self._make_decision(inputs)
        
        logger.info(f"AI Decision: {decision.action} "
                   f"(confidence: {decision.confidence})")
        
        return decision
```

## Performance

### Profiling Backend
```python
# Ajouter dans les routes critiques
import time
start_time = time.time()

# ... code ...

logger.info(f"Execution time: {time.time() - start_time:.3f}s")
```

### Optimisation Frontend
```typescript
// React.memo pour éviter re-renders
export const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* Expensive rendering */}</div>;
});

// useMemo pour calculs coûteux
const expensiveValue = useMemo(() => {
  return heavyCalculation(data);
}, [data]);

// useCallback pour fonctions stables
const handleClick = useCallback((id: string) => {
  onItemClick(id);
}, [onItemClick]);
```

## Déploiement

### Production Build
```bash
# Build optimisé
./scripts/dev-tools.sh build

# Mode production
./scripts/dev-tools.sh prod

# Vérification
./scripts/dev-tools.sh status
```

### Environment Production
```env
# .env.production
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Sécurité renforcée
SECRET_KEY=very-long-random-key
CORS_ORIGINS=["https://yourapp.com"]
```

## Troubleshooting

### Problèmes Courants

#### "Container ne démarre pas"
```bash
# Vérifier logs
./scripts/dev-tools.sh logs backend

# Rebuild complet
./scripts/dev-tools.sh build

# Reset si nécessaire
./scripts/dev-tools.sh reset
```

#### "Erreur dépendances Python"
```bash
# Update requirements.txt et rebuild
docker compose build backend --no-cache
```

#### "Erreur dépendances Node"
```bash
# Update package.json et rebuild  
docker compose build frontend --no-cache
```

#### "API non accessible"
```bash
# Vérifier ports
docker compose ps

# Vérifier réseau
docker network ls
```

### Logs Utiles
```bash
# Système complet
./scripts/dev-tools.sh logs all

# Filtrer erreurs seulement
./scripts/dev-tools.sh logs backend | grep ERROR

# Suivre en temps réel
./scripts/dev-tools.sh logs backend -f
```

## Contribution

### Before Commit
```bash
# Format code
./scripts/dev-tools.sh format

# Lint
./scripts/dev-tools.sh lint

# Tests
./scripts/dev-tools.sh test

# Vérification manuelle
./scripts/dev-tools.sh status
```

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if UI changes)
```

Happy coding! 🚀 

## Démarrage Rapide

### 1. Prérequis
- Docker & Docker Compose
- Git
- IDE recommandé: VSCode avec extensions TypeScript/Python

### 2. Installation Ultra-Rapide
```bash
git clone https://github.com/votre-repo/numerusx.git
cd numerusx
./scripts/dev-tools.sh setup
./scripts/dev-tools.sh start
```

🎉 L'application sera disponible sur:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Structure du Projet

```
NumerusX/
├── 📱 numerusx-ui/              # Frontend React + TypeScript
│   ├── src/
│   │   ├── components/          # Composants réutilisables
│   │   ├── pages/              # Pages principales
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utilitaires & API client
│   │   └── store/              # State management
│   ├── public/                 # Assets statiques
│   └── package.json
│
├── 🐍 app/                      # Backend Python FastAPI
│   ├── api/                    # API routes
│   │   └── v1/                 # API version 1
│   ├── models/                 # Modèles de données
│   ├── trading/                # Logique de trading
│   ├── ai_agent/               # Agent IA central
│   ├── strategies/             # Stratégies de trading
│   ├── market/                 # Données de marché
│   ├── security/               # Sécurité & validation
│   └── utils/                  # Utilitaires
│
├── 🐳 Docker/                   # Configuration Docker
│   ├── backend/                # Dockerfile backend
│   └── frontend/               # Dockerfile frontend
│
├── 📋 todo/                     # Documentation TODO
├── 🧪 tests/                    # Tests automatisés
├── 📚 docs/                     # Documentation
└── 📝 scripts/                  # Scripts de développement
```

## Conventions de Code

### Python (Backend)

**Style**: Black + Flake8
```python
# Imports organization
from typing import List, Optional
import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models import Trade
from app.utils import logger

# Classes avec docstrings
class TradeDecision(BaseModel):
    """Décision de trading de l'Agent IA."""
    
    action: str  # BUY/SELL/HOLD
    confidence: float  # 0.0 - 1.0
    reasoning: str
    
# Functions avec type hints
async def execute_trade(
    trade: Trade,
    confidence: float = 0.8
) -> TradeResult:
    """Execute un trade avec validation."""
    pass
```

**Naming Conventions**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### TypeScript (Frontend)

**Style**: Prettier + ESLint
```typescript
// Interfaces avec documentation
interface TradeData {
  /** Identifiant unique du trade */
  id: string;
  /** Montant en USD */
  amount: number;
  /** Timestamp d'exécution */
  timestamp: Date;
}

// Components fonctionnels avec types
interface TradingPanelProps {
  trades: TradeData[];
  onExecuteTrade: (trade: TradeData) => void;
}

const TradingPanel: React.FC<TradingPanelProps> = ({ 
  trades, 
  onExecuteTrade 
}) => {
  // Hook state avec types
  const [selectedTrade, setSelectedTrade] = useState<TradeData | null>(null);
  
  return (
    <div className="trading-panel">
      {/* JSX content */}
    </div>
  );
};
```

**Naming Conventions**:
- Files: `PascalCase.tsx` (components), `camelCase.ts` (utils)
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

## Développement Local

### Mode Développement
```bash
# Démarrage avec hot reload
./scripts/dev-tools.sh dev

# Logs en temps réel
./scripts/dev-tools.sh logs backend  # Backend only
./scripts/dev-tools.sh logs frontend # Frontend only
./scripts/dev-tools.sh logs all      # Tous les services
```

### Variables d'Environnement
```bash
# Copier et modifier .env
cp .env.example .env

# Variables importantes pour dev
DEBUG=true
LOG_LEVEL=DEBUG
RELOAD=true
VITE_DEV_MODE=true
```

### Base de Données
```bash
# Voir les données
./scripts/dev-tools.sh exec backend python -c "
from app.database import get_db
# Inspect database
"

# Reset complet (ATTENTION: perte données)
./scripts/dev-tools.sh reset
```

## Workflow de Développement

### 1. Nouvelle Fonctionnalité

#### Backend (API)
```bash
# 1. Créer le modèle Pydantic
# app/models/new_feature.py
class NewFeature(BaseModel):
    name: str
    value: float

# 2. Créer les routes API
# app/api/v1/new_feature_routes.py
@router.post("/new-feature")
async def create_feature(feature: NewFeature):
    return {"status": "created"}

# 3. Ajouter au router principal
# app/api/v1/__init__.py
from .new_feature_routes import router as new_feature_router
api_router.include_router(new_feature_router)

# 4. Tests
# tests/api/v1/test_new_feature.py
def test_create_feature():
    response = client.post("/api/v1/new-feature", json={...})
    assert response.status_code == 200
```

#### Frontend (React)
```bash
# 1. Créer le hook
# numerusx-ui/src/hooks/useNewFeature.ts
export const useNewFeature = () => {
  return useQuery({
    queryKey: ['new-feature'],
    queryFn: () => apiClient.get('/new-feature')
  });
};

# 2. Créer le composant
# numerusx-ui/src/components/NewFeaturePanel.tsx
export const NewFeaturePanel = () => {
  const { data, isLoading } = useNewFeature();
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>New Feature</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Content */}
      </CardContent>
    </Card>
  );
};

# 3. Intégrer dans la page
# numerusx-ui/src/pages/DashboardPage.tsx
import { NewFeaturePanel } from '../components/NewFeaturePanel';
```

### 2. Git Workflow

```bash
# Nouvelle branche
git checkout -b feature/nouvelle-fonctionnalite

# Commits atomiques
git add .
git commit -m "feat: ajouter nouvelle fonctionnalité"

# Types de commits (Conventional Commits)
# feat: nouvelle fonctionnalité
# fix: correction de bug
# docs: documentation
# style: formatage, style
# refactor: refactoring
# test: ajout/modification tests
# chore: tâches maintenance

# Push et Pull Request
git push origin feature/nouvelle-fonctionnalite
# Créer PR sur GitHub
```

### 3. Tests

#### Backend Tests
```bash
# Lancer tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/api/v1/test_trades.py -v

# Coverage
pytest --cov=app tests/

# Tests avec base de données test
pytest tests/ --db-test
```

#### Frontend Tests
```bash
cd numerusx-ui

# Tests unitaires
npm test

# Tests E2E (si configurés)
npm run test:e2e

# Coverage
npm run test:coverage
```

## Debugging

### Backend Debug
```bash
# Logs détaillés
./scripts/dev-tools.sh logs backend

# Debug en container
docker compose exec backend python -c "
from app.main import app
# Debug code here
"

# Accès shell container
docker compose exec backend bash
```

### Frontend Debug
```bash
# React DevTools dans le navigateur
# Chrome: https://chrome.google.com/webstore/detail/react-developer-tools

# Console browser avec:
console.log('Debug:', data);

# Network tab pour voir les API calls
```

### AI Agent Debug
```python
# Ajouter logs dans l'agent
from app.utils.logger import logger

class AIAgent:
    async def analyze_market_decision(self, inputs: AggregatedInputs):
        logger.debug(f"AI Agent inputs: {inputs}")
        
        decision = await self._make_decision(inputs)
        
        logger.info(f"AI Decision: {decision.action} "
                   f"(confidence: {decision.confidence})")
        
        return decision
```

## Performance

### Profiling Backend
```python
# Ajouter dans les routes critiques
import time
start_time = time.time()

# ... code ...

logger.info(f"Execution time: {time.time() - start_time:.3f}s")
```

### Optimisation Frontend
```typescript
// React.memo pour éviter re-renders
export const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* Expensive rendering */}</div>;
});

// useMemo pour calculs coûteux
const expensiveValue = useMemo(() => {
  return heavyCalculation(data);
}, [data]);

// useCallback pour fonctions stables
const handleClick = useCallback((id: string) => {
  onItemClick(id);
}, [onItemClick]);
```

## Déploiement

### Production Build
```bash
# Build optimisé
./scripts/dev-tools.sh build

# Mode production
./scripts/dev-tools.sh prod

# Vérification
./scripts/dev-tools.sh status
```

### Environment Production
```env
# .env.production
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Sécurité renforcée
SECRET_KEY=very-long-random-key
CORS_ORIGINS=["https://yourapp.com"]
```

## Troubleshooting

### Problèmes Courants

#### "Container ne démarre pas"
```bash
# Vérifier logs
./scripts/dev-tools.sh logs backend

# Rebuild complet
./scripts/dev-tools.sh build

# Reset si nécessaire
./scripts/dev-tools.sh reset
```

#### "Erreur dépendances Python"
```bash
# Update requirements.txt et rebuild
docker compose build backend --no-cache
```

#### "Erreur dépendances Node"
```bash
# Update package.json et rebuild  
docker compose build frontend --no-cache
```

#### "API non accessible"
```bash
# Vérifier ports
docker compose ps

# Vérifier réseau
docker network ls
```

### Logs Utiles
```bash
# Système complet
./scripts/dev-tools.sh logs all

# Filtrer erreurs seulement
./scripts/dev-tools.sh logs backend | grep ERROR

# Suivre en temps réel
./scripts/dev-tools.sh logs backend -f
```

## Contribution

### Before Commit
```bash
# Format code
./scripts/dev-tools.sh format

# Lint
./scripts/dev-tools.sh lint

# Tests
./scripts/dev-tools.sh test

# Vérification manuelle
./scripts/dev-tools.sh status
```

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if UI changes)
```

Happy coding! 🚀 