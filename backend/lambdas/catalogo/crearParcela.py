"""POST /parcelas: registra una parcela de un productor.

Cuerpo: id_productor, nombre y superficie_ha (obligatorios), ubicacion (opcional).
Si el productor no existe responde 404.
"""
import logging

import psycopg2
from psycopg2 import errors

from common.catalogo import fila_publica, validar_parcela
from common.rds import obtener_conexion
from common.respuestas import error, respuesta
from common.validaciones import leer_cuerpo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

COLUMNAS = "id_parcela, id_productor, nombre, ubicacion, superficie_ha, fecha_alta"


def lambda_handler(evento, contexto):
    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    valores, problema = validar_parcela(datos)
    if problema:
        return error(400, problema)

    columnas = list(valores)
    sql = (
        f"INSERT INTO parcelas ({', '.join(columnas)}) "
        f"VALUES ({', '.join(['%s'] * len(columnas))}) RETURNING {COLUMNAS}"
    )

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(sql, [valores[c] for c in columnas])
            fila = cursor.fetchone()
    except errors.ForeignKeyViolation:
        return error(404, "No existe un productor con ese id_productor.")
    except psycopg2.Error:
        logger.exception("Error de RDS al registrar la parcela")
        return error(500, "No se pudo registrar la parcela.")

    return respuesta(201, {"mensaje": "Parcela registrada", "parcela": fila_publica(fila)})
