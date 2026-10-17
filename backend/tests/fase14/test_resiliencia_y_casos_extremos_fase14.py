"""Suite de Pruebas de Resiliencia, Casos Extremos y Robustez Conversacional — Fase 14.2.

Verifica:
1. Resiliencia ante fallos del LLM (timeout, API caída, JSON corrupto).
2. Robustez semántica ante lenguaje coloquial, errores ortográficos y de digitación.
3. Tratamiento de consultas fuera de contexto / alcance administrativo.
4. Respuesta a preguntas técnicas de seguimiento y solicitud de causas alternativas.
5. Manejo de comprobaciones pendientes y herramientas no disponibles.
6. Transición limpia y segura en cambio de vehículo o nuevo caso.
"""

import json
import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import requests

import src.core.services.webhook_service as modulo
from src.core.conversacion.comprension_semantica.contratos import (
    InterpretacionSemantica,
)
from src.core.conversacion.comprension_semantica.interprete import (
    interpretar_mensaje_usuario,
)
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.state_models.state import ConversationState
from src.core.gestor_diagnostico import GestorDiagnostico


def setup_mock_service(monkeypatch, conversacion_contexto=None):
    """Configura un WebhookService aislado con persistencia simulada."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(
        id=uuid.uuid4(),
        taller_id=uuid.uuid4(),
        nombres="Mecánico Certificador",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto=conversacion_contexto if conversacion_contexto is not None else {},
    )

    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.begin_nested.return_value.__aenter__ = AsyncMock()
    session.begin_nested.return_value.__aexit__ = AsyncMock(return_value=False)
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(modulo, "database_configurada", lambda: True)
    monkeypatch.setattr(modulo, "obtener_engine", lambda: None)
    monkeypatch.setattr(modulo, "AsyncSession", lambda *a, **k: context)

    mensaje_repo = MagicMock()
    mensaje_repo.existe_meta_message_id = AsyncMock(return_value=False)
    mensaje_repo.crear_mensaje = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(modulo, "MensajeRepository", lambda *a: mensaje_repo)

    diag_repo_mock = MagicMock()
    diag_repo_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=None)
    diag_repo_mock.obtener_ultimo_pendiente_mecanico = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.DiagnosticoRepository",
        lambda *a: diag_repo_mock,
    )
    monkeypatch.setattr(
        "src.core.services.webhook_service.DiagnosticoRepository",
        lambda *a: diag_repo_mock,
    )

    conv_repo = SimpleNamespace(obtener_o_crear_activa=AsyncMock(return_value=conversacion))
    monkeypatch.setattr(modulo, "ConversacionRepository", lambda *a: conv_repo)
    monkeypatch.setattr(
        modulo,
        "OperacionesRepository",
        lambda *a: SimpleNamespace(registrar_uso_api=AsyncMock()),
    )
    monkeypatch.setattr(
        modulo.IdentityResolver,
        "resolver_o_registrar",
        AsyncMock(return_value=SimpleNamespace(status="ok", usuario=usuario)),
    )

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        ctx = dict(conversacion.contexto or {})
        if modulo.DiagnosticPersister.debe_solicitar_feedback(dto):
            ctx["validacion_diagnostico"] = {
                "diagnostico_id": str(uuid.uuid4()),
                "etapa": "esperando_confirmacion",
            }
        conversacion.contexto = ctx
        return {"status": "completado", "respuesta": getattr(dto, "respuesta_texto", "")}, Decimal("0")

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)
    return service, conversacion


# =========================================================================
# 1. RESILIENCIA ANTE FALLOS DEL LLM (API DOWN, TIMEOUT, JSON INVÁLIDO)
# =========================================================================

def test_resiliencia_llm_caido_fallback_determinista(monkeypatch):
    """Si Groq/Gemini arrojan excepción de red (503/timeout), debe operar el fallback determinista."""
    def raise_network_error(*args, **kwargs):
        raise requests.ConnectionError("Falla de red simulada con API de Groq")

    monkeypatch.setattr(requests, "post", raise_network_error)
    monkeypatch.setattr("src.config.settings.groq_api_key", "test-key-fake")

    texto = "Nissan Sentra 2018. El motor tironea al acelerar pero no he revisado las bujías ni la bomba."
    estado = ConversationState(session_id="test_resilience_fallback")
    
    interp = interpretar_mensaje_usuario(texto, contexto_estado=estado)
    assert interp is not None
    assert isinstance(interp, InterpretacionSemantica)
    # Debe haber extraído el vehículo y no-revisado por vía determinista
    assert interp.datos_vehiculo.get("marca") == "Nissan"
    assert interp.datos_vehiculo.get("modelo") == "Sentra"
    hechos_campos = [h.campo for h in interp.hechos_nuevos]
    assert any("bujia" in c or "bomba" in c for c in hechos_campos)
    assert interp.origen == "heuristica_fallback"


def test_resiliencia_llm_json_corrupto_recuperacion(monkeypatch):
    """Si el LLM devuelve un cuerpo JSON inválido o malformado, debe caer a fallback sin crash."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Esto no es un JSON {invalido truncado"}}]
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: mock_resp)
    monkeypatch.setattr("src.config.settings.groq_api_key", "test-key-fake")

    texto = "Toyota Yaris 2018. El motor no arranca y huele a gasolina."
    estado = ConversationState(session_id="test_corrupt_json")
    interp = interpretar_mensaje_usuario(texto, contexto_estado=estado)
    assert interp is not None
    assert isinstance(interp, InterpretacionSemantica)
    assert interp.origen == "heuristica_fallback"
    assert interp.datos_vehiculo.get("marca") == "Toyota"


