"""
Actualiza los artefactos finales con la matriz verificada por capas (50 casos).
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / "scratch" / "matriz_50_verificada.json", "r", encoding="utf-8") as f:
    matriz = json.load(f)

t = len(matriz)
s_top1 = sum(c["top1_ok"] for c in matriz)
s_top3 = sum(c["top3_ok"] for c in matriz)
s_e2e_estricto = sum(c["e2e_estricto"] for c in matriz)
s_e2e_dif = sum(c["e2e_dif"] for c in matriz)
s_e2e_inc = t - (s_e2e_estricto + s_e2e_dif)
s_macro = sum(c["macro_ok"] for c in matriz)
s_inter = sum(c["inter_ok"] for c in matriz)

# Guardar JSON oficial
resumen_json = {
    "metricas_globales_por_capa": {
        "total_casos": t,
        "top1_ml_correcto_conteo": s_top1,
        "top1_ml_correcto_pct": round(s_top1 / t * 100, 2),
        "top3_ml_correcto_conteo": s_top3,
        "top3_ml_correcto_pct": round(s_top3 / t * 100, 2),
        "e2e_estricto_conteo": s_e2e_estricto,
        "e2e_estricto_pct": round(s_e2e_estricto / t * 100, 2),
        "e2e_diferencial_conteo": s_e2e_dif,
        "e2e_diferencial_pct": round(s_e2e_dif / t * 100, 2),
        "e2e_incorrecto_conteo": s_e2e_inc,
        "e2e_incorrecto_pct": round(s_e2e_inc / t * 100, 2),
        "e2e_global_conteo": s_e2e_estricto + s_e2e_dif,
        "e2e_global_pct": round((s_e2e_estricto + s_e2e_dif) / t * 100, 2),
        "macro_correcto_conteo": s_macro,
        "macro_correcto_pct": round(s_macro / t * 100, 2),
        "interrogador_correcto_conteo": s_inter,
        "interrogador_correcto_pct": round(s_inter / t * 100, 2)
    },
    "matriz_50_casos": matriz
}

json_path = BASE_DIR / "docs" / "graficas" / "reporte_auditoria_50_casos_ground_truth.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(resumen_json, f, indent=2, ensure_ascii=False)

# Generar Markdown oficial con la matriz final
lines = []
lines.append("# Verificación Aritmética y Metodológica Final: 50 Casos de Taller vs. Ground Truth")
lines.append("\n**Fase:** Fase 7 - Auditoría Científica Independiente por Capas (Pipeline y Modelos 100% Congelados)")
lines.append("**Reglas Metodológicas Estrictas:**")
lines.append("- **Top-1 ML:** Evalúa únicamente la clase predicha en primera posición por el SVM.")
lines.append("- **Top-3 ML:** Evalúa exclusivamente las 3 clases de salida del SVM; RAG, LLM y auto-interrogador no pueden convertir un fallo ML en acierto Top-3.")
lines.append("- **E2E (Estricto / Diferencial / Incorrecto):** Evalúa el diagnóstico final recibido por el mecánico tras ML+DTC+RAG+LLM+Auto-interrogador. RAG puede mejorar E2E, pero nunca Top-3 ML.")
lines.append("- **Macro-Sistema:** Exactitud del macro-dominio vehicular asignado.")
lines.append("- **Auto-Interrogador:** Evalúa la decisión de flujo (activación oportuna en ambigüedad y derivación directa en consultas claras).\n")

lines.append("## 1. Resumen Aritmético Consolidado por Capas (N = 50)\n")
lines.append("| Capa Evaluada | Conteo Exacto | Porcentaje (%) | Criterio Metodológico Estricto |")
lines.append("|---|:---:|:---:|---|")
lines.append(f"| **Top1_ML_correcto** | **{s_top1} / {t}** | **{s_top1/t*100:.2f}%** | Acierto unívoco de la clase Top-1 del Linear SVM con la causa esperada. |")
lines.append(f"| **Top3_ML_correcto** | **{s_top3} / {t}** | **{s_top3/t*100:.2f}%** | Causa esperada presente en las tres clases ML puras (sin auxilio de RAG). |")
lines.append(f"| **E2E_estricto** | **{s_e2e_estricto} / {t}** | **{s_e2e_estricto/t*100:.2f}%** | Hipótesis principal entregada al usuario coincide con la causa esperada. |")
lines.append(f"| **E2E_diferencial** | **{s_e2e_dif} / {t}** | **{s_e2e_dif/t*100:.2f}%** | Causa esperada entregada explícitamente en el diagnóstico diferencial o procedimiento RAG. |")
lines.append(f"| **E2E_incorrecto** | **{s_e2e_inc} / {t}** | **{s_e2e_inc/t*100:.2f}%** | Causa esperada no entregada al usuario o fallo en activación interactiva (G1_50). |")
lines.append(f"| **E2E_global (estricto + diferencial)** | **{s_e2e_estricto + s_e2e_dif} / {t}** | **{(s_e2e_estricto + s_e2e_dif)/t*100:.2f}%** | Tasa total de casos donde el mecánico recibió la hipótesis correcta. |")
lines.append(f"| **macro_correcto** | **{s_macro} / {t}** | **{s_macro/t*100:.2f}%** | Macro-sistema automotriz correctamente identificado. |")
lines.append(f"| **interrogador_correcto** | **{s_inter} / {t}** | **{s_inter/t*100:.2f}%** | Decisión de flujo correcta (activó en ambigüedad / no activó en datos claros). |\n")

lines.append("## 2. Matriz Final Caso por Caso (50 Filas Auditadas)\n")
lines.append("| ID | Causa Esperada (*Ground Truth*) | Top1_ML | Top3_ML | E2E_estricto | E2E_dif | macro | inter | Diagnóstico Final E2E Entregado |")
lines.append("|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|---|")

for c in matriz:
    lines.append(f"| **{c['id']}** | {c['gt']} | {c['top1_ok']} | {c['top3_ok']} | {c['e2e_estricto']} | {c['e2e_dif']} | {c['macro_ok']} | {c['inter_ok']} | {c['literal_e2e']} |")

lines.append("\n**Suma Total de Verificación Aritmética:**")
lines.append(f"- `Top1_ML_correcto`: {s_top1} / {t}")
lines.append(f"- `Top3_ML_correcto`: {s_top3} / {t}")
lines.append(f"- `E2E_estricto`: {s_e2e_estricto} / {t}")
lines.append(f"- `E2E_diferencial`: {s_e2e_dif} / {t}")
lines.append(f"- `E2E_incorrecto`: {s_e2e_inc} / {t} (Comprobación: {s_e2e_estricto} + {s_e2e_dif} + {s_e2e_inc} = {t})")
lines.append(f"- `macro_correcto`: {s_macro} / {t}")
lines.append(f"- `interrogador_correcto`: {s_inter} / {t}")

md_path = BASE_DIR / "docs" / "REPORTE_COMPARATIVO_50_CASOS_GROUND_TRUTH.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Artefactos finales actualizados:")
print(f"- {json_path}")
print(f"- {md_path}")
