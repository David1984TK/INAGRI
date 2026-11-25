from datetime import datetime, timedelta, timezone

from lambdas.lecturas import crearLectura
from scripts import cargarLecturas

AHORA = datetime(2026, 11, 24, 21, 37, tzinfo=timezone.utc)


def test_genera_una_lectura_por_hora_y_por_sensor():
    lecturas = cargarLecturas.generar_lecturas(AHORA, dias=2)
    # 10 sensores x 48 horas, menos las horas que el sensor sin señal no reportó
    esperado = 10 * 48 - cargarLecturas.HORAS_SIN_SENAL
    assert len(lecturas) == esperado


def test_son_miles_de_lecturas_con_el_valor_por_defecto():
    assert len(cargarLecturas.generar_lecturas(AHORA)) > 3000


def test_las_llaves_no_se_repiten():
    lecturas = cargarLecturas.generar_lecturas(AHORA, dias=3)
    llaves = {(l["id_sensor"], l["fecha_hora"]) for l in lecturas}
    assert len(llaves) == len(lecturas)


def test_la_ultima_lectura_es_de_la_hora_actual_redondeada():
    lecturas = cargarLecturas.generar_lecturas(AHORA, dias=1)
    assert max(l["fecha_hora"] for l in lecturas) == "2026-11-24T21:00:00Z"


def test_un_sensor_esta_sin_senal():
    lecturas = cargarLecturas.generar_lecturas(AHORA, dias=1)
    sin_senal = [l["fecha_hora"] for l in lecturas if l["id_sensor"] == cargarLecturas.SENSOR_SIN_SENAL]
    assert max(sin_senal) == "2026-11-24T19:00:00Z"


def test_cada_sensor_pertenece_a_su_parcela():
    for lectura in cargarLecturas.generar_lecturas(AHORA, dias=1):
        assert lectura["id_parcela"] == cargarLecturas.SENSORES[lectura["id_sensor"]]


def test_todas_las_lecturas_pasan_la_misma_validacion_que_el_post():
    for lectura in cargarLecturas.generar_lecturas(AHORA, dias=2):
        datos = {
            "id_sensor": lectura["id_sensor"],
            "humedad": float(lectura["humedad"]),
            "temperatura": float(lectura["temperatura"]),
            "fecha_hora": lectura["fecha_hora"],
            "origen": lectura["origen"],
            "id_parcela": lectura["id_parcela"],
        }
        item, problema = crearLectura.validar(datos, ahora=AHORA)
        assert problema is None, (problema, datos)
        assert item["expira_en"] == lectura["expira_en"]


def test_es_determinista():
    assert cargarLecturas.generar_lecturas(AHORA, dias=1) == cargarLecturas.generar_lecturas(AHORA, dias=1)


def test_la_parcela_sur_tiene_humedad_mas_baja_que_la_del_rio():
    lecturas = cargarLecturas.generar_lecturas(AHORA, dias=3)

    def promedio(parcela):
        valores = [float(l["humedad"]) for l in lecturas if l["id_parcela"] == parcela]
        return sum(valores) / len(valores)

    assert promedio(1) < promedio(3) < promedio(2)


def test_main_sin_cargar_no_toca_aws(capsys, monkeypatch):
    monkeypatch.setattr(cargarLecturas, "cargar", lambda lecturas: (_ for _ in ()).throw(AssertionError("no debe cargar")))
    assert cargarLecturas.main(["--dias", "1"]) == 0
    assert "No se escribió nada en AWS" in capsys.readouterr().out


def test_main_con_cargar_sin_tabla_configurada(capsys, monkeypatch):
    monkeypatch.delenv("DYNAMODB_TABLA_LECTURAS", raising=False)
    assert cargarLecturas.main(["--dias", "1", "--cargar"]) == 1
    assert "DYNAMODB_TABLA_LECTURAS" in capsys.readouterr().out


def test_main_con_cargar_usa_las_lecturas_generadas(monkeypatch):
    monkeypatch.setenv("DYNAMODB_TABLA_LECTURAS", "lecturas")
    recibidas = []
    monkeypatch.setattr(cargarLecturas, "cargar", recibidas.extend)
    assert cargarLecturas.main(["--dias", "1", "--cargar"]) == 0
    assert len(recibidas) == 10 * 24 - cargarLecturas.HORAS_SIN_SENAL


def test_main_rechaza_dias_fuera_de_rango(capsys):
    assert cargarLecturas.main(["--dias", "0"]) == 1
    assert cargarLecturas.main(["--dias", "9999"]) == 1
