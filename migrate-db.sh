#!/bin/bash
# Script para aplicar la migración de province_id

echo "🔧 Aplicando migración: Agregar province_id a events..."

# Ejecutar SQL en el contenedor de PostgreSQL
docker exec -i sacv_postgres psql -U sacv_user -d sacv_db <<EOF
-- Agregar columna province_id si no existe
ALTER TABLE events ADD COLUMN IF NOT EXISTS province_id INTEGER REFERENCES provinces (province_id);

-- Verificar que se agregó
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'events' AND column_name = 'province_id';
EOF

echo "✅ Migración completada!"
echo ""
echo "📊 Verifica creando un evento de prueba desde el simulador."
