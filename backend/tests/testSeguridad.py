import pytest

from common import seguridad


# ---------- Contraseñas ----------

def test_cifra_y_verifica_una_contrasena():
    hash_guardado = seguridad.cifrar_contrasena("Inagri2026")
    assert hash_guardado.startswith("scrypt$")
    assert "Inagri2026" not in hash_guardado
    assert seguridad.verificar_contrasena("Inagri2026", hash_guardado)
    assert not seguridad.verificar_contrasena("inagri2026", hash_guardado)


def test_la_misma_contrasena_da_hash_distinto():
    assert seguridad.cifrar_contrasena("Inagri2026") != seguridad.cifrar_contrasena("Inagri2026")


@pytest.mark.parametrize("hash_guardado", ["", "texto", None, "md5$a$b$c$d$e", "scrypt$x$8$1$aa$bb"])
def test_hash_invalido_no_deja_pasar(hash_guardado):
    assert not seguridad.verificar_contrasena("Inagri2026", hash_guardado)


def test_hash_de_los_datos_de_demostracion():
    # Mismo hash que está en sql/03_datos_demo.sql para admin@inagri.com
    guardado = "scrypt$16384$8$1$DCD9czl/+srapQslJY+bLA==$5gxUR0QMJbYEsrM7q0TskFCjV2G7mBFED0kZQPNLBhU="
    assert seguridad.verificar_contrasena("Inagri2026", guardado)


@pytest.mark.parametrize("contrasena", ["corta1", "sinnumeros", "12345678", None, "a1" * 40])
def test_rechaza_contrasenas_debiles(contrasena):
    assert seguridad.validar_contrasena_nueva(contrasena) is not None


def test_acepta_una_contrasena_valida():
    assert seguridad.validar_contrasena_nueva("Maiz2026") is None


def test_contrasena_temporal_es_valida_y_aleatoria():
    temporales = {seguridad.generar_contrasena_temporal() for _ in range(20)}
    assert len(temporales) == 20
    for temporal in temporales:
        assert len(temporal) == 10
        assert seguridad.validar_contrasena_nueva(temporal) is None
        assert not set(temporal) & set("lI1O0o")


# ---------- Tokens ----------

def test_crea_y_verifica_un_token():
    token = seguridad.crear_token({"sub": "7", "rol": "productor", "id_productor": 2})
    datos = seguridad.verificar_token(token)
    assert datos["sub"] == "7" and datos["rol"] == "productor" and datos["id_productor"] == 2
    assert datos["exp"] - datos["iat"] == 8 * 3600


def test_token_caducado():
    token = seguridad.crear_token({"sub": "7"}, ahora=1_000_000)
    assert seguridad.verificar_token(token, ahora=1_000_000 + 8 * 3600 + 1) is None


def test_token_alterado():
    token = seguridad.crear_token({"sub": "7", "rol": "productor"})
    encabezado, cuerpo, firma = token.split(".")
    falso = seguridad.crear_token({"sub": "7", "rol": "administrador"}).split(".")[1]
    assert seguridad.verificar_token(f"{encabezado}.{falso}.{firma}") is None


def test_token_firmado_con_otra_llave(monkeypatch):
    token = seguridad.crear_token({"sub": "7"})
    monkeypatch.setattr(seguridad, "_llave_token", b"otra-llave-distinta-de-32-caracteres-o-mas")
    assert seguridad.verificar_token(token) is None


@pytest.mark.parametrize("token", [None, "", "abc", "a.b", "a.b.c", "....", 123])
def test_tokens_mal_formados(token):
    assert seguridad.verificar_token(token) is None


def test_llave_demasiado_corta(monkeypatch):
    monkeypatch.setenv("TOKEN_SECRET", "corta")
    with pytest.raises(RuntimeError):
        seguridad.crear_token({"sub": "1"})


def test_lee_el_token_del_encabezado():
    token = seguridad.crear_token({"sub": "3"})
    assert seguridad.leer_token({"headers": {"Authorization": f"Bearer {token}"}})["sub"] == "3"
    assert seguridad.leer_token({"headers": {"authorization": f"bearer {token}"}})["sub"] == "3"
    assert seguridad.leer_token({"headers": {"Authorization": token}}) is None
    assert seguridad.leer_token({}) is None
