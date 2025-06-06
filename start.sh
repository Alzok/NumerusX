#!/bin/bash
set -e

echo "🚀 NumerusX - Lancement du système de trading IA"
echo "================================================"
echo ""

# Fonction pour vérifier si Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker n'est pas installé ou n'est pas dans le PATH"
        echo "   Veuillez installer Docker Desktop depuis https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose n'est pas installé"
        echo "   Veuillez installer Docker Compose"
        exit 1
    fi
}

# Fonction pour créer les fichiers .env s'ils n'existent pas
setup_env_files() {
    local need_config=false
    
    # Backend .env
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo "📝 Création du fichier .env backend..."
            cp .env.example .env
            need_config=true
        else
            echo "❌ Erreur: .env.example non trouvé!"
            exit 1
        fi
    fi
    
    # Frontend .env
    if [ ! -f "numerusx-ui/.env" ]; then
        if [ -f "numerusx-ui/.env.example" ]; then
            echo "📝 Création du fichier .env frontend..."
            cp numerusx-ui/.env.example numerusx-ui/.env
            need_config=true
        else
            echo "❌ Erreur: numerusx-ui/.env.example non trouvé!"
            exit 1
        fi
    fi
    
    if [ "$need_config" = true ]; then
        echo ""
        echo "✅ Fichiers .env créés avec des valeurs par défaut"
        echo ""
        echo "🔧 CONFIGURATION REQUISE:"
        echo "   1. Éditez le fichier '.env' avec vos clés API (Google, Solana, etc.)"
        echo "   2. Éditez le fichier 'numerusx-ui/.env' avec votre configuration Auth0"
        echo "   3. Relancez ce script: ./start.sh"
        echo ""
        echo "📖 Consultez le README.md pour obtenir toutes ces clés API"
        echo ""
        
        # Vérifier si l'utilisateur veut continuer quand même
        read -p "❓ Voulez-vous continuer avec les valeurs par défaut ? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "⏸️  Configuration nécessaire avant le lancement."
            echo "   Relancez ./start.sh après avoir configuré vos fichiers .env"
            exit 0
        fi
        echo ""
        echo "⚠️  Lancement avec les valeurs par défaut (fonctionnalités limitées)"
        echo ""
    else
        echo "✅ Fichiers .env détectés"
    fi
}

# Fonction pour démarrer les services
start_services() {
    echo "🐳 Lancement des conteneurs Docker..."
    echo ""
    
    # Arrêter les conteneurs existants si ils tournent
    if docker-compose ps -q | grep -q .; then
        echo "🛑 Arrêt des conteneurs existants..."
        docker-compose down
        echo ""
    fi
    
    # Construire et démarrer les services
    echo "🏗️  Construction et démarrage des services..."
    docker-compose up --build
}

# Fonction principale
main() {
    echo "🔍 Vérification des prérequis..."
    check_docker
    echo "✅ Docker détecté"
    echo ""
    
    echo "⚙️  Configuration des fichiers d'environnement..."
    setup_env_files
    echo ""
    
    start_services
}

# Gestion des signaux pour arrêter proprement
trap 'echo ""; echo "🛑 Arrêt demandé..."; docker-compose down; exit 0' INT TERM

# Point d'entrée
main "$@" 