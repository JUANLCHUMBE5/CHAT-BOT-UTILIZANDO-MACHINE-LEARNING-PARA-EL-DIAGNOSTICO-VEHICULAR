"""Regresiones de durabilidad para la cola Gemini, sin invocar servicios externos."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.diagnostico.response_generator import generar_respuesta_con_metadatos
from src.core.gemini_queue import GeminiRateLimiter, SolicitudGeminiEncolada
from src.core.gemini_queue.db_persistence import (
    actualizar_diagnostico_y_trabajo_db,
    persistir_solicitud_en_sesion_db,
)
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.models.jobs import TrabajoGemini
from src.infrastructure.database.models.messaging import Conversacion
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.trabajo_gemini_repository import TrabajoGeminiRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


class GestorConClave:
    api_key = "clave-de-prueba"


def test_no_devuelve_cola_efimera_sin_contexto_durable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un consumidor directo nunca recibe UUID en cola si no hay transacción durable."""
    limiter = GeminiRateLimiter()
    monkeypatch.setattr(limiter, "intentar_adquirir_slot", lambda: False)
    monkeypatch.setattr(
        "src.core.diagnostico.response_generator.gemini_rate_limiter",
        limiter,
    )

    _, metadatos = generar_respuesta_con_metadatos(
        GestorConClave(),
        pregunta="El motor tironea al acelerar",
        diagnostico_ml="Falla de encendido",
        contexto_manual="Inspeccionar encendido.",
        confianza_ml=0.8,
        diferir_encolado_persistente=False,
    )

    assert metadatos["modo"] == "diagnostico_degradado_ml_rag"
    assert "solicitud_id" not in metadatos
    assert len(limiter._cola_pendientes) == 0


