import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from psycopg2 import errors

from lambdas.catalogo import (
    actualizarParcela,
    crearParcela,
    eliminarParcela,
    obtenerParcelas,
)
from tests.conexionFalsa import ConexionFalsa

FECHA = datetime(2026, 11, 24, 18, 30, tzinfo=timezone.utc)
PARCELA = {
    "id_parcela": 1,
    "id_productor": 1,
    "nombre": "Parcela Sur",
    "ubicacion": "Ayala, Morelos",
    "superficie_ha": Decimal("3.50"),
    "fecha_alta": FECHA,
}


def _usar(monkeypatch, modulo, conexion):
    monkeypatch.setattr(modulo, "obtener_conexion", lambda: conexion)
    return conexion


def _evento(cuerpo=None, id_ruta=None):
    evento = {}
    if cuerpo is not None:
        evento["body"] = json.dumps(cuerpo)
    if id_ruta is not None:
        evento["pathParameters"] = {"id": id_ruta}
    return evento


# ---------- POST /parcelas ----------

def test_crea_una_parcela(monkeypatch):
    conexion = _usar(monkeypatch, crearParcela, ConexionFalsa([PARCELA]))
    resp = crearParcela.lambda_handler(
        _evento({"id_productor": 1, "nombre": "Parcela Sur", "superficie_ha": 3.5}), None
    )
    cuerpo = json.loads(resp["body"])

    assert resp["statusCode"] == 201
    assert cuerpo["parcela"]["superficie_ha"] == 3.5
    assert conexion.consultas[0][1] == [1, "Parcela Sur", Decimal("3.50")]


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"nombre": "Sur", "superficie_ha": 2},
        {"id_productor": 1, "superficie_ha": 2},
        {"id_productor": 1, "nombre": "Sur"},
        {"id_productor": "1", "nombre": "Sur", "superficie_ha": 2},
        {"id_productor": 1, "nombre": "Sur", "superficie_ha": 0},
        {"id_productor": 1, "nombre": "Sur", "superficie_ha": -3},
        {"id_productor": 1, "nombre": "Sur", "superficie_ha": "mucha"},
        {"id_productor": 1, "nombre": "Sur", "superficie_ha": 2, "ubicacion": ""},
    ],
)
def test_rechaza_parcelas_invalidas(monkeypatch, cuerpo):
    conexion = _usar(monkeypatch, crearParcela, ConexionFalsa())
    assert crearParcela.lambda_handler(_evento(cuerpo), None)["statusCode"] == 400
    assert conexion.consultas == []


def test_productor_inexistente_regresa_404(monkeypatch):
    _usar(monkeypatch, crearParcela, ConexionFalsa(error=errors.ForeignKeyViolation("fk")))
    resp = crearParcela.lambda_handler(
        _evento({"id_productor": 99, "nombre": "Sur", "superficie_ha": 2}), None
    )
    assert resp["statusCode"] == 404


# ---------- GET /parcelas y /parcelas/{id} ----------

def test_lista_parcelas(monkeypatch):
    fila = {**PARCELA, "productor": "Juan Pérez", "total_sensores": 4}
    _usar(monkeypatch, obtenerParcelas, ConexionFalsa([fila]))
    resp = obtenerParcelas.lambda_handler(_evento(), None)
    cuerpo = json.loads(resp["body"])
    assert resp["statusCode"] == 200
    assert cuerpo["total"] == 1 and cuerpo["parcelas"][0]["total_sensores"] == 4


def test_obtiene_una_parcela_con_sus_sensores(monkeypatch):
    fila = {**PARCELA, "productor": "Juan Pérez", "total_sensores": 2}
    sensores = [
        {"id_sensor": 1, "descripcion": "Centro", "estatus": "activo"},
        {"id_sensor": 2, "descripcion": "Norte", "estatus": "activo"},
    ]
    conexion = _usar(monkeypatch, obtenerParcelas, ConexionFalsa([fila], sensores))
    resp = obtenerParcelas.lambda_handler(_evento(id_ruta="1"), None)
    cuerpo = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert [s["id_sensor"] for s in cuerpo["parcela"]["sensores"]] == [1, 2]
    assert len(conexion.consultas) == 2


def test_parcela_inexistente_regresa_404(monkeypatch):
    conexion = _usar(monkeypatch, obtenerParcelas, ConexionFalsa([]))
    assert obtenerParcelas.lambda_handler(_evento(id_ruta="99"), None)["statusCode"] == 404
    assert len(conexion.consultas) == 1


def test_id_de_parcela_invalido_regresa_400(monkeypatch):
    _usar(monkeypatch, obtenerParcelas, ConexionFalsa())
    assert obtenerParcelas.lambda_handler(_evento(id_ruta="x"), None)["statusCode"] == 400


# ---------- PUT /parcelas/{id} ----------

def test_actualiza_la_superficie(monkeypatch):
    conexion = _usar(monkeypatch, actualizarParcela, ConexionFalsa([{**PARCELA, "superficie_ha": Decimal("4.00")}]))
    resp = actualizarParcela.lambda_handler(_evento({"superficie_ha": 4}, id_ruta="1"), None)
    assert resp["statusCode"] == 200
    sql, valores = conexion.consultas[0]
    assert sql.startswith("UPDATE parcelas SET superficie_ha = %s WHERE id_parcela = %s")
    assert valores == [Decimal("4.00"), 1]


def test_actualizar_parcela_inexistente_regresa_404(monkeypatch):
    _usar(monkeypatch, actualizarParcela, ConexionFalsa([]))
    resp = actualizarParcela.lambda_handler(_evento({"nombre": "Nueva"}, id_ruta="99"), None)
    assert resp["statusCode"] == 404


def test_reasignar_a_productor_inexistente_regresa_404(monkeypatch):
    _usar(monkeypatch, actualizarParcela, ConexionFalsa(error=errors.ForeignKeyViolation("fk")))
    resp = actualizarParcela.lambda_handler(_evento({"id_productor": 99}, id_ruta="1"), None)
    assert resp["statusCode"] == 404


@pytest.mark.parametrize("cuerpo", [{}, {"superficie_ha": None}, {"id_parcela": 3}])
def test_actualizar_parcela_rechaza_cuerpos_invalidos(monkeypatch, cuerpo):
    _usar(monkeypatch, actualizarParcela, ConexionFalsa())
    assert actualizarParcela.lambda_handler(_evento(cuerpo, id_ruta="1"), None)["statusCode"] == 400


# ---------- DELETE /parcelas/{id} ----------

def test_elimina_una_parcela(monkeypatch):
    _usar(monkeypatch, eliminarParcela, ConexionFalsa([{"id_parcela": 9}]))
    assert eliminarParcela.lambda_handler(_evento(id_ruta="9"), None)["statusCode"] == 200


def test_eliminar_parcela_inexistente_regresa_404(monkeypatch):
    _usar(monkeypatch, eliminarParcela, ConexionFalsa([]))
    assert eliminarParcela.lambda_handler(_evento(id_ruta="99"), None)["statusCode"] == 404


def test_no_elimina_una_parcela_con_sensores(monkeypatch):
    _usar(monkeypatch, eliminarParcela, ConexionFalsa(error=errors.ForeignKeyViolation("fk")))
    assert eliminarParcela.lambda_handler(_evento(id_ruta="1"), None)["statusCode"] == 409
