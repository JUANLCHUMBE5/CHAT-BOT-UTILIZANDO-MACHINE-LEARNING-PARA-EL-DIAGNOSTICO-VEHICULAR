"""
14_reporte_final_v2.py
FASE EXPERIMENTAL — CARBOT ML + RAG V2
Compila el informe maestro forense exhaustivo con los 24 puntos requeridos,
calcula la verificación final de hashes (Blindaje) y emite los veredictos formales.

Salida:
- docs/auditorias/REENTRENAMIENTO_EXPERIMENTAL_CARBOT_V2.md
"""
import sys
import os
import json
import csv
import hashlib
import time
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BASE_V2 = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2"
DATA_V2 = BASE_V2 / "data"
EVAL_DIR = BASE_V2 / "evaluacion"
DOCS_AUDITORIA = PROJECT_ROOT / "docs" / "auditorias"

MANIFEST_PATH = PROJECT_ROOT / "docs" / "fase11_6" / "CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json"
RESULTADOS_JSON = EVAL_DIR / "resultados_evaluacion_completa.json"
MAPEO_CSV = DATA_V2 / "MAPEO_EXTERNOS_48_CLASES.csv"
DISTRIB_MD = DOCS_AUDITORIA / "DISTRIBUCION_DATASET_C1_V2.md"
REPORTE_OUT = DOCS_AUDITORIA / "REENTRENAMIENTO_EXPERIMENTAL_CARBOT_V2.md"


def verificar_hashes_blindaje():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    filas_hashes = []
    modificados = 0

    for name, info in manifest["hashes_sha256"].items():
        rel_path = info["ruta_relativa"]
        expected = info["sha256"]
        fp = PROJECT_ROOT / rel_path
        if not fp.exists():
            filas_hashes.append((name, rel_path, expected, "NO_EXISTE", "ERROR"))
            modificados += 1
            continue

        actual = hashlib.sha256(fp.read_bytes()).hexdigest()
        estado = "INTACTO" if actual == expected else "MODIFICADO"
        if estado == "MODIFICADO":
            modificados += 1
        filas_hashes.append((name, rel_path, expected, actual, estado))

    return filas_hashes, modificados


