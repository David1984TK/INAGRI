"""Formato público de una lectura (sin atributos internos como expira_en)."""

CAMPOS_PUBLICOS = ("fecha_hora", "humedad", "temperatura", "origen", "registrado_por", "id_parcela")


def lectura_publica(item):
    return {campo: item[campo] for campo in CAMPOS_PUBLICOS if campo in item}
