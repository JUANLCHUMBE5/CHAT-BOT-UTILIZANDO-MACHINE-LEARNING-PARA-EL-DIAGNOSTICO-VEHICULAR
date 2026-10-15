"""Gate del webhook real con identidad, persistencia y envío sustituidos en memoria."""

import json
import os
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.services import webhook_service as modulo
from src.infrastructure.motor_rag import _consulta_indica_fuga_refrigerante

WEBHOOK_TRACE = []


@pytest.mark.parametrize(
    ("consulta", "esperada"),
    [
        ("El motor se recalienta y pierde refrigerante", True),
        ("Recalienta y deja una mancha en el piso", True),
        ("Recalienta pero no hay fuga de refrigerante", False),
        ("Recalienta pero no pierde agua", False),
    ],
)
def test_detector_fuga_refrigerante_respeta_negaciones(consulta, esperada):
    assert _consulta_indica_fuga_refrigerante(consulta) is esperada


@pytest.mark.anyio
@pytest.mark.parametrize("sintoma", ["El auto recalienta", "El motor se calienta y pierde refrigerante"])
async def test_placa_sintoma_cancelar_nueva_placa_sin_bd_ni_envio(monkeypatch, sintoma):
    gestor = GestorDiagnostico()
    WEBHOOK_TRACE.clear()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    gestor._registrar_en_tracker = lambda **_: None
    monkeypatch.setattr(modulo.settings, "gemini_api_key", "")
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")
    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Prueba aislada",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(id=uuid.uuid4(), contexto={})
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.begin_nested.return_value.__aenter__ = AsyncMock()
    session.begin_nested.return_value.__aexit__ = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock()
    monkeypatch.setattr(modulo, "database_configurada", lambda: True)
    monkeypatch.setattr(modulo, "obtener_engine", lambda: None)
    monkeypatch.setattr(modulo, "AsyncSession", lambda *a, **k: context)
    mensaje_repo = MagicMock()
    mensaje_repo.existe_meta_message_id = AsyncMock(return_value=False)
    mensaje_repo.crear_mensaje = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(modulo, "MensajeRepository", lambda *a: mensaje_repo)
    conv_repo = SimpleNamespace(obtener_o_crear_activa=AsyncMock(return_value=conversacion))
    monkeypatch.setattr(modulo, "ConversacionRepository", lambda *a: conv_repo)
    monkeypatch.setattr(modulo, "OperacionesRepository", lambda *a: SimpleNamespace(registrar_uso_api=AsyncMock()))
    monkeypatch.setattr(
        modulo.IdentityResolver, "resolver_o_registrar",
        AsyncMock(return_value=SimpleNamespace(status="ok", usuario=usuario)),
    )
    monkeypatch.setattr(modulo.ValidationWorkflow, "manejar_flujo_validacion", AsyncMock(return_value=None))
    enviar = AsyncMock()
    monkeypatch.setattr(modulo.whatsapp_provider_service, "enviar", enviar)

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        WEBHOOK_TRACE.append({
            "caso": "refrigeracion_webhook_final",
            "titulo": dto.titulo_manual,
            "similitud": dto.similitud_rag,
            "contexto_presente": bool(dto.contexto_manual),
            "ml_confianza": dto.confianza_ml,
            "diagnostico": dto.diagnostico_ml,
            "llm_usado": dto.llm_usado,
        })
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    preparar = AsyncMock(wraps=modulo.TechnicalDiagnosticWorkflow.preparar)
    monkeypatch.setattr(modulo.TechnicalDiagnosticWorkflow, "preparar", preparar)

    recuperar_rag_original = gestor.motor_rag.recuperar_procedimiento_hibrido

    def recuperar_rag_observado(**kwargs):
        resultado = recuperar_rag_original(**kwargs)
        WEBHOOK_TRACE.append({
            "caso": "sistema_webhook",
            "consulta": kwargs.get("consulta", ""),
            "titulo": resultado[1],
            "similitud": resultado[2],
            "contexto_presente": bool(resultado[0]),
            "rag_falla": resultado[3].get("falla"),
            "rag_sistema": resultado[3].get("macro_sistema") or resultado[3].get("sistema"),
        })
        return resultado

    gestor.motor_rag.recuperar_procedimiento_hibrido = recuperar_rag_observado
    service = modulo.WebhookService(gestor)

    async def turno(texto):
        return await service.procesar_mensaje(
            remitente="local-ficticio", meta_message_id=f"local-{uuid.uuid4()}",
            texto_cliente=texto, proveedor="api", marca_modelo="Mazda 3 2019",
        )

    inicio = await turno(sintoma)
    assert inicio["status"] == "esperando_placa"
    assert conversacion.contexto["preplate_pending_input"] == sintoma
    invalida = await turno("!")
    assert invalida["status"] == "esperando_placa"
    assert "válida" in invalida["respuesta"]
    assert preparar.await_count == 0
    valida = await turno("ABC123")
    assert valida["status"] == "completado"
    assert preparar.await_count == 1
    assert preparar.call_args.args[6] == sintoma
    assert "preplate_pending_input" not in conversacion.contexto
    assert conversacion.contexto["conversation_state"]["active_system"] == "refrigeracion", (
        conversacion.contexto["conversation_state"]
    )
    followup = await turno("No es mezcla; el ventilador ya fue revisado")
    assert followup["status"] == "completado"
    assert conversacion.contexto["conversation_state"]["active_system"] == "refrigeracion", (
        conversacion.contexto["conversation_state"]
    )
    assert WEBHOOK_TRACE, "El hilo refrigeración/Mazda debía consultar el RAG local"
    if "pierde refrigerante" in sintoma.lower():
        turnos_finales = [
            entrada
            for entrada in WEBHOOK_TRACE
            if entrada.get("caso") == "refrigeracion_webhook_final"
        ]
        turno_fuga = turnos_finales[1]
        assert "FUGA EN SISTEMA DE ENFRIAMIENTO" in turno_fuga["titulo"], turno_fuga
        assert turno_fuga["contexto_presente"]
        assert turno_fuga["similitud"] > 0
        assert "Fuga en mangueras de refrigerante" in turno_fuga["diagnostico"]
    await turno("Cancelar")
    limpio = conversacion.contexto["conversation_state"]
    assert limpio["active_system"] is None
    assert not limpio["hechos"]
    await turno("XYZ789")
    assert conversacion.contexto["placa"] == "XYZ789"
    nuevo = await turno("El motor tiembla en ralentí")
    assert nuevo["status"] == "completado"
    assert conversacion.contexto["conversation_state"]["active_system"] == "encendido"
    # Todos los envíos y commits anteriores fueron exclusivamente AsyncMocks.
    assert enviar.await_count >= 3
    assert not session.rollback.await_count


