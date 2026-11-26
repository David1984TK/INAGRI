"""Servidor local que imita API Gateway: recibe peticiones HTTP y llama a las Lambdas.

Sirve para probar los endpoints con Postman o con el frontend sin desplegar nada en AWS.
Usa las bases de Docker (docker compose up -d) y los valores de .env.

Uso (desde la carpeta backend, con el entorno virtual activo):
  python scripts/servidorLocal.py             escucha en http://localhost:3001
  python scripts/servidorLocal.py --puerto 4000
"""
import argparse
import importlib
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ / ".env")

from common.respuestas import ENCABEZADOS  # noqa: E402

# (método, ruta como en API Gateway, módulo de la Lambda)
RUTAS = [
    ("POST", "/auth/login", "lambdas.auth.iniciarSesion"),
    ("PUT", "/auth/contrasena", "lambdas.auth.cambiarContrasena"),
    ("POST", "/lecturas", "lambdas.lecturas.crearLectura"),
    ("GET", "/sensores/{id}/lecturas", "lambdas.lecturas.obtenerLecturas"),
    ("PUT", "/sensores/{id}/lecturas/{fechaHora}", "lambdas.lecturas.actualizarLectura"),
    ("DELETE", "/sensores/{id}/lecturas/{fechaHora}", "lambdas.lecturas.eliminarLectura"),
    ("GET", "/productores", "lambdas.catalogo.obtenerProductores"),
    ("POST", "/productores", "lambdas.catalogo.crearProductor"),
    ("GET", "/productores/{id}", "lambdas.catalogo.obtenerProductores"),
    ("PUT", "/productores/{id}", "lambdas.catalogo.actualizarProductor"),
    ("DELETE", "/productores/{id}", "lambdas.catalogo.eliminarProductor"),
    ("GET", "/productores/{id}/parcelas", "lambdas.catalogo.obtenerParcelasProductor"),
    ("GET", "/parcelas", "lambdas.catalogo.obtenerParcelas"),
    ("POST", "/parcelas", "lambdas.catalogo.crearParcela"),
    ("GET", "/parcelas/{id}", "lambdas.catalogo.obtenerParcelas"),
    ("GET", "/parcelas/{id}/sensores", "lambdas.catalogo.obtenerSensoresParcela"),
    ("PUT", "/parcelas/{id}", "lambdas.catalogo.actualizarParcela"),
    ("DELETE", "/parcelas/{id}", "lambdas.catalogo.eliminarParcela"),
]


def _patron(ruta):
    return re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", ruta) + "/?$")


TABLA_RUTAS = [(metodo, ruta, _patron(ruta), modulo) for metodo, ruta, modulo in RUTAS]


def buscar_ruta(metodo, camino):
    """Regresa (ruta, modulo, parametros) o None."""
    for metodo_ruta, ruta, patron, modulo in TABLA_RUTAS:
        coincidencia = patron.match(camino)
        if metodo_ruta == metodo and coincidencia:
            return ruta, modulo, coincidencia.groupdict()
    return None


def armar_evento(metodo, ruta, camino, parametros, consulta, cuerpo, encabezados=None):
    """Arma un evento igual al que manda API Gateway con integración proxy."""
    return {
        "httpMethod": metodo,
        "resource": ruta,
        "path": camino,
        "pathParameters": parametros or None,
        "queryStringParameters": dict(parse_qsl(consulta)) or None,
        "headers": encabezados or {"Content-Type": "application/json"},
        "body": cuerpo,
        "isBase64Encoded": False,
    }


class Manejador(BaseHTTPRequestHandler):
    def _responder(self, codigo, cuerpo, encabezados=ENCABEZADOS):
        datos = cuerpo.encode("utf-8")
        self.send_response(codigo)
        for nombre, valor in encabezados.items():
            self.send_header(nombre, valor)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _atender(self):
        partes = urlsplit(self.path)
        encontrada = buscar_ruta(self.command, partes.path)
        if encontrada is None:
            self._responder(404, json.dumps({"error": "Ruta no encontrada."}))
            return

        ruta, modulo, parametros = encontrada
        largo = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(largo).decode("utf-8") if largo else None
        evento = armar_evento(
            self.command, ruta, partes.path, parametros, partes.query, cuerpo, dict(self.headers)
        )

        lambda_handler = importlib.import_module(modulo).lambda_handler
        resultado = lambda_handler(evento, None)
        self._responder(resultado["statusCode"], resultado["body"], resultado.get("headers", ENCABEZADOS))

    def do_OPTIONS(self):  # respuesta a la "preflight" de CORS del navegador
        self._responder(204, "")

    do_GET = do_POST = do_PUT = do_DELETE = _atender


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="API local de INAGRI.")
    parser.add_argument("--puerto", type=int, default=3001)
    args = parser.parse_args(argumentos)

    servidor = ThreadingHTTPServer(("localhost", args.puerto), Manejador)
    print(f"API local de INAGRI en http://localhost:{args.puerto} (Ctrl + C para salir)")
    for metodo, ruta, _ in RUTAS:
        print(f"  {metodo:6} {ruta}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
