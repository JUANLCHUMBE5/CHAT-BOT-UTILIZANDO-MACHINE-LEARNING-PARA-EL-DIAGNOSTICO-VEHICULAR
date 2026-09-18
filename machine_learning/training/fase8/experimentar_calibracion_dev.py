"""
Experimento Sistemático de Calibración Probabilística en DEV (60 Casos).
Compara Platt/Sigmoide, Isotónica y Temperature Scaling para optimizar ECE y Brier Score
cumpliendo las metas:
- ECE <= 0.0800
- Brier <= 0.1500
- Top-1 DEV >= 80.00%
- Top-3 DEV >= 90.00%
- Accuracy (conf >= 80%) >= 85.00%
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema

DATA_TRAIN = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

def calcular_metricas_calibracion(confianzas: np.ndarray, aciertos: np.ndarray, num_bins: int = 10):
    n = len(confianzas)
    brier = float(np.mean((confianzas - aciertos) ** 2))
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
                "bin": f"({bin_lower:.1f}, {bin_upper:.1f}]",
                "count": bin_size,
                "acc": round(bin_acc, 4),
                "conf": round(bin_conf, 4),
                "gap": round(abs(bin_acc - bin_conf), 4),
            })

    mask_gte80 = confianzas >= 0.80
    acc_gte80 = float(np.mean(aciertos[mask_gte80])) if np.any(mask_gte80) else 0.0
    cov_gte80 = float(np.mean(mask_gte80))

    conf_aciertos = float(np.mean(confianzas[aciertos == 1])) if np.any(aciertos == 1) else 0.0
    conf_errores = float(np.mean(confianzas[aciertos == 0])) if np.any(aciertos == 0) else 0.0

    return {
        "brier": round(brier, 4),
        "ece": round(ece, 4),
        "acc_gte_80": round(acc_gte80, 4),
        "cov_gte_80": round(cov_gte80, 4),
        "conf_aciertos": round(conf_aciertos, 4),
        "conf_errores": round(conf_errores, 4),
        "bins": bins_info,
    }

def evaluar_en_dev(modelo_falla, modelo_sist, vectorizador, temp=1.0, exp_sist=0.65):
    X_dev = [c["sintoma"] for c in CASOS_DEV_60]
    y_dev = [c["falla_esperada"] for c in CASOS_DEV_60]
    X_dev_vec = vectorizador.transform(X_dev)
    probs_falla = modelo_falla.predict_proba(X_dev_vec)
    probs_sist = modelo_sist.predict_proba(X_dev_vec)

    clases_falla = list(modelo_falla.classes_)
    clases_sist = list(modelo_sist.classes_)

    probs_sist_dict = [
        {clases_sist[j]: probs_sist[i, j] for j in range(len(clases_sist))}
        for i in range(len(X_dev))
    ]

    probs_combinadas = np.zeros_like(probs_falla)
    for i in range(len(X_dev)):
        for j, f_nom in enumerate(clases_falla):
            macro = obtener_macro_sistema(f_nom)
            p_s = probs_sist_dict[i].get(macro, 0.10)
            p_f = probs_falla[i, j]
            probs_combinadas[i, j] = p_f * (p_s ** exp_sist)
        suma = np.sum(probs_combinadas[i])
        if suma > 0:
            probs_combinadas[i] /= suma

    top1_indices = np.argmax(probs_combinadas, axis=1)
    top1_probs = np.max(probs_combinadas, axis=1)

    if temp != 1.0:
        eps = 1e-6
        clipped_probs = np.clip(top1_probs, eps, 1.0 - eps)
        scaled_logits = logit(clipped_probs) / temp
        top1_probs = expit(scaled_logits)

    top1_predichas = [clases_falla[idx] for idx in top1_indices]
    aciertos = np.array([1 if top1_predichas[i] == y_dev[i] else 0 for i in range(len(y_dev))])

    top3_indices = np.argsort(probs_combinadas, axis=1)[:, -3:][:, ::-1]
    top3_aciertos = 0
    for i in range(len(y_dev)):
        preds_3 = [clases_falla[idx] for idx in top3_indices[i]]
        if y_dev[i] in preds_3:
            top3_aciertos += 1

    acc_top1 = float(np.mean(aciertos))
    acc_top3 = top3_aciertos / len(y_dev)

    calib = calcular_metricas_calibracion(top1_probs, aciertos)

    return {
        "acc_top1": round(acc_top1, 4),
        "acc_top3": round(acc_top3, 4),
        **calib,
    }

def main():
    print("Cargando dataset TRAIN 8.1...")
    df_train = pd.read_csv(DATA_TRAIN)
    X = df_train["sintoma"].values
    y_falla = df_train["falla"].values
    y_sistema = [obtener_macro_sistema(f) for f in y_falla]

    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
        max_features=25000,
    )
    X_vec = vec.fit_transform(X)

    print("Evaluando métodos de calibración en DEV (60 casos):")
    print("=" * 90)

    metodos = [
        ("Sigmoid (Platt) cv=3", "sigmoid", 3),
        ("Sigmoid (Platt) cv=5", "sigmoid", 5),
        ("Isotonic cv=3", "isotonic", 3),
        ("Isotonic cv=5", "isotonic", 5),
    ]

    resultados = []

    for nombre, metodo, cv in metodos:
        svc_s = LinearSVC(C=1.0, class_weight="balanced", random_state=42, max_iter=3000)
        cal_s = CalibratedClassifierCV(estimator=svc_s, method=metodo, cv=cv)
        cal_s.fit(X_vec, y_sistema)

        svc_f = LinearSVC(C=1.2, class_weight="balanced", random_state=42, max_iter=3500)
        cal_f = CalibratedClassifierCV(estimator=svc_f, method=metodo, cv=cv)
        cal_f.fit(X_vec, y_falla)

        res = evaluar_en_dev(cal_f, cal_s, vec, temp=1.0)
        res["nombre"] = nombre
        resultados.append((res, cal_f, cal_s, vec))
        print(f"[{nombre}] Top-1: {res['acc_top1']*100:.2f}% | Top-3: {res['acc_top3']*100:.2f}% | Brier: {res['brier']:.4f} | ECE: {res['ece']:.4f} | Acc>=80%: {res['acc_gte_80']*100:.2f}% (Cov: {res['cov_gte_80']*100:.1f}%) | Conf Aciertos: {res['conf_aciertos']:.4f} | Conf Errores: {res['conf_errores']:.4f}")

    print("\nEvaluando Temperature Scaling sobre Isotonic cv=5:")
    cal_f_iso = resultados[3][1]
    cal_s_iso = resultados[3][2]
    temps = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]
    mejor_t = None
    mejor_ece = 999.0
    for t in temps:
        res_t = evaluar_en_dev(cal_f_iso, cal_s_iso, vec, temp=t)
        res_t["nombre"] = f"Isotonic cv=5 + Temp={t}"
        print(f"[Iso cv=5 + Temp={t:.2f}] Top-1: {res_t['acc_top1']*100:.2f}% | Top-3: {res_t['acc_top3']*100:.2f}% | Brier: {res_t['brier']:.4f} | ECE: {res_t['ece']:.4f} | Acc>=80%: {res_t['acc_gte_80']*100:.2f}% (Cov: {res_t['cov_gte_80']*100:.1f}%) | Conf Aciertos: {res_t['conf_aciertos']:.4f} | Conf Errores: {res_t['conf_errores']:.4f}")
        if res_t['ece'] < mejor_ece:
            mejor_ece = res_t['ece']
            mejor_t = t

    print(f"\nMejor Temperatura para Isotonic cv=5: {mejor_t} con ECE = {mejor_ece:.4f}")
    res_opt = evaluar_en_dev(cal_f_iso, cal_s_iso, vec, temp=mejor_t)
    print("Bins de fiabilidad para el modelo óptimo:")
    for b in res_opt["bins"]:
        print(f"  Bin {b['bin']}: n={b['count']}, Acc={b['acc']*100:.1f}%, Conf={b['conf']*100:.1f}%, Gap={b['gap']:.4f}")

if __name__ == "__main__":
    main()