@pytest.mark.anyio
async def test_versa_webhook_placa_y_contexto_llegan_a_diagnostico_sin_meta(monkeypatch):
    """El gate local conserva mezcla pobre y el siguiente dato activa ML/RAG."""
    gestor = GestorDiagnostico()
    WEBHOOK_TRACE.clear()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    gestor._registrar_en_tracker = lambda **_: None
    monkeypatch.setattr(modulo.settings, "gemini_api_key", "")
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")
    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Prueba Versa",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(id=uuid.uuid4(), contexto={})
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.begin_nested.return_value.__aenter__ = AsyncMock()
    session.begin_nested.return_value.__aexit__ = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock()
    monkeypatch.setattr(modulo, "database_configurada", lambda: True)
    monkeypatch.setattr(modulo, "obtener_engine", lambda: None)
    monkeypatch.setattr(modulo, "AsyncSession", lambda *a, **k: context)
    mensaje_repo = MagicMock()
    mensaje_repo.existe_meta_message_id = AsyncMock(return_value=False)
    mensaje_repo.crear_mensaje = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(modulo, "MensajeRepository", lambda *a: mensaje_repo)
    conv_repo = SimpleNamespace(obtener_o_crear_activa=AsyncMock(return_value=conversacion))
    monkeypatch.setattr(modulo, "ConversacionRepository", lambda *a: conv_repo)
    monkeypatch.setattr(
        modulo, "OperacionesRepository",
        lambda *a: SimpleNamespace(registrar_uso_api=AsyncMock()),
    )
    monkeypatch.setattr(
        modulo.IdentityResolver, "resolver_o_registrar",
        AsyncMock(return_value=SimpleNamespace(status="ok", usuario=usuario)),
    )
    monkeypatch.setattr(
        modulo.ValidationWorkflow, "manejar_flujo_validacion", AsyncMock(return_value=None),
    )
    enviar = AsyncMock()
    monkeypatch.setattr(modulo.whatsapp_provider_service, "enviar", enviar)

    dtos_persistidos = []

    async def persistir_local(**kwargs):
        dto = kwargs["dto"]
        dtos_persistidos.append(dto)
        WEBHOOK_TRACE.append({
            "caso": "versa_webhook_final",
            "titulo": dto.titulo_manual,
            "similitud": dto.similitud_rag,
            "contexto_presente": bool(dto.contexto_manual),
            "ml_confianza": dto.confianza_ml,
            "diagnostico": dto.diagnostico_ml,
            "llm_usado": dto.llm_usado,
        })
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(
        modulo.DiagnosticPersister,
        "persistir_y_responder",
        AsyncMock(side_effect=persistir_local),
    )
    preparar = AsyncMock(wraps=modulo.TechnicalDiagnosticWorkflow.preparar)
    monkeypatch.setattr(modulo.TechnicalDiagnosticWorkflow, "preparar", preparar)

    recuperar_rag_original = gestor.motor_rag.recuperar_procedimiento_hibrido

    def recuperar_rag_observado(**kwargs):
        resultado = recuperar_rag_original(**kwargs)
        WEBHOOK_TRACE.append({
            "caso": "versa",
            "consulta": kwargs.get("consulta", ""),
            "titulo": resultado[1],
            "similitud": resultado[2],
            "contexto_presente": bool(resultado[0]),
            "rag_falla": resultado[3].get("falla"),
            "rag_sistema": resultado[3].get("macro_sistema") or resultado[3].get("sistema"),
        })
        return resultado

    gestor.motor_rag.recuperar_procedimiento_hibrido = recuperar_rag_observado
    service = modulo.WebhookService(gestor)

    async def turno(texto):
        return await service.procesar_mensaje(
            remitente="local-versa-ficticio", meta_message_id=f"local-{uuid.uuid4()}",
            texto_cliente=texto, proveedor="api", marca_modelo="Vehiculo Generico",
        )

    sintoma = "Se prende el check y arroja mezcla pobre"
    antes_placa = await turno(sintoma)
    assert antes_placa["status"] == "esperando_placa"
    assert conversacion.contexto["preplate_pending_input"] == sintoma
    assert preparar.await_count == 0

    con_placa = await turno("TST754")
    assert con_placa["status"] == "completado"
    assert preparar.await_count == 1
    assert conversacion.contexto["conversation_state"]["active_system"] == "combustible_admision"

    contexto = await turno("Al acelerar y en caliente")
    estado = conversacion.contexto["conversation_state"]
    assert contexto["status"] == "completado"
    assert preparar.await_count == 2
    assert estado["active_system"] == "combustible_admision"
    assert "caliente" in " ".join(estado["historial_mensajes_usuario"]).lower()
    assert dtos_persistidos[-1].tipo_consulta == "diagnostico"
    assert dtos_persistidos[-1].diagnostico_ml
    assert dtos_persistidos[-1].similitud_rag > modulo.settings.diagnostic.rag_min_similarity
    assert dtos_persistidos[-1].contexto_manual
    assert not dtos_persistidos[-1].llm_usado
    assert enviar.await_count == 1

    # Replay largo del mismo caso: el usuario no tiene la medición, descarta
    # una pieza y aporta un hallazgo. Cada turno conserva el case_id original.
    case_id = estado["case_id"]
    traza_turnos = []
    for mensaje in (
        "No tengo DTC ni valores STFT/LTFT medidos todavía",
        "Ya revisé el cuerpo de aceleración y está bien",
        "Los injectores no inyectan lo suficiente",
        "No",
    ):
        previo = dict(conversacion.contexto["conversation_state"])
        dtos_antes = len(dtos_persistidos)
        rag_antes = len(WEBHOOK_TRACE)
        resultado = await turno(mensaje)
        posterior = conversacion.contexto["conversation_state"]
        traza = (posterior.get("trazabilidad") or [{}])[-1]
        traza_turnos.append({
            "mensaje": mensaje,
            "clasificacion": traza.get("tipo_mensaje"),
            "case_id_antes": previo.get("case_id"),
            "case_id_despues": posterior.get("case_id"),
            "sistema_antes": previo.get("active_system"),
            "sistema_despues": posterior.get("active_system"),
            "preguntas_antes": len(previo.get("preguntas_realizadas") or []),
            "preguntas_despues": len(posterior.get("preguntas_realizadas") or []),
            "decision": traza.get("decision"),
            "motivo": traza.get("motivo_decision"),
            "pregunta": traza.get("pregunta_final"),
            "ml": len(dtos_persistidos) > dtos_antes,
            "rag": any(
                item.get("caso") == "versa" for item in WEBHOOK_TRACE[rag_antes:]
            ),
            "llm": bool(dtos_persistidos[-1].llm_usado) if len(dtos_persistidos) > dtos_antes else False,
            "resultado_webhook": resultado.get("status"),
        })
        assert posterior["case_id"] == case_id, traza_turnos
        assert posterior["active_system"] == "combustible_admision", traza_turnos
    assert len(dtos_persistidos) >= 2, traza_turnos
    if os.getenv("CARBOT_TRACE_VERSA") == "1":
        print("VERSA_TRACE=" + json.dumps(traza_turnos, ensure_ascii=False))
