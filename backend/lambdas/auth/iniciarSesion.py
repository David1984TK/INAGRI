"""POST /auth/login: inicia sesión con correo y contraseña.

Cuerpo: {"correo": "...", "contrasena": "..."}
Respuesta 200: token de sesión (JWT, dura 8 horas) y los datos del usuario, incluido su rol.
El frontend manda el token en cada petición: Authorization: Bearer <token>.

Por seguridad, si el correo no existe o la contraseña está mal se responde lo mismo (401).
Un productor dado de baja (estatus inactivo) no puede entrar (403).
"""
import logging

import psycopg2

from common.catalogo import validar_correo
from common.rds import obtener_conexion
from common.respuestas import error, respuesta
from common.seguridad import HASH_RELLENO, crear_token, verificar_contrasena
from common.validaciones import leer_cuerpo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQL_USUARIO = """
    SELECT u.id_usuario, u.nombre, u.correo, u.hash_contrasena, u.rol, u.id_productor,
           u.debe_cambiar_contrasena, p.estatus AS estatus_productor
    FROM usuarios u
    LEFT JOIN productores p ON p.id_productor = u.id_productor
    WHERE u.correo = %s
"""
SQL_ACCESO = "UPDATE usuarios SET ultimo_acceso = now() WHERE id_usuario = %s"

CREDENCIALES_INCORRECTAS = "Correo o contraseña incorrectos."


def lambda_handler(evento, contexto):
    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    correo, problema = validar_correo(datos.get("correo"))
    contrasena = datos.get("contrasena")
    if problema or not isinstance(contrasena, str) or not 0 < len(contrasena) <= 72:
        return error(400, "Escribe tu correo y tu contraseña.")

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(SQL_USUARIO, [correo])
            usuario = cursor.fetchone()

            hash_guardado = usuario["hash_contrasena"] if usuario else HASH_RELLENO
            correcta = verificar_contrasena(contrasena, hash_guardado)
            if usuario is None or not correcta:
                return error(401, CREDENCIALES_INCORRECTAS)
            if usuario["rol"] == "productor" and usuario["estatus_productor"] != "activo":
                return error(403, "Tu cuenta está dada de baja. Comunícate con el administrador.")

            cursor.execute(SQL_ACCESO, [usuario["id_usuario"]])
    except psycopg2.Error:
        logger.exception("Error de RDS al iniciar sesión")
        return error(500, "No se pudo iniciar sesión.")

    token = crear_token(
        {
            "sub": str(usuario["id_usuario"]),
            "rol": usuario["rol"],
            "id_productor": usuario["id_productor"],
        }
    )
    return respuesta(
        200,
        {
            "token": token,
            "usuario": {
                "id_usuario": usuario["id_usuario"],
                "nombre": usuario["nombre"],
                "correo": usuario["correo"],
                "rol": usuario["rol"],
                "id_productor": usuario["id_productor"],
                "debe_cambiar_contrasena": usuario["debe_cambiar_contrasena"],
            },
        },
    )
