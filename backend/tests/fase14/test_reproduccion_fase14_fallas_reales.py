"""Tests de reproducción de fallos conversacionales reales en Fase 14.

Reproduce exactamente la conversación observada en WhatsApp real para el Nissan Sentra 2018:
- Turno 1: Usuario describe falla de aceleración en pendiente sin placa. CarBot emite hipótesis preliminar y pregunta de confirmación (SÍ / NO).
- Turno 2: Usuario aclara que no ha comprobado la bomba, añade evidencia (tanque a más de la mitad, terreno plano ok), y pregunta qué otras posibles causas existen y qué dato se necesita para diferenciarlas.
  CORRECCIÓN VERIFICADA: CarBot no emite una plantilla fija ignorando la pregunta y la nueva evidencia ni deja el caso atrapado. Mantiene hipótesis y adapta la comprobación técnica.
- Turno 3: Usuario insiste en continuar el caso sin reiniciar y solicita causas alternativas y pregunta discriminante.
  CORRECCIÓN VERIFICADA: CarBot no se resetea emitiendo el saludo inicial pidiendo la placa.
"""

import traceback
import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.core.services.webhook_service as modulo
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.anyio
async def test_reproduccion_falla_real_nissan_sentra_turnos_2_y_3(monkeypatch):
    """Reproduce el fallo de interceptación en turno 2 y reseteo a saludo inicial en turno 3."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(
        id=uuid.uuid4(),
        taller_id=uuid.uuid4(),
        nombres="Mecánico Prueba Sentra",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    # Conversación inicial limpia
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={},
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
        # Simular comportamiento de DiagnosticPersister respecto a validacion_diagnostico
        contexto_conv = dict(conversacion.contexto or {})
        if modulo.DiagnosticPersister.debe_solicitar_feedback(dto):
            contexto_conv["validacion_diagnostico"] = {
                "diagnostico_id": str(uuid.uuid4()),
                "etapa": "esperando_confirmacion",
            }
        conversacion.contexto = contexto_conv
        return {"status": "completado", "respuesta": getattr(dto, "respuesta_texto", "")}, Decimal("0")

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)

    # ---------------- TURNO 1 ----------------
    t1_text = (
        "NEUVO CASO. Tengo un Nissan Sentra 2018 automático. Cuando acelero en una subida "
        "pierde fuerza y empieza a tironear. En terreno plano funciona mejor. No tengo luces "
        "de advertencia encendidas y no dispongo de la placa en este momento. ¿Qué podría estar fallando?"
    )
    try:
        r1 = await service.procesar_mensaje(
            remitente="51999888777",
            meta_message_id="msg-sentra-1",
            texto_cliente=t1_text,
            proveedor="api",
        )
    except Exception as exc:
        traceback.print_exc()
        raise exc

    assert r1 is not None
    resp1 = str(r1.get("respuesta", ""))
    # No debe bloquear por placa
    assert "Indique una placa válida" not in resp1
    assert "Bomba de gasolina" in resp1 or "combustible" in resp1.lower()

    # ---------------- TURNO 2 ----------------
    # El usuario responde sobre la comprobación, aporta datos nuevos y pregunta causas alternativas
    t2_text = (
        "No he comprobado si se escucha la bomba al poner el contacto en ON. "
        "El tanque tiene más de la mitad de combustible. El problema ocurre principalmente cuando "
        "subo pendientes y acelero; en terreno plano funciona mejor. "
        "¿Qué otras posibles causas existen y qué dato necesitas para diferenciarlas?"
    )
    try:
        r2 = await service.procesar_mensaje(
            remitente="51999888777",
            meta_message_id="msg-sentra-2",
            texto_cliente=t2_text,
            proveedor="api",
        )
    except Exception as exc:
        traceback.print_exc()
        raise exc

    assert r2 is not None
    resp2 = str(r2.get("respuesta", ""))

    # Verificación de que NO se emite la plantilla estática de hipótesis pendiente ignorando la pregunta
    assert "La hipótesis queda pendiente: no registraré una confirmación ni un descarte sin evidencia física" not in resp2, (
        f"FALLO DETECTADO Turno 2: Se emitió plantilla fija que ignoró la pregunta y los nuevos síntomas: {resp2}"
    )
    # Debe conservar hipótesis técnica compatible y orientar según nivel de combustible
    assert "Bomba de gasolina" in resp2 or "combustible" in resp2.lower()
    assert "tanque" in resp2.lower() or "gasolina" in resp2.lower() or "bomba" in resp2.lower()

    # ---------------- TURNO 3 ----------------
    # El usuario pide continuar el caso sin reiniciar
    t3_text = (
        "Quiero continuar el mismo diagnóstico del Nissan Sentra 2018 automático. "
        "Ya te indiqué que pierde fuerza y tironea principalmente al acelerar en pendientes, "
        "que en terreno plano funciona mejor y que el tanque tiene más de la mitad de combustible. "
        "Todavía no he comprobado la bomba de gasolina. "
        "Con la información que ya tienes, dime qué otras causas podrían explicar estos síntomas y "
        "hazme una pregunta concreta que ayude a diferenciarlas. No quiero iniciar otro caso ni repetir información."
    )
    try:
        r3 = await service.procesar_mensaje(
            remitente="51999888777",
            meta_message_id="msg-sentra-3",
            texto_cliente=t3_text,
            proveedor="api",
        )
    except Exception as exc:
        traceback.print_exc()
        raise exc

    assert r3 is not None
    resp3 = str(r3.get("respuesta", ""))

    # Verificación de que NO se resetea al saludo inicial pidiendo placa
    assert "Soy CarBot y estoy aquí para apoyarte con el diagnóstico del vehículo. Para comenzar, ingresa la placa" not in resp3, (
        f"FALLO DETECTADO Turno 3: Se reseteó al saludo inicial pidiendo placa: {resp3}"
    )
    assert "Hola, ¿qué tal? Soy CarBot" not in resp3
    assert len(resp3) > 10
