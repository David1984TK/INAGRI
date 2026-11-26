"""DELETE /productores/{id}: elimina un productor.

Si el productor todavía tiene parcelas responde 409: primero hay que eliminar
o reasignar sus parcelas (la llave foránea lo impide).
Al eliminarlo se elimina también su cuenta de acceso (ON DELETE CASCADE en usuarios).
"""
import logging

import psycopg2
from psycopg2 import errors

from common.catalogo import leer_id
from common.rds import obtener_conexion
from common.respuestas import error, respuesta

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(evento, contexto):
    id_productor = leer_id(evento)
    if id_productor is None:
        return error(400, "El id del productor debe ser un número entero positivo.")

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(
                "DELETE FROM productores WHERE id_productor = %s RETURNING id_productor",
                [id_productor],
            )
            fila = cursor.fetchone()
    except errors.ForeignKeyViolation:
        return error(409, "El productor tiene parcelas registradas. Elimínalas o reasígnalas primero.")
    except psycopg2.Error:
        logger.exception("Error de RDS al eliminar el productor")
        return error(500, "No se pudo eliminar el productor.")

    if fila is None:
        return error(404, "No existe un productor con ese id.")
    return respuesta(200, {"mensaje": "Productor eliminado"})
