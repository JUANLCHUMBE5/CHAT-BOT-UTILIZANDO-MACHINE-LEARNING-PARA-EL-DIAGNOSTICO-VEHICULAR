#!/usr/bin/env python3
"""Completa procedimientos RAG faltantes sin sobrescribir datos ya registrados."""

import asyncio
from pathlib import Path
import sys

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))
load_dotenv(RAIZ_PROYECTO / ".env")

from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.motor_rag import MotorRAG


VALORES_SIN_PROCEDIMIENTO = {
    "",
    "Sin procedimiento RAG registrado",
    "Inspección directa de componentes en taller mecánico",
}


def tiene_procedimiento_real(valor: str | None) -> bool:
    normalizado = (valor or "").strip().lower()
    if not normalizado:
        return False
    return not any(
        indicador in normalizado
        for indicador in (
            "sin procedimiento rag",
            "inspección directa de componentes",
            "no se encontró un procedimiento",
            "no se encontro un procedimiento",
            "manual técnico no indexado",
            "manual tecnico no indexado",
            "error al buscar",
        )
    )


async def main() -> None:
    motor = MotorRAG()
    actualizados = 0
    sin_coincidencia = 0

    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        diagnosticos = (
            await session.execute(
                select(Diagnostico).options(selectinload(Diagnostico.hipotesis))
            )
        ).scalars().all()

        for diagnostico in diagnosticos:
            if not diagnostico.hipotesis:
                continue
            hipotesis = diagnostico.hipotesis[0]
            procedimiento_actual = (hipotesis.prueba_recomendada or "").strip()
            if tiene_procedimiento_real(procedimiento_actual):
                continue

            consulta = diagnostico.sintoma_normalizado or diagnostico.sintoma_original
            procedimiento, titulo, similitud = motor.recuperar_contexto_con_similitud(consulta)
            if titulo in {"Coincidencia baja", "Desconocido", "Error"}:
                sin_coincidencia += 1
                continue

            hipotesis.prueba_recomendada = procedimiento
            hipotesis.evidencia = (
                "Fuente: Corpus local preliminar no validado como OEM. "
                f"Procedimiento: {titulo}. Corpus: {motor.corpus_version}"
            )
            diagnostico.similitud_rag = similitud
            diagnostico.version_corpus_rag = motor.corpus_version
            actualizados += 1

        await session.commit()

    print(f"Diagnósticos RAG completados: {actualizados}")
    print(f"Sin coincidencia suficiente: {sin_coincidencia}")


if __name__ == "__main__":
    asyncio.run(main())
