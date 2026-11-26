"""POST /productores: registra un productor en RDS.

Cuerpo: nombre (obligatorio), telefono, correo y estatus ('activo' o 'inactivo').
"""
import logging

import psycopg2
from psycopg2 import errors

from common.catalogo import fila_publica, validar_productor
from common.rds import obtener_conexion
from common.respuestas import error, respuesta
from common.validaciones import leer_cuerpo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

COLUMNAS = "id_productor, nombre, telefono, correo, estatus, fecha_alta"


def lambda_handler(evento, contexto):
    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    valores, problema = validar_productor(datos)
    if problema:
        return error(400, problema)

    # Los nombres de columna vienen de una lista fija (CAMPOS_PRODUCTOR), no del usuario.
    columnas = list(valores)
    sql = (
        f"INSERT INTO productores ({', '.join(columnas)}) "
        f"VALUES ({', '.join(['%s'] * len(columnas))}) RETURNING {COLUMNAS}"
    )

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(sql, [valores[c] for c in columnas])
            fila = cursor.fetchone()
    except errors.UniqueViolation:
        return error(409, "Ya existe un productor con ese correo.")
    except psycopg2.Error:
        logger.exception("Error de RDS al registrar el productor")
        return error(500, "No se pudo registrar el productor.")

    return respuesta(201, {"mensaje": "Productor registrado", "productor": fila_publica(fila)})
