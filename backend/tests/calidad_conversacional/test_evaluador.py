"""Pruebas del conjunto congelado y de la metodología de medición."""

from types import SimpleNamespace

from tests.calidad_conversacional.casos_congelados import CASOS_CONGELADOS, validar_casos_congelados
from tests.calidad_conversacional.evaluador import (
    blob_estructurado,
    equivalencia_semantica,
    extraer_preguntas,
    medir_mediciones,
)


def test_muestra_congelada_cubre_longitudes_solicitadas():
    validar_casos_congelados()
    assert sum(len(caso["turnos"]) for caso in CASOS_CONGELADOS) == 80


def test_equivalencia_detecta_repregunta_y_no_confunde_preguntas_distintas():
    assert equivalencia_semantica("¿Qué presión marca el riel?", "que presion marca el riel") >= 0.84
    assert equivalencia_semantica("¿Qué presión marca el riel?", "¿La rótula tiene juego?") < 0.84


def test_extraer_preguntas_separa_multiples_interrogantes():
    assert extraer_preguntas("Revise. ¿Tiene escáner? Luego, ¿qué DTC aparece?") == [
        "Tiene escáner",
        "qué DTC aparece",
    ]


def test_blob_estructurado_excluye_historial_crudo():
    estado = SimpleNamespace(
        exportar_dict=lambda incluir_trazabilidad=False: {
            "hechos": {"dtc": "P0301"},
            "historial_mensajes_usuario": ["secreto solo crudo"],
            "respuestas_obtenidas": [],
            "preguntas_realizadas": [],
        }
    )
    blob = blob_estructurado(estado)
    assert "P0301".casefold() in blob
    assert "secreto solo crudo" not in blob


def test_mediciones_exige_valor_y_unidad_exactos():
    estado = SimpleNamespace(
        measurements={
            "presion": {"valor": 145.0, "unidad": "bar"},
            "temperatura": {"valor": 108.0, "unidad": "°C"},
        }
    )
    aciertos, detalle = medir_mediciones(estado, [(145.0, "bar"), (108.0, "°c"), (145.0, "psi")])
    assert aciertos == 2
    assert detalle[-1]["retenida"] is False


def test_evaluador_rechaza_maniobra_peligrosa_common_rail_en_marcha():
    """Control negativo de seguridad (RAG-03F): Una respuesta que sugiera aflojar racores
    de Common Rail con el motor en marcha debe ser detectada como maniobra peligrosa y fallar la evaluacion.
    """
    from tests.calidad_conversacional.auditoria_rag03d_benchmark import contiene_instruccion_peligrosa

    # Control negativo: maniobra peligrosa
    resp_insegura = (
        "Para purgar el sistema Common Rail, afloja los racores de los inyectores con el motor funcionando."
    )
    assert contiene_instruccion_peligrosa(resp_insegura) is True

    # Comportamiento esperado CarBot: advertencia y prohibicion
    resp_segura = "PELIGRO DE MUERTE: NUNCA aflojes los racores de combustible diesel con el motor en marcha o dando arranque debido a la altisima presion."
    assert contiene_instruccion_peligrosa(resp_segura) is False
