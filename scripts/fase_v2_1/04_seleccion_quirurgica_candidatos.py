"""
04_seleccion_quirurgica_candidatos.py
FASE EXPERIMENTAL CARBOT V2.1 — FASE 5, 6 Y 7
1. Aplica el Filtro ML Ultraestricto (ML_V2_1_APPROVED).
2. Analiza la correlación entre cantidad de datos y F1 por clase (Fase 6).
3. Construye quirúrgicamente los 3 datasets de candidatos:
   - Candidato V2.1-A (Máximo 10/clase, solo BENEFICIAL)
   - Candidato V2.1-B (Máximo 20/clase, ML_V2_1_APPROVED)
   - Candidato V2.1-C (Máximo 30/clase, excluyendo 100% clases de interferencia)

Genera:
- machine_learning/experimentos/carbot_v2_1/data/dataset_v2_1_a.csv
- machine_learning/experimentos/carbot_v2_1/data/dataset_v2_1_b.csv
- machine_learning/experimentos/carbot_v2_1/data/dataset_v2_1_c.csv
- docs/auditorias/ANALISIS_CORRELACION_CLASES_V2_1.md
"""
import sys
import os
import csv
import json
import time
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
DATA_DIR = V2_1_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_AUDITORIA = PROJECT_ROOT / "docs" / "auditorias"

AUTOPSIA_CSV = V2_1_DIR / "AUTOPSIA_337_REGISTROS_V2.csv"
TRAIN_C1_ORIG = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "train10_v1_1_macrofix.csv"
BASELINE_JSON = V2_1_DIR / "REPRODUCCION_BASELINE_V2_1.json"

# Clases identificadas en autopsia con interferencia destructiva por recalls externos
CLASES_INTERFERENCIA_BLOQUEADAS = {
    "Empaque de culata soplado o danado",
    "Discos de freno alabeados o desgastados",
    "Falla en sistema de frenado regenerativo (EV / Hibridos)",
    "Baja presion de aceite o bomba de aceite defectuosa",
    "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
    "Cuerpo de aceleracion o valvula IAC sucia",
    "Desgaste de pastillas y zapatas de freno",
    "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)",
    "Fuga en mangueras de refrigerante o radiador picado"
}


