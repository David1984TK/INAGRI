"""Conexión falsa de PostgreSQL para las pruebas: no se conecta a ninguna base.

Se le indica qué filas debe regresar cada consulta (en orden) y guarda el SQL
que se ejecutó para poder revisarlo en las pruebas.
"""


class CursorFalso:
    def __init__(self, conexion):
        self.conexion = conexion
        self._filas = []

    def execute(self, sql, valores=None):
        self.conexion.consultas.append((" ".join(sql.split()), list(valores or [])))
        numero = len(self.conexion.consultas)
        if self.conexion.error and (self.conexion.error_en is None or numero == self.conexion.error_en):
            raise self.conexion.error
        self._filas = self.conexion.resultados.pop(0) if self.conexion.resultados else []

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ConexionFalsa:
    def __init__(self, *resultados, error=None, error_en=None):
        """resultados: una lista de filas (diccionarios) por cada execute, en orden.

        error: excepción que lanza execute. error_en: número de execute (1, 2, ...) en el
        que falla; si no se indica, falla en todos.
        """
        self.resultados = [list(r) for r in resultados]
        self.error = error
        self.error_en = error_en
        self.consultas = []
        self.confirmada = False
        self.revertida = False

    def cursor(self):
        return CursorFalso(self)

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traza):
        if tipo is None:
            self.confirmada = True
        else:
            self.revertida = True
        return False
