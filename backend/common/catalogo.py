"""Validaciones y utilidades compartidas por las Lambdas del catálogo (RDS)."""
import re
from datetime import date, datetime
from decimal import Decimal

from common.fechas import formatear_fecha
from common.validaciones import a_decimal, entero_positivo

ESTATUS = ("activo", "inactivo")
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_TELEFONO = re.compile(r"^[0-9+\- ]{7,20}$")
SUPERFICIE_MAX = Decimal("10000")


def leer_id(evento, nombre="id"):
    """Saca un id numérico de la ruta. Regresa el entero o None si no es válido."""
    valor = str((evento.get("pathParameters") or {}).get(nombre, ""))
    if valor.isdigit() and int(valor) > 0:
        return int(valor)
    return None


def fila_publica(fila):
    """Convierte las fechas a texto ISO 8601 para poder mandarlas en JSON."""
    resultado = {}
    for campo, valor in dict(fila).items():
        if isinstance(valor, datetime):
            valor = formatear_fecha(valor)
        elif isinstance(valor, date):
            valor = valor.isoformat()
        resultado[campo] = valor
    return resultado


# Cada validador regresa (valor_limpio, None) o (None, mensaje).

def validar_texto(campo, maximo):
    def validador(valor):
        if not isinstance(valor, str) or not 0 < len(valor.strip()) <= maximo:
            return None, f"{campo} debe ser un texto de 1 a {maximo} caracteres."
        return valor.strip(), None

    return validador


def validar_opcional(validador):
    """Permite mandar null para dejar el campo vacío."""

    def envoltura(valor):
        if valor is None:
            return None, None
        return validador(valor)

    return envoltura


def validar_telefono(valor):
    if not isinstance(valor, str) or not PATRON_TELEFONO.match(valor.strip()):
        return None, "telefono debe tener de 7 a 20 caracteres (números, espacios, + o -)."
    return valor.strip(), None


def validar_correo(valor):
    if not isinstance(valor, str) or len(valor) > 100 or not PATRON_CORREO.match(valor.strip()):
        return None, "correo no tiene un formato válido."
    return valor.strip().lower(), None


def validar_estatus(valor):
    if valor not in ESTATUS:
        return None, "estatus debe ser 'activo' o 'inactivo'."
    return valor, None


def validar_id_productor(valor):
    if not entero_positivo(valor):
        return None, "id_productor debe ser un número entero positivo."
    return valor, None


def validar_superficie(valor):
    numero = a_decimal(valor)
    if numero is None or not Decimal("0") < numero <= SUPERFICIE_MAX:
        return None, f"superficie_ha debe ser un número mayor a 0 y hasta {SUPERFICIE_MAX}."
    return numero.quantize(Decimal("0.01")), None


def validar_campos(datos, campos, obligatorios, parcial):
    """Valida un cuerpo contra un diccionario {campo: validador}.

    parcial=False (POST): exige los obligatorios.
    parcial=True  (PUT):  basta con mandar al menos un campo.
    Regresa (valores, None) o (None, mensaje).
    """
    no_permitidos = sorted(set(datos) - set(campos))
    if no_permitidos:
        return None, "Campos no permitidos: " + ", ".join(no_permitidos) + "."

    if not parcial:
        for campo in obligatorios:
            if datos.get(campo) is None:
                return None, f"Falta el campo obligatorio: {campo}."

    valores = {}
    for campo, validador in campos.items():
        if campo in datos:
            if campo in obligatorios and datos[campo] is None:
                return None, f"{campo} no puede quedar vacío."
            valor, problema = validador(datos[campo])
            if problema:
                return None, problema
            valores[campo] = valor

    if parcial and not valores:
        return None, "Manda al menos uno de estos campos: " + ", ".join(campos) + "."
    return valores, None


CAMPOS_PRODUCTOR = {
    "nombre": validar_texto("nombre", 100),
    "telefono": validar_opcional(validar_telefono),
    "correo": validar_opcional(validar_correo),
    "estatus": validar_estatus,
}
OBLIGATORIOS_PRODUCTOR = ("nombre",)

CAMPOS_PARCELA = {
    "id_productor": validar_id_productor,
    "nombre": validar_texto("nombre", 100),
    "ubicacion": validar_opcional(validar_texto("ubicacion", 150)),
    "superficie_ha": validar_superficie,
}
OBLIGATORIOS_PARCELA = ("id_productor", "nombre", "superficie_ha")


def validar_productor(datos, parcial=False):
    return validar_campos(datos, CAMPOS_PRODUCTOR, OBLIGATORIOS_PRODUCTOR, parcial)


def validar_parcela(datos, parcial=False):
    return validar_campos(datos, CAMPOS_PARCELA, OBLIGATORIOS_PARCELA, parcial)
