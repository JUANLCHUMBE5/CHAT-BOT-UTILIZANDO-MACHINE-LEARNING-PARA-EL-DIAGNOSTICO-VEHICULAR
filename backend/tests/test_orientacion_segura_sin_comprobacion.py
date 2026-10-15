"""Pruebas de regresión para orientación provisional segura ante imposibilidad de comprobaciones físicas."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.conversacion.models import ConversationState
from src.core.conversacion.orientacion_provisional import (
    es_feedback_conversacional,
    es_imposibilidad_comprobacion_fisica,
    es_sin_mas_sintomas,
    generar_orientacion_provisional,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.gestor_diagnostico import GestorDiagnostico, ResultadoDiagnostico
from src.core.services.webhook.diagnostic_persister import DiagnosticPersister
from src.core.services.webhook.validation_workflow import ValidationWorkflow


def _crear_escenario_frenos() -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace, MagicMock, MagicMock]:
    diagnostico_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba")
    estado = ConversationState(session_id="test-corolla-frenos")
    case_id = f"caso-frenos-{uuid.uuid4()}"
    estado.case_id = case_id
    estado.active_system = "frenos"
    estado.active_symptoms = [
        "Chirrido delantero al frenar",
        "Vibración en el pedal de freno",
    ]
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "case_id": case_id,
            "conversation_state": estado.exportar_dict(),
            "validacion_diagnostico": {
                "etapa": "esperando_confirmacion",
                "diagnostico_id": str(diagnostico_id),
            },
        },
    )
    diagnostico = SimpleNamespace(
        id=diagnostico_id,
        falla_predicha="Discos de freno alabeados o desgastados",
        sintoma_original="Chirrido delantero al frenar y vibración en el pedal",
        hipotesis=[
            SimpleNamespace(orden=1, falla_probable="Discos de freno alabeados o desgastados", resultado=None),
            SimpleNamespace(orden=2, falla_probable="Pastillas de freno desgastadas", resultado=None),
            SimpleNamespace(orden=3, falla_probable="Cáliper delantero trabado", resultado=None),
        ],
        trazabilidad={"orientacion_provisional": True},
        conclusion_mecanico="Orientación provisional sin confirmación física.",
        estado="generado",
    )
    diagnosticos = MagicMock()
    diagnosticos.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    mensajes = MagicMock()
    mensajes.crear_mensaje = AsyncMock()
    return usuario, conversacion, diagnostico, diagnosticos, mensajes


@pytest.mark.anyio
async def test_imposibilidad_comprobaciones_en_flujo_validacion(monkeypatch):
    """El mecánico declara que no puede hacer comprobaciones ni confirmar más síntomas."""
    usuario, conversacion, diagnostico, diagnosticos, mensajes = _crear_escenario_frenos()
    session = AsyncMock()
    contexto_previo = dict(conversacion.contexto)

    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.DiagnosticoRepository",
        lambda _session: diagnosticos,
    )
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.MensajeRepository",
        lambda _session: mensajes,
    )

    mensaje_usuario = "no puedo realizar comprobaciones físicas ni confirmar síntomas adicionales"
    assert es_imposibilidad_comprobacion_fisica(mensaje_usuario)
    assert es_sin_mas_sintomas(mensaje_usuario)
    resultado = await ValidationWorkflow.manejar_flujo_validacion(
        session=session,
        conversacion=conversacion,
        usuario=usuario,
        texto_cliente=mensaje_usuario,
        tipo_mensaje="text",
        meta_message_id="msg-imposible-1",
        proveedor="api",
        remitente="mecanico-frenos",
        t_inicio=0.0,
    )

    assert resultado is not None
    assert resultado["status"] == "orientacion_provisional"
    resp = resultado["respuesta"]

    # 1. No insiste en comprobaciones que ya declaró imposibles
    assert "no insistiré en pruebas pendientes" in resp.lower() or "no insistire" in resp.lower()
    assert "continúa con la comprobación pendiente" not in resp.lower()
    assert "continua con la comprobacion pendiente" not in resp.lower()

    # 2. Ofrece orientación provisional con datos disponibles sin inventar
    assert "orientación" in resp.lower() or "orientacion" in resp.lower()
    assert "provisional" in resp.lower()
    assert "no confirma" in resp.lower() or "no un diagnóstico confirmado" in resp.lower()

    # 3. Recomienda revisión presencial con prioridad de frenos
    assert "revisión presencial" in resp.lower() or "revision presencial" in resp.lower()
    assert "frenos" in resp.lower()
    assert "seguridad" in resp.lower()

    # 4. No incluye la pregunta de confirmación SÍ/NO
    assert "¿Fue correcta? SÍ / NO" not in resp
    assert "🔎 ¿Fue correcta?" not in resp

    # 5. Preserva case_id, contexto y no altera hipótesis
    assert "validacion_diagnostico" not in conversacion.contexto
    assert conversacion.contexto["case_id"] == contexto_previo["case_id"]
    assert all(h.resultado is None for h in diagnostico.hipotesis)


@pytest.mark.anyio
async def test_consulta_memoria_precede_orientacion_en_validacion(monkeypatch):
    """La consulta no consume validación ni convierte una limitación en diagnóstico."""
    usuario, conversacion, diagnostico, diagnosticos, mensajes = _crear_escenario_frenos()
    session = AsyncMock()
    contexto_previo = dict(conversacion.contexto)
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.DiagnosticoRepository",
        lambda _session: diagnosticos,
    )
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.MensajeRepository",
        lambda _session: mensajes,
    )

    resultado = await ValidationWorkflow.manejar_flujo_validacion(
        session=session,
        conversacion=conversacion,
        usuario=usuario,
        texto_cliente="No puedo comprobar bobinas; consulta la memoria sin generar diagnóstico.",
        tipo_mensaje="text",
        meta_message_id="msg-memoria-validacion",
        proveedor="api",
        remitente="mecanico-frenos",
        t_inicio=0.0,
    )

    assert resultado is not None and resultado["status"] == "consulta_memoria"
    assert "orientación provisional" not in resultado["respuesta"].lower()
    assert conversacion.contexto == contexto_previo
    assert all(h.resultado is None for h in diagnostico.hipotesis)


@pytest.mark.anyio
async def test_feedback_no_confirma_ni_descarta_hipotesis_en_orientacion_provisional(monkeypatch):
    """Una respuesta de feedback a un diagnóstico orientativo o provisional no confirma la falla."""
    usuario, conversacion, diagnostico, diagnosticos, mensajes = _crear_escenario_frenos()
    session = AsyncMock()

    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.DiagnosticoRepository",
        lambda _session: diagnosticos,
    )
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.MensajeRepository",
        lambda _session: mensajes,
    )

    # Usuario responde afirmativamente ("fue correcta" o "sí") a una orientación provisional
    assert es_feedback_conversacional("fue correcta la explicación, gracias")
    resultado = await ValidationWorkflow.manejar_flujo_validacion(
        session=session,
        conversacion=conversacion,
        usuario=usuario,
        texto_cliente="fue correcta la explicación, gracias",
        tipo_mensaje="text",
        meta_message_id="msg-feedback-1",
        proveedor="api",
        remitente="mecanico-frenos",
        t_inicio=0.0,
    )

    assert resultado is not None
    assert resultado["status"] == "feedback_registrado"
    assert "retroalimentación" in resultado["respuesta"].lower() or "retroalimentacion" in resultado["respuesta"].lower()
    assert "sin confirmación física" in resultado["respuesta"].lower() or "sin confirmacion fisica" in resultado["respuesta"].lower()

    # La hipótesis NUNCA debe marcarse como confirmada físicamente
    assert diagnostico.estado == "generado"
    assert all(h.resultado is None for h in diagnostico.hipotesis)
    assert "validacion_diagnostico" not in conversacion.contexto


@pytest.mark.anyio
async def test_orquestador_maneja_imposibilidad_comprobacion_directamente():
    """El orquestador genera orientación provisional segura cuando el usuario declara imposibilidad."""
    gestor = GestorDiagnostico()
    orq = OrquestadorConversacion()
    sid = "test-orq-imposible-frenos"

    # Turno 1: Síntoma de frenos
    res1 = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="Tengo un Toyota Yaris con chirrido en las ruedas al frenar y pedal esponjoso",
        gestor_diagnostico=gestor,
    )
    assert res1["estado"].case_id is not None
    case_id_inicial = res1["estado"].case_id

    # Turno 2: Declaración de imposibilidad de pruebas físicas
    res2 = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="No puedo realizar comprobaciones físicas ni confirmar síntomas adicionales",
        gestor_diagnostico=gestor,
    )

    assert res2["decision"] == "ORIENTACION_PROVISIONAL"
    assert res2["es_pregunta"] is False
    assert res2["case_id"] == case_id_inicial
    resp2 = res2["respuesta_texto"]

    # Debe contener orientación segura, advertencia de frenos y revisión presencial
    assert "orientación preliminar" in resp2.lower() or "orientacion preliminar" in resp2.lower()
    assert "frenos" in resp2.lower()
    assert "revisión presencial" in resp2.lower() or "revision presencial" in resp2.lower()
    assert "no insistiré" in resp2.lower() or "no insistire" in resp2.lower()
    assert "¿Fue correcta? SÍ / NO" not in resp2

    # El dto tiene flag es_orientacion_provisional
    dto = res2.get("dto")
    assert dto is not None
    assert dto.es_orientacion_provisional is True


@pytest.mark.anyio
async def test_diagnostic_persister_no_agrega_pregunta_si_no_en_orientacion_provisional():
    """DiagnosticPersister no anexa '¿Fue correcta? SÍ / NO' en orientaciones provisionales."""
    texto = (
        "Entendido. Al no ser posible realizar comprobaciones físicas, no insistiré en pruebas pendientes.\n\n"
        "Con los datos recopilados, la orientación preliminar apunta a Discos de freno. "
        "El diagnóstico permanece sin confirmar.\n\n"
        "Se recomienda acudir a revisión presencial en taller especializado."
    )
    dto = ResultadoDiagnostico(
        respuesta_texto=texto,
        diagnostico_ml="Discos de freno",
        confianza_ml=0.5,
        contexto_manual="",
        titulo_manual="",
        modo_diagnostico="orientacion_provisional",
        es_orientacion_provisional=True,
    )

    assert DiagnosticPersister.debe_solicitar_feedback(dto) is False


def test_orientacion_provisional_sistema_no_frenos():
    """Para sistemas que no son frenos, la orientación no incluye advertencia específica de frenos."""
    estado = ConversationState(session_id="test-motor")
    estado.active_system = "encendido"
    estado.active_symptoms = ["Motor pierde fuerza en subida", "Jaloneo leve al acelerar"]
    estado.falla_principal = "Falla en bujías o bobinas de encendido"

    resp = generar_orientacion_provisional(estado)
    assert "no insistiré en pruebas pendientes" in resp.lower() or "no insistire" in resp.lower()
    assert "orientación preliminar" in resp.lower() or "orientacion preliminar" in resp.lower()
    assert "taller especializado" not in resp.lower()
    assert "sistema de frenos" not in resp.lower()
    assert "riesgo de pérdida de frenado" not in resp.lower()


@pytest.mark.anyio
@pytest.mark.parametrize("respuesta_binaria_usuario", ["SÍ", "si", "NO", "no"])
async def test_feedback_binario_si_no_nunca_modifica_confirmacion_fisica_ni_exactitud_tesis(
    monkeypatch, respuesta_binaria_usuario
):
    """Garantizar que una respuesta binaria SÍ o NO recibida como feedback
    a una orientación provisional NUNCA altera el estado de confirmación
    física ni corrompe el Indicador 3 de Exactitud ML de la tesis."""
    usuario, conversacion, diagnostico, diagnosticos, mensajes = _crear_escenario_frenos()
    session = AsyncMock()

    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.DiagnosticoRepository",
        lambda _session: diagnosticos,
    )
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.MensajeRepository",
        lambda _session: mensajes,
    )

    resultado = await ValidationWorkflow.manejar_flujo_validacion(
        session=session,
        conversacion=conversacion,
        usuario=usuario,
        texto_cliente=respuesta_binaria_usuario,
        tipo_mensaje="text",
        meta_message_id=f"msg-binario-{respuesta_binaria_usuario}",
        proveedor="api",
        remitente="mecanico-frenos",
        t_inicio=0.0,
    )

    assert resultado is not None
    assert resultado["status"] == "feedback_registrado"
    assert "retroalimentación" in resultado["respuesta"].lower() or "retroalimentacion" in resultado["respuesta"].lower()
    assert "sin confirmación física" in resultado["respuesta"].lower() or "sin confirmacion fisica" in resultado["respuesta"].lower()

    # Integridad metodológica estricta:
    # 1. El diagnóstico nunca pasa a "confirmado" (ni a "descartado")
    assert diagnostico.estado == "generado"
    assert diagnostico.estado != "confirmado"

    # 2. Las hipótesis diagnósticas nunca se computan como confirmadas físicamente
    for h in diagnostico.hipotesis:
        assert h.resultado is None
        assert h.resultado != "confirmada"
        assert h.resultado != "descartada"

    # 3. La etapa de validación se libera sin bucles
    assert "validacion_diagnostico" not in conversacion.contexto


@pytest.mark.anyio
async def test_conservacion_integral_case_id_vehiculo_sintomas_descartes():
    """Comprobar que una orientación provisional preserva fielmente case_id,
    vehículo, síntomas reportados y descartes acumulados."""
    gestor = GestorDiagnostico()
    orq = OrquestadorConversacion()
    sid = "test-conservacion-frenos-completa"

    # Turno 1: Reporte con datos de vehículo y síntomas
    res1 = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="Nissan Sentra 2018 placa B4V-123 chirrido metálico al frenar",
        gestor_diagnostico=gestor,
    )
    estado1 = res1["estado"]
    case_id_original = estado1.case_id
    assert case_id_original is not None

    # Agregar descarte explícito previo
    estado1.hipotesis_descartadas.append("Falla en servofreno")
    estado1.placa = "B4V-123"
    estado1.marca = "Nissan"
    estado1.modelo = "Sentra"
    await orq.repositorio.save_session(sid, estado1)

    # Turno 2: Declaración de imposibilidad física y de síntomas
    res2 = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="No puedo realizar comprobaciones físicas ni confirmar síntomas adicionales",
        gestor_diagnostico=gestor,
    )

    assert res2["decision"] == "ORIENTACION_PROVISIONAL"
    assert res2["es_pregunta"] is False
    estado2 = res2["estado"]

    # Invariantes de persistencia y contexto:
    assert estado2.case_id == case_id_original
    assert estado2.placa == "B4V-123"
    assert estado2.marca == "Nissan"
    assert estado2.modelo == "Sentra"
    assert "Falla en servofreno" in estado2.hipotesis_descartadas
    assert len(estado2.active_symptoms) > 0
    assert any("frenar" in s.lower() or "chirrido" in s.lower() for s in estado2.active_symptoms)
    assert estado2.trazabilidad[-1]["decision"] == "ORIENTACION_PROVISIONAL"

