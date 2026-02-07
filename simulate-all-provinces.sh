#!/bin/bash
# Script rápido para ejecutar la simulación de 24 provincias

cd ~/sistema-alertas

echo "🚀 Ejecutando simulación de las 24 provincias..."
echo ""

python3 scripts/simulate_24_provinces.py

echo ""
echo "✅ Proceso completado. Revisa tu Telegram!"
