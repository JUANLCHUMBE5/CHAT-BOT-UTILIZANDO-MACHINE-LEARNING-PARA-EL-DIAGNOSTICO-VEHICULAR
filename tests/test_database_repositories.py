"""Pruebas de integración para la capa de repositorios SQLAlchemy con PostgreSQL."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_identificador_persistencia
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico, HipotesisDiagnostico, Vehiculo
from src.infrastructure.database.models.messaging import Conversacion, Mensaje
from src.infrastructure.database.models.operations import Auditoria, UsoApi
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@pytest.fixture
async def async_db_session():
    """Entrega una sesión asíncrona conectada a PostgreSQL y limpia los datos creados."""
    if not database_configurada():
        pytest.skip("PostgreSQL no está configurado para pruebas.")

    engine = obtener_engine()
    talleres_creados = []

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    # Limpieza al finalizar el test
    if talleres_creados:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            for t_id in talleres_creados:
                subq = select(Diagnostico.id).where(Diagnostico.taller_id == t_id)
                await session.execute(delete(HipotesisDiagnostico).where(HipotesisDiagnostico.diagnostico_id.in_(subq)))
                await session.execute(delete(UsoApi).where(UsoApi.taller_id == t_id))
                await session.execute(delete(Auditoria).where(Auditoria.taller_id == t_id))
                await session.execute(delete(Diagnostico).where(Diagnostico.taller_id == t_id))
                await session.execute(delete(Mensaje).where(Mensaje.taller_id == t_id))
                await session.execute(delete(Conversacion).where(Conversacion.taller_id == t_id))
                await session.execute(delete(Vehiculo).where(Vehiculo.taller_id == t_id))
                await session.execute(delete(Usuario).where(Usuario.taller_id == t_id))
                await session.execute(delete(Taller).where(Taller.id == t_id))
            await session.commit()


@pytest.mark.anyio
async def test_taller_repository_crud(async_db_session: AsyncSession):
    repo = TallerRepository(async_db_session)
    ruc_test = f"20{uuid.uuid4().int % 1000000000:09d}"

    # 1. Crear taller
    taller = await repo.crear_taller(
        nombre="Taller Mecánico Carabayllo Norte Test",
        ruc=ruc_test,
        telefono="015432100",
        direccion="Av. Universitaria 5500",
    )
    await async_db_session.commit()
    assert taller.id is not None
    assert taller.nombre == "Taller Mecánico Carabayllo Norte Test"
    assert taller.ruc == ruc_test

    # 2. Buscar por RUC
    encontrado = await repo.obtener_por_ruc(ruc_test)
    assert encontrado is not None
    assert encontrado.id == taller.id

    # 3. Obtener primer taller activo
    primer = await repo.obtener_primer_taller_activo()
    assert primer is not None

    # 4. Listar talleres
    todos = await repo.listar_talleres()
    assert len(todos) >= 1

    # Limpiar taller
    await async_db_session.execute(delete(Taller).where(Taller.id == taller.id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_usuario_repository_hash_auth(async_db_session: AsyncSession):
    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)

    # 1. Crear taller y asegurar roles
    taller = await taller_repo.crear_taller(nombre="Taller Diesel Carabayllo Test")
    roles = await usuario_repo.asegurar_roles_estandar()
    assert "admin" in roles
    assert "mecanico" in roles

    # 2. Registrar mecánico con teléfono hasheado
    telefono_real = f"+51 9{uuid.uuid4().int % 100000000:08d}"
    whatsapp_hash = hash_identificador_persistencia(telefono_real, "telefono")
    ultimos4 = telefono_real[-4:]

    mecanico = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Carlos Test",
        apellidos="Mendoza",
        whatsapp_hash=whatsapp_hash,
        whatsapp_ultimos4=ultimos4,
        activo=True,
    )
    await async_db_session.commit()

    assert mecanico.id is not None
    assert mecanico.whatsapp_hash == whatsapp_hash
    assert mecanico.whatsapp_ultimos4 == ultimos4

    # 3. Buscar mecánico por hash
    buscado = await usuario_repo.buscar_por_whatsapp_hash(whatsapp_hash)
    assert buscado is not None
    assert buscado.id == mecanico.id
    assert buscado.taller.nombre == "Taller Diesel Carabayllo Test"
    assert buscado.rol.codigo == "mecanico"

    # 4. Buscar mecánico por número en cualquier formato
    buscado_por_tel = await usuario_repo.buscar_por_telefono(telefono_real)
    assert buscado_por_tel is not None
    assert buscado_por_tel.id == mecanico.id

    # Limpiar
    await async_db_session.execute(delete(Usuario).where(Usuario.id == mecanico.id))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller.id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_conversacion_repository_service_window(async_db_session: AsyncSession):
    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)
    conv_repo = ConversacionRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre="Taller Frenos Express Test")
    roles = await usuario_repo.asegurar_roles_estandar()
    user_hash = hash_identificador_persistencia(f"51999{uuid.uuid4().int % 100000:06d}", "telefono")
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Roberto Test",
        whatsapp_hash=user_hash,
        whatsapp_ultimos4="1222",
    )
    await async_db_session.commit()

    # 1. Crear conversación
    conv = await conv_repo.obtener_o_crear_activa(taller_id=taller.id, usuario_id=usuario.id)
    await async_db_session.commit()
    assert conv.id is not None
    assert conv.estado == "abierta"

    # 2. Reutilizar conversación activa dentro de la ventana de 24h
    conv_reutilizada = await conv_repo.obtener_o_crear_activa(taller_id=taller.id, usuario_id=usuario.id)
    assert conv_reutilizada.id == conv.id

    # 3. Cerrar conversación
    cerrada = await conv_repo.cerrar_conversacion(conv.id)
    await async_db_session.commit()
    assert cerrada is not None
    assert cerrada.estado == "cerrada"

    # Limpiar
    await async_db_session.execute(delete(Conversacion).where(Conversacion.id == conv.id))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario.id))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller.id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_mensaje_repository_idempotencia_meta(async_db_session: AsyncSession):
    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)
    conv_repo = ConversacionRepository(async_db_session)
    msg_repo = MensajeRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre="Taller Mecánica Integral Test")
    roles = await usuario_repo.asegurar_roles_estandar()
    u_hash = hash_identificador_persistencia(f"51955{uuid.uuid4().int % 100000:06d}", "telefono")
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Lucía Test",
        whatsapp_hash=u_hash,
        whatsapp_ultimos4="3322",
    )
    conv = await conv_repo.obtener_o_crear_activa(taller_id=taller.id, usuario_id=usuario.id)
    await async_db_session.commit()

    meta_id = f"wamid.HBgL{uuid.uuid4().hex[:12]}=="

    # 1. Comprobar que no existe
    assert await msg_repo.existe_meta_message_id(meta_id) is False

    # 2. Insertar mensaje
    msg = await msg_repo.crear_mensaje(
        conversacion_id=conv.id,
        taller_id=taller.id,
        usuario_id=usuario.id,
        meta_message_id=meta_id,
        direccion="entrada",
        tipo="texto",
        texto="El auto tiembla al frenar",
    )
    await async_db_session.commit()
    assert msg.id is not None
    assert msg.meta_message_id == meta_id

    # 3. Comprobar que ahora existe (idempotencia verificable)
    assert await msg_repo.existe_meta_message_id(meta_id) is True

    # 4. Listar mensajes
    mensajes = await msg_repo.listar_por_conversacion(conv.id)
    assert len(mensajes) == 1
    assert mensajes[0].texto == "El auto tiembla al frenar"

    # Limpiar
    await async_db_session.execute(delete(Mensaje).where(Mensaje.id == msg.id))
    await async_db_session.execute(delete(Conversacion).where(Conversacion.id == conv.id))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario.id))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller.id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_diagnostico_e_hipotesis_repository(async_db_session: AsyncSession):
    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)
    conv_repo = ConversacionRepository(async_db_session)
    diag_repo = DiagnosticoRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre="Taller Diagnóstico Pro Test")
    roles = await usuario_repo.asegurar_roles_estandar()
    u_hash = hash_identificador_persistencia(f"51988{uuid.uuid4().int % 100000:06d}", "telefono")
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["mecanico"].id,
        nombres="Víctor Test",
        whatsapp_hash=u_hash,
        whatsapp_ultimos4="6655",
    )
    conv = await conv_repo.obtener_o_crear_activa(taller_id=taller.id, usuario_id=usuario.id)
    await async_db_session.commit()

    # 1. Crear diagnóstico con modo tripartito
    diag = await diag_repo.crear_diagnostico(
        taller_id=taller.id,
        mecanico_id=usuario.id,
        conversacion_id=conv.id,
        sintoma_original="Siento un chillido agudo al frenar",
        sintoma_normalizado="chillido agudo frenar",
        falla_predicha="Frenos / Desgaste de Pastillas",
        confianza=0.925,
        fuente="gemini",
        modo_diagnostico="completo_ml_rag_llm",
        estado="generado",
        duracion_ms=145,
        conclusion_mecanico="[COMPLETO_ML_RAG_LLM] Síntesis Gemini 3.5 Flash-Lite",
    )
    assert diag.id is not None
    assert diag.falla_predicha == "Frenos / Desgaste de Pastillas"
    assert diag.confianza == Decimal("0.9250")
    assert diag.modo_diagnostico == "completo_ml_rag_llm"
    assert diag.duracion_ms == 145

    # 2. Agregar hipótesis
    hipotesis = await diag_repo.agregar_hipotesis(
        diagnostico_id=diag.id,
        orden=1,
        falla_probable="Pastillas de freno desgastadas o cristalizadas",
        confianza=0.925,
        evidencia="Manual técnico de frenos sección 4.2",
        prueba_recomendada="Medir espesor de pastillas con calibrador",
        resultado="pendiente",
    )
    await async_db_session.commit()
    assert hipotesis.id is not None
    assert hipotesis.orden == 1

    # 3. Obtener diagnóstico con hipótesis
    diag_completo = await diag_repo.obtener_por_id(diag.id)
    assert diag_completo is not None
    assert len(diag_completo.hipotesis) == 1
    assert diag_completo.hipotesis[0].falla_probable == "Pastillas de freno desgastadas o cristalizadas"

    # Limpiar
    await async_db_session.execute(delete(HipotesisDiagnostico).where(HipotesisDiagnostico.id == hipotesis.id))
    await async_db_session.execute(delete(Diagnostico).where(Diagnostico.id == diag.id))
    await async_db_session.execute(delete(Conversacion).where(Conversacion.id == conv.id))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario.id))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller.id))
    await async_db_session.commit()


@pytest.mark.anyio
async def test_operaciones_repository_costo_y_auditoria(async_db_session: AsyncSession):
    taller_repo = TallerRepository(async_db_session)
    usuario_repo = UsuarioRepository(async_db_session)
    operaciones_repo = OperacionesRepository(async_db_session)

    taller = await taller_repo.crear_taller(nombre="Taller Mecánica y Costos Test")
    roles = await usuario_repo.asegurar_roles_estandar()
    u_hash = hash_identificador_persistencia(f"51912{uuid.uuid4().int % 100000:06d}", "telefono")
    usuario = await usuario_repo.crear_usuario(
        taller_id=taller.id,
        rol_id=roles["admin"].id,
        nombres="Elena Test",
        whatsapp_hash=u_hash,
        whatsapp_ultimos4="5678",
    )
    await async_db_session.commit()

    # 1. Registrar uso de API Gemini
    uso1 = await operaciones_repo.registrar_uso_api(
        taller_id=taller.id,
        proveedor="google",
        operacion="gemini_generacion_diagnostico",
        modelo="gemini-1.5-flash",
        tokens_entrada=120,
        tokens_salida=250,
        unidades=Decimal("370"),
        costo_estimado=Decimal("0.000084"),
        moneda="USD",
    )
    await async_db_session.commit()
    assert uso1.id is not None
    assert uso1.tokens_entrada == 120
    assert uso1.tokens_salida == 250

    # 2. Registrar evento de auditoría
    auditoria = await operaciones_repo.registrar_auditoria(
        accion="registro_mecanico",
        entidad="usuario",
        taller_id=taller.id,
        usuario_id=usuario.id,
        detalles={"nombres": "Elena Test", "rol": "admin"},
    )
    await async_db_session.commit()
    assert auditoria.id is not None
    assert auditoria.accion == "registro_mecanico"

    # 3. Costo acumulado
    total = await operaciones_repo.obtener_costo_total_taller(taller.id)
    assert total >= Decimal("0.000084")

    # Limpiar
    await async_db_session.execute(delete(UsoApi).where(UsoApi.id == uso1.id))
    await async_db_session.execute(delete(Auditoria).where(Auditoria.id == auditoria.id))
    await async_db_session.execute(delete(Usuario).where(Usuario.id == usuario.id))
    await async_db_session.execute(delete(Taller).where(Taller.id == taller.id))
    await async_db_session.commit()
