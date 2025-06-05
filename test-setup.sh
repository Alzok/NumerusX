#!/bin/bash

echo "🚀 Test de démarrage NumerusX"
echo "================================"

# Vérifier que Docker Compose fonctionne
echo "📦 Vérification des conteneurs..."
docker compose ps

echo ""
echo "🔍 Images Docker construites:"
docker images | grep numerusx

echo ""
echo "📝 Test des endpoints (si backend running):"
echo "Backend Health: http://localhost:8000/health"
echo "API Health: http://localhost:8000/api/v1/system/health"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"

echo ""
echo "🧪 Test de connectivité:"
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ Backend disponible"
else
    echo "❌ Backend non accessible"
fi

if curl -f http://localhost:5173 &>/dev/null; then
    echo "✅ Frontend disponible"
else
    echo "❌ Frontend non accessible"
fi

echo ""
echo "📊 Logs récents:"
echo "docker compose logs --tail=10" 

echo "🚀 Test de démarrage NumerusX"
echo "================================"

# Vérifier que Docker Compose fonctionne
echo "📦 Vérification des conteneurs..."
docker compose ps

echo ""
echo "🔍 Images Docker construites:"
docker images | grep numerusx

echo ""
echo "📝 Test des endpoints (si backend running):"
echo "Backend Health: http://localhost:8000/health"
echo "API Health: http://localhost:8000/api/v1/system/health"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"

echo ""
echo "🧪 Test de connectivité:"
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ Backend disponible"
else
    echo "❌ Backend non accessible"
fi

if curl -f http://localhost:5173 &>/dev/null; then
    echo "✅ Frontend disponible"
else
    echo "❌ Frontend non accessible"
fi

echo ""
echo "📊 Logs récents:"
echo "docker compose logs --tail=10" 