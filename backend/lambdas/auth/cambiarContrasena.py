"""PUT /auth/contrasena: el usuario con sesión iniciada cambia su contraseña.

Encabezado: Authorization: Bearer <token>
Cuerpo: {"contrasena_actual": "...", "contrasena_nueva": "..."}

Se usa sobre todo la primera vez que entra un productor, para cambiar la contraseña
temporal que le dio el administrador (debe_cambiar_contrasena = true).
"""
import logging

import psycopg2

from common.rds import obtener_conexion
from common.respuestas import error, respuesta
from common.seguridad import (
    cifrar_contrasena,
    leer_token,
    validar_contrasena_nueva,
    verificar_contrasena,
)
from common.validaciones import leer_cuerpo

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(evento, contexto):
    sesion = leer_token(evento)
    if sesion is None:
        return error(401, "Inicia sesión para continuar.")

    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    actual = datos.get("contrasena_actual")
    nueva = datos.get("contrasena_nueva")
    if not isinstance(actual, str) or not actual:
        return error(400, "Escribe tu contraseña actual.")
    problema = validar_contrasena_nueva(nueva)
    if problema:
        return error(400, problema)
    if nueva == actual:
        return error(400, "La contraseña nueva debe ser distinta de la actual.")

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(
                "SELECT hash_contrasena FROM usuarios WHERE id_usuario = %s",
                [int(sesion["sub"])],
            )
            usuario = cursor.fetchone()
            if usuario is None:
                return error(401, "Inicia sesión para continuar.")
            if not verificar_contrasena(actual, usuario["hash_contrasena"]):
                return error(400, "La contraseña actual no es correcta.")
            cursor.execute(
                "UPDATE usuarios SET hash_contrasena = %s, debe_cambiar_contrasena = FALSE "
                "WHERE id_usuario = %s",
                [cifrar_contrasena(nueva), int(sesion["sub"])],
            )
    except psycopg2.Error:
        logger.exception("Error de RDS al cambiar la contraseña")
        return error(500, "No se pudo cambiar la contraseña.")

    return respuesta(200, {"mensaje": "Contraseña actualizada"})
