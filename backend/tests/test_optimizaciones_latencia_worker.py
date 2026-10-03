"""Pruebas unitarias de las optimizaciones de latencia y rendimiento de la cola Gemini."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

from src.config import settings
from src.core.gemini_queue.models import SolicitudGeminiEncolada
from src.core.gemini_queue.rate_limiter import GeminiRateLimiter
from src.core.gemini_queue.worker_processor import (
    _obtener_http_session_gemini,
    procesar_solicitud_encolada,
)
from src.core.gestor_diagnostico import GestorDiagnostico


def test_pool_http_session_gemini_es_singleton_y_reutiliza_sockets():
    """El pool HTTP debe devolver siempre la misma instancia configurada."""
    sess1 = _obtener_http_session_gemini()
    sess2 = _obtener_http_session_gemini()

    assert sess1 is sess2
    # Verificar adaptadores con pool de conexiones
    adapter = sess1.get_adapter("https://generativelanguage.googleapis.com")
    assert adapter is not None
    assert adapter._pool_connections >= 10
    assert adapter._pool_maxsize >= 10


@pytest.mark.anyio
async def test_tokens_de_salida_ajustados_para_latencia():
    """Verifica que el payload enviado a Gemini configure los tokens óptimos."""
    limiter = GeminiRateLimiter(max_por_minuto=15, max_por_dia=1500)
    solicitud_diag = SolicitudGeminiEncolada(
        sintoma="falla en encendido",
        diagnostico_ml="Falla en bujias o bobinas de encendido (misfire)",
        confianza_ml=0.85,
        contexto_manual="Manual RAG",
        titulo_manual="Manual Bujías",
        tipo_consulta="diagnostico",
    )

    payload_capturado = {}

    def mock_post(url, json=None, **kwargs):
        nonlocal payload_capturado
        payload_capturado = json or {}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "🛠️ **1. Posible Falla**\n\n📖 **2. Procedimiento**\n\n⏱️ **3. Tiempo**"}]}}],
            "usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 80},
        }
        return mock_resp

    with (
        patch.object(_obtener_http_session_gemini(), "post", side_effect=mock_post),
        patch.object(settings, "gemini_api_key", "ci_gemini_key"),
    ):
        texto, meta = await procesar_solicitud_encolada(solicitud_diag, limiter)

    assert payload_capturado.get("generationConfig", {}).get("maxOutputTokens") == 420
    assert meta.get("usado") is True
    assert meta.get("modo") == "completo_ml_rag_llm"


@pytest.mark.anyio
async def test_consulta_tecnica_tokens_reducidos_a_140():
    """Verifica que para consultas informativas maxOutputTokens sea 140."""
    limiter = GeminiRateLimiter(max_por_minuto=15, max_por_dia=1500)
    solicitud_info = SolicitudGeminiEncolada(
        sintoma="¿qué presión de aceite lleva un Corolla 1.8?",
        diagnostico_ml="Consulta técnica informativa",
        confianza_ml=0.0,
        contexto_manual="Manual Corolla",
        titulo_manual="Manual Motor Corolla",
        tipo_consulta="consulta_tecnica",
    )

    payload_capturado = {}

    def mock_post(url, json=None, **kwargs):
        nonlocal payload_capturado
        payload_capturado = json or {}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Orientación general: 29-43 psi a 3000 RPM."}]}}],
            "usageMetadata": {"promptTokenCount": 40, "candidatesTokenCount": 20},
        }
        return mock_resp

    with (
        patch.object(_obtener_http_session_gemini(), "post", side_effect=mock_post),
        patch.object(settings, "gemini_api_key", "ci_gemini_key"),
    ):
        texto, meta = await procesar_solicitud_encolada(solicitud_info, limiter)

    assert payload_capturado.get("generationConfig", {}).get("maxOutputTokens") == 140
    assert meta.get("modo") == "consulta_tecnica"


@pytest.mark.anyio
async def test_timeout_de_gemini_usa_groq_sin_enviar_whatsapp():
    """Simula timeout local: Groq responde y no se toca DB ni WhatsApp."""
    limiter = GeminiRateLimiter(max_por_minuto=15, max_por_dia=1500)
    solicitud = SolicitudGeminiEncolada(
        sintoma="sensor de oxígeno con mezcla pobre",
        diagnostico_ml="Mezcla pobre en sistema de inyección",
        confianza_ml=0.82,
        contexto_manual="Verificar señal de sonda lambda y presión de combustible.",
        titulo_manual="Manual Inyección",
    )
    timeout_capturado = {}

    def gemini_lento(*_args, **kwargs):
        timeout_capturado["segundos"] = kwargs["timeout"]
        raise requests.Timeout("simulación aislada de Gemini lento")

    def groq_local(_prompt_sistema, *, tipo_consulta="diagnostico"):
        assert tipo_consulta == "diagnostico"
        return "Respuesta simulada de Groq para mezcla pobre.", {
            "usado": True,
            "modelo": "modelo-prueba",
            "proveedor": "groq",
            "modo": "completo_ml_rag_llm",
            "tokens_entrada": 1,
            "tokens_salida": 1,
        }

    with (
        patch.object(_obtener_http_session_gemini(), "post", side_effect=gemini_lento),
        patch.object(settings, "gemini_api_key", "clave-solo-prueba"),
        patch.object(settings, "gemini_timeout_seconds", 7),
        patch.object(settings, "groq_api_key", "clave-solo-prueba"),
        patch.object(settings, "groq_chat_enabled", True),
        patch.object(settings.database, "enabled", False),
        patch("src.core.gemini_queue.worker_processor.generar_respuesta_groq", side_effect=groq_local),
    ):
        texto, meta = await procesar_solicitud_encolada(solicitud, limiter)

    assert timeout_capturado["segundos"] == 7
    assert texto == "Respuesta simulada de Groq para mezcla pobre."
    assert meta["proveedor"] == "groq"
    assert meta["usado"] is True


def test_generador_directo_respeta_timeout_configurable_de_gemini(monkeypatch):
    """El flujo directo local comparte el mismo límite antes de pasar a Groq."""
    gestor = GestorDiagnostico(gemini_api_key="clave-solo-prueba")
    capturado = {}

    def gemini_lento(_url, **kwargs):
        capturado["timeout"] = kwargs["timeout"]
        raise requests.Timeout("simulación aislada")

    def groq_local(_prompt_sistema, *, tipo_consulta="diagnostico"):
        return "Respuesta local simulada.", {
            "usado": True,
            "modelo": "modelo-prueba",
            "proveedor": "groq",
            "modo": "completo_ml_rag_llm",
            "tokens_entrada": 0,
            "tokens_salida": 0,
        }

    monkeypatch.setattr(gestor._http_session, "post", gemini_lento)
    monkeypatch.setattr(settings, "gemini_timeout_seconds", 7)
    monkeypatch.setattr(settings, "groq_api_key", "clave-solo-prueba")
    monkeypatch.setattr(settings, "groq_chat_enabled", True)
    monkeypatch.setattr("src.core.diagnostico.response_generator.generar_respuesta_groq", groq_local)

    texto, meta = gestor._generar_respuesta_con_metadatos(
        pregunta="mezcla pobre con P0171",
        diagnostico_ml="Falla de inyección",
        contexto_manual="Comprobar combustible.",
    )

    assert capturado["timeout"] == 7
    assert texto == "Respuesta local simulada."
    assert meta["proveedor"] == "groq"


@pytest.mark.anyio
async def test_forzar_degradado_genera_respuesta_ml_rag_inmediata_sin_api():
    """Cuando forzar_degradado es True, responde de inmediato sin consumir API."""
    limiter = GeminiRateLimiter(max_por_minuto=15, max_por_dia=1500)
    solicitud = SolicitudGeminiEncolada(
        sintoma="motor no arranca",
        diagnostico_ml="Bateria descargada o bornes sulfatados",
        confianza_ml=0.88,
        contexto_manual="Comprobar voltaje de reposo 12.6V",
        titulo_manual="Manual Eléctrico",
    )

    texto, meta = await procesar_solicitud_encolada(solicitud, limiter, forzar_degradado=True)

    assert meta.get("usado") is False
    assert meta.get("modo") == "diagnostico_degradado_ml_rag"
    assert "Posible Falla Vehicular" in texto
    assert "Modo Degradado ML+RAG" in texto
    assert "Procedimiento Técnico de Reparación" in texto
    assert "Tiempo Estimado y Gravedad" in texto
    assert "Bateria descargada o bornes sulfatados" in texto


@pytest.mark.anyio
async def test_despacho_outbox_inmediato_tras_persistir():
    """Verifica que al terminar el procesamiento se invoque de inmediato el despacho a WhatsApp."""
    limiter = GeminiRateLimiter(max_por_minuto=15, max_por_dia=1500)
    solicitud = SolicitudGeminiEncolada(
        sintoma="frenos chillan",
        diagnostico_ml="Desgaste de pastillas y zapatas de freno",
        confianza_ml=0.9,
        contexto_manual="Inspección visual de pastillas",
        titulo_manual="Manual Frenos",
        conversacion_id="conv_123",
    )

    with (
        patch("src.config.settings.database.enabled", True),
        patch("src.core.gemini_queue.worker_processor.actualizar_diagnostico_y_trabajo_db", new_callable=AsyncMock),
        patch("src.core.gemini_queue.worker_processor.persistir_mensaje_saliente_db", new_callable=AsyncMock) as mock_persist,
        patch("src.core.gemini_queue.db_persistence.procesar_siguiente_entrega_whatsapp", new_callable=AsyncMock) as mock_entrega,
    ):
        await procesar_solicitud_encolada(solicitud, limiter, forzar_degradado=True)

        mock_persist.assert_called_once()
        mock_entrega.assert_called_once()


def test_rate_limiter_respeto_ventana_rpm():
    """El rate limiter concede hasta max_por_minuto y luego rechaza."""
    limiter = GeminiRateLimiter(max_por_minuto=3, max_por_dia=100)
    assert limiter.intentar_adquirir_slot() is True
    assert limiter.intentar_adquirir_slot() is True
    assert limiter.intentar_adquirir_slot() is True
    assert limiter.intentar_adquirir_slot() is False
