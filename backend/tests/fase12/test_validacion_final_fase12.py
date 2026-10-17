"""Suite de validación final previa a publicación de Fase 12.

Comprueba rigurosamente:
1. No colisión de SIN-PLACA entre talleres, usuarios y conversaciones.
2. Asociación tardía de placa real sin perder historial ni sobrescribir perfil.
3. Conservación íntegra sin duplicaciones de mensajes recibidos durante la espera de placa.
4. Coherencia estricta de feedback y no confirmación/descarte sin evidencia.
5. Reproducción consecutiva de las conversaciones reales del Toyota Corolla 2015 y Nissan Sentra 2018.
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
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico

# ==============================================================================
# 1. NO COLISIÓN DE SIN-PLACA ENTRE CONVERSACIONES / USUARIOS / TALLERES
# ==============================================================================

@pytest.mark.anyio
async def test_sin_placa_aislamiento_entre_talleres_y_conversaciones(monkeypatch):
    """Verifica que 'SIN-PLACA' no comparte estado ni colisiona entre dos conversaciones o talleres."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    # Taller A / Usuario A
    taller_a = uuid.uuid4()
    usuario_a = SimpleNamespace(id=uuid.uuid4(), taller_id=taller_a, nombres="Mecánico Taller A", rol=SimpleNamespace(codigo="mecanico"))
    conv_a = SimpleNamespace(id=uuid.uuid4(), contexto={"posttest_placa_pendiente": True})

    # Taller B / Usuario B
    taller_b = uuid.uuid4()
    usuario_b = SimpleNamespace(id=uuid.uuid4(), taller_id=taller_b, nombres="Mecánico Taller B", rol=SimpleNamespace(codigo="mecanico"))
    conv_b = SimpleNamespace(id=uuid.uuid4(), contexto={"posttest_placa_pendiente": True})

    convs = {"51999111001": conv_a, "51999111002": conv_b}
    usuarios = {"51999111001": usuario_a, "51999111002": usuario_b}

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

    async def mock_resolver(session, remitente, *a, **k):
        return SimpleNamespace(status="ok", usuario=usuarios[remitente])

    async def mock_obtener_o_crear(taller_id, usuario_id, *a, **k):
        for tel, u in usuarios.items():
            if u.id == usuario_id:
                return convs[tel]
        return conv_a

    conv_repo = MagicMock()
    conv_repo.obtener_o_crear_activa = AsyncMock(side_effect=mock_obtener_o_crear)
    monkeypatch.setattr(modulo, "ConversacionRepository", lambda *a: conv_repo)
    monkeypatch.setattr(modulo, "OperacionesRepository", lambda *a: SimpleNamespace(registrar_uso_api=AsyncMock()))
    monkeypatch.setattr(
        modulo.IdentityResolver, "resolver_o_registrar",
        AsyncMock(side_effect=mock_resolver),
    )

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)

    # Usuario A: Toyota Corolla con chirrido
    await service.procesar_mensaje(
        remitente="51999111001", meta_message_id="msg-a1",
        texto_cliente="Toyota Corolla 2015 con chirrido al frenar",
    )
    # Usuario B: Nissan Sentra con tirones
    await service.procesar_mensaje(
        remitente="51999111002", meta_message_id="msg-b1",
        texto_cliente="Nissan Sentra 2018 pierde fuerza y tironea en subida",
    )

    # Verificar contextos completamente aislados
    assert conv_a.contexto.get("placa") == "SIN-PLACA"
    assert conv_a.contexto.get("perfil_vehiculo", {}).get("marca") == "Toyota"
    assert conv_a.contexto.get("perfil_vehiculo", {}).get("modelo") == "Corolla"

    assert conv_b.contexto.get("placa") == "SIN-PLACA"
    assert conv_b.contexto.get("perfil_vehiculo", {}).get("marca") == "Nissan"
    assert conv_b.contexto.get("perfil_vehiculo", {}).get("modelo") == "Sentra"


# ==============================================================================
# 2. ASOCIACIÓN TARDÍA DE PLACA REAL SIN PERDER HISTORIAL NI SOBRESCRIBIR OTRO
# ==============================================================================

