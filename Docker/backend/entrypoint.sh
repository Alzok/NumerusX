#!/bin/sh
set -e

echo "🚀 Starting NumerusX Backend..."

# Créer le fichier .env à partir de .env.example s'il n'existe pas
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Création du fichier .env à partir de .env.example..."
        cp .env.example .env
        echo "✅ Fichier .env créé! Vous devez maintenant le configurer avec vos vraies valeurs."
        echo "⚠️  Arrêtez le conteneur (Ctrl+C), éditez le fichier .env, puis relancez."
        echo ""
        echo "🔍 Le fichier .env a été créé à la racine du projet."
        echo "   Éditez-le avec vos vraies clés API et relancez docker-compose up"
    else
        echo "❌ Erreur: Le fichier .env.example n'existe pas!"
        exit 1
    fi
fi

# Créer les dossiers nécessaires s'ils n'existent pas
mkdir -p data logs keys models

echo "🔍 Vérification des variables d'environnement critiques..."

# Vérifier que les variables critiques ne sont pas vides ou par défaut
check_env_var() {
    local var_name="$1"
    local var_value="$2"
    local default_pattern="$3"
    
    if [ -z "$var_value" ] || echo "$var_value" | grep -q "$default_pattern"; then
        echo "⚠️  WARNING: $var_name n'est pas configurée ou utilise une valeur par défaut"
        echo "   Veuillez configurer cette variable dans le fichier .env"
        return 1
    fi
    return 0
}

# Liste des variables critiques à vérifier
warnings=0

if ! check_env_var "GOOGLE_API_KEY" "$GOOGLE_API_KEY" "your-google-api-key"; then
    warnings=$((warnings + 1))
fi

if ! check_env_var "JWT_SECRET_KEY" "$JWT_SECRET_KEY" "your-jwt-secret-key"; then
    warnings=$((warnings + 1))
fi

if ! check_env_var "MASTER_ENCRYPTION_KEY" "$MASTER_ENCRYPTION_KEY" "your-master-encryption-key"; then
    warnings=$((warnings + 1))
fi

if [ $warnings -gt 0 ]; then
    echo "⚠️  $warnings variable(s) critique(s) non configurée(s)"
    echo "🔧 Le backend va démarrer en mode développement avec des limitations"
    echo ""
fi

echo "🎯 Lancement de l'application..."

# Exécuter la commande principale passée au script
exec "$@" 