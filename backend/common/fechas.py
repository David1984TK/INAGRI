"""Manejo de fechas: siempre ISO 8601 en UTC, por ejemplo 2026-11-24T18:30:00Z."""
from datetime import datetime, timezone

FORMATO = "%Y-%m-%dT%H:%M:%SZ"


def parsear_fecha(texto):
    """Devuelve un datetime en UTC, o None si el texto no es una fecha ISO 8601."""
    if not isinstance(texto, str):
        return None
    try:
        fecha = datetime.fromisoformat(texto.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def formatear_fecha(fecha):
    return fecha.astimezone(timezone.utc).strftime(FORMATO)
