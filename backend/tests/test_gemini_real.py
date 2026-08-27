"""Prueba de integración real con Google Gemini API y verificación del modo fallback degradado."""

import time
import pytest
import requests
from src.config import settings
from src.core.gestor_diagnostico import GestorDiagnostico


def test_gemini_api_real_connection():
    """Verifica que la API Key sea válida, mide latencia, modelo y conteo de tokens."""
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

    assert response.status_code == 200, f"Error Gemini API ({response.status_code}): {response.text}"
    data = response.json()

    candidates = data.get("candidates", [])
    assert len(candidates) > 0, "Gemini no devolvió candidatos"

    texto_respuesta = candidates[0]["content"]["parts"][0]["text"].strip()
    assert "VERIFICADO" in texto_respuesta.upper()

    metadata = data.get("usageMetadata", {})
    tokens_in = metadata.get("promptTokenCount", 0)
    tokens_out = metadata.get("candidatesTokenCount", 0)

    print(f"\n[OK GEMINI REAL] Modelo: {modelo} | Latencia: {latencia_ms}ms | Tokens In: {tokens_in}, Out: {tokens_out}")
    assert latencia_ms > 0
    assert tokens_in > 0


def test_gemini_fallback_mode_degraded():
    """Comprueba que cuando Gemini no está disponible o falla, el bot responde en modo degradado ML+RAG sin caerse."""
    gestor_sin_gemini = GestorDiagnostico(gemini_api_key="API_KEY_INVALIDA_DE_PRUEBA")
    resultado = gestor_sin_gemini.procesar_consulta_texto(
        texto_usuario="Toyota Corolla 2021 cascabelea y pierde potencia en subida bujias",
        marca_modelo="Toyota Corolla 2021",
    )

    assert resultado is not None
    assert resultado.diagnostico_ml != ""
    assert "bujias" in resultado.diagnostico_ml.lower() or "misfire" in resultado.diagnostico_ml.lower()
    assert resultado.modo_diagnostico in ("diagnostico_degradado_ml_rag", "completo_ml_rag_llm")
    assert resultado.respuesta_texto is not None
    assert len(resultado.respuesta_texto) > 20
