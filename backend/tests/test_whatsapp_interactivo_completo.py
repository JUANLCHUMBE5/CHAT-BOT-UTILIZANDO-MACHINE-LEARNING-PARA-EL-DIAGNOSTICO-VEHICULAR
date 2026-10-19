"""Pruebas exhaustivas para la integración de WhatsApp interactivo (botones de hipótesis y confirmación SÍ/NO)."""

from __future__ import annotations

import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.services.confirmacion_diagnostico import (
    construir_botones_confirmacion,
    construir_botones_hipotesis,
    generar_titulo_boton_hipotesis,
)
from src.core.services.webhook.validation_workflow import ValidationWorkflow


def test_generar_titulo_boton_hipotesis_limite_20_caracteres():
    # Long title must be safely truncated to <= 20 chars without broken words
    titulo = generar_titulo_boton_hipotesis(1, "Fuga hidráulica o aire en el sistema de frenos", max_chars=20)
    assert len(titulo) <= 20
    assert titulo.startswith("1.") or "1" in titulo

    titulo2 = generar_titulo_boton_hipotesis(2, "Discos de freno alabeados o desgastados", max_chars=20)
    assert len(titulo2) <= 20
    assert "2." in titulo2 or "2" in titulo2


def test_construir_botones_hipotesis_tres_o_menos_quick_reply():
    hipotesis = [
        {"falla": "Fuga hidráulica en frenos", "probabilidad": 0.60},
        {"falla": "Discos de freno alabeados", "probabilidad": 0.25},
        {"falla": "Pastillas desgastadas", "probabilidad": 0.15},
    ]
    payload = construir_botones_hipotesis(hipotesis, case_id="caso-test-123")
    assert payload["type"] == "button"
    assert len(payload["action"]["buttons"]) == 3
    for btn in payload["action"]["buttons"]:
        assert btn["type"] == "reply"
        assert len(btn["reply"]["title"]) <= 20
        assert "hip_" in btn["reply"]["id"]


def test_construir_botones_hipotesis_mas_de_tres_lista_interactiva():
    hipotesis = [
        {"falla": "Falla 1", "probabilidad": 0.4},
        {"falla": "Falla 2", "probabilidad": 0.3},
        {"falla": "Falla 3", "probabilidad": 0.2},
        {"falla": "Falla 4", "probabilidad": 0.1},
    ]
    payload = construir_botones_hipotesis(hipotesis, case_id="caso-test-456")
    assert payload["type"] == "list"
    assert "sections" in payload["action"]
    assert len(payload["action"]["sections"][0]["rows"]) == 4


def test_construir_botones_confirmacion_si_no():
    payload = construir_botones_confirmacion(case_id="caso-conf-789")
    assert payload["type"] == "button"
    buttons = payload["action"]["buttons"]
    assert len(buttons) == 2
    assert any(b["reply"]["id"].startswith("conf_si") for b in buttons)
    assert any(b["reply"]["id"].startswith("conf_no") for b in buttons)
    for b in buttons:
        assert len(b["reply"]["title"]) <= 20


