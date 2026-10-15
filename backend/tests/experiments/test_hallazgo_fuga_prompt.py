"""Contrato local de hallazgo, fuente documental y salida realmente mostrada."""

from types import SimpleNamespace

import pytest

from src.core.conversacion.avance_preguntas import asegurar_pregunta_util
from src.core.diagnostico.coherencia_evidencia import preparar_contexto_rag_para_llm
from src.core.diagnostico.hallazgo_refrigerante import estado_fuga
from src.core.diagnostico.prompt_builder import construir_prompt_diagnostico


@pytest.mark.parametrize("texto,esperado", [
    ("Hay fuga de refrigerante y mancha en el piso", True),
    ("Pierde agua", True),
    ("Recalienta y deja una mancha en el piso", True),
    ("No hay fuga de refrigerante", False),
    ("No pierde agua", False),
    ("Quizás hay fuga de refrigerante", None),
    ("¿Hay fuga de refrigerante?", None),
    ("Mancha en el piso", None),
    ("Mezcla pobre e injectores", None),
])
def test_polaridad(texto, esperado):
    assert estado_fuga(texto) is esperado


def test_prompt_prioriza_hallazgo_sin_inyectar_corpus_preliminar():
    contexto, titulo = preparar_contexto_rag_para_llm("FRAGMENTO_NO_VALIDADO", "Fuga", {}, False)
    prompt = construir_prompt_diagnostico(
        "Recalienta y pierde agua", "Hipótesis", 30, titulo, contexto, "",
    )
    assert contexto == ""
    assert "FRAGMENTO_NO_VALIDADO" not in prompt
    assert "corpus preliminar no inyectado" in prompt
    assert "prueba de presión" in prompt
    assert "NO temperatura genérica" in prompt


def test_sin_documento_no_afirma_que_existe_corpus_preliminar():
    assert preparar_contexto_rag_para_llm("", "", {}, False) == (
        "", "Sin procedimiento RAG recuperado aplicable",
    )


def test_fuente_validada_conserva_contexto():
    meta = {"estado_validacion": "validado_oem_taller", "manual_oem": "Mazda manual servicio",
            "auditoria": {"verificado_documental": True, "auditoria_mecanica_formal_firmada": True}}
    assert preparar_contexto_rag_para_llm("Procedimiento", "Manual", meta, True) == (
        "Procedimiento", "Manual",
    )


def estado(mensajes, sistema="refrigeracion"):
    return SimpleNamespace(active_system=sistema, historial_mensajes_usuario=mensajes,
                           preguntas_realizadas=[], turno_actual=1,
                           registrar_pregunta=lambda *a, **k: None)


def test_fuga_prevalece_sobre_temperatura_aunque_no_sea_pregunta_repetida():
    s = estado(["Recalienta", "Hay fuga de refrigerante"])
    respuesta, pregunta = asegurar_pregunta_util(s, "¿Qué temperatura marca el escáner?", [])
    assert "presión" in respuesta and "radiador" in pregunta
    assert "escáner" not in respuesta
    assert "no como pieza confirmada" in respuesta


def test_fuga_no_bucle_y_negacion_posterior_prevalece():
    s = estado(["Hay fuga de refrigerante"])
    previas = []
    for _ in range(2):
        _, pregunta = asegurar_pregunta_util(s, "¿Qué temperatura marca el escáner?", previas)
        assert pregunta and pregunta not in [p["texto"] for p in previas]
        previas.append({"texto": pregunta})
    respuesta, pregunta = asegurar_pregunta_util(s, "¿Qué temperatura marca el escáner?", previas)
    assert pregunta is None and "pendiente" in respuesta
    s.historial_mensajes_usuario.append("No hay fuga de refrigerante")
    respuesta, _ = asegurar_pregunta_util(s, "¿Funciona el ventilador?", [])
    assert respuesta == "¿Funciona el ventilador?"


def test_versa_y_mazda_simple_no_cambian():
    for s in [estado(["recalienta"]), estado(["injectores no inyectan"], "combustible_admision")]:
        assert asegurar_pregunta_util(s, "¿Qué resultado obtuviste?", [])[0] == "¿Qué resultado obtuviste?"
