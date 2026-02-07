#!/bin/bash
# Script para crear el usuario dummy de Telegram

echo "🔧 Creando usuario dummy para suscripciones de Telegram..."

docker exec -i sacv_postgres psql -U sacv_user -d sacv_db <<EOF
-- Crear usuario dummy para suscripciones de Telegram
INSERT INTO users (user_id, email, password_hash, role, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'telegram_bot@sacv.ec',
    'no_password_telegram_only',
    'telegram_subscriber',
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- Verificar
SELECT user_id, email, role FROM users WHERE email = 'telegram_bot@sacv.ec';
EOF

echo ""
echo "✅ Usuario creado. Ahora intenta suscribirte al bot nuevamente."
echo "📱 Envía /start en Telegram y elige tu provincia."
