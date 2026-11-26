from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from common import monitoreo
from common.fechas import formatear_fecha
from tests.tablaLecturasFalsa import TablaLecturasFalsa

AHORA = datetime(2026, 11, 26, 18, 0, tzinfo=timezone.utc)
RANGO_FRIJOL = {
    "humedad_min": Decimal("40"),
    "humedad_max": Decimal("65"),
    "temp_min": Decimal("15"),
    "temp_max": Decimal("28"),
}


def _lectura(minutos_atras, humedad, temperatura):
    return {
        "fecha_hora": formatear_fecha(AHORA - timedelta(minutes=minutos_atras)),
        "humedad": Decimal(str(humedad)),
        "temperatura": Decimal(str(temperatura)),
    }


def _sensor(id_sensor, estatus="activo"):
    return {"id_sensor": id_sensor, "descripcion": f"Sensor {id_sensor}", "estatus": estatus}


# ---------- Últimas lecturas ----------

def test_trae_solo_la_lectura_mas_reciente_de_cada_sensor():
    tabla = TablaLecturasFalsa(
        {1: [_lectura(30, 40, 20), _lectura(5, 41, 21), _lectura(60, 39, 19)], 2: []}
    )
    resultado = monitoreo.ultimas_lecturas(tabla, [1, 2])
    assert resultado[1]["humedad"] == Decimal("41")
    assert resultado[2] is None
    assert all(c["descendente"] and c["limite"] == 1 for c in tabla.consultas)


# ---------- Estado del sensor ----------

@pytest.mark.parametrize(
    "estatus, lectura, esperado",
    [
        ("activo", _lectura(5, 40, 20), ("en_linea", 5)),
        ("activo", _lectura(15, 40, 20), ("en_linea", 15)),
        ("activo", _lectura(16, 40, 20), ("sin_senal", 16)),
        ("activo", None, ("sin_senal", None)),
        ("inactivo", _lectura(5, 40, 20), ("inactivo", 5)),
    ],
)
def test_estado_del_sensor(estatus, lectura, esperado):
    assert monitoreo.estado_sensor(estatus, lectura, AHORA) == esperado


# ---------- Rango ideal ----------

def test_lectura_en_rango_no_tiene_alertas():
    assert monitoreo.revisar_rango(Decimal("50"), Decimal("22"), RANGO_FRIJOL) == []


def test_humedad_baja_pide_regar():
    alertas = monitoreo.revisar_rango(Decimal("30"), Decimal("22"), RANGO_FRIJOL)
    assert alertas == [
        {"tipo": "humedad", "nivel": "bajo", "mensaje": "Humedad por debajo del rango ideal: conviene regar."}
    ]


def test_humedad_y_temperatura_altas():
    alertas = monitoreo.revisar_rango(Decimal("70"), Decimal("31"), RANGO_FRIJOL)
    assert [(a["tipo"], a["nivel"]) for a in alertas] == [("humedad", "alto"), ("temperatura", "alto")]


def test_sin_rango_no_hay_alertas():
    assert monitoreo.revisar_rango(Decimal("5"), Decimal("50"), None) == []


def test_rango_ideal_de_una_fila():
    assert monitoreo.rango_ideal({**RANGO_FRIJOL, "otro": 1}) == RANGO_FRIJOL
    assert monitoreo.rango_ideal({"humedad_min": None}) is None


# ---------- Ciclo de siembra ----------

def test_avance_del_ciclo():
    fila = {
        "id_ciclo": 4,
        "cultivo": "Maíz",
        "fecha_siembra": date(2026, 9, 10),
        "fecha_cosecha_estimada": date(2027, 1, 8),
    }
    ciclo = monitoreo.resumen_ciclo(fila, hoy=date(2026, 10, 13))
    assert ciclo["dia_actual"] == 34
    assert ciclo["dias_totales"] == 120
    assert ciclo["fecha_siembra"] == "2026-09-10"


def test_ciclo_terminado_no_pasa_del_total():
    fila = {"id_ciclo": 1, "cultivo": "Maíz", "fecha_siembra": date(2026, 1, 1),
            "fecha_cosecha_estimada": date(2026, 1, 31)}
    assert monitoreo.resumen_ciclo(fila, hoy=date(2026, 6, 1))["dia_actual"] == 30


def test_parcela_sin_ciclo():
    assert monitoreo.resumen_ciclo({"id_ciclo": None}) is None


# ---------- Estado de la parcela ----------

def test_parcela_seca_con_un_sensor_sin_senal():
    """Como la Parcela Sur del boceto: 3 de 4 en línea y humedad baja."""
    sensores = [_sensor(1), _sensor(2), _sensor(3), _sensor(4)]
    lecturas = {
        1: _lectura(3, 30, 22),
        2: _lectura(4, 32, 23),
        3: _lectura(2, 31, 22),
        4: _lectura(180, 80, 10),  # vieja: no debe contar para el promedio
    }
    estado, detalles = monitoreo.estado_parcela(sensores, lecturas, AHORA, RANGO_FRIJOL)

    assert estado["sensores"] == {"total": 4, "en_linea": 3, "sin_senal": 1, "inactivos": 0}
    assert estado["ultima_lectura"]["humedad"] == Decimal("31.0")
    assert estado["ultima_lectura"]["temperatura"] == Decimal("22.3")
    assert estado["ultima_lectura"]["fecha_hora"] == lecturas[3]["fecha_hora"]
    assert estado["estado"] == "requiere_atencion"
    assert [a["tipo"] for a in estado["alertas"]] == ["humedad", "sensor"]
    assert estado["alertas"][1]["mensaje"] == "1 sensor sin señal."
    assert detalles[3]["estado"] == "sin_senal" and detalles[3]["alertas"] == []
    assert detalles[0]["alertas"][0]["tipo"] == "humedad"


def test_parcela_en_rango():
    sensores = [_sensor(7), _sensor(8)]
    lecturas = {7: _lectura(2, 42, 24), 8: _lectura(3, 44, 25)}
    estado, _ = monitoreo.estado_parcela(sensores, lecturas, AHORA, RANGO_FRIJOL)
    assert estado["estado"] == "optima"
    assert estado["alertas"] == []


def test_parcela_sin_lecturas_recientes():
    estado, _ = monitoreo.estado_parcela([_sensor(1), _sensor(2)], {}, AHORA, RANGO_FRIJOL)
    assert estado["estado"] == "sin_datos"
    assert estado["ultima_lectura"] is None
    assert estado["alertas"][0]["mensaje"] == "2 sensores sin señal."


def test_parcela_sin_sensores():
    estado, detalles = monitoreo.estado_parcela([], {}, AHORA, None)
    assert estado["estado"] == "sin_datos" and estado["alertas"] == [] and detalles == []


def test_sensor_inactivo_no_cuenta_como_sin_senal():
    sensores = [_sensor(1), _sensor(2, estatus="inactivo")]
    estado, _ = monitoreo.estado_parcela(sensores, {1: _lectura(1, 50, 20)}, AHORA, RANGO_FRIJOL)
    assert estado["sensores"] == {"total": 2, "en_linea": 1, "sin_senal": 0, "inactivos": 1}
    assert estado["estado"] == "optima"
