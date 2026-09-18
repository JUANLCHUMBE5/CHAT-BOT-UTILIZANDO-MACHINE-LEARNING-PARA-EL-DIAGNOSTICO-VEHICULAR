"""
Script de generación, auditoría y congelamiento de TRAIN10 y DEV10 para CarBot Fase 10.
Garantiza:
1. StratifiedGroupKFold sobre los 6189 registros originales.
2. GroupSplit estratificado sobre los 2440 registros Fase 10.
3. Cero intersección de IDs y de id_grupo.
4. Cero duplicados exactos y cero leakage.
5. Preservación de 61 clases en ambos splits.
6. Trazabilidad completa por fila.
"""

import sys
import json
import hashlib
import re
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Normalizador para agrupación de paráfrasis en dataset original
PREFIJOS = re.compile(
    r"\b(amigo una consulta|tengo un problema con mi auto|tengo un problema|"
    r"resulta que en mi carro|resulta que|sabes que|mi carro presenta|"
    r"amigo mi auto presenta|maestro una consulta|buenas tardes mecanico|"
    r"en mi vehiculo noto que|hace dos dias noto que)\b"
)
SUFIJOS = re.compile(
    r"\b(ultimamente|desde ayer|en carabayllo|en la pista|en las mananas|"
    r"cuando voy manejando|cuando salgo a trabajar|al pasar un rompemuelles|"
    r"de la nada|al acelerar|al andar a \d+ km(?:/h| por hora)?)\b"
)

