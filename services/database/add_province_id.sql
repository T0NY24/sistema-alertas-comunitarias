-- Script para agregar province_id a la tabla events si ya existe
-- Ejecutar SOLO si la base de datos ya fue creada sin province_id

-- Agregar columna province_id
ALTER TABLE events
ADD COLUMN IF NOT EXISTS province_id INTEGER REFERENCES provinces (province_id);

-- Verificar que se agregó correctamente
SELECT column_name, data_type
FROM information_schema.columns
WHERE
    table_name = 'events'
ORDER BY ordinal_position;