-- INAGRI: datos inventados para la demostración.
-- Las parcelas 1, 2 y 3 y los sensores 1 a 10 coinciden con scripts/cargarLecturas.py:
--   Parcela Sur (1): sensores 1-4 | Parcela Río (2): sensores 5-6 | Parcela Norte (3): sensores 7-10
-- Se puede correr sobre una base recién creada (las llaves empiezan en 1).

INSERT INTO productores (nombre, telefono, correo, estatus) VALUES
    ('Juan Pérez Morales',      '7771234501', 'juan.perez@ejemplo.com',     'activo'),
    ('María López Sánchez',     '7771234502', 'maria.lopez@ejemplo.com',    'activo'),
    ('Pedro Ramírez Flores',    '7771234503', 'pedro.ramirez@ejemplo.com',  'activo'),
    ('Rosa Hernández Díaz',     '7771234504', 'rosa.hernandez@ejemplo.com', 'activo'),
    ('Luis García Ortiz',       '7771234505', 'luis.garcia@ejemplo.com',    'inactivo');

INSERT INTO parcelas (id_productor, nombre, ubicacion, superficie_ha) VALUES
    (1, 'Parcela Sur',        'Ayala, Morelos',       3.50),
    (1, 'Parcela Río',        'Ayala, Morelos',       2.20),
    (2, 'Parcela Norte',      'Cuautla, Morelos',     4.75),
    (2, 'Parcela El Llano',   'Cuautla, Morelos',     1.80),
    (3, 'Parcela Las Palmas', 'Yautepec, Morelos',    5.00),
    (3, 'Parcela El Huerto',  'Yautepec, Morelos',    0.90),
    (4, 'Parcela La Loma',    'Tlaltizapán, Morelos', 2.60),
    (4, 'Parcela San José',   'Tlaltizapán, Morelos', 3.10),
    (5, 'Parcela El Ojo',     'Jojutla, Morelos',     1.50),
    (5, 'Parcela La Joya',    'Jojutla, Morelos',     2.00);

INSERT INTO sensores (id_sensor, id_parcela, descripcion) VALUES
    (1, 1, 'Sensor esquina noreste'),
    (2, 1, 'Sensor esquina noroeste'),
    (3, 1, 'Sensor centro'),
    (4, 1, 'Sensor esquina sur'),
    (5, 2, 'Sensor junto al canal'),
    (6, 2, 'Sensor centro'),
    (7, 3, 'Sensor entrada'),
    (8, 3, 'Sensor centro'),
    (9, 3, 'Sensor lado este'),
    (10, 3, 'Sensor lado oeste');

-- Como los id_sensor se pusieron a mano, el contador sigue desde el 11.
SELECT setval(pg_get_serial_sequence('sensores', 'id_sensor'), (SELECT max(id_sensor) FROM sensores));

INSERT INTO cultivos (nombre, tipo, duracion_dias) VALUES
    ('Maíz',     'Grano',    120),
    ('Frijol',   'Leguminosa', 90),
    ('Jitomate', 'Hortaliza', 100),
    ('Sorgo',    'Grano',    110),
    ('Caña de azúcar', 'Industrial', 365);

INSERT INTO ciclos_siembra (id_parcela, id_cultivo, fecha_siembra, fecha_cosecha_estimada, estado) VALUES
    (1, 1, '2026-07-01', '2026-10-29', 'cosechado'),
    (1, 2, '2026-11-05', '2027-02-03', 'en_curso'),
    (2, 3, '2026-10-15', '2027-01-23', 'en_curso'),
    (3, 1, '2026-09-10', '2027-01-08', 'en_curso'),
    (4, 4, '2026-08-20', '2026-12-08', 'en_curso'),
    (5, 5, '2026-03-01', '2027-03-01', 'en_curso'),
    (7, 2, '2026-12-01', '2027-03-01', 'planeado');
