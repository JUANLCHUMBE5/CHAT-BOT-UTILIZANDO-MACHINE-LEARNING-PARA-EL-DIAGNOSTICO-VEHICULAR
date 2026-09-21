"""
Comparación Exhaustiva de Métodos de Calibración Probabilística en DEV (60 casos)
para Iteración 8.3 de CarBot.
Evalúa:
1. Platt (Sigmoide) cv=3 (Baseline 8.1)
2. Platt (Sigmoide) cv=5
3. Isotónica cv=3
4. Isotónica cv=5
5. Vector Temperature Scaling sobre Isotónica cv=5
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema
from machine_learning.training.fase8.experimentar_calibracion_dev import calcular_metricas_calibracion

DATA_TRAIN = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

def evaluar_modelo_prob(cal_falla, cal_sist, vec, temp_vector=1.0, exp_sist=0.65):
    X_dev = [c["sintoma"] for c in CASOS_DEV_60]
    y_dev = [c["falla_esperada"] for c in CASOS_DEV_60]

    X_vec = vec.transform(X_dev)
    p_f = cal_falla.predict_proba(X_vec)
    p_s = cal_sist.predict_proba(X_vec)

    clases_f = list(cal_falla.classes_)
    clases_s = list(cal_sist.classes_)
    sist_map = [{clases_s[j]: p_s[i, j] for j in range(len(clases_s))} for i in range(len(X_dev))]

    p_comb = np.zeros_like(p_f)
    for i in range(len(X_dev)):
        for j, f in enumerate(clases_f):
            m = obtener_macro_sistema(f)
            p_comb[i, j] = p_f[i, j] * (sist_map[i].get(m, 0.10) ** exp_sist)
        p_comb[i] /= np.sum(p_comb[i])

    if temp_vector != 1.0:
        for i in range(len(X_dev)):
            p_comb[i] = p_comb[i] ** (1.0 / temp_vector)
            p_comb[i] /= np.sum(p_comb[i])

    top1_idx = np.argmax(p_comb, axis=1)
    top1_conf = np.max(p_comb, axis=1)
    aciertos = np.array([1 if clases_f[top1_idx[i]] == y_dev[i] else 0 for i in range(len(y_dev))])

    top3_idx = np.argsort(p_comb, axis=1)[:, -3:][:, ::-1]
    top3_aciertos = sum(1 for i in range(len(y_dev)) if y_dev[i] in [clases_f[idx] for idx in top3_idx[i]])

    acc_top1 = float(np.mean(aciertos))
    acc_top3 = top3_aciertos / len(y_dev)

    calib = calcular_metricas_calibracion(top1_conf, aciertos)
    return {
        "acc_top1": acc_top1,
        "acc_top3": acc_top3,
        **calib,
    }

def main():
    print("Cargando TRAIN y ajustando TF-IDF...")
    df = pd.read_csv(DATA_TRAIN)
    X = df["sintoma"].values
    y_f = df["falla"].values
    y_s = [obtener_macro_sistema(f) for f in y_f]

    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
        max_features=25000,
    )
    X_vec = vec.fit_transform(X)

    configs = [
        ("Sigmoid cv=3 (Baseline 8.1)", "sigmoid", 3, 1.0),
        ("Sigmoid cv=5", "sigmoid", 5, 1.0),
        ("Isotonic cv=3", "isotonic", 3, 1.0),
        ("Isotonic cv=5 (crudo)", "isotonic", 5, 1.0),
        ("Isotonic cv=5 + Vec Temp=0.90", "isotonic", 5, 0.90),
        ("Isotonic cv=5 + Vec Temp=0.85", "isotonic", 5, 0.85),
        ("Isotonic cv=5 + Vec Temp=0.80", "isotonic", 5, 0.80),
        ("Isotonic cv=5 + Vec Temp=0.75", "isotonic", 5, 0.75),
    ]

    print("\n" + "=" * 115)
    print(f"{'Método':<32} | {'Top-1':<7} | {'Top-3':<7} | {'Brier':<7} | {'ECE':<7} | {'Acc>=80%':<9} | {'Cov>=80%':<8} | {'Conf Ok':<7} | {'Conf Err':<8}")
    print("=" * 115)

    modelos_entrenados = {}
    for nombre, metodo, cv, temp in configs:
        key = (metodo, cv)
        if key not in modelos_entrenados:
            svc_s = LinearSVC(C=1.0, class_weight="balanced", random_state=42, max_iter=3000)
            cal_s = CalibratedClassifierCV(estimator=svc_s, method=metodo, cv=cv)
            cal_s.fit(X_vec, y_s)

            svc_f = LinearSVC(C=1.2, class_weight="balanced", random_state=42, max_iter=3500)
            cal_f = CalibratedClassifierCV(estimator=svc_f, method=metodo, cv=cv)
            cal_f.fit(X_vec, y_f)

            modelos_entrenados[key] = (cal_f, cal_s)

        cal_f, cal_s = modelos_entrenados[key]
        res = evaluar_modelo_prob(cal_f, cal_s, vec, temp_vector=temp)
        print(f"{nombre:<32} | {res['acc_top1']*100:>6.2f}% | {res['acc_top3']*100:>6.2f}% | {res['brier']:>7.4f} | {res['ece']:>7.4f} | {res['acc_gte_80']*100:>8.2f}% | {res['cov_gte_80']*100:>7.1f}% | {res['conf_aciertos']:>7.4f} | {res['conf_errores']:>8.4f}")

    print("=" * 115)

if __name__ == "__main__":
    main()