@pytest.mark.anyio
async def test_uuid_encolado_es_durable_y_el_worker_puede_finalizarlo(
    async_db_session: AsyncSession,
) -> None:
    """El UUID persistido conserva diagnóstico/conversación antes y después del worker."""
    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)
    diagnostico_repo = DiagnosticoRepository(async_db_session)
    trabajo_repo = TrabajoGeminiRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre=f"Taller cola {uuid.uuid4().hex[:8]}")
    roles = await usuario_repo.asegurar_roles_estandar()
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Mecanico cola",
        whatsapp_hash=uuid.uuid4().hex * 2,
        whatsapp_ultimos4="0001",
    )
    ahora = datetime.now(timezone.utc)
    conversacion = Conversacion(
        id=uuid.uuid4(),
        taller_id=taller.id,
        usuario_id=usuario.id,
        canal="api",
        estado="abierta",
        iniciada_en=ahora,
        ultimo_mensaje_en=ahora,
        ventana_servicio_hasta=ahora + timedelta(hours=24),
        contexto={},
    )
    async_db_session.add(conversacion)
    await async_db_session.flush()
    diagnostico = await diagnostico_repo.crear_diagnostico(
        taller_id=taller.id,
        mecanico_id=usuario.id,
        conversacion_id=conversacion.id,
        sintoma_original="El motor pierde fuerza",
        falla_predicha="Filtro de combustible obstruido",
        confianza=0.8,
        fuente="hibrido",
        modo_diagnostico="en_cola_gemini",
        trazabilidad={"tiempo_total_ms": 10},
        tipo_registro="DEVELOPMENT",
    )
    solicitud_id = str(uuid.uuid4())
    await persistir_solicitud_en_sesion_db(
        async_db_session,
        solicitud_id=solicitud_id,
        sintoma=diagnostico.sintoma_original,
        diagnostico_ml=diagnostico.falla_predicha or "Sin prediccion",
        confianza_ml=0.8,
        contexto_manual="Verificar presion de combustible.",
        titulo_manual="Alimentacion",
        requiere_revision_humana=False,
        proveedor="api",
        taller_id=str(taller.id),
        usuario_id=str(usuario.id),
        conversacion_id=str(conversacion.id),
        diagnostico_id=str(diagnostico.id),
    )
    await async_db_session.commit()
    diagnostico_id = diagnostico.id
    conversacion_id = conversacion.id
    usuario_id = usuario.id
    taller_id = taller.id

    persistido = await trabajo_repo.obtener_por_id(uuid.UUID(solicitud_id))
    assert persistido is not None
    assert persistido.diagnostico_id == diagnostico.id
    assert persistido.conversacion_id == conversacion.id

    recuperado = await trabajo_repo.obtener_siguiente_pendiente_bloqueado()
    assert recuperado is not None
    assert recuperado.id == persistido.id
    await async_db_session.commit()

    solicitud = SolicitudGeminiEncolada(
        id=solicitud_id,
        diagnostico_id=str(diagnostico_id),
        conversacion_id=str(conversacion_id),
        taller_id=str(taller_id),
        usuario_id=str(usuario_id),
        proveedor="api",
        sintoma="El motor pierde fuerza",
        diagnostico_ml="Filtro de combustible obstruido",
        confianza_ml=0.8,
    )
    await actualizar_diagnostico_y_trabajo_db(
        solicitud,
        "Resultado durable de prueba.",
        {"usado": False, "modo": "diagnostico_degradado_ml_rag", "tiempo_llm_ms": 4},
    )

    async_db_session.expire_all()
    final = await trabajo_repo.obtener_por_id(uuid.UUID(solicitud_id))
    diagnostico_final = await diagnostico_repo.obtener_por_id(diagnostico_id)
    assert final is not None and final.estado == "completado"
    assert final.diagnostico_id == diagnostico_id
    assert final.conversacion_id == conversacion_id
    assert diagnostico_final is not None
    assert diagnostico_final.sintesis_llm == "Resultado durable de prueba."

    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.id == final.id))
    await async_db_session.execute(delete(Diagnostico).where(Diagnostico.id == diagnostico_id))
    await async_db_session.execute(delete(Conversacion).where(Conversacion.id == conversacion_id))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario_id))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller_id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_rest_flujo_completo_a_b_c_d(
    async_db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prueba A, B, C, D: encolado vía REST persiste UUID, worker lo procesa y resultado es durable."""
    from starlette.requests import Request

    from src.core.gemini_queue import gemini_rate_limiter
    from src.core.gestor_diagnostico import GestorDiagnostico
    from src.infrastructure.database.models.diagnostics import HipotesisDiagnostico, Vehiculo
    from src.interfaces.api.v1.endpoints.diagnostico import analizar_sintoma
    from src.interfaces.api.v1.schemas import ConsultaDiagnostico

    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)
    trabajo_repo = TrabajoGeminiRepository(async_db_session)
    diag_repo = DiagnosticoRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre=f"Taller REST {uuid.uuid4().hex[:8]}")
    roles = await usuario_repo.asegurar_roles_estandar()
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Mecanico REST",
        whatsapp_hash=uuid.uuid4().hex * 2,
        whatsapp_ultimos4="0002",
    )
    taller_id_val = taller.id
    usuario_id_val = usuario.id
    await async_db_session.commit()

    # Forzar que el slot no esté disponible para gatillar el encolado
    async def slot_bloqueado():
        return False, "rpd_excedido"

    monkeypatch.setattr(gemini_rate_limiter, "intentar_adquirir_slot_db", slot_bloqueado)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/diagnostico/analizar",
        "headers": [],
        "client": ("127.0.0.1", 12345),
    }
    dummy_request = Request(scope)
    consulta = ConsultaDiagnostico(
        sintoma="El motor tiembla en ralenti, bota humo negro por el escape y el escaner arroja codigo P0301",
        placa="DEV-DUR01",
        marca="Toyota",
        modelo="Yaris",
    )
    payload = {"taller_id": str(taller_id_val), "usuario_id": str(usuario_id_val)}

    gestor = GestorDiagnostico()
    gestor.api_key = "clave-simulada"

    resultado = await analizar_sintoma(
        request=dummy_request,
        consulta=consulta,
        token_payload=payload,
        gestor=gestor,
    )

    # Condición A: si devuelve en_cola_gemini, el UUID existe realmente en DB
    assert resultado.modo_diagnostico == "en_cola_gemini"
    assert resultado.solicitud_id is not None
    assert resultado.diagnostico_id is not None
    solicitud_uuid = uuid.UUID(resultado.solicitud_id)
    diag_uuid = uuid.UUID(resultado.diagnostico_id)

    async_db_session.expire_all()
    trabajo_db = await trabajo_repo.obtener_por_id(solicitud_uuid)
    assert trabajo_db is not None
    assert trabajo_db.id == solicitud_uuid

    # Condición D: se conserva asociación con conversación y diagnóstico
    assert trabajo_db.diagnostico_id == diag_uuid
    assert trabajo_db.conversacion_id is not None

    diag_db = await diag_repo.obtener_por_id(diag_uuid)
    assert diag_db is not None
    assert diag_db.conversacion_id == trabajo_db.conversacion_id
    assert diag_db.modo_diagnostico == "en_cola_gemini"

    # Condición B: el worker puede recuperar ese mismo UUID
    recuperado = await trabajo_repo.obtener_siguiente_pendiente_bloqueado()
    assert recuperado is not None
    assert recuperado.id == solicitud_uuid
    await async_db_session.commit()

    # Condición C: después de procesarlo existe resultado durable
    solicitud_worker = SolicitudGeminiEncolada(
        id=resultado.solicitud_id,
        diagnostico_id=resultado.diagnostico_id,
        conversacion_id=str(trabajo_db.conversacion_id),
        taller_id=str(taller_id_val),
        usuario_id=str(usuario_id_val),
        proveedor="api",
        sintoma=consulta.sintoma,
        diagnostico_ml=resultado.falla_predicha,
        confianza_ml=resultado.confianza / 100.0,
    )
    await actualizar_diagnostico_y_trabajo_db(
        solicitud_worker,
        "Diagnóstico sintetizado final por el worker.",
        {"usado": True, "modelo": "gemini-2.0-flash", "tiempo_llm_ms": 15},
    )

    async_db_session.expire_all()
    trabajo_final = await trabajo_repo.obtener_por_id(solicitud_uuid)
    diag_final = await diag_repo.obtener_por_id(diag_uuid)

    assert trabajo_final is not None and trabajo_final.estado == "completado"
    assert trabajo_final.diagnostico_id == diag_uuid
    assert trabajo_final.conversacion_id == trabajo_db.conversacion_id

    assert diag_final is not None
    assert diag_final.sintesis_llm == "Diagnóstico sintetizado final por el worker."
    assert diag_final.modo_diagnostico == "completo_ml_rag_llm"

    # Limpieza
    from src.infrastructure.database.models.operations import UsoApi
    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.taller_id == taller_id_val))
    await async_db_session.execute(delete(UsoApi).where(UsoApi.taller_id == taller_id_val))
    await async_db_session.execute(delete(HipotesisDiagnostico).where(HipotesisDiagnostico.diagnostico_id == diag_uuid))
    await async_db_session.execute(delete(Diagnostico).where(Diagnostico.taller_id == taller_id_val))
    await async_db_session.execute(delete(Vehiculo).where(Vehiculo.taller_id == taller_id_val))
    await async_db_session.execute(delete(Conversacion).where(Conversacion.taller_id == taller_id_val))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario_id_val))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller_id_val))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_e_fallo_insert_commit_en_rest_nunca_devuelve_en_cola_gemini(
    async_db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Condición E: si el INSERT/commit falla, el endpoint lanza error 500 y nunca devuelve éxito en cola."""
    from fastapi import HTTPException
    from starlette.requests import Request

    from src.core.gemini_queue import gemini_rate_limiter
    from src.core.gestor_diagnostico import GestorDiagnostico
    from src.infrastructure.database.models.diagnostics import HipotesisDiagnostico, Vehiculo
    from src.interfaces.api.v1.endpoints.diagnostico import analizar_sintoma
    from src.interfaces.api.v1.schemas import ConsultaDiagnostico

    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre=f"Taller Error {uuid.uuid4().hex[:8]}")
    roles = await usuario_repo.asegurar_roles_estandar()
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Mecanico Error",
        whatsapp_hash=uuid.uuid4().hex * 2,
        whatsapp_ultimos4="0003",
    )
    taller_id_val = taller.id
    usuario_id_val = usuario.id
    await async_db_session.commit()

    async def slot_bloqueado():
        return False, "rpd_excedido"

    monkeypatch.setattr(gemini_rate_limiter, "intentar_adquirir_slot_db", slot_bloqueado)

    # Inducir fallo en persistencia del trabajo
    async def fallo_persistir(*args, **kwargs):
        raise RuntimeError("Fallo catastrófico simulado en la base de datos durante INSERT/commit")

    monkeypatch.setattr(gemini_rate_limiter, "persistir_solicitud_en_sesion", fallo_persistir)

    dummy_request = Request({"type": "http", "method": "POST", "path": "/api/v1/diagnostico/analizar", "headers": [], "client": ("127.0.0.1", 12345)})
    consulta = ConsultaDiagnostico(
        sintoma="El motor tiembla en ralenti, bota humo negro por el escape y el escaner arroja codigo P0301",
        placa="DEV-ERR01",
        marca="Nissan",
        modelo="Sentra",
    )
    payload = {"taller_id": str(taller_id_val), "usuario_id": str(usuario_id_val)}

    gestor = GestorDiagnostico()
    gestor.api_key = "clave-simulada"

    with pytest.raises(HTTPException) as exc_info:
        await analizar_sintoma(
            request=dummy_request,
            consulta=consulta,
            token_payload=payload,
            gestor=gestor,
        )

    assert exc_info.value.status_code == 500
    assert "Error interno" in exc_info.value.detail

    # Limpieza
    await async_db_session.execute(delete(TrabajoGemini).where(TrabajoGemini.taller_id == taller_id_val))
    await async_db_session.execute(delete(HipotesisDiagnostico).where(HipotesisDiagnostico.diagnostico_id.in_(
        select(Diagnostico.id).where(Diagnostico.taller_id == taller_id_val)
    )))
    await async_db_session.execute(delete(Diagnostico).where(Diagnostico.taller_id == taller_id_val))
    await async_db_session.execute(delete(Vehiculo).where(Vehiculo.taller_id == taller_id_val))
    await async_db_session.execute(delete(Conversacion).where(Conversacion.taller_id == taller_id_val))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario_id_val))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller_id_val))
    await async_db_session.commit()


def test_e_sin_base_de_datos_nunca_devuelve_en_cola_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    """Condición E: si PostgreSQL no está disponible, nunca se devuelve en_cola_gemini ni UUID fantasma."""
    from src.core.gestor_diagnostico import GestorDiagnostico

    monkeypatch.setattr("src.core.diagnostico.response_generator.database_configurada", lambda: False)

    gestor = GestorDiagnostico()
    gestor.api_key = "clave-prueba"

    res = gestor.procesar_consulta_texto(
        "Falla de embrague patinando en tercera marcha sin tracción",
        placa="DEV-NODB1",
        marca_modelo="Toyota Yaris",
        proveedor="api",
        slot_gemini_preconcedido=False,
        diferir_encolado_persistente=True,
        taller_id=str(uuid.uuid4()),
        usuario_id=str(uuid.uuid4()),
    )

    assert res.modo_diagnostico == "diagnostico_degradado_ml_rag"
    assert res.solicitud_id is None


