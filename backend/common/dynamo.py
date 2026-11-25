"""Acceso a la tabla de lecturas en DynamoDB."""
import os

import boto3


def obtener_tabla():
    nombre = os.environ["DYNAMODB_TABLA_LECTURAS"]
    region = os.environ.get("AWS_REGION")
    return boto3.resource("dynamodb", region_name=region).Table(nombre)
