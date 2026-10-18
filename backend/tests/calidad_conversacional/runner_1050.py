"""Ejecutor y validador por lotes de los 1,050 escenarios multiturno conversacionales."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

os.environ.setdefault("DATABASE_ENABLED", "false")
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["GROQ_CHAT_ENABLED"] = "false"

# Silenciar logs para máximo rendimiento y evitar I/O bottlenecks en consola
logging.getLogger("ChatbotVehicular").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from tests.calidad_conversacional.escenarios_1050 import construir_1050_escenarios


async def evaluar_un_escenario(
    esc: Dict[str, Any],
    gestor: GestorDiagnostico,
) -> Dict[str, Any]:
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    session_id = esc["id"]
    familia = esc["familia"]
    turnos = esc["turnos"]

    preguntas_previas: List[str] = []
    preguntas_repetidas = 0
    consultas_tecnicas_ok = 0
    fallo = False
    razon = ""

    import re
    for num_t, mensaje in enumerate(turnos, start=1):
        res = await orquestador.procesar_turno(session_id, mensaje, gestor)
        resp_txt = str(res.get("respuesta_texto") or "")
        decision = res.get("decision")
        status = str(res.get("status") or "")

        # Detección de repreguntas idénticas
        preguntas_turno = [p.strip().lower() for p in re.findall(r"¿([^?]+)\?", resp_txt)]
        for p in preguntas_turno:
            if p in preguntas_previas:
                preguntas_repetidas += 1
            preguntas_previas.append(p)

        # Familia 1: verificación de turno 2 para consultas técnicas
        if familia == "1_CONSULTAS_TECNICAS" and num_t == 2:
            if decision in ("DETALLE", "TOLERANCIA_OEM", "CONCLUSION_TECNICA") or any(
                s in status.lower() for s in ("detalle", "consulta_tecnica", "tolerancia")
            ):
                consultas_tecnicas_ok = 1
            else:
                fallo = True
                razon = f"Consulta técnica turno 2 no despachada como DETALLE: decision={decision}, status={status}"

    # Verificación de retención de vehículo y síntomas
    estado = await repo.get_session(session_id)
    ret_veh = False
    ret_sint = None
    if estado:
        esperado_v = esc.get("vehiculo_esperado", {})
        marca_esp = esperado_v.get("marca")
        if marca_esp and estado.marca and estado.marca.lower() == marca_esp.lower():
            ret_veh = True
        elif marca_esp:
            fallo = True
            razon = f"Vehículo no retenido: esperado={marca_esp}, actual={estado.marca}"

        if esc.get("sintoma_preservado"):
            if estado.active_symptoms or estado.hechos:
                ret_sint = True
            else:
                fallo = True
                razon = "Síntomas o hechos borrados"

    return {
        "id": session_id,
        "familia": familia,
        "fallo": fallo,
        "razon": razon,
        "retencion_vehiculo": ret_veh,
        "retencion_sintomas": ret_sint,
        "consultas_tecnicas_ok": consultas_tecnicas_ok,
        "preguntas_repetidas": preguntas_repetidas,
    }


async def ejecutar_lote(
    start_idx: int,
    end_idx: int,
    gestor: GestorDiagnostico,
    todos_escenarios: List[Dict[str, Any]],
    archivo_salida: str,
    concurrencia: int = 10,
):
    lote = todos_escenarios[start_idx:end_idx]
    sem = asyncio.Semaphore(concurrencia)
    resultados = []

    t0 = time.time()

    async def _worker(esc):
        async with sem:
            return await evaluar_un_escenario(esc, gestor)

    tasks = [_worker(esc) for esc in lote]
    resultados = await asyncio.gather(*tasks)

    t1 = time.time()
    duracion = t1 - t0

    payload = {
        "start_idx": start_idx,
        "end_idx": end_idx,
        "total_procesados": len(resultados),
        "tiempo_segundos": duracion,
        "resultados": resultados,
    }

    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Lote [{start_idx}:{end_idx}] completado en {duracion:.2f}s ({len(resultados)} escenarios)")


async def main_async(args):
    gestor = GestorDiagnostico()
    todos_escenarios = construir_1050_escenarios()

    total = len(todos_escenarios)
    start = max(0, args.start)
    end = min(total, args.end)

    base_dir = os.path.dirname(__file__)
    salida_parcial = os.path.join(base_dir, f"parcial_{start}_{end}.json")

    print(f"Iniciando ejecucion de escenarios {start} a {end} (concurrencia={args.concurrencia})...")
    await ejecutar_lote(
        start_idx=start,
        end_idx=end,
        gestor=gestor,
        todos_escenarios=todos_escenarios,
        archivo_salida=salida_parcial,
        concurrencia=args.concurrencia,
    )


def consolidar_resultados():
    base_dir = os.path.dirname(__file__)
    todos_escenarios = construir_1050_escenarios()
    total_esperado = len(todos_escenarios)

    resultados_map = {}
    tiempo_total = 0.0

    for fname in os.listdir(base_dir):
        if fname.startswith("parcial_") and fname.endswith(".json"):
            fp = os.path.join(base_dir, fname)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tiempo_total += float(data.get("tiempo_segundos", 0.0))
                    for r in data.get("resultados", []):
                        resultados_map[r["id"]] = r
            except Exception as e:
                print(f"Error leyendo {fname}: {e}")

    resultados = list(resultados_map.values())
    total = len(resultados)

    fam_1_total = sum(1 for e in todos_escenarios if e["familia"] == "1_CONSULTAS_TECNICAS")
    sint_escenario_ids = {e["id"] for e in todos_escenarios if e.get("sintoma_preservado")}
    sint_total = len(sint_escenario_ids)

    retencion_vehiculo_aciertos = sum(1 for r in resultados if r["retencion_vehiculo"])
    retencion_sintomas_aciertos = sum(
        1 for r in resultados
        if r.get("id") in sint_escenario_ids and r.get("retencion_sintomas")
    )
    consultas_tecnicas_aciertos = sum(r["consultas_tecnicas_ok"] for r in resultados)
    preguntas_repetidas_totales = sum(r["preguntas_repetidas"] for r in resultados)

    fallos_por_familia: Dict[str, int] = {}
    detalles_fallos: List[Dict[str, Any]] = []

    for r in resultados:
        if r["fallo"]:
            fam = r["familia"]
            fallos_por_familia[fam] = fallos_por_familia.get(fam, 0) + 1
            detalles_fallos.append({
                "id": r["id"],
                "familia": fam,
                "razon": r["razon"],
            })

    metricas = {
        "total_escenarios": total,
        "total_turnos": total * 3,
        "tiempo_total_segundos": round(tiempo_total, 2),
        "latencia_promedio_turno_ms": round((tiempo_total / (total * 3)) * 1000, 2) if total else 0.0,
        "retencion_vehiculo": {
            "aciertos": retencion_vehiculo_aciertos,
            "total": total,
            "porcentaje": round(retencion_vehiculo_aciertos / total * 100, 2) if total else 0.0,
        },
        "retencion_sintomas": {
            "aciertos": retencion_sintomas_aciertos,
            "total": sint_total,
            "porcentaje": round(retencion_sintomas_aciertos / sint_total * 100, 2) if sint_total else 0.0,
        },
        "despacho_consultas_tecnicas": {
            "aciertos": consultas_tecnicas_aciertos,
            "total": fam_1_total,
            "porcentaje": round(consultas_tecnicas_aciertos / fam_1_total * 100, 2) if fam_1_total else 0.0,
        },
        "preguntas_repetidas_totales": preguntas_repetidas_totales,
        "fallos_por_familia": fallos_por_familia,
        "ejemplos_fallos": detalles_fallos[:10],
    }

    out_path = os.path.join(base_dir, "resultado_1050_escenarios.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("CONSOLIDADO DE EVALUACIÓN DE 1,050 ESCENARIOS:")
    print(f"Total escenarios consolidados: {total}/{total_esperado} (turnos: {total * 3})")
    print(f"Tiempo acumulado: {tiempo_total:.2f}s | Latencia promedio concurrente/turno: {metricas['latencia_promedio_turno_ms']}ms")
    print(f"Retención de Vehículo: {metricas['retencion_vehiculo']['porcentaje']}% ({retencion_vehiculo_aciertos}/{total})")
    print(f"Retención de Síntomas: {metricas['retencion_sintomas']['porcentaje']}% ({retencion_sintomas_aciertos}/{sint_total})")
    print(f"Despacho de Consultas Técnicas: {metricas['despacho_consultas_tecnicas']['porcentaje']}% ({consultas_tecnicas_aciertos}/{fam_1_total})")
    print(f"Repreguntas idénticas totales: {preguntas_repetidas_totales}")
    print(f"Fallos totales: {len(detalles_fallos)}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=1050)
    parser.add_argument("--concurrencia", type=int, default=15)
    parser.add_argument("--consolidar", action="store_true")

    args = parser.parse_args()

    if args.consolidar:
        consolidar_resultados()
    else:
        asyncio.run(main_async(args))
