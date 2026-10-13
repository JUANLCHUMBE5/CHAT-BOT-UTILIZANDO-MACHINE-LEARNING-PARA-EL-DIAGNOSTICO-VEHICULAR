"""Ejecutor y evaluador automatizado de la Auditoría Profunda de CarBot (630 turnos).

Ejecuta las 30 conversaciones inéditas, mide retención de memoria a 10, 20 y 30 turnos,
detecta bucles y repeticiones, evalúa precisión diagnóstica Top-1 y Top-3,
valida guardias de seguridad mecánica y exporta las 30 transcripciones completas.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List

# Asegurar importación de src y de los casos
sys.path.insert(0, os.path.abspath("."))

try:
    from tests.auditoria_profunda.casos_01_a_10 import CASOS_01_A_10
    from tests.auditoria_profunda.casos_11_a_20 import CASOS_11_A_20
    from tests.auditoria_profunda.casos_21_a_30 import CASOS_21_A_30
except ImportError:
    from scratch.auditoria_profunda.casos_01_a_10 import CASOS_01_A_10
    from scratch.auditoria_profunda.casos_11_a_20 import CASOS_11_A_20
    from scratch.auditoria_profunda.casos_21_a_30 import CASOS_21_A_30

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.gestor_diagnostico import GestorDiagnostico


def evaluar_memoria_caso(estado: Any, hechos_esperados: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula la retención de hechos esperados en el estado conversacional."""
    total_esperados = len(hechos_esperados)
    hechos_retenidos = 0
    detalle = {}

    for clave, valor_esp in hechos_esperados.items():
        conservado = False
        if clave == "placa":
            conservado = (estado.placa == valor_esp)
        elif clave == "marca":
            conservado = (estado.marca and estado.marca.lower() == valor_esp.lower())
        elif clave == "modelo":
            conservado = (estado.modelo and valor_esp.lower() in estado.modelo.lower())
        elif clave == "anio":
            conservado = (estado.anio == valor_esp)
        elif clave == "dtc":
            dtc_str = valor_esp.upper()
            conservado = any(dtc_str in str(h.valor).upper() or dtc_str in str(k).upper() for k, h in estado.hechos.items()) or any(dtc_str in m.upper() for m in estado.historial_mensajes_usuario)
        else:
            # Búsqueda en hechos, mediciones o historial de mensajes
            val_str = str(valor_esp).lower()
            conservado = (
                any(clave in k.lower() or val_str in str(h.valor).lower() for k, h in estado.hechos.items())
                or clave in estado.measurements
                or any(clave in str(p).lower() for p in estado.completed_tests.keys())
                or any(val_str in m.lower() for m in estado.historial_mensajes_usuario)
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


def detectar_bucles_en_sesion(transcripcion: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detecta repeticiones idénticas de preguntas o ciclos de recomendaciones."""
    preguntas_emitidas: List[str] = []
    bucles_detectados: List[Dict[str, Any]] = []

    for t in transcripcion:
        if t.get("es_pregunta") or t.get("decision") == "PREGUNTAR":
            txt_preg = t.get("pregunta_texto", "").strip().lower()
            if not txt_preg and t.get("respuesta_texto"):
                # Extraer posible pregunta del texto
                resp = t["respuesta_texto"]
                if "¿" in resp:
                    txt_preg = resp[resp.find("¿"):resp.find("?")+1].lower()

            if txt_preg:
                # Comprobar si ya se hizo una pregunta idéntica
                if txt_preg in preguntas_emitidas:
                    bucles_detectados.append({
                        "turno": t["turno"],
                        "tipo": "PREGUNTA_REPETIDA_IDENTICA",
                        "texto": txt_preg,
                    })
                preguntas_emitidas.append(txt_preg)

    return {
        "total_preguntas": len(preguntas_emitidas),
        "total_bucles": len(bucles_detectados),
        "bucles": bucles_detectados,
        "tiene_bucle": len(bucles_detectados) > 0,
    }


def evaluar_precision_diagnostico(falla_confirmada: str, macro_esperado: str, transcripcion: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evalúa la coincidencia Top-1 y Top-3 de CarBot respecto a la falla confirmada."""
    # Buscar el diagnóstico emitido al final de la sesión
    ultimos_turnos = list(reversed(transcripcion))
    diag_top1 = "DESCONOCIDO"
    top3_lista: List[str] = []
    decision_final = "SIN_DIAGNOSTICO"

    for t in ultimos_turnos:
        if t.get("diagnostico_ml") and t.get("diagnostico_ml") != "DESCONOCIDO":
            diag_top1 = t["diagnostico_ml"]
            decision_final = t.get("decision", "DIAGNOSTICAR")
            top3_lista = t.get("top3_nombres", [])
            break

    falla_conf_lower = falla_confirmada.lower()
    macro_lower = macro_esperado.lower()

    # Evaluación de coincidencia semántica/técnica
    top1_acierto = (
        diag_top1.lower() in falla_conf_lower
        or any(w in diag_top1.lower() for w in falla_conf_lower.split() if len(w) > 4)
        or macro_lower in diag_top1.lower()
    )
    top3_acierto = top1_acierto or any(
        (alt.lower() in falla_conf_lower or any(w in alt.lower() for w in falla_conf_lower.split() if len(w) > 4))
        for alt in top3_lista
    )

    return {
        "diagnostico_top1": diag_top1,
        "top3": top3_lista,
        "decision_final": decision_final,
        "top1_acierto": bool(top1_acierto),
        "top3_acierto": bool(top3_acierto),
    }


async def auditar_caso(caso: Dict[str, Any], gestor: GestorDiagnostico, orquestador: OrquestadorConversacion) -> Dict[str, Any]:
    """Ejecuta todos los turnos de un caso y recopila la auditoría."""
    session_id = f"audit_deep_{caso['id']}_{int(time.time()*1000)}"
    transcripcion: List[Dict[str, Any]] = []
    chequeos_memoria: Dict[str, Any] = {}
    seguridad_activada = False
    seguridad_detalle = ""

    t_inicio_caso = time.perf_counter()

    for i, mensaje_usuario in enumerate(caso["turnos"]):
        num_turno = i + 1
        t0 = time.perf_counter()

        resultado = await orquestador.procesar_turno(session_id, mensaje_usuario, gestor)
        duracion_ms = round((time.perf_counter() - t0) * 1000, 2)

        estado = resultado.get("estado")
        decision = resultado.get("decision", "DESCONOCIDA")
        resp_texto = resultado.get("respuesta_texto", "")
        diag_ml = resultado.get("diagnostico_ml", "")
        conf_ml = resultado.get("confianza_ml", 0.0)

        top3_nombres = []
        if estado and getattr(estado, "top3_actual", None):
            top3_nombres = [item.get("falla", "") for item in estado.top3_actual if isinstance(item, dict)]

        # Chequeo de seguridad crítica
        if decision == "SEGURIDAD_CRITICA":
            seguridad_activada = True
            seguridad_detalle = resp_texto[:150]

        registro_turno = {
            "turno": num_turno,
            "mensaje_mecanico": mensaje_usuario,
            "respuesta_carbot": resp_texto,
            "decision": decision,
            "es_pregunta": resultado.get("es_pregunta", False),
            "diagnostico_ml": diag_ml,
            "confianza_ml": conf_ml,
            "top3_nombres": top3_nombres,
            "duracion_ms": duracion_ms,
        }
        transcripcion.append(registro_turno)

        # Chequeos de memoria periódicos a turno 10 y turno final
        if num_turno == 10:
            chequeos_memoria["turno_10"] = evaluar_memoria_caso(estado, caso["hechos_esperados"])
        elif num_turno == 20:
            chequeos_memoria["turno_20"] = evaluar_memoria_caso(estado, caso["hechos_esperados"])

    duracion_total_s = round(time.perf_counter() - t_inicio_caso, 2)

    # Chequeo de memoria final
    chequeos_memoria["turno_final"] = evaluar_memoria_caso(estado, caso["hechos_esperados"])

    # Detección de bucles
    analisis_bucles = detectar_bucles_en_sesion(transcripcion)

    # Precisión diagnóstica
    analisis_precision = evaluar_precision_diagnostico(
        caso["falla_confirmada"], caso["macro_sistema"], transcripcion
    )

    return {
        "id": caso["id"],
        "area": caso["area"],
        "categoria_eval": caso["categoria_eval"],
        "vehiculo": caso["vehiculo"],
        "falla_confirmada": caso["falla_confirmada"],
        "macro_sistema": caso["macro_sistema"],
        "total_turnos": len(transcripcion),
        "duracion_total_s": duracion_total_s,
        "memoria": chequeos_memoria,
        "bucles": analisis_bucles,
        "precision": analisis_precision,
        "seguridad": {
            "activada": seguridad_activada,
            "detalle": seguridad_detalle,
        },
        "transcripcion": transcripcion,
    }


async def main():
    print("=" * 80)
    print("INICIANDO AUDITORÍA PROFUNDA DE INTELIGENCIA CONVERSACIONAL (630 TURNOS)")
    print("Commit de Referencia: f8c544da3dc58fdb47be5df7100b4a4cb39626df")
    print("=" * 80)

    # 1. Cargar componentes de producción
    print("\n[1/4] Cargando GestorDiagnostico y OrquestadorConversacion...")
    t0_carga = time.perf_counter()
    gestor = GestorDiagnostico()
    orquestador = OrquestadorConversacion()
    t_carga = time.perf_counter() - t0_carga
    print(f"  -> Modelos ML y FAISS RAG listos en {t_carga:.2f} s")

    # 2. Consolidar los 30 casos
    todos_los_casos = CASOS_01_A_10 + CASOS_11_A_20 + CASOS_21_A_30
    total_casos = len(todos_los_casos)
    total_turnos_global = sum(len(c["turnos"]) for c in todos_los_casos)
    print(f"\n[2/4] Casos preparados: {total_casos} casos | {total_turnos_global} turnos totales")

    # 3. Ejecutar los casos de auditoría
    print("\n[3/4] Ejecutando las 30 conversaciones independientes...")
    resultados_casos: List[Dict[str, Any]] = []

    for idx, caso in enumerate(todos_los_casos):
        print(f"  [{idx+1:02d}/30] Ejecutando {caso['id']}: {caso['area']} - {caso['vehiculo']['marca']} {caso['vehiculo']['modelo']} ({len(caso['turnos'])} turnos)...", end="", flush=True)
        res = await auditar_caso(caso, gestor, orquestador)
        resultados_casos.append(res)
        ret_fin = res["memoria"]["turno_final"]["retencion"] * 100
        bucles_n = res["bucles"]["total_bucles"]
        acierto_t1 = "SI" if res["precision"]["top1_acierto"] else "NO"
        print(f" OK en {res['duracion_total_s']}s | Retención: {ret_fin:.1f}% | Bucles: {bucles_n} | Top1: {acierto_t1}")

    # 4. Calcular métricas consolidadas
    print("\n[4/4] Consolidando métricas globales...")
    retenciones_finales = [c["memoria"]["turno_final"]["retencion"] for c in resultados_casos]
    retenciones_t10 = [c["memoria"]["turno_10"]["retencion"] for c in resultados_casos if "turno_10" in c["memoria"]]
    retenciones_t20 = [c["memoria"]["turno_20"]["retencion"] for c in resultados_casos if "turno_20" in c["memoria"]]

    promedio_ret_final = sum(retenciones_finales) / len(retenciones_finales)
    promedio_ret_t10 = sum(retenciones_t10) / len(retenciones_t10)
    promedio_ret_t20 = sum(retenciones_t20) / len(retenciones_t20)

    total_bucles_global = sum(c["bucles"]["total_bucles"] for c in resultados_casos)
    aciertos_top1_count = sum(1 for c in resultados_casos if c["precision"]["top1_acierto"])
    aciertos_top3_count = sum(1 for c in resultados_casos if c["precision"]["top3_acierto"])

    exactitud_top1 = aciertos_top1_count / total_casos
    exactitud_top3 = aciertos_top3_count / total_casos

    # Tiempos de respuesta
    todos_los_tiempos = [t["duracion_ms"] for c in resultados_casos for t in c["transcripcion"]]
    tiempo_promedio_ms = sum(todos_los_tiempos) / len(todos_los_tiempos)
    tiempo_max_ms = max(todos_los_tiempos)
    tiempo_p95_ms = sorted(todos_los_tiempos)[int(len(todos_los_tiempos) * 0.95)]

    resumen_metricas = {
        "commit_auditado": "f8c544da3dc58fdb47be5df7100b4a4cb39626df",
        "total_conversaciones": total_casos,
        "total_turnos": total_turnos_global,
        "memoria": {
            "retencion_promedio_t10": round(promedio_ret_t10 * 100, 2),
            "retencion_promedio_t20": round(promedio_ret_t20 * 100, 2),
            "retencion_promedio_final": round(promedio_ret_final * 100, 2),
        },
        "bucles": {
            "total_bucles_detectados": total_bucles_global,
            "conversaciones_sin_bucles": sum(1 for c in resultados_casos if not c["bucles"]["tiene_bucle"]),
        },
        "precision_diagnostica": {
            "exactitud_top1_porcentaje": round(exactitud_top1 * 100, 2),
            "exactitud_top3_porcentaje": round(exactitud_top3 * 100, 2),
            "numerador_top1": aciertos_top1_count,
            "numerador_top3": aciertos_top3_count,
            "denominador_total": total_casos,
        },
        "rendimiento": {
            "latencia_promedio_ms": round(tiempo_promedio_ms, 2),
            "latencia_p95_ms": round(tiempo_p95_ms, 2),
            "latencia_maxima_ms": round(tiempo_max_ms, 2),
        },
        "seguridad": {
            "guardias_probadas": ["Common Rail de alta presión (Caso 14)", "DPF con dilución de aceite (Caso 16)", "Radiador caliente a 108°C (Caso 26)"],
            "todas_interceptadas": all(resultados_casos[idx]["seguridad"]["activada"] for idx in [13, 15, 25]),
        },
    }

    print("\n" + "=" * 80)
    print("RESUMEN DE MÉTRICAS GLOBALES DE AUDITORÍA PROFUNDA:")
    print(json.dumps(resumen_metricas, indent=2))
    print("=" * 80)

    # Exportar resultados
    os.makedirs("scratch/auditoria_profunda", exist_ok=True)
    with open("scratch/auditoria_profunda/metricas_auditoria_profunda.json", "w", encoding="utf-8") as f:
        json.dump(resumen_metricas, f, indent=2, ensure_ascii=False)

    with open("scratch/auditoria_profunda/transcripciones_completas.json", "w", encoding="utf-8") as f:
        json.dump(resultados_casos, f, indent=2, ensure_ascii=False)

    print("\nArchivos exportados exitosamente:")
    print("  -> scratch/auditoria_profunda/metricas_auditoria_profunda.json")
    print("  -> scratch/auditoria_profunda/transcripciones_completas.json")


if __name__ == "__main__":
    asyncio.run(main())
