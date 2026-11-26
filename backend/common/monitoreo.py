"""Une los datos de RDS (parcelas, sensores, cultivos) con las lecturas de DynamoDB.

Lo usan las pantallas Mis parcelas y Detalle de parcela:
- Estado de cada sensor: en_linea, sin_senal o inactivo.
- Última lectura de cada sensor y promedio de la parcela.
- Alertas cuando la humedad o la temperatura salen del rango ideal del cultivo.
- Avance del ciclo de siembra ("día 34 de 127").
"""
import os
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from boto3.dynamodb.conditions import Key

from common.fechas import parsear_fecha

# Un sensor se marca "sin señal" si no manda lecturas en este tiempo (los sensores mandan cada 5 min).
MINUTOS_SIN_SENAL = int(os.environ.get("MINUTOS_SIN_SENAL", "15"))

# Morelos usa la hora del centro de México, UTC-6 todo el año (ya no hay horario de verano).
ZONA_MEXICO = timezone(timedelta(hours=-6))

EN_LINEA, SIN_SENAL, INACTIVO = "en_linea", "sin_senal", "inactivo"
OPTIMA, REQUIERE_ATENCION, SIN_DATOS = "optima", "requiere_atencion", "sin_datos"


def ultimas_lecturas(tabla, ids_sensores):
    """Regresa {id_sensor: lectura o None} con la lectura más reciente de cada sensor.

    Es una consulta por sensor con Limit=1 y orden descendente por fecha_hora,
    así que solo lee un registro de DynamoDB por sensor.
    """
    resultado = {}
    for id_sensor in ids_sensores:
        respuesta = tabla.query(
            KeyConditionExpression=Key("id_sensor").eq(id_sensor),
            ScanIndexForward=False,
            Limit=1,
        )
        elementos = respuesta.get("Items", [])
        resultado[id_sensor] = elementos[0] if elementos else None
    return resultado


