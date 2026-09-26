"""Publica resultados SIMULACION_POST en el historial de la base local solamente.

Los registros quedan con tipo_registro=DEVELOPMENT y con etiqueta visible
SIMULACION_POST. El script rechaza cualquier base que no sea localhost.
"""

from __future__ import annotations

import asyncio
import csv
import json
import sys
from datetime import datetime, time, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from src.config import settings
from src.infrastructure.database.connection import cerrar_conexion, obtener_engine
from src.infrastructure.database.models.catalogs import Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository


ESTADO = "SIMULACION_POST"
SALIDA = ROOT / "docs" / "simulaciones_tecnicas" / "simulacion_post_202609"
ARCHIVO = SALIDA / "SIMULACION_POST_30_CASOS_DETALLE.csv"
MODOS_HISTORIAL_VALIDOS = {
    "completo_ml_rag_llm", "diagnostico_degradado_ml_rag", "en_cola_gemini",
    "audio_espectral", "saludo", "baja_confianza", "esperando_clarificacion",
}


def predicciones(texto: str) -> list[dict]:
    try:
        valor = json.loads(texto or "[]")
        return valor if isinstance(valor, list) else []
    except json.JSONDecodeError:
        return []


async def publicar() -> None:
    if settings.database.host not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("SEGURIDAD: solo se permite publicar SIMULACION_POST en PostgreSQL local.")
    if not ARCHIVO.exists():
        raise FileNotFoundError(f"No existe el detalle de simulación: {ARCHIVO}")

    with ARCHIVO.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    exitosas = [fila for fila in filas if fila.get("estado_ejecucion") == "EJECUTADO"]
    if len(exitosas) != 30:
        raise RuntimeError(f"Se esperaban 30 ejecuciones exitosas y hay {len(exitosas)}; no se publica un lote parcial.")

    engine = obtener_engine()
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            async with session.begin():
                existentes = await session.execute(
                    select(Diagnostico.id).where(Diagnostico.sintoma_original.like("[SIMULACION_POST:%"))
                )
                if existentes.first():
                    if "--reemplazar" not in sys.argv:
                        raise RuntimeError("Ya existen simulaciones en el historial local; se evita duplicarlas.")
                    await session.execute(
                        delete(Diagnostico).where(Diagnostico.sintoma_original.like("[SIMULACION_POST:%"))
                    )

                usuario = (
                    await session.execute(
                        select(Usuario)
                        .where(Usuario.activo.is_(True), Usuario.bloqueado.is_(False))
                        .order_by(Usuario.creado_en.asc())
                        .limit(1)
                    )
                ).scalar_one_or_none()
                if not usuario:
                    raise RuntimeError("No hay un usuario activo local para asociar el historial.")

                repo = DiagnosticoRepository(session)
                for indice, fila in enumerate(exitosas, start=1):
                    alternativas = predicciones(fila.get("alternativas_diagnosticas_carbot", ""))
                    modo_real = fila.get("modo_diagnostico") or "sin_modo_reportado"
                    modo_historial = (
                        modo_real if modo_real in MODOS_HISTORIAL_VALIDOS
                        else "diagnostico_degradado_ml_rag"
                    )
                    marca = f"[{ESTADO}:{fila['id_caso']}] "
                    trazabilidad = {
                        "origen": ESTADO,
                        "no_oficial": True,
                        "excluido_de_tesis": True,
                        "id_caso": fila["id_caso"],
                        "fecha_simulada": fila["fecha"],
                        "referencia_esperada_simulada": fila["diagnostico_referencia_esperado_simulado"],
                        "coincide_principal_con_referencia": fila["coincide_principal_con_referencia"] == "True",
                        "predicciones_ml": alternativas,
                        "modo_diagnostico_real": modo_real,
                        "modo_diagnostico_historial": modo_historial,
                        "tiempo_total_ms": int(float(fila["tiempo_real_ms"])),
                        "etapas": [
                            {"clave": "ml", "nombre": settings.model_algorithm, "estado": "completado", "duracion_ms": int(float(fila.get("tiempo_ml_ms") or 0))},
                            {"clave": "rag", "nombre": "Búsqueda RAG en manuales", "estado": "completado", "duracion_ms": int(float(fila.get("tiempo_rag_ms") or 0))},
                            {"clave": "llm", "nombre": "Respuesta del pipeline", "estado": "completado", "duracion_ms": int(float(fila.get("tiempo_llm_ms") or 0))},
                        ],
                    }
                    diagnostico = await repo.crear_diagnostico(
                        taller_id=usuario.taller_id,
                        mecanico_id=usuario.id,
                        sintoma_original=marca + fila["sintoma_ingresado"],
                        sintoma_normalizado=fila["sintoma_ingresado"],
                        falla_predicha=fila["diagnostico_principal_carbot"],
                        confianza=float(fila.get("confianza_ml") or 0),
                        similitud_rag=0,
                        fuente="hibrido",
                        modo_diagnostico=modo_historial,
                        estado="generado",
                        duracion_ms=int(float(fila["tiempo_real_ms"])),
                        tiempo_inferencia_ml_ms=int(float(fila.get("tiempo_ml_ms") or 0)),
                        conclusion_mecanico=(
                            f"{ESTADO} — referencia esperada simulada: "
                            f"{fila['diagnostico_referencia_esperado_simulado']}. "
                            "No es confirmación física ni dato oficial de tesis."
                        ),
                        sintesis_llm=fila.get("informacion_generada_carbot") or "",
                        version_modelo_ml=settings.model_version,
                        version_corpus_rag="RAG_CANDIDATO_V1",
                        trazabilidad=trazabilidad,
                    )
                    diagnostico.tipo_registro = "DEVELOPMENT"
                    fecha = datetime.fromisoformat(fila["fecha"]).replace(
                        hour=9 + ((indice - 1) % 3), tzinfo=timezone.utc
                    )
                    diagnostico.creado_en = fecha
                    for orden, prediccion in enumerate(alternativas[:3], start=1):
                        await repo.agregar_hipotesis(
                            diagnostico_id=diagnostico.id,
                            orden=orden,
                            falla_probable=str(prediccion.get("falla") or fila["diagnostico_principal_carbot"]),
                            confianza=float(prediccion.get("probabilidad") or 0),
                            evidencia=f"{ESTADO}; no oficial; excluido de tesis.",
                            prueba_recomendada=fila.get("contexto_rag") or None,
                        )
    finally:
        await cerrar_conexion()

    print("OK: 30 registros SIMULACION_POST publicados exclusivamente en el historial PostgreSQL local.")


if __name__ == "__main__":
    asyncio.run(publicar())
