import json
from decimal import Decimal

import pytest
from botocore.exceptions import ClientError

from lambdas.lecturas import actualizarLectura

FECHA = "2026-11-24T18:30:00Z"


class TablaFalsa:
    """Imita update_item de DynamoDB sin conectarse a AWS."""

    def __init__(self, error=None):
        self.error = error
        self.llamadas = []

    def update_item(self, **argumentos):
        self.llamadas.append(argumentos)
        if self.error:
            raise self.error
        valores = {c.lstrip(":"): v for c, v in argumentos["ExpressionAttributeValues"].items()}
        atributos = {
            **argumentos["Key"],
            "humedad": Decimal("40"),
            "temperatura": Decimal("27"),
            "origen": "sensor",
            "expira_en": 1900000000,
            **valores,
        }
        return {"Attributes": atributos}


def _evento(cuerpo, id_sensor="1", fecha=FECHA):
    return {
        "pathParameters": {"id": id_sensor, "fechaHora": fecha},
        "body": json.dumps(cuerpo),
    }


@pytest.fixture
def tabla(monkeypatch):
    falsa = TablaFalsa()
    monkeypatch.setattr(actualizarLectura, "obtener_tabla", lambda: falsa)
    return falsa


def test_actualiza_solo_la_humedad(tabla):
    resp = actualizarLectura.lambda_handler(_evento({"humedad": 55.5}), None)
    cuerpo = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert cuerpo["lectura"]["humedad"] == 55.5
    assert cuerpo["lectura"]["temperatura"] == 27
    assert "expira_en" not in cuerpo["lectura"]
    llamada = tabla.llamadas[0]
    assert llamada["Key"] == {"id_sensor": 1, "fecha_hora": FECHA}
    assert llamada["UpdateExpression"] == "SET humedad = :humedad"
    assert llamada["ExpressionAttributeValues"] == {":humedad": Decimal("55.5")}


def test_actualiza_humedad_y_temperatura(tabla):
    resp = actualizarLectura.lambda_handler(_evento({"humedad": 30, "temperatura": 21}), None)
    assert resp["statusCode"] == 200
    expresion = tabla.llamadas[0]["UpdateExpression"]
    assert "humedad = :humedad" in expresion and "temperatura = :temperatura" in expresion


def test_exige_que_la_lectura_exista(tabla):
    actualizarLectura.lambda_handler(_evento({"humedad": 30}), None)
    assert tabla.llamadas[0]["ConditionExpression"] == "attribute_exists(id_sensor)"


def test_acepta_la_fecha_codificada_en_la_url(tabla):
    resp = actualizarLectura.lambda_handler(
        _evento({"humedad": 30}, fecha="2026-11-24T18%3A30%3A00Z"), None
    )
    assert resp["statusCode"] == 200
    assert tabla.llamadas[0]["Key"]["fecha_hora"] == FECHA


def test_normaliza_la_fecha_de_la_ruta_a_utc(tabla):
    actualizarLectura.lambda_handler(_evento({"humedad": 30}, fecha="2026-11-24T12:30:00-06:00"), None)
    assert tabla.llamadas[0]["Key"]["fecha_hora"] == FECHA


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"humedad": 101},
        {"humedad": "mucha"},
        {"temperatura": 90},
        {"temperatura": None},
        {"humedad": 30, "origen": "manual"},
        {"id_sensor": 2},
        {"fecha_hora": "2026-01-01T00:00:00Z"},
    ],
)
def test_rechaza_cuerpos_invalidos(tabla, cuerpo):
    resp = actualizarLectura.lambda_handler(_evento(cuerpo), None)
    assert resp["statusCode"] == 400
    assert tabla.llamadas == []


@pytest.mark.parametrize("id_sensor", ["abc", "0", "-1", ""])
def test_rechaza_un_id_invalido(tabla, id_sensor):
    resp = actualizarLectura.lambda_handler(_evento({"humedad": 30}, id_sensor=id_sensor), None)
    assert resp["statusCode"] == 400


@pytest.mark.parametrize("fecha", ["ayer", "", "2026-13-45"])
def test_rechaza_una_fecha_invalida(tabla, fecha):
    resp = actualizarLectura.lambda_handler(_evento({"humedad": 30}, fecha=fecha), None)
    assert resp["statusCode"] == 400


@pytest.mark.parametrize("evento", [{"pathParameters": {"id": "1", "fechaHora": FECHA}}, {}])
def test_sin_cuerpo_o_sin_ruta(tabla, evento):
    resp = actualizarLectura.lambda_handler(evento, None)
    assert resp["statusCode"] == 400


def test_cuerpo_que_no_es_json(tabla):
    evento = {"pathParameters": {"id": "1", "fechaHora": FECHA}, "body": "no es json"}
    assert actualizarLectura.lambda_handler(evento, None)["statusCode"] == 400


def test_lectura_inexistente_regresa_404(monkeypatch):
    no_existe = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "x"}}, "UpdateItem"
    )
    monkeypatch.setattr(actualizarLectura, "obtener_tabla", lambda: TablaFalsa(no_existe))
    resp = actualizarLectura.lambda_handler(_evento({"humedad": 30}), None)
    assert resp["statusCode"] == 404


def test_error_de_dynamodb_regresa_500(monkeypatch):
    fallo = ClientError({"Error": {"Code": "InternalServerError", "Message": "x"}}, "UpdateItem")
    monkeypatch.setattr(actualizarLectura, "obtener_tabla", lambda: TablaFalsa(fallo))
    resp = actualizarLectura.lambda_handler(_evento({"humedad": 30}), None)
    assert resp["statusCode"] == 500
