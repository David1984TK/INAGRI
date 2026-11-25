"""Validaciones compartidas por las Lambdas de lecturas."""
import base64
import json
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote

from common.fechas import formatear_fecha, parsear_fecha

HUMEDAD_MIN, HUMEDAD_MAX = Decimal("0"), Decimal("100")
TEMPERATURA_MIN, TEMPERATURA_MAX = Decimal("-40"), Decimal("85")


def leer_cuerpo(evento):
    """Devuelve el JSON del cuerpo como diccionario. Lanza ValueError si viene mal."""
    cuerpo = evento.get("body")
    if cuerpo is None:
        raise ValueError("Falta el cuerpo de la petición.")
    if evento.get("isBase64Encoded"):
        cuerpo = base64.b64decode(cuerpo).decode("utf-8")
    try:
        datos = json.loads(cuerpo)
    except (TypeError, ValueError):
        raise ValueError("El cuerpo debe ser un JSON válido.")
    if not isinstance(datos, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON.")
    return datos


def entero_positivo(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def a_decimal(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        return None


def validar_humedad(valor):
    """Regresa (Decimal, None) o (None, mensaje)."""
    numero = a_decimal(valor)
    if numero is None or not HUMEDAD_MIN <= numero <= HUMEDAD_MAX:
        return None, "humedad debe ser un número entre 0 y 100."
    return numero, None


def validar_temperatura(valor):
    """Regresa (Decimal, None) o (None, mensaje)."""
    numero = a_decimal(valor)
    if numero is None or not TEMPERATURA_MIN <= numero <= TEMPERATURA_MAX:
        return None, "temperatura debe ser un número entre -40 y 85."
    return numero, None


def leer_llave_lectura(evento):
    """Saca id_sensor y fecha_hora de la ruta /sensores/{id}/lecturas/{fechaHora}.

    Regresa (id_sensor, fecha_hora, None) o (None, None, mensaje).
    """
    parametros = evento.get("pathParameters") or {}

    id_texto = str(parametros.get("id", ""))
    if not (id_texto.isdigit() and int(id_texto) > 0):
        return None, None, "El id del sensor debe ser un número entero positivo."

    fecha = parsear_fecha(unquote(str(parametros.get("fechaHora", ""))))
    if fecha is None:
        return None, None, "fechaHora debe tener formato ISO 8601, por ejemplo 2026-11-24T18:30:00Z."

    return int(id_texto), formatear_fecha(fecha), None
