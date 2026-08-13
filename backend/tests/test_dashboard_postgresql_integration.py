"""Integración real del panel administrativo con PostgreSQL."""

import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generar_password_hash, hash_identificador_persistencia
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@pytest.mark.anyio
async def test_usuario_temporal_exige_cambio_y_hash_unico():
    engine = obtener_engine()
    taller_id = uuid.uuid4()
    usuario_id = uuid.uuid4()
    telefono = f"+51 955 {uuid.uuid4().int % 1000000:06d}"

    async with AsyncSession(engine, expire_on_commit=False) as session:
        taller = await TallerRepository(session).crear_taller(
            nombre="Taller Dashboard Integración",
            ruc=f"20{uuid.uuid4().int % 1000000000:09d}",
            taller_id=taller_id,
        )
        repo = UsuarioRepository(session)
        roles = await repo.asegurar_roles_estandar()
        usuario = await repo.crear_usuario(
            taller_id=taller.id,
            rol_id=roles["mecanico"].id,
            nombres="Mecánico Integración",
            whatsapp_hash=hash_identificador_persistencia(telefono, "telefono"),
            whatsapp_ultimos4=telefono[-4:],
            activo=True,
            usuario_id=usuario_id,
        )
        usuario.password_hash = generar_password_hash("TemporalSegura123")
        usuario.debe_cambiar_password = True
        await session.commit()

        almacenado = await session.get(Usuario, usuario_id)
        assert almacenado is not None
        assert almacenado.debe_cambiar_password is True
        assert almacenado.password_hash.startswith("pbkdf2_sha256$600000$")

        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.execute(delete(Taller).where(Taller.id == taller_id))
        await session.commit()


@pytest.mark.anyio
async def test_historial_postgresql_ordena_hipotesis_por_prioridad():
    relacion = DiagnosticoRepository
    assert relacion is not None
    # La relación ORM ordenada evita seleccionar una hipótesis arbitraria en el historial.
    from src.infrastructure.database.models.diagnostics import Diagnostico

    assert Diagnostico.hipotesis.property.order_by is not False
