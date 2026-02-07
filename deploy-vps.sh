#!/bin/bash
# Script de deployment FORZADO para VPS
# Elimina TODO el caché y reconstruye desde cero

echo "🔥 DEPLOYMENT VPS - Eliminando caché completo..."

# Detener TODOS los contenedores
docker-compose down

# Eliminar contenedores huérfanos
docker-compose down --remove-orphans

# Eliminar imágenes viejas del proyecto
docker rmi -f $(docker images | grep 'sistema-alertas' | awk '{print $3}') 2>/dev/null || true
docker rmi -f $(docker images | grep 'admin-panel' | awk '{print $3}') 2>/dev/null || true
docker rmi -f $(docker images | grep 'api-gateway' | awk '{print $3}') 2>/dev/null || true

# Limpiar caché de build de Docker
docker builder prune -af

echo "🔨 Reconstruyendo admin-panel SIN CACHÉ..."
docker-compose build --no-cache --pull admin-panel

echo "🔨 Reconstruyendo api-gateway SIN CACHÉ..."
docker-compose build --no-cache --pull api-gateway

echo "🚀 Levantando servicios..."
docker-compose up -d

echo "✅ Deployment completado!"
echo ""
echo "📊 Verifica:"
echo "   - Frontend: http://217.216.67.99:3001"
echo "   - API Stats: http://217.216.67.99:8001/api/stats"
echo ""
echo "🔍 Ver logs:"
echo "   docker-compose logs -f admin-panel"
echo "   docker-compose logs -f api-gateway"
