"""Asocia de forma segura un taller existente con Meta Cloud API."""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parents[1]
if str(RAIZ_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAIZ_BACKEND))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import cerrar_conexion, obtener_engine


async def actualizar_taller(taller_id: uuid.UUID, meta_phone_number_id: str) -> None:
    engine = obtener_engine()
    try:
        async with AsyncSession(engine) as session:
            result = await session.execute(
                text(
                    "UPDATE talleres SET telefono_id_meta = :meta_id, activo = true "
                    "WHERE id = :taller_id RETURNING id, nombre"
                ),
                {"meta_id": meta_phone_number_id.strip(), "taller_id": taller_id},
            )
            taller = result.first()
            if taller is None:
                raise RuntimeError("No existe un taller con el identificador indicado.")
            await session.commit()
            print(f"Taller actualizado correctamente: {taller.nombre} ({taller.id})")
    finally:
        await cerrar_conexion()


def main() -> None:
    parser = argparse.ArgumentParser(description="Asocia un taller con el Phone Number ID de Meta.")
    parser.add_argument("--taller-id", type=uuid.UUID, required=True)
    parser.add_argument("--meta-phone-number-id", required=True)
    args = parser.parse_args()
    asyncio.run(actualizar_taller(args.taller_id, args.meta_phone_number_id))


if __name__ == "__main__":
    main()
