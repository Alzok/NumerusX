#!/bin/bash

echo "🚀 NumerusX - Vérification du statut de build"
echo "=============================================="

echo ""
echo "📦 Images Docker construites:"
docker images | grep numerusx

echo ""
echo "🔍 Conteneurs en cours d'exécution:"
docker compose ps

echo ""
echo "🧪 Test rapide des services:"

# Test backend
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ Backend disponible à http://localhost:8000"
    echo "   📋 API Docs: http://localhost:8000/docs"
    echo "   🔧 Admin: http://localhost:8000/api/v1/system/health"
else
    echo "❌ Backend non accessible (en cours de démarrage ?)"
fi

# Test frontend
if curl -f http://localhost:5173 &>/dev/null; then
    echo "✅ Frontend disponible à http://localhost:5173"
else
    echo "❌ Frontend non accessible (en cours de démarrage ?)"
fi

echo ""
echo "📊 Statut final:"
if docker compose ps | grep -q "running"; then
    echo "🎉 Application NumerusX démarrée avec succès !"
    echo ""
    echo "Accès utilisateur:"
    echo "  🌐 Interface principale: http://localhost:5173"
    echo "  📱 Dashboard mobile-friendly"
    echo "  🔐 Authentification intégrée"
    echo ""
    echo "Accès développeur:"
    echo "  🛠️ API Backend: http://localhost:8000"
    echo "  📖 Documentation: http://localhost:8000/docs"
    echo "  ⚡ WebSocket: ws://localhost:8000"
else
    echo "⏳ Services en cours de démarrage..."
    echo "   Relancer ce script dans quelques minutes"
fi

echo ""
echo "🔧 Commandes utiles:"
echo "  docker compose logs backend    # Logs backend"
echo "  docker compose logs frontend   # Logs frontend"
echo "  docker compose restart        # Redémarrer"
echo "  docker compose down           # Arrêter" 