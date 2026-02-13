-- Poblar tabla de provincias del Ecuador
-- ID 0 = Alertas Nacionales
-- IDs 1-24 = 24 provincias del Ecuador

INSERT INTO
    provinces (province_id, name)
VALUES (0, 'Nacional'),
    (1, 'Azuay'),
    (2, 'Bolívar'),
    (3, 'Cañar'),
    (4, 'Carchi'),
    (5, 'Chimborazo'),
    (6, 'Cotopaxi'),
    (7, 'El Oro'),
    (8, 'Esmeraldas'),
    (9, 'Galápagos'),
    (10, 'Guayas'),
    (11, 'Imbabura'),
    (12, 'Loja'),
    (13, 'Los Ríos'),
    (14, 'Manabí'),
    (15, 'Morona Santiago'),
    (16, 'Napo'),
    (17, 'Orellana'),
    (18, 'Pastaza'),
    (19, 'Pichincha'),
    (20, 'Santa Elena'),
    (
        21,
        'Santo Domingo de los Tsáchilas'
    ),
    (22, 'Sucumbíos'),
    (23, 'Tungurahua'),
    (24, 'Zamora Chinchipe') ON CONFLICT (province_id) DO NOTHING;

-- Verificar que se insertaron correctamente
SELECT COUNT(*) as total_provincias FROM provinces;

SELECT province_id, name FROM provinces ORDER BY province_id;