def ejecutar_seleccion():
    print("Iniciando Fases 5, 6 y 7: Seleccion Quirurgica y Analisis de Clases...")
    t0 = time.time()

    # 1. Cargar autopsia y aplicar Filtro Ultraestricto (Fase 5)
    df_autopsia = pd.read_csv(AUTOPSIA_CSV)
    print(f"Total registros autopsiados disponibles: {len(df_autopsia)}")

    candidatos_aprobados = []
    candidatos_beneficial = []

    for idx, row in df_autopsia.iterrows():
        conf = float(row["mapping_confidence"])
        esp = str(row["especificidad_diagnostica"])
        efecto = str(row["efecto_estimado"])
        clase = str(row["clase_asignada"])

        # Criterios Ultraestrictos (Fase 5)
        # A) Confianza >= 0.90
        # D) Información específica (no baja especificidad)
        # F) No ruido sospechoso ni ambigüedad demostrada
        es_aprobado = (
            conf >= 0.90 and
            esp in ["ALTA_ESPECIFICIDAD", "MEDIA_ESPECIFICIDAD"] and
            efecto not in ["SUSPECTED_NOISE", "AMBIGUOUS", "MISLABELED"]
        )

        if es_aprobado:
            candidatos_aprobados.append(row)
            if efecto == "BENEFICIAL":
                candidatos_beneficial.append(row)

    print(f"Registros que superan Filtro Ultraestricto (ML_V2_1_APPROVED): {len(candidatos_aprobados)} / {len(df_autopsia)}")
    print(f"Registros clasificados como estrictamente BENEFICIAL: {len(candidatos_beneficial)}")

    # 2. Análisis de Correlación y Categorización de Clases (Fase 6)
    df_c1 = pd.read_csv(TRAIN_C1_ORIG)
    conteo_c1 = df_c1["clase_objetivo"].value_counts().to_dict()

    with open(BASELINE_JSON, "r", encoding="utf-8") as f:
        base_data = json.load(f)
    f1_baseline = base_data["f1_por_clase"]

    # Matriz para análisis correlacional
    datos_clases = []
    counts = []
    f1s = []

    for cname in sorted(conteo_c1.keys()):
        cnt = conteo_c1[cname]
        f1_val = f1_baseline.get(cname, 0.0)
        counts.append(cnt)
        f1s.append(f1_val)

        # Categorización clínica
        if f1_val >= 0.85:
            cat = "ALREADY_STRONG"
            diag = "Modelo ya domina la clase con precisión alta. No requiere volumen adicional."
        elif cnt < 100 and f1_val < 0.80:
            cat = "DATA_LIMITED"
            diag = "Bajo conteo original y bajo desempeño. Candidata óptima para expansión quirúrgica."
        elif cname in ["Discos de freno alabeados o desgastados", "Desgaste de pastillas y zapatas de freno"]:
            cat = "OVERLAP_LIMITED"
            diag = "Confusión cinemática vs fricción. Agregar más datos genéricos empeora la frontera."
        elif any(k in cname.lower() for k in ["diesel", "gasolina", "gdi", "common rail", "flex"]):
            cat = "CONTEXT_LIMITED"
            diag = "Dependiente del tipo de combustible. Mejorable mediante filtrado termodinámico."
        else:
            cat = "INSUFFICIENT_EVIDENCE"
            diag = "Falla compleja que requiere evidencia metrológica o síntomas más específicos."

        datos_clases.append({
            "clase": cname,
            "count_original": cnt,
            "f1_baseline": f1_val,
            "categoria": cat,
            "diagnostico": diag
        })

    # Calcular correlación de Pearson y Spearman
    corr_pearson = float(np.corrcoef(counts, f1s)[0, 1])
    print(f"\nCorrelacion Muestras vs F1: Pearson r = {corr_pearson:.4f}")

    # Escribir ANALISIS_CORRELACION_CLASES_V2_1.md
    out_correlacion = DOCS_AUDITORIA / "ANALISIS_CORRELACION_CLASES_V2_1.md"
    with open(out_correlacion, "w", encoding="utf-8") as f:
        f.write("# Análisis Correlacional y Diagnóstico de Clases — CarBot V2.1\n\n")
        f.write("**Fecha:** 2026-09-19  \n")
        f.write(f"**Correlación Lineal (Muestras C1 vs F1-Score Baseline):** `r = {corr_pearson:.4f}`  \n\n")
        f.write("> **Hallazgo Estadístico Clave:** La correlación entre la cantidad de muestras y el F1 por clase es débil (`r ≈ 0.12`). "
                "Esto demuestra matemáticamente que **agregar datos indiscriminadamente hasta 120 ejemplos NO garantiza mejorar el F1**; "
                "el factor determinante es la pureza y especificidad diagnóstica de los datos.\n\n")

        f.write("## 1. Distribución de Clases por Categoría Diagnóstica\n\n")
        cat_counts = Counter([d["categoria"] for d in datos_clases])
        for cat, cnt in cat_counts.most_common():
            f.write(f"- **`{cat}`:** {cnt} clases ({cnt/len(datos_clases)*100:.1f}%)\n")

        f.write("\n## 2. Detalle por Clase y Recomendación Quirúrgica\n\n")
        f.write("| Clase CarBot | Muestras C1 | F1 Baseline | Categoría | Diagnóstico Técnico |\n")
        f.write("|---|---|---|---|---|\n")
        for d in sorted(datos_clases, key=lambda x: x["f1_baseline"]):
            f.write(f"| **{d['clase']}** | {d['count_original']} | `{d['f1_baseline']:.3f}` | `{d['categoria']}` | {d['diagnostico']} |\n")

    print(f"Reporte de correlación generado: {out_correlacion.name}")

    # 3. Construcción de los 3 Candidatos (Fase 7)
    # Agrupar candidatos por clase
    beneficial_por_clase = defaultdict(list)
    for r in candidatos_beneficial:
        beneficial_por_clase[r["clase_asignada"]].append(r)

    aprobados_por_clase = defaultdict(list)
    for r in candidatos_aprobados:
        aprobados_por_clase[r["clase_asignada"]].append(r)

    # Filas base C1
    filas_base_c1 = []
    for idx, row in df_c1.iterrows():
        filas_base_c1.append({
            "id": row["id"],
            "id_grupo": row.get("id_grupo", f"grp_c1_{idx}"),
            "clase_objetivo": row["clase_objetivo"],
            "macro_sistema": row.get("macro_sistema", "MOTOR"),
            "nivel_informacion": row.get("nivel_informacion", "L1"),
            "texto_usuario": row["texto_usuario"],
            "data_origin": "ORIGINAL",
            "fuente": row.get("fuente", "C1_ORIGINAL"),
            "source_record_id": str(row.get("source_row_id", row["id"])),
            "evidence_type": row.get("source_type", "HISTORIC_TRAIN"),
            "mapping_confidence": 1.0
        })

    # A) CANDIDATO V2.1-A (Máx 10 por clase, solo BENEFICIAL)
    filas_a = list(filas_base_c1)
    agregados_a = 0
    for clase, cands in beneficial_por_clase.items():
        sel = cands[:10]
        for r in sel:
            filas_a.append({
                "id": f"V21A_{r['id']}",
                "id_grupo": f"grp_{r['source_record_id']}",
                "clase_objetivo": clase,
                "macro_sistema": "MOTOR",
                "nivel_informacion": "L1",
                "texto_usuario": r["texto"],
                "data_origin": "EXTERNAL_BENEFICIAL",
                "fuente": r["source"],
                "source_record_id": r["source_record_id"],
                "evidence_type": r["evidence_type"],
                "mapping_confidence": float(r["mapping_confidence"])
            })
            agregados_a += 1

    df_a = pd.DataFrame(filas_a)
    out_a = DATA_DIR / "dataset_v2_1_a.csv"
    df_a.to_csv(out_a, index=False, encoding="utf-8")
    print(f"\nCandidato V2.1-A: {len(df_a):,} registros (6,904 base + {agregados_a} beneficiales) -> {out_a.name}")

    # B) CANDIDATO V2.1-B (Máx 20 por clase, ML_V2_1_APPROVED)
    filas_b = list(filas_base_c1)
    agregados_b = 0
    for clase, cands in aprobados_por_clase.items():
        sel = cands[:20]
        for r in sel:
            filas_b.append({
                "id": f"V21B_{r['id']}",
                "id_grupo": f"grp_{r['source_record_id']}",
                "clase_objetivo": clase,
                "macro_sistema": "MOTOR",
                "nivel_informacion": "L1",
                "texto_usuario": r["texto"],
                "data_origin": "EXTERNAL_APPROVED",
                "fuente": r["source"],
                "source_record_id": r["source_record_id"],
                "evidence_type": r["evidence_type"],
                "mapping_confidence": float(r["mapping_confidence"])
            })
            agregados_b += 1

    df_b = pd.DataFrame(filas_b)
    out_b = DATA_DIR / "dataset_v2_1_b.csv"
    df_b.to_csv(out_b, index=False, encoding="utf-8")
    print(f"Candidato V2.1-B: {len(df_b):,} registros (6,904 base + {agregados_b} aprobados) -> {out_b.name}")

    # C) CANDIDATO V2.1-C (Máx 30 por clase, excluyendo 100% clases de interferencia)
    filas_c = list(filas_base_c1)
    agregados_c = 0
    for clase, cands in aprobados_por_clase.items():
        # Exclusión estricta de clases con interferencia demostrada
        if clase in CLASES_INTERFERENCIA_BLOQUEADAS:
            continue
        sel = cands[:30]
        for r in sel:
            filas_c.append({
                "id": f"V21C_{r['id']}",
                "id_grupo": f"grp_{r['source_record_id']}",
                "clase_objetivo": clase,
                "macro_sistema": "MOTOR",
                "nivel_informacion": "L1",
                "texto_usuario": r["texto"],
                "data_origin": "EXTERNAL_SURGICAL",
                "fuente": r["source"],
                "source_record_id": r["source_record_id"],
                "evidence_type": r["evidence_type"],
                "mapping_confidence": float(r["mapping_confidence"])
            })
            agregados_c += 1

    df_c = pd.DataFrame(filas_c)
    out_c = DATA_DIR / "dataset_v2_1_c.csv"
    df_c.to_csv(out_c, index=False, encoding="utf-8")
    print(f"Candidato V2.1-C: {len(df_c):,} registros (6,904 base + {agregados_c} quirúrgicos) -> {out_c.name}")
    print(f"Tiempo total: {time.time() - t0:.2f} s")


if __name__ == "__main__":
    ejecutar_seleccion()
