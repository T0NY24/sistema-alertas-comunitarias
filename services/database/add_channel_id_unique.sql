-- Agregar constraint UNIQUE a channel_id en la tabla subscriptions
-- Esto permite que el bot de Telegram use ON CONFLICT (channel_id)

-- Agregar el constraint
ALTER TABLE subscriptions
ADD CONSTRAINT subscriptions_channel_id_unique UNIQUE (channel_id);

-- Verificar que se agregó
SELECT
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE
    table_name = 'subscriptions'
    AND constraint_type = 'UNIQUE';