"""Pruebas de las pantallas Mis parcelas y Detalle de parcela (RDS + DynamoDB)."""
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from botocore.exceptions import ClientError
from psycopg2 import OperationalError

from common.fechas import formatear_fecha
from lambdas.catalogo import obtenerParcelasProductor, obtenerSensoresParcela
from tests.conexionFalsa import ConexionFalsa
from tests.tablaLecturasFalsa import TablaLecturasFalsa

AHORA = datetime(2026, 11, 26, 18, 0, tzinfo=timezone.utc)
RANGO_FRIJOL = {"humedad_min": Decimal("40"), "humedad_max": Decimal("65"),
                "temp_min": Decimal("15"), "temp_max": Decimal("28")}
RANGO_MAIZ = {"humedad_min": Decimal("35"), "humedad_max": Decimal("60"),
              "temp_min": Decimal("18"), "temp_max": Decimal("32")}
SIN_CICLO = {"id_ciclo": None, "fecha_siembra": None, "fecha_cosecha_estimada": None, "cultivo": None,
             "humedad_min": None, "humedad_max": None, "temp_min": None, "temp_max": None}


def _lectura(minutos_atras, humedad, temperatura):
    return {
        "fecha_hora": formatear_fecha(AHORA - timedelta(minutes=minutos_atras)),
        "humedad": Decimal(str(humedad)),
        "temperatura": Decimal(str(temperatura)),
    }


def _preparar(monkeypatch, modulo, conexion, tabla):
    monkeypatch.setattr(modulo, "obtener_conexion", lambda: conexion)
    monkeypatch.setattr(modulo, "obtener_tabla", lambda: tabla)
    monkeypatch.setattr(modulo, "ahora_utc", lambda: AHORA)
    return conexion


def _evento(id_ruta):
    return {"pathParameters": {"id": id_ruta}}


# ---------- GET /productores/{id}/parcelas (Mis parcelas) ----------

PRODUCTOR = {"id_productor": 1, "nombre": "Juan Pérez", "comunidad": "Ayala", "estatus": "activo"}
PARCELAS = [
    {"id_parcela": 1, "nombre": "Parcela Sur", "ubicacion": "Ayala", "superficie_ha": Decimal("3.50"),
     "id_ciclo": 2, "fecha_siembra": date(2026, 11, 5), "fecha_cosecha_estimada": date(2027, 2, 3),
     "cultivo": "Frijol", **RANGO_FRIJOL},
    {"id_parcela": 3, "nombre": "Parcela Norte", "ubicacion": "Cuautla", "superficie_ha": Decimal("4.75"),
     "id_ciclo": 4, "fecha_siembra": date(2026, 9, 10), "fecha_cosecha_estimada": date(2027, 1, 8),
     "cultivo": "Maíz", **RANGO_MAIZ},
    {"id_parcela": 4, "nombre": "Parcela El Llano", "ubicacion": None, "superficie_ha": Decimal("1.80"),
     **SIN_CICLO},
]
SENSORES = [
    {"id_sensor": 1, "id_parcela": 1, "descripcion": "Noreste", "estatus": "activo"},
    {"id_sensor": 2, "id_parcela": 1, "descripcion": "Noroeste", "estatus": "activo"},
    {"id_sensor": 4, "id_parcela": 1, "descripcion": "Sur", "estatus": "activo"},
    {"id_sensor": 7, "id_parcela": 3, "descripcion": "Entrada", "estatus": "activo"},
    {"id_sensor": 8, "id_parcela": 3, "descripcion": "Centro", "estatus": "activo"},
]
LECTURAS = {
    1: [_lectura(3, 30, 22), _lectura(63, 33, 21)],
    2: [_lectura(4, 32, 23)],
    4: [_lectura(200, 31, 20)],
    7: [_lectura(2, 42, 24)],
    8: [_lectura(1, 44, 26)],
}


def test_mis_parcelas_junta_rds_y_dynamodb(monkeypatch):
    conexion = ConexionFalsa([PRODUCTOR], PARCELAS, SENSORES)
    tabla = TablaLecturasFalsa(LECTURAS)
    _preparar(monkeypatch, obtenerParcelasProductor, conexion, tabla)

    resp = obtenerParcelasProductor.lambda_handler(_evento("1"), None)
    cuerpo = json.loads(resp["body"])
    assert resp["statusCode"] == 200

    assert cuerpo["resumen"] == {"parcelas": 3, "sensores_total": 5, "sensores_en_linea": 4,
                                 "parcelas_con_alerta": 1}
    sur, norte, llano = cuerpo["parcelas"]

    assert sur["estado"] == "requiere_atencion"
    assert sur["sensores"] == {"total": 3, "en_linea": 2, "sin_senal": 1, "inactivos": 0}
    assert sur["ultima_lectura"]["humedad"] == 31.0
    assert sur["ciclo"]["cultivo"] == "Frijol" and sur["ciclo"]["dias_totales"] == 90
    assert sur["rango_ideal"]["humedad_min"] == 40
    assert sur["alertas"][0]["mensaje"].endswith("conviene regar.")

    assert norte["estado"] == "optima" and norte["ultima_lectura"]["temperatura"] == 25.0
    assert llano["estado"] == "sin_datos" and llano["ciclo"] is None and llano["sensores"]["total"] == 0

    # Una consulta a DynamoDB por sensor, solo la más reciente.
    assert sorted(c["id_sensor"] for c in tabla.consultas) == [1, 2, 4, 7, 8]
    assert conexion.consultas[1][1] == [1] and conexion.consultas[2][1] == [1]


