"""POST /productores: registra un productor y su cuenta de acceso (pantalla de Altas).

Cuerpo: nombre y correo (obligatorios), telefono, comunidad y estatus ('activo' o 'inactivo').

En una sola transacción se crean dos registros en RDS:
  - productores: los datos del productor.
  - usuarios: su cuenta con rol productor, el mismo correo y una contraseña temporal.
La contraseña temporal se regresa UNA sola vez en la respuesta, para que el administrador
se la entregue al productor. Al entrar por primera vez, el sistema le pide cambiarla.
"""
import logging

import psycopg2
from psycopg2 import errors

from common.catalogo import fila_publica, validar_productor
from common.rds import obtener_conexion
from common.respuestas import error, respuesta
from common.seguridad import cifrar_contrasena, generar_contrasena_temporal
from common.validaciones import leer_cuerpo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

COLUMNAS = "id_productor, nombre, telefono, correo, comunidad, estatus, fecha_alta"
SQL_USUARIO = """
    INSERT INTO usuarios (nombre, correo, hash_contrasena, rol, id_productor, debe_cambiar_contrasena)
    VALUES (%s, %s, %s, 'productor', %s, TRUE)
"""


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
    contrasena_temporal = generar_contrasena_temporal()

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(sql, [valores[c] for c in columnas])
            fila = cursor.fetchone()
            cursor.execute(
                SQL_USUARIO,
                [fila["nombre"], fila["correo"], cifrar_contrasena(contrasena_temporal), fila["id_productor"]],
            )
    except errors.UniqueViolation:
        return error(409, "Ya existe una cuenta con ese correo.")
    except psycopg2.Error:
        logger.exception("Error de RDS al registrar el productor")
        return error(500, "No se pudo registrar el productor.")

    return respuesta(
        201,
        {
            "mensaje": "Productor registrado",
            "productor": fila_publica(fila),
            "acceso": {"correo": fila["correo"], "contrasena_temporal": contrasena_temporal},
        },
    )
