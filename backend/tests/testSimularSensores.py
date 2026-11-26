import random
from datetime import datetime, timezone

import pytest

from lambdas.lecturas.crearLectura import validar
from scripts import simularSensores
from scripts.cargarLecturas import SENSOR_SIN_SENAL, SENSORES

TARDE = datetime(2026, 11, 26, 21, 0, tzinfo=timezone.utc)   # 15:00 en México
MADRUGADA = datetime(2026, 11, 26, 9, 0, tzinfo=timezone.utc)  # 03:00 en México


def test_las_lecturas_pasan_la_validacion_de_crear_lectura():
    azar = random.Random(1)
    for id_sensor in SENSORES:
        lectura = simularSensores.generar_lectura(id_sensor, TARDE, azar)
        item, problema = validar(lectura, ahora=TARDE)
        assert problema is None, problema
        assert item["id_parcela"] == SENSORES[id_sensor]


def test_en_la_tarde_hace_mas_calor_que_en_la_madrugada():
    azar = random.Random(1)
    tarde = simularSensores.generar_lectura(7, TARDE, azar)
    madrugada = simularSensores.generar_lectura(7, MADRUGADA, azar)
    assert tarde["temperatura"] > madrugada["temperatura"]
    assert tarde["humedad"] < madrugada["humedad"]


def test_la_parcela_sur_sale_seca():
    azar = random.Random(1)
    humedades = [simularSensores.generar_lectura(s, TARDE, azar)["humedad"] for s in (1, 2, 3)]
    assert max(humedades) < 40  # debajo del rango del frijol


def test_por_defecto_no_manda_el_sensor_sin_senal():
    assert SENSOR_SIN_SENAL not in simularSensores.sensores_activos(False)
    assert len(simularSensores.sensores_activos(True)) == len(SENSORES)


def test_una_ronda_manda_una_lectura_por_sensor(monkeypatch):
    enviadas = []

    def enviar_falso(url, lectura, api_key=None):
        enviadas.append((url, lectura["id_sensor"], api_key))
        return 201, "{}"

    monkeypatch.setattr(simularSensores, "enviar", enviar_falso)
    correctas = simularSensores.ronda("http://localhost:3001", False, "llave", random.Random(1))
    assert correctas == len(SENSORES) - 1
    assert all(url == "http://localhost:3001" and llave == "llave" for url, _, llave in enviadas)


def test_cuenta_los_errores(monkeypatch):
    monkeypatch.setattr(simularSensores, "enviar", lambda *a, **k: (None, "Connection refused"))
    assert simularSensores.ronda("http://localhost:3001", False, None, random.Random(1)) == 0


def test_no_acepta_intervalos_muy_cortos():
    with pytest.raises(SystemExit):
        simularSensores.main(["--cada", "2"])
