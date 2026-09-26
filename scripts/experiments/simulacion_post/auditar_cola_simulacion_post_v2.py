"""Audita los UUID V2 en la cola durable sin crear ni reprocesar diagnósticos."""
from __future__ import annotations

import asyncio
import csv
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from src.infrastructure.database.connection import cerrar_conexion, obtener_engine
from src.infrastructure.database.models.jobs import TrabajoGemini

CSV_V2 = (
    ROOT
    / "docs"
    / "simulaciones_tecnicas"
    / "simulacion_post_v2_202609"
    / "SIMULACION_POST_V2_30_CONVERSACIONES.csv"
)


async def main() -> None:
    with CSV_V2.open(encoding="utf-8-sig", newline="") as archivo:
        filas = [fila for fila in csv.DictReader(archivo) if fila["estado_final"] == "en_cola_gemini"]
    ids = [uuid.UUID(fila["solicitud_id"]) for fila in filas]
    async with obtener_engine().connect() as conexion:
        resultado = await conexion.execute(select(TrabajoGemini).where(TrabajoGemini.id.in_(ids)))
        trabajos = {str(trabajo.id): trabajo for trabajo in resultado.scalars()}
    auditoria = []
    ids_no_recuperables: set[str] = set()
    for fila in filas:
        trabajo = trabajos.get(fila["solicitud_id"])
        auditoria.append(
            {
                "caso": fila["id_caso"],
                "placa": fila["placa_simulada"],
                "solicitud_id": fila["solicitud_id"],
                "en_trabajos_gemini": trabajo is not None,
                "estado_trabajo": trabajo.estado if trabajo else None,
                "diagnostico_id": str(trabajo.diagnostico_id) if trabajo and trabajo.diagnostico_id else None,
                "conversacion_id": str(trabajo.conversacion_id) if trabajo and trabajo.conversacion_id else None,
                "proveedor": trabajo.proveedor if trabajo else None,
                "error_ultimo": trabajo.error_ultimo if trabajo else None,
            }
        )
        if trabajo is None:
            ids_no_recuperables.add(fila["solicitud_id"])
    if ids_no_recuperables:
        for fila in filas:
            if fila["solicitud_id"] in ids_no_recuperables:
                fila["estado_final_original"] = fila["estado_final"]
                fila["estado_final"] = "JOB_NO_RECUPERABLE"
                fila["motivo_no_recuperable"] = (
                    "El UUID no existe en trabajos_gemini; la cola en memoria de la ejecución V2 "
                    "ya no está disponible y no hay conversación ni diagnóstico durable asociados."
                )
        with CSV_V2.open(encoding="utf-8-sig", newline="") as archivo:
            todas_las_filas = list(csv.DictReader(archivo))
        for fila in todas_las_filas:
            if fila["solicitud_id"] in ids_no_recuperables:
                fila["estado_final_original"] = fila["estado_final"]
                fila["estado_final"] = "JOB_NO_RECUPERABLE"
                fila["motivo_no_recuperable"] = (
                    "El UUID no existe en trabajos_gemini; la cola en memoria de la ejecución V2 "
                    "ya no está disponible y no hay conversación ni diagnóstico durable asociados."
                )
            else:
                fila.setdefault("estado_final_original", "")
                fila.setdefault("motivo_no_recuperable", "")
        campos = list(todas_las_filas[0])
        with CSV_V2.open("w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(todas_las_filas)
    print(json.dumps(auditoria, ensure_ascii=False, indent=2, default=str))
    await cerrar_conexion()


if __name__ == "__main__":
    asyncio.run(main())
