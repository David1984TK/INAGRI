import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from botocore.exceptions import ClientError

from common.fechas import parsear_fecha
from lambdas.lecturas import obtenerLecturas

AHORA = datetime(2026, 11, 24, 21, 0, tzinfo=timezone.utc)


class TablaFalsa:
    """Imita la tabla de DynamoDB: cada llamada a query devuelve una página."""

    def __init__(self, paginas=None, error=None):
        self.paginas = list(paginas if paginas is not None else [[]])
        self.error = error
        self.llamadas = []

    def query(self, **argumentos):
        self.llamadas.append(argumentos)
        if self.error:
            raise self.error
        resultado = {"Items": self.paginas.pop(0)}
        if self.paginas:
            resultado["LastEvaluatedKey"] = {"id_sensor": 1}
        return resultado


def _condicion(llamada):
    """Saca (id_sensor, [desde, hasta]) de la condición que se mandó a DynamoDB."""
    igual, entre = llamada["KeyConditionExpression"].get_expression()["values"]
    return igual.get_expression()["values"][1], list(entre.get_expression()["values"][1:])


def _evento(id_sensor="1", **parametros):
    return {"pathParameters": {"id": id_sensor}, "queryStringParameters": parametros or None}


def _lectura(hora, humedad=40, **extra):
    item = {
        "id_sensor": 1,
        "fecha_hora": f"2026-11-24T{hora}:00:00Z",
        "humedad": Decimal(str(humedad)),
        "temperatura": Decimal("27"),
        "origen": "sensor",
        "expira_en": 1900000000,
    }
    item.update(extra)
    return item


def _usar(monkeypatch, tabla):
    monkeypatch.setattr(obtenerLecturas, "obtener_tabla", lambda: tabla)


def test_consulta_las_ultimas_24_horas_por_defecto(monkeypatch):
    tabla = TablaFalsa([[_lectura("20"), _lectura("19")]])
    _usar(monkeypatch, tabla)

    resp = obtenerLecturas.lambda_handler(_evento(), None)
    cuerpo = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert cuerpo["id_sensor"] == 1
    assert cuerpo["total"] == 2
    assert parsear_fecha(cuerpo["hasta"]) - parsear_fecha(cuerpo["desde"]) == timedelta(hours=24)
    id_sensor, (desde, hasta) = _condicion(tabla.llamadas[0])
    assert id_sensor == 1
    assert (desde, hasta) == (cuerpo["desde"], cuerpo["hasta"])


def test_pide_las_lecturas_mas_recientes_primero(monkeypatch):
    tabla = TablaFalsa()
    _usar(monkeypatch, tabla)
    obtenerLecturas.lambda_handler(_evento(), None)
    assert tabla.llamadas[0]["ScanIndexForward"] is False


def test_no_regresa_expira_en_y_convierte_los_numeros(monkeypatch):
    _usar(monkeypatch, TablaFalsa([[_lectura("20", humedad="28.5", id_parcela=3)]]))
    resp = obtenerLecturas.lambda_handler(_evento(), None)
    lectura = json.loads(resp["body"])["lecturas"][0]
    assert "expira_en" not in lectura
    assert lectura["humedad"] == 28.5
    assert lectura["temperatura"] == 27
    assert lectura["id_parcela"] == 3


def test_sin_lecturas_regresa_lista_vacia(monkeypatch):
    _usar(monkeypatch, TablaFalsa([[]]))
    resp = obtenerLecturas.lambda_handler(_evento(), None)
    cuerpo = json.loads(resp["body"])
    assert resp["statusCode"] == 200
    assert cuerpo["total"] == 0
    assert cuerpo["lecturas"] == []


def test_junta_todas_las_paginas_de_dynamodb(monkeypatch):
    tabla = TablaFalsa([[_lectura("20")], [_lectura("19")], [_lectura("18")]])
    _usar(monkeypatch, tabla)
    resp = obtenerLecturas.lambda_handler(_evento(), None)
    assert json.loads(resp["body"])["total"] == 3
    assert len(tabla.llamadas) == 3
    assert "ExclusiveStartKey" in tabla.llamadas[1]


def test_acepta_horas_y_rango_en_la_misma_consulta_con_desde_hasta(monkeypatch):
    tabla = TablaFalsa()
    _usar(monkeypatch, tabla)
    evento = _evento(desde="2026-11-01T00:00:00Z", hasta="2026-11-02T00:00:00Z", horas="5")
    resp = obtenerLecturas.lambda_handler(evento, None)
    assert resp["statusCode"] == 200
    _, (desde, hasta) = _condicion(tabla.llamadas[0])
    assert (desde, hasta) == ("2026-11-01T00:00:00Z", "2026-11-02T00:00:00Z")


@pytest.mark.parametrize(
    "parametros",
    [
        {"horas": "0"},
        {"horas": "169"},
        {"horas": "mucho"},
        {"horas": "2.5"},
        {"desde": "ayer"},
        {"desde": "2026-11-01T00:00:00Z", "hasta": "mañana"},
        {"desde": "2026-11-02T00:00:00Z", "hasta": "2026-11-01T00:00:00Z"},
        {"desde": "2026-01-01T00:00:00Z", "hasta": "2026-11-01T00:00:00Z"},
        {"hasta": "2026-11-01T00:00:00Z"},
    ],
)
def test_rechaza_parametros_invalidos(monkeypatch, parametros):
    tabla = TablaFalsa()
    _usar(monkeypatch, tabla)
    resp = obtenerLecturas.lambda_handler(_evento(**parametros), None)
    assert resp["statusCode"] == 400
    assert tabla.llamadas == []


@pytest.mark.parametrize("id_sensor", ["abc", "0", "-3", "1.5", ""])
def test_rechaza_un_id_de_sensor_invalido(monkeypatch, id_sensor):
    _usar(monkeypatch, TablaFalsa())
    resp = obtenerLecturas.lambda_handler(_evento(id_sensor), None)
    assert resp["statusCode"] == 400


def test_sin_id_en_la_ruta(monkeypatch):
    _usar(monkeypatch, TablaFalsa())
    resp = obtenerLecturas.lambda_handler({}, None)
    assert resp["statusCode"] == 400


def test_calcular_rango_con_horas():
    desde, hasta, problema = obtenerLecturas.calcular_rango({"horas": "6"}, AHORA)
    assert problema is None
    assert hasta == AHORA
    assert desde == AHORA - timedelta(hours=6)


def test_calcular_rango_solo_con_desde_usa_ahora_como_hasta():
    desde, hasta, problema = obtenerLecturas.calcular_rango({"desde": "2026-11-20T00:00:00Z"}, AHORA)
    assert problema is None
    assert hasta == AHORA


def test_error_de_dynamodb_regresa_500(monkeypatch):
    fallo = ClientError({"Error": {"Code": "InternalServerError", "Message": "x"}}, "Query")
    _usar(monkeypatch, TablaFalsa(error=fallo))
    resp = obtenerLecturas.lambda_handler(_evento(), None)
    assert resp["statusCode"] == 500
