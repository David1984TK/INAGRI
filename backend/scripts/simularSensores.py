"""Simula los sensores de campo: cada cierto tiempo manda una lectura por sensor a POST /lecturas.

Hace lo mismo que harían los sensores reales (que mandan una lectura cada 5 minutos),
usando la API de verdad: primero la local y, ya en AWS, la URL de API Gateway.
Así las pantallas muestran sensores "en línea" y lecturas actuales durante la demo.

Usa los mismos sensores y valores típicos que scripts/cargarLecturas.py
(Parcela Sur seca, Parcela Río caliente, Parcela Norte en rango). El sensor 4 no manda
nada, para que en la Parcela Sur se vea un sensor "sin señal" como en los bocetos.

Uso (desde la carpeta backend, con el entorno virtual activo):
  python scripts/simularSensores.py                    cada 5 minutos a http://localhost:3001
  python scripts/simularSensores.py --cada 60          cada minuto
  python scripts/simularSensores.py --una-vez          manda una sola ronda y termina
  python scripts/simularSensores.py --todos            incluye el sensor 4
  python scripts/simularSensores.py --url https://xxxx.execute-api.us-east-1.amazonaws.com/dev --api-key XXXX
"""
import argparse
import json
import math
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from scripts.cargarLecturas import PERFILES, SENSOR_SIN_SENAL, SENSORES  # noqa: E402

# Cada sensor mide un poco distinto, siempre igual entre una ronda y otra.
DESFASES = {id_sensor: random.Random(id_sensor).uniform(-2, 2) for id_sensor in SENSORES}


def generar_lectura(id_sensor, momento, azar):
    """Valores con el ciclo diario: la temperatura sube en la tarde y la humedad baja."""
    perfil = PERFILES[SENSORES[id_sensor]]
    hora_mexico = (momento.hour - 6) % 24
    ciclo = math.sin(2 * math.pi * (hora_mexico - 9) / 24)
    desfase = DESFASES[id_sensor]
    temperatura = perfil["temperatura"] + perfil["amplitud"] * ciclo + desfase * 0.5 + azar.gauss(0, 0.6)
    humedad = perfil["humedad"] - 6 * ciclo + desfase + azar.gauss(0, 1.0)
    return {
        "id_sensor": id_sensor,
        "id_parcela": SENSORES[id_sensor],
        "humedad": round(min(max(humedad, 5), 95), 1),
        "temperatura": round(min(max(temperatura, -10), 50), 1),
        "origen": "sensor",
    }


def sensores_activos(incluir_todos):
    return [s for s in SENSORES if incluir_todos or s != SENSOR_SIN_SENAL]


def enviar(url, lectura, api_key=None):
    """Manda una lectura. Regresa (codigo_http, texto_de_respuesta)."""
    encabezados = {"Content-Type": "application/json"}
    if api_key:
        encabezados["x-api-key"] = api_key
    peticion = urllib.request.Request(
        url.rstrip("/") + "/lecturas",
        data=json.dumps(lectura).encode("utf-8"),
        headers=encabezados,
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            return respuesta.status, respuesta.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except urllib.error.URLError as e:
        return None, str(e.reason)


def ronda(url, incluir_todos, api_key, azar):
    momento = datetime.now(timezone.utc)
    correctas = 0
    for id_sensor in sensores_activos(incluir_todos):
        lectura = generar_lectura(id_sensor, momento, azar)
        codigo, texto = enviar(url, lectura, api_key)
        if codigo == 201:
            correctas += 1
        else:
            print(f"  Sensor {id_sensor}: error {codigo} {texto}")
    hora = momento.astimezone().strftime("%H:%M:%S")
    print(f"[{hora}] {correctas} lecturas enviadas.")
    return correctas


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Simulador de sensores de INAGRI.")
    parser.add_argument("--url", default="http://localhost:3001", help="URL base de la API.")
    parser.add_argument("--cada", type=int, default=300, help="Segundos entre rondas (300 = 5 minutos).")
    parser.add_argument("--una-vez", action="store_true", help="Manda una sola ronda y termina.")
    parser.add_argument("--todos", action="store_true", help=f"Incluye el sensor {SENSOR_SIN_SENAL}.")
    parser.add_argument("--api-key", help="API key de los sensores (solo en AWS).")
    args = parser.parse_args(argumentos)
    if args.cada < 10:
        parser.error("--cada debe ser de al menos 10 segundos.")

    azar = random.Random()
    print(f"Simulando {len(sensores_activos(args.todos))} sensores contra {args.url}. Ctrl + C para salir.")
    if args.una_vez:
        return 0 if ronda(args.url, args.todos, args.api_key, azar) else 1
    try:
        while True:
            ronda(args.url, args.todos, args.api_key, azar)
            time.sleep(args.cada)
    except KeyboardInterrupt:
        print("\nSimulador detenido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
