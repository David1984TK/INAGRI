"""Respuestas HTTP con el formato que espera API Gateway (integración proxy)."""
import json
from decimal import Decimal

ENCABEZADOS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}


def _convertir(valor):
    # DynamoDB devuelve los números como Decimal y json no sabe serializarlos.
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    raise TypeError(f"No se puede serializar {type(valor).__name__}")


def respuesta(codigo, cuerpo):
    return {
        "statusCode": codigo,
        "headers": ENCABEZADOS,
        "body": json.dumps(cuerpo, default=_convertir, ensure_ascii=False),
    }


def error(codigo, mensaje):
    return respuesta(codigo, {"error": mensaje})
