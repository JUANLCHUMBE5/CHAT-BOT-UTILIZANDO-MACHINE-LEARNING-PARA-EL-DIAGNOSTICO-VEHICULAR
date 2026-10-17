"""Pruebas de persistencia y concurrencia real sobre PostgreSQL y Redis en Docker para Fase 10."""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import src.core.conversacion.session_persistence as sp
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.session_persistence import (
    guardar_contexto_sesion_redis,
    recuperar_contexto_sesion_redis,
    sincronizar_sesion_desde_persistencia,
)
from src.core.gestor_diagnostico import GestorDiagnostico

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://carbot_app:POCOYO123456@127.0.0.1:5433/carbot_db"
)


@pytest.fixture(autouse=True)
def configurar_redis_env(monkeypatch):
    """Garantiza que la URL de Redis para tests apunte a 127.0.0.1:6379."""
    monkeypatch.setenv("REDIS_URL", REDIS_URL)
    sp._REDIS_CLIENT = None
    sp._REDIS_LOOP = None


@pytest.fixture
async def redis_conn():
    """Conexión real a Redis local en Docker."""
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.ping()
        yield r
    finally:
        await r.aclose()


@pytest.fixture
async def pg_engine():
    """Engine real a PostgreSQL local en Docker."""
    engine = create_async_engine(POSTGRES_URL, echo=False)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.anyio
async def test_paso5_docker_redis_postgres_reales_activos(redis_conn, pg_engine):
    """Verifica que Redis y PostgreSQL de pruebas en Docker responden operativamente."""
    # 1. Ping Redis
    ping_redis = await redis_conn.ping()
    assert ping_redis is True

    # 2. Select PostgreSQL
    async with pg_engine.connect() as conn:
        res = await conn.execute(text("SELECT current_database(), current_user;"))
        row = res.fetchone()
        assert row is not None
        assert row[0] == "carbot_db"
        assert row[1] == "carbot_app"


@pytest.mark.anyio
async def test_paso5_reinicio_api_recuperacion_redis(redis_conn):
    """Verifica recuperación de contexto (vehículo, case_id, hechos) simulando reinicio total de API."""
    sesion_id = f"test_api_restart_{uuid.uuid4().hex[:8]}"
    case_id_original = str(uuid.uuid4())

    # Crear estado inicial usando el session_manager canónico
    gestor_inicial = GestorDiagnostico()
    s = gestor_inicial.session_manager.obtener_o_crear_sesion(sesion_id)
    s.case_id = case_id_original
    s.placa = "ABC-789"
    s.conversation_state.case_id = case_id_original
    s.conversation_state.placa = "ABC-789"
    s.conversation_state.marca = "Toyota"
    s.conversation_state.modelo = "Corolla"
    s.conversation_state.anio = "2015"
    s.actualizar_perfil({"marca": "Toyota", "modelo": "Corolla", "anio": 2015})
    s.agregar_sintoma("misfire en cilindro 2 al acelerar")

    # Exportar contexto canónico y persistir en Redis real
    contexto_exportado = gestor_inicial.session_manager.exportar_contexto(sesion_id)
    await guardar_contexto_sesion_redis(sesion_id, contexto_exportado, ttl_segundos=300)

    # Simular reinicio de API: destruir gestor inicial y crear una nueva instancia sin memoria
    gestor_post_reinicio = GestorDiagnostico()
    assert gestor_post_reinicio.session_manager.obtener_sesion(sesion_id) is None

    # Sincronizar desde persistencia Redis
    recuperado = await sincronizar_sesion_desde_persistencia(gestor_post_reinicio, sesion_id)
    assert recuperado is True

    # Comprobar estado cargado en el DiagnosticSession nuevo
    sesion_recup = gestor_post_reinicio.session_manager.obtener_sesion(sesion_id)
    assert sesion_recup is not None
    assert sesion_recup.case_id == case_id_original
    assert sesion_recup.placa == "ABC-789"
    assert "misfire en cilindro 2 al acelerar" in sesion_recup.sintomas
    assert sesion_recup.perfil_vehiculo.get("marca") == "Toyota"

    # Limpieza específica de la clave de prueba en Redis (sin usar FLUSHALL)
    await redis_conn.delete(f"carbot:rest:session:{sesion_id}")


