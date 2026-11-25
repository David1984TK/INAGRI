"""GET /sensores/{id}/lecturas: consulta las lecturas de un sensor en un rango.

Parámetros opcionales (query string):
  horas        últimas N horas, de 1 a 168. Por defecto 24.
  desde, hasta rango en ISO 8601 (para el botón "Rango"). Si se manda desde, se
               ignora horas. Si no se manda hasta, se usa la hora actual.

Es un solo Query a DynamoDB: llave de partición id_sensor y rango sobre fecha_hora.
"""
import logging
from datetime import datetime, timedelta, timezone

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from common.dynamo import obtener_tabla
from common.fechas import formatear_fecha, parsear_fecha
from common.lecturas import lectura_publica
from common.respuestas import error, respuesta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

HORAS_POR_DEFECTO = 24
HORAS_MAXIMAS = 168
DIAS_MAXIMOS_RANGO = 31


def _leer_id_sensor(evento):
    valor = str((evento.get("pathParameters") or {}).get("id", ""))
    if valor.isdigit() and int(valor) > 0:
        return int(valor)
    return None


def calcular_rango(parametros, ahora):
    """Regresa (desde, hasta, None) o (None, None, mensaje) si hay un error."""
    if parametros.get("desde") is not None:
        desde = parsear_fecha(parametros["desde"])
        if desde is None:
            return None, None, "desde debe tener formato ISO 8601, por ejemplo 2026-11-01T00:00:00Z."
        hasta = ahora
        if parametros.get("hasta") is not None:
            hasta = parsear_fecha(parametros["hasta"])
            if hasta is None:
                return None, None, "hasta debe tener formato ISO 8601, por ejemplo 2026-11-02T00:00:00Z."
        if desde >= hasta:
            return None, None, "desde debe ser anterior a hasta."
        if hasta - desde > timedelta(days=DIAS_MAXIMOS_RANGO):
            return None, None, f"El rango no puede ser mayor a {DIAS_MAXIMOS_RANGO} días."
        return desde, hasta, None

    if parametros.get("hasta") is not None:
        return None, None, "Si mandas hasta, también tienes que mandar desde."

    horas = parametros.get("horas", HORAS_POR_DEFECTO)
    try:
        horas = int(horas)
    except (TypeError, ValueError):
        return None, None, "horas debe ser un número entero."
    if not 1 <= horas <= HORAS_MAXIMAS:
        return None, None, f"horas debe estar entre 1 y {HORAS_MAXIMAS}."
    return ahora - timedelta(hours=horas), ahora, None


def _consultar(tabla, id_sensor, desde, hasta):
    argumentos = {
        "KeyConditionExpression": Key("id_sensor").eq(id_sensor)
        & Key("fecha_hora").between(desde, hasta),
        "ScanIndexForward": False,  # más reciente primero
    }
    items = []
    while True:
        resultado = tabla.query(**argumentos)
        items.extend(resultado.get("Items", []))
        ultima = resultado.get("LastEvaluatedKey")
        if not ultima:
            return items
        argumentos["ExclusiveStartKey"] = ultima


def lambda_handler(evento, contexto):
    id_sensor = _leer_id_sensor(evento)
    if id_sensor is None:
        return error(400, "El id del sensor debe ser un número entero positivo.")

    ahora = datetime.now(timezone.utc)
    desde, hasta, problema = calcular_rango(evento.get("queryStringParameters") or {}, ahora)
    if problema:
        return error(400, problema)

    desde_texto, hasta_texto = formatear_fecha(desde), formatear_fecha(hasta)
    try:
        items = _consultar(obtener_tabla(), id_sensor, desde_texto, hasta_texto)
    except ClientError:
        logger.exception("Error de DynamoDB al consultar las lecturas")
        return error(500, "No se pudieron consultar las lecturas.")

    lecturas = [lectura_publica(item) for item in items]
    return respuesta(
        200,
        {
            "id_sensor": id_sensor,
            "desde": desde_texto,
            "hasta": hasta_texto,
            "total": len(lecturas),
            "lecturas": lecturas,
        },
    )
