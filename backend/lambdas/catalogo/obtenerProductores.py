"""GET /productores y GET /productores/{id}: consulta productores en RDS.

- /productores          lista todos. Filtro opcional: ?estatus=activo o ?estatus=inactivo
- /productores/{id}     regresa uno, con el total de parcelas. 404 si no existe.
"""
import logging

import psycopg2

from common.catalogo import ESTATUS, fila_publica, leer_id
from common.rds import obtener_conexion
from common.respuestas import error, respuesta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQL_BASE = """
    SELECT pr.id_productor, pr.nombre, pr.telefono, pr.correo, pr.estatus, pr.fecha_alta,
           COUNT(pa.id_parcela) AS total_parcelas
    FROM productores pr
    LEFT JOIN parcelas pa ON pa.id_productor = pr.id_productor
"""
SQL_AGRUPAR = " GROUP BY pr.id_productor ORDER BY pr.id_productor"


def lambda_handler(evento, contexto):
    parametros_ruta = evento.get("pathParameters") or {}
    filtros = evento.get("queryStringParameters") or {}

    if "id" in parametros_ruta:
        id_productor = leer_id(evento)
        if id_productor is None:
            return error(400, "El id del productor debe ser un número entero positivo.")
        sql, valores = SQL_BASE + " WHERE pr.id_productor = %s" + SQL_AGRUPAR, [id_productor]
    else:
        id_productor = None
        estatus = filtros.get("estatus")
        if estatus is not None and estatus not in ESTATUS:
            return error(400, "estatus debe ser 'activo' o 'inactivo'.")
        if estatus:
            sql, valores = SQL_BASE + " WHERE pr.estatus = %s" + SQL_AGRUPAR, [estatus]
        else:
            sql, valores = SQL_BASE + SQL_AGRUPAR, []

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(sql, valores)
            filas = cursor.fetchall()
    except psycopg2.Error:
        logger.exception("Error de RDS al consultar productores")
        return error(500, "No se pudieron consultar los productores.")

    productores = [fila_publica(fila) for fila in filas]

    if id_productor is not None:
        if not productores:
            return error(404, "No existe un productor con ese id.")
        return respuesta(200, {"productor": productores[0]})

    return respuesta(200, {"total": len(productores), "productores": productores})
