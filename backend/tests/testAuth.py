import json

import pytest
from psycopg2 import OperationalError

from common.seguridad import cifrar_contrasena, crear_token, verificar_contrasena, verificar_token
from lambdas.auth import cambiarContrasena, iniciarSesion
from tests.conexionFalsa import ConexionFalsa

HASH = cifrar_contrasena("Inagri2026")


def _usuario(**cambios):
    usuario = {
        "id_usuario": 2,
        "nombre": "Juan Pérez",
        "correo": "juan@ejemplo.com",
        "hash_contrasena": HASH,
        "rol": "productor",
        "id_productor": 1,
        "debe_cambiar_contrasena": False,
        "estatus_productor": "activo",
    }
    usuario.update(cambios)
    return usuario


def _usar(monkeypatch, modulo, conexion):
    monkeypatch.setattr(modulo, "obtener_conexion", lambda: conexion)
    return conexion


def _login(correo="juan@ejemplo.com", contrasena="Inagri2026"):
    return {"body": json.dumps({"correo": correo, "contrasena": contrasena})}


# ---------- POST /auth/login ----------

def test_inicia_sesion(monkeypatch):
    conexion = _usar(monkeypatch, iniciarSesion, ConexionFalsa([_usuario()], []))
    resp = iniciarSesion.lambda_handler(_login(correo="  JUAN@ejemplo.com "), None)
    cuerpo = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert cuerpo["usuario"]["rol"] == "productor"
    assert cuerpo["usuario"]["id_productor"] == 1
    assert "hash_contrasena" not in cuerpo["usuario"]
    datos = verificar_token(cuerpo["token"])
    assert datos["sub"] == "2" and datos["rol"] == "productor" and datos["id_productor"] == 1
    assert conexion.consultas[0][1] == ["juan@ejemplo.com"]
    assert conexion.consultas[1][0].startswith("UPDATE usuarios SET ultimo_acceso")


def test_inicia_sesion_el_administrador(monkeypatch):
    admin = _usuario(id_usuario=1, rol="administrador", id_productor=None, estatus_productor=None)
    _usar(monkeypatch, iniciarSesion, ConexionFalsa([admin], []))
    resp = iniciarSesion.lambda_handler(_login(), None)
    assert resp["statusCode"] == 200
    assert verificar_token(json.loads(resp["body"])["token"])["rol"] == "administrador"


def test_avisa_si_debe_cambiar_la_contrasena(monkeypatch):
    _usar(monkeypatch, iniciarSesion, ConexionFalsa([_usuario(debe_cambiar_contrasena=True)], []))
    cuerpo = json.loads(iniciarSesion.lambda_handler(_login(), None)["body"])
    assert cuerpo["usuario"]["debe_cambiar_contrasena"] is True


def test_contrasena_incorrecta(monkeypatch):
    conexion = _usar(monkeypatch, iniciarSesion, ConexionFalsa([_usuario()]))
    resp = iniciarSesion.lambda_handler(_login(contrasena="otra1234"), None)
    assert resp["statusCode"] == 401
    assert len(conexion.consultas) == 1


def test_correo_no_registrado_responde_igual(monkeypatch):
    _usar(monkeypatch, iniciarSesion, ConexionFalsa([]))
    resp = iniciarSesion.lambda_handler(_login(correo="nadie@ejemplo.com"), None)
    assert resp["statusCode"] == 401
    assert json.loads(resp["body"])["error"] == iniciarSesion.CREDENCIALES_INCORRECTAS


def test_productor_dado_de_baja_no_entra(monkeypatch):
    _usar(monkeypatch, iniciarSesion, ConexionFalsa([_usuario(estatus_productor="inactivo")]))
    assert iniciarSesion.lambda_handler(_login(), None)["statusCode"] == 403


@pytest.mark.parametrize(
    "cuerpo",
    [{}, {"correo": "juan@ejemplo.com"}, {"contrasena": "x"}, {"correo": "no-es", "contrasena": "x"},
     {"correo": "juan@ejemplo.com", "contrasena": ""}, {"correo": "juan@ejemplo.com", "contrasena": 123}],
)
def test_login_con_datos_incompletos(monkeypatch, cuerpo):
    conexion = _usar(monkeypatch, iniciarSesion, ConexionFalsa())
    resp = iniciarSesion.lambda_handler({"body": json.dumps(cuerpo)}, None)
    assert resp["statusCode"] == 400
    assert conexion.consultas == []


def test_login_sin_base_de_datos(monkeypatch):
    def falla():
        raise OperationalError("sin conexión")

    monkeypatch.setattr(iniciarSesion, "obtener_conexion", falla)
    assert iniciarSesion.lambda_handler(_login(), None)["statusCode"] == 500


# ---------- PUT /auth/contrasena ----------

def _cambio(actual="Inagri2026", nueva="Maiz2027x", token=None):
    token = token or crear_token({"sub": "2", "rol": "productor", "id_productor": 1})
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "body": json.dumps({"contrasena_actual": actual, "contrasena_nueva": nueva}),
    }


def test_cambia_la_contrasena(monkeypatch):
    conexion = _usar(monkeypatch, cambiarContrasena, ConexionFalsa([{"hash_contrasena": HASH}], []))
    resp = cambiarContrasena.lambda_handler(_cambio(), None)

    assert resp["statusCode"] == 200
    sql, valores = conexion.consultas[1]
    assert "debe_cambiar_contrasena = FALSE" in sql
    assert verificar_contrasena("Maiz2027x", valores[0])
    assert valores[1] == 2


def test_cambiar_sin_sesion(monkeypatch):
    conexion = _usar(monkeypatch, cambiarContrasena, ConexionFalsa())
    evento = _cambio()
    evento["headers"] = {}
    assert cambiarContrasena.lambda_handler(evento, None)["statusCode"] == 401
    evento["headers"] = {"Authorization": "Bearer token.falso.x"}
    assert cambiarContrasena.lambda_handler(evento, None)["statusCode"] == 401
    assert conexion.consultas == []


def test_cambiar_con_contrasena_actual_incorrecta(monkeypatch):
    conexion = _usar(monkeypatch, cambiarContrasena, ConexionFalsa([{"hash_contrasena": HASH}]))
    resp = cambiarContrasena.lambda_handler(_cambio(actual="Otra2026"), None)
    assert resp["statusCode"] == 400
    assert len(conexion.consultas) == 1


@pytest.mark.parametrize("nueva", ["corta1", "solotexto", "Inagri2026"])
def test_rechaza_contrasena_nueva_invalida(monkeypatch, nueva):
    conexion = _usar(monkeypatch, cambiarContrasena, ConexionFalsa())
    assert cambiarContrasena.lambda_handler(_cambio(nueva=nueva), None)["statusCode"] == 400
    assert conexion.consultas == []
