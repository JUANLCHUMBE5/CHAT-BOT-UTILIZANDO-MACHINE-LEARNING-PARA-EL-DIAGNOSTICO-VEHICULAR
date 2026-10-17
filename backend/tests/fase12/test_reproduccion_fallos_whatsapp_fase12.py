"""Tests de reproducción y validación de fallos de WhatsApp en Fase 12.

Reproduce de forma determinista y sin tocar producción los fallos reportados en la prueba
real de WhatsApp (Commit base main 15dad809b7339ffec62678b78578a6d1fda5f8d6):
1. Inconsistencia de feedback (ofrece 1/2/3 cuando solo hay 1 hipótesis).
2. Interpretación de "No he comprobado si los discos están dañados" y negaciones múltiples.
3. Clasificación errónea de consultas con síntomas ("chirrido") como consulta informativa técnica OEM.
4. Bucle infinito de solicitud de placa ("Indique una placa válida...") al no disponer de placa o al reintentar el diagnóstico.
5. Reproducción secuencial de los 5 turnos de la conversación real de WhatsApp (Toyota Corolla 2015).
6. Reproducción de evidencia adicional de WhatsApp real (Caso "NEUVO CASO" y Nissan Sentra 2018).
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.core.services.webhook_service as modulo
from src.application.services.confirmacion_diagnostico import (
    instrucciones_confirmacion_whatsapp,
    interpretar_respuesta_validacion_whatsapp,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.state_models.enums import FactState
from src.core.conversacion.state_models.state import ConversationState
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.intent_classifier import clasificar_intencion_consulta

# ==============================================================================
# TEST 1: INCONSISTENCIA DE FEEDBACK (TOP-1 vs TOP-3)
# ==============================================================================

def test_feedback_instrucciones_coherente_con_cantidad_hipotesis():
    """El texto de feedback no debe ofrecer (1/2/3) cuando solo se presenta 1 hipótesis."""
    texto_1 = instrucciones_confirmacion_whatsapp(cantidad_hipotesis=1)
    assert "(1/2/3)" not in texto_1
    assert "(1/2)" not in texto_1
    assert "*SÍ / NO*" in texto_1

    texto_2 = instrucciones_confirmacion_whatsapp(cantidad_hipotesis=2)
    assert "(1/2)" in texto_2
    assert "(1/2/3)" not in texto_2

    texto_3 = instrucciones_confirmacion_whatsapp(cantidad_hipotesis=3)
    assert "(1/2/3)" in texto_3


# ==============================================================================
# TEST 2: INTERPRETACIÓN DE "NO HE COMPROBADO" Y NEGACIONES MÚLTIPLES
# ==============================================================================

def test_no_he_comprobado_no_es_descarte_de_hipotesis():
    """'No he comprobado si los discos están dañados' no debe marcarse como descarte 'NO'."""
    res = interpretar_respuesta_validacion_whatsapp(
        "No he comprobado si los discos están dañados. El pedal no se va al fondo y tampoco vibra el volante al frenar."
    )
    # Debe ser None (no es un simple 'no' de descarte ni 'si' de confirmación)
    assert res is None


def test_extraccion_negaciones_pedal_y_vibracion():
    """Verifica que 'el pedal no se va al fondo' y 'tampoco vibra el volante' se extraigan."""
    texto = "No he comprobado si los discos están dañados. El pedal no se va al fondo y tampoco vibra el volante al frenar."
    estado = ConversationState(session_id="test-session")
    ExtractorHechos.extraer_y_actualizar(estado, texto)

    # Debe identificar ausencia de vibración y ausencia de pedal esponjoso / hundido
    campos_negados = [campo for campo, h in estado.hechos.items() if h.estado == FactState.AUSENTE_NEGADO]
    assert any("vibra" in c or "vibracion" in c for c in campos_negados), f"Campos extraídos: {campos_negados}"
    assert "sintoma_pedal_se_va_al_fondo" in campos_negados


# ==============================================================================
# TEST 3: INTENT CLASSIFIER NO DEBE MARCAR PREGUNTAS DIAGNÓSTICAS COMO INFORMATIVAS
# ==============================================================================

def test_mensaje_con_chirrido_y_pregunta_es_diagnostico():
    """Mensajes que describen síntomas y preguntan causas deben ser 'diagnostico' y no 'consulta_tecnica'."""
    texto_t3 = (
        "No he comprobado si los discos están dañados. El pedal no se va al fondo y tampoco vibra el volante al frenar. "
        "Solo escucho un chirrido cuando piso el freno suavemente. ¿Por qué sospechas de los discos y qué otras causas podrían ser?"
    )
    # Contiene chirrido, freno, etc. Debe ser 'diagnostico' y no 'consulta_tecnica'
    intencion = clasificar_intencion_consulta(texto_t3)
    assert intencion == "diagnostico", f"FALLO REPRODUCIDO: Intención clasificada erróneamente como '{intencion}'"


# ==============================================================================
# TEST 4: MANEJO DE "NO TENGO LA PLACA" EN FLUJO DE VEHÍCULO
# ==============================================================================

@pytest.mark.anyio
async def test_usuario_indica_no_tener_placa_permite_continuar_diagnostico(monkeypatch):
    """Si el usuario dice 'no tengo la placa disponible', el sistema no debe responder en bucle 'Indique una placa válida'."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "perfil_vehiculo": {"marca": "Toyota", "modelo": "Corolla", "anio": "2015"},
            "posttest_placa_pendiente": True,
        },
    )
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

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)

    # El usuario indica que no tiene la placa disponible
    res = await service.procesar_mensaje(
        remitente="51999111222",
        meta_message_id=f"msg-{uuid.uuid4()}",
        texto_cliente="No tengo la placa disponible en este momento. Ya te indiqué que es un Toyota Corolla 2015 y presenta un chirrido al frenar.",
        proveedor="api",
        marca_modelo="",
    )

    assert res is not None
    # No debe devolver el error de placa inválida en bucle
    assert "Indique una placa válida" not in str(res.get("respuesta", "")), (
        f"FALLO REPRODUCIDO: Se cayó en el bucle de placa: {res.get('respuesta')}"
    )


