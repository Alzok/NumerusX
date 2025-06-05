#!/bin/bash

# 🚀 NumerusX - Outils de Développement
# ====================================

set -e  # Exit on error

PROJECT_NAME="NumerusX"
DOCKER_COMPOSE="docker compose"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================="
    echo "🚀 $PROJECT_NAME - $1"
    echo "=================================="
    echo -e "${NC}"
}

# Main functions
show_help() {
    print_header "Outils de Développement"
    echo ""
    echo "Commandes disponibles:"
    echo "  setup     - Configuration initiale du projet"
    echo "  start     - Démarrer l'application (docker compose up)"
    echo "  stop      - Arrêter l'application"
    echo "  restart   - Redémarrer l'application"
    echo "  build     - Rebuild complet des images Docker"
    echo "  logs      - Voir les logs (backend/frontend/all)"
    echo "  status    - Statut de l'application"
    echo "  test      - Lancer les tests"
    echo "  clean     - Nettoyer les données et images"
    echo "  reset     - Reset complet (ATTENTION: perte de données)"
    echo "  backup    - Sauvegarder la base de données"
    echo "  restore   - Restaurer une sauvegarde"
    echo "  dev       - Mode développement avec hot reload"
    echo "  prod      - Mode production"
    echo "  install   - Installer les dépendances localement"
    echo "  format    - Formater le code (black, prettier)"
    echo "  lint      - Linter le code"
    echo "  docs      - Générer la documentation"
    echo "  monitor   - Surveiller les logs en temps réel"
    echo "  db        - Outils base de données (export/import/reset)"
    echo "  security  - Scanner de sécurité"
    echo "  update    - Mettre à jour les dépendances"
    echo ""
    echo "Usage: $0 <commande> [options]"
}

setup_project() {
    print_header "Configuration Initiale"
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Créer .env si nécessaire
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_success "Fichier .env créé depuis .env.example"
        else
            log_warning "Créer votre fichier .env manuellement"
        fi
    fi
    
    # Créer dossiers nécessaires
    mkdir -p logs data backups
    log_success "Dossiers créés: logs, data, backups"
    
    # Build initial
    log_info "Build initial des images Docker..."
    $DOCKER_COMPOSE build
    log_success "Images Docker construites"
    
    log_success "Configuration terminée! Utilisez '$0 start' pour démarrer"
}

start_app() {
    print_header "Démarrage Application"
    log_info "Démarrage de $PROJECT_NAME..."
    $DOCKER_COMPOSE up -d
    sleep 3
    show_status
}

stop_app() {
    print_header "Arrêt Application"
    log_info "Arrêt de $PROJECT_NAME..."
    $DOCKER_COMPOSE down
    log_success "Application arrêtée"
}

restart_app() {
    print_header "Redémarrage Application"
    stop_app
    sleep 2
    start_app
}

build_app() {
    print_header "Build Application"
    log_info "Rebuild complet..."
    $DOCKER_COMPOSE build --no-cache
    log_success "Build terminé"
}

show_logs() {
    service=${1:-all}
    print_header "Logs - $service"
    
    case $service in
        backend)
            $DOCKER_COMPOSE logs -f backend
            ;;
        frontend)
            $DOCKER_COMPOSE logs -f frontend
            ;;
        redis)
            $DOCKER_COMPOSE logs -f redis
            ;;
        all|*)
            $DOCKER_COMPOSE logs -f
            ;;
    esac
}

show_status() {
    print_header "Statut Application"
    
    # Statut containers
    echo "📦 Containers:"
    $DOCKER_COMPOSE ps
    echo ""
    
    # Test endpoints
    echo "🧪 Tests de connectivité:"
    
    # Backend
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "Backend disponible (http://localhost:8000)"
    else
        log_error "Backend non accessible"
    fi
    
    # Frontend
    if curl -f http://localhost:5173 &>/dev/null; then
        log_success "Frontend disponible (http://localhost:5173)"
    else
        log_error "Frontend non accessible"
    fi
    
    # Redis
    if $DOCKER_COMPOSE exec redis redis-cli ping &>/dev/null; then
        log_success "Redis disponible"
    else
        log_error "Redis non accessible"
    fi
    
    echo ""
    echo "🌐 URLs utiles:"
    echo "  Frontend:      http://localhost:5173"
    echo "  Backend API:   http://localhost:8000"
    echo "  API Docs:      http://localhost:8000/docs"
    echo "  Admin:         http://localhost:8000/api/v1/system/health"
}

