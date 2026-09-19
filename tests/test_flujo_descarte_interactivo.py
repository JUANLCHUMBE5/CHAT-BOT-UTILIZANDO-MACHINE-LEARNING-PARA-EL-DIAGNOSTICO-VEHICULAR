"""Pruebas unitarias completas para el flujo interactivo de descarte técnico y selección de alternativas."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.services.confirmacion_diagnostico import (
    ConfirmacionDiagnosticoWhatsApp,
    interpretar_respuesta_validacion_whatsapp,
)
from src.core.services.webhook.validation_workflow import ValidationWorkflow


@pytest.mark.anyio
async def test_interpretacion_afirmativa_variantes():
    variantes_si = ["SÍ", "si", "Sí", "correcto", "correcta", "fue correcto", "esta bien"]
    for v in variantes_si:
        assert interpretar_respuesta_validacion_whatsapp(v) == "si", f"Falló para: {v}"


@pytest.mark.anyio
async def test_interpretacion_negativa_variantes():
    variantes_no = ["NO", "no", "No", "incorrecto", "incorrecta", "fue incorrecto", "fue incorrecta", "esta mal"]
    for v in variantes_no:
        assert interpretar_respuesta_validacion_whatsapp(v) == "no", f"Falló para: {v}"


@pytest.mark.anyio
async def test_frase_larga_no_es_binaria():
    frases = [
        "El carro no arranca cuando calienta en subida",
        "Sí tiene chispa pero no llega gasolina al riel",
        "Revisé las bujías y todas están quemadas",
    ]
    for f in frases:
        assert interpretar_respuesta_validacion_whatsapp(f) is None, f"No debió ser binario: {f}"


@pytest.mark.anyio
async def test_procesar_confirmacion_sin_diagnostico_pendiente():
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    diag_repo = MagicMock()
    diag_repo.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=None)
    diag_repo.obtener_ultimo_pendiente_mecanico = AsyncMock(return_value=None)
    operaciones_repo = MagicMock()

    confirmacion = ConfirmacionDiagnosticoWhatsApp(estado="confirmado")
    msg, diag_id = await ValidationWorkflow.procesar_confirmacion_tecnica(
        confirmacion, usuario, diag_repo, operaciones_repo
    )

    assert diag_id is None
    assert "No tienes un diagnóstico pendiente" in msg


@pytest.mark.anyio
async def test_procesar_descarte_requiere_observacion():
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    diag_repo = MagicMock()
    operaciones_repo = MagicMock()

    confirmacion = ConfirmacionDiagnosticoWhatsApp(estado="descartado", requiere_observacion=True, observacion=None)
    msg, diag_id = await ValidationWorkflow.procesar_confirmacion_tecnica(
        confirmacion, usuario, diag_repo, operaciones_repo
    )

    assert diag_id is None
    assert "Para descartar el diagnóstico indica la falla encontrada" in msg


@pytest.mark.anyio
async def test_procesar_confirmacion_exitosa_actualiza_hipotesis_y_auditoria():
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    hipotesis_1 = SimpleNamespace(orden=1, resultado=None)
    hipotesis_2 = SimpleNamespace(orden=2, resultado=None)

    diagnostico = SimpleNamespace(
        id=diag_id,
        estado="generado",
        conclusion_mecanico=None,
        hipotesis=[hipotesis_1, hipotesis_2],
        trazabilidad={},
    )

    diag_repo = MagicMock()
    diag_repo.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    operaciones_repo = MagicMock()
    operaciones_repo.registrar_auditoria = AsyncMock()

    confirmacion = ConfirmacionDiagnosticoWhatsApp(estado="confirmado", observacion="Cambié bujías y quedó ok")
    msg, res_id = await ValidationWorkflow.procesar_confirmacion_tecnica(
        confirmacion, usuario, diag_repo, operaciones_repo, diagnostico_id=diag_id
    )

    assert res_id == diag_id
    assert diagnostico.estado == "confirmado"
    assert hipotesis_1.resultado == "confirmada"
    assert hipotesis_2.resultado is None  # no debe tocar hipotesis orden > 1
    assert "confirmado por el mecánico" in msg
    assert "Cambié bujías y quedó ok" in msg
    operaciones_repo.registrar_auditoria.assert_called_once()


@pytest.mark.anyio
async def test_manejar_flujo_no_presenta_alternativas_ml():
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={"validacion_diagnostico": {"etapa": "esperando_confirmacion", "diagnostico_id": str(diag_id)}},
    )

    diagnostico = SimpleNamespace(
        id=diag_id,
        falla_predicha="Falla en bujias o bobinas de encendido (misfire)",
        sintoma_original="El carro tironea en subida",
        trazabilidad={
            "predicciones_ml": [
                {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.82},
                {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.12},
                {"falla": "Inyectores sucios o filtro de combustible obstruido", "probabilidad": 0.06},
            ]
        },
    )

    session = AsyncMock()
    diag_mock = MagicMock()
    diag_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)

    msg_mock = MagicMock()
    msg_mock.crear_mensaje = AsyncMock()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.core.services.webhook.validation_workflow.DiagnosticoRepository", lambda s: diag_mock)
        mp.setattr("src.core.services.webhook.validation_workflow.MensajeRepository", lambda s: msg_mock)

        resultado = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="NO",
            tipo_mensaje="text",
            meta_message_id="wamid_123",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=0.0,
        )

    assert resultado is not None
    assert resultado["status"] == "esperando_falla_real"
    respuesta = resultado["respuesta"]
    assert "Se descarta *Falla en bujias o bobinas de encendido (misfire)*" in respuesta or "se descarta *Falla en bujias" in respuesta
    assert "Pregunta técnica discriminante" in respuesta
    assert conversacion.contexto["validacion_diagnostico"]["etapa"] == "esperando_falla_real"


@pytest.mark.anyio
async def test_manejar_flujo_seleccion_alternativa_2_lanza_rediagnostico():
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "validacion_diagnostico": {
                "etapa": "esperando_falla_real",
                "diagnostico_id": str(diag_id),
                "sintoma_base": "Motor pierde fuerza en subida",
                "falla_descartada": "Bujias desgastadas",
            }
        },
    )

    diagnostico = SimpleNamespace(
        id=diag_id,
        estado="generado",
        conclusion_mecanico=None,
        hipotesis=[SimpleNamespace(orden=1, resultado=None)],
        trazabilidad={},
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

        resultado = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="al acelerar fuerte pierde presion la bomba",
            tipo_mensaje="text",
            meta_message_id="wamid_456",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=0.0,
        )

    assert resultado is not None
    assert resultado["status"] == "evaluar_alternativa"
    assert "Motor pierde fuerza en subida" in resultado["texto_evaluar"]
    assert "al acelerar fuerte pierde presion la bomba" in resultado["texto_evaluar"]
    assert resultado["diagnostico_forzado"] is None
    assert "validacion_diagnostico" not in conversacion.contexto


@pytest.mark.anyio
async def test_manejar_flujo_seleccion_alternativa_variantes_texto():
    variantes = ["en alta jalonea", "cascabelea al acelerar"]
    for var in variantes:
        usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
        conversacion = SimpleNamespace(
            id=uuid.uuid4(),
            contexto={
                "validacion_diagnostico": {
                    "etapa": "esperando_falla_real",
                    "diagnostico_id": str(uuid.uuid4()),
                    "sintoma_base": "Falla en alta",
                    "falla_descartada": "Inyector tapado",
                }
            },
        )
        diagnostico = SimpleNamespace(
            id=uuid.uuid4(),
            estado="generado",
            conclusion_mecanico=None,
            hipotesis=[SimpleNamespace(orden=1, resultado=None)],
            trazabilidad={},
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

            resultado = await ValidationWorkflow.manejar_flujo_validacion(
                session=session,
                conversacion=conversacion,
                usuario=usuario,
                texto_cliente=var,
                tipo_mensaje="text",
                meta_message_id="wamid_var",
                proveedor="meta",
                remitente="+51999888777",
                t_inicio=0.0,
            )

        assert resultado is not None, f"Falló para variante: {var}"
        assert resultado["status"] == "evaluar_alternativa"
        assert var in resultado["texto_evaluar"]
        assert resultado["diagnostico_forzado"] is None


@pytest.mark.anyio
async def test_manejar_flujo_no_sin_alternativas_previas():
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={"validacion_diagnostico": {"etapa": "esperando_confirmacion", "diagnostico_id": str(diag_id)}},
    )

    diagnostico = SimpleNamespace(
        id=diag_id,
        falla_predicha="Falla de alternador",
        sintoma_original="Batería se descarga",
        trazabilidad={},  # Sin predicciones_ml
    )

    session = AsyncMock()
    diag_mock = MagicMock()
    diag_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    msg_mock = MagicMock()
    msg_mock.crear_mensaje = AsyncMock()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.core.services.webhook.validation_workflow.DiagnosticoRepository", lambda s: diag_mock)
        mp.setattr("src.core.services.webhook.validation_workflow.MensajeRepository", lambda s: msg_mock)

        resultado = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="NO",
            tipo_mensaje="text",
            meta_message_id="wamid_sin_alts",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=0.0,
        )

    assert resultado is not None
    assert resultado["status"] == "esperando_falla_real"
    assert "Pregunta técnica discriminante" in resultado["respuesta"]
    assert "Falla de alternador" in resultado["respuesta"]
