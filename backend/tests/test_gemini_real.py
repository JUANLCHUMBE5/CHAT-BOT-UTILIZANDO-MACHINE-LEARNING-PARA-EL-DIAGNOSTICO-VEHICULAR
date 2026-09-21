"""Integración opcional con Gemini y verificación determinista del fallback."""

import os
import time

import pytest
import requests

from src.config import settings
from src.core.gemini_queue import gemini_rate_limiter
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.real_gemini
@pytest.mark.skipif(
    os.getenv("RUN_REAL_GEMINI_TESTS") != "1",
    reason="Prueba externa desactivada; usar RUN_REAL_GEMINI_TESTS=1 para ejecutarla.",
)
def test_gemini_api_real_connection():
    """Verifica bajo demanda la API key, latencia, modelo y tokens reales."""
    api_key = settings.gemini_api_key
    assert api_key and api_key != "tu_api_key_aqui", "API Key de Gemini no configurada"

    modelo = settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    payload = {
        "contents": [{"parts": [{"text": "Responde exactamente la palabra: VERIFICADO"}]}]
    }

    t0 = time.perf_counter()
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    latencia_ms = int((time.perf_counter() - t0) * 1000)
    gemini_rate_limiter.registrar_estado_gemini(
        exitoso=response.status_code == 200,
        codigo_http=response.status_code,
        error=None if response.status_code == 200 else f"Gemini HTTP {response.status_code}",
    )

    assert response.status_code == 200, f"Error Gemini API ({response.status_code}): {response.text}"
    data = response.json()
    candidates = data.get("candidates", [])
    assert candidates, "Gemini no devolvió candidatos"

    texto_respuesta = candidates[0]["content"]["parts"][0]["text"].strip()
    assert "VERIFICADO" in texto_respuesta.upper()

    metadata = data.get("usageMetadata", {})
    tokens_in = metadata.get("promptTokenCount", 0)
    tokens_out = metadata.get("candidatesTokenCount", 0)
    print(
        f"\n[OK GEMINI REAL] Modelo: {modelo} | Latencia: {latencia_ms}ms "
        f"| Tokens In: {tokens_in}, Out: {tokens_out}"
    )
    assert latencia_ms > 0
    assert tokens_in > 0


def test_gemini_fallback_mode_degraded(monkeypatch):
    """Comprueba sin red que un fallo de Gemini activa el fallback ML+RAG."""
    gestor_sin_gemini = GestorDiagnostico(gemini_api_key="API_KEY_INVALIDA_DE_PRUEBA")

    class RespuestaGeminiNoDisponible:
        status_code = 503

    monkeypatch.setattr(
        gestor_sin_gemini._http_session,
        "post",
        lambda *args, **kwargs: RespuestaGeminiNoDisponible(),
    )
    resultado = gestor_sin_gemini.procesar_consulta_texto(
        texto_usuario="Toyota Corolla 2021 cascabelea y pierde potencia en subida bujias",
        marca_modelo="Toyota Corolla 2021",
    )

    assert resultado is not None
    assert resultado.diagnostico_ml != ""
    assert "bujias" in resultado.diagnostico_ml.lower() or "misfire" in resultado.diagnostico_ml.lower()
    assert resultado.modo_diagnostico == "diagnostico_degradado_ml_rag"
    assert resultado.respuesta_texto is not None
    assert len(resultado.respuesta_texto) > 20
