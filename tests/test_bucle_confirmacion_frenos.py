"""Regresiones del cierre de validación cuando el mecánico aún quiere investigar."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.conversacion.models import ConversationState
from src.core.services.webhook.validation_workflow import ValidationWorkflow


def _escenario_confirmacion() -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace, MagicMock, MagicMock]:
    diagnostico_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    estado = ConversationState(session_id="corolla-frenos")
    case_id = f"caso-corolla-frenos-{uuid.uuid4()}"
    estado.case_id = case_id
    estado.active_symptoms = [
        "Chirrido delantero al frenar",
        "Vibración en el pedal sin vibración en el volante",
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
        falla_predicha="Discos alabeados o desgastados",
        sintoma_original="Chirrido delantero al frenar y vibración en el pedal",
        hipotesis=[
            SimpleNamespace(orden=1, falla_probable="Discos alabeados o desgastados", resultado=None),
            SimpleNamespace(orden=2, falla_probable="Pastillas de freno desgastadas", resultado=None),
            SimpleNamespace(orden=3, falla_probable="Cáliper delantero trabado", resultado=None),
        ],
        trazabilidad={},
    )
    diagnosticos = MagicMock()
    diagnosticos.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    mensajes = MagicMock()
    mensajes.crear_mensaje = AsyncMock()
    return usuario, conversacion, diagnostico, diagnosticos, mensajes


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("texto", "fragmento"),
    [
        ("No he verificado ninguna falla; quiero continuar el diagnóstico", "Podemos continuar"),
        ("No puedo desmontar la rueda", "sin desmontar la rueda"),
        ("No sé todavía", "Podemos continuar"),
    ],
)
async def test_confirmacion_pendiente_permite_continuar_sin_perder_contexto(monkeypatch, texto, fragmento):
    usuario, conversacion, diagnostico, diagnosticos, mensajes = _escenario_confirmacion()
    session = AsyncMock()
    contexto_antes = dict(conversacion.contexto)

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
        texto_cliente=texto,
        tipo_mensaje="text",
        meta_message_id="local-corolla",
        proveedor="api",
        remitente="local-corolla",
        t_inicio=0.0,
    )

    assert resultado is not None
    assert resultado["status"] == "continuar_diagnostico"
    assert fragmento in resultado["respuesta"]
    assert "1, 2 o 3" not in resultado["respuesta"]
    assert "validacion_diagnostico" not in conversacion.contexto
    assert conversacion.contexto["case_id"] == contexto_antes["case_id"]
    assert conversacion.contexto["conversation_state"] == contexto_antes["conversation_state"]
    assert all(hipotesis.resultado is None for hipotesis in diagnostico.hipotesis)


@pytest.mark.anyio
async def test_no_aislado_no_descarta_ni_selecciona_la_hipotesis_uno(monkeypatch):
    usuario, conversacion, diagnostico, diagnosticos, mensajes = _escenario_confirmacion()
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
        texto_cliente="NO",
        tipo_mensaje="text",
        meta_message_id="local-no",
        proveedor="api",
        remitente="local-corolla",
        t_inicio=0.0,
    )

    assert resultado is not None
    assert resultado["status"] == "esperando_aclaracion_confirmacion"
    assert "confirmación ni un descarte" in resultado["respuesta"]
    assert all(hipotesis.resultado is None for hipotesis in diagnostico.hipotesis)
    assert conversacion.contexto["validacion_diagnostico"]["etapa"] == "esperando_aclaracion_confirmacion"


@pytest.mark.anyio
async def test_conversaciones_concurrentes_no_comparten_confirmacion(monkeypatch):
    uno = _escenario_confirmacion()
    dos = _escenario_confirmacion()
    diagnosticos_uno = uno[3]
    diagnosticos_dos = dos[3]
    mensajes = MagicMock()
    mensajes.crear_mensaje = AsyncMock()

    def repo_diagnostico(session):
        return diagnosticos_uno if session is sesiones[0] else diagnosticos_dos

    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.DiagnosticoRepository",
        repo_diagnostico,
    )
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.MensajeRepository",
        lambda _session: mensajes,
    )
    sesiones = [AsyncMock(), AsyncMock()]

    resultados = await asyncio.gather(
        ValidationWorkflow.manejar_flujo_validacion(
            sesiones[0], uno[1], uno[0], "Quiero continuar el diagnóstico", "text",
            "local-uno", "api", "local-uno", 0.0,
        ),
        ValidationWorkflow.manejar_flujo_validacion(
            sesiones[1], dos[1], dos[0], "No puedo desmontar la rueda", "text",
            "local-dos", "api", "local-dos", 0.0,
        ),
    )

    assert [resultado["status"] for resultado in resultados] == [
        "continuar_diagnostico",
        "continuar_diagnostico",
    ]
    assert uno[1].contexto["case_id"] != dos[1].contexto["case_id"]
    assert "validacion_diagnostico" not in uno[1].contexto
    assert "validacion_diagnostico" not in dos[1].contexto
