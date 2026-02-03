-- Script para registrar la fuente del IGEPN en la base de datos
-- Ejecutar este script en DBeaver o psql

-- Insertar la fuente del IGEPN
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
        'IGEPN - Instituto Geofísico',
        'https://www.igepn.edu.ec/servicios/ultimo-sismo',
        'sismo',
        'igepn.edu.ec',
        '{"selector": "#sismo_table tr", "fields": ["fecha", "lat", "long", "prof", "mag", "zona"]}',
        300, -- 5 minutos
        true
    ) ON CONFLICT (base_url) DO
UPDATE
SET
    active = true,
    frequency_sec = 300;

-- Verificar que se insertó correctamente
SELECT
    source_id,
    name,
    type,
    base_url,
    active,
    frequency_sec
FROM sources
WHERE
    domain = 'igepn.edu.ec';