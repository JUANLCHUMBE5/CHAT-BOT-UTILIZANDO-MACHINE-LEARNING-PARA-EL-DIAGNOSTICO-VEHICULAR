"""Auditoría forense de los 1,930 registros THESIS_POSTTEST en estado borrador.
Genera el artefacto docs/fase12/FASE12_3_AUDITORIA_HISTORICOS.csv.
"""

from __future__ import annotations

import asyncio
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.validation import ValidacionTaller

CSV_HISTORICOS = ROOT / "docs" / "fase12" / "FASE12_3_AUDITORIA_HISTORICOS.csv"


async def auditar_historicos() -> None:
    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # 1. Conteo total y estados
        stmt_total = (
            select(
                ValidacionTaller.tipo_registro,
                ValidacionTaller.estado_registro,
                ValidacionTaller.fase,
                func.count(),
                func.min(ValidacionTaller.fecha),
                func.max(ValidacionTaller.fecha),
                func.min(ValidacionTaller.item),
                func.max(ValidacionTaller.item),
            )
            .where(ValidacionTaller.tipo_registro == "THESIS_POSTTEST")
            .group_by(
                ValidacionTaller.tipo_registro,
                ValidacionTaller.estado_registro,
                ValidacionTaller.fase,
            )
        )
        res = (await session.execute(stmt_total)).all()
        print("=== RESUMEN GENERAL THESIS_POSTTEST ===")
        for r in res:
            print(f"Tipo: {r[0]} | Estado: {r[1]} | Fase: {r[2]} | Total: {r[3]} | Fechas: {r[4]} a {r[5]} | Items: {r[6]} a {r[7]}")

        # 2. Análisis de origen_clave
        # Ver cuántos son nulos vs con valor
        stmt_nulos = select(func.count()).where(
            ValidacionTaller.tipo_registro == "THESIS_POSTTEST",
            ValidacionTaller.origen_clave.is_(None),
        )
        nulos_count = (await session.execute(stmt_nulos)).scalar_one()

        stmt_con_origen = select(func.count()).where(
            ValidacionTaller.tipo_registro == "THESIS_POSTTEST",
            ValidacionTaller.origen_clave.isnot(None),
        )
        con_origen_count = (await session.execute(stmt_con_origen)).scalar_one()
        print(f"\nOrigen clave: {nulos_count} NULOS | {con_origen_count} CON VALOR")

        # Inspeccionar distintos valores de origen_clave si existen
        stmt_distintos = select(ValidacionTaller.origen_clave, func.count()).where(
            ValidacionTaller.tipo_registro == "THESIS_POSTTEST",
            ValidacionTaller.origen_clave.isnot(None),
        ).group_by(ValidacionTaller.origen_clave).limit(20)
        distintos = (await session.execute(stmt_distintos)).all()
        print("Muestra de origen_clave con valor:")
        for d in distintos:
            print(f"  {d[0]}: {d[1]}")

        # 3. Inspeccionar evidencia_ref y metodo_confirmacion
        stmt_evidencia = select(
            func.count().filter(ValidacionTaller.evidencia_ref.isnot(None)),
            func.count().filter(ValidacionTaller.evidencia_ref.is_(None)),
            func.count().filter(ValidacionTaller.diagnostico_id.isnot(None)),
            func.count().filter(ValidacionTaller.conversacion_id.isnot(None)),
        ).where(ValidacionTaller.tipo_registro == "THESIS_POSTTEST")
        ev_stats = (await session.execute(stmt_evidencia)).one()
        print(f"\nTrazabilidad: Con Evidencia={ev_stats[0]}, Sin Evidencia={ev_stats[1]}, Con Diagnostico_ID={ev_stats[2]}, Con Conversacion_ID={ev_stats[3]}")

        # 4. Muestra representativa de 100 filas para el CSV de auditoría
        stmt_export = (
            select(
                ValidacionTaller.id,
                ValidacionTaller.item,
                ValidacionTaller.fase,
                ValidacionTaller.tipo_registro,
                ValidacionTaller.estado_registro,
                ValidacionTaller.fecha,
                ValidacionTaller.origen_clave,
                ValidacionTaller.placa_enmascarada,
                ValidacionTaller.marca_modelo,
                ValidacionTaller.sintoma,
                ValidacionTaller.falla_real,
                ValidacionTaller.chatbot_prediccion,
                ValidacionTaller.tiempo_diagnostico_minutos,
                ValidacionTaller.prediccion_correcta,
                ValidacionTaller.campos_completos,
                ValidacionTaller.metodo_confirmacion,
                ValidacionTaller.evidencia_ref,
                ValidacionTaller.diagnostico_id,
            )
            .where(ValidacionTaller.tipo_registro == "THESIS_POSTTEST")
            .order_by(ValidacionTaller.item.asc())
            .limit(100)
        )
        filas = (await session.execute(stmt_export)).all()

        CSV_HISTORICOS.parent.mkdir(parents=True, exist_ok=True)
        with open(CSV_HISTORICOS, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id", "item", "fase", "tipo_registro", "estado_registro", "fecha",
                "origen_clave", "placa_enmascarada", "marca_modelo", "sintoma",
                "falla_real", "chatbot_prediccion", "tiempo_diagnostico_minutos",
                "prediccion_correcta", "campos_completos", "metodo_confirmacion",
                "evidencia_ref", "diagnostico_id"
            ])
            for r in filas:
                writer.writerow([str(v) if v is not None else "" for v in r])

        print(f"\n[ARTEFACTO GENERADO] {CSV_HISTORICOS} con muestra de {len(filas)} filas históricas.")


if __name__ == "__main__":
    asyncio.run(auditar_historicos())