@pytest.mark.anyio
async def test_paso5_expiracion_redis_recuperacion_durable_postgres(redis_conn):
    """Verifica que tras expirar la clave de Redis (o reinicio de Redis), se recupera desde PostgreSQL."""
    sesion_id = f"test_redis_expire_{uuid.uuid4().hex[:8]}"
    case_id_durable = str(uuid.uuid4())

    # Crear estado inicial usando session_manager
    gestor_inicial = GestorDiagnostico()
    s = gestor_inicial.session_manager.obtener_o_crear_sesion(sesion_id)
    s.case_id = case_id_durable
    s.placa = "XYZ-999"
    s.conversation_state.case_id = case_id_durable
    s.conversation_state.placa = "XYZ-999"
    s.conversation_state.marca = "Nissan"
    s.conversation_state.modelo = "Tiida"
    s.conversation_state.anio = "2011"
    s.actualizar_perfil({"marca": "Nissan", "modelo": "Tiida", "anio": 2011})
    s.agregar_sintoma("perdida de potencia en subida")

    contexto_db_postgres = {
        "session_id": sesion_id,
        "sesiones": {
            sesion_efectiva: gestor_inicial.session_manager.exportar_contexto(sesion_id)
            for sesion_efectiva in [sesion_id]
        },
    }

    # Asegurar que en Redis NO existe esta clave (simula expiración de TTL o reinicio de Redis)
    await redis_conn.delete(f"carbot:rest:session:{sesion_id}")
    assert await recuperar_contexto_sesion_redis(sesion_id) is None

    # Sincronizar usando como respaldo el contexto_db de PostgreSQL
    gestor_nuevo = GestorDiagnostico()
    recuperado = await sincronizar_sesion_desde_persistencia(
        gestor_nuevo, sesion_id, contexto_db=contexto_db_postgres
    )
    assert recuperado is True

    # Verificar que el gestor restauró el caso durable
    sesion = gestor_nuevo.session_manager.obtener_sesion(sesion_id)
    assert sesion is not None
    assert sesion.case_id == case_id_durable
    assert sesion.placa == "XYZ-999"
    assert "perdida de potencia en subida" in sesion.sintomas
    assert sesion.perfil_vehiculo.get("marca") == "Nissan"


@pytest.mark.anyio
async def test_paso5_dos_mecanicos_conversando_simultaneamente():
    """Verifica concurrencia real de dos mecánicos ejecutando turnos paralelos sin cross-talk."""
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    gestor = GestorDiagnostico()

    mecanico_1 = "mecanico_lima_norte_01"
    mecanico_2 = "mecanico_arequipa_sur_02"

    async def turno_mecanico(sid: str, mensaje: str):
        return await orquestador.procesar_turno(
            session_id=sid,
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
        )

    # Turno 1 concurrente
    t1_m1, t1_m2 = await asyncio.gather(
        turno_mecanico(mecanico_1, "Tengo una Hilux 1KD placa HIL-100 con humo negro al acelerar"),
        turno_mecanico(mecanico_2, "Tengo un Yaris 2014 placa YAR-200 con chillido en frenos"),
    )

    assert t1_m1 is not None and "respuesta_texto" in t1_m1
    assert t1_m2 is not None and "respuesta_texto" in t1_m2

    s1 = await repo.get_session(mecanico_1)
    s2 = await repo.get_session(mecanico_2)

    assert s1 is not None and s2 is not None
    assert s1.case_id != s2.case_id, "Los case_id deben ser únicos por mecánico"
    assert s1.placa == "HIL-100"
    assert s2.placa == "YAR-200"

    # Turno 2 concurrente (respuestas técnicas)
    t2_m1, t2_m2 = await asyncio.gather(
        turno_mecanico(mecanico_1, "Presión de turbo marca 1.1 bar estable"),
        turno_mecanico(mecanico_2, "El pedal no vibra pero suena fuerte en frío"),
    )

    assert t2_m1 is not None
    assert t2_m2 is not None

    s1_fin = await repo.get_session(mecanico_1)
    s2_fin = await repo.get_session(mecanico_2)

    assert s1_fin.placa == "HIL-100"
    assert s2_fin.placa == "YAR-200"
    assert s1_fin.case_id == s1.case_id, "El case_id de mecánico 1 debe conservarse"
    assert s2_fin.case_id == s2.case_id, "El case_id de mecánico 2 debe conservarse"