def test_mis_parcelas_productor_inexistente(monkeypatch):
    tabla = TablaLecturasFalsa()
    conexion = _preparar(monkeypatch, obtenerParcelasProductor, ConexionFalsa([]), tabla)
    assert obtenerParcelasProductor.lambda_handler(_evento("99"), None)["statusCode"] == 404
    assert len(conexion.consultas) == 1 and tabla.consultas == []


def test_mis_parcelas_productor_sin_parcelas(monkeypatch):
    _preparar(monkeypatch, obtenerParcelasProductor, ConexionFalsa([PRODUCTOR], [], []), TablaLecturasFalsa())
    cuerpo = json.loads(obtenerParcelasProductor.lambda_handler(_evento("1"), None)["body"])
    assert cuerpo["parcelas"] == [] and cuerpo["resumen"]["parcelas"] == 0


def test_mis_parcelas_id_invalido(monkeypatch):
    _preparar(monkeypatch, obtenerParcelasProductor, ConexionFalsa(), TablaLecturasFalsa())
    assert obtenerParcelasProductor.lambda_handler(_evento("x"), None)["statusCode"] == 400


def test_mis_parcelas_falla_dynamodb(monkeypatch):
    error = ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "x"}}, "Query")
    _preparar(monkeypatch, obtenerParcelasProductor, ConexionFalsa([PRODUCTOR], PARCELAS, SENSORES),
              TablaLecturasFalsa(error=error))
    assert obtenerParcelasProductor.lambda_handler(_evento("1"), None)["statusCode"] == 500


def test_mis_parcelas_falla_rds(monkeypatch):
    def falla():
        raise OperationalError("sin conexión")

    monkeypatch.setattr(obtenerParcelasProductor, "obtener_conexion", falla)
    assert obtenerParcelasProductor.lambda_handler(_evento("1"), None)["statusCode"] == 500


# ---------- GET /parcelas/{id}/sensores (Detalle de parcela) ----------

PARCELA_SUR = {"id_productor": 1, "productor": "Juan Pérez", **PARCELAS[0]}
SENSORES_SUR = [{k: v for k, v in s.items() if k != "id_parcela"} for s in SENSORES[:3]]


def test_detalle_de_parcela(monkeypatch):
    conexion = ConexionFalsa([PARCELA_SUR], SENSORES_SUR)
    _preparar(monkeypatch, obtenerSensoresParcela, conexion, TablaLecturasFalsa(LECTURAS))

    resp = obtenerSensoresParcela.lambda_handler(_evento("1"), None)
    cuerpo = json.loads(resp["body"])
    assert resp["statusCode"] == 200

    parcela = cuerpo["parcela"]
    assert parcela["productor"] == "Juan Pérez"
    assert parcela["estado"] == "requiere_atencion"
    assert parcela["sensores"]["en_linea"] == 2

    s1, s2, s4 = cuerpo["sensores"]
    assert s1["estado"] == "en_linea" and s1["minutos_sin_datos"] == 3
    assert s1["ultima_lectura"]["humedad"] == 30.0
    assert s1["alertas"][0]["tipo"] == "humedad"
    assert s4["estado"] == "sin_senal" and s4["minutos_sin_datos"] == 200
    assert s4["ultima_lectura"]["humedad"] == 31.0 and s4["alertas"] == []
    assert conexion.consultas[1][1] == [1]


def test_detalle_de_sensor_que_nunca_ha_mandado_datos(monkeypatch):
    sensores = [{"id_sensor": 11, "descripcion": "Nuevo", "estatus": "activo"}]
    _preparar(monkeypatch, obtenerSensoresParcela, ConexionFalsa([PARCELA_SUR], sensores), TablaLecturasFalsa())
    cuerpo = json.loads(obtenerSensoresParcela.lambda_handler(_evento("1"), None)["body"])
    sensor = cuerpo["sensores"][0]
    assert sensor["estado"] == "sin_senal" and sensor["ultima_lectura"] is None
    assert sensor["minutos_sin_datos"] is None
    assert cuerpo["parcela"]["estado"] == "sin_datos"


def test_detalle_parcela_inexistente(monkeypatch):
    tabla = TablaLecturasFalsa()
    _preparar(monkeypatch, obtenerSensoresParcela, ConexionFalsa([]), tabla)
    assert obtenerSensoresParcela.lambda_handler(_evento("99"), None)["statusCode"] == 404
    assert tabla.consultas == []


def test_detalle_id_invalido(monkeypatch):
    _preparar(monkeypatch, obtenerSensoresParcela, ConexionFalsa(), TablaLecturasFalsa())
    assert obtenerSensoresParcela.lambda_handler(_evento("0"), None)["statusCode"] == 400
