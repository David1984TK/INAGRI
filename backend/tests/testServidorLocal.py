import pytest

from scripts import servidorLocal


@pytest.mark.parametrize(
    "metodo, camino, modulo, parametros",
    [
        ("POST", "/lecturas", "lambdas.lecturas.crearLectura", {}),
        ("GET", "/sensores/3/lecturas", "lambdas.lecturas.obtenerLecturas", {"id": "3"}),
        (
            "DELETE",
            "/sensores/3/lecturas/2026-11-24T18:30:00Z",
            "lambdas.lecturas.eliminarLectura",
            {"id": "3", "fechaHora": "2026-11-24T18:30:00Z"},
        ),
        ("GET", "/productores", "lambdas.catalogo.obtenerProductores", {}),
        ("GET", "/productores/1", "lambdas.catalogo.obtenerProductores", {"id": "1"}),
        ("GET", "/productores/1/parcelas", "lambdas.catalogo.obtenerParcelasProductor", {"id": "1"}),
        ("PUT", "/parcelas/2", "lambdas.catalogo.actualizarParcela", {"id": "2"}),
    ],
)
def test_encuentra_la_lambda_de_cada_ruta(metodo, camino, modulo, parametros):
    _, encontrado, params = servidorLocal.buscar_ruta(metodo, camino)
    assert encontrado == modulo
    assert params == parametros


def test_ruta_desconocida():
    assert servidorLocal.buscar_ruta("GET", "/cultivos") is None
    assert servidorLocal.buscar_ruta("PATCH", "/productores/1") is None


def test_arma_el_evento_como_api_gateway():
    evento = servidorLocal.armar_evento(
        "GET", "/sensores/{id}/lecturas", "/sensores/3/lecturas", {"id": "3"}, "horas=6", None
    )
    assert evento["pathParameters"] == {"id": "3"}
    assert evento["queryStringParameters"] == {"horas": "6"}
    assert evento["resource"] == "/sensores/{id}/lecturas"


def test_todas_las_lambdas_existen():
    import importlib

    for _, _, modulo in servidorLocal.RUTAS:
        assert callable(importlib.import_module(modulo).lambda_handler)
