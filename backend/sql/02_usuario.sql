-- INAGRI: usuario de base de datos con privilegios limitados para las Lambdas.
-- Solo puede SELECT, INSERT, UPDATE y DELETE. No puede crear, modificar ni borrar tablas.
--
-- La contraseña NO se escribe aquí: se pasa como variable de psql.
--   psql -h <host> -U <usuario_admin> -d inagri -v clave_app='<contraseña>' -f sql/02_usuario.sql
-- En AWS, esa misma contraseña se guarda en Secrets Manager (no en el código).

CREATE ROLE inagri_app LOGIN PASSWORD :'clave_app';

SELECT format('GRANT CONNECT ON DATABASE %I TO inagri_app', current_database()) \gexec

GRANT USAGE ON SCHEMA public TO inagri_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO inagri_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO inagri_app;

-- Las tablas que se creen después con el mismo administrador también le dan estos permisos.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO inagri_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO inagri_app;
