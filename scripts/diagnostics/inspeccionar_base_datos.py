"""Inspecciona relaciones de diagnósticos y usuarios en PostgreSQL."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.catalogs import Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico, Vehiculo
from src.infrastructure.database.models.messaging import Conversacion


async def inspeccionar_diagnosticos():
    async with AsyncSession(obtener_engine()) as session:
        stmt = select(Diagnostico).options(
            selectinload(Diagnostico.mecanico),
            selectinload(Diagnostico.vehiculo).selectinload(Vehiculo.registrado_por),
            selectinload(Diagnostico.conversacion).selectinload(Conversacion.usuario),
        ).limit(10)
        res = await session.execute(stmt)
        diags = res.scalars().all()
        print(f"Total diagnostics found (first 10): {len(diags)}")
        for d in diags:
            mecanico_nom = d.mecanico.nombres if d.mecanico else "None"
            conv_user = d.conversacion.usuario.nombres if d.conversacion and d.conversacion.usuario else "None"
            veh_user = d.vehiculo.registrado_por.nombres if d.vehiculo and d.vehiculo.registrado_por else "None"
            print(f"ID: {d.id} | Falla: {d.falla_predicha} | Mecánico: {mecanico_nom} | Conv User: {conv_user} | Veh User: {veh_user} | Conv_id: {d.conversacion_id} | Veh_id: {d.vehiculo_id}")

        # Also let's check all users in DB
        res_users = await session.execute(select(Usuario).options(selectinload(Usuario.rol)))
        users = res_users.scalars().all()
        print("\nAll Users in DB:")
        for u in users:
            print(f"- {u.nombres} (ID: {u.id}, Rol: {u.rol.codigo if u.rol else 'N/A'}, Phone: ***{u.whatsapp_ultimos4})")

if __name__ == "__main__":
    asyncio.run(inspeccionar_diagnosticos())
