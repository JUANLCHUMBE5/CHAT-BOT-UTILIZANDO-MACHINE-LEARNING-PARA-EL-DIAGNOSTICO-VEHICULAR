"""
Comparación exhaustiva entre TRAIN original (6,189) y Corpus Fase 10 (2,440).
Detecta:
1. Duplicados exactos textuales.
2. Duplicados normalizados (lowercase, sin tildes, sin signos).
3. Near-duplicates (similitud coseno > 0.85 y > 0.88).
4. Posibles conflictos de etiquetas.
"""

import pandas as pd
import numpy as np
import unicodedata
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def comparar():
    df_orig = pd.read_csv("machine_learning/data/dataset_sintomas_limpio.csv")
    df_f10 = pd.read_csv("machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv")

    print(f"Total registros Original: {len(df_orig)}")
    print(f"Total registros Fase 10:  {len(df_f10)}")

    txt_orig_raw = df_orig["sintoma"].astype(str).tolist()
    txt_f10_raw = df_f10["texto_usuario"].astype(str).tolist()

    txt_orig_norm = [normalizar(t) for t in txt_orig_raw]
    txt_f10_norm = [normalizar(t) for t in txt_f10_raw]

    # 1. Duplicados exactos raw
    set_orig_raw = set(txt_orig_raw)
    dups_raw = []
    for i, t in enumerate(txt_f10_raw):
        if t in set_orig_raw:
            j = txt_orig_raw.index(t)
            dups_raw.append((df_f10.iloc[i]["id"], df_f10.iloc[i]["clase_objetivo"], j, df_orig.iloc[j]["falla"], t))
    print(f"Duplicados exactos raw: {len(dups_raw)}")

    # 2. Duplicados exactos normalizados
    set_orig_norm = set(txt_orig_norm)
    dups_norm = []
    for i, tn in enumerate(txt_f10_norm):
        if tn in set_orig_norm:
            j = txt_orig_norm.index(tn)
            dups_norm.append((df_f10.iloc[i]["id"], df_f10.iloc[i]["clase_objetivo"], j, df_orig.iloc[j]["falla"], tn))
    print(f"Duplicados normalizados: {len(dups_norm)}")

    # 3. TF-IDF y Near-duplicates
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    vec.fit(txt_orig_norm + txt_f10_norm)
    mat_orig = vec.transform(txt_orig_norm)
    mat_f10 = vec.transform(txt_f10_norm)

    print("Calculando similitud coseno entre 2,440 Fase 10 y 6,189 Originales...")
    sim = cosine_similarity(mat_f10, mat_orig)

    max_sim_por_f10 = np.max(sim, axis=1)
    max_idx_por_f10 = np.argmax(sim, axis=1)

    max_global = float(np.max(max_sim_por_f10))
    print(f"Similitud máxima global Fase 10 vs Original: {max_global:.4f} (umbral < 0.88)")

    near_dups_85 = []
    conflictos_etiqueta = []

    for i in range(len(df_f10)):
        s = float(max_sim_por_f10[i])
        if s >= 0.85:
            j = int(max_idx_por_f10[i])
            c_f10 = df_f10.iloc[i]["clase_objetivo"]
            c_orig = df_orig.iloc[j]["falla"]
            near_dups_85.append({
                "id_f10": df_f10.iloc[i]["id"],
                "clase_f10": c_f10,
                "idx_orig": j,
                "clase_orig": c_orig,
                "similitud": round(s, 4),
                "texto_f10": txt_f10_raw[i],
                "texto_orig": txt_orig_raw[j]
            })
            if c_f10 != c_orig:
                conflictos_etiqueta.append(near_dups_85[-1])

    print(f"Near-duplicates con similitud >= 0.85: {len(near_dups_85)}")
    print(f"Conflictos de etiqueta en near-duplicates: {len(conflictos_etiqueta)}")

    return dups_raw, dups_norm, near_dups_85, conflictos_etiqueta, max_global


if __name__ == "__main__":
    comparar()
