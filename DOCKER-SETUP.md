# 🐳 NumerusX - Setup Docker

## Commandes principales

### Démarrage automatique complet
```bash
docker-compose up --build -d
```

### Vérification des services
```bash
docker-compose ps
```

### Logs en temps réel
```bash
docker-compose logs -f
```

### Arrêt des services
```bash
docker-compose down
```

### Reconstruction complète
```bash
docker-compose down --volumes --remove-orphans
docker-compose up --build -d
```

## URLs d'accès

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Redis**: localhost:6379

## Ordre de démarrage automatique

1. **Redis** (base de données en mémoire)
2. **Backend** (API FastAPI - attend Redis)
3. **Frontend** (React/Vite - attend Backend)

Les healthchecks assurent que chaque service démarre uniquement quand le précédent est prêt.

## Développement

- Les fichiers sont montés en volumes pour le **hot-reload**
- Backend: modifications dans `./app/` se reflètent automatiquement
- Frontend: modifications dans `./numerusx-ui/src/` se reflètent automatiquement

## Résolution des erreurs Python VSCode

Les erreurs Pylance sont normales car les dépendances Python sont dans Docker.
La configuration `.vscode/settings.json` les désactive automatiquement. 