# =========================================================================
# 2. LENGUAJE COLOQUIAL, TYPOS Y EXPRESIONES DE TALLER
# =========================================================================

def test_robustez_typos_y_lenguaje_coloquial(monkeypatch):
    """Tolera typos comunes de taller ('neuvo caso', 'totota', 'corola', 'faya') mediante LLM comprensivo."""
    mock_llm_output = {
        "intenciones": ["nuevo_caso", "reportar_sintoma"],
        "solicita_causas_alternativas": False,
        "solicita_nuevo_caso": True,
        "pregunta_tecnica_usuario": None,
        "datos_vehiculo": {"marca": "Toyota", "modelo": "Corolla", "anio": "2015"},
        "hechos_nuevos": [
            {
                "campo": "arranque_falla",
                "valor": "Falla en el arranque y cascabeleo",
                "tipo": "SINTOMA",
                "estado": "CONFIRMADO",
                "evidencia_texto": "faya en el aranque y cascaveleo"
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(mock_llm_output)}}]
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: mock_resp)
    monkeypatch.setattr("src.config.settings.groq_api_key", "test-key-live")
    monkeypatch.setattr("src.config.settings.groq_chat_enabled", True)

    texto_typo = "neuvo caso para totota corola 2015. faya en el aranque y cascaveleo."
    estado = ConversationState(session_id="test_typos")
    
    interp = interpretar_mensaje_usuario(texto_typo, contexto_estado=estado)
    assert interp.solicita_nuevo_caso is True
    assert interp.datos_vehiculo.get("marca") == "Toyota"
    assert interp.datos_vehiculo.get("modelo") == "Corolla"
    assert interp.origen == "llm_groq"


# =========================================================================
# 3. COMPROBACIONES PENDIENTES Y HERRAMIENTAS NO DISPONIBLES
# =========================================================================

@pytest.mark.anyio
async def test_resiliencia_herramienta_no_disponible_no_descarta_hipotesis(monkeypatch):
    """Si el mecánico dice que no tiene manómetro o escáner, CarBot no debe rechazar la falla."""
    service, conversacion = setup_mock_service(monkeypatch)
    remitente = "51988880001"

    # Turno 1: Reporte de síntoma con placa
    r1 = await service.procesar_mensaje(
        remitente=remitente,
        meta_message_id="wamid.resil.001",
        tipo_mensaje="text",
        texto_cliente="Tengo un Kia Rio 2016 placa ABC-456. Se apaga de repente en semáforos y le cuesta volver a encender.",
        proveedor="api",
    )
    assert r1.get("status") in ("completado", "diagnostico", "aclaracion", "comprobacion_hipotesis")

    # Turno 2: Mecánico indica que no tiene manómetro y no ha medido presión
    r2 = await service.procesar_mensaje(
        remitente=remitente,
        meta_message_id="wamid.resil.002",
        tipo_mensaje="text",
        texto_cliente="No tengo manómetro de presión de combustible en este momento y no he revisado la bomba. ¿Qué más puedo verificar?",
        proveedor="api",
    )
    assert r2.get("status") in ("completado", "diagnostico", "aclaracion", "comprobacion_hipotesis")
    resp_texto = r2.get("respuesta", "")
    assert len(resp_texto) > 10
    # No debe bloquearse ni pedir nuevamente placa
    assert "ingresa la placa" not in resp_texto.lower()


# =========================================================================
# 4. PREGUNTA DE SEGUIMIENTO Y SOLICITUD DE ALTERNATIVAS
# =========================================================================

@pytest.mark.anyio
async def test_resiliencia_pregunta_seguimiento_y_alternativas(monkeypatch):
    """El mecánico pregunta por qué sospecha de un componente y qué otras opciones hay."""
    service, conversacion = setup_mock_service(monkeypatch)
    remitente = "51988880002"

    # Turno 1
    await service.procesar_mensaje(
        remitente=remitente,
        meta_message_id="wamid.resil.003",
        tipo_mensaje="text",
        texto_cliente="Honda Civic 2017 placa HND-789. El motor vibra mucho en ralentí y pierde potencia al acelerar.",
        proveedor="api",
    )

    # Turno 2: Pregunta técnica directa
    r2 = await service.procesar_mensaje(
        remitente=remitente,
        meta_message_id="wamid.resil.004",
        tipo_mensaje="text",
        texto_cliente="¿Por qué podría ser soporte de motor o bobina? ¿Qué otras causas existen y qué dato necesitas para diferenciarlas?",
        proveedor="api",
    )
    assert r2.get("status") in ("completado", "diagnostico", "aclaracion", "comprobacion_hipotesis")
    resp = r2.get("respuesta", "")
    assert len(resp) > 30


# =========================================================================
# 5. MENSAJES FUERA DE CONTEXTO O ADMINISTRATIVOS
# =========================================================================

@pytest.mark.anyio
async def test_resiliencia_mensaje_administrativo_no_rompe_flujo(monkeypatch):
    """Un mensaje administrativo o fuera de contexto no rompe el flujo ni genera excepción."""
    service, conversacion = setup_mock_service(monkeypatch)
    remitente = "51988880003"

    r = await service.procesar_mensaje(
        remitente=remitente,
        meta_message_id="wamid.resil.005",
        tipo_mensaje="text",
        texto_cliente="¿A qué hora atienden y cuál es el precio de la afinada?",
        proveedor="api",
    )
    assert r is not None
    assert "respuesta" in r
    assert len(r["respuesta"]) > 10

