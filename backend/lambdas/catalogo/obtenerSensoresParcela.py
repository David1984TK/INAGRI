"""GET /parcelas/{id}/sensores: pantalla Detalle de parcela.

Junta datos de las dos bases:
- RDS: la parcela, su productor, el ciclo en curso con el rango ideal del cultivo y los sensores.
- DynamoDB: la última lectura de cada sensor.

Cada sensor regresa su estado ("en_linea", "sin_senal" o "inactivo"), su última lectura
y sus alertas. Un sensor está "sin señal" si no ha mandado lecturas en 15 minutos
(MINUTOS_SIN_SENAL). Para ver la gráfica de un sensor, el frontend usa
GET /sensores/{id}/lecturas?horas=24.
404 si la parcela no existe.
"""
import logging

import psycopg2
from botocore.exceptions import BotoCoreError, ClientError

from common.catalogo import leer_id
from common.dynamo import obtener_tabla
from common.monitoreo import ahora_utc, estado_parcela, rango_ideal, resumen_ciclo, ultimas_lecturas
from common.rds import obtener_conexion
from common.respuestas import error, respuesta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQL_PARCELA = """
    SELECT pa.id_parcela, pa.id_productor, pr.nombre AS productor, pa.nombre, pa.ubicacion,
           pa.superficie_ha,
           c.id_ciclo, c.fecha_siembra, c.fecha_cosecha_estimada,
           cu.nombre AS cultivo, cu.humedad_min, cu.humedad_max, cu.temp_min, cu.temp_max
    FROM parcelas pa
    JOIN productores pr ON pr.id_productor = pa.id_productor
    LEFT JOIN LATERAL (
        SELECT cs.id_ciclo, cs.id_cultivo, cs.fecha_siembra, cs.fecha_cosecha_estimada
        FROM ciclos_siembra cs
        WHERE cs.id_parcela = pa.id_parcela AND cs.estado = 'en_curso'
        ORDER BY cs.fecha_siembra DESC
        LIMIT 1
    ) c ON TRUE
    LEFT JOIN cultivos cu ON cu.id_cultivo = c.id_cultivo
    WHERE pa.id_parcela = %s
"""
SQL_SENSORES = """
    SELECT id_sensor, descripcion, estatus
    FROM sensores
    WHERE id_parcela = %s
    ORDER BY id_sensor
"""


def lambda_handler(evento, contexto):
    id_parcela = leer_id(evento)
    if id_parcela is None:
        return error(400, "El id de la parcela debe ser un número entero positivo.")

    try:
        conexion = obtener_conexion()
        with conexion, conexion.cursor() as cursor:
            cursor.execute(SQL_PARCELA, [id_parcela])
            parcela = cursor.fetchone()
            sensores = []
            if parcela is not None:
                cursor.execute(SQL_SENSORES, [id_parcela])
                sensores = cursor.fetchall()
    except psycopg2.Error:
        logger.exception("Error de RDS al consultar la parcela")
        return error(500, "No se pudo consultar la parcela.")

    if parcela is None:
        return error(404, "No existe una parcela con ese id.")

    try:
        lecturas = ultimas_lecturas(obtener_tabla(), [s["id_sensor"] for s in sensores])
    except (ClientError, BotoCoreError):
        logger.exception("Error de DynamoDB al consultar las últimas lecturas")
        return error(500, "No se pudieron consultar las lecturas de los sensores.")

    rango = rango_ideal(parcela)
    estado, detalles = estado_parcela(sensores, lecturas, ahora_utc(), rango)

    return respuesta(
        200,
        {
            "parcela": {
                "id_parcela": parcela["id_parcela"],
                "id_productor": parcela["id_productor"],
                "productor": parcela["productor"],
                "nombre": parcela["nombre"],
                "ubicacion": parcela["ubicacion"],
                "superficie_ha": parcela["superficie_ha"],
                "ciclo": resumen_ciclo(parcela),
                "rango_ideal": rango,
                **estado,
            },
            "sensores": detalles,
        },
    )
