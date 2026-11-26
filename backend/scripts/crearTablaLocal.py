"""Crea la tabla de lecturas en DynamoDB Local (Docker), con la misma llave que en AWS.

Uso (desde la carpeta backend, con el entorno virtual activo y docker compose up -d):
  python scripts/crearTablaLocal.py

Solo funciona contra DynamoDB Local: exige DYNAMODB_ENDPOINT_URL en .env, para que
nunca cree nada en la cuenta de AWS por accidente.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ / ".env")

from common.dynamo import obtener_tabla  # noqa: E402


def main():
    if not os.environ.get("DYNAMODB_ENDPOINT_URL"):
        print("Falta DYNAMODB_ENDPOINT_URL en .env (por ejemplo http://localhost:8000).")
        return 1
    if not os.environ.get("DYNAMODB_TABLA_LECTURAS"):
        print("Falta DYNAMODB_TABLA_LECTURAS en .env.")
        return 1

    tabla = obtener_tabla()
    cliente = tabla.meta.client
    nombre = tabla.name

    if nombre in cliente.list_tables()["TableNames"]:
        print(f"La tabla {nombre} ya existe en DynamoDB Local.")
        return 0

    cliente.create_table(
        TableName=nombre,
        KeySchema=[
            {"AttributeName": "id_sensor", "KeyType": "HASH"},
            {"AttributeName": "fecha_hora", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "id_sensor", "AttributeType": "N"},
            {"AttributeName": "fecha_hora", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    cliente.get_waiter("table_exists").wait(TableName=nombre)
    cliente.update_time_to_live(
        TableName=nombre,
        TimeToLiveSpecification={"Enabled": True, "AttributeName": "expira_en"},
    )
    print(f"Tabla {nombre} creada en DynamoDB Local.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
