import json

import pytest
from botocore.exceptions import ClientError

from lambdas.lecturas import eliminarLectura

FECHA = "2026-11-24T18:30:00Z"


class TablaFalsa:
    """Imita delete_item de DynamoDB sin conectarse a AWS."""

    def __init__(self, error=None):
        self.error = error
        self.llamadas = []

    def delete_item(self, **argumentos):
        self.llamadas.append(argumentos)
        if self.error:
            raise self.error
        return {}


def _evento(id_sensor="1", fecha=FECHA):
    return {"pathParameters": {"id": id_sensor, "fechaHora": fecha}}


@pytest.fixture
def tabla(monkeypatch):
    falsa = TablaFalsa()
    monkeypatch.setattr(eliminarLectura, "obtener_tabla", lambda: falsa)
    return falsa


def test_elimina_una_lectura(tabla):
    resp = eliminarLectura.lambda_handler(_evento(), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["mensaje"] == "Lectura eliminada"
    llamada = tabla.llamadas[0]
    assert llamada["Key"] == {"id_sensor": 1, "fecha_hora": FECHA}
    assert llamada["ConditionExpression"] == "attribute_exists(id_sensor)"


def test_acepta_la_fecha_codificada_en_la_url(tabla):
    resp = eliminarLectura.lambda_handler(_evento(fecha="2026-11-24T18%3A30%3A00Z"), None)
    assert resp["statusCode"] == 200
    assert tabla.llamadas[0]["Key"]["fecha_hora"] == FECHA


@pytest.mark.parametrize("id_sensor", ["abc", "0", "-1", "1.5", ""])
def test_rechaza_un_id_invalido(tabla, id_sensor):
    assert eliminarLectura.lambda_handler(_evento(id_sensor=id_sensor), None)["statusCode"] == 400
    assert tabla.llamadas == []


@pytest.mark.parametrize("fecha", ["ayer", "", "2026-13-45"])
def test_rechaza_una_fecha_invalida(tabla, fecha):
    assert eliminarLectura.lambda_handler(_evento(fecha=fecha), None)["statusCode"] == 400
    assert tabla.llamadas == []


def test_sin_ruta(tabla):
    assert eliminarLectura.lambda_handler({}, None)["statusCode"] == 400


def test_lectura_inexistente_regresa_404(monkeypatch):
    no_existe = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "x"}}, "DeleteItem"
    )
    monkeypatch.setattr(eliminarLectura, "obtener_tabla", lambda: TablaFalsa(no_existe))
    assert eliminarLectura.lambda_handler(_evento(), None)["statusCode"] == 404


def test_error_de_dynamodb_regresa_500(monkeypatch):
    fallo = ClientError({"Error": {"Code": "InternalServerError", "Message": "x"}}, "DeleteItem")
    monkeypatch.setattr(eliminarLectura, "obtener_tabla", lambda: TablaFalsa(fallo))
    assert eliminarLectura.lambda_handler(_evento(), None)["statusCode"] == 500
