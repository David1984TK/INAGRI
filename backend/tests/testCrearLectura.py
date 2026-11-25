import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from botocore.exceptions import ClientError

from lambdas.lecturas import crearLectura


class TablaFalsa:
    """Imita la tabla de DynamoDB sin conectarse a AWS."""

    def __init__(self, error=None):
        self.items = []
        self.error = error

    def put_item(self, Item, ConditionExpression=None):
        if self.error:
            raise self.error
        self.items.append(Item)


def _evento(cuerpo):
    return {"body": json.dumps(cuerpo)}


def _cuerpo_valido(**cambios):
    cuerpo = {"id_sensor": 1, "humedad": 42.5, "temperatura": 27}
    cuerpo.update(cambios)
    return cuerpo


@pytest.fixture
def tabla(monkeypatch):
    falsa = TablaFalsa()
    monkeypatch.setattr(crearLectura, "obtener_tabla", lambda: falsa)
    return falsa


def test_guarda_una_lectura_valida(tabla):
    resp = crearLectura.lambda_handler(_evento(_cuerpo_valido()), None)

    assert resp["statusCode"] == 201
    assert len(tabla.items) == 1
    item = tabla.items[0]
    assert item["id_sensor"] == 1
    assert item["humedad"] == Decimal("42.5")
    assert item["temperatura"] == Decimal("27")
    assert item["origen"] == "sensor"
    assert isinstance(item["expira_en"], int)


def test_sin_fecha_usa_la_hora_actual(tabla):
    antes = datetime.now(timezone.utc).replace(microsecond=0)
    crearLectura.lambda_handler(_evento(_cuerpo_valido()), None)
    guardada = datetime.strptime(tabla.items[0]["fecha_hora"], "%Y-%m-%dT%H:%M:%SZ")
    assert abs(guardada.replace(tzinfo=timezone.utc) - antes) < timedelta(seconds=5)


def test_normaliza_la_fecha_a_utc(tabla):
    cuerpo = _cuerpo_valido(fecha_hora="2026-11-09T16:00:00-06:00")
    crearLectura.lambda_handler(_evento(cuerpo), None)
    assert tabla.items[0]["fecha_hora"] == "2026-11-09T22:00:00Z"


def test_expira_en_suma_los_dias_de_retencion(tabla):
    cuerpo = _cuerpo_valido(fecha_hora="2026-11-09T22:00:00Z")
    crearLectura.lambda_handler(_evento(cuerpo), None)
    esperado = datetime(2026, 11, 9, 22, 0, tzinfo=timezone.utc) + timedelta(
        days=crearLectura.DIAS_RETENCION
    )
    assert tabla.items[0]["expira_en"] == int(esperado.timestamp())


def test_guarda_los_campos_opcionales(tabla):
    cuerpo = _cuerpo_valido(origen="manual", registrado_por=" jperez ", id_parcela=3)
    crearLectura.lambda_handler(_evento(cuerpo), None)
    item = tabla.items[0]
    assert item["origen"] == "manual"
    assert item["registrado_por"] == "jperez"
    assert item["id_parcela"] == 3


@pytest.mark.parametrize("campo", ["id_sensor", "humedad", "temperatura"])
def test_falta_un_campo_obligatorio(tabla, campo):
    cuerpo = _cuerpo_valido()
    del cuerpo[campo]
    resp = crearLectura.lambda_handler(_evento(cuerpo), None)
    assert resp["statusCode"] == 400
    assert campo in json.loads(resp["body"])["error"]
    assert tabla.items == []


@pytest.mark.parametrize(
    "cambios",
    [
        {"humedad": 101},
        {"humedad": -1},
        {"humedad": "mucha"},
        {"temperatura": 90},
        {"temperatura": None},
        {"id_sensor": 0},
        {"id_sensor": "1"},
        {"id_sensor": True},
        {"origen": "satelite"},
        {"fecha_hora": "ayer"},
        {"fecha_hora": "2999-01-01T00:00:00Z"},
        {"id_parcela": -5},
        {"registrado_por": ""},
    ],
)
def test_rechaza_datos_invalidos(tabla, cambios):
    resp = crearLectura.lambda_handler(_evento(_cuerpo_valido(**cambios)), None)
    assert resp["statusCode"] == 400
    assert tabla.items == []


@pytest.mark.parametrize("evento", [{}, {"body": "esto no es json"}, {"body": "[1, 2]"}])
def test_cuerpo_invalido(tabla, evento):
    resp = crearLectura.lambda_handler(evento, None)
    assert resp["statusCode"] == 400


def test_lectura_duplicada_regresa_409(monkeypatch):
    duplicado = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "duplicada"}},
        "PutItem",
    )
    monkeypatch.setattr(crearLectura, "obtener_tabla", lambda: TablaFalsa(duplicado))
    resp = crearLectura.lambda_handler(_evento(_cuerpo_valido()), None)
    assert resp["statusCode"] == 409


def test_error_de_dynamodb_regresa_500(monkeypatch):
    fallo = ClientError({"Error": {"Code": "InternalServerError", "Message": "x"}}, "PutItem")
    monkeypatch.setattr(crearLectura, "obtener_tabla", lambda: TablaFalsa(fallo))
    resp = crearLectura.lambda_handler(_evento(_cuerpo_valido()), None)
    assert resp["statusCode"] == 500
