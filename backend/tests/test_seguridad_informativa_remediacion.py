import pytest

from src.core.diagnostico.seguridad_informativa import proteger_respuesta_informativa


@pytest.mark.parametrize("pregunta,respuesta", [
    ("Reaprendizaje del cuerpo de aceleración", "Purgar frenos y cambiar pastillas."),
    ("Inspección de embrague", "Medir discos de freno."),
    ("Caja termostática", "Desmontar caja de cambios."),
    ("Gasolina", "Aflojar inyectores Common Rail."),
    ("Radiador", "Abrir radiador caliente."),
    ("Cuerpo de aceleración", "Revisar cuerpo de aceleración y purgar frenos."),
    ("Cuerpo de aceleración", "Ajustar cuerpo de aceleración a 900 rpm."),
])
def test_rechaza_respuestas_incompatibles(pregunta, respuesta):
    texto, meta = proteger_respuesta_informativa(pregunta, respuesta, {"usado": True})
    assert respuesta not in texto
    assert "información suficientemente verificada" in texto
    assert meta["usado"] is False


def test_conserva_orientacion_pertinente_sin_valores_inventados():
    respuesta = "El reaprendizaje del cuerpo de aceleración depende del manual OEM del motor."
    texto, meta = proteger_respuesta_informativa("Reaprendizaje del cuerpo de aceleración", respuesta, {"usado": True})
    assert texto == respuesta
    assert meta["usado"] is True


@pytest.mark.parametrize("proveedor", ["gemini", "groq", "local"])
@pytest.mark.parametrize("contexto", ["", "No busco información de frenos.",
                                      'Antes dijo "purgar frenos".', "Antes hablamos de frenos."])
def test_generador_rechaza_respuesta_cruzada_en_todos_los_proveedores(monkeypatch, proveedor, contexto):
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from src.config import settings
    from src.core.diagnostico import response_generator as modulo

    incompatible = "Purgar frenos y sustituir las pastillas de freno."
    sesion = MagicMock()
    sesion.post.return_value.status_code = 200
    sesion.post.return_value.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": incompatible}]}}]
    }
    gestor = SimpleNamespace(api_key="mock" if proveedor == "gemini" else "", _http_session=sesion)
    monkeypatch.setattr(settings, "groq_api_key", "mock" if proveedor == "groq" else "")
    monkeypatch.setattr(settings, "groq_chat_enabled", proveedor == "groq")
    monkeypatch.setattr(modulo, "generar_respuesta_groq", lambda *a, **k: (incompatible, {"usado": True}))
    texto, meta = modulo.generar_respuesta_con_metadatos(
        gestor, "Reaprendizaje de cuerpo de aceleración. " + contexto, "Consulta técnica informativa",
        incompatible, tipo_consulta="consulta_tecnica", slot_gemini_preconcedido=True,
    )
    assert "pastillas" not in texto
    assert "frenos" not in texto
    assert "información suficientemente verificada" in texto
    assert meta["modo"] == "consulta_tecnica_degradada"


@pytest.mark.anyio
@pytest.mark.parametrize("contexto", ["", "No busco información de frenos.",
                                      'Antes dijo "purgar frenos".', "Antes hablamos de frenos."])
async def test_worker_degradado_no_entrega_documento_incompatible(monkeypatch, contexto):
    from src.config import settings
    from src.core.gemini_queue.models import SolicitudGeminiEncolada
    from src.core.gemini_queue.rate_limiter import GeminiRateLimiter
    from src.core.gemini_queue.worker_processor import procesar_solicitud_encolada

    monkeypatch.setattr(settings.database, "enabled", False)
    solicitud = SolicitudGeminiEncolada(
        sintoma="Reaprendizaje de cuerpo de aceleración. " + contexto,
        diagnostico_ml="Consulta técnica informativa", confianza_ml=0,
        contexto_manual="Purgar frenos y revisar pastillas.", titulo_manual="Frenos",
        tipo_consulta="consulta_tecnica",
    )
    texto, meta = await procesar_solicitud_encolada(solicitud, GeminiRateLimiter(), forzar_degradado=True)
    assert "pastillas" not in texto
    assert "frenos" not in texto
    assert meta["modo"] == "consulta_tecnica_degradada"


@pytest.mark.anyio
async def test_consulta_de_memoria_no_se_desvia_a_proveedor_informativo():
    from src.core.services.webhook.consulta_informativa import responder_consulta_informativa

    resultado = await responder_consulta_informativa(
        None, None, None, None,
        "¿Qué síntomas tienes registrados? No generes otro diagnóstico.",
        "memoria-prueba", "sintetico", "meta",
    )
    assert resultado is None