@pytest.mark.anyio
async def test_flujo_completo_seleccion_boton_hipotesis_y_confirmacion_si():
    # 1. Setup scenario
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    hip1 = SimpleNamespace(orden=1, falla_probable="Fuga hidráulica o aire", resultado=None, confianza=0.60)
    hip2 = SimpleNamespace(orden=2, falla_probable="Discos desgastados", resultado=None, confianza=0.25)
    diagnostico = SimpleNamespace(
        id=diag_id,
        estado="generado",
        falla_predicha="Fuga hidráulica o aire",
        sintoma_original="Pedal esponjoso",
        hipotesis=[hip1, hip2],
        trazabilidad={},
        conclusion_mecanico=None,
    )

    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "case_id": f"caso-{diag_id}",
            "validacion_diagnostico": {
                "etapa": "esperando_confirmacion",
                "diagnostico_id": str(diag_id),
            },
        },
    )

    session = AsyncMock()
    diag_mock = MagicMock()
    diag_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    op_mock = MagicMock()
    op_mock.registrar_auditoria = AsyncMock()
    msg_mock = MagicMock()
    msg_mock.crear_mensaje = AsyncMock()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.core.services.webhook.validation_workflow.DiagnosticoRepository", lambda s: diag_mock)
        mp.setattr("src.core.services.webhook.validation_workflow.OperacionesRepository", lambda s: op_mock)
        mp.setattr("src.core.services.webhook.validation_workflow.MensajeRepository", lambda s: msg_mock)

        # Paso 1: Mecánico presiona botón Hipótesis 1 (payload: 'hip_1_...')
        res_sel = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="1 — Fuga hidráulica",
            tipo_mensaje="interactive",
            meta_message_id="msg_btn_1",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=time.perf_counter(),
            payload_interactivo=f"hip_1_{diag_id}",
        )

        assert res_sel is not None
        assert res_sel["status"] == "esperando_confirmacion"
        # Verifica que presenta la comprobación técnica y pide confirmar con SÍ/NO
        assert "verificación física" in res_sel["respuesta"].lower() or "comprobaste" in res_sel["respuesta"].lower()
        # Verifica que NO se confirmó automáticamente
        assert hip1.resultado is None

        # Paso 2: Mecánico realiza la comprobación física y presiona botón SÍ (payload: 'conf_si_...')
        res_conf = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="SÍ",
            tipo_mensaje="interactive",
            meta_message_id="msg_btn_si",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=time.perf_counter(),
            payload_interactivo=f"conf_si_{diag_id}",
        )

        assert res_conf is not None
        assert res_conf["status"] in ("confirmado", "validacion_tecnica")
        assert hip1.resultado == "confirmada"
        assert diagnostico.estado == "confirmado"
        assert "confirmado por el mecánico" in res_conf["respuesta"].lower() or "confirmado" in res_conf["respuesta"].lower()
        # Trazabilidad y auditoría
        assert op_mock.registrar_auditoria.called


@pytest.mark.anyio
async def test_flujo_seleccion_boton_hipotesis_y_descarte_no_continuando_mismo_caso():
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    hip1 = SimpleNamespace(orden=1, falla_probable="Discos desgastados", resultado=None, confianza=0.60)
    hip2 = SimpleNamespace(orden=2, falla_probable="Fuga hidráulica", resultado=None, confianza=0.25)
    diagnostico = SimpleNamespace(
        id=diag_id,
        estado="generado",
        falla_predicha="Discos desgastados",
        sintoma_original="Pedal esponjoso y tarda en detenerse",
        hipotesis=[hip1, hip2],
        trazabilidad={},
        conclusion_mecanico=None,
    )

    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "case_id": f"caso-{diag_id}",
            "validacion_diagnostico": {
                "etapa": "esperando_confirmacion",
                "diagnostico_id": str(diag_id),
                "orden_seleccionado": 1,
            },
        },
    )

    session = AsyncMock()
    diag_mock = MagicMock()
    diag_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    op_mock = MagicMock()
    op_mock.registrar_auditoria = AsyncMock()
    msg_mock = MagicMock()
    msg_mock.crear_mensaje = AsyncMock()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.core.services.webhook.validation_workflow.DiagnosticoRepository", lambda s: diag_mock)
        mp.setattr("src.core.services.webhook.validation_workflow.OperacionesRepository", lambda s: op_mock)
        mp.setattr("src.core.services.webhook.validation_workflow.MensajeRepository", lambda s: msg_mock)

        # Mecánico presiona botón [NO] (payload: 'conf_no_...')
        res_no = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="NO",
            tipo_mensaje="interactive",
            meta_message_id="msg_btn_no",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=time.perf_counter(),
            payload_interactivo=f"conf_no_{diag_id}",
        )

        assert res_no is not None
        assert res_no["status"] == "esperando_falla_real"
        # ÚNICAMENTE la hipótesis 1 se descarta
        assert hip1.resultado == "descartada"
        assert hip2.resultado is None
        # Mantiene el mismo case_id
        assert conversacion.contexto["case_id"] == f"caso-{diag_id}"
        # Pregunta técnica discriminante formulada
        assert "se descarta *Discos desgastados*" in res_no["respuesta"]