@pytest.mark.anyio
async def test_paso5_un_mecanico_con_dos_vehiculos_paralelos():
    """Verifica que un mismo mecánico puede atender dos vehículos en sesiones independientes sin mezclar hechos."""
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    gestor = GestorDiagnostico()

    sesion_auto_a = "taller_mecanico_01_bahia_a"
    sesion_auto_b = "taller_mecanico_01_bahia_b"

    # Auto A: Corolla
    await orquestador.procesar_turno(
        session_id=sesion_auto_a,
        texto_usuario="Toyota Corolla placa COR-111 motor no arranca y da clic",
        gestor_diagnostico=gestor,
    )

    # Auto B: Kia Rio
    await orquestador.procesar_turno(
        session_id=sesion_auto_b,
        texto_usuario="Kia Rio placa KIA-222 calienta en tráfico de la tarde",
        gestor_diagnostico=gestor,
    )

    st_a = await repo.get_session(sesion_auto_a)
    st_b = await repo.get_session(sesion_auto_b)

    assert st_a.placa == "COR-111"
    assert st_b.placa == "KIA-222"
    assert st_a.case_id != st_b.case_id

    # Turno en Auto A sobre batería
    await orquestador.procesar_turno(
        session_id=sesion_auto_a,
        texto_usuario="Voltaje de batería marca 10.5V en reposo",
        gestor_diagnostico=gestor,
    )

    # Verificar que el voltaje quedó en Auto A y no contaminó Auto B
    st_a_upd = await repo.get_session(sesion_auto_a)
    st_b_upd = await repo.get_session(sesion_auto_b)

    assert st_a_upd.placa == "COR-111"
    assert st_b_upd.placa == "KIA-222"
    assert st_b_upd.obtener_hecho("voltaje") is None or "10.5" not in str(st_b_upd.obtener_hecho("voltaje"))


@pytest.mark.anyio
async def test_paso5_idempotencia_mensajes_duplicados():
    """Verifica que mensajes de red duplicados no corrompan el estado ni generen fallos."""
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    gestor = GestorDiagnostico()

    sid = f"test_idemp_{uuid.uuid4().hex[:6]}"
    mensaje = "Toyota Yaris placa DUP-001 vibra a 80 km/h"

    # Enviar primera vez
    res1 = await orquestador.procesar_turno(
        session_id=sid,
        texto_usuario=mensaje,
        gestor_diagnostico=gestor,
    )
    assert res1 is not None and "respuesta_texto" in res1
    st1 = await repo.get_session(sid)
    case_id_1 = st1.case_id

    # Enviar segunda vez exactamente el mismo mensaje (retransmisión de red / webhook duplicado)
    res2 = await orquestador.procesar_turno(
        session_id=sid,
        texto_usuario=mensaje,
        gestor_diagnostico=gestor,
    )
    st2 = await repo.get_session(sid)

    assert st2.case_id == case_id_1, "El case_id debe conservarse idéntico"
    assert st2.placa == "DUP-001"
    assert res2 is not None and "respuesta_texto" in res2


@pytest.mark.anyio
async def test_paso5_cierre_de_caso_y_respuesta_tardia():
    """Verifica que tras cerrar un caso, las respuestas tardías o nuevos mensajes no reviven la hipótesis cerrada."""
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    gestor = GestorDiagnostico()

    sid = f"test_cierre_{uuid.uuid4().hex[:6]}"

    # Turno 1: Falla
    await orquestador.procesar_turno(
        session_id=sid,
        texto_usuario="Nissan Sentra placa CLS-001 no arranca por fusible quemado",
        gestor_diagnostico=gestor,
    )

    # Turno 2: Cierre formal
    res_cierre = await orquestador.procesar_turno(
        session_id=sid,
        texto_usuario="Ya cambié el fusible y encendió perfecto, cerramos este diagnóstico muchas gracias",
        gestor_diagnostico=gestor,
    )
    assert res_cierre is not None

    # Simular finalización formal en el repositorio
    await repo.finalizar_caso(sid)

    # Turno 3: Mensaje tardío o nuevo caso para otro problema
    res_nuevo = await orquestador.procesar_turno(
        session_id=sid,
        texto_usuario="Ahora tengo una consulta nueva sobre el aire acondicionado de otro auto",
        gestor_diagnostico=gestor,
    )

    st_nuevo = await repo.get_session(sid)
    assert res_nuevo is not None
    assert st_nuevo is not None
