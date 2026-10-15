"""Regresiones de las pérdidas de contratos durante la integración local."""

import subprocess
import sys
from types import SimpleNamespace

import pytest

from src.core.conversacion.presentacion_dto import alinear_predicciones_presentadas
from src.core.diagnostico.models import ResultadoDiagnostico
from src.infrastructure.rag_checks.frozen_integrity import FrozenRAGMismatch, validar_espacio_congelado


def test_motor_rag_puede_importarse_sin_orden_previo_de_imports():
    resultado = subprocess.run(
        [sys.executable, "-c", "from src.infrastructure.motor_rag import MotorRAG"],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert resultado.returncode == 0, resultado.stderr


@pytest.mark.parametrize("dimension,count", [(4, 2), (3, 1)])
def test_indice_incompatible_no_autoriza_busqueda(dimension, count):
    vectorizer = SimpleNamespace(get_feature_names_out=lambda: ["a", "b", "c"])
    with pytest.raises(FrozenRAGMismatch, match="No se reconstruirá"):
        validar_espacio_congelado(SimpleNamespace(d=dimension, ntotal=count), vectorizer, 2)


def test_abstencion_no_filtra_svm_original_ni_muta_dto():
    dto = ResultadoDiagnostico(
        respuesta_texto="Sin hipótesis compatible", diagnostico_ml="Válvula IAC sucia",
        confianza_ml=0.98, contexto_manual="", titulo_manual="",
        predicciones_ml=[{"falla": "Válvula IAC sucia", "probabilidad": 0.98}],
    )
    presentado = alinear_predicciones_presentadas(dto, [])
    assert presentado.predicciones_ml == []
    assert presentado.predicciones_ml_raw[0].probabilidad == 0.98
    assert dto.predicciones_ml[0].falla == "Válvula IAC sucia"


@pytest.mark.parametrize("respuesta", ["No es JSON", '{"hipotesis":"Termostato"}'])
def test_groq_no_entrega_respuesta_sin_validar(monkeypatch, respuesta):
    from src.config import settings
    from src.core.diagnostico.response_generator import generar_respuesta_con_metadatos

    monkeypatch.setattr(settings, "groq_api_key", "clave-sintetica")
    monkeypatch.setattr(settings, "groq_chat_enabled", True)
    monkeypatch.setattr(
        "src.core.diagnostico.response_generator.generar_respuesta_groq",
        lambda *args, **kwargs: (respuesta, {"usado": True, "proveedor": "groq"}),
    )
    texto, metadatos = generar_respuesta_con_metadatos(
        SimpleNamespace(api_key=""), "Falla de encendido", "Bobina defectuosa", "",
    )
    assert texto != respuesta
    assert not metadatos.get("usado")


@pytest.mark.parametrize("mensaje", [
    "No tengo escáner para saber qué código arroja.",
    "El motor nunca está caliente.",
])
def test_evidencia_taller_no_confirma_herramienta_o_temperatura_negadas(mensaje):
    from src.core.conversacion.evidencia_taller import registrar_evidencia
    from src.core.conversacion.models import ConversationState

    estado = ConversationState(session_id="negaciones-taller")
    registrar_evidencia(estado, mensaje)
    assert estado.obtener_valor_confirmado("escaner_disponible") is None
    assert estado.obtener_valor_confirmado("temperatura") is None


@pytest.mark.parametrize("clase", ["LoginAttemptStore", "RefreshTokenStore"])
def test_redis_async_no_reutiliza_conexion_entre_event_loops(monkeypatch, clase):
    import asyncio

    from src.core.login_attempt_store import LoginAttemptStore
    from src.core.refresh_token_store import RefreshTokenStore

    llamadas = []

    def nuevo_cliente(*args, **kwargs):
        cliente = object()
        llamadas.append(cliente)
        return cliente

    monkeypatch.setattr("redis.asyncio.Redis.from_url", nuevo_cliente)
    store = {"LoginAttemptStore": LoginAttemptStore, "RefreshTokenStore": RefreshTokenStore}[clase]()

    async def cliente_del_loop():
        cliente = store._cliente_redis()
        assert cliente is store._cliente_redis()
        return cliente

    primero = asyncio.run(cliente_del_loop())
    segundo = asyncio.run(cliente_del_loop())
    assert primero is not segundo
    assert len(llamadas) == 2
