import json
from datetime import datetime, timezone

import pytest
from psycopg2 import OperationalError, errors

from lambdas.catalogo import (
    actualizarProductor,
    crearProductor,
    eliminarProductor,
    obtenerProductores,
)
from tests.conexionFalsa import ConexionFalsa

FECHA = datetime(2026, 11, 24, 18, 30, tzinfo=timezone.utc)
PRODUCTOR = {
    "id_productor": 1,
    "nombre": "Juan Pérez",
    "telefono": "7771234501",
    "correo": "juan@ejemplo.com",
    "estatus": "activo",
    "fecha_alta": FECHA,
}


def _usar(monkeypatch, modulo, conexion):
    monkeypatch.setattr(modulo, "obtener_conexion", lambda: conexion)
    return conexion


def _evento(cuerpo=None, id_productor=None, consulta=None):
    evento = {}
    if cuerpo is not None:
        evento["body"] = json.dumps(cuerpo)
    if id_productor is not None:
        evento["pathParameters"] = {"id": id_productor}
    if consulta is not None:
        evento["queryStringParameters"] = consulta
    return evento


# ---------- POST /productores ----------

def test_crea_un_productor(monkeypatch):
    conexion = _usar(monkeypatch, crearProductor, ConexionFalsa([PRODUCTOR]))
    resp = crearProductor.lambda_handler(
        _evento({"nombre": "  Juan Pérez ", "correo": "JUAN@ejemplo.com", "telefono": "7771234501"}), None
    )
    cuerpo = json.loads(resp["body"])

    assert resp["statusCode"] == 201
    assert cuerpo["productor"]["fecha_alta"] == "2026-11-24T18:30:00Z"
    sql, valores = conexion.consultas[0]
    assert sql.startswith("INSERT INTO productores (nombre, telefono, correo)")
    assert valores == ["Juan Pérez", "7771234501", "juan@ejemplo.com"]
    assert conexion.confirmada


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"nombre": ""},
        {"nombre": None},
        {"nombre": "x" * 101},
        {"nombre": "Juan", "correo": "no-es-correo"},
        {"nombre": "Juan", "telefono": "12"},
        {"nombre": "Juan", "estatus": "baja"},
        {"nombre": "Juan", "id_productor": 9},
    ],
)
def test_rechaza_productores_invalidos(monkeypatch, cuerpo):
    conexion = _usar(monkeypatch, crearProductor, ConexionFalsa())
    resp = crearProductor.lambda_handler(_evento(cuerpo), None)
    assert resp["statusCode"] == 400
    assert conexion.consultas == []


def test_sin_cuerpo_regresa_400(monkeypatch):
    _usar(monkeypatch, crearProductor, ConexionFalsa())
    assert crearProductor.lambda_handler({}, None)["statusCode"] == 400


def test_correo_repetido_regresa_409(monkeypatch):
    _usar(monkeypatch, crearProductor, ConexionFalsa(error=errors.UniqueViolation("duplicado")))
    resp = crearProductor.lambda_handler(_evento({"nombre": "Juan", "correo": "a@b.com"}), None)
    assert resp["statusCode"] == 409


def test_error_de_conexion_regresa_500(monkeypatch):
    def falla():
        raise OperationalError("sin conexión")

    monkeypatch.setattr(crearProductor, "obtener_conexion", falla)
    resp = crearProductor.lambda_handler(_evento({"nombre": "Juan"}), None)
    assert resp["statusCode"] == 500


# ---------- GET /productores y /productores/{id} ----------

def test_lista_productores(monkeypatch):
    fila = {**PRODUCTOR, "total_parcelas": 2}
    conexion = _usar(monkeypatch, obtenerProductores, ConexionFalsa([fila, {**fila, "id_productor": 2}]))
    resp = obtenerProductores.lambda_handler(_evento(), None)
    cuerpo = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert cuerpo["total"] == 2
    assert conexion.consultas[0][1] == []


def test_filtra_por_estatus(monkeypatch):
    conexion = _usar(monkeypatch, obtenerProductores, ConexionFalsa([]))
    resp = obtenerProductores.lambda_handler(_evento(consulta={"estatus": "inactivo"}), None)
    assert resp["statusCode"] == 200
    sql, valores = conexion.consultas[0]
    assert "WHERE pr.estatus = %s" in sql and valores == ["inactivo"]


