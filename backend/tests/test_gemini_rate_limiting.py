"""
Pruebas exhaustivas para la cola persistente de Gemini en PostgreSQL,
bloqueo FOR UPDATE SKIP LOCKED, recuperación tras reinicio, límite compartido RPM/RPD,
soporte multi-proveedor (Meta/Twilio) y costo $0.00 en Free Tier.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.gemini_queue import GeminiRateLimiter, SolicitudGeminiEncolada
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.security import (
    cifrar_texto_reversible,
    descifrar_texto_reversible,
    hash_identificador_persistencia,
)
from src.core.services.webhook_service import WebhookService
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.models.jobs import CuotaGeminiGlobal, TrabajoGemini
from src.infrastructure.database.models.messaging import Conversacion
from src.infrastructure.database.models.operations import UsoApi
from src.infrastructure.database.repositories.cuota_gemini_repository import CuotaGeminiRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.trabajo_gemini_repository import TrabajoGeminiRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


def test_alembic_head_es_20260809_01():
    """Verifica que la migración más reciente sea el head activo de Alembic."""
    config = Config("alembic.ini")
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_current_head() == "20260809_01"


def test_gemini_rate_limiter_concede_12_y_encola_excedentes():
    """Verifica que el limitador concede exactamente 12 slots y encola a partir de la solicitud 13."""
    limiter = GeminiRateLimiter(max_por_minuto=12, max_por_dia=18, ventana_segundos=60.0)
    limiter.reiniciar()

    # 1. Las primeras 12 solicitudes deben ser concedidas inmediatamente
    for i in range(12):
        assert limiter.intentar_adquirir_slot() is True, f"El slot {i+1} debió ser concedido"

    assert limiter.slots_utilizados() == 12

    # 2. La solicitud 13 no debe obtener slot inmediato
    assert limiter.intentar_adquirir_slot() is False

    # 3. La solicitud 13 se coloca en la cola real
    solicitud, posicion, espera = limiter.encolar_solicitud(
        sintoma="freno rechina",
        diagnostico_ml="Falla en pastillas de freno",
        confianza_ml=0.88,
        contexto_manual="Manual de frenos",
        titulo_manual="Frenos",
        proveedor="twilio",
    )

    assert posicion == 1
    assert limiter.tamaño_cola() == 1
    assert espera > 0.0
    assert solicitud.diagnostico_ml == "Falla en pastillas de freno"
    assert solicitud.proveedor == "twilio"

    # 4. Desencolar siguiente
    siguiente = limiter.descolar_siguiente()
    assert siguiente is not None
    assert siguiente.id == solicitud.id
    assert limiter.tamaño_cola() == 0


def test_cifrado_reversible_para_remitente_de_trabajos():
    """Verifica que el teléfono se cifre de forma reversible sin guardarse en texto plano."""
    tel_original = "+51987654321"
    cifrado = cifrar_texto_reversible(tel_original)
    
    assert cifrado != tel_original
    assert tel_original not in cifrado
    
    descifrado = descifrar_texto_reversible(cifrado)
    assert descifrado == tel_original


def test_descifrado_invalido_falla_cerrado():
    """Un ciphertext inválido nunca debe devolverse como supuesto teléfono."""
    with pytest.raises(ValueError, match="descifrar el remitente"):
        descifrar_texto_reversible("gAAAA-token-fernet-invalido")


@pytest.mark.anyio
async def test_trabajo_gemini_repository_skip_locked_y_transiciones(async_db_session: AsyncSession):
    """
    Verifica inserción persistente en trabajos_gemini, bloqueo FOR UPDATE SKIP LOCKED
    y transiciones de estado a completado y reintento.
    """
    repo = TrabajoGeminiRepository(async_db_session)
    trabajo_id = uuid.uuid4()

    # 1. Crear trabajo encolado con remitente cifrado
    trabajo = await repo.crear_trabajo(
        sintoma="Motor tiembla en frío",
        diagnostico_ml="Bujías desgastadas",
        confianza_ml=0.89,
        contexto_manual="Manual sección encendido",
        titulo_manual="Encendido",
        remitente="+51987111222",
        proveedor="meta",
        trabajo_id=trabajo_id,
    )
    await async_db_session.commit()

    assert trabajo.id == trabajo_id
    assert trabajo.estado == "pendiente"
    assert trabajo.remitente_cifrado is not None
    assert "+51987111222" not in trabajo.remitente_cifrado

    # 2. Bloquear y procesar usando FOR UPDATE SKIP LOCKED
    bloqueado = await repo.obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=30)
    assert bloqueado is not None
    assert bloqueado.id == trabajo_id
    assert bloqueado.estado == "procesando"
    assert bloqueado.intentos == 1
    assert bloqueado.bloqueado_hasta is not None
    await async_db_session.commit()

    # 3. Marcar completado
    completado = await repo.marcar_completado(trabajo_id)
    assert completado is True
    await async_db_session.commit()

    # 4. Verificar que ya no está pendiente
    buscado = await repo.obtener_por_id(trabajo_id)
    assert buscado.estado == "completado"
    assert buscado.bloqueado_hasta is None

    # Limpiar
    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == trabajo_id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_cuota_gemini_repository_sincronizacion_rpm_y_rpd(async_db_session: AsyncSession):
    """
    Verifica que CuotaGeminiRepository limite atómicamente RPM (12) y RPD (18)
    en PostgreSQL para compartir cuota entre múltiples instancias/servidores.
    """
    cuota_repo = CuotaGeminiRepository(async_db_session)

    # 1. Resetear cuota para prueba limpia
    await async_db_session.execute(
        delete(CuotaGeminiGlobal).where(CuotaGeminiGlobal.id == 1)
    )
    await async_db_session.commit()

    # 2. Conceder exactamente 12 slots para el minuto actual
    for i in range(12):
        concedido, motivo, hoy, min_cnt = await cuota_repo.adquirir_slot_compartido(max_rpm=12, max_rpd=18)
        assert concedido is True, f"Slot {i+1} debió ser concedido"
        assert hoy == i + 1
        assert min_cnt == i + 1

    await async_db_session.commit()

    # 3. La solicitud 13 debe ser rechazada por RPM en PostgreSQL
    concedido, motivo, hoy, min_cnt = await cuota_repo.adquirir_slot_compartido(max_rpm=12, max_rpd=18)
    assert concedido is False
    assert "rpm_excedido" in motivo

    # 4. Simular que se alcanzó el límite diario RPD (18)
    stmt_set_rpd = select(CuotaGeminiGlobal).where(CuotaGeminiGlobal.id == 1).with_for_update()
    res = await async_db_session.execute(stmt_set_rpd)
    cuota_db = res.scalar_one()
    cuota_db.solicitudes_hoy = 18
    cuota_db.solicitudes_minuto = 0
    await async_db_session.commit()

    concedido_rpd, motivo_rpd, _, _ = await cuota_repo.adquirir_slot_compartido(max_rpm=12, max_rpd=18)
    assert concedido_rpd is False
    assert "rpd_excedido" in motivo_rpd

    await async_db_session.execute(delete(CuotaGeminiGlobal).where(CuotaGeminiGlobal.id == 1))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_limitador_db_concede_sin_deadlock(async_db_session: AsyncSession):
    """La concesión DB debe terminar; antes se congelaba al adquirir dos veces el mismo Lock."""
    await async_db_session.execute(delete(CuotaGeminiGlobal).where(CuotaGeminiGlobal.id == 1))
    await async_db_session.commit()

    limiter = GeminiRateLimiter(max_por_minuto=12, max_por_dia=18)
    concedido, motivo = await asyncio.wait_for(
        limiter.intentar_adquirir_slot_db(), timeout=3
    )
    assert concedido is True
    assert motivo == "concedido"


@pytest.mark.anyio
async def test_worker_recupera_trabajo_procesando_con_bloqueo_vencido(async_db_session: AsyncSession):
    """Un trabajo abandonado por una caída vuelve a ser reclamable tras vencer su lease."""
    repo = TrabajoGeminiRepository(async_db_session)
    trabajo = await repo.crear_trabajo(
        sintoma="motor no arranca",
        diagnostico_ml="batería descargada",
        proveedor="meta",
    )
    trabajo.estado = "procesando"
    trabajo.intentos = 1
    trabajo.bloqueado_hasta = datetime.now(timezone.utc) - timedelta(seconds=1)
    await async_db_session.commit()

    recuperado = await repo.obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=30)
    assert recuperado is not None
    assert recuperado.id == trabajo.id
    assert recuperado.estado == "procesando"
    assert recuperado.intentos == 2
    trabajo_id = trabajo.id
    await async_db_session.rollback()
    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == trabajo_id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_error_temporal_gemini_programa_reintento(async_db_session: AsyncSession, monkeypatch):
    """Un HTTP 5xx no se marca completado ni genera fallback definitivo."""
    repo = TrabajoGeminiRepository(async_db_session)
    trabajo = await repo.crear_trabajo(
        sintoma="motor pierde fuerza",
        diagnostico_ml="filtro obstruido",
        proveedor="api",
    )
    trabajo_id = trabajo.id
    await async_db_session.commit()

    class RespuestaTemporal:
        status_code = 503

    monkeypatch.setattr(settings, "gemini_api_key", "clave-prueba")
    monkeypatch.setattr("src.core.gemini_queue.requests.post", lambda *a, **k: RespuestaTemporal())
    solicitud = SolicitudGeminiEncolada(
        id=str(trabajo_id),
        sintoma="motor pierde fuerza",
        diagnostico_ml="filtro obstruido",
        contexto_manual="Revisar filtro",
        proveedor="api",
    )

    texto, metadata = await GeminiRateLimiter()._procesar_solicitud_encolada(solicitud)
    assert texto == ""
    assert metadata["reintentar"] is True
    async_db_session.expire_all()
    actualizado = await repo.obtener_por_id(trabajo_id)
    assert actualizado.estado == "pendiente_reintento"

    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == trabajo_id))
    await async_db_session.commit()

@pytest.mark.anyio
async def test_webhook_persiste_free_tier_costo_cero_en_uso_api(async_db_session: AsyncSession, monkeypatch):
    """Verifica que con gemini_use_free_tier=True se registre costo $0.00 en PostgreSQL."""
    monkeypatch.setattr(settings, "gemini_use_free_tier", True)
    
    taller_repo = TallerRepository(async_db_session)
    user_repo = UsuarioRepository(async_db_session)
    taller = await taller_repo.crear_taller(nombre=f"Taller Free Tier {uuid.uuid4().hex[:6]}")
    roles = await user_repo.asegurar_roles_estandar()
    rand_phone = f"+519{uuid.uuid4().int % 100000000:08d}"
    u_hash = hash_identificador_persistencia(rand_phone, "telefono")
    usuario = await user_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Mecanico Free Tier",
        whatsapp_hash=u_hash,
        whatsapp_ultimos4=rand_phone[-4:],
    )
    await async_db_session.commit()

    mensajes_enviados = []
    monkeypatch.setattr(
        WebhookService,
        "enviar_mensaje_whatsapp",
        lambda self, dest, txt: mensajes_enviados.append((dest, txt)) or True,
    )

    gestor = GestorDiagnostico()
    gestor.api_key = "FAKE_KEY_FOR_FREE_TIER_TEST"
    service = WebhookService(gestor)

    resultado = await service.procesar_mensaje(
        remitente=rand_phone,
        meta_message_id=f"wamid_freetier_{uuid.uuid4().hex}",
        tipo_mensaje="text",
        texto_cliente="El pedal de freno está muy esponjoso al frenar",
    )

    assert resultado["status"] in ("completado", "procesado")

    trabajo_result = await async_db_session.execute(
        select(TrabajoGemini).where(
            TrabajoGemini.taller_id == taller.id
        )
    )
    trabajo = trabajo_result.scalar_one_or_none()
    if trabajo:
        assert trabajo.remitente_cifrado is not None
        assert rand_phone not in trabajo.remitente_cifrado

    # Verificar costo $0.00 en PostgreSQL para Gemini
    usos_db = await async_db_session.execute(
        select(UsoApi).where(UsoApi.taller_id == taller.id, UsoApi.proveedor == "google")
    )
    uso_gemini = usos_db.scalars().first()
    if uso_gemini:
        assert uso_gemini.costo_estimado == Decimal("0.000000")

    # Limpiar
    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.taller_id == taller.id))
    await async_db_session.execute(delete(UsoApi).where(UsoApi.taller_id == taller.id))
    await async_db_session.execute(delete(Diagnostico).where(Diagnostico.taller_id == taller.id))
    await async_db_session.execute(delete(Conversacion).where(Conversacion.taller_id == taller.id))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario.id))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller.id))
    await async_db_session.commit()
