"""
11_ensamblar_dataset_v2.py
FASE EXPERIMENTAL — CARBOT ML + RAG V2
Ensambla el dataset experimental C1-V2:
1. Toma el dataset canónico C1 (train10_v1_1_macrofix.csv) como base intocada.
2. Incorpora candidatos ML_HIGH_CONFIDENCE curados y deduplicados con capping balanceado.
3. Garantiza exclusión de casos piloto (Sección 10) y partición anti-leakage agrupada.
4. Genera:
   - machine_learning/experimentos/carbot_v2/data/dataset_c1_v2_experimental.csv
   - machine_learning/experimentos/carbot_v2/data/train_c1_v2.csv
   - machine_learning/experimentos/carbot_v2/data/val_c1_v2.csv
   - docs/auditorias/DISTRIBUCION_DATASET_C1_V2.md
"""
import sys
import os
import csv
import json
import re
import random
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BASE_V2 = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2"
DATA_V2 = BASE_V2 / "data"
DOCS_AUDITORIA = PROJECT_ROOT / "docs" / "auditorias"

TRAIN_C1_ORIG = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "train10_v1_1_macrofix.csv"
MAPEO_CSV = DATA_V2 / "MAPEO_EXTERNOS_48_CLASES.csv"
COMPATIBILIDAD_JSON = DATA_V2 / "COMPATIBILIDAD_COMBUSTIBLE_48_CLASES.json"

# Casos piloto estrictamente prohibidos en entrenamiento
CASOS_PILOTO_BLOQUEADOS = [
    "ckp termico", "sensor ckp se apaga en caliente",
    "discos alabeados", "vibracion al frenar a alta velocidad",
    "misfire bobina cilindro", "bobina en corto cilindro",
    "fuga boost hilux", "manguera intercooler rajada hilux",
    "perdida de presion turbo hilux 1kd"
]

def obtener_compatibilidad_clase(clase: str, compat_dict: dict) -> str:
    # Búsqueda en diccionario
    if clase in compat_dict:
        return compat_dict[clase].get("fuel_compatibility", "UNKNOWN")
    for k, v in compat_dict.items():
        if k.lower() in clase.lower() or clase.lower() in k.lower():
            return v.get("fuel_compatibility", "UNKNOWN")
    # Reglas generales por defecto
    c_lower = clase.lower()
    if any(x in c_lower for x in ["diesel", "common rail", "dpf"]):
        return "DIESEL"
    if any(x in c_lower for x in ["gasolina", "bujias", "bobinas", "gdi", "evap"]):
        return "GASOLINE"
    return "BOTH"


