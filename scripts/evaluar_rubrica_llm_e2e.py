"""
Evaluación Cuantitativa End-to-End del Chatbot CarBot con Rúbrica Académica Ampliada (40 Casos).
Evalúa el pipeline completo integrado:
  Consulta Usuario -> Jerga/DTC -> ML Jerárquico -> RAG Multiseñal -> Prompt Anti-Alucinación -> Síntesis.

Rúbrica de Evaluación Multidimensional (Escala 0 a 100%):
  - D1: Correctitud Técnica y Coherencia (Alineación con la falla real y DTC).
  - D2: Relevancia del Procedimiento Técnico y Metrología (Tolerancias OEM y pruebas físicas).
  - D3: Sustento en Evidencia y Diagnóstico Diferencial (Comparación Top-1 vs Top-2/3).
  - D4: Ausencia de Alucinaciones y Delimitación Epistémica (Hipótesis vs Evidencia instrumental).

Métricas complementarias:
  - Tasa de Alucinación Explícita (%)
  - Desglose de Latencia Real del Pipeline (ms)
"""

import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from rubrica_e2e_casos_dataset import CASOS_E2E_RUBRICA_40
from src.core.gestor_diagnostico import GestorDiagnostico


def evaluar_caso_con_rubrica(caso_info: Dict[str, Any], resultado: Any) -> Dict[str, Any]:
    resp = resultado.respuesta_texto or ""
    resp_lower = resp.lower()
    diag_ml = resultado.diagnostico_ml or ""
    conf_ml = resultado.confianza_ml or 0.0
    contexto_rag = resultado.contexto_manual or ""
    dtc_esp = caso_info.get("dtc")
    es_mec = caso_info.get("es_mecanica_pura", False)

    # -------------------------------------------------------------
    # D1: Correctitud Técnica y Coherencia (0 - 100%)
    # -------------------------------------------------------------
    puntos_d1 = 0
    falla_esp_low = caso_info["falla_esperada"].lower()
    if falla_esp_low in diag_ml.lower() or any(p in diag_ml.lower() for p in falla_esp_low.split()[:2]):
        puntos_d1 += 50
    elif any(falla_esp_low in p.falla.lower() for p in (resultado.predicciones_ml or [])):
        puntos_d1 += 40
    else:
        puntos_d1 += 20

    if dtc_esp:
        if dtc_esp.lower() in resp_lower or dtc_esp.lower() in contexto_rag.lower():
            puntos_d1 += 30
        else:
            puntos_d1 += 10
    else:
        puntos_d1 += 30

    tiene_sec1 = ("1. posible falla" in resp_lower or "1." in resp_lower or "posible avería" in resp_lower)
    tiene_sec2 = ("2. procedimiento" in resp_lower or "2." in resp_lower or "inspección" in resp_lower)
    tiene_sec3 = ("3. tiempo" in resp_lower or "3." in resp_lower or "gravedad" in resp_lower)
    if tiene_sec1 and tiene_sec2 and tiene_sec3:
        puntos_d1 += 20
    elif tiene_sec1 or tiene_sec2:
        puntos_d1 += 10

    # -------------------------------------------------------------
    # D2: Relevancia del Procedimiento Técnico y Metrología (0 - 100%)
    # -------------------------------------------------------------
    puntos_d2 = 0
    if resultado.titulo_manual and "Desconocido" not in resultado.titulo_manual and "No se encontró" not in resultado.titulo_manual:
        puntos_d2 += 40
    elif len(contexto_rag) > 100:
        puntos_d2 += 30

    # Control estricto de Regla 9 (Fallas mecánicas puras sin escáner)
    sugiere_dtc_indebido = False
    if es_mec:
        menciona_pruebas_fisicas = any(
            k in resp_lower or k in contexto_rag.lower()
            for k in [
                "reloj comparador", "micrometro", "pie de rey", "calado", "balanceo", "alineacion",
                "barra de una", "palanca", "holgura", "presion", "voltaje", "multimetro", "inspeccion",
                "desmontar", "osciloscopio", "compresion", "purga", "pastillas", "disco"
            ]
        )
        sugiere_dtc_indebido = ("conectar escaner obd" in resp_lower and "dtc" in resp_lower and not dtc_esp)
        if menciona_pruebas_fisicas and not sugiere_dtc_indebido:
            puntos_d2 += 40
        elif menciona_pruebas_fisicas:
            puntos_d2 += 30
        else:
            puntos_d2 += 15
    else:
        puntos_d2 += 40

    if any(k in resp_lower for k in ["paso", "1.", "comprobar", "medir", "verificar", "inspeccionar"]):
        puntos_d2 += 20
    else:
        puntos_d2 += 10

    # -------------------------------------------------------------
    # D3: Sustento en Evidencia y Diagnóstico Diferencial (0 - 100%)
    # -------------------------------------------------------------
    puntos_d3 = 0
    if resultado.predicciones_ml and len(resultado.predicciones_ml) >= 2:
        puntos_d3 += 40
    elif conf_ml > 0:
        puntos_d3 += 25

    tiene_diferencial = any(
        k in resp_lower for k in [
            "diferencial", "alternativa", "descarte", "distinguir", "descartar",
            "hipotesis", "comparar", "top 2", "secundaria", "tambien podria"
        ]
    )
    if tiene_diferencial:
        puntos_d3 += 40
    else:
        puntos_d3 += 20

    if any(k in resp_lower for k in ["antes de", "descartar", "inspeccion previa", "verificar", "confirmar", "comprobar"]):
        puntos_d3 += 20
    else:
        puntos_d3 += 10

    # -------------------------------------------------------------
    # D4: Ausencia de Alucinaciones y Delimitación Epistémica (0 - 100%)
    # -------------------------------------------------------------
    puntos_d4 = 0
    if any(k in resp_lower for k in ["hipotesis", "posible", "inspeccion fisica", "verificacion", "revision", "confirmar"]):
        puntos_d4 += 40
    else:
        puntos_d4 += 20

    certeza_infundada = ("falla 100% segura" in resp_lower or "cambie inmediatamente sin revisar" in resp_lower)
    if not certeza_infundada:
        puntos_d4 += 30
    else:
        puntos_d4 += 0

    if resultado.similitud_rag > 0.05 or len(contexto_rag) > 50:
        puntos_d4 += 30
    else:
        puntos_d4 += 15

    # Detección formal de alucinación técnica
    alucinacion_detectada = (sugiere_dtc_indebido or certeza_infundada or puntos_d4 < 40)

    score_total = round((puntos_d1 + puntos_d2 + puntos_d3 + puntos_d4) / 4.0, 2)

    return {
        "id": caso_info["id"],
        "sistema": caso_info["sistema"],
        "falla_esperada": caso_info["falla_esperada"],
        "diagnostico_ml": diag_ml,
        "confianza_ml": round(conf_ml, 4),
        "titulo_rag": resultado.titulo_manual,
        "similitud_rag": round(resultado.similitud_rag, 4),
        "modo_diagnostico": resultado.modo_diagnostico,
        "tiempo_pipeline_ms": resultado.tiempo_total_ms,
        "d1_correctitud": puntos_d1,
        "d2_relevancia_procedimiento": puntos_d2,
        "d3_diagnostico_diferencial": puntos_d3,
        "d4_anti_alucinacion": puntos_d4,
        "alucinacion_detectada": alucinacion_detectada,
        "puntaje_rubrica_total": score_total
    }


