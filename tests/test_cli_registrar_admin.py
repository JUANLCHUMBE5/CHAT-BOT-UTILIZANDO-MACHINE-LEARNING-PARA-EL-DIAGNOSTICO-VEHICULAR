"""Pruebas para el script CLI de registro seguro de taller y administrador con PostgreSQL."""

import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.registrar_taller_admin import registrar_taller_y_administrador
from src.core.security import hash_identificador_persistencia
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@pytest.fixture
async def setup_cli_db():
    """Configura el entorno de pruebas para el script CLI y limpia los registros al finalizar."""
    if not database_configurada():
        pytest.skip("PostgreSQL no está configurado para pruebas.")

    engine = obtener_engine()
    created_taller_ids = []
    created_hashes = []

    yield {
        "engine": engine,
        "created_taller_ids": created_taller_ids,
        "created_hashes": created_hashes,
    }

    async with AsyncSession(engine, expire_on_commit=False) as session:
        if created_hashes:
            await session.execute(delete(Usuario).where(Usuario.whatsapp_hash.in_(created_hashes)))
        if created_taller_ids:
            await session.execute(delete(Taller).where(Taller.id.in_(created_taller_ids)))
        await session.commit()


@pytest.mark.anyio
async def test_registrar_taller_y_admin_seguro(setup_cli_db):
    data = setup_cli_db
    random_num = uuid.uuid4().int % 1000000
    tel_confidencial = f"+51 987 {random_num:06d}"
    digits_only = "".join(c for c in tel_confidencial if c.isdigit())
    expected_ultimos4 = digits_only[-4:]
    ruc_test = f"20{uuid.uuid4().int % 1000000000:09d}"

    # 1. Ejecutar registro seguro
    res = await registrar_taller_y_administrador(
        nombre_taller="Taller Mecánico Carabayllo Motors Test",
        ruc=ruc_test,
        direccion="Av. Tupac Amaru 1234",
        telefono_taller="015432100",
        nombres="Juan Admin",
        apellidos="López",
        telefono_whatsapp=tel_confidencial,
        codigo_rol="admin",
    )

    data["created_taller_ids"].append(uuid.UUID(res["taller_id"]))
    data["created_hashes"].append(res["whatsapp_hash"])

    assert res["estado"] == "creado"
    assert res["taller_nombre"] == "Taller Mecánico Carabayllo Motors Test"
    assert res["whatsapp_ultimos4"] == expected_ultimos4
    assert len(res["whatsapp_hash"]) == 64
    assert res["whatsapp_hash"] == hash_identificador_persistencia(tel_confidencial, "telefono")

    # 2. Verificar que en la base de datos solo se guardó el hash y los últimos 4 dígitos
    engine = data["engine"]
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        usuario = await user_repo.buscar_por_whatsapp_hash(res["whatsapp_hash"])
        assert usuario is not None
        assert usuario.whatsapp_hash == res["whatsapp_hash"]
        assert usuario.whatsapp_ultimos4 == expected_ultimos4

        # Garantizar que el número en texto claro NO está en la entidad
        assert not hasattr(usuario, "telefono")
        assert not hasattr(usuario, "numero_whatsapp")

    # 3. Idempotencia: Intentar registrarlo nuevamente debe indicar 'existente'
    res_repetido = await registrar_taller_y_administrador(
        nombre_taller="Taller Mecánico Carabayllo Motors Test",
        ruc=ruc_test,
        direccion="Av. Tupac Amaru 1234",
        telefono_taller="015432100",
        nombres="Juan Admin",
        apellidos="López",
        telefono_whatsapp=tel_confidencial,
        codigo_rol="admin",
    )
    assert res_repetido["estado"] == "existente"
    assert res_repetido["usuario_id"] == res["usuario_id"]


@pytest.mark.anyio
async def test_registrar_taller_telefono_invalido(setup_cli_db):
    with pytest.raises(ValueError, match="al menos 6 dígitos"):
        await registrar_taller_y_administrador(
            nombre_taller="Taller Test",
            ruc=None,
            direccion=None,
            telefono_taller=None,
            nombres="Test",
            apellidos=None,
            telefono_whatsapp="123",  # Menor a 6 dígitos
            codigo_rol="admin",
        )