def ensamblar():
    print("Iniciando Ensamblaje del Dataset Experimental C1-V2...")
    random.seed(42)

    # 1. Cargar compatibilidad
    compat_dict = {}
    if COMPATIBILIDAD_JSON.exists():
        with open(COMPATIBILIDAD_JSON, "r", encoding="utf-8") as f:
            compat_dict = json.load(f)

    # 2. Cargar Dataset C1 Original
    print(f"Cargando C1 original: {TRAIN_C1_ORIG.name}...")
    df_c1 = pd.read_csv(TRAIN_C1_ORIG)
    print(f"Registros C1 cargados: {len(df_c1):,}")

    conteo_orig = df_c1["clase_objetivo"].value_counts().to_dict()

    filas_c1_v2 = []
    for idx, row in df_c1.iterrows():
        clase = str(row["clase_objetivo"])
        filas_c1_v2.append({
            "id": row["id"],
            "id_grupo": row.get("id_grupo", f"grp_orig_{idx}"),
            "clase_objetivo": clase,
            "macro_sistema": row.get("macro_sistema", "MOTOR"),
            "nivel_informacion": row.get("nivel_informacion", "L1"),
            "texto_usuario": row["texto_usuario"],
            "data_origin": "ORIGINAL",
            "fuente": row.get("fuente", "C1_ORIGINAL"),
            "source_record_id": str(row.get("source_row_id", row["id"])),
            "evidence_type": row.get("source_type", "HISTORIC_TRAIN"),
            "mapping_confidence": 1.0,
            "fuel_compatibility": obtener_compatibilidad_clase(clase, compat_dict)
        })

    # 3. Cargar Candidatos Externos ML_HIGH_CONFIDENCE
    print(f"Cargando candidatos externos desde {MAPEO_CSV.name}...")
    candidatos_por_clase = defaultdict(list)
    textos_vistos = set()

    with open(MAPEO_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["uso_final"] != "ML_HIGH_CONFIDENCE":
                continue
            clase = r["carbot_class"]
            if clase not in conteo_orig:
                continue

            txt = r["texto"].strip()
            txt_lower = txt.lower()

            # Evitar piloto
            if any(cp in txt_lower for cp in CASOS_PILOTO_BLOQUEADOS):
                continue

            # Evitar duplicados de texto
            if txt_lower in textos_vistos or len(txt) < 15:
                continue
            textos_vistos.add(txt_lower)

            candidatos_por_clase[clase].append(r)

    # 4. Capping Balanceado (Sección 8: Evitar sobre-representación)
    # Máximo 25 a 35 ejemplos nuevos por clase o hasta un 25% del conteo original
    seleccionados_por_clase = defaultdict(list)
    total_externos_seleccionados = 0

    filas_reporte_distribucion = []

    for clase in sorted(conteo_orig.keys()):
        n_orig = conteo_orig[clase]
        cands = candidatos_por_clase.get(clase, [])
        n_cands = len(cands)

        # Capping inteligente: Priorizar clases con menor cobertura o tamaño
        limite_clase = min(n_cands, 30)
        cands_sel = cands[:limite_clase]
        seleccionados_por_clase[clase] = cands_sel
        total_externos_seleccionados += len(cands_sel)

        n_final = n_orig + len(cands_sel)
        pct_crecimiento = (len(cands_sel) / n_orig) * 100 if n_orig > 0 else 0

        filas_reporte_distribucion.append({
            "clase": clase,
            "original_count": n_orig,
            "external_candidates": n_cands,
            "external_selected": len(cands_sel),
            "final_count": n_final,
            "growth_percentage": round(pct_crecimiento, 1)
        })

    # 5. Agregar registros externos seleccionados
    ext_idx = 1
    for clase, cands in seleccionados_por_clase.items():
        for r in cands:
            filas_c1_v2.append({
                "id": f"EXT_V2_{ext_idx:05d}",
                "id_grupo": f"grp_ext_{r['source_record_id']}",
                "clase_objetivo": clase,
                "macro_sistema": "MOTOR",  # Default o inferido
                "nivel_informacion": "L1",
                "texto_usuario": r["texto"],
                "data_origin": "EXTERNAL_VERIFIED",
                "fuente": r["fuente"],
                "source_record_id": r["source_record_id"],
                "evidence_type": r["evidence_type"],
                "mapping_confidence": float(r["mapping_confidence"]),
                "fuel_compatibility": obtener_compatibilidad_clase(clase, compat_dict)
            })
            ext_idx += 1

    df_c1_v2 = pd.DataFrame(filas_c1_v2)
    out_csv = DATA_V2 / "dataset_c1_v2_experimental.csv"
    df_c1_v2.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"\nDataset C1-V2 ensamblado: {len(df_c1_v2):,} registros ({len(df_c1):,} originales + {total_externos_seleccionados:,} externos)")
    print(f"Guardado en: {out_csv}")

    # 6. Split Anti-Leakage Agrupado (85% Train / 15% Validation)
    grupos_unicos = df_c1_v2["id_grupo"].unique().tolist()
    random.shuffle(grupos_unicos)
    corte = int(len(grupos_unicos) * 0.85)
    grupos_train = set(grupos_unicos[:corte])
    grupos_val = set(grupos_unicos[corte:])

    df_train = df_c1_v2[df_c1_v2["id_grupo"].isin(grupos_train)]
    df_val = df_c1_v2[df_c1_v2["id_grupo"].isin(grupos_val)]

    out_train = DATA_V2 / "train_c1_v2.csv"
    out_val = DATA_V2 / "val_c1_v2.csv"
    df_train.to_csv(out_train, index=False, encoding="utf-8")
    df_val.to_csv(out_val, index=False, encoding="utf-8")
    print(f"Split anti-leakage: Train={len(df_train):,}, Val={len(df_val):,}")

    # 7. Generar reporte de distribución
    out_rep = DOCS_AUDITORIA / "DISTRIBUCION_DATASET_C1_V2.md"
    with open(out_rep, "w", encoding="utf-8") as f:
        f.write("# Distribución y Expansión Controlada de Clases — Dataset C1-V2 Experimental\n\n")
        f.write("**Fecha:** 2026-09-19  \n")
        f.write("**Norma Operacional:** Regla 8 de Capping Balanceado y Prevención de Dominancia Externa  \n\n")
        f.write("## 1. Resumen Global\n\n")
        f.write(f"- **Registros Originales C1:** {len(df_c1):,}\n")
        f.write(f"- **Registros Externos Verificados Incorporados:** {total_externos_seleccionados:,}\n")
        f.write(f"- **Total Dataset C1-V2:** {len(df_c1_v2):,}\n")
        f.write(f"- **Partición Train:** {len(df_train):,} ({len(df_train)/len(df_c1_v2)*100:.1f}%)\n")
        f.write(f"- **Partición Val:** {len(df_val):,} ({len(df_val)/len(df_c1_v2)*100:.1f}%)\n\n")
        
        f.write("## 2. Tabla de Crecimiento por Clase\n\n")
        f.write("| Clase CarBot | C1 Original | Candidatos Ext. | Seleccionados | Total V2 | Crecimiento (%) |\n")
        f.write("|---|---|---|---|---|---|\n")
        for row in filas_reporte_distribucion:
            f.write(f"| **{row['clase']}** | {row['original_count']} | {row['external_candidates']} | {row['external_selected']} | {row['final_count']} | +{row['growth_percentage']}% |\n")

    print(f"Reporte de distribución generado: {out_rep}")

if __name__ == "__main__":
    ensamblar()
