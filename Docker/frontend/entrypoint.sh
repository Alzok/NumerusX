#!/bin/sh
set -e

echo "🎨 Starting NumerusX Frontend..."

# Se déplacer dans le répertoire de l'application frontend
cd /app/numerusx-ui

# Créer le fichier .env à partir de .env.example s'il n'existe pas
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Création du fichier .env à partir de .env.example..."
        cp .env.example .env
        echo "✅ Fichier .env créé! Vous devez maintenant le configurer avec vos valeurs Auth0."
        echo "⚠️  Arrêtez le conteneur (Ctrl+C), éditez le fichier numerusx-ui/.env, puis relancez."
        echo ""
        echo "🔍 Le fichier numerusx-ui/.env a été créé."
        echo "   Configurez vos valeurs Auth0 et relancez docker-compose up"
    else
        echo "❌ Erreur: Le fichier .env.example n'existe pas!"
        exit 1
    fi
fi

echo "🔍 Vérification des variables d'environnement critiques..."

# Vérifier que les variables critiques ne sont pas vides ou par défaut
check_env_var() {
    local var_name="$1"
    local var_value="$2"
    local default_pattern="$3"
    
    if [ -z "$var_value" ] || echo "$var_value" | grep -q "$default_pattern"; then
        echo "⚠️  WARNING: $var_name n'est pas configurée ou utilise une valeur par défaut"
        echo "   Veuillez configurer cette variable dans le fichier numerusx-ui/.env"
        return 1
    fi
    return 0
}

# Charger les variables d'environnement depuis le fichier .env
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

# Liste des variables critiques à vérifier
warnings=0

if ! check_env_var "VITE_APP_AUTH0_DOMAIN" "$VITE_APP_AUTH0_DOMAIN" "your-domain.auth0.com"; then
    warnings=$((warnings + 1))
fi

if ! check_env_var "VITE_APP_AUTH0_CLIENT_ID" "$VITE_APP_AUTH0_CLIENT_ID" "your-auth0-client-id"; then
    warnings=$((warnings + 1))
fi

if ! check_env_var "VITE_APP_AUTH0_AUDIENCE" "$VITE_APP_AUTH0_AUDIENCE" "your-api-identifier"; then
    warnings=$((warnings + 1))
fi

if [ $warnings -gt 0 ]; then
    echo "⚠️  $warnings variable(s) critique(s) non configurée(s)"
    echo "🔧 Le frontend va démarrer mais l'authentification ne fonctionnera pas"
    echo ""
fi

echo "📦 Vérification des dépendances..."

# Vérifier si node_modules existe et est à jour
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    echo "📦 Installation des dépendances npm..."
    npm install --legacy-peer-deps
fi

echo "🎯 Lancement de l'application frontend..."

# Exécuter la commande principale passée au script
exec "$@" 