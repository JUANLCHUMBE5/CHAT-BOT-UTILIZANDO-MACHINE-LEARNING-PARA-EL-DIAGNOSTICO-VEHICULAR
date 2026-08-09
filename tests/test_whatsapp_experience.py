"""Regresiones de experiencia conversacional y salida breve para WhatsApp."""

from src.core.gemini_queue import GeminiRateLimiter, SolicitudGeminiEncolada
from src.core.gestor_diagnostico import GestorDiagnostico


def test_resumen_whatsapp_gnv_es_breve_y_prioriza_prueba_comparativa():
    solicitud = SolicitudGeminiEncolada(
        sintoma="pierde fuerza en subida pero el auto es a GNV",
        diagnostico_ml="Disco de embrague desgastado o patinando",
        confianza_ml=0.42,
        requiere_revision_humana=True,
    )
    resumen = GeminiRateLimiter._crear_resumen_whatsapp(solicitud, "Gravedad: Media")
    assert "gasolina y GNV/GLP" in resumen
    assert "embrague" not in resumen.lower()
    assert "Gravedad: *Media*" in resumen
    assert "Análisis completo disponible en el panel" in resumen
    assert len(resumen) < 700


def test_contexto_multiturno_une_dato_gnv_sin_arrastrar_consulta_nueva(monkeypatch):
    gestor = GestorDiagnostico()
    capturados = []

    monkeypatch.setattr(
        gestor.modelo_ml,
        "predecir_falla_con_confianza",
        lambda texto: (capturados.append(texto) or "falla de alimentación", 0.75),
    )
    monkeypatch.setattr(
        gestor,
        "_generar_respuesta_con_metadatos",
        lambda **kwargs: ("respuesta", {"usado": False, "modo": "diagnostico_degradado_ml_rag"}),
    )

    gestor.procesar_consulta_texto("pierde fuerza en subida y se apaga", session_id="sesion-gnv")
    segundo = gestor.procesar_consulta_texto("pero el auto es a GNV", session_id="sesion-gnv")
    assert "pierde fuerza en subida" in capturados[-1]
    assert "gnv" in capturados[-1].lower()
    assert segundo.sintoma_evaluado == capturados[-1]

    gestor.procesar_consulta_texto("la puerta no abre con el control", session_id="sesion-gnv")
    assert "pierde fuerza" not in capturados[-1]