def estado_sensor(estatus, lectura, ahora):
    """Regresa (estado, minutos_desde_la_ultima_lectura o None)."""
    minutos = None
    if lectura is not None:
        fecha = parsear_fecha(lectura.get("fecha_hora"))
        if fecha is not None:
            minutos = max(0, int((ahora - fecha).total_seconds() // 60))
    if estatus != "activo":
        return INACTIVO, minutos
    if minutos is None or minutos > MINUTOS_SIN_SENAL:
        return SIN_SENAL, minutos
    return EN_LINEA, minutos


def _redondear(valor):
    return Decimal(valor).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def revisar_rango(humedad, temperatura, rango):
    """Compara una lectura con el rango ideal del cultivo. Regresa una lista de alertas."""
    if not rango:
        return []
    alertas = []
    revisiones = (
        ("humedad", humedad, "humedad_min", "humedad_max",
         "Humedad por debajo del rango ideal: conviene regar.",
         "Humedad por encima del rango ideal: revisar exceso de riego o drenaje."),
        ("temperatura", temperatura, "temp_min", "temp_max",
         "Temperatura por debajo del rango ideal.",
         "Temperatura por encima del rango ideal."),
    )
    for tipo, valor, campo_min, campo_max, mensaje_bajo, mensaje_alto in revisiones:
        minimo, maximo = rango.get(campo_min), rango.get(campo_max)
        if valor is None:
            continue
        if minimo is not None and valor < minimo:
            alertas.append({"tipo": tipo, "nivel": "bajo", "mensaje": mensaje_bajo})
        elif maximo is not None and valor > maximo:
            alertas.append({"tipo": tipo, "nivel": "alto", "mensaje": mensaje_alto})
    return alertas


def rango_ideal(fila):
    """Saca el rango del cultivo de una fila con humedad_min, humedad_max, temp_min y temp_max."""
    campos = ("humedad_min", "humedad_max", "temp_min", "temp_max")
    if all(fila.get(c) is None for c in campos):
        return None
    return {c: fila.get(c) for c in campos}


def resumen_ciclo(fila, hoy=None):
    """Datos del ciclo de siembra en curso, con el avance en días. None si no hay ciclo."""
    if fila.get("id_ciclo") is None:
        return None
    hoy = hoy or datetime.now(ZONA_MEXICO).date()
    siembra, cosecha = fila["fecha_siembra"], fila.get("fecha_cosecha_estimada")
    dias_totales = (cosecha - siembra).days if cosecha else None
    dia_actual = (hoy - siembra).days + 1
    if dias_totales is not None:
        dia_actual = min(dia_actual, dias_totales)
    return {
        "id_ciclo": fila["id_ciclo"],
        "cultivo": fila.get("cultivo"),
        "fecha_siembra": siembra.isoformat(),
        "fecha_cosecha_estimada": cosecha.isoformat() if cosecha else None,
        "dia_actual": max(dia_actual, 0),
        "dias_totales": dias_totales,
    }


def detalle_sensor(sensor, lectura, ahora, rango):
    """Arma la información de un sensor para la pantalla de Detalle de parcela."""
    estado, minutos = estado_sensor(sensor["estatus"], lectura, ahora)
    ultima = None
    alertas = []
    if lectura is not None:
        ultima = {
            "fecha_hora": lectura["fecha_hora"],
            "humedad": lectura.get("humedad"),
            "temperatura": lectura.get("temperatura"),
        }
        if estado == EN_LINEA:
            alertas = revisar_rango(lectura.get("humedad"), lectura.get("temperatura"), rango)
    return {
        "id_sensor": sensor["id_sensor"],
        "descripcion": sensor.get("descripcion"),
        "estatus": sensor["estatus"],
        "estado": estado,
        "minutos_sin_datos": minutos,
        "ultima_lectura": ultima,
        "alertas": alertas,
    }


def estado_parcela(sensores, lecturas, ahora, rango):
    """Resume una parcela: conteo de sensores, promedio de la última lectura y alertas.

    El promedio solo usa los sensores en línea, para que un sensor que dejó de mandar
    datos hace horas no cambie el valor actual de la parcela.
    """
    detalles = [detalle_sensor(s, lecturas.get(s["id_sensor"]), ahora, rango) for s in sensores]
    en_linea = [d for d in detalles if d["estado"] == EN_LINEA]
    sin_senal = [d for d in detalles if d["estado"] == SIN_SENAL]

    ultima_lectura = None
    alertas = []
    if en_linea:
        humedades = [d["ultima_lectura"]["humedad"] for d in en_linea]
        temperaturas = [d["ultima_lectura"]["temperatura"] for d in en_linea]
        humedad = _redondear(sum(humedades) / len(humedades))
        temperatura = _redondear(sum(temperaturas) / len(temperaturas))
        ultima_lectura = {
            "humedad": humedad,
            "temperatura": temperatura,
            "fecha_hora": max(d["ultima_lectura"]["fecha_hora"] for d in en_linea),
        }
        alertas = revisar_rango(humedad, temperatura, rango)

    if sin_senal:
        cuantos = len(sin_senal)
        texto = "1 sensor sin señal." if cuantos == 1 else f"{cuantos} sensores sin señal."
        alertas.append({"tipo": "sensor", "nivel": "sin_senal", "mensaje": texto})

    if ultima_lectura is None:
        estado = SIN_DATOS
    elif alertas:
        estado = REQUIERE_ATENCION
    else:
        estado = OPTIMA

    return {
        "sensores": {
            "total": len(detalles),
            "en_linea": len(en_linea),
            "sin_senal": len(sin_senal),
            "inactivos": len(detalles) - len(en_linea) - len(sin_senal),
        },
        "ultima_lectura": ultima_lectura,
        "estado": estado,
        "alertas": alertas,
    }, detalles


def ahora_utc():
    return datetime.now(timezone.utc)
