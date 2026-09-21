"""
Actualización de los artefactos oficiales con los resultados de la reauditoría estricta.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Importar la lista de los 50 casos del script riguroso
from scratch.reauditar_50_riguroso import AUDITORIA_CASOS

total = len(AUDITORIA_CASOS)
assert total == 50

conteo_top1 = sum(1 for c in AUDITORIA_CASOS if c["eval_top1"] == "SÍ")
conteo_top3 = sum(1 for c in AUDITORIA_CASOS if c["eval_top3"] == "SÍ")
conteo_final_correcto = sum(1 for c in AUDITORIA_CASOS if c["eval_final"] == "CORRECTO")
conteo_final_diferencial = sum(1 for c in AUDITORIA_CASOS if c["eval_final"] == "DIFERENCIAL ACEPTABLE")
conteo_final_incorrecto = sum(1 for c in AUDITORIA_CASOS if c["eval_final"] == "INCORRECTO")
conteo_macro_ok = sum(1 for c in AUDITORIA_CASOS if c["macro_ok"] == "SÍ")

casos_requiere_inter = [c for c in AUDITORIA_CASOS if c["requiere_interrogador"]]
total_requiere_inter = len(casos_requiere_inter)
conteo_interrogador_exito = sum(1 for c in casos_requiere_inter if "SÍ" in c["interrogador_eval"])

conteo_respaldo_si = sum(1 for c in AUDITORIA_CASOS if c["valores_respaldo"] == "SÍ")
conteo_respaldo_parcial = sum(1 for c in AUDITORIA_CASOS if c["valores_respaldo"] == "PARCIAL")
conteo_respaldo_no = sum(1 for c in AUDITORIA_CASOS if c["valores_respaldo"] == "NO")

# 1. Guardar JSON oficial
resumen_json = {
    "metricas_globales": {
        "total_casos_auditados": 50,
        "top1_ml_accuracy_pct": round(conteo_top1 / total * 100, 2),
        "top1_ml_conteo": conteo_top1,
        "top3_ml_accuracy_pct": round(conteo_top3 / total * 100, 2),
        "top3_ml_conteo": conteo_top3,
        "e2e_diagnostico_final_estricto_pct": round(conteo_final_correcto / total * 100, 2),
        "e2e_diagnostico_final_estricto_conteo": conteo_final_correcto,
        "e2e_diagnostico_final_diferencial_pct": round(conteo_final_diferencial / total * 100, 2),
        "e2e_diagnostico_final_diferencial_conteo": conteo_final_diferencial,
        "e2e_diagnostico_final_incorrecto_pct": round(conteo_final_incorrecto / total * 100, 2),
        "e2e_diagnostico_final_incorrecto_conteo": conteo_final_incorrecto,
        "e2e_diagnostico_final_global_pct": round((conteo_final_correcto + conteo_final_diferencial) / total * 100, 2),
        "macro_sistema_accuracy_pct": round(conteo_macro_ok / total * 100, 2),
        "macro_sistema_conteo": conteo_macro_ok,
        "auto_interrogador_efectividad_requerida_pct": round(conteo_interrogador_exito / total_requiere_inter * 100, 2),
        "auto_interrogador_conteo_exito": conteo_interrogador_exito,
        "auto_interrogador_total_requerido": total_requiere_inter,
        "respaldo_documental_si_pct": round(conteo_respaldo_si / total * 100, 2),
        "respaldo_documental_si_conteo": conteo_respaldo_si,
        "respaldo_documental_parcial_pct": round(conteo_respaldo_parcial / total * 100, 2),
        "respaldo_documental_parcial_conteo": conteo_respaldo_parcial,
        "respaldo_documental_no_pct": round(conteo_respaldo_no / total * 100, 2),
        "respaldo_documental_no_conteo": conteo_respaldo_no,
    },
    "detalle_por_caso": AUDITORIA_CASOS
}

json_path = BASE_DIR / "docs" / "graficas" / "reporte_auditoria_50_casos_ground_truth.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(resumen_json, f, indent=2, ensure_ascii=False)

# 2. Generar Markdown oficial
with open("docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)
casos_raw = {c["id"]: c for c in raw_data["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"}

lines = []
lines.append("# Reauditoría Científica Estricta: 50 Casos de Taller vs. Ground Truth Original")
lines.append("\n**Fase:** Fase 7 - Validación Empírica sin Reentrenamiento, sin Recalibración y sin Modificación del Pipeline (Modelo Congelado)")
lines.append("**Principio Académico Innegociable:** Criterio estricto de coincidencia diagnóstica; no considerar 'respuesta generada' como 'respuesta correcta'. No convertir fallas del mismo macro-sistema en diferencial aceptable automáticamente.\n")

lines.append("## 1. Métricas Globales Consolidadas (Recálculo Riguroso desde Cero)\n")
lines.append("| Métrica de Evaluación | Exactitud (%) | Numerador / Denominador | Definición y Criterio Estricto |")
lines.append("|---|:---:|:---:|---|")
lines.append(f"| **Top-1 ML Accuracy** | **{conteo_top1/total*100:.2f}%** | **{conteo_top1} / 50** | Coincidencia unívoca de la predicción primaria del clasificador Linear SVM con la falla esperada. |")
lines.append(f"| **Top-3 ML Accuracy** | **{conteo_top3/total*100:.2f}%** | **{conteo_top3} / 50** | La falla esperada figura explícitamente en la terna de probabilidades (Top-1, Top-2 o Top-3). |")
lines.append(f"| **Diagnóstico Final E2E: Correcto Estricto** | **{conteo_final_correcto/total*100:.2f}%** | **{conteo_final_correcto} / 50** | La hipótesis principal final reportada al mecánico coincide exactamente con la causa raíz real. |")
lines.append(f"| **Diagnóstico Final E2E: Diferencial Aceptable** | **{conteo_final_diferencial/total*100:.2f}%** | **{conteo_final_diferencial} / 50** | La hipótesis primaria difirió, pero la causa esperada aparece explícitamente en Top-2/Top-3 o diagnóstico diferencial y es técnicamente compatible. |")
lines.append(f"| **Diagnóstico Final E2E: Incorrecto** | **{conteo_final_incorrecto/total*100:.2f}%** | **{conteo_final_incorrecto} / 50** | La causa esperada no aparece ni como hipótesis principal ni como diferencial técnico válido. |")
lines.append(f"| **Exactitud Global E2E (Correcto + Diferencial)** | **{(conteo_final_correcto+conteo_final_diferencial)/total*100:.2f}%** | **{conteo_final_correcto+conteo_final_diferencial} / 50** | Suma exacta de Correcto Estricto ({conteo_final_correcto}) + Diferencial Aceptable ({conteo_final_diferencial}). |")
lines.append(f"| **Exactitud de Macro-Sistema** | **{conteo_macro_ok/total*100:.2f}%** | **{conteo_macro_ok} / 50** | Clasificación correcta en Motor, Frenos, Transmisión, Suspensión/Chasis, Eléctrico, Neumática. |")
lines.append(f"| **Efectividad Auto-Interrogador (Casos Requeridos)** | **{conteo_interrogador_exito/total_requiere_inter*100:.2f}%** | **{conteo_interrogador_exito} / {total_requiere_inter}** | Activación exitosa en los 7 escenarios con ambigüedad crítica (combustible dual, EVAP, síntomas térmicos y tren delantero difuso). |")
lines.append(f"| **Respaldo Documental de Tolerancias OEM** | **{conteo_respaldo_si/total*100:.2f}%** | **{conteo_respaldo_si} / 50** | Valores cuantitativos citados estrictamente respaldados en manuales de taller OEM (8% adicional cuenta con respaldo parcial). |\n")

lines.append("## 2. Detalle Exhaustivo Caso por Caso (G1_01 a G1_50)\n")
lines.append("| ID | Diagnóstico Esperado (Ground Truth) | Top-1 ML | Top-2 / Top-3 ML | Diagnóstico Final E2E | Clasificación | Macro-Sistema | Auto-Interrogador | Evidencia RAG Utilizada | Respaldo Valores |")
lines.append("|:---:|---|---|---|---|:---:|:---:|:---:|---|:---:|")

for c in AUDITORIA_CASOS:
    cid = c["id"]
    raw = casos_raw[cid]
    preds = raw.get("predicciones_ml", [])
    top1_str = f"{raw.get('diagnostico_ml')} ({raw.get('confianza_ml', 0)*100:.1f}%)" if not raw.get('es_interactivo') else f"Clarificación interactiva ({raw.get('confianza_ml', 0)*100:.1f}%)"
    top2_str = preds[1]["falla"] if len(preds) > 1 else "N/A"
    top3_str = preds[2]["falla"] if len(preds) > 2 else "N/A"
    top2_3 = f"**2:** {top2_str}<br>**3:** {top3_str}"
    
    if raw.get("es_interactivo") and "interaccion_turno2" in raw:
        diag_final = raw["interaccion_turno2"]["diagnostico_final"]
    else:
        diag_final = raw.get("diagnostico_ml")
        
    rag_doc = c["rag_doc"]
    
    lines.append(f"| **{cid}** | {c['gt']} | {top1_str} | {top2_3} | {diag_final} | **{c['eval_final']}** | {c['macro_ok']} ({raw.get('macro_sistema')}) | {c['interrogador_eval']} | {rag_doc} | {c['valores_respaldo']} |")

md_path = BASE_DIR / "docs" / "REPORTE_COMPARATIVO_50_CASOS_GROUND_TRUTH.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Artefactos oficiales actualizados con éxito:")
print(f"- {json_path}")
print(f"- {md_path}")
