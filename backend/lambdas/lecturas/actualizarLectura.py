"""PUT /sensores/{id}/lecturas/{fechaHora}: corrige la humedad y/o la temperatura.

Solo se pueden modificar esos dos campos. Si la lectura no existe responde 404
(la condición evita que un update cree una lectura nueva por accidente).
"""
import logging

from botocore.exceptions import ClientError

from common.dynamo import obtener_tabla
from common.lecturas import lectura_publica
from common.respuestas import error, respuesta
from common.validaciones import (
    leer_cuerpo,
    leer_llave_lectura,
    validar_humedad,
    validar_temperatura,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VALIDADORES = {"humedad": validar_humedad, "temperatura": validar_temperatura}


def validar(datos):
    """Regresa (cambios, None) o (None, mensaje)."""
    no_permitidos = sorted(set(datos) - set(VALIDADORES))
    if no_permitidos:
        return None, "Solo se pueden modificar humedad y temperatura. No permitidos: " + ", ".join(no_permitidos) + "."

    cambios = {}
    for campo, validador in VALIDADORES.items():
        if campo in datos:
            valor, problema = validador(datos[campo])
            if problema:
                return None, problema
            cambios[campo] = valor

    if not cambios:
        return None, "Manda humedad, temperatura o ambas."
    return cambios, None


def lambda_handler(evento, contexto):
    id_sensor, fecha_hora, problema = leer_llave_lectura(evento)
    if problema:
        return error(400, problema)

    try:
        datos = leer_cuerpo(evento)
    except ValueError as e:
        return error(400, str(e))

    cambios, problema = validar(datos)
    if problema:
        return error(400, problema)

    try:
        resultado = obtener_tabla().update_item(
            Key={"id_sensor": id_sensor, "fecha_hora": fecha_hora},
            UpdateExpression="SET " + ", ".join(f"{campo} = :{campo}" for campo in cambios),
            ExpressionAttributeValues={f":{campo}": valor for campo, valor in cambios.items()},
            ConditionExpression="attribute_exists(id_sensor)",
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error(404, "No existe una lectura de ese sensor con esa fecha y hora.")
        logger.exception("Error de DynamoDB al actualizar la lectura")
        return error(500, "No se pudo actualizar la lectura.")

    return respuesta(
        200,
        {"mensaje": "Lectura actualizada", "lectura": lectura_publica(resultado["Attributes"])},
    )
