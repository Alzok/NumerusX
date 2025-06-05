#!/bin/bash

# 💾 NumerusX - Script de Sauvegarde Base de Données
# =================================================

set -e

# Configuration
PROJECT_NAME="NumerusX"
BACKUP_DIR="./backups"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="numerusx-backend-1"
DB_PATH="/app/data/trading_bot.db"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Créer le dossier de backup
mkdir -p "$BACKUP_DIR"

# Vérifier que le container existe
if ! docker container inspect "$DB_CONTAINER" >/dev/null 2>&1; then
    log_error "Container $DB_CONTAINER non trouvé. Assurez-vous que l'application est démarrée."
    exit 1
fi

log_info "Début de la sauvegarde de la base de données..."

# Créer le backup SQLite
BACKUP_FILE="$BACKUP_DIR/numerusx_backup_$DATE.db"

if docker cp "$DB_CONTAINER:$DB_PATH" "$BACKUP_FILE"; then
    log_success "Sauvegarde créée: $BACKUP_FILE"
    
    # Obtenir la taille du fichier
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Taille de la sauvegarde: $SIZE"
    
    # Créer aussi un export JSON pour la portabilité
    JSON_BACKUP="$BACKUP_DIR/numerusx_export_$DATE.json"
    
    log_info "Création de l'export JSON..."
    
    # Script Python pour exporter en JSON
    cat > /tmp/export_db.py << 'EOF'
import sqlite3
import json
import sys

def export_to_json(db_path, json_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    data = {}
    cursor = conn.cursor()
    
    # Obtenir toutes les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        data[table_name] = []
        for row in rows:
            data[table_name].append(dict(row))
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    conn.close()
    print(f"Export JSON créé: {json_path}")

if __name__ == "__main__":
    export_to_json(sys.argv[1], sys.argv[2])
EOF

    if python3 /tmp/export_db.py "$BACKUP_FILE" "$JSON_BACKUP"; then
        log_success "Export JSON créé: $JSON_BACKUP"
    else
        log_error "Échec de l'export JSON"
    fi
    
    # Nettoyer
    rm -f /tmp/export_db.py
    
    # Statistiques des sauvegardes
    echo ""
    log_info "=== Statistiques des Sauvegardes ==="
    echo "📁 Dossier: $BACKUP_DIR"
    echo "📊 Nombre de sauvegardes: $(ls -1 "$BACKUP_DIR"/*.db 2>/dev/null | wc -l)"
    echo "💾 Espace utilisé: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo ""
    
    # Lister les 5 dernières sauvegardes
    echo "🕒 Dernières sauvegardes:"
    ls -lt "$BACKUP_DIR"/*.db 2>/dev/null | head -5 | while read line; do
        echo "   $line"
    done
    
    echo ""
    log_success "Sauvegarde terminée avec succès!"
    
    # Nettoyer les anciennes sauvegardes (garder seulement les 10 dernières)
    log_info "Nettoyage des anciennes sauvegardes..."
    
    cd "$BACKUP_DIR"
    ls -t *.db 2>/dev/null | tail -n +11 | xargs -r rm -f
    ls -t *.json 2>/dev/null | tail -n +11 | xargs -r rm -f
    
    log_success "Anciennes sauvegardes nettoyées (gardé les 10 dernières)"
    
else
    log_error "Échec de la sauvegarde"
    exit 1
fi 

# 💾 NumerusX - Script de Sauvegarde Base de Données
# =================================================

set -e

# Configuration
PROJECT_NAME="NumerusX"
BACKUP_DIR="./backups"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="numerusx-backend-1"
DB_PATH="/app/data/trading_bot.db"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Créer le dossier de backup
mkdir -p "$BACKUP_DIR"

# Vérifier que le container existe
if ! docker container inspect "$DB_CONTAINER" >/dev/null 2>&1; then
    log_error "Container $DB_CONTAINER non trouvé. Assurez-vous que l'application est démarrée."
    exit 1
fi

log_info "Début de la sauvegarde de la base de données..."

# Créer le backup SQLite
BACKUP_FILE="$BACKUP_DIR/numerusx_backup_$DATE.db"

if docker cp "$DB_CONTAINER:$DB_PATH" "$BACKUP_FILE"; then
    log_success "Sauvegarde créée: $BACKUP_FILE"
    
    # Obtenir la taille du fichier
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Taille de la sauvegarde: $SIZE"
    
    # Créer aussi un export JSON pour la portabilité
    JSON_BACKUP="$BACKUP_DIR/numerusx_export_$DATE.json"
    
    log_info "Création de l'export JSON..."
    
    # Script Python pour exporter en JSON
    cat > /tmp/export_db.py << 'EOF'
import sqlite3
import json
import sys

def export_to_json(db_path, json_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    data = {}
    cursor = conn.cursor()
    
    # Obtenir toutes les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        data[table_name] = []
        for row in rows:
            data[table_name].append(dict(row))
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    conn.close()
    print(f"Export JSON créé: {json_path}")

if __name__ == "__main__":
    export_to_json(sys.argv[1], sys.argv[2])
EOF

    if python3 /tmp/export_db.py "$BACKUP_FILE" "$JSON_BACKUP"; then
        log_success "Export JSON créé: $JSON_BACKUP"
    else
        log_error "Échec de l'export JSON"
    fi
    
    # Nettoyer
    rm -f /tmp/export_db.py
    
    # Statistiques des sauvegardes
    echo ""
    log_info "=== Statistiques des Sauvegardes ==="
    echo "📁 Dossier: $BACKUP_DIR"
    echo "📊 Nombre de sauvegardes: $(ls -1 "$BACKUP_DIR"/*.db 2>/dev/null | wc -l)"
    echo "💾 Espace utilisé: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo ""
    
    # Lister les 5 dernières sauvegardes
    echo "🕒 Dernières sauvegardes:"
    ls -lt "$BACKUP_DIR"/*.db 2>/dev/null | head -5 | while read line; do
        echo "   $line"
    done
    
    echo ""
    log_success "Sauvegarde terminée avec succès!"
    
    # Nettoyer les anciennes sauvegardes (garder seulement les 10 dernières)
    log_info "Nettoyage des anciennes sauvegardes..."
    
    cd "$BACKUP_DIR"
    ls -t *.db 2>/dev/null | tail -n +11 | xargs -r rm -f
    ls -t *.json 2>/dev/null | tail -n +11 | xargs -r rm -f
    
    log_success "Anciennes sauvegardes nettoyées (gardé les 10 dernières)"
    
else
    log_error "Échec de la sauvegarde"
    exit 1
fi 