def norm_g(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = PREFIJOS.sub(" ", t)
    t = SUFIJOS.sub(" ", t)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()

def normalizar_texto(texto: str) -> str:
    texto = str(texto).lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def calcular_sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 70)
    print("GENERACIÓN Y AUDITORÍA DE SPLITS TRAIN10 / DEV10")
    print("=" * 70)

    # 1. Cargar fuentes
    ruta_orig = Path("machine_learning/data/dataset_sintomas_limpio.csv")
    ruta_f10 = Path("machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv")
    
    sha_orig = calcular_sha256(ruta_orig)
    sha_f10 = calcular_sha256(ruta_f10)
    print(f"Dataset Original: {ruta_orig} | SHA-256: {sha_orig}")
    print(f"Dataset Fase 10: {ruta_f10} | SHA-256: {sha_f10}")

    df_orig = pd.read_csv(ruta_orig)
    df_f10 = pd.read_csv(ruta_f10)

    print(f"Filas original: {len(df_orig)} | Clases: {df_orig['falla'].nunique()}")
    print(f"Filas Fase 10: {len(df_f10)} | Clases: {df_f10['clase_objetivo'].nunique()}")

    # 2. Construir Capa de Trazabilidad para Dataset Original
    print("\n--- 2. CONSTRUYENDO CAPA DE TRAZABILIDAD PARA ORIGINAL ---")
    grupos_raw = df_orig.apply(lambda r: r["falla"] + "###" + norm_g(r["sintoma"]), axis=1)
    grp_map = {g: f"G-ORIG-{idx:04d}" for idx, g in enumerate(grupos_raw.unique(), 1)}
    print(f"Grupos de paráfrasis identificados en original: {len(grp_map)} grupos para {len(df_orig)} filas")

    df_orig_prep = pd.DataFrame({
        "id": [f"ORIG-{i:04d}" for i in range(1, len(df_orig) + 1)],
        "id_grupo": grupos_raw.map(grp_map),
        "clase_objetivo": df_orig["falla"],
        "macro_sistema": df_orig["sistema"],
        "nivel_informacion": "ORIGINAL_NO_ESTRATIFICADO",
        "texto_usuario": df_orig["sintoma"],
        "tipo_lenguaje": "COTIDIANO",
        "condicion_operacion": "NO_REPORTA",
        "sintomas_presentes": df_orig["sintoma"],
        "sintomas_negados": "NO_REPORTA",
        "dtc": df_orig["codigo_falla"].fillna("").astype(str).replace("nan", ""),
        "requiere_pregunta": "NO",
        "es_contrastivo": "NO",
        "clase_contrastiva": "",
        "fuente": "ORIGINAL",
        "observaciones": "TRAIN_CANONICO_ORIGINAL",
        "source_dataset": "dataset_sintomas_limpio.csv",
        "source_row_id": [str(i) for i in range(len(df_orig))],
        "source_type": "ORIGINAL",
        "specificity_level": "ORIGINAL_NO_ESTRATIFICADO",
        "synthetic_or_original": "ORIGINAL"
    })

    # 3. Preparar Dataset Fase 10 con Trazabilidad Coherente
    print("\n--- 3. PREPARANDO DATASET FASE 10 CON TRAZABILIDAD ---")
    df_f10_prep = pd.DataFrame({
        "id": df_f10["id"],
        "id_grupo": df_f10["id_grupo"],
        "clase_objetivo": df_f10["clase_objetivo"],
        "macro_sistema": df_f10["macro_sistema"],
        "nivel_informacion": df_f10["nivel_informacion"],
        "texto_usuario": df_f10["texto_usuario"],
        "tipo_lenguaje": df_f10["tipo_lenguaje"],
        "condicion_operacion": df_f10["condicion_operacion"],
        "sintomas_presentes": df_f10["sintomas_presentes"],
        "sintomas_negados": df_f10["sintomas_negados"],
        "dtc": df_f10["dtc"].fillna("").astype(str).replace("nan", ""),
        "requiere_pregunta": df_f10["requiere_pregunta"],
        "es_contrastivo": df_f10["es_contrastivo"],
        "clase_contrastiva": df_f10["clase_contrastiva"].fillna("").astype(str).replace("nan", ""),
        "fuente": df_f10["fuente"],
        "observaciones": df_f10["observaciones"],
        "source_dataset": "dataset_fase10_master_v1_1_2440.csv",
        "source_row_id": df_f10["id"],
        "source_type": "SINTETICO",
        "specificity_level": df_f10["nivel_informacion"],
        "synthetic_or_original": "SINTETICO"
    })

    # 4. Ejecutar Split Controlado Original (StratifiedGroupKFold, seed=42)
    print("\n--- 4. EJECUTANDO SPLIT ORIGINAL (StratifiedGroupKFold, n_splits=5, seed=42) ---")
    sgkf_orig = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_idx_orig, dev_idx_orig = next(sgkf_orig.split(df_orig_prep, df_orig_prep["clase_objetivo"], df_orig_prep["id_grupo"]))

    df_orig_train = df_orig_prep.iloc[train_idx_orig].copy()
    df_orig_dev = df_orig_prep.iloc[dev_idx_orig].copy()

    print(f"Original TRAIN: {len(df_orig_train)} filas ({len(df_orig_train)/len(df_orig_prep)*100:.2f}%) | Clases: {df_orig_train['clase_objetivo'].nunique()} | Grupos: {df_orig_train['id_grupo'].nunique()}")
    print(f"Original DEV:   {len(df_orig_dev)} filas ({len(df_orig_dev)/len(df_orig_prep)*100:.2f}%) | Clases: {df_orig_dev['clase_objetivo'].nunique()} | Grupos: {df_orig_dev['id_grupo'].nunique()}")

    # Validar que ningún grupo original esté compartido
    grps_orig_train = set(df_orig_train["id_grupo"])
    grps_orig_dev = set(df_orig_dev["id_grupo"])
    assert len(grps_orig_train.intersection(grps_orig_dev)) == 0, "ERROR: Colisión de id_grupo en original!"

    # 5. Ejecutar Split Controlado Fase 10 (Estratificado por clase y nivel, seed=42)
    print("\n--- 5. EJECUTANDO SPLIT FASE 10 (Estratificado por Clase y Nivel L1/L2/L3, seed=42) ---")
    f10_dev_ids = []
    f10_train_ids = []

    for c in sorted(df_f10_prep["clase_objetivo"].unique()):
        sub_c = df_f10_prep[df_f10_prep["clase_objetivo"] == c]
        for niv, n_dev in [("L1", 2), ("L2", 3), ("L3", 3)]:
            sub_niv = sub_c[sub_c["nivel_informacion"] == niv]
            # Muestreo reproducible
            dev_sub = sub_niv.sample(n=n_dev, random_state=42)
            train_sub = sub_niv.drop(dev_sub.index)
            f10_dev_ids.extend(dev_sub["id"].tolist())
            f10_train_ids.extend(train_sub["id"].tolist())

    df_f10_train = df_f10_prep[df_f10_prep["id"].isin(f10_train_ids)].copy()
    df_f10_dev = df_f10_prep[df_f10_prep["id"].isin(f10_dev_ids)].copy()

    print(f"Fase 10 TRAIN: {len(df_f10_train)} filas ({len(df_f10_train)/len(df_f10_prep)*100:.2f}%) | Clases: {df_f10_train['clase_objetivo'].nunique()} | Niveles: {df_f10_train['nivel_informacion'].value_counts().to_dict()}")
    print(f"Fase 10 DEV:   {len(df_f10_dev)} filas ({len(df_f10_dev)/len(df_f10_prep)*100:.2f}%) | Clases: {df_f10_dev['clase_objetivo'].nunique()} | Niveles: {df_f10_dev['nivel_informacion'].value_counts().to_dict()}")

    grps_f10_train = set(df_f10_train["id_grupo"])
    grps_f10_dev = set(df_f10_dev["id_grupo"])
    assert len(grps_f10_train.intersection(grps_f10_dev)) == 0, "ERROR: Colisión de id_grupo en Fase 10!"

    # 6. Unir TRAIN10 y DEV10
    print("\n--- 6. UNIFICANDO DATASETS EN TRAIN10 Y DEV10 ---")
    cols_orden = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones", "source_dataset",
        "source_row_id", "source_type", "specificity_level", "synthetic_or_original"
    ]

    df_train10 = pd.concat([df_orig_train[cols_orden], df_f10_train[cols_orden]], ignore_index=True)
    df_dev10 = pd.concat([df_orig_dev[cols_orden], df_f10_dev[cols_orden]], ignore_index=True)

    print(f"TRAIN10 Total: {len(df_train10)} filas (Original: {len(df_orig_train)}, Sintético: {len(df_f10_train)})")
    print(f"DEV10 Total:   {len(df_dev10)} filas (Original: {len(df_orig_dev)}, Sintético: {len(df_f10_dev)})")
    print(f"Total combinado: {len(df_train10) + len(df_dev10)} (esperado: {len(df_orig) + len(df_f10)})")

    assert len(df_train10) + len(df_dev10) == len(df_orig) + len(df_f10)
    assert df_train10["clase_objetivo"].nunique() == 61
    assert df_dev10["clase_objetivo"].nunique() == 61

    # 7. Auditoría de Intersección y Leakage entre TRAIN10 y DEV10
    print("\n--- 7. AUDITORÍA DE INTERSECCIÓN Y LEAKAGE TRAIN10 vs DEV10 ---")
    # A) Intersección de IDs
    inter_ids = set(df_train10["id"]).intersection(set(df_dev10["id"]))
    print(f"Intersección de IDs: {len(inter_ids)}")
    assert len(inter_ids) == 0, f"ERROR: IDs compartidos: {inter_ids}"

    # B) Intersección de id_grupo
    inter_grps = set(df_train10["id_grupo"]).intersection(set(df_dev10["id_grupo"]))
    print(f"Intersección de id_grupo: {len(inter_grps)}")
    assert len(inter_grps) == 0, f"ERROR: id_grupo compartidos: {inter_grps}"

    # C) Duplicados exactos entre TRAIN10 y DEV10
    train_textos = df_train10["texto_usuario"].tolist()
    dev_textos = df_dev10["texto_usuario"].tolist()

    train_textos_set = set(train_textos)
    dev_textos_set = set(dev_textos)
    exact_dups = train_textos_set.intersection(dev_textos_set)
    print(f"Duplicados exactos de texto TRAIN10 vs DEV10: {len(exact_dups)}")
    assert len(exact_dups) == 0, f"ERROR: Textos exactos compartidos: {exact_dups}"

    # D) Duplicados normalizados
    train_norm = {normalizar_texto(t): i for i, t in enumerate(train_textos)}
    dev_norm = {normalizar_texto(t): i for i, t in enumerate(dev_textos)}
    norm_dups = set(train_norm.keys()).intersection(set(dev_norm.keys()))
    print(f"Duplicados normalizados TRAIN10 vs DEV10: {len(norm_dups)}")
    assert len(norm_dups) == 0, f"ERROR: Textos normalizados compartidos: {norm_dups}"

    # E) Similitud y Near-Duplicates TRAIN10 vs DEV10
    print("Calculando similitud TF-IDF TRAIN10 vs DEV10...")
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    X_train = vec.fit_transform(train_textos)
    X_dev = vec.transform(dev_textos)

    # Calcular máxima similitud para cada muestra de DEV contra todo TRAIN
    # Muestreo por bloques para optimizar memoria
    sim_max_list = []
    leakage_records = []
    UMBRAL_NEAR_DUP = 0.88

    batch_size = 500
    for start in range(0, len(dev_textos), batch_size):
        end = min(start + batch_size, len(dev_textos))
        batch_sim = cosine_similarity(X_dev[start:end], X_train)
        for idx_local, row_sim in enumerate(batch_sim):
            idx_dev = start + idx_local
            max_idx_train = np.argmax(row_sim)
            max_val = row_sim[max_idx_train]
            sim_max_list.append(max_val)

            if max_val >= UMBRAL_NEAR_DUP:
                leakage_records.append({
                    "dev_id": df_dev10.iloc[idx_dev]["id"],
                    "dev_fuente": df_dev10.iloc[idx_dev]["synthetic_or_original"],
                    "dev_clase": df_dev10.iloc[idx_dev]["clase_objetivo"],
                    "dev_texto": df_dev10.iloc[idx_dev]["texto_usuario"],
                    "train_id": df_train10.iloc[max_idx_train]["id"],
                    "train_fuente": df_train10.iloc[max_idx_train]["synthetic_or_original"],
                    "train_clase": df_train10.iloc[max_idx_train]["clase_objetivo"],
                    "train_texto": df_train10.iloc[max_idx_train]["texto_usuario"],
                    "similitud_tfidf": round(float(max_val), 4)
                })

    print(f"Máxima similitud encontrada TRAIN10 vs DEV10: {max(sim_max_list):.4f}")
    print(f"Similitud promedio DEV10 vs TRAIN10: {np.mean(sim_max_list):.4f}")
    print(f"Near-duplicates (>= {UMBRAL_NEAR_DUP}) TRAIN10 vs DEV10: {len(leakage_records)}")

    # Guardar reporte de leakage
    df_leakage = pd.DataFrame(leakage_records)
    ruta_leakage = Path("machine_learning/data/fase10/fase10_leakage_train_dev.csv")
    df_leakage.to_csv(ruta_leakage, index=False, encoding="utf-8")
    print(f"Reporte de leakage guardado en: {ruta_leakage} ({len(df_leakage)} filas)")

    # 8. Guardar Archivos Congelados TRAIN10 y DEV10
    print("\n--- 8. GUARDANDO ARCHIVOS CONGELADOS TRAIN10 Y DEV10 ---")
    ruta_train10 = Path("machine_learning/data/fase10/train10_v1.csv")
    ruta_dev10 = Path("machine_learning/data/fase10/dev10_v1.csv")

    df_train10.to_csv(ruta_train10, index=False, encoding="utf-8")
    df_dev10.to_csv(ruta_dev10, index=False, encoding="utf-8")

    sha_train10 = calcular_sha256(ruta_train10)
    sha_dev10 = calcular_sha256(ruta_dev10)

    print(f"TRAIN10 guardado: {ruta_train10} | SHA-256: {sha_train10}")
    print(f"DEV10 guardado:   {ruta_dev10} | SHA-256: {sha_dev10}")

    # 9. Crear Tabla de Auditoría TRAIN / DEV por Clase
    print("\n--- 9. GENERANDO TABLA DE AUDITORÍA TRAIN / DEV ---")
    auditoria_filas = []
    for c in sorted(df_train10["clase_objetivo"].unique()):
        t_c = df_train10[df_train10["clase_objetivo"] == c]
        d_c = df_dev10[df_dev10["clase_objetivo"] == c]

        t_orig = len(t_c[t_c["synthetic_or_original"] == "ORIGINAL"])
        t_synth = len(t_c[t_c["synthetic_or_original"] == "SINTETICO"])
        t_l1 = len(t_c[t_c["nivel_informacion"] == "L1"])
        t_l2 = len(t_c[t_c["nivel_informacion"] == "L2"])
        t_l3 = len(t_c[t_c["nivel_informacion"] == "L3"])

        d_orig = len(d_c[d_c["synthetic_or_original"] == "ORIGINAL"])
        d_synth = len(d_c[d_c["synthetic_or_original"] == "SINTETICO"])
        d_l1 = len(d_c[d_c["nivel_informacion"] == "L1"])
        d_l2 = len(d_c[d_c["nivel_informacion"] == "L2"])
        d_l3 = len(d_c[d_c["nivel_informacion"] == "L3"])

        auditoria_filas.append({
            "clase": c,
            "macro_sistema": t_c.iloc[0]["macro_sistema"],
            "train_total": len(t_c),
            "train_original": t_orig,
            "train_sintetico": t_synth,
            "train_l1_synth": t_l1,
            "train_l2_synth": t_l2,
            "train_l3_synth": t_l3,
            "train_grupos": t_c["id_grupo"].nunique(),
            "dev_total": len(d_c),
            "dev_original": d_orig,
            "dev_sintetico": d_synth,
            "dev_l1_synth": d_l1,
            "dev_l2_synth": d_l2,
            "dev_l3_synth": d_l3,
            "dev_grupos": d_c["id_grupo"].nunique(),
            "ratio_train_pct": round(len(t_c) / (len(t_c) + len(d_c)) * 100, 1),
            "ratio_dev_pct": round(len(d_c) / (len(t_c) + len(d_c)) * 100, 1)
        })

    df_auditoria_train_dev = pd.DataFrame(auditoria_filas)
    ruta_auditoria_td = Path("machine_learning/data/fase10/fase10_auditoria_train_dev.csv")
    df_auditoria_train_dev.to_csv(ruta_auditoria_td, index=False, encoding="utf-8")
    print(f"Tabla de auditoría guardada en: {ruta_auditoria_td} ({len(df_auditoria_train_dev)} clases)")

    # 10. Crear SPLIT10_MANIFEST.json
    print("\n--- 10. GENERANDO SPLIT10_MANIFEST.json ---")
    ruta_manifest_split = Path("machine_learning/data/fase10/SPLIT10_MANIFEST.json")

    manifest_split_data = {
        "seed": 42,
        "metodo_split": {
            "original": "StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42) sobre grupos de paráfrasis norm_g",
            "fase10": "GroupSplit estratificado por clase y nivel L1(8/2), L2(12/3), L3(12/3) con id_grupo individual preservado"
        },
        "fuentes_utilizadas": [
            {
                "archivo": "dataset_sintomas_limpio.csv",
                "sha256": sha_orig,
                "filas": len(df_orig),
                "clases": 61,
                "tipo": "ORIGINAL_CANONICO"
            },
            {
                "archivo": "dataset_fase10_master_v1_1_2440.csv",
                "sha256": sha_f10,
                "filas": len(df_f10),
                "clases": 61,
                "tipo": "SINTETICO_DERIVADO_NORMALIZADO_COLOQUIAL"
            }
        ],
        "train10": {
            "archivo": str(ruta_train10.name),
            "sha256": sha_train10,
            "total_filas": len(df_train10),
            "total_clases": df_train10["clase_objetivo"].nunique(),
            "proporcion_pool": round(len(df_train10) / (len(df_train10) + len(df_dev10)) * 100, 2),
            "filas_original": len(df_orig_train),
            "filas_sintetico": len(df_f10_train),
            "sinteticos_por_nivel": df_f10_train["nivel_informacion"].value_counts().to_dict(),
            "total_grupos_unicos": df_train10["id_grupo"].nunique()
        },
        "dev10": {
            "archivo": str(ruta_dev10.name),
            "sha256": sha_dev10,
            "total_filas": len(df_dev10),
            "total_clases": df_dev10["clase_objetivo"].nunique(),
            "proporcion_pool": round(len(df_dev10) / (len(df_train10) + len(df_dev10)) * 100, 2),
            "filas_original": len(df_orig_dev),
            "filas_sintetico": len(df_f10_dev),
            "sinteticos_por_nivel": df_f10_dev["nivel_informacion"].value_counts().to_dict(),
            "total_grupos_unicos": df_dev10["id_grupo"].nunique()
        },
        "verificacion_integridad": {
            "interseccion_ids": len(inter_ids),
            "interseccion_id_grupo": len(inter_grps),
            "duplicados_exactos_texto": len(exact_dups),
            "duplicados_normalizados_texto": len(norm_dups),
            "maxima_similitud_tfidf": round(float(max(sim_max_list)), 4),
            "similitud_promedio_tfidf": round(float(np.mean(sim_max_list)), 4),
            "near_duplicates_umbral_088": len(leakage_records),
            "estado": "LOCKED_VALIDATED_SPLIT"
        }
    }

    with open(ruta_manifest_split, "w", encoding="utf-8") as f:
        json.dump(manifest_split_data, f, indent=2, ensure_ascii=False)
    print(f"Manifiesto de split guardado en: {ruta_manifest_split}")

    print("\n" + "=" * 70)
    print("GENERACIÓN Y CONGELAMIENTO DE TRAIN10 / DEV10 COMPLETADO CON ÉXITO")
    print("=" * 70)

if __name__ == "__main__":
    main()
