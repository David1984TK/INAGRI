"""GET /productores/{id}/parcelas: lista las parcelas de un productor.

Es una de las operaciones mínimas del tema 5. Regresa los datos básicos del productor
y sus parcelas, cada una con su total de sensores. 404 si el productor no existe.
"""
import logging

import psycopg2

from common.catalogo import fila_publica, leer_id
from common.rds import obtener_conexion
from common.respuestas import error, respuesta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQL_PRODUCTOR = "SELECT id_productor, nombre, estatus FROM productores WHERE id_productor = %s"
SQL_PARCELAS = """
    SELECT pa.id_parcela, pa.nombre, pa.ubicacion, pa.superficie_ha, pa.fecha_alta,
           COUNT(s.id_sensor) AS total_sensores
    FROM parcelas pa
    LEFT JOIN sensores s ON s.id_parcela = pa.id_parcela
    WHERE pa.id_productor = %s
    GROUP BY pa.id_parcela
    ORDER BY pa.id_parcela
"""


def lambda_handler(evento, contexto):
    id_productor = leer_id(evento)
    if id_productor is None:
        return error(400, "El id del productor debe ser un número entero positivo.")

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(SQL_PRODUCTOR, [id_productor])
            productor = cursor.fetchone()
            parcelas = []
            if productor is not None:
                cursor.execute(SQL_PARCELAS, [id_productor])
                parcelas = cursor.fetchall()
    except psycopg2.Error:
        logger.exception("Error de RDS al consultar las parcelas del productor")
        return error(500, "No se pudieron consultar las parcelas.")

    if productor is None:
        return error(404, "No existe un productor con ese id.")

    lista = [fila_publica(fila) for fila in parcelas]
    return respuesta(
        200,
        {"productor": fila_publica(productor), "total": len(lista), "parcelas": lista},
    )
