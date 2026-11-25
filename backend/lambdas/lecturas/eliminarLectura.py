"""DELETE /sensores/{id}/lecturas/{fechaHora}: elimina una lectura.

Si la lectura no existe responde 404.
"""
import logging

from botocore.exceptions import ClientError

from common.dynamo import obtener_tabla
from common.respuestas import error, respuesta
from common.validaciones import leer_llave_lectura

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(evento, contexto):
    id_sensor, fecha_hora, problema = leer_llave_lectura(evento)
    if problema:
        return error(400, problema)

    try:
        obtener_tabla().delete_item(
            Key={"id_sensor": id_sensor, "fecha_hora": fecha_hora},
            ConditionExpression="attribute_exists(id_sensor)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error(404, "No existe una lectura de ese sensor con esa fecha y hora.")
        logger.exception("Error de DynamoDB al eliminar la lectura")
        return error(500, "No se pudo eliminar la lectura.")

    return respuesta(200, {"mensaje": "Lectura eliminada"})
