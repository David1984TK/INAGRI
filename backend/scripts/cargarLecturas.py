"""Genera lecturas inventadas para la demostración y, si se pide, las carga en DynamoDB.

Uso (desde la carpeta backend, con el entorno virtual activo):
  python scripts/cargarLecturas.py                    solo muestra un resumen, no toca AWS
  python scripts/cargarLecturas.py --salida datos.json   además guarda las lecturas en un archivo
  python scripts/cargarLecturas.py --cargar           escribe las lecturas en la tabla de DynamoDB

Para --cargar hace falta llenar .env (AWS_REGION y DYNAMODB_TABLA_LECTURAS) y tener
credenciales de AWS configuradas. Cargar dos veces es seguro: las lecturas tienen la
misma llave y se sobrescriben, no se duplican.
"""
import argparse
import json
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ / ".env")

from common.fechas import formatear_fecha  # noqa: E402
from lambdas.lecturas.crearLectura import DIAS_RETENCION  # noqa: E402

# id_sensor -> id_parcela. Coincide con el prototipo: Parcela Sur (1) tiene 4 sensores,
# Parcela Río (2) tiene 2 y Parcela Norte (3) tiene 4.
SENSORES = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 3}

# Valores típicos de cada parcela: Sur con humedad baja, Río con temperatura alta
# y Norte en rango, como en las pantallas.
PERFILES = {
    1: {"humedad": 30, "temperatura": 28, "amplitud": 5},
    2: {"humedad": 52, "temperatura": 31, "amplitud": 4},
    3: {"humedad": 42, "temperatura": 26, "amplitud": 4},
}

# El prototipo muestra un sensor sin señal desde hace unas horas.
SENSOR_SIN_SENAL = 4
HORAS_SIN_SENAL = 2


def _decimal(numero, minimo, maximo):
    return Decimal(str(round(min(max(numero, minimo), maximo), 1)))


def generar_lecturas(ahora, dias=14, semilla=42):
    """Una lectura por hora y por sensor, de ahora hacia atrás. Es determinista."""
    azar = random.Random(semilla)
    fin = ahora.replace(minute=0, second=0, microsecond=0)
    lecturas = []

    for id_sensor, id_parcela in SENSORES.items():
        perfil = PERFILES[id_parcela]
        desfase = azar.uniform(-2, 2)  # cada sensor mide un poco distinto

        for horas_atras in range(dias * 24):
            if id_sensor == SENSOR_SIN_SENAL and horas_atras < HORAS_SIN_SENAL:
                continue
            momento = fin - timedelta(hours=horas_atras)
            # Ciclo diario: la temperatura sube en la tarde (15:00 hora de México = 21:00 UTC).
            ciclo = math.sin(2 * math.pi * (momento.hour - 15) / 24)
            temperatura = perfil["temperatura"] + perfil["amplitud"] * ciclo + desfase * 0.5 + azar.gauss(0, 0.6)
            humedad = perfil["humedad"] - 6 * ciclo + desfase + azar.gauss(0, 1.0)

            lecturas.append(
                {
                    "id_sensor": id_sensor,
                    "fecha_hora": formatear_fecha(momento),
                    "humedad": _decimal(humedad, 5, 95),
                    "temperatura": _decimal(temperatura, -10, 50),
                    "origen": "sensor",
                    "id_parcela": id_parcela,
                    "expira_en": int((momento + timedelta(days=DIAS_RETENCION)).timestamp()),
                }
            )
    return lecturas


def cargar(lecturas):
    from common.dynamo import obtener_tabla

    tabla = obtener_tabla()
    with tabla.batch_writer() as lote:
        for lectura in lecturas:
            lote.put_item(Item=lectura)


def _guardar_json(lecturas, ruta):
    def convertir(valor):
        if isinstance(valor, Decimal):
            return float(valor)
        raise TypeError(type(valor).__name__)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(lecturas, archivo, default=convertir, ensure_ascii=False, indent=2)


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Genera lecturas inventadas para INAGRI.")
    parser.add_argument("--dias", type=int, default=14, help="días de historial (por defecto 14)")
    parser.add_argument("--salida", help="archivo JSON donde guardar las lecturas")
    parser.add_argument("--cargar", action="store_true", help="escribir en DynamoDB")
    args = parser.parse_args(argumentos)

    if not 1 <= args.dias <= DIAS_RETENCION:
        print(f"--dias debe estar entre 1 y {DIAS_RETENCION}.")
        return 1

    lecturas = generar_lecturas(datetime.now(timezone.utc), dias=args.dias)
    fechas = [l["fecha_hora"] for l in lecturas]
    print(f"Lecturas generadas: {len(lecturas)}")
    print(f"Sensores: {len(SENSORES)} | Parcelas: {len(set(SENSORES.values()))}")
    print(f"Desde {min(fechas)} hasta {max(fechas)}")
    print(f"Ejemplo: {lecturas[0]}")

    if args.salida:
        _guardar_json(lecturas, args.salida)
        print(f"Guardadas en {args.salida}")

    if args.cargar:
        if not os.environ.get("DYNAMODB_TABLA_LECTURAS"):
            print("Falta DYNAMODB_TABLA_LECTURAS. Llena el archivo .env (copia de .env.example).")
            return 1
        cargar(lecturas)
        print(f"Cargadas en la tabla {os.environ['DYNAMODB_TABLA_LECTURAS']}.")
    else:
        print("No se escribió nada en AWS (usa --cargar para hacerlo).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