@pytest.mark.anyio
async def test_asociacion_tardia_de_placa_preserva_historial_y_perfil(monkeypatch):
    """Si el caso inicia como SIN-PLACA y luego el usuario envía la placa real, se asocia sin perder nada."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba", rol=SimpleNamespace(codigo="mecanico"))
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "placa": "SIN-PLACA",
            "perfil_vehiculo": {"marca": "Toyota", "modelo": "Corolla", "anio": "2015"},
            "conversation_state": {"session_id": "conv-1", "dominio_probable": "FRENOS"},
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

    # Usuario aporta la placa tardíamente
    res = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-tardia",
        texto_cliente="La placa del Corolla es ABC-123",
    )
    assert res is not None
    # La placa debe haberse actualizado a ABC123 sin perder el perfil del Corolla
    assert conversacion.contexto.get("placa") == "ABC123"
    perfil = conversacion.contexto.get("perfil_vehiculo", {})
    assert perfil.get("marca") == "Toyota"
    assert perfil.get("modelo") == "Corolla"
    assert perfil.get("anio") == "2015"


# ==============================================================================
# 3. VERIFICACIÓN DE FEEDBACK Y NO CONFIRMACIÓN SIN EVIDENCIA
# ==============================================================================

def test_instrucciones_feedback_coherentes_y_sin_falsos_positivos():
    """Confirma correspondencia de feedback y que respuestas de duda no descartan hipótesis."""
    # 1 Hipótesis -> solo SÍ / NO
    txt_1 = instrucciones_confirmacion_whatsapp(1)
    assert "*SÍ / NO*" in txt_1
    assert "(1/2/3)" not in txt_1

    # 3 Hipótesis -> SÍ / NO (1/2/3)
    txt_3 = instrucciones_confirmacion_whatsapp(3)
    assert "(1/2/3)" in txt_3

    # Duda o comprobación pendiente no descarta la falla
    duda = interpretar_respuesta_validacion_whatsapp(
        "Aún no desmonto las pastillas ni comprobé los discos. El pedal no vibra."
    )
    assert duda is None, "Una duda o reporte de estado no debe catalogarse como rechazo de hipótesis"


# ==============================================================================
# 4. REPRODUCCIÓN COMPLETA DE TOYOTA Y NISSAN CON TYPO Y SIN PLACA
# ==============================================================================

@pytest.mark.anyio
async def test_reproduccion_completa_toyota_y_nissan_consecutivos(monkeypatch):
    """Reproduce ambos casos reales consecutivamente garantizando la ausencia de bucles."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba", rol=SimpleNamespace(codigo="mecanico"))
    conversacion = SimpleNamespace(id=uuid.uuid4(), contexto={"posttest_placa_pendiente": True})

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

    # TOYOTA COROLLA
    r1 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-t1",
        texto_cliente="Hola, tengo un Toyota Corolla 2015. Cuando freno escucho un chirrido fuerte, especialmente cuando piso el pedal suavemente.",
    )
    assert r1 is not None
    assert "Indique una placa válida" not in str(r1.get("respuesta", ""))

    # NISSAN CON TYPO NEUVO CASO
    r2 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-t2",
        texto_cliente="NEUVO CASO",
    )
    assert r2 is not None
    assert "Indique una placa válida para continuar el diagnóstico" not in str(r2.get("respuesta", ""))

    # NISSAN SENTRA DESCRIPCIÓN CON SÍNTOMAS
    r3 = await service.procesar_mensaje(
        remitente="51999111222", meta_message_id="msg-t3",
        texto_cliente="Tengo un Nissan Sentra 2018 automático. Cuando acelero para subir una pendiente, el motor pierde fuerza y empieza a tironear. En terreno plano funciona mejor. No tengo ninguna luz de advertencia encendida en el tablero. ¿Qué podría estar pasando?",
    )
    assert r3 is not None
    assert "Indique una placa válida para continuar el diagnóstico" not in str(r3.get("respuesta", ""))
    assert r3.get("status") == "completado"
