"""Tabla falsa de DynamoDB para las pruebas de monitoreo: solo implementa query."""


class TablaLecturasFalsa:
    def __init__(self, lecturas=None, error=None):
        """lecturas: {id_sensor: [lecturas]} (en cualquier orden)."""
        self.lecturas = lecturas or {}
        self.error = error
        self.consultas = []

    def query(self, KeyConditionExpression, ScanIndexForward=True, Limit=None):
        if self.error:
            raise self.error
        id_sensor = KeyConditionExpression.get_expression()["values"][1]
        self.consultas.append({"id_sensor": id_sensor, "descendente": not ScanIndexForward, "limite": Limit})
        elementos = sorted(
            self.lecturas.get(id_sensor, []), key=lambda l: l["fecha_hora"], reverse=not ScanIndexForward
        )
        if Limit is not None:
            elementos = elementos[:Limit]
        return {"Items": elementos}
