-- INAGRI: datos inventados para la demostración.
-- Las parcelas 1, 2 y 3 y los sensores 1 a 10 coinciden con scripts/cargarLecturas.py:
--   Parcela Sur (1): sensores 1-4 | Parcela Río (2): sensores 5-6 | Parcela Norte (3): sensores 7-10
-- Con los rangos de los cultivos, la Parcela Sur sale con humedad baja y la Río con
-- temperatura alta (alerta "Requiere atención"), y la Norte en rango, como en los bocetos.
-- Se puede correr sobre una base recién creada (las llaves empiezan en 1).
--
-- Cuentas de demostración (contraseña de todas: Inagri2026):
--   admin@inagri.com            administrador
--   juan.perez@ejemplo.com      productor (Parcela Sur y Parcela Río)
--   maria.lopez@ejemplo.com     productor (Parcela Norte)
--   rosa.hernandez@ejemplo.com  productor que debe cambiar su contraseña al entrar
--   luis.garcia@ejemplo.com     productor dado de baja (no puede entrar)

INSERT INTO productores (nombre, telefono, correo, comunidad, estatus) VALUES
    ('Juan Pérez Morales',   '7771234501', 'juan.perez@ejemplo.com',     'Ayala',       'activo'),
    ('María López Sánchez',  '7771234502', 'maria.lopez@ejemplo.com',    'Cuautla',     'activo'),
    ('Pedro Ramírez Flores', '7771234503', 'pedro.ramirez@ejemplo.com',  'Yautepec',    'activo'),
    ('Rosa Hernández Díaz',  '7771234504', 'rosa.hernandez@ejemplo.com', 'Tlaltizapán', 'activo'),
    ('Luis García Ortiz',    '7771234505', 'luis.garcia@ejemplo.com',    'Jojutla',     'inactivo');

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

INSERT INTO cultivos (nombre, tipo, duracion_dias, humedad_min, humedad_max, temp_min, temp_max) VALUES
    ('Maíz',           'Grano',      120, 35, 60, 18, 32),
    ('Frijol',         'Leguminosa',  90, 40, 65, 15, 28),
    ('Jitomate',       'Hortaliza',  100, 50, 75, 18, 30),
    ('Sorgo',          'Grano',      110, 30, 55, 20, 35),
    ('Caña de azúcar', 'Industrial', 365, 45, 75, 20, 35);

INSERT INTO ciclos_siembra (id_parcela, id_cultivo, fecha_siembra, fecha_cosecha_estimada, estado) VALUES
    (1, 1, '2026-07-01', '2026-10-29', 'cosechado'),
    (1, 2, '2026-11-05', '2027-02-03', 'en_curso'),
    (2, 3, '2026-10-15', '2027-01-23', 'en_curso'),
    (3, 1, '2026-09-10', '2027-01-08', 'en_curso'),
    (4, 4, '2026-08-20', '2026-12-08', 'en_curso'),
    (5, 5, '2026-03-01', '2027-03-01', 'en_curso'),
    (7, 2, '2026-12-01', '2027-03-01', 'planeado');

-- Los hash son de la contraseña Inagri2026 (scrypt, generados con common/seguridad.py).
INSERT INTO usuarios (nombre, correo, hash_contrasena, rol, id_productor, debe_cambiar_contrasena) VALUES
    ('Administrador INAGRI', 'admin@inagri.com',
     'scrypt$16384$8$1$DCD9czl/+srapQslJY+bLA==$5gxUR0QMJbYEsrM7q0TskFCjV2G7mBFED0kZQPNLBhU=', 'administrador', NULL, FALSE),
    ('Juan Pérez Morales', 'juan.perez@ejemplo.com',
     'scrypt$16384$8$1$IpX/61l6Zn2mwl67+k/qUQ==$46nxZO6+yKpxHa820Q9/+MJcmTFvvQdXNicrgATu7Yw=', 'productor', 1, FALSE),
    ('María López Sánchez', 'maria.lopez@ejemplo.com',
     'scrypt$16384$8$1$BvTnZke+DppTP5AvLQPI9w==$M0oy5cLjHVrPqmCh06yWm1IzL9ZOdDNoBOq2ifOTv+E=', 'productor', 2, FALSE),
    ('Pedro Ramírez Flores', 'pedro.ramirez@ejemplo.com',
     'scrypt$16384$8$1$76V1PFKa2ogy6c2or257RA==$PgyT3tuD11jG4U6rArgN8E0mxefadbZfQNYNIVXY/P8=', 'productor', 3, FALSE),
    ('Rosa Hernández Díaz', 'rosa.hernandez@ejemplo.com',
     'scrypt$16384$8$1$oi42uhylQdW6onXlWBKtYw==$MfG7CB23kygJ1KG976ipERPpHuNoxeC6CP9NSb+Frdo=', 'productor', 4, TRUE),
    ('Luis García Ortiz', 'luis.garcia@ejemplo.com',
     'scrypt$16384$8$1$85ug6FIRg8RlktpCPri1DQ==$V4H64IpzXd7TbCwgeovRPjjz6PA47Wp8OxCcSXeCCvc=', 'productor', 5, FALSE);