run_tests() {
    print_header "Tests"
    log_info "Lancement des tests..."
    
    # Tests backend
    log_info "Tests backend..."
    $DOCKER_COMPOSE exec backend python -m pytest tests/ -v
    
    # Tests frontend (si configurés)
    if [ -f "numerusx-ui/package.json" ] && grep -q "test" numerusx-ui/package.json; then
        log_info "Tests frontend..."
        $DOCKER_COMPOSE exec frontend npm test
    fi
    
    log_success "Tests terminés"
}

clean_data() {
    print_header "Nettoyage"
    
    log_warning "Cela va supprimer:"
    echo "  - Volumes Docker"
    echo "  - Images inutilisées"
    echo "  - Logs anciens"
    
    read -p "Continuer? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $DOCKER_COMPOSE down -v
        docker system prune -f
        rm -rf logs/*.log
        log_success "Nettoyage terminé"
    else
        log_info "Nettoyage annulé"
    fi
}

reset_all() {
    print_header "Reset Complet"
    
    log_error "ATTENTION: Cela va supprimer TOUTES les données!"
    echo "  - Base de données"
    echo "  - Volumes Docker"
    echo "  - Images Docker"
    echo "  - Logs"
    
    read -p "Êtes-vous sûr? Tapez 'RESET' pour confirmer: " -r
    if [[ $REPLY == "RESET" ]]; then
        $DOCKER_COMPOSE down -v --rmi all
        docker system prune -a -f
        rm -rf data/* logs/* backups/*
        log_success "Reset complet terminé"
        log_info "Utilisez '$0 setup' pour reconfigurer"
    else
        log_info "Reset annulé"
    fi
}

backup_db() {
    print_header "Sauvegarde"
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="backups/numerusx_backup_$timestamp.db"
    
    mkdir -p backups
    
    if [ -f "data/numerusx.db" ]; then
        cp data/numerusx.db "$backup_file"
        log_success "Sauvegarde créée: $backup_file"
    else
        log_error "Base de données non trouvée"
    fi
}

restore_db() {
    print_header "Restauration"
    
    if [ -z "$1" ]; then
        echo "Sauvegardes disponibles:"
        ls -la backups/*.db 2>/dev/null || echo "Aucune sauvegarde trouvée"
        echo ""
        echo "Usage: $0 restore <fichier_sauvegarde>"
        return 1
    fi
    
    if [ -f "$1" ]; then
        stop_app
        cp "$1" data/numerusx.db
        start_app
        log_success "Base de données restaurée depuis $1"
    else
        log_error "Fichier de sauvegarde non trouvé: $1"
    fi
}

dev_mode() {
    print_header "Mode Développement"
    
    log_info "Démarrage en mode développement..."
    
    # Override pour dev
    export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
    
    $DOCKER_COMPOSE up -d
    
    log_success "Mode développement actif"
    echo "  - Hot reload activé"
    echo "  - Debug mode activé"
    echo "  - Logs verbeux"
    
    show_status
}

prod_mode() {
    print_header "Mode Production"
    
    log_info "Démarrage en mode production..."
    
    # Override pour prod
    export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
    
    $DOCKER_COMPOSE up -d
    
    log_success "Mode production actif"
    show_status
}

install_deps() {
    print_header "Installation Dépendances"
    
    # Backend
    if [ -f "requirements.txt" ]; then
        log_info "Installation dépendances Python..."
        pip install -r requirements.txt
    fi
    
    # Frontend
    if [ -f "numerusx-ui/package.json" ]; then
        log_info "Installation dépendances Node.js..."
        cd numerusx-ui && npm install && cd ..
    fi
    
    log_success "Dépendances installées"
}

format_code() {
    print_header "Formatage Code"
    
    # Python avec black
    if command -v black &> /dev/null; then
        log_info "Formatage Python avec black..."
        black app/ tests/
    fi
    
    # JavaScript/TypeScript avec prettier
    if [ -f "numerusx-ui/package.json" ]; then
        log_info "Formatage TypeScript avec prettier..."
        cd numerusx-ui && npm run format && cd ..
    fi
    
    log_success "Code formaté"
}

lint_code() {
    print_header "Linting Code"
    
    # Python avec flake8
    if command -v flake8 &> /dev/null; then
        log_info "Linting Python..."
        flake8 app/ tests/
    fi
    
    # TypeScript avec eslint
    if [ -f "numerusx-ui/package.json" ]; then
        log_info "Linting TypeScript..."
        cd numerusx-ui && npm run lint && cd ..
    fi
    
    log_success "Linting terminé"
}

generate_docs() {
    print_header "Génération Documentation"
    
    # API docs automatiques via FastAPI
    log_info "Documentation API disponible sur http://localhost:8000/docs"
    
    # Documentation code
    if command -v sphinx-build &> /dev/null; then
        log_info "Génération documentation Sphinx..."
        sphinx-build -b html docs/ docs/_build/
    fi
    
    log_success "Documentation générée"
}

# Main script logic
main() {
    case "${1:-help}" in
        setup)
            setup_project
            ;;
        start)
            start_app
            ;;
        stop)
            stop_app
            ;;
        restart)
            restart_app
            ;;
        build)
            build_app
            ;;
        logs)
            show_logs "$2"
            ;;
        status)
            show_status
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_data
            ;;
        reset)
            reset_all
            ;;
        backup)
            backup_db
            ;;
        restore)
            restore_db "$2"
            ;;
        dev)
            dev_mode
            ;;
        prod)
            prod_mode
            ;;
        install)
            install_deps
            ;;
        format)
            format_code
            ;;
        lint)
            lint_code
            ;;
        docs)
            generate_docs
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@" 

# 🚀 NumerusX - Outils de Développement
# ====================================

set -e  # Exit on error

PROJECT_NAME="NumerusX"
DOCKER_COMPOSE="docker compose"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================="
    echo "🚀 $PROJECT_NAME - $1"
    echo "=================================="
    echo -e "${NC}"
}

# Main functions
show_help() {
    print_header "Outils de Développement"
    echo ""
    echo "Commandes disponibles:"
    echo "  setup     - Configuration initiale du projet"
    echo "  start     - Démarrer l'application (docker compose up)"
    echo "  stop      - Arrêter l'application"
    echo "  restart   - Redémarrer l'application"
    echo "  build     - Rebuild complet des images Docker"
    echo "  logs      - Voir les logs (backend/frontend/all)"
    echo "  status    - Statut de l'application"
    echo "  test      - Lancer les tests"
    echo "  clean     - Nettoyer les données et images"
    echo "  reset     - Reset complet (ATTENTION: perte de données)"
    echo "  backup    - Sauvegarder la base de données"
    echo "  restore   - Restaurer une sauvegarde"
    echo "  dev       - Mode développement avec hot reload"
    echo "  prod      - Mode production"
    echo "  install   - Installer les dépendances localement"
    echo "  format    - Formater le code (black, prettier)"
    echo "  lint      - Linter le code"
    echo "  docs      - Générer la documentation"
    echo "  monitor   - Surveiller les logs en temps réel"
    echo "  db        - Outils base de données (export/import/reset)"
    echo "  security  - Scanner de sécurité"
    echo "  update    - Mettre à jour les dépendances"
    echo ""
    echo "Usage: $0 <commande> [options]"
}

setup_project() {
    print_header "Configuration Initiale"
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Créer .env si nécessaire
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_success "Fichier .env créé depuis .env.example"
        else
            log_warning "Créer votre fichier .env manuellement"
        fi
    fi
    
    # Créer dossiers nécessaires
    mkdir -p logs data backups
    log_success "Dossiers créés: logs, data, backups"
    
    # Build initial
    log_info "Build initial des images Docker..."
    $DOCKER_COMPOSE build
    log_success "Images Docker construites"
    
    log_success "Configuration terminée! Utilisez '$0 start' pour démarrer"
}

start_app() {
    print_header "Démarrage Application"
    log_info "Démarrage de $PROJECT_NAME..."
    $DOCKER_COMPOSE up -d
    sleep 3
    show_status
}

stop_app() {
    print_header "Arrêt Application"
    log_info "Arrêt de $PROJECT_NAME..."
    $DOCKER_COMPOSE down
    log_success "Application arrêtée"
}

restart_app() {
    print_header "Redémarrage Application"
    stop_app
    sleep 2
    start_app
}

build_app() {
    print_header "Build Application"
    log_info "Rebuild complet..."
    $DOCKER_COMPOSE build --no-cache
    log_success "Build terminé"
}

show_logs() {
    service=${1:-all}
    print_header "Logs - $service"
    
    case $service in
        backend)
            $DOCKER_COMPOSE logs -f backend
            ;;
        frontend)
            $DOCKER_COMPOSE logs -f frontend
            ;;
        redis)
            $DOCKER_COMPOSE logs -f redis
            ;;
        all|*)
            $DOCKER_COMPOSE logs -f
            ;;
    esac
}

show_status() {
    print_header "Statut Application"
    
    # Statut containers
    echo "📦 Containers:"
    $DOCKER_COMPOSE ps
    echo ""
    
    # Test endpoints
    echo "🧪 Tests de connectivité:"
    
    # Backend
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "Backend disponible (http://localhost:8000)"
    else
        log_error "Backend non accessible"
    fi
    
    # Frontend
    if curl -f http://localhost:5173 &>/dev/null; then
        log_success "Frontend disponible (http://localhost:5173)"
    else
        log_error "Frontend non accessible"
    fi
    
    # Redis
    if $DOCKER_COMPOSE exec redis redis-cli ping &>/dev/null; then
        log_success "Redis disponible"
    else
        log_error "Redis non accessible"
    fi
    
    echo ""
    echo "🌐 URLs utiles:"
    echo "  Frontend:      http://localhost:5173"
    echo "  Backend API:   http://localhost:8000"
    echo "  API Docs:      http://localhost:8000/docs"
    echo "  Admin:         http://localhost:8000/api/v1/system/health"
}

run_tests() {
    print_header "Tests"
    log_info "Lancement des tests..."
    
    # Tests backend
    log_info "Tests backend..."
    $DOCKER_COMPOSE exec backend python -m pytest tests/ -v
    
    # Tests frontend (si configurés)
    if [ -f "numerusx-ui/package.json" ] && grep -q "test" numerusx-ui/package.json; then
        log_info "Tests frontend..."
        $DOCKER_COMPOSE exec frontend npm test
    fi
    
    log_success "Tests terminés"
}

clean_data() {
    print_header "Nettoyage"
    
    log_warning "Cela va supprimer:"
    echo "  - Volumes Docker"
    echo "  - Images inutilisées"
    echo "  - Logs anciens"
    
    read -p "Continuer? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $DOCKER_COMPOSE down -v
        docker system prune -f
        rm -rf logs/*.log
        log_success "Nettoyage terminé"
    else
        log_info "Nettoyage annulé"
    fi
}

reset_all() {
    print_header "Reset Complet"
    
    log_error "ATTENTION: Cela va supprimer TOUTES les données!"
    echo "  - Base de données"
    echo "  - Volumes Docker"
    echo "  - Images Docker"
    echo "  - Logs"
    
    read -p "Êtes-vous sûr? Tapez 'RESET' pour confirmer: " -r
    if [[ $REPLY == "RESET" ]]; then
        $DOCKER_COMPOSE down -v --rmi all
        docker system prune -a -f
        rm -rf data/* logs/* backups/*
        log_success "Reset complet terminé"
        log_info "Utilisez '$0 setup' pour reconfigurer"
    else
        log_info "Reset annulé"
    fi
}

backup_db() {
    print_header "Sauvegarde"
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="backups/numerusx_backup_$timestamp.db"
    
    mkdir -p backups
    
    if [ -f "data/numerusx.db" ]; then
        cp data/numerusx.db "$backup_file"
        log_success "Sauvegarde créée: $backup_file"
    else
        log_error "Base de données non trouvée"
    fi
}

restore_db() {
    print_header "Restauration"
    
    if [ -z "$1" ]; then
        echo "Sauvegardes disponibles:"
        ls -la backups/*.db 2>/dev/null || echo "Aucune sauvegarde trouvée"
        echo ""
        echo "Usage: $0 restore <fichier_sauvegarde>"
        return 1
    fi
    
    if [ -f "$1" ]; then
        stop_app
        cp "$1" data/numerusx.db
        start_app
        log_success "Base de données restaurée depuis $1"
    else
        log_error "Fichier de sauvegarde non trouvé: $1"
    fi
}

dev_mode() {
    print_header "Mode Développement"
    
    log_info "Démarrage en mode développement..."
    
    # Override pour dev
    export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
    
    $DOCKER_COMPOSE up -d
    
    log_success "Mode développement actif"
    echo "  - Hot reload activé"
    echo "  - Debug mode activé"
    echo "  - Logs verbeux"
    
    show_status
}

prod_mode() {
    print_header "Mode Production"
    
    log_info "Démarrage en mode production..."
    
    # Override pour prod
    export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
    
    $DOCKER_COMPOSE up -d
    
    log_success "Mode production actif"
    show_status
}

install_deps() {
    print_header "Installation Dépendances"
    
    # Backend
    if [ -f "requirements.txt" ]; then
        log_info "Installation dépendances Python..."
        pip install -r requirements.txt
    fi
    
    # Frontend
    if [ -f "numerusx-ui/package.json" ]; then
        log_info "Installation dépendances Node.js..."
        cd numerusx-ui && npm install && cd ..
    fi
    
    log_success "Dépendances installées"
}

format_code() {
    print_header "Formatage Code"
    
    # Python avec black
    if command -v black &> /dev/null; then
        log_info "Formatage Python avec black..."
        black app/ tests/
    fi
    
    # JavaScript/TypeScript avec prettier
    if [ -f "numerusx-ui/package.json" ]; then
        log_info "Formatage TypeScript avec prettier..."
        cd numerusx-ui && npm run format && cd ..
    fi
    
    log_success "Code formaté"
}

lint_code() {
    print_header "Linting Code"
    
    # Python avec flake8
    if command -v flake8 &> /dev/null; then
        log_info "Linting Python..."
        flake8 app/ tests/
    fi
    
    # TypeScript avec eslint
    if [ -f "numerusx-ui/package.json" ]; then
        log_info "Linting TypeScript..."
        cd numerusx-ui && npm run lint && cd ..
    fi
    
    log_success "Linting terminé"
}

generate_docs() {
    print_header "Génération Documentation"
    
    # API docs automatiques via FastAPI
    log_info "Documentation API disponible sur http://localhost:8000/docs"
    
    # Documentation code
    if command -v sphinx-build &> /dev/null; then
        log_info "Génération documentation Sphinx..."
        sphinx-build -b html docs/ docs/_build/
    fi
    
    log_success "Documentation générée"
}

# Main script logic
main() {
    case "${1:-help}" in
        setup)
            setup_project
            ;;
        start)
            start_app
            ;;
        stop)
            stop_app
            ;;
        restart)
            restart_app
            ;;
        build)
            build_app
            ;;
        logs)
            show_logs "$2"
            ;;
        status)
            show_status
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_data
            ;;
        reset)
            reset_all
            ;;
        backup)
            backup_db
            ;;
        restore)
            restore_db "$2"
            ;;
        dev)
            dev_mode
            ;;
        prod)
            prod_mode
            ;;
        install)
            install_deps
            ;;
        format)
            format_code
            ;;
        lint)
            lint_code
            ;;
        docs)
            generate_docs
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@" 