"""Script seguro para eliminar exclusivamente el lote piloto temporal PILOTO_TEMPORAL_20260919.

Por defecto ejecuta DRY RUN.
Requiere --confirm para aplicar la eliminación física.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from sqlalchemy import delete, func, select

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.validation import ValidacionTaller

LOTE_TAG = "PILOTO_TEMPORAL_20260919"


async def ejecutar_eliminacion(confirm: bool = False):
    engine = obtener_engine()

    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # 1. Total antes
        total_antes = (
            await session.execute(select(func.count()).select_from(ValidacionTaller))
        ).scalar_one()

        # 2. Localizar registros del lote
        stmt_lote = (
            select(ValidacionTaller)
            .where(
                ValidacionTaller.evidencia_ref.like(f"%{LOTE_TAG}%")
                | ValidacionTaller.origen_clave.like(f"{LOTE_TAG}%")
            )
            .order_by(ValidacionTaller.fase, ValidacionTaller.item)
        )
        registros_lote = (await session.execute(stmt_lote)).scalars().all()

        print(f"=== AUDITORÍA DE ELIMINACIÓN SEGURA: LOTE {LOTE_TAG} ===")
        print(f"Total registros en validaciones_taller antes: {total_antes}")
        print(f"Registros encontrados del lote '{LOTE_TAG}': {len(registros_lote)}")

        if not registros_lote:
            print("No se encontraron registros pertenecientes al lote temporal.")
            await engine.dispose()
            return

        print("\nListado detallado de registros a eliminar:")
        for r in registros_lote:
            # Comprobar que todos son efectivamente del lote temporal
            detalles = r.detalles_campos or {}
            meta = detalles.get("_metadata", {})
            lote_en_meta = meta.get("lote")
            es_oficial = meta.get("es_dato_oficial", False)

            if es_oficial is True:
                raise RuntimeError(
                    f"¡ALERTA DE SEGURIDAD! El registro {r.id} está marcado como oficial (es_dato_oficial=True). "
                    "Operación abortada inmediatamente."
                )

            print(
                f"  [{r.fase}] ID={r.id} | Item={r.item} | Placa={r.placa_enmascarada} "
                f"| Veh={r.marca_modelo} | Falla={r.falla_real[:30]} | LoteMeta={lote_en_meta}"
            )

    if not confirm:
        print("\n[MODO DRY-RUN ACTIVO] No se ha eliminado ningún registro.")
        print("Para ejecutar la eliminación física, ejecute con: python scripts/eliminar_piloto_temporal_20260919.py --confirm")
        await engine.dispose()
        return

    # Ejecución física con confirmación
    print("\n[CONFIRMACIÓN RECIBIDA] Procediendo a eliminar registros del lote...")
    async with engine.begin() as session:
        res = await session.execute(
            delete(ValidacionTaller).where(
                ValidacionTaller.evidencia_ref.like(f"%{LOTE_TAG}%")
                | ValidacionTaller.origen_clave.like(f"{LOTE_TAG}%")
            )
        )
        eliminados = res.rowcount
        total_despues = (
            await session.execute(select(func.count()).select_from(ValidacionTaller))
        ).scalar_one()

    print(f"Registros eliminados físicamente: {eliminados}")
    print(f"Total registros en validaciones_taller después: {total_despues} (reducción exacta de {eliminados})")
    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma la eliminación física de los registros del lote temporal en base de datos.",
    )
    args = parser.parse_args()
    asyncio.run(ejecutar_eliminacion(confirm=args.confirm))


if __name__ == "__main__":
    main()
