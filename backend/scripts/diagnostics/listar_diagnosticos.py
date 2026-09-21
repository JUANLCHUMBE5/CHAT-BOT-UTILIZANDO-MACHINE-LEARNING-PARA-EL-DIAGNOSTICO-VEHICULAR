"""Lista los diagnósticos persistidos para verificación operativa."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.diagnostics import Diagnostico, Vehiculo
from src.infrastructure.database.models.messaging import Conversacion


async def listar_diagnosticos():
    async with AsyncSession(obtener_engine()) as session:
        stmt = select(Diagnostico).options(
            selectinload(Diagnostico.mecanico),
            selectinload(Diagnostico.vehiculo).selectinload(Vehiculo.registrado_por),
            selectinload(Diagnostico.conversacion).selectinload(Conversacion.usuario),
        ).order_by(Diagnostico.creado_en.desc())
        res = await session.execute(stmt)
        diags = res.scalars().all()
        print(f"Total diags: {len(diags)}")
        for i, d in enumerate(diags):
            mecanico_nom = d.mecanico.nombres if d.mecanico else "Sin mecánico"
            conv_user = d.conversacion.usuario.nombres if d.conversacion and d.conversacion.usuario else "Sin conv user"
            placa = d.vehiculo.placa_ultimos4 if d.vehiculo else "Sin placa"
            print(
                f"[{i + 1}] {d.creado_en} | Cliente: {conv_user} | Mecánico: {mecanico_nom} "
                f"| Placa: ***{placa} | Falla: {d.falla_predicha} | Síntoma: {d.sintoma_original[:40]}..."
            )

if __name__ == "__main__":
    asyncio.run(listar_diagnosticos())
