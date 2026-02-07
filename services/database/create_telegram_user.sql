-- Crear usuario dummy para suscripciones de Telegram
-- Este usuario no es para login, solo para asociar suscripciones

INSERT INTO users (user_id, email, password_hash, role, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'telegram_bot@sacv.ec',
    'no_password_telegram_only',
    'telegram_subscriber',
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- Verificar que se creó
SELECT user_id, email, role
FROM users
WHERE
    email = 'telegram_bot@sacv.ec';