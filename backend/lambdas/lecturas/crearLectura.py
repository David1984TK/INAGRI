"""POST /lecturas: registra una lectura de humedad y temperatura en DynamoDB.

Tabla: llave de partición id_sensor (número), llave de ordenamiento fecha_hora
(texto ISO 8601 en UTC). expira_en es el atributo de TTL (segundos epoch).
"""
import logging
import os
from datetime import datetime, timedelta, timezone

from botocore.exceptions import ClientError

from common.dynamo import obtener_tabla
from common.fechas import formatear_fecha, parsear_fecha
from common.respuestas import error, respuesta
from common.validaciones import (
    entero_positivo,
    leer_cuerpo,
    validar_humedad,
    validar_temperatura,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DIAS_RETENCION = int(os.environ.get("DIAS_RETENCION_LECTURAS", "90"))
ORIGENES = ("sensor", "manual")
TOLERANCIA_FUTURO = timedelta(minutes=5)


def validar(datos, ahora=None):
    """Regresa (item, None) si todo está bien, o (None, mensaje) si hay un error."""
    ahora = ahora or datetime.now(timezone.utc)

    for campo in ("id_sensor", "humedad", "temperatura"):
        if campo not in datos:
            return None, f"Falta el campo obligatorio: {campo}."

    if not entero_positivo(datos["id_sensor"]):
        return None, "id_sensor debe ser un número entero positivo."

    humedad, problema = validar_humedad(datos["humedad"])
    if problema:
        return None, problema

    temperatura, problema = validar_temperatura(datos["temperatura"])
    if problema:
        return None, problema

    if datos.get("fecha_hora") is None:
        fecha = ahora
    else:
        fecha = parsear_fecha(datos["fecha_hora"])
        if fecha is None:
            return None, "fecha_hora debe tener formato ISO 8601, por ejemplo 2026-11-24T18:30:00Z."
        if fecha > ahora + TOLERANCIA_FUTURO:
            return None, "fecha_hora no puede estar en el futuro."

    origen = datos.get("origen", "sensor")
    if origen not in ORIGENES:
        return None, "origen debe ser 'sensor' o 'manual'."

    registrado_por = datos.get("registrado_por")
    if registrado_por is not None and (
        not isinstance(registrado_por, str) or not 0 < len(registrado_por.strip()) <= 50
    ):
        return None, "registrado_por debe ser un texto de máximo 50 caracteres."

    id_parcela = datos.get("id_parcela")
    if id_parcela is not None and not entero_positivo(id_parcela):
        return None, "id_parcela debe ser un número entero positivo."

    item = {
        "id_sensor": datos["id_sensor"],
        "fecha_hora": formatear_fecha(fecha),
        "humedad": humedad,
        "temperatura": temperatura,
        "origen": origen,
        "expira_en": int((fecha + timedelta(days=DIAS_RETENCION)).timestamp()),
    }
    if registrado_por is not None:
        item["registrado_por"] = registrado_por.strip()
    if id_parcela is not None:
        item["id_parcela"] = id_parcela
    return item, None


def lambda_handler(evento, contexto):
    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    item, problema = validar(datos)
    if problema:
        return error(400, problema)

    try:
        obtener_tabla().put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(id_sensor)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error(409, "Ya existe una lectura de ese sensor con esa fecha y hora.")
        logger.exception("Error de DynamoDB al guardar la lectura")
        return error(500, "No se pudo guardar la lectura.")

    return respuesta(201, {"mensaje": "Lectura registrada", "lectura": item})
