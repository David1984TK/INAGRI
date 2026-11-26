#!/bin/bash
# Se ejecuta solo la primera vez que arranca el contenedor de Postgres (base vacía).
# Crea las tablas, el usuario limitado y carga los datos de demostración.
set -e

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /sql/01_tablas.sql
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v clave_app="$DB_APP_PASSWORD" -f /sql/02_usuario.sql
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /sql/03_datos_demo.sql
