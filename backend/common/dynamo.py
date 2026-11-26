"""Acceso a la tabla de lecturas en DynamoDB.

En local, DYNAMODB_ENDPOINT_URL apunta a DynamoDB Local (http://localhost:8000).
En AWS esa variable no se define y se usa la tabla real.
"""
import os

import boto3


def obtener_tabla():
    nombre = os.environ["DYNAMODB_TABLA_LECTURAS"]
    region = os.environ.get("AWS_REGION")
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL")
    if endpoint:
        # DynamoDB Local acepta cualquier credencial; así no se usan las de AWS.
        recurso = boto3.resource(
            "dynamodb",
            region_name=region or "us-east-1",
            endpoint_url=endpoint,
            aws_access_key_id="local",
            aws_secret_access_key="local",
        )
    else:
        recurso = boto3.resource("dynamodb", region_name=region)
    return recurso.Table(nombre)
