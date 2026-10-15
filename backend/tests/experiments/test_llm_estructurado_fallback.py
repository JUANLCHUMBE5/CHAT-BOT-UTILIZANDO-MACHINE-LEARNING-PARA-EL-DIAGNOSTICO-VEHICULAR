"""Contrato JSON y fallback determinista sin llamadas externas."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.config import settings
from src.core.diagnostico.response_generator import generar_respuesta_con_metadatos
from src.core.diagnostico.respuesta_llm_estructurada import validar_y_formatear
from src.core.gemini_queue import gemini_rate_limiter


def _respuesta(texto):
    return SimpleNamespace(
        status_code=200,
        json=lambda: {"candidates": [{"content": {"parts": [{"text": texto}]}}]},
    )


def _gestor(respuestas):
    return SimpleNamespace(
        api_key="clave-ficticia-local",
        _http_session=SimpleNamespace(post=MagicMock(side_effect=respuestas)),
    )


def _invocar(gestor):
    return generar_respuesta_con_metadatos(
        gestor, pregunta="Nissan Versa con mezcla pobre", diagnostico_ml="Mezcla por revisar",
        contexto_manual="", confianza_ml=0.39, proveedor="api",
    )


def test_json_valido_renderiza_campos_y_tope():
    texto = json.dumps({
        "hipotesis": "información insuficiente",
        "explicacion": "No hay medición confirmatoria.",
        "siguiente_prueba": "Medir presión de combustible según manual aplicable.",
        "pregunta": "¿Tienes el resultado?",
    })
    assert "información insuficiente" in validar_y_formatear(texto)
    with pytest.raises(ValueError):
        validar_y_formatear("respuesta libre sin JSON")
    with pytest.raises(ValueError):
        validar_y_formatear(json.dumps({"hipotesis": "X"}))


def test_gemini_json_invalido_reintenta_y_degrada(monkeypatch):
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    monkeypatch.setattr(gemini_rate_limiter, "intentar_adquirir_slot", lambda: True)
    monkeypatch.setattr(gemini_rate_limiter, "registrar_estado_gemini", lambda **_: None)
    gestor = _gestor([_respuesta("no JSON"), _respuesta("sigue inválido")])
    texto, meta = _invocar(gestor)
    assert gestor._http_session.post.call_count == 2
    assert not meta["usado"]
    assert texto


def test_gemini_json_valido_usa_proveedor_y_registra_exito(monkeypatch):
    estados = []
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    monkeypatch.setattr(gemini_rate_limiter, "intentar_adquirir_slot", lambda: True)
    monkeypatch.setattr(gemini_rate_limiter, "registrar_estado_gemini", lambda **kwargs: estados.append(kwargs))
    gestor = _gestor([_respuesta(json.dumps({
        "hipotesis": "Revisar alimentación de combustible",
        "explicacion": "La mezcla pobre requiere una medición confirmatoria.",
        "siguiente_prueba": "Medir presión de combustible según la especificación del vehículo.",
        "pregunta": "¿Tienes el valor de presión?",
    }))])
    texto, meta = _invocar(gestor)
    assert meta["usado"] is True
    assert meta["proveedor"] == "gemini"
    assert "presión de combustible" in texto
    assert gestor._http_session.post.call_count == 1
    assert estados == [{"exitoso": True, "codigo_http": 200}]


def test_gemini_timeout_degrada_sin_dejar_sin_respuesta(monkeypatch):
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    monkeypatch.setattr(gemini_rate_limiter, "intentar_adquirir_slot", lambda: True)
    monkeypatch.setattr(gemini_rate_limiter, "registrar_estado_gemini", lambda **_: None)
    gestor = _gestor([TimeoutError("timeout local simulado")])
    texto, meta = _invocar(gestor)
    assert not meta["usado"]
    assert texto
