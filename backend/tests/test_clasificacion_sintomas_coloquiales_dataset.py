"""Pruebas exhaustivas de clasificación de síntomas vehiculares coloquiales con el modelo Linear SVM."""

from __future__ import annotations

import pytest

from src.infrastructure.modelo_ml import ModeloML


@pytest.fixture(scope="module")
def modelo_ml():
    return ModeloML()


def test_clasificacion_bujias_o_bobinas_jaloneo(modelo_ml):
    sintoma = "el motor jalonea cabecea al acelerar con falla de chispa y bobina o bujia de encendido"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "bujia" in clase.lower() or "bobina" in clase.lower() or "misfire" in clase.lower()
    assert conf > 0.35


def test_clasificacion_discos_alabeados_frenado(modelo_ml):
    sintoma = "cuando piso el freno bajando a 80 km/h el pedal vibra y el timón tiembla"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "disco" in clase.lower() or "alabeado" in clase.lower()
    assert conf > 0.40


def test_clasificacion_pastillas_freno_chirrido(modelo_ml):
    sintoma = "se escucha un chirrido metálico constante de fierro con fierro cada vez que freno"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "pastilla" in clase.lower() or "freno" in clase.lower()
    assert conf > 0.40


def test_clasificacion_embrague_patinando(modelo_ml):
    sintoma = "acelero a fondo y suben las revoluciones del motor pero el carro no avanza con fuerza"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "embrague" in clase.lower() or "patina" in clase.lower()
    assert conf > 0.40


def test_clasificacion_bateria_descargada(modelo_ml):
    sintoma = "al girar la llave las luces del tablero se apagan por completo y hace tac tac lento"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "bateria" in clase.lower() or "bornes" in clase.lower()
    assert conf > 0.40


def test_clasificacion_alternador_defectuoso(modelo_ml):
    sintoma = "el testigo de la bateria se queda encendido en el tablero mientras voy manejando"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "alternador" in clase.lower() or "bateria" in clase.lower()
    assert conf > 0.40


def test_clasificacion_cuerpo_aceleracion_iac_ralenti(modelo_ml):
    sintoma = "en neutro y en los semáforos las revoluciones suben y bajan solas y a veces se apaga"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "cuerpo" in clase.lower() or "iac" in clase.lower() or "aceleracion" in clase.lower()
    assert conf > 0.25


def test_clasificacion_empaque_culata_soplado(modelo_ml):
    sintoma = "bota humo blanco espeso por el tubo de escape y el aceite parece café con leche chocolatada"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "culata" in clase.lower() or "empaque" in clase.lower()
    assert conf > 0.40


def test_clasificacion_termostato_motoventilador_calentamiento(modelo_ml):
    sintoma = "la temperatura sube al máximo en el tráfico pesado y el ventilador del radiador no prende"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "termostato" in clase.lower() or "ventilador" in clase.lower() or "refrigerante" in clase.lower() or "radiador" in clase.lower()
    assert conf > 0.40


def test_clasificacion_llantas_desbalanceadas_en_carretera(modelo_ml):
    sintoma = "el timón vibra y la direccion tiembla en carretera por llantas desbalanceadas o desalineadas"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "llanta" in clase.lower() or "desbalance" in clase.lower() or "alinea" in clase.lower()
    assert conf > 0.35


def test_clasificacion_junta_homocinetica_curvas(modelo_ml):
    sintoma = "al doblar toda la dirección a la izquierda acelerando suena clac clac clac continuo"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "homocinetica" in clase.lower() or "palier" in clase.lower()
    assert conf > 0.40


def test_clasificacion_inyectores_sucios(modelo_ml):
    sintoma = "el motor tose y le cuesta responder al acelerador a cualquier velocidad"
    clase, conf = modelo_ml.predecir(sintoma)
    assert any(w in clase.lower() for w in ("inyector", "filtro", "bomba", "bujia", "cuerpo", "aceleracion"))
    assert conf > 0.25


def test_clasificacion_amortiguadores_reventados(modelo_ml):
    sintoma = "el carro rebota como hamaca en los baches y golpea seco en la rueda delantera"
    clase, conf = modelo_ml.predecir(sintoma)
    assert "amortiguador" in clase.lower() or "suspension" in clase.lower() or "buje" in clase.lower()
    assert conf > 0.35


def test_modelo_devuelve_probabilidades_calibradas(modelo_ml):
    predicciones = modelo_ml.predecir_top_fallas("el carro no acelera bien", limite=3)
    assert len(predicciones) <= 3
    assert len(predicciones) >= 1

    total_prob = sum(float(p["probabilidad"]) for p in predicciones)
    assert total_prob <= 1.05
    for p in predicciones:
        assert isinstance(p["falla"], str)
        assert 0.0 <= float(p["probabilidad"]) <= 1.0
