"""Script de saneamiento de registros piloto existentes para FASE 12.2.

Identifica exclusivamente registros con origen_clave LIKE 'PILOTO_TEMPORAL_20260919_%',
respalda su estado previo en CSV de auditoría y los reclasifica a PILOT.
"""

from __future__ import annotations

import asyncio
import csv
import sys
from pathlib import Path

# Setup sys.path
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.validation import ValidacionTaller

CSV_AUDITORIA = ROOT / "docs" / "fase12" / "FASE12_2_AUDITORIA_SANEAMIENTO.csv"


async def sanear_registros_piloto() -> None:
    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            # 1. Identificar registros objetivo
            stmt = (
                select(ValidacionTaller)
                .where(ValidacionTaller.origen_clave.like("PILOTO_TEMPORAL_20260919_%"))
                .order_by(ValidacionTaller.creado_en.asc())
            )
            registros = (await session.execute(stmt)).scalars().all()
            total_identificados = len(registros)
            print(f"[AUDITORIA] Total de registros piloto identificados con origen_clave LIKE 'PILOTO_TEMPORAL_20260919_%': {total_identificados}")

            # 2. Respaldar en CSV antes de modificar
            CSV_AUDITORIA.parent.mkdir(parents=True, exist_ok=True)
            filas_respaldo = []
            ids_a_modificar = []

            for r in registros:
                ids_a_modificar.append(r.id)
                filas_respaldo.append({
                    "id": str(r.id),
                    "taller_id": str(r.taller_id),
                    "vehiculo_marca_modelo": r.marca_modelo,
                    "diagnostico_id": str(r.diagnostico_id) if r.diagnostico_id else "",
                    "fase_previa": r.fase,
                    "tipo_registro_previo": r.tipo_registro,
                    "estado_registro_previo": r.estado_registro,
                    "origen_clave": r.origen_clave or "",
                    "tipo_registro_nuevo": "PILOT",
                    "estado_registro_nuevo": "borrador",
                    "motivo": "Reclasificacion de registros piloto temporales para blindaje oficial de muestra (0/60)",
                })

            fieldnames = [
                "id",
                "taller_id",
                "vehiculo_marca_modelo",
                "diagnostico_id",
                "fase_previa",
                "tipo_registro_previo",
                "estado_registro_previo",
                "origen_clave",
                "tipo_registro_nuevo",
                "estado_registro_nuevo",
                "motivo",
            ]

            with open(CSV_AUDITORIA, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filas_respaldo)

            print(f"[AUDITORIA] Respaldo guardado exitosamente en: {CSV_AUDITORIA}")

            # 3. Aplicar actualización exclusiva a los registros identificados
            if ids_a_modificar:
                upd_stmt = (
                    update(ValidacionTaller)
                    .where(ValidacionTaller.id.in_(ids_a_modificar))
                    .values(tipo_registro="PILOT", estado_registro="borrador")
                )
                await session.execute(upd_stmt)
                await session.commit()
                print(f"[AUDITORIA] Actualizados {len(ids_a_modificar)} registros a tipo_registro='PILOT', estado_registro='borrador'")

            # 4. Verificaciones finales en base de datos
            c_thesis_pre_oficial = await session.scalar(
                select(func.count())
                .select_from(ValidacionTaller)
                .where(
                    ValidacionTaller.tipo_registro == "THESIS_PRETEST",
                    ValidacionTaller.estado_registro == "verificado",
                )
            )
            c_thesis_post_oficial = await session.scalar(
                select(func.count())
                .select_from(ValidacionTaller)
                .where(
                    ValidacionTaller.tipo_registro == "THESIS_POSTTEST",
                    ValidacionTaller.estado_registro == "verificado",
                )
            )
            c_pilot = await session.scalar(
                select(func.count()).select_from(ValidacionTaller).where(ValidacionTaller.tipo_registro == "PILOT")
            )
            c_dev = await session.scalar(
                select(func.count()).select_from(ValidacionTaller).where(ValidacionTaller.tipo_registro == "DEVELOPMENT")
            )
            c_reg = await session.scalar(
                select(func.count()).select_from(ValidacionTaller).where(ValidacionTaller.tipo_registro == "REGRESSION")
            )

            print("\n=== CONTEO POST-SANEAMIENTO EN POSTGRESQL ===")
            print(f"THESIS_PRETEST oficial (verificado) : {c_thesis_pre_oficial}")
            print(f"THESIS_POSTTEST oficial (verificado): {c_thesis_post_oficial}")
            print(f"PILOT                               : {c_pilot}")
            print(f"DEVELOPMENT                         : {c_dev}")
            print(f"REGRESSION                          : {c_reg}")
            print(f"MUESTRA OFICIAL TOTAL (verificada)  : {c_thesis_pre_oficial + c_thesis_post_oficial} / 60")
            print("============================================\n")

            assert c_thesis_pre_oficial == 0, f"ERROR: THESIS_PRETEST oficial debe ser 0, pero es {c_thesis_pre_oficial}"
            assert c_thesis_post_oficial == 0, f"ERROR: THESIS_POSTTEST oficial debe ser 0, pero es {c_thesis_post_oficial}"
            assert c_pilot == 20, f"ERROR: PILOT debe ser 20, pero es {c_pilot}"
            print("[VERIFICACION EXITOSA] Muestra oficial limpia: 0/60 registros oficiales.")

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Fallo durante el saneamiento: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(sanear_registros_piloto())
