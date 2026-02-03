-- Script para reemplazar IGEPN con USGS API
-- Ejecutar en DBeaver o psql

-- 1. Desactivar la fuente rota del IGEPN
UPDATE sources SET active = false WHERE domain = 'igepn.edu.ec';

-- 2. Insertar la nueva fuente confiable del USGS
INSERT INTO
    sources (
        source_id,
        name,
        base_url,
        type,
        domain,
        parser_config,
        frequency_sec,
        active
    )
VALUES (
        gen_random_uuid (),
        'USGS Earthquake API',
        'https://earthquake.usgs.gov/fdsnws/event/1/query',
        'sismo',
        'earthquake.usgs.gov',
        '{"format": "geojson", "country": "EC", "minmagnitude": 4.0}',
        300, -- Cada 5 minutos
        true
    ) ON CONFLICT (base_url) DO
UPDATE
SET
    active = true,
    frequency_sec = 300;

-- 3. Verificar que se registró correctamente
SELECT
    source_id,
    name,
    type,
    base_url,
    active,
    frequency_sec,
    domain
FROM sources
WHERE
    domain IN (
        'earthquake.usgs.gov',
        'igepn.edu.ec'
    )
ORDER BY active DESC, name;

-- Deberías ver:
-- ✅ USGS Earthquake API (active = true)
-- ❌ IGEPN - Instituto Geofísico (active = false)