def test_estatus_invalido_regresa_400(monkeypatch):
    _usar(monkeypatch, obtenerProductores, ConexionFalsa())
    resp = obtenerProductores.lambda_handler(_evento(consulta={"estatus": "x"}), None)
    assert resp["statusCode"] == 400


def test_obtiene_un_productor(monkeypatch):
    _usar(monkeypatch, obtenerProductores, ConexionFalsa([{**PRODUCTOR, "total_parcelas": 2}]))
    resp = obtenerProductores.lambda_handler(_evento(id_productor="1"), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["productor"]["total_parcelas"] == 2


def test_productor_inexistente_regresa_404(monkeypatch):
    _usar(monkeypatch, obtenerProductores, ConexionFalsa([]))
    assert obtenerProductores.lambda_handler(_evento(id_productor="99"), None)["statusCode"] == 404


@pytest.mark.parametrize("id_productor", ["abc", "0", "-1", ""])
def test_id_invalido_regresa_400(monkeypatch, id_productor):
    _usar(monkeypatch, obtenerProductores, ConexionFalsa())
    resp = obtenerProductores.lambda_handler(_evento(id_productor=id_productor), None)
    assert resp["statusCode"] == 400


# ---------- PUT /productores/{id} ----------

def test_actualiza_el_estatus(monkeypatch):
    conexion = _usar(monkeypatch, actualizarProductor, ConexionFalsa([{**PRODUCTOR, "estatus": "inactivo"}]))
    resp = actualizarProductor.lambda_handler(_evento({"estatus": "inactivo"}, id_productor="1"), None)

    assert resp["statusCode"] == 200
    sql, valores = conexion.consultas[0]
    assert sql.startswith("UPDATE productores SET estatus = %s WHERE id_productor = %s")
    assert valores == ["inactivo", 1]


def test_permite_borrar_el_telefono(monkeypatch):
    conexion = _usar(monkeypatch, actualizarProductor, ConexionFalsa([PRODUCTOR]))
    resp = actualizarProductor.lambda_handler(_evento({"telefono": None}, id_productor="1"), None)
    assert resp["statusCode"] == 200
    assert conexion.consultas[0][1] == [None, 1]


@pytest.mark.parametrize("cuerpo", [{}, {"nombre": None}, {"estatus": "baja"}, {"fecha_alta": "hoy"}])
def test_actualizar_rechaza_cuerpos_invalidos(monkeypatch, cuerpo):
    conexion = _usar(monkeypatch, actualizarProductor, ConexionFalsa())
    resp = actualizarProductor.lambda_handler(_evento(cuerpo, id_productor="1"), None)
    assert resp["statusCode"] == 400
    assert conexion.consultas == []


def test_actualizar_inexistente_regresa_404(monkeypatch):
    _usar(monkeypatch, actualizarProductor, ConexionFalsa([]))
    resp = actualizarProductor.lambda_handler(_evento({"nombre": "Ana"}, id_productor="99"), None)
    assert resp["statusCode"] == 404


def test_actualizar_correo_repetido_regresa_409(monkeypatch):
    _usar(monkeypatch, actualizarProductor, ConexionFalsa(error=errors.UniqueViolation("dup")))
    resp = actualizarProductor.lambda_handler(_evento({"correo": "a@b.com"}, id_productor="1"), None)
    assert resp["statusCode"] == 409


# ---------- DELETE /productores/{id} ----------

def test_elimina_un_productor(monkeypatch):
    conexion = _usar(monkeypatch, eliminarProductor, ConexionFalsa([{"id_productor": 5}]))
    resp = eliminarProductor.lambda_handler(_evento(id_productor="5"), None)
    assert resp["statusCode"] == 200
    assert conexion.consultas[0][1] == [5]


def test_eliminar_inexistente_regresa_404(monkeypatch):
    _usar(monkeypatch, eliminarProductor, ConexionFalsa([]))
    assert eliminarProductor.lambda_handler(_evento(id_productor="99"), None)["statusCode"] == 404


def test_no_elimina_un_productor_con_parcelas(monkeypatch):
    conexion = _usar(monkeypatch, eliminarProductor, ConexionFalsa(error=errors.ForeignKeyViolation("fk")))
    resp = eliminarProductor.lambda_handler(_evento(id_productor="1"), None)
    assert resp["statusCode"] == 409
    assert conexion.revertida
