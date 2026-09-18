"""
Evaluador de Desempeño y Calibración en Benchmark DEV (60 Casos Independientes).
Permite evaluar hiperparámetros, pesos de clase y calibración de confianza
sin tocar en ningún momento el conjunto TEST reservado (G1_01-G1_50).
"""

import json
import numpy as np
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema
import joblib

def evaluar_modelo_en_dev(modelo_falla, modelo_sistema, vectorizador, exponente_jerarquico: float = 0.65):
    clases_f = list(modelo_falla.classes_)
    clases_s = list(modelo_sistema.classes_)
    sist_indices = {s: i for i, s in enumerate(clases_s)}

    top1_correctos = 0
    top3_correctos = 0
    macro_correctos = 0

    confianzas = []
    aciertos = []

    for c in CASOS_DEV_60:
        texto = c["sintoma"]
        gt_falla = c["falla_esperada"]
        gt_macro = c["macro_sistema"]
        dtc = c.get("codigo_dtc")

        vec = vectorizador.transform([texto])
        pf = modelo_falla.predict_proba(vec)[0]
        ps = modelo_sistema.predict_proba(vec)[0]

        # Macro-sistema top-1
        top_s_idx = np.argmax(ps)
        pred_macro = clases_s[top_s_idx]
        if pred_macro == gt_macro:
            macro_correctos += 1

        # Ponderación jerárquica
        scores = np.zeros_like(pf)
        for j, f_nom in enumerate(clases_f):
            s_nom = obtener_macro_sistema(f_nom)
            s_idx = sist_indices.get(s_nom, 0)
            scores[j] = pf[j] * (ps[s_idx] ** exponente_jerarquico)

        # Normalizar a distribución de probabilidad
        suma = scores.sum()
        probs = scores / suma if suma > 0 else scores

        indices_ordenados = probs.argsort()[::-1]
        top1_falla = clases_f[indices_ordenados[0]]
        confianza_top1 = probs[indices_ordenados[0]]
        top3_fallas = [clases_f[idx] for idx in indices_ordenados[:3]]

        es_top1 = (top1_falla == gt_falla)
        es_top3 = (gt_falla in top3_fallas)

        if es_top1:
            top1_correctos += 1
        if es_top3:
            top3_correctos += 1

        confianzas.append(confianza_top1)
        aciertos.append(1 if es_top1 else 0)

    n = len(CASOS_DEV_60)
    acc_top1 = top1_correctos / n
    acc_top3 = top3_correctos / n
    acc_macro = macro_correctos / n

    confianzas = np.array(confianzas)
    aciertos = np.array(aciertos)

    # 1. Brier Score (para Top-1)
    brier_score = float(np.mean((confianzas - aciertos) ** 2))

    # 2. Expected Calibration Error (ECE) con 10 bins
    num_bins = 10
    bin_boundaries = np.linspace(0, 1, num_bins + 1)
    ece = 0.0
    bins_info = []

    for b in range(num_bins):
        bin_lower = bin_boundaries[b]
        bin_upper = bin_boundaries[b + 1]
        mask = (confianzas > bin_lower) & (confianzas <= bin_upper)
        if np.any(mask):
            bin_acc = float(np.mean(aciertos[mask]))
            bin_conf = float(np.mean(confianzas[mask]))
            bin_size = int(np.sum(mask))
            ece += (bin_size / n) * abs(bin_acc - bin_conf)
            bins_info.append({
                "bin": f"({bin_lower:.2f}, {bin_upper:.2f}]",
                "count": bin_size,
                "accuracy": round(bin_acc, 4),
                "confidence": round(bin_conf, 4),
            })

    # 3. Confianza media en aciertos vs errores
    conf_aciertos = float(np.mean(confianzas[aciertos == 1])) if np.any(aciertos == 1) else 0.0
    conf_errores = float(np.mean(confianzas[aciertos == 0])) if np.any(aciertos == 0) else 0.0

    # 4. Accuracy | confianza >= 80%
    mask_alta = confianzas >= 0.80
    acc_alta_conf = float(np.mean(aciertos[mask_alta])) if np.any(mask_alta) else 0.0
    pct_alta_conf = float(np.mean(mask_alta))

    return {
        "n_muestras": n,
        "acc_top1": round(acc_top1, 4),
        "acc_top3": round(acc_top3, 4),
        "acc_macro": round(acc_macro, 4),
        "brier_score": round(brier_score, 4),
        "ece": round(ece, 4),
        "conf_media_aciertos": round(conf_aciertos, 4),
        "conf_media_errores": round(conf_errores, 4),
        "accuracy_alta_confianza_gte_80": round(acc_alta_conf, 4),
        "pct_casos_alta_confianza": round(pct_alta_conf, 4),
        "bins_calibracion": bins_info,
    }

if __name__ == "__main__":
    modelo_dir = BASE_DIR / "machine_learning" / "models"
    mf = joblib.load(modelo_dir / "modelo_diagnostico.pkl")
    ms = joblib.load(modelo_dir / "modelo_sistema.pkl")
    vec = joblib.load(modelo_dir / "vectorizador_tfidf.pkl")
    res = evaluar_modelo_en_dev(mf, ms, vec)
    print(json.dumps(res, indent=2))
