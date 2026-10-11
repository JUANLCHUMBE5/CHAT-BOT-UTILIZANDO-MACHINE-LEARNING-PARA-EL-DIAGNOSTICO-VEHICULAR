"""Pruebas de consistencia de vehículos: actualización de marca/modelo y aislamiento."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_identificador_persistencia
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository
from src.infrastructure.database.repositories.vehiculo_repository import VehiculoRepository


@pytest.fixture
async def setup_test_talleres():
    if not database_configurada():
        pytest.skip("PostgreSQL no está configurado para pruebas.")

    engine = obtener_engine()
    taller1_id = uuid.uuid4()
    taller2_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        taller_repo = TallerRepository(session)
        user_repo = UsuarioRepository(session)

        t1 = await taller_repo.crear_taller(
            nombre=f"Taller Uno Test {taller1_id.hex[:6]}",
            ruc=f"20{uuid.uuid4().int % 1000000000:09d}",
            taller_id=taller1_id,
            telefono_id_meta=f"META_{taller1_id.hex[:8]}",
        )
        t2 = await taller_repo.crear_taller(
            nombre=f"Taller Dos Test {taller2_id.hex[:6]}",
            ruc=f"20{uuid.uuid4().int % 1000000000:09d}",
            taller_id=taller2_id,
            telefono_id_meta=f"META_{taller2_id.hex[:8]}",
        )
        roles = await user_repo.asegurar_roles_estandar()

        tel1 = f"+51 981 {uuid.uuid4().int % 1000000:06d}"
        tel2 = f"+51 982 {uuid.uuid4().int % 1000000:06d}"
        await user_repo.crear_usuario(
            taller_id=t1.id,
            rol_id=roles["mecanico"].id,
            nombres="Mecanico T1",
            whatsapp_hash=hash_identificador_persistencia(tel1, "telefono"),
            whatsapp_ultimos4=tel1[-4:],
            usuario_id=user1_id,
        )
        await user_repo.crear_usuario(
            taller_id=t2.id,
            rol_id=roles["mecanico"].id,
            nombres="Mecanico T2",
            whatsapp_hash=hash_identificador_persistencia(tel2, "telefono"),
            whatsapp_ultimos4=tel2[-4:],
            usuario_id=user2_id,
        )
        await session.commit()

    yield {
        "engine": engine,
        "taller1_id": taller1_id,
        "taller2_id": taller2_id,
        "user1_id": user1_id,
        "user2_id": user2_id,
    }


@pytest.mark.anyio
async def test_vehiculo_repository_actualiza_toyota_a_nissan(setup_test_talleres):
    data = setup_test_talleres
    placa = "ABC1234"

    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        repo = VehiculoRepository(session)

        # 1. Registro inicial como Toyota Yaris
        v1 = await repo.obtener_o_crear(
            taller_id=data["taller1_id"],
            registrado_por_id=data["user1_id"],
            placa_str=placa,
            marca="Toyota",
            modelo="Yaris",
            anio=2018,
        )
        await session.commit()
        assert v1.marca == "Toyota"
        assert v1.modelo == "Yaris"
        vehiculo_id_original = v1.id

    # 2. Corrección posterior a Nissan Tiida con la misma placa
    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        repo = VehiculoRepository(session)
        v2 = await repo.obtener_o_crear(
            taller_id=data["taller1_id"],
            registrado_por_id=data["user1_id"],
            placa_str=placa,
            marca="Nissan",
            modelo="Tiida",
            anio=2015,
        )
        await session.commit()

        # Debe conservar el mismo ID de vehículo y haber actualizado marca/modelo/año
        assert v2.id == vehiculo_id_original
        assert v2.marca == "Nissan"
        assert v2.modelo == "Tiida"
        assert v2.anio == 2015


@pytest.mark.anyio
async def test_vehiculo_repository_no_sobrescribe_con_valores_genericos(setup_test_talleres):
    data = setup_test_talleres
    placa = "XYZ9876"

    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        repo = VehiculoRepository(session)

        # Registro con datos confirmados
        v = await repo.obtener_o_crear(
            taller_id=data["taller1_id"],
            registrado_por_id=data["user1_id"],
            placa_str=placa,
            marca="Honda",
            modelo="Civic",
            anio=2020,
        )
        await session.commit()
        assert v.marca == "Honda"

    # Intento de sobrescritura con "Vehiculo Generico"
    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        repo = VehiculoRepository(session)
        v_mod = await repo.obtener_o_crear(
            taller_id=data["taller1_id"],
            registrado_por_id=data["user1_id"],
            placa_str=placa,
            marca="Vehiculo Generico",
            modelo="Generico",
        )
        await session.commit()

        # Los datos reales deben ser preservados intactos
        assert v_mod.marca == "Honda"
        assert v_mod.modelo == "Civic"
        assert v_mod.anio == 2020


@pytest.mark.anyio
async def test_vehiculo_aislamiento_estricto_entre_talleres(setup_test_talleres):
    data = setup_test_talleres
    placa = "PLK5544"

    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        repo = VehiculoRepository(session)

        # Taller 1 registra su vehículo
        v_t1 = await repo.obtener_o_crear(
            taller_id=data["taller1_id"],
            registrado_por_id=data["user1_id"],
            placa_str=placa,
            marca="Kia",
            modelo="Rio",
        )
        await session.commit()
        assert v_t1.taller_id == data["taller1_id"]

    # Taller 2 con la misma placa registra su propio registro aislado
    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        repo = VehiculoRepository(session)
        v_t2 = await repo.obtener_o_crear(
            taller_id=data["taller2_id"],
            registrado_por_id=data["user2_id"],
            placa_str=placa,
            marca="Kia",
            modelo="Cerato",
        )
        await session.commit()
        assert v_t2.taller_id == data["taller2_id"]
        assert v_t2.id != v_t1.id

    # Comprobación de que el registro de Taller 1 no fue alterado por Taller 2
    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        repo = VehiculoRepository(session)
        v_t1_check = await repo.buscar_por_placa(data["taller1_id"], placa)
        assert v_t1_check.modelo == "Rio"
        assert v_t1_check.taller_id == data["taller1_id"]
