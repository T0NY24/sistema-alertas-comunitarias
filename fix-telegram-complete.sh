#!/bin/bash
# Script para arreglar el error de suscripción de Telegram

echo "🔧 Arreglando restricciones de la tabla subscriptions..."

# 1. Crear usuario dummy si no existe
echo "📝 Paso 1: Crear usuario para Telegram..."
docker exec -i sacv_postgres psql -U sacv_user -d sacv_db <<EOF
INSERT INTO users (user_id, email, password_hash, role, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'telegram_bot@sacv.ec',
    'no_password_telegram_only',
    'telegram_subscriber',
    NOW()
)
ON CONFLICT (email) DO NOTHING;
EOF

# 2. Agregar constraint UNIQUE a channel_id
echo "🔑 Paso 2: Agregar constraint UNIQUE a channel_id..."
docker exec -i sacv_postgres psql -U sacv_user -d sacv_db <<EOF
-- Eliminar duplicados si existen
DELETE FROM subscriptions a USING subscriptions b
WHERE a.sub_id < b.sub_id AND a.channel_id = b.channel_id;

-- Agregar el constraint
ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_channel_id_unique;
ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_channel_id_unique UNIQUE (channel_id);

-- Verificar
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'subscriptions' AND constraint_type = 'UNIQUE';
EOF

echo ""
echo "✅ ¡Arreglado!"
echo ""
echo "📱 Ahora intenta suscribirte al bot nuevamente:"
echo "   1. Abre Telegram"
echo "   2. Envía /start a @AlertasComunitariasAnthonyBot"
echo "   3. Selecciona tu provincia"
echo ""
echo "¡Debería funcionar sin errores! 🎉"
