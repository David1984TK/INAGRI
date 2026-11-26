"""GET /productores/{id}/parcelas: pantalla Mis parcelas.

Es una de las operaciones mínimas del tema 5. Junta datos de las dos bases:
- RDS: el productor, sus parcelas, el ciclo de siembra en curso, el cultivo con su
  rango ideal y los sensores de cada parcela.
- DynamoDB: la última lectura de cada sensor.

Por cada parcela regresa el cultivo y el avance del ciclo, los sensores en línea,
el promedio de la última lectura y si "Requiere atención" (alertas). Arriba va un
resumen con el total de parcelas, sensores en línea y parcelas con alerta.
404 si el productor no existe.
"""
import logging

import psycopg2
from botocore.exceptions import BotoCoreError, ClientError

from common.catalogo import fila_publica, leer_id
from common.dynamo import obtener_tabla
from common.monitoreo import (
    REQUIERE_ATENCION,
    ahora_utc,
    estado_parcela,
    rango_ideal,
    resumen_ciclo,
    ultimas_lecturas,
)
from common.rds import obtener_conexion
from common.respuestas import error, respuesta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQL_PRODUCTOR = (
    "SELECT id_productor, nombre, comunidad, estatus FROM productores WHERE id_productor = %s"
)
# LATERAL: por cada parcela trae solo su ciclo en curso más reciente.
SQL_PARCELAS = """
    SELECT pa.id_parcela, pa.nombre, pa.ubicacion, pa.superficie_ha,
           c.id_ciclo, c.fecha_siembra, c.fecha_cosecha_estimada,
           cu.nombre AS cultivo, cu.humedad_min, cu.humedad_max, cu.temp_min, cu.temp_max
    FROM parcelas pa
    LEFT JOIN LATERAL (
        SELECT cs.id_ciclo, cs.id_cultivo, cs.fecha_siembra, cs.fecha_cosecha_estimada
        FROM ciclos_siembra cs
        WHERE cs.id_parcela = pa.id_parcela AND cs.estado = 'en_curso'
        ORDER BY cs.fecha_siembra DESC
        LIMIT 1
    ) c ON TRUE
    LEFT JOIN cultivos cu ON cu.id_cultivo = c.id_cultivo
    WHERE pa.id_productor = %s
    ORDER BY pa.id_parcela
"""
SQL_SENSORES = """
    SELECT s.id_sensor, s.id_parcela, s.descripcion, s.estatus
    FROM sensores s
    JOIN parcelas pa ON pa.id_parcela = s.id_parcela
    WHERE pa.id_productor = %s
    ORDER BY s.id_sensor
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
            parcelas, sensores = [], []
            if productor is not None:
                cursor.execute(SQL_PARCELAS, [id_productor])
                parcelas = cursor.fetchall()
                cursor.execute(SQL_SENSORES, [id_productor])
                sensores = cursor.fetchall()
    except psycopg2.Error:
        logger.exception("Error de RDS al consultar las parcelas del productor")
        return error(500, "No se pudieron consultar las parcelas.")

    if productor is None:
        return error(404, "No existe un productor con ese id.")

    try:
        lecturas = ultimas_lecturas(obtener_tabla(), [s["id_sensor"] for s in sensores])
    except (ClientError, BotoCoreError):
        logger.exception("Error de DynamoDB al consultar las últimas lecturas")
        return error(500, "No se pudieron consultar las lecturas de los sensores.")

    ahora = ahora_utc()
    lista = []
    for fila in parcelas:
        rango = rango_ideal(fila)
        sensores_parcela = [s for s in sensores if s["id_parcela"] == fila["id_parcela"]]
        estado, _ = estado_parcela(sensores_parcela, lecturas, ahora, rango)
        lista.append(
            {
                "id_parcela": fila["id_parcela"],
                "nombre": fila["nombre"],
                "ubicacion": fila["ubicacion"],
                "superficie_ha": fila["superficie_ha"],
                "ciclo": resumen_ciclo(fila),
                "rango_ideal": rango,
                **estado,
            }
        )

    resumen = {
        "parcelas": len(lista),
        "sensores_total": sum(p["sensores"]["total"] for p in lista),
        "sensores_en_linea": sum(p["sensores"]["en_linea"] for p in lista),
        "parcelas_con_alerta": sum(1 for p in lista if p["estado"] == REQUIERE_ATENCION),
    }
    return respuesta(
        200,
        {"productor": fila_publica(productor), "resumen": resumen, "total": len(lista), "parcelas": lista},
    )
