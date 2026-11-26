"""GET /parcelas y GET /parcelas/{id}: consulta parcelas en RDS.

- /parcelas        lista todas, con el nombre del productor y el total de sensores.
- /parcelas/{id}   regresa una, con la lista de sus sensores. 404 si no existe.

Para las parcelas de un productor usar GET /productores/{id}/parcelas
(Lambda obtenerParcelasProductor).
"""
import logging

import psycopg2

from common.catalogo import fila_publica, leer_id
from common.rds import obtener_conexion
from common.respuestas import error, respuesta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQL_LISTA = """
    SELECT pa.id_parcela, pa.id_productor, pr.nombre AS productor, pa.nombre, pa.ubicacion,
           pa.superficie_ha, pa.fecha_alta, COUNT(s.id_sensor) AS total_sensores
    FROM parcelas pa
    JOIN productores pr ON pr.id_productor = pa.id_productor
    LEFT JOIN sensores s ON s.id_parcela = pa.id_parcela
    {filtro}
    GROUP BY pa.id_parcela, pr.nombre
    ORDER BY pa.id_parcela
"""
SQL_SENSORES = """
    SELECT id_sensor, descripcion, estatus
    FROM sensores
    WHERE id_parcela = %s
    ORDER BY id_sensor
"""


def lambda_handler(evento, contexto):
    parametros_ruta = evento.get("pathParameters") or {}
    id_parcela = None
    if "id" in parametros_ruta:
        id_parcela = leer_id(evento)
        if id_parcela is None:
            return error(400, "El id de la parcela debe ser un número entero positivo.")

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            if id_parcela is None:
                cursor.execute(SQL_LISTA.format(filtro=""), [])
                filas = cursor.fetchall()
                sensores = []
            else:
                cursor.execute(SQL_LISTA.format(filtro="WHERE pa.id_parcela = %s"), [id_parcela])
                filas = cursor.fetchall()
                sensores = []
                if filas:
                    cursor.execute(SQL_SENSORES, [id_parcela])
                    sensores = cursor.fetchall()
    except psycopg2.Error:
        logger.exception("Error de RDS al consultar parcelas")
        return error(500, "No se pudieron consultar las parcelas.")

    parcelas = [fila_publica(fila) for fila in filas]

    if id_parcela is not None:
        if not parcelas:
            return error(404, "No existe una parcela con ese id.")
        parcela = parcelas[0]
        parcela["sensores"] = [fila_publica(s) for s in sensores]
        return respuesta(200, {"parcela": parcela})

    return respuesta(200, {"total": len(parcelas), "parcelas": parcelas})