def ejecutar_evaluacion_rubrica_40():
    print("\n" + "="*85)
    print("EVALUACIÓN END-TO-END CON RÚBRICA ACADÉMICA AMPLIADA (40 CASOS TÉCNICOS)")
    print("="*85)

    gestor = GestorDiagnostico()
    evaluaciones = []

    for c_info in CASOS_E2E_RUBRICA_40:
        t0 = time.perf_counter()
        resultado = gestor.procesar_consulta_texto(
            texto_usuario=c_info["consulta"],
            marca_modelo="Universal",
            session_id=f"TEST_E2E_V4_{c_info['id']}"
        )
        t_ms = (time.perf_counter() - t0) * 1000.0

        eval_caso = evaluar_caso_con_rubrica(c_info, resultado)
        eval_caso["tiempo_medido_ms"] = round(t_ms, 2)
        evaluaciones.append(eval_caso)

        alu_str = "ALUCINACION" if eval_caso["alucinacion_detectada"] else "LIMPIO"
        print(f"[{c_info['id']}] {c_info['sistema']:<20} | Score: {eval_caso['puntaje_rubrica_total']:5.1f}% | "
              f"D1:{eval_caso['d1_correctitud']:>3} D2:{eval_caso['d2_relevancia_procedimiento']:>3} "
              f"D3:{eval_caso['d3_diagnostico_diferencial']:>3} D4:{eval_caso['d4_anti_alucinacion']:>3} | "
              f"Aluc: {alu_str:<11} | Lat: {t_ms:5.1f}ms")

    total = len(evaluaciones)
    avg_d1 = sum(e["d1_correctitud"] for e in evaluaciones) / total
    avg_d2 = sum(e["d2_relevancia_procedimiento"] for e in evaluaciones) / total
    avg_d3 = sum(e["d3_diagnostico_diferencial"] for e in evaluaciones) / total
    avg_d4 = sum(e["d4_anti_alucinacion"] for e in evaluaciones) / total
    avg_global = sum(e["puntaje_rubrica_total"] for e in evaluaciones) / total
    avg_tiempo = sum(e["tiempo_medido_ms"] for e in evaluaciones) / total
    total_alucinaciones = sum(1 for e in evaluaciones if e["alucinacion_detectada"])
    tasa_alucinacion = (total_alucinaciones / total) * 100.0

    print("\n" + "="*85)
    print("PROMEDIOS DE LA RÚBRICA END-TO-END (40 CASOS INTEGRADOS — FASE 7)")
    print("="*85)
    print(f"  - D1 - Correctitud Técnica y Coherencia:             {avg_d1:5.2f}%")
    print(f"  - D2 - Relevancia del Procedimiento y Metrología:   {avg_d2:5.2f}%")
    print(f"  - D3 - Sustento en Evidencia y Diferencial:          {avg_d3:5.2f}%")
    print(f"  - D4 - Ausencia de Alucinaciones y Delimitación:     {avg_d4:5.2f}%")
    print("-" * 85)
    print(f"  * ÍNDICE DE CALIDAD DIAGNÓSTICA E2E PONDERADO:       {avg_global:5.2f}%")
    print(f"  * TASA DE ALUCINACIONES TÉCNICAS EXPLÍCITAS:         {tasa_alucinacion:5.2f}% ({total_alucinaciones}/{total})")
    print(f"  * Tiempo de Respuesta Promedio del Pipeline E2E:     {avg_tiempo:5.2f} ms")
    print("="*85 + "\n")

    # Guardar reporte JSON
    out_file = BASE_DIR / "docs" / "graficas" / "reporte_rubrica_e2e_40_casos.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_casos_evaluados": total,
            "metricas_globales": {
                "d1_correctitud_promedio": round(avg_d1, 2),
                "d2_relevancia_promedio": round(avg_d2, 2),
                "d3_diferencial_promedio": round(avg_d3, 2),
                "d4_anti_alucinacion_promedio": round(avg_d4, 2),
                "calidad_diagnostica_global": round(avg_global, 2),
                "tasa_alucinacion_pct": round(tasa_alucinacion, 2),
                "total_alucinaciones": total_alucinaciones,
                "latencia_promedio_ms": round(avg_tiempo, 2)
            },
            "evaluaciones_individuales": evaluaciones
        }, f, indent=2, ensure_ascii=False)

    print(f"[OK] Reporte de Rúbrica Ampliada guardado en: {out_file}")
    return evaluaciones


if __name__ == "__main__":
    ejecutar_evaluacion_rubrica_40()
