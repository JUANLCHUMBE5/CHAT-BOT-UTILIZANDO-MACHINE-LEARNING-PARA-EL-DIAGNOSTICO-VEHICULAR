"""Ejecutor automatizado de los 200 turnos completamente nuevos para validación de regresión."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, os.path.abspath("."))

try:
    from tests.auditoria_profunda.casos_nuevos_200_turnos import CASOS_NUEVOS_200_TURNOS
except ImportError:
    from scratch.auditoria_profunda.casos_nuevos_200_turnos import CASOS_NUEVOS_200_TURNOS
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.gestor_diagnostico import GestorDiagnostico


def evaluar_memoria_caso_nuevo(estado: Any, hechos_esperados: Dict[str, Any]) -> Dict[str, Any]:
    total_esperados = len(hechos_esperados)
    hechos_retenidos = 0
    detalle = {}

    for clave, valor_esp in hechos_esperados.items():
        conservado = False
        if clave == "placa":
            conservado = (estado.placa == valor_esp)
        elif clave == "marca":
            conservado = bool(estado.marca and estado.marca.lower() == valor_esp.lower())
        elif clave == "modelo":
            conservado = bool(estado.modelo and valor_esp.lower() in estado.modelo.lower())
        elif clave == "anio":
            conservado = (estado.anio == valor_esp)
        elif clave == "dtc":
            dtc_str = valor_esp.upper()
            conservado = any(dtc_str in str(h.valor).upper() or dtc_str in str(k).upper() for k, h in estado.hechos.items()) or any(dtc_str in m.upper() for m in estado.historial_mensajes_usuario)
        else:
            val_str = str(valor_esp).lower()
            conservado = (
                any(clave in k.lower() or val_str in str(h.valor).lower() for k, h in estado.hechos.items())
                or clave in estado.measurements
                or any(clave in str(p).lower() for p in estado.completed_tests.keys())
                or any(val_str in m.lower() for m in estado.historial_mensajes_usuario)
                or any(val_str in str(v).lower() for v in estado.measurements.values())
            )

        if conservado:
            hechos_retenidos += 1
        detalle[clave] = conservado

    retencion = (hechos_retenidos / total_esperados) if total_esperados > 0 else 1.0
    return {
        "hechos_esperados": total_esperados,
        "hechos_retenidos": hechos_retenidos,
        "retencion": round(retencion, 4),
        "detalle": detalle,
    }


async def ejecutar_200_turnos():
    print("=" * 80)
    print("EJECUTANDO 200 TURNOS NUEVOS E INÉDITOS (10 CASOS x 20 TURNOS)")
    print("=" * 80)

    gestor = GestorDiagnostico()
    latencias = []
    total_turnos = 0
    seguridad_interceptada = []
    resultados_casos = []

    for idx, c in enumerate(CASOS_NUEVOS_200_TURNOS, 1):
        cid = c["id"]
        titulo = c["titulo"]
        turnos = c["turnos"]
        hechos_esp = c["hechos_esperados"]
        
        session_id = f"nuevo_val_{cid}_{time.time_ns()}"
        orquestador = OrquestadorConversacion()
        transcripcion = []

        print(f"\n[{idx}/10] {cid}: {titulo} ({len(turnos)} turnos)...")

        estado_actual = None
        for num_t, msg in enumerate(turnos, 1):
            t0 = time.perf_counter()
            resp = await orquestador.procesar_turno(session_id, msg, gestor)
            dt_ms = (time.perf_counter() - t0) * 1000
            latencias.append(dt_ms)
            total_turnos += 1

            estado_act = resp.get("estado")
            estado_actual = estado_act
            ultimo_trace = estado_act.trazabilidad[-1] if (estado_act and estado_act.trazabilidad) else {}

            resp_texto = resp.get("respuesta_texto", "")
            es_seguridad = (
                resp.get("decision") == "SEGURIDAD_CRITICA"
                or ultimo_trace.get("decision") == "SEGURIDAD_CRITICA"
                or "🛑" in resp_texto
                or bool(ultimo_trace.get("intervencion_seguridad"))
            )

            if es_seguridad:
                seguridad_interceptada.append({
                    "caso": cid,
                    "turno": num_t,
                    "mensaje": msg,
                    "decision": resp.get("decision"),
                    "respuesta": resp_texto[:120].encode("ascii", "replace").decode("ascii"),
                })

            transcripcion.append({
                "turno": num_t,
                "mensaje": msg,
                "respuesta": resp_texto,
                "decision": resp.get("decision"),
                "seguridad": es_seguridad,
            })

        estado_final = estado_actual
        memoria_eval = evaluar_memoria_caso_nuevo(estado_final, hechos_esp)

        resultados_casos.append({
            "id": cid,
            "titulo": titulo,
            "turnos": len(turnos),
            "memoria": memoria_eval,
            "transcripcion": transcripcion,
        })
        print(f"  -> Retención de hechos: {memoria_eval['retencion']:.1%} ({memoria_eval['hechos_retenidos']}/{memoria_eval['hechos_esperados']})")

    # Resumen
    retenciones = [r["memoria"]["retencion"] for r in resultados_casos]
    retencion_promedio = sum(retenciones) / len(retenciones) if retenciones else 0.0
    lat_prom = sum(latencias) / len(latencias) if latencias else 0.0
    lat_p95 = sorted(latencias)[int(len(latencias) * 0.95)] if latencias else 0.0

    print("\n" + "=" * 80)
    print("RESUMEN DE LOS 200 TURNOS NUEVOS:")
    print(f"  Total turnos procesados: {total_turnos}")
    print(f"  Retención promedio de memoria: {retencion_promedio:.1%}")
    print(f"  Intercepciones críticas de seguridad: {len(seguridad_interceptada)}")
    print(f"  Latencia promedio: {lat_prom:.2f} ms (P95: {lat_p95:.2f} ms)")
    print("=" * 80)

    # Detalle de seguridad
    print("\nINTERCEPCIONES DE SEGURIDAD DETECTADAS EN LOS 200 TURNOS:")
    for s in seguridad_interceptada:
        print(f"  [{s['caso']} Turno {s['turno']}] Mensaje: '{s['mensaje']}'")
        print(f"       Decisión: {s['decision']}")

    resumen_json = {
        "total_turnos": total_turnos,
        "total_casos": len(resultados_casos),
        "retencion_promedio_memoria": round(retencion_promedio, 4),
        "intercepciones_seguridad": len(seguridad_interceptada),
        "detalle_seguridad": seguridad_interceptada,
        "latencia_promedio_ms": round(lat_prom, 2),
        "latencia_p95_ms": round(lat_p95, 2),
        "casos": [
            {
                "id": r["id"],
                "titulo": r["titulo"],
                "memoria": r["memoria"],
            }
            for r in resultados_casos
        ],
    }

    out_path = Path("tests/auditoria_profunda/metricas_200_turnos_nuevos.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resumen_json, f, indent=2, ensure_ascii=False)

    print(f"\nMétricas guardadas en {out_path}")


if __name__ == "__main__":
    asyncio.run(ejecutar_200_turnos())
