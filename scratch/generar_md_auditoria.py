"""
Generador de Reporte Markdown de Auditoría Científica de 50 Casos vs Ground Truth.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / "docs" / "graficas" / "reporte_auditoria_50_casos_ground_truth.json", "r", encoding="utf-8") as f:
    data = json.load(f)

m = data["metricas_globales"]
casos = data["detalle_por_caso"]

md = []
md.append("# Auditoría Científica: Comparación de 50 Casos de Taller vs. Ground Truth Establecido")
md.append("\n**Fase:** Fase 7 - Validación Empírica sin Reentrenamiento ni Recalibración (Modelo Congelado)")
md.append("**Metodología:** Doble ciego a priori contra estándar oro de taller mecánico automotriz")
md.append("**Principio:** No considerar 'respuesta generada' como 'respuesta correcta'.\n")

md.append("## 1. Métricas Globales Consolidadas\n")
md.append("| Métrica de Evaluación | Valor Numérico | Casos / Total | Interpretación Metodológica |")
md.append("|---|:---:|:---:|---|")
md.append(f"| **Top-1 ML Accuracy (Estricto)** | **{m['top1_ml_accuracy_pct']:.2f}%** | {m['top1_ml_conteo']}/50 | Coincidencia unívoca del clasificador Linear SVM con la falla raíz. |")
md.append(f"| **Top-3 ML Accuracy (Diferencial)** | **{m['top3_ml_accuracy_pct']:.2f}%** | {m['top3_ml_conteo']}/50 | Falla raíz capturada dentro de la terna diferencial de mayor probabilidad. |")
md.append(f"| **Accuracy Diagnóstico Final E2E (Estricto)** | **{m['e2e_diagnostico_final_estricto_pct']:.2f}%** | {m['e2e_diagnostico_final_estricto_conteo']}/50 | Hipótesis primaria final reportada al mecánico coincide estrictamente con Ground Truth. |")
md.append(f"| **Accuracy Diagnóstico Final E2E (Global con Diferencial)** | **{m['e2e_diagnostico_final_global_pct']:.2f}%** | {m['e2e_diagnostico_final_estricto_conteo'] + m['e2e_diagnostico_final_diferencial_conteo']}/50 | Diagnóstico final ubica la falla esperada como primaria (64%) o diferencial válida (26%). |")
md.append(f"| **Casos Incorrectos E2E** | **{(m['e2e_diagnostico_final_incorrecto_conteo']/50)*100:.2f}%** | {m['e2e_diagnostico_final_incorrecto_conteo']}/50 | Casos no resueltos por ambigüedad crítica, fallo en 2do turno o descarte. |")
md.append(f"| **Exactitud de Macro-Sistema** | **{m['macro_sistema_accuracy_pct']:.2f}%** | {m['macro_sistema_conteo']}/50 | Clasificación correcta en Motor, Frenos, Transmisión, Suspensión/Chasis, Eléctrico. |")
md.append(f"| **Efectividad del Auto-Interrogador** | **{m['auto_interrogador_efectividad_pct']:.2f}%** | {m['auto_interrogador_requerido_activado']}/{m['auto_interrogador_total_requerido']} | Activación apropiada en escenarios con ambigüedad de combustible o síntomas cruzados. |")
md.append(f"| **Respaldo Documental de Tolerancias OEM** | **{m['respaldo_documental_si_pct']:.2f}%** | {int(m['respaldo_documental_si_pct']*50/100)}/50 | Valores de presión, par o voltaje explícitamente fundamentados en manuales OEM FAISS. |\n")

md.append("## 2. Detalle Exhaustivo Caso por Caso (G1_01 a G1_50)\n")
md.append("| ID | Diagnóstico Esperado (Ground Truth) | Top-1 ML | Top-2 / Top-3 ML | Diagnóstico Final E2E | Clasificación | Macro-Sistema | Auto-Interrogador | Evidencia RAG Utilizada | Respaldo Valores |")
md.append("|:---:|---|---|---|---|:---:|:---:|:---:|---|:---:|")

for c in casos:
    top2_3 = f"**2:** {c['top2_ml']}<br>**3:** {c['top3_ml']}"
    rag_doc = c['documento_rag_utilizado'][:50] + "..." if len(c['documento_rag_utilizado']) > 50 else c['documento_rag_utilizado']
    md.append(f"| **{c['id']}** | {c['diagnostico_esperado']} | {c['top1_ml']} | {top2_3} | {c['diagnostico_final_e2e']} | **{c['clasificacion_final_e2e']}** | {c['macro_sistema_correcto']} ({c['macro_sistema_predicho']}) | {c['auto_interrogador_status']} | {rag_doc} | {c['respaldo_documental_valores']} |")

out_path = BASE_DIR / "docs" / "REPORTE_COMPARATIVO_50_CASOS_GROUND_TRUTH.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print(f"Reporte markdown generado exitosamente en: {out_path} ({len(md)} líneas)")
