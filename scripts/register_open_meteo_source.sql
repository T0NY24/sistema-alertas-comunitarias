-- Registrar fuente de Clima (Open-Meteo) para Loja
-- Tipo: 'lluvia' (Compatible con restricciones de DB)
-- Coordenadas Loja: -3.9931, -79.2042

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
SELECT
    gen_random_uuid (),
    'Open-Meteo Loja',
    'https://api.open-meteo.com/v1/forecast',
    'lluvia', -- USAMOS 'lluvia' para pasar el Check Constraint
    'open-meteo.com',
    '{"lat": -3.9931, "lon": -79.2042, "city": "Loja"}',
    600,
    true
WHERE
    NOT EXISTS (
        SELECT 1
        FROM sources
        WHERE
            name = 'Open-Meteo Loja'
    );

-- Verificar inserción
SELECT name, type, active
FROM sources
WHERE
    name = 'Open-Meteo Loja';