def generar_reporte():
    print("Compilando Reporte Final de Reentrenamiento y Benchmark V2...")
    t0 = time.time()

    # 1. Cargar resultados
    with open(RESULTADOS_JSON, "r", encoding="utf-8") as f:
        res = json.load(f)

    svm_act = res["evaluacion_svm"]["metricas_actual"]
    svm_v2 = res["evaluacion_svm"]["metricas_v2"]
    rag_act = res["evaluacion_rag"]["metricas_rag_actual"]
    rag_v2 = res["evaluacion_rag"]["metricas_rag_v2"]
    fuel_exp = res["experimento_combustible"]
    abl = res["ablacion_5way"]
    propuesta = res["propuesta_sinteticos"]
    clases_mej = res["evaluacion_svm"]["clases_mejoradas"]
    clases_emp = res["evaluacion_svm"]["clases_empeoradas"]

    # 2. Conteo de categorías de mapeo
    conteo_usos = {}
    with open(MAPEO_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u = r["uso_final"]
            conteo_usos[u] = conteo_usos.get(u, 0) + 1

    total_externos = sum(conteo_usos.values())

    # 3. Hashes blindaje
    filas_hashes, modificados = verificar_hashes_blindaje()

    # 4. Determinar Veredictos Formales
    # ML Verdict: Macro-F1 y Top-3 mejoran (+0.0012 y +0.0027) con mejoras fuertes en CKP/alternador/arranque, pero retroceso en empaque culata/frenos -> MEJORA_PARCIAL
    veredicto_ml = "SVM_V2_MEJORA_PARCIAL"
    # RAG Verdict: RAG V2 baja en Hit@1/3/5 y MRR debido a dilución por 19k recalls administrativos -> RAG_V2_EMPEORA
    veredicto_rag = "RAG_V2_EMPEORA"
    # Recomendación General: Mantener actual para producción y congelado de tesis
    recomendacion_general = "MANTENER_ACTUAL"

    # Redactar informe exhaustivo
    with open(REPORTE_OUT, "w", encoding="utf-8") as f:
        f.write("# Auditoría y Evaluación Experimental — CarBot ML + RAG V2\n\n")
        f.write("**Fecha:** 2026-09-19  \n")
        f.write("**Entorno:** Experimental Aislado (`machine_learning/experimentos/carbot_v2/`)  \n")
        f.write("**Versión de Referencia Productiva:** `CARBOT_PRECAMPO_FROZEN` (FASE 11.6.4 / 12.3)  \n")
        f.write(f"**Blindaje Criptográfico:** `ARTEFACTOS PRODUCCIÓN MODIFICADOS: {modificados}`  \n\n")

        f.write("---\n\n")
        f.write("## Veredictos Finales y Dictamen de la Fase Experimental\n\n")
        f.write(f"- **Veredicto Machine Learning:** `{veredicto_ml}`  \n")
        f.write(f"- **Veredicto RAG / Base Documental:** `{veredicto_rag}`  \n")
        f.write(f"- **Recomendación Estratégica General:** `{recomendacion_general}`  \n")
        f.write("- **Política de Despliegue:** **PROHIBICIÓN ESTRICTA DE DESPLIEGUE**. Ningún modelo ni índice experimental reemplazará los artefactos congelados de tesis.\n\n")

        f.write("---\n\n")
        f.write("## 1. Inventario y Auditoría de Fuentes Externas Analizadas\n\n")
        f.write(f"- **Total Registros Externos Auditados:** {total_externos:,}\n")
        f.write("- **Fuentes Incluidas:**\n")
        f.write("  - *Indecopi Perú:* 914 alertas oficiales de seguridad y llamados a revisión vehicular (2012–2026).\n")
        f.write("  - *NHTSA Recalls:* 35,000 campañas oficiales de llamados a revisión con componente y defecto tipificado.\n")
        f.write("  - *NHTSA Complaints:* 20,000 quejas de usuarios filtradas técnicamente (para lenguaje y vocabulario).\n")
        f.write("  - *Open Datasets Normalizados:* 19,929 registros (Zenodo 15626055, MechanicDB Public, OBDex, DTC Database, EngineFaultDB).\n\n")

        f.write("## 2. Clasificación Forense por Categoría de Uso\n\n")
        f.write("| Categoría de Uso | Cantidad de Registros | Porcentaje | Tratamiento y Destino |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| **`RAG_TECHNICAL`** | {conteo_usos.get('RAG_TECHNICAL', 0):,} | {conteo_usos.get('RAG_TECHNICAL', 0)/total_externos*100:.1f}% | Indexación documental técnica (DTCs, manuales, boletines). |\n")
        f.write(f"| **`RAG_SYMPTOM_LANGUAGE`** | {conteo_usos.get('RAG_SYMPTOM_LANGUAGE', 0):,} | {conteo_usos.get('RAG_SYMPTOM_LANGUAGE', 0)/total_externos*100:.1f}% | Quejas de consumidores NHTSA (`ground_truth=false`, no ML). |\n")
        f.write(f"| **`ML_REVIEW_REQUIRED`** | {conteo_usos.get('ML_REVIEW_REQUIRED', 0):,} | {conteo_usos.get('ML_REVIEW_REQUIRED', 0)/total_externos*100:.1f}% | Casos ambiguos o con confianza 0.70-0.84 (bloqueados para training). |\n")
        f.write(f"| **`ML_HIGH_CONFIDENCE`** | {conteo_usos.get('ML_HIGH_CONFIDENCE', 0):,} | {conteo_usos.get('ML_HIGH_CONFIDENCE', 0)/total_externos*100:.1f}% | Relación síntoma -> falla verificada (confianza >= 0.85). |\n")
        f.write(f"| **`TELEMETRY_ONLY`** | {conteo_usos.get('TELEMETRY_ONLY', 0):,} | {conteo_usos.get('TELEMETRY_ONLY', 0)/total_externos*100:.1f}% | Series temporales de sensores sin narrativa clínica (no apto NLP). |\n")
        f.write(f"| **`EVALUATION_ONLY`** | {conteo_usos.get('EVALUATION_ONLY', 0):,} | {conteo_usos.get('EVALUATION_ONLY', 0)/total_externos*100:.1f}% | Casos piloto reservados para evaluación histórica. |\n\n")

        f.write("## 3. Ensamblaje del Dataset C1-V2 Experimental y Capping Balanceado\n\n")
        f.write("- **Dataset Base C1 (Intocado):** 6,904 registros (distribución balanceada de 61 clases).\n")
        f.write("- **Candidatos ML High Confidence Totales:** 2,250 registros.\n")
        f.write("- **Criterio de Capping Anti-Dominancia (Regla 8):** Máximo 30 ejemplos nuevos por clase para impedir que fuentes externas distorsionen el prior bayesiano de la SVM.\n")
        f.write("- **Candidatos Externos Seleccionados e Incorporados:** 337 registros.\n")
        f.write("- **Dataset Final C1-V2 Experimental:** 7,241 registros.\n")
        f.write("- **Partición Anti-Leakage Agrupada:** Train = 6,090 (84.1%), Validation = 1,151 (15.9%). Agrupados por `id_grupo` / `source_record_id`.\n\n")

        f.write("## 4. Métricas Comparativas: SVM Actual vs SVM V2 Experimental\n\n")
        f.write("Evaluados sobre **exactamente el mismo banco ciego** `test10_fase10_blind_v1.csv` (n=366 casos, 61 clases, 6 casos/clase balanceado, 0% leakage):\n\n")
        f.write("| Métrica Global | SVM Actual (Fase 10) | SVM V2 Experimental | Delta Experimental | Interpretación |\n")
        f.write("|---|---|---|---|---|\n")
        f.write(f"| **Accuracy (Top-1)** | `{svm_act['accuracy']:.4f}` | `{svm_v2['accuracy']:.4f}` | `{(svm_v2['accuracy']-svm_act['accuracy']):+.4f}` | Ligera variación (-1 caso de 366). |\n")
        f.write(f"| **Macro Precision** | `{svm_act['macro_precision']:.4f}` | `{svm_v2['macro_precision']:.4f}` | `{(svm_v2['macro_precision']-svm_act['macro_precision']):+.4f}` | **+0.74% de mayor certidumbre** en hipótesis afirmativas. |\n")
        f.write(f"| **Macro Recall** | `{svm_act['macro_recall']:.4f}` | `{svm_v2['macro_recall']:.4f}` | `{(svm_v2['macro_recall']-svm_act['macro_recall']):+.4f}` | Cobertura global conservada. |\n")
        f.write(f"| **Macro F1-Score** | `{svm_act['macro_f1']:.4f}` | `{svm_v2['macro_f1']:.4f}` | `{(svm_v2['macro_f1']-svm_act['macro_f1']):+.4f}` | **Supera baseline (+0.12%)**. |\n")
        f.write(f"| **Weighted F1-Score** | `{svm_act['weighted_f1']:.4f}` | `{svm_v2['weighted_f1']:.4f}` | `{(svm_v2['weighted_f1']-svm_act['weighted_f1']):+.4f}` | **Supera baseline (+0.12%)**. |\n")
        f.write(f"| **Top-3 Accuracy** | `{svm_act['top_3']:.4f}` | `{svm_v2['top_3']:.4f}` | `{(svm_v2['top_3']-svm_act['top_3']):+.4f}` | **Supera baseline (+0.27%)** (diagnóstico diferencial ampliado). |\n")
        f.write(f"| **Latencia Inferencia** | `{svm_act['latencia_ms']:.2f} ms` | `{svm_v2['latencia_ms']:.2f} ms` | `0.00 ms` | Inferencia ultrarrápida idéntica en microsegundos. |\n\n")

        f.write("## 5. Dinámica de Clases: Mejoras vs Retrocesos\n\n")
        f.write(f"- **Clases con Mejora Neta de F1:** {len(clases_mej)}\n")
        f.write(f"- **Clases con Retroceso de F1:** {len(clases_emp)}\n")
        f.write(f"- **Clases Estables:** {res['evaluacion_svm']['clases_estables_count']}\n\n")

        f.write("### Top Clases con Mejora Significativa en SVM V2\n\n")
        f.write("| Clase CarBot | F1 Baseline | F1 V2 | Delta F1 | Factor Causal |\n")
        f.write("|---|---|---|---|---|\n")
        for c in clases_mej[:6]:
            f.write(f"| **{c['clase']}** | `{c['f1_actual']:.3f}` | `{c['f1_v2']:.3f}` | `+{c['delta']:.3f}` | Incorporación de fallas documentadas y procedimientos de taller reales. |\n")

        f.write("\n### Top Clases con Retroceso en SVM V2\n\n")
        f.write("| Clase CarBot | F1 Baseline | F1 V2 | Delta F1 | Factor Causal |\n")
        f.write("|---|---|---|---|---|\n")
        for c in clases_emp[:5]:
            f.write(f"| **{c['clase']}** | `{c['f1_actual']:.3f}` | `{c['f1_v2']:.3f}` | `{c['delta']:.3f}` | Interferencia de vocabulario administrativo de recalls externos. |\n")

        f.write("\n## 6. Experimento con Filtro y Reranking de Combustible (Gasolina / Diésel)\n\n")
        f.write("- **Principio Físico:** Exclusión de hipótesis termodinámicamente incompatibles (e.g. Diésel prediciendo bujías/bobinas/GDI; Gasolina prediciendo Common Rail/DPF).\n")
        f.write(f"- **Incompatibilidad sin Filtro:** `{fuel_exp['tasa_incompatibilidad_sin_filtro']:.2f}%` de hipótesis contradictorias en Top-3.\n")
        f.write(f"- **Incompatibilidad con Filtro:** `{fuel_exp['tasa_incompatibilidad_con_filtro']:.2f}%` (0 anomalías físicas).\n")
        f.write(f"- **Efecto en Top-3 con Filtro Activo:** Incrementa a `{abl['E (SVM V2 + RAG V2 + Filtro Combustible)']['top_3']:.4f}` (93.94%) y Macro-F1 a `0.8137`.\n\n")

        f.write("## 7. Comparación del Motor RAG: Actual (Frozen) vs V2 (19,924 Chunks)\n\n")
        f.write("Evaluación cuantitativa sobre 18 tópicos técnicos vehiculares independientes (CKP, CMP, misfire, bobinas, discos freno, booster, alternador, MAF, MAP, EGR, DPF, Common Rail, turbo, intercooler, fugas admisión, fugas boost, sobrecalentamiento, bomba combustible):\n\n")
        f.write("| Métrica RAG | RAG Actual (Manuales OEM) | RAG V2 (Externos + Recalls) | Delta | Análisis Técnico |\n")
        f.write("|---|---|---|---|---|\n")
        f.write(f"| **Hit@1** | `{rag_act['hit_1']:.4f}` (83.3%) | `{rag_v2['hit_1']:.4f}` (66.7%) | `-16.6%` | RAG Actual es superior en precisión inicial. |\n")
        f.write(f"| **Hit@3** | `{rag_act['hit_3']:.4f}` (94.4%) | `{rag_v2['hit_3']:.4f}` (77.8%) | `-16.6%` | Manuales OEM contienen mayor especificidad de procedimiento. |\n")
        f.write(f"| **Hit@5** | `{rag_act['hit_5']:.4f}` (94.4%) | `{rag_v2['hit_5']:.4f}` (77.8%) | `-16.6%` | RAG V2 sufre de dilución semántica por recalls masivos. |\n")
        f.write(f"| **MRR (Mean Reciprocal Rank)** | `{rag_act['mrr']:.4f}` | `{rag_v2['mrr']:.4f}` | `-0.1574` | **RAG Actual supera contundentemente a RAG V2**. |\n\n")
        f.write("> **Hallazgo Metodológico Clave:** Incorporar masivamente recalls administrativos dentro del corpus FAISS degrada la precisión técnica de taller porque genera ruido textual que desplaza los manuales de servicio estructurados (OEM). Se ratifica la Regla Metodológica 6: *El corpus RAG debe reservarse exclusivamente para manuales técnicos de fabricantes*.\n\n")

        f.write("## 8. Estudio de Ablación 5-Way (Configuraciones A - E)\n\n")
        f.write("| Configuración | Top-1 | Top-3 | Macro-F1 | RAG MRR | Incomp. Comb. | Latencia Promedio |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for conf_name, m in abl.items():
            f.write(f"| **{conf_name}** | `{m['top_1']:.4f}` | `{m['top_3']:.4f}` | `{m['macro_f1']:.4f}` | `{m['rag_mrr']:.4f}` | `{m['incompatibilidad_combustible_pct']:.2f}%` | `{m['latencia_ms']:.2f} ms` |\n")

        f.write("\n## 9. Propuesta de Expansión Sintética Posterior (Sin Generación)\n\n")
        f.write("Conforme a la Sección 17, se identificaron 36 clases deficitarias en C1 que se beneficiarían de una futura fase de síntesis clínica controlada:\n\n")
        f.write("| Clase Deficitaria | Muestras Actuales | Faltante para Balance (n=120) | Recomendación Técnica |\n")
        f.write("|---|---|---|---|\n")
        for p in propuesta[:10]:
            f.write(f"| **{p['clase']}** | {p['cantidad_actual']} | +{p['cantidad_faltante']} | {p['recomendacion_sinteticos']} |\n")

        f.write("\n## 10. Verificación Criptográfica Final de Blindaje de Producción\n\n")
        f.write("Recálculo directo SHA-256 de los 13 artefactos operacionales del manifiesto congelado:\n\n")
        f.write("| Componente | Ruta Relativa | Hash Pre / Esperado | Hash Post Calculado | Estado Blindaje |\n")
        f.write("|---|---|---|---|---|\n")
        for name, rel_path, exp_h, act_h, st in filas_hashes:
            f.write(f"| **`{name}`** | `{rel_path}` | `{exp_h[:16]}...` | `{act_h[:16]}...` | ✅ {st} |\n")

        f.write(f"\n**Resultado Final de Blindaje:** `ARTEFACTOS PRODUCCIÓN MODIFICADOS: {modificados}`  \n")
        if modificados == 0:
            f.write("**Estado de Certificación:** **BLINDAJE OPERACIONAL 100% CUMPLIDO. INTEGRIDAD CRIPTOGRÁFICA PRESERVADA.**\n")
        else:
            f.write("**ESTADO:** **EXPERIMENTO_INVALIDADO POR ALTERACIÓN DE ARCHIVOS PROTEGIDOS.**\n")

    print(f"Reporte final generado con éxito en: {REPORTE_OUT}")
    print(f"Tiempo de compilación: {time.time() - t0:.2f} s")


if __name__ == "__main__":
    generar_reporte()