# ==============================================================================
# TEST 5: REPRODUCCIÓN COMPLETA DE LA CONVERSACIÓN REAL DE 5 TURNOS (COROLLA 2015)
# ==============================================================================

@pytest.mark.anyio
async def test_reproduccion_conversacion_real_5_turnos(monkeypatch):
    """Reproduce los 5 turnos de la conversación real de WhatsApp reportada en Fase 12."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "conversation_state": {
                "session_id": "prev-session",
                "dominio_probable": "MOTOR",
                "active_system": "MOTOR",
            }
        },
    )
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

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)

    # ---------------- TURNO 1 ----------------
    t1_text = "Hola, tengo un Toyota Corolla 2015. Cuando freno escucho un chirrido fuerte, especialmente cuando piso el pedal suavemente. ¿Me puedes ayudar a identificar qué podría estar fallando?"
    r1 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-1", texto_cliente=t1_text, proveedor="api",
    )
    assert r1 is not None

    # ---------------- TURNO 2 ----------------
    t2_text = "Es una falla diferente. Quiero iniciar un diagnóstico nuevo para un Toyota Corolla 2015 que presenta un chirrido fuerte al frenar suavemente."
    r2 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-2", texto_cliente=t2_text, proveedor="api",
    )
    assert r2 is not None

    # ---------------- TURNO 3 ----------------
    t3_text = "No he comprobado si los discos están dañados. El pedal no se va al fondo y tampoco vibra el volante al frenar. Solo escucho un chirrido cuando piso el freno suavemente. ¿Por qué sospechas de los discos y qué otras causas podrían ser?"
    r3 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-3", texto_cliente=t3_text, proveedor="api",
    )
    assert r3 is not None
    resp3_str = str(r3.get("respuesta", ""))
    assert "Indique una placa válida para continuar el diagnóstico" not in resp3_str, (
        f"FALLO REPRODUCIDO Turno 3: Exigió placa en vez de responder al caso: {resp3_str}"
    )

    # ---------------- TURNO 4 ----------------
    t4_text = "No tengo la placa disponible en este momento. Ya te indiqué que es un Toyota Corolla 2015 y que presenta un chirrido al frenar suavemente. ¿Podemos continuar el diagnóstico con esa información sin perder el caso anterior?"
    r4 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-4", texto_cliente=t4_text, proveedor="api",
    )
    assert r4 is not None
    resp4_str = str(r4.get("respuesta", ""))
    assert "no dispongo de información suficientemente verificada para indicar ese procedimiento" not in resp4_str, (
        f"FALLO REPRODUCIDO Turno 4: Disparó fallback OEM de procedimiento: {resp4_str}"
    )
    assert "Indique una placa válida para continuar el diagnóstico" not in resp4_str


# ==============================================================================
# TEST 6: CASO "NEUVO CASO" Y NISSAN SENTRA 2018 (EVIDENCIA ADICIONAL FASE 12)
# ==============================================================================

@pytest.mark.anyio
async def test_reproduccion_evidencia_adicional_nissan_sentra_y_typo(monkeypatch):
    """Reproduce y valida la evidencia adicional reportada en Fase 12:
    1. 'NEUVO CASO' (con typo) no debe rebotar con error rígido de placa inválida.
    2. Solicitud de cerrar diagnóstico anterior y comenzar con otro vehículo.
    3. Párrafo con Nissan Sentra 2018 y síntomas de aceleración sin placa no debe bloquearse.
    """
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "conversation_state": {
                "session_id": "prev-session",
                "dominio_probable": "FRENOS",
                "active_system": "FRENOS",
            },
            "posttest_placa_pendiente": True,  # Sesión previa dejó gate de placa activo
        },
    )
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

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)

    # ---------------- TURNO 1: 'NEUVO CASO' (con typo) ----------------
    t1_text = "NEUVO CASO"
    r1 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-nissan-1", texto_cliente=t1_text, proveedor="api",
    )
    assert r1 is not None
    resp1_str = str(r1.get("respuesta", ""))
    # NO debe responder 'Indique una placa válida para continuar el diagnóstico.'
    assert "Indique una placa válida para continuar el diagnóstico." not in resp1_str, (
        f"FALLO REPRODUCIDO: 'NEUVO CASO' fue tratado como placa errónea: {resp1_str}"
    )
    assert "Nueva consulta iniciada" in resp1_str or "placa" in resp1_str.lower()

    # ---------------- TURNO 2: 'Quiero cerrar el diagnóstico anterior...' ----------------
    t2_text = "Quiero cerrar el diagnóstico anterior y comenzar un caso completamente nuevo con otro vehículo."
    r2 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-nissan-2", texto_cliente=t2_text, proveedor="api",
    )
    assert r2 is not None
    resp2_str = str(r2.get("respuesta", ""))
    assert "Nueva consulta iniciada" in resp2_str

    # ---------------- TURNO 3: Descripción completa de Nissan Sentra 2018 con síntomas ----------------
    t3_text = (
        "Tengo un Nissan Sentra 2018 automático. Cuando acelero para subir una pendiente, el motor "
        "pierde fuerza y empieza a tironear. En terreno plano funciona mejor. No tengo ninguna luz "
        "de advertencia encendida en el tablero. ¿Qué podría estar pasando?"
    )
    r3 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-nissan-3", texto_cliente=t3_text, proveedor="api",
    )
    assert r3 is not None
    resp3_str = str(r3.get("respuesta", ""))
    # CRÍTICO: NO debe bloquear exigiendo placa
    assert "Indique una placa válida para continuar el diagnóstico." not in resp3_str, (
        f"BLOQUEO REPRODUCIDO: Exigió placa en vez de diagnosticar el Nissan Sentra: {resp3_str}"
    )
    # Debe ser una respuesta diagnóstica
    assert r3.get("status") == "completado"
    # El perfil de vehículo debe haberse capturado
    perfil = conversacion.contexto.get("perfil_vehiculo", {})
    assert perfil.get("marca") == "Nissan"
    assert perfil.get("modelo") == "Sentra"
    assert perfil.get("anio") == "2018"
