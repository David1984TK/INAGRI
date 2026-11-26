"""DELETE /parcelas/{id}: elimina una parcela.

Si la parcela todavía tiene sensores o ciclos de siembra responde 409
(la llave foránea lo impide).
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
    id_parcela = leer_id(evento)
    if id_parcela is None:
        return error(400, "El id de la parcela debe ser un número entero positivo.")

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(
                "DELETE FROM parcelas WHERE id_parcela = %s RETURNING id_parcela",
                [id_parcela],
            )
            fila = cursor.fetchone()
    except errors.ForeignKeyViolation:
        return error(409, "La parcela tiene sensores o ciclos de siembra. Elimínalos primero.")
    except psycopg2.Error:
        logger.exception("Error de RDS al eliminar la parcela")
        return error(500, "No se pudo eliminar la parcela.")

    if fila is None:
        return error(404, "No existe una parcela con ese id.")
    return respuesta(200, {"mensaje": "Parcela eliminada"})
