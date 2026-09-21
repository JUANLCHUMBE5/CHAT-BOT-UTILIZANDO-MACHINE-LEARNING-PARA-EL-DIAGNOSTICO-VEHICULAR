"""
Auditoría Metodológica de Contaminación y Deduplicación (Fase 8).
Comprueba rigurosamente:
1. Duplicados exactos (exact string matching normalizado).
2. Near-duplicates (Jaccard token similarity >= 0.75).
3. Similitud semántica anormalmente alta (TF-IDF Cosine Similarity >= 0.85).
Cumple con la directriz metodológica: no penalizar n-gramas técnicos comunes de taller.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60


def normalizar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def calcular_jaccard(tokens_a: set, tokens_b: set) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    inter = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return inter / union if union > 0 else 0.0

def auditar_contaminacion():
    print("=" * 80)
    print("AUDITORÍA METODOLÓGICA DE CONTAMINACIÓN Y DEDUPLICACIÓN (FASE 8)")
    print("=" * 80)

    # 1. Cargar TRAIN
    ruta_train = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
    df_train = pd.read_csv(ruta_train, encoding="utf-8")
    train_textos_raw = df_train["sintoma"].astype(str).tolist()
    train_norm = [normalizar_texto(t) for t in train_textos_raw]
    train_tokens = [set(t.split()) for t in train_norm]
    print(f"Total registros en TRAIN: {len(train_norm)}")

    # 2. Cargar DEV (60 casos)
    dev_ids = [c["id"] for c in CASOS_DEV_60]
    dev_textos_raw = [c["sintoma"] for c in CASOS_DEV_60]
    dev_norm = [normalizar_texto(t) for t in dev_textos_raw]
    dev_tokens = [set(t.split()) for t in dev_norm]
    print(f"Total casos en DEV: {len(dev_norm)}")

    # 3. Cargar TEST G1 (50 casos)
    ruta_g1 = BASE_DIR / "docs" / "graficas" / "reporte_prueba_general_100_casos.json"
    with open(ruta_g1, "r", encoding="utf-8") as f:
        data_g1 = json.load(f)
    g1_casos = [c for c in data_g1["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"]
    g1_ids = [c["id"] for c in g1_casos]
    g1_textos_raw = [c["texto_usuario"] for c in g1_casos]
    g1_norm = [normalizar_texto(t) for t in g1_textos_raw]
    g1_tokens = [set(t.split()) for t in g1_norm]
    print(f"Total casos en TEST G1 (benchmark externo de regresión): {len(g1_norm)}")

    # A. Duplicados exactos
    train_set = set(train_norm)
    exact_dev = [(dev_ids[i], dev_textos_raw[i]) for i, t in enumerate(dev_norm) if t in train_set]
    exact_g1 = [(g1_ids[i], g1_textos_raw[i]) for i, t in enumerate(g1_norm) if t in train_set]

    print("\n--- 1. DUPLICADOS EXACTOS ---")
    print(f"Colisiones exactas TRAIN vs DEV: {len(exact_dev)}")
    print(f"Colisiones exactas TRAIN vs TEST G1: {len(exact_g1)}")

    # B. Near-duplicates (Jaccard >= 0.75)
    UMBRAL_JACCARD = 0.75
    near_dev = []
    for i, dt in enumerate(dev_tokens):
        for j, tt in enumerate(train_tokens):
            sim = calcular_jaccard(dt, tt)
            if sim >= UMBRAL_JACCARD:
                near_dev.append({
                    "id": dev_ids[i],
                    "sim": round(sim, 4),
                    "eval_texto": dev_textos_raw[i],
                    "train_texto": train_textos_raw[j],
                })

    near_g1 = []
    for i, gt in enumerate(g1_tokens):
        for j, tt in enumerate(train_tokens):
            sim = calcular_jaccard(gt, tt)
            if sim >= UMBRAL_JACCARD:
                near_g1.append({
                    "id": g1_ids[i],
                    "sim": round(sim, 4),
                    "eval_texto": g1_textos_raw[i],
                    "train_texto": train_textos_raw[j],
                })

    print(f"\n--- 2. NEAR-DUPLICATES (Jaccard Token Overlap >= {UMBRAL_JACCARD}) ---")
    print(f"Candidatos near-duplicate TRAIN vs DEV: {len(near_dev)}")
    print(f"Candidatos near-duplicate TRAIN vs TEST G1: {len(near_g1)}")

    # C. Similitud Semántica Alta (TF-IDF Cosine Similarity >= 0.85)
    UMBRAL_COSENO = 0.85
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)
    vec.fit(train_norm + dev_norm + g1_norm)

    X_train = vec.transform(train_norm)
    X_dev = vec.transform(dev_norm)
    X_g1 = vec.transform(g1_norm)

    sim_dev = cosine_similarity(X_dev, X_train)
    max_sim_dev = sim_dev.max(axis=1)
    idx_max_dev = sim_dev.argmax(axis=1)

    candidatos_cos_dev = []
    for i, sim_val in enumerate(max_sim_dev):
        if sim_val >= UMBRAL_COSENO:
            candidatos_cos_dev.append({
                "id": dev_ids[i],
                "sim_coseno": round(float(sim_val), 4),
                "eval_texto": dev_textos_raw[i],
                "train_texto": train_textos_raw[idx_max_dev[i]],
            })

    sim_g1 = cosine_similarity(X_g1, X_train)
    max_sim_g1 = sim_g1.max(axis=1)
    idx_max_g1 = sim_g1.argmax(axis=1)

    candidatos_cos_g1 = []
    for i, sim_val in enumerate(max_sim_g1):
        if sim_val >= UMBRAL_COSENO:
            candidatos_cos_g1.append({
                "id": g1_ids[i],
                "sim_coseno": round(float(sim_val), 4),
                "eval_texto": g1_textos_raw[i],
                "train_texto": train_textos_raw[idx_max_g1[i]],
            })

    print(f"\n--- 3. SIMILITUD SEMÁNTICA ALTA (TF-IDF Cosine >= {UMBRAL_COSENO}) ---")
    print(f"Candidatos con similitud >= {UMBRAL_COSENO} TRAIN vs DEV: {len(candidatos_cos_dev)}")
    print(f"Candidatos con similitud >= {UMBRAL_COSENO} TRAIN vs TEST G1: {len(candidatos_cos_g1)}")
    print(f"Máxima similitud coseno observada TRAIN vs DEV: {float(max_sim_dev.max()):.4f}")
    print(f"Similitud coseno media TRAIN vs DEV: {float(max_sim_dev.mean()):.4f}")
    print(f"Máxima similitud coseno observada TRAIN vs TEST G1: {float(max_sim_g1.max()):.4f}")
    print(f"Similitud coseno media TRAIN vs TEST G1: {float(max_sim_g1.mean()):.4f}")

    # Guardar reporte detallado
    resultado = {
        "resumen": {
            "total_train": len(train_norm),
            "total_dev": len(dev_norm),
            "total_g1": len(g1_norm),
            "exact_duplicates_dev": len(exact_dev),
            "exact_duplicates_g1": len(exact_g1),
            "near_duplicates_dev": len(near_dev),
            "near_duplicates_g1": len(near_g1),
            "high_semantic_sim_dev": len(candidatos_cos_dev),
            "high_semantic_sim_g1": len(candidatos_cos_g1),
            "max_cosine_dev": round(float(max_sim_dev.max()), 4),
            "mean_cosine_dev": round(float(max_sim_dev.mean()), 4),
            "max_cosine_g1": round(float(max_sim_g1.max()), 4),
            "mean_cosine_g1": round(float(max_sim_g1.mean()), 4),
        },
        "detalles": {
            "near_dev": near_dev,
            "near_g1": near_g1,
            "high_semantic_dev": candidatos_cos_dev,
            "high_semantic_g1": candidatos_cos_g1,
        }
    }

    out_file = BASE_DIR / "machine_learning" / "models" / "auditoria_contaminacion_fase8.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nReporte de auditoría de contaminación guardado en: {out_file}")

if __name__ == "__main__":
    auditar_contaminacion()
