"""PUT /parcelas/{id}: modifica los datos de una parcela.

Se puede mandar cualquiera de estos campos: id_productor, nombre, ubicacion, superficie_ha.
Si se cambia id_productor y ese productor no existe responde 404.
"""
import logging

import psycopg2
from psycopg2 import errors

from common.catalogo import fila_publica, leer_id, validar_parcela
from common.rds import obtener_conexion
from common.respuestas import error, respuesta
from common.validaciones import leer_cuerpo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

COLUMNAS = "id_parcela, id_productor, nombre, ubicacion, superficie_ha, fecha_alta"


def lambda_handler(evento, contexto):
    id_parcela = leer_id(evento)
    if id_parcela is None:
        return error(400, "El id de la parcela debe ser un número entero positivo.")

    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    cambios, problema = validar_parcela(datos, parcial=True)
    if problema:
        return error(400, problema)

    columnas = list(cambios)
    sql = (
        "UPDATE parcelas SET "
        + ", ".join(f"{c} = %s" for c in columnas)
        + f" WHERE id_parcela = %s RETURNING {COLUMNAS}"
    )

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(sql, [cambios[c] for c in columnas] + [id_parcela])
            fila = cursor.fetchone()
    except errors.ForeignKeyViolation:
        return error(404, "No existe un productor con ese id_productor.")
    except psycopg2.Error:
        logger.exception("Error de RDS al actualizar la parcela")
        return error(500, "No se pudo actualizar la parcela.")

    if fila is None:
        return error(404, "No existe una parcela con ese id.")
    return respuesta(200, {"mensaje": "Parcela actualizada", "parcela": fila_publica(fila)})
