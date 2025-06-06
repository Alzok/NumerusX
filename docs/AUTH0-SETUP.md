# Configuration Auth0 pour NumerusX

## 🎯 Résumé

L'authentification Auth0 est maintenant **intégrée et obligatoire** pour accéder à :
- L'interface d'onboarding 
- La configuration du système
- Tous les endpoints sensibles
- Les outils de gestion

## 🔧 Configuration Auth0 Requise

### **Domaine Auth0 Configuré**
- **Domaine** : `numerus.eu.auth0.com`
- **API Audience** : `https://numerus.eu.auth0.com/api/v2/`

### **Applications Auth0 à Créer**

#### **1. Application de Développement (localhost)**
```
Type: Single Page Application (SPA)
Nom: NumerusX Development
Allowed Callback URLs: http://localhost:5173/callback
Allowed Logout URLs: http://localhost:5173
Allowed Web Origins: http://localhost:5173
```

#### **2. Application de Production**
```
Type: Single Page Application (SPA)  
Nom: NumerusX Production
Allowed Callback URLs: https://your-domain.com/callback
Allowed Logout URLs: https://your-domain.com
Allowed Web Origins: https://your-domain.com
```

## ⚙️ Variables d'Environnement

### **Fichier: `Docker/backend/auth0.env`**
Remplacez les valeurs par défaut :

```bash
# Development Application
AUTH0_CLIENT_ID_DEV=your_real_dev_client_id
AUTH0_CLIENT_SECRET_DEV=your_real_dev_client_secret

# Production Application  
AUTH0_CLIENT_ID_PROD=your_real_prod_client_id
AUTH0_CLIENT_SECRET_PROD=your_real_prod_client_secret

# Production URLs (à mettre à jour lors du déploiement)
AUTH0_CALLBACK_URL_PROD=https://your-domain.com/callback
AUTH0_LOGOUT_URL_PROD=https://your-domain.com
```

## 🚀 Démarrage

### **Pour Démarrer Auth0 depuis Docker**

```bash
# Linux / macOS
sh exec.sh

# Windows Powershell  
./exec.ps1
```

## 🔒 Sécurité Implémentée

### **Protection des Endpoints**
- ✅ `POST /api/v1/onboarding/validate-step1` - Authentification requise
- ✅ `POST /api/v1/onboarding/complete` - Authentification requise  
- ✅ `GET /api/v1/onboarding/configuration` - Authentification requise
- ✅ `POST /api/v1/onboarding/update-mode` - Authentification requise
- ✅ `POST /debug/*` - Authentification requise (localhost uniquement)

### **Flux d'Authentification**
1. L'utilisateur accède à `http://localhost:5173`
2. Il est redirigé vers Auth0 pour connexion
3. Après connexion, retour sur l'interface NumerusX
4. Token JWT vérifié pour chaque API call
5. Accès aux fonctionnalités de configuration

## 🎛️ Interface Utilisateur

### **Onboarding Sécurisé**
- L'assistant de configuration n'apparaît qu'après authentification
- Validation en temps réel des clés API avec protection
- Chiffrement automatique des données sensibles
- Persistance sécurisée de la configuration

### **Gestion des Sessions**
- Tokens JWT avec expiration
- Refresh automatique des tokens
- Déconnexion sécurisée
- Protection CSRF intégrée

## ✅ Tests de Validation

### **Test Backend (API)**
```bash
# 1. Vérifier que status fonctionne sans auth
curl http://localhost:8000/api/v1/onboarding/status

# 2. Vérifier que les endpoints protégés rejettent sans auth
curl -X POST http://localhost:8000/api/v1/onboarding/validate-step1

# 3. Logs backend - vérifier les erreurs d'auth
docker-compose logs backend | grep -i auth
```

### **Test Frontend (Interface)**
1. Aller sur `http://localhost:5173`
2. Vérifier la redirection vers Auth0
3. Se connecter avec un compte valide
4. Vérifier l'accès à l'onboarding
5. Tester la sauvegarde de configuration

## 🔄 Prochaines Étapes

1. **Créer les applications Auth0** avec les URLs ci-dessus
2. **Récupérer les Client ID/Secret** depuis le dashboard Auth0
3. **Mettre à jour** `Docker/backend/auth0.env` avec les vraies valeurs
4. **Redémarrer** les containers : `docker-compose restart`
5. **Tester** le flow complet d'authentification

## 📞 Support

Si vous avez besoin d'aide avec la configuration Auth0 :
- Dashboard Auth0 : https://manage.auth0.com/
- Documentation : https://auth0.com/docs/
- Vérifiez les logs : `docker-compose logs backend` 