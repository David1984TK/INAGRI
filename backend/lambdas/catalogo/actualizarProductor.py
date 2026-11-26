"""PUT /productores/{id}: modifica los datos de un productor.

Se puede mandar cualquiera de estos campos: nombre, telefono, correo, estatus.
Para dar de baja sin borrar, mandar {"estatus": "inactivo"}.
"""
import logging

import psycopg2
from psycopg2 import errors

from common.catalogo import fila_publica, leer_id, validar_productor
from common.rds import obtener_conexion
from common.respuestas import error, respuesta
from common.validaciones import leer_cuerpo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

COLUMNAS = "id_productor, nombre, telefono, correo, estatus, fecha_alta"


def lambda_handler(evento, contexto):
    id_productor = leer_id(evento)
    if id_productor is None:
        return error(400, "El id del productor debe ser un número entero positivo.")

    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    cambios, problema = validar_productor(datos, parcial=True)
    if problema:
        return error(400, problema)

    columnas = list(cambios)
    sql = (
        "UPDATE productores SET "
        + ", ".join(f"{c} = %s" for c in columnas)
        + f" WHERE id_productor = %s RETURNING {COLUMNAS}"
    )

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(sql, [cambios[c] for c in columnas] + [id_productor])
            fila = cursor.fetchone()
    except errors.UniqueViolation:
        return error(409, "Ya existe un productor con ese correo.")
    except psycopg2.Error:
        logger.exception("Error de RDS al actualizar el productor")
        return error(500, "No se pudo actualizar el productor.")

    if fila is None:
        return error(404, "No existe un productor con ese id.")
    return respuesta(200, {"mensaje": "Productor actualizado", "productor": fila_publica(fila)})
