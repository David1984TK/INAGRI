"""Conexión a PostgreSQL: Amazon RDS en AWS, o el contenedor de Docker en local.

- En AWS: se define RDS_SECRET_NAME y las credenciales se leen de Secrets Manager.
  El secreto es el JSON que crea RDS: {"host", "port", "username", "password", "dbname"}.
- En local: RDS_SECRET_NAME se deja vacío y se usan DB_HOST, DB_PORT, DB_NAME,
  DB_USER y DB_PASSWORD del archivo .env.

La conexión se guarda en una variable del módulo para reutilizarla entre invocaciones
de la misma Lambda (así no se abre una conexión nueva en cada petición).
"""
import json
import os

import psycopg2
from psycopg2.extras import RealDictCursor

_conexion = None


def _credenciales():
    nombre_secreto = os.environ.get("RDS_SECRET_NAME")
    if nombre_secreto:
        import boto3

        cliente = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION"))
        secreto = json.loads(cliente.get_secret_value(SecretId=nombre_secreto)["SecretString"])
        return {
            "host": secreto["host"],
            "port": int(secreto.get("port", 5432)),
            "dbname": secreto.get("dbname") or os.environ.get("DB_NAME", "inagri"),
            "user": secreto["username"],
            "password": secreto["password"],
        }

    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ.get("DB_NAME", "inagri"),
        "user": os.environ.get("DB_USER", "inagri_app"),
        "password": os.environ["DB_PASSWORD"],
    }


def obtener_conexion():
    """Regresa una conexión abierta. Las filas se leen como diccionarios."""
    global _conexion
    if _conexion is None or _conexion.closed:
        _conexion = psycopg2.connect(
            **_credenciales(), connect_timeout=5, cursor_factory=RealDictCursor
        )
    return _conexion
