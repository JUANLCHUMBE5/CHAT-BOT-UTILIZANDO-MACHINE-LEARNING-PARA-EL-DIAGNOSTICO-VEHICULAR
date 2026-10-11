"""
Pruebas exhaustivas para la Fase 4:
Worker de Gemini, gestión segura de cuotas, concurrencia transaccional,
reintentos controlados, recuperación tras reinicios y fallback degradado ML+RAG observable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.gemini_queue import GeminiRateLimiter, SolicitudGeminiEncolada
from src.core.gemini_queue.db_persistence import (
    posponer_trabajo_por_cuota_db,
    registrar_intento_ejecucion_db,
)
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.models.jobs import TrabajoGemini
from src.infrastructure.database.models.messaging import Conversacion
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.trabajo_gemini_repository import TrabajoGeminiRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@pytest.mark.anyio
async def test_separacion_reserva_cuota_e_intento_real(async_db_session: AsyncSession) -> None:
    """Verifica que reservar y posponer por cuota NO modifiquen los intentos del trabajo."""
    repo = TrabajoGeminiRepository(async_db_session)
    trabajo = await repo.crear_trabajo(
        sintoma="falla de encendido cilindro 1",
        diagnostico_ml="Bobina de encendido defectuosa",
        proveedor="api",
    )
    trabajo_id = trabajo.id
    await async_db_session.commit()

    assert trabajo.intentos == 0

    # 1. Reserva atómica: el lease se adquiere pero NO se cobra intento de API
    bloqueado = await repo.obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=45)
    assert bloqueado is not None
    assert bloqueado.id == trabajo_id
    assert bloqueado.estado == "procesando"
    assert bloqueado.intentos == 0
    await async_db_session.commit()

    # 2. Sin cuota disponible: posponer por cuota
    pospuesto = await repo.posponer_por_cuota(trabajo_id, espera_segundos=10, motivo="rpm_excedido")
    assert pospuesto is True
    await async_db_session.commit()

    revisado = await repo.obtener_por_id(trabajo_id)
    assert revisado is not None
    assert revisado.estado == "pendiente_reintento"
    assert revisado.intentos == 0  # Cero intentos cobrados
    assert revisado.bloqueado_hasta is None
    assert revisado.error_ultimo == "rpm_excedido"

    # 3. Registro explícito de intento real hacia el proveedor
    await repo.registrar_intento_ejecucion(trabajo_id)
    await async_db_session.commit()

    con_intento = await repo.obtener_por_id(trabajo_id)
    assert con_intento is not None
    assert con_intento.intentos == 1

    # Limpieza
    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == trabajo_id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_recuperacion_tras_reinicio_conserva_intentos(async_db_session: AsyncSession) -> None:
    """Un trabajo abandonado por caída de proceso no infla indebidamente sus intentos al reanudarse."""
    repo = TrabajoGeminiRepository(async_db_session)
    trabajo = await repo.crear_trabajo(
        sintoma="perdida de potencia en subida",
        diagnostico_ml="Catalizador obstruido",
        proveedor="api",
    )
    trabajo_id = trabajo.id
    trabajo.estado = "procesando"
    trabajo.intentos = 1
    trabajo.bloqueado_hasta = datetime.now(timezone.utc) - timedelta(seconds=5)
    await async_db_session.commit()

    # Worker tras reinicio toma el trabajo vencido
    recuperado = await repo.obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=60)
    assert recuperado is not None
    assert recuperado.id == trabajo_id
    assert recuperado.estado == "procesando"
    assert recuperado.intentos == 1  # No se incrementó a 2 antes de iniciar la llamada

    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == trabajo_id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_max_intentos_excedidos_activa_fallback_degradado(
    async_db_session: AsyncSession,
) -> None:
    """Cuando un trabajo alcanza el límite de intentos, debe forzar modo degradado ML+RAG y completarse."""
    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)
    diag_repo = DiagnosticoRepository(async_db_session)
    trabajo_repo = TrabajoGeminiRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre=f"Taller Max Retry {uuid.uuid4().hex[:6]}")
    roles = await usuario_repo.asegurar_roles_estandar()
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Mecanico Retry",
        whatsapp_hash=uuid.uuid4().hex * 2,
        whatsapp_ultimos4="0099",
    )
    ahora = datetime.now(timezone.utc)
    conv = Conversacion(
        id=uuid.uuid4(),
        taller_id=taller.id,
        usuario_id=usuario.id,
        canal="api",
        estado="abierta",
        iniciada_en=ahora,
        ultimo_mensaje_en=ahora,
        ventana_servicio_hasta=ahora + timedelta(hours=24),
    )
    async_db_session.add(conv)
    await async_db_session.flush()

    diag = await diag_repo.crear_diagnostico(
        taller_id=taller.id,
        mecanico_id=usuario.id,
        conversacion_id=conv.id,
        sintoma_original="El auto recalienta en subidas",
        falla_predicha="Termostato trabado cerrado",
        confianza=0.88,
        fuente="hibrido",
        modo_diagnostico="en_cola_gemini",
    )

    trabajo = await trabajo_repo.crear_trabajo(
        sintoma=diag.sintoma_original,
        diagnostico_ml=diag.falla_predicha,
        confianza_ml=0.88,
        contexto_manual="Revisar apertura de termostato",
        titulo_manual="Refrigeración",
        taller_id=taller.id,
        usuario_id=usuario.id,
        conversacion_id=conv.id,
        diagnostico_id=diag.id,
        proveedor="api",
    )
    trabajo.intentos = 3  # Ya alcanzó el máximo
    await async_db_session.commit()

    solicitud = SolicitudGeminiEncolada(
        id=str(trabajo.id),
        diagnostico_id=str(diag.id),
        taller_id=str(taller.id),
        usuario_id=str(usuario.id),
        conversacion_id=str(conv.id),
        sintoma=trabajo.sintoma,
        diagnostico_ml=trabajo.diagnostico_ml,
        confianza_ml=0.88,
        contexto_manual=trabajo.contexto_manual,
        titulo_manual=trabajo.titulo_manual,
        motivo_degradado="max_intentos_excedido",
    )

    limiter = GeminiRateLimiter()
    # Ejecutar en modo forzado por reintentos agotados
    texto, meta = await limiter._procesar_solicitud_encolada(solicitud, forzar_degradado=True)

    assert "Modo Degradado ML+RAG" in texto
    assert meta["modo"] == "diagnostico_degradado_ml_rag"
    assert meta["motivo_degradado"] == "max_intentos_excedido"
    assert meta["usado"] is False

    # Verificar que el trabajo en DB quedó completado
    trabajo_id_val = trabajo.id
    diag_id_val = diag.id
    taller_id_val = taller.id
    usuario_id_val = usuario.id

    async_db_session.expire_all()
    trabajo_final = await trabajo_repo.obtener_por_id(trabajo_id_val)
    assert trabajo_final is not None
    assert trabajo_final.estado == "completado"

    # Verificar observabilidad en diagnóstico
    diag_final = await diag_repo.obtener_por_id(diag_id_val)
    assert diag_final is not None
    assert diag_final.modo_diagnostico == "diagnostico_degradado_ml_rag"
    assert diag_final.trazabilidad["gemini"]["motivo_degradado"] == "max_intentos_excedido"

    # Limpieza
    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.taller_id == taller_id_val))
    await async_db_session.execute(delete(Diagnostico).where(Diagnostico.taller_id == taller_id_val))
    await async_db_session.execute(delete(Conversacion).where(Conversacion.taller_id == taller_id_val))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario_id_val))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller_id_val))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_concurrencia_skip_locked_dos_workers(async_db_session: AsyncSession) -> None:
    """Dos workers concurrentes bloquean trabajos distintos sin competir ni colisionar."""
    from src.infrastructure.database.connection import obtener_engine

    repo = TrabajoGeminiRepository(async_db_session)
    t1 = await repo.crear_trabajo(sintoma="falla 1", diagnostico_ml="d1", proveedor="api")
    t2 = await repo.crear_trabajo(sintoma="falla 2", diagnostico_ml="d2", proveedor="api")
    await async_db_session.commit()
    t1_id = t1.id
    t2_id = t2.id

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as s1, AsyncSession(engine, expire_on_commit=False) as s2:
        async with s1.begin(), s2.begin():
            r1 = await TrabajoGeminiRepository(s1).obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=30)
            r2 = await TrabajoGeminiRepository(s2).obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=30)

            assert r1 is not None
            assert r2 is not None
            assert r1.id != r2.id
            assert {r1.id, r2.id} == {t1_id, t2_id}

    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id.in_([t1_id, t2_id])))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_cuota_saturada_rpm_pospone_sin_quemar_intentos(async_db_session: AsyncSession) -> None:
    """Saturación temporal por RPM pospone el trabajo liberando el lease sin quemar intentos."""
    repo = TrabajoGeminiRepository(async_db_session)
    trabajo = await repo.crear_trabajo(
        sintoma="humo blanco por escape",
        diagnostico_ml="Empaque de culata soplado",
        proveedor="api",
    )
    trabajo_id = trabajo.id
    await async_db_session.commit()

    # Worker reserva el trabajo
    bloqueado = await repo.obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=30)
    assert bloqueado is not None
    assert bloqueado.intentos == 0
    await async_db_session.commit()

    # Slot rechazado por RPM: se pospone a nivel de BD
    await posponer_trabajo_por_cuota_db(str(trabajo_id), motivo="rpm_excedido (12/12 min)")

    async_db_session.expire_all()
    actualizado = await repo.obtener_por_id(trabajo_id)
    assert actualizado is not None
    assert actualizado.estado == "pendiente_reintento"
    assert actualizado.intentos == 0
    assert actualizado.bloqueado_hasta is None
    assert "rpm_excedido" in (actualizado.error_ultimo or "")

    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == trabajo_id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_intento_real_se_incrementa_al_ejecutar_gemini(async_db_session: AsyncSession) -> None:
    """El contador de intentos solo se incrementa al iniciar la invocación real al LLM."""
    repo = TrabajoGeminiRepository(async_db_session)
    trabajo = await repo.crear_trabajo(
        sintoma="luz de check engine parpadea",
        diagnostico_ml="Falla de encendido múltiple",
        proveedor="api",
    )
    trabajo_id = trabajo.id
    await async_db_session.commit()

    assert trabajo.intentos == 0

    await registrar_intento_ejecucion_db(str(trabajo_id))

    async_db_session.expire_all()
    actualizado = await repo.obtener_por_id(trabajo_id)
    assert actualizado is not None
    assert actualizado.intentos == 1

    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == trabajo_id))
    await async_db_session.commit()

