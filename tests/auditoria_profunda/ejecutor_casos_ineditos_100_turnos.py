"""Ejecutor automatizado de los 100 turnos adicionales inéditos (5 casos x 20 turnos)."""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict

sys.path.insert(0, os.path.abspath("."))
os.environ["DATABASE_ENABLED"] = "false"
os.environ["ML_ROOT"] = r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning"

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from tests.auditoria_profunda.casos_ineditos_100_turnos import CONVERSACIONES_INEDITAS_100_TURNOS


def evaluar_memoria_estricta(estado: Any, vehiculo_esp: Dict[str, Any], hechos_esp: Dict[str, Any]) -> Dict[str, Any]:
    total_esperados = len(hechos_esp)
    hechos_retenidos = 0
    detalles = {}

    for k, v in hechos_esp.items():
        conservado = False
        val_str = str(v).lower()
        if k == "marca":
            conservado = bool(estado.marca and estado.marca.lower() == vehiculo_esp["marca"].lower())
        elif k == "modelo":
            conservado = bool(estado.modelo and vehiculo_esp["modelo"].lower() in estado.modelo.lower())
        elif k == "anio":
            conservado = bool(estado.anio and str(vehiculo_esp["anio"]) in str(estado.anio))
        elif k == "placa":
            p_esp = vehiculo_esp["placa"].replace("-", "").lower()
            p_act = (estado.placa or "").replace("-", "").lower()
            conservado = bool(p_esp in p_act)
        elif k == "combustible":
            conservado = bool(estado.combustible and vehiculo_esp.get("combustible", "").lower() in estado.combustible.lower())
        elif k.startswith("dtc_"):
            dtc_code = k.replace("dtc_", "").upper()
            conservado = any(dtc_code in hk.upper() or dtc_code in str(h.valor).upper() for hk, h in estado.hechos.items())
        else:
            conservado = (
                any(k in hk.lower() or val_str in str(h.valor).lower() for hk, h in estado.hechos.items())
                or k in estado.measurements
                or any(k in str(p).lower() for p in estado.completed_tests.keys())
                or any(k.replace("_descartada", "").replace("_descartado", "") in d for d in estado.hipotesis_descartadas)
            )

        if conservado:
            hechos_retenidos += 1
        detalles[k] = conservado

    retencion = (hechos_retenidos / total_esperados) if total_esperados > 0 else 1.0
    return {
        "hechos_esperados": total_esperados,
        "hechos_retenidos": hechos_retenidos,
        "retencion": round(retencion, 4),
        "detalles": detalles,
    }


async def ejecutar_100_turnos_ineditos():
    print("=" * 80)
    print("EJECUTANDO EVALUACIÓN DE 100 TURNOS ADICIONALES INÉDITOS (5 CASOS x 20 TURNOS)")
    print("=" * 80)

    repo = InMemoryConversationRepository()
    gestor = GestorDiagnostico()
    orquestador = OrquestadorConversacion(repositorio=repo)

    total_turnos = 0
    hechos_totales_esperados = 0
    hechos_totales_retenidos = 0
    tiempos_ms = []
    bucles_total = 0
    casos_resumen = []

    for caso in CONVERSACIONES_INEDITAS_100_TURNOS:
        cid = caso["id"]
        titulo = caso["titulo"]
        print(f"\n[{cid}] {titulo} (20 turnos)...")
        session_id = f"inedita_100_{cid}_{int(time.time()*1000)}"

        preguntas_emitidas = set()
        bucles_caso = 0

        for num_t, (msg, tag) in enumerate(caso["turnos"], start=1):
            total_turnos += 1
            t0 = time.perf_counter()
            res = await orquestador.procesar_turno(
                session_id,
                msg,
                gestor,
            )
            dt_ms = round((time.perf_counter() - t0) * 1000, 2)
            tiempos_ms.append(dt_ms)

            resp_txt = res.get("respuesta_texto", "")
            if res.get("es_pregunta"):
                preg_clean = " ".join(resp_txt.split())
                if preg_clean in preguntas_emitidas:
                    bucles_caso += 1
                    bucles_total += 1
                preguntas_emitidas.add(preg_clean)

        est = res.get("estado")
        eval_mem = evaluar_memoria_estricta(est, caso["vehiculo_esperado"], caso["hechos_esperados"])
        hechos_totales_esperados += eval_mem["hechos_esperados"]
        hechos_totales_retenidos += eval_mem["hechos_retenidos"]

        pct = eval_mem["retencion"] * 100
        print(f"  -> Retención de hechos estructurada: {pct:.1f}% ({eval_mem['hechos_retenidos']}/{eval_mem['hechos_esperados']})")
        print(f"  -> Bucles detectados: {bucles_caso}")

        casos_resumen.append({
            "id": cid,
            "titulo": titulo,
            "turnos": len(caso["turnos"]),
            "memoria": eval_mem,
            "bucles": bucles_caso,
        })

    pct_global = (hechos_totales_retenidos / hechos_totales_esperados * 100) if hechos_totales_esperados else 0
    lat_prom = round(sum(tiempos_ms) / len(tiempos_ms), 2) if tiempos_ms else 0
    tiempos_ordenados = sorted(tiempos_ms)
    p95_idx = int(len(tiempos_ordenados) * 0.95)
    lat_p95 = tiempos_ordenados[p95_idx] if tiempos_ordenados else 0

    print("\n" + "=" * 80)
    print("RESUMEN DE LOS 100 TURNOS ADICIONALES INÉDITOS:")
    print(f"  Total turnos procesados: {total_turnos}")
    print(f"  Retención de hechos estructurada: {hechos_totales_retenidos}/{hechos_totales_esperados} ({pct_global:.2f}%)")
    print(f"  Total bucles detectados: {bucles_total}")
    print(f"  Latencia promedio: {lat_prom} ms (P95: {lat_p95} ms)")
    print("=" * 80)

    res_final = {
        "total_turnos": total_turnos,
        "total_casos": len(casos_resumen),
        "retencion_global": {
            "numerador": hechos_totales_retenidos,
            "denominador": hechos_totales_esperados,
            "porcentaje": round(pct_global, 2),
        },
        "bucles_total": bucles_total,
        "rendimiento": {
            "latencia_promedio_ms": lat_prom,
            "latencia_p95_ms": lat_p95,
        },
        "casos": casos_resumen,
    }

    out_path = "tests/auditoria_profunda/metricas_100_turnos_ineditos.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res_final, f, ensure_ascii=False, indent=2)
    print(f"Métricas guardadas en {out_path}")


if __name__ == "__main__":
    asyncio.run(ejecutar_100_turnos_ineditos())
