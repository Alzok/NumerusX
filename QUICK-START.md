# 🚀 NumerusX - Guide de Démarrage Rapide

## En 30 secondes

```bash
git clone https://github.com/your-repo/numerusx.git
cd numerusx
./start.sh
```

C'est tout ! 🎉

## Première utilisation

1. **Le script détecte** que vous n'avez pas de configuration
2. **Il crée automatiquement** les fichiers `.env` et `numerusx-ui/.env`
3. **Il vous demande** si vous voulez continuer avec les valeurs par défaut
4. **Répondez `y`** pour tester le système
5. **Ouvrez** http://localhost:5173 dans votre navigateur

## Fonctionnalités disponibles sans configuration

- ✅ Interface utilisateur complète
- ✅ Dashboard temps réel
- ✅ API backend fonctionnelle
- ✅ Base de données locale
- ✅ Cache Redis
- ⚠️ IA désactivée (besoin clé Google)
- ⚠️ Trading désactivé (besoin clés Solana)
- ⚠️ Auth désactivée (besoin Auth0)

## Configuration complète (optionnelle)

Pour débloquer toutes les fonctionnalités :

1. **Arrêtez** le système (`Ctrl+C`)
2. **Éditez** `.env` avec vos clés API
3. **Éditez** `numerusx-ui/.env` avec Auth0
4. **Relancez** `./start.sh`

### Clés principales nécessaires

```bash
# Dans .env
GOOGLE_API_KEY=your-key          # Pour l'IA Gemini
SOLANA_PRIVATE_KEY_BS58=your-key # Pour le trading
JWT_SECRET_KEY=$(openssl rand -hex 32)
MASTER_ENCRYPTION_KEY=$(openssl rand -hex 32)

# Dans numerusx-ui/.env  
VITE_APP_AUTH0_DOMAIN=your-domain.auth0.com
VITE_APP_AUTH0_CLIENT_ID=your-client-id
VITE_APP_AUTH0_AUDIENCE=your-api-id
```

## Commandes utiles

```bash
# Lancer le système
./start.sh

# Arrêter le système
docker-compose down

# Voir les logs
docker-compose logs -f

# Redémarrer un service
docker-compose restart backend
docker-compose restart frontend

# Accéder aux conteneurs
docker-compose exec backend bash
docker-compose exec frontend sh

# Nettoyer complètement
docker-compose down -v
docker system prune -f
```

## URLs d'accès

- **Frontend** : http://localhost:5173
- **Backend API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Base de données** : `data/numerusx.db` (SQLite)
- **Logs** : `logs/numerusx.log`

## Problèmes courants

### Docker n'est pas installé
```bash
# Sur Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ou téléchargez Docker Desktop
# https://www.docker.com/products/docker-desktop
```

### Permission denied sur start.sh
```bash
chmod +x start.sh
./start.sh
```

### Port déjà utilisé
```bash
# Vérifier qui utilise le port 8000
sudo netstat -tulpn | grep :8000

# Ou changer les ports dans docker-compose.yml
```

### Conteneurs ne démarrent pas
```bash
# Nettoyer et reconstruire
docker-compose down -v
docker system prune -f
./start.sh
```

## Support

- 📖 **Documentation complète** : `README.md`
- 🐳 **Configuration Docker** : `docker-compose.yml`
- ⚙️ **Variables d'environnement** : `.env.example`
- 🔧 **Script de lancement** : `start.sh` 