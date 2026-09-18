"""Pruebas unitarias de las optimizaciones de latencia y rendimiento de la cola Gemini."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.gemini_queue.models import SolicitudGeminiEncolada
from src.core.gemini_queue.rate_limiter import GeminiRateLimiter
from src.core.gemini_queue.worker_processor import (
    _obtener_http_session_gemini,
    procesar_solicitud_encolada,
)


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

    with patch.object(_obtener_http_session_gemini(), "post", side_effect=mock_post):
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

    with patch.object(_obtener_http_session_gemini(), "post", side_effect=mock_post):
        texto, meta = await procesar_solicitud_encolada(solicitud_info, limiter)

    assert payload_capturado.get("generationConfig", {}).get("maxOutputTokens") == 140
    assert meta.get("modo") == "consulta_tecnica"


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
