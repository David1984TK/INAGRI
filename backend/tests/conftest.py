import pytest

from common import seguridad


@pytest.fixture(autouse=True)
def llave_de_tokens(monkeypatch):
    """Todas las pruebas usan una llave de prueba para los tokens (nunca la real)."""
    monkeypatch.setenv("TOKEN_SECRET", "llave-de-prueba-solo-para-pytest-0123456789")
    monkeypatch.delenv("TOKEN_SECRET_NAME", raising=False)
    monkeypatch.setattr(seguridad, "_llave_token", None)
