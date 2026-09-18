"""
Evaluación y Calibración Completa para Iteración 8.1 de CarBot.
Ejecuta:
1. Holdout estratificado interno (80/20) sobre TRAIN.
2. Optimización de hiperparámetros y calibración sobre DEV (60 casos).
3. Evaluación por clase, matrices de confusión (holdout y DEV).
4. Métricas de calibración (Brier, ECE, Accuracy|conf>=80%, Cobertura).
5. Hash SHA-256 de artefactos Fase 7 baseline y Candidata Fase 8.
"""

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema

DATA_TRAIN = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
DATA_F7 = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_fase7_baseline.csv"
MODEL_DIR = BASE_DIR / "machine_learning" / "models"
F8_CANDIDATA_DIR = MODEL_DIR / "fase8_candidata"
F7_BASELINE_DIR = MODEL_DIR / "fase7_baseline"

def calcular_sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

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
                "accuracy": round(bin_acc, 4),
                "confidence": round(bin_conf, 4),
            })

    mask_gte80 = confianzas >= 0.80
    acc_gte80 = float(np.mean(aciertos[mask_gte80])) if np.any(mask_gte80) else 0.0
    cobertura_gte80 = float(np.mean(mask_gte80))

    mask_lt80 = confianzas < 0.80
    acc_lt80 = float(np.mean(aciertos[mask_lt80])) if np.any(mask_lt80) else 0.0

    return {
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "accuracy_gte_80": round(acc_gte80, 4),
        "cobertura_gte_80": round(cobertura_gte80, 4),
        "accuracy_lt_80": round(acc_lt80, 4),
        "confianza_promedio": round(float(np.mean(confianzas)), 4),
        "bins": bins_info
    }

def evaluar_holdout_interno(df: pd.DataFrame):
    print("\n--- PASO 1: EVALUACIÓN EN HOLDOUT ESTRATIFICADO INTERNO (80/20) ---")
    X = df["sintoma"].values
    y = df["falla"].values

    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Entrenamiento interno: {len(X_tr)} ejemplos | Holdout interno: {len(X_val)} ejemplos")

    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", min_df=1, max_features=30000)
    X_tr_vec = vec.fit_transform(X_tr)
    X_val_vec = vec.transform(X_val)

    svc = LinearSVC(C=1.2, class_weight="balanced", random_state=42, max_iter=3500)
    clf = CalibratedClassifierCV(estimator=svc, method="sigmoid", cv=3)
    clf.fit(X_tr_vec, y_tr)

    probs = clf.predict_proba(X_val_vec)
    preds_top1 = clf.classes_[probs.argmax(axis=1)]

    # Top-3
    top3_idx = np.argsort(probs, axis=1)[:, -3:]
    top3_classes = clf.classes_[top3_idx]
    es_top3 = [y_val[i] in top3_classes[i] for i in range(len(y_val))]

    aciertos = (preds_top1 == y_val).astype(int)
    confianzas = probs.max(axis=1)

    acc_top1 = float(np.mean(aciertos))
    acc_top3 = float(np.mean(es_top3))

    calib = calcular_metricas_calibracion(confianzas, aciertos)

    # Classification report
    rep = classification_report(y_val, preds_top1, output_dict=True, zero_division=0)

    # Top confusiones
    conf_pairs = {}
    for true_c, pred_c in zip(y_val, preds_top1):
        if true_c != pred_c:
            pair = f"{true_c} -> {pred_c}"
            conf_pairs[pair] = conf_pairs.get(pair, 0) + 1
    top_confusiones = sorted(conf_pairs.items(), key=lambda x: x[1], reverse=True)[:10]

    print(f"Top-1 Holdout: {acc_top1*100:.2f}% ({aciertos.sum()}/{len(y_val)})")
    print(f"Top-3 Holdout: {acc_top3*100:.2f}% ({sum(es_top3)}/{len(y_val)})")
    print(f"Brier Score Holdout: {calib['brier_score']:.4f} | ECE: {calib['ece']:.4f}")
    print(f"Accuracy (conf >= 80%): {calib['accuracy_gte_80']*100:.2f}% | Cobertura: {calib['cobertura_gte_80']*100:.2f}%")

    return {
        "n_muestras_holdout": len(y_val),
        "acc_top1": round(acc_top1, 4),
        "acc_top3": round(acc_top3, 4),
        "calibracion": calib,
        "top_confusiones": top_confusiones,
        "weighted_avg": rep["weighted avg"],
        "macro_avg": rep["macro avg"],
    }

def evaluar_y_seleccionar_en_dev(df: pd.DataFrame):
    print("\n--- PASO 2: SELECCIÓN DE HIPERPARÁMETROS Y EVALUACIÓN EN DEV (60 CASOS) ---")
    X = df["sintoma"].values
    y_falla = df["falla"].values
    y_sist = df["macro_sistema"].values

    # Grid de búsqueda
    c_grid = [1.0, 1.2, 1.5]
    cw_grid = ["balanced", None]
    mf_grid = [25000, 30000]

    mejor_config = None
    mejor_score = -1.0
    mejor_artefactos = None

    for mf in mf_grid:
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", min_df=1, max_features=mf)
        X_vec = vec.fit_transform(X)

        for cw in cw_grid:
            for c_val in c_grid:
                # Sistema
                svc_s = LinearSVC(C=1.0, class_weight=cw, random_state=42, max_iter=3000)
                clf_s = CalibratedClassifierCV(estimator=svc_s, method="sigmoid", cv=3)
                clf_s.fit(X_vec, y_sist)

                # Falla
                svc_f = LinearSVC(C=c_val, class_weight=cw, random_state=42, max_iter=3500)
                clf_f = CalibratedClassifierCV(estimator=svc_f, method="sigmoid", cv=3)
                clf_f.fit(X_vec, y_falla)

                # Evaluar DEV
                dev_res = ejecutar_eval_dev(clf_f, clf_s, vec, alpha=0.65)
                score_combinado = dev_res["top1_puro"] + dev_res["top3_puro"] - dev_res["calib_puro"]["ece"]

                if score_combinado > mejor_score:
                    mejor_score = score_combinado
                    mejor_config = {"max_features": mf, "class_weight": cw, "C": c_val, "alpha": 0.65}
                    mejor_artefactos = (clf_f, clf_s, vec)

    print(f"Mejor configuración en DEV: {mejor_config}")
    clf_f, clf_s, vec = mejor_artefactos

    # Evaluaciones exhaustivas con mejor modelo
    dev_completo = ejecutar_eval_dev(clf_f, clf_s, vec, alpha=0.65, detallado=True)
    return mejor_config, clf_f, clf_s, vec, dev_completo

def ejecutar_eval_dev(clf_f, clf_s, vec, alpha: float = 0.65, detallado: bool = False):
    clases_f = list(clf_f.classes_)
    clases_s = list(clf_s.classes_)
    sist_indices = {s: i for i, s in enumerate(clases_s)}

    t1_puro = 0
    t3_puro = 0
    t1_jer = 0
    t3_jer = 0
    macro_hits = 0

    conf_puro = []
    aciertos_puro = []
    conf_jer = []
    aciertos_jer = []

    detalles_casos = []

    for c in CASOS_DEV_60:
        texto = c["sintoma"]
        gt_f = c["falla_esperada"]
        gt_s = c["macro_sistema"]

        x_v = vec.transform([texto])
        pf = clf_f.predict_proba(x_v)[0]
        ps = clf_s.predict_proba(x_v)[0]

        # 1. Macro-sistema
        pred_s = clases_s[np.argmax(ps)]
        if pred_s == gt_s:
            macro_hits += 1

        # 2. Puro Linear SVM
        idx_puro = np.argsort(pf)[::-1]
        top1_f_puro = clases_f[idx_puro[0]]
        conf_top1_puro = float(pf[idx_puro[0]])
        top3_f_puro = [clases_f[i] for i in idx_puro[:3]]

        hit1_p = (top1_f_puro == gt_f)
        hit3_p = (gt_f in top3_f_puro)
        if hit1_p:
            t1_puro += 1
        if hit3_p:
            t3_puro += 1
        conf_puro.append(conf_top1_puro)
        aciertos_puro.append(1 if hit1_p else 0)

        # 3. Jerárquico
        scores = np.zeros_like(pf)
        for j, f_nom in enumerate(clases_f):
            s_nom = obtener_macro_sistema(f_nom)
            s_idx = sist_indices.get(s_nom, 0)
            scores[j] = pf[j] * (ps[s_idx] ** alpha)
        suma = scores.sum()
        p_jer = scores / suma if suma > 0 else scores

        idx_jer = np.argsort(p_jer)[::-1]
        top1_f_jer = clases_f[idx_jer[0]]
        conf_top1_jer = float(p_jer[idx_jer[0]])
        top3_f_jer = [clases_f[i] for i in idx_jer[:3]]

        hit1_j = (top1_f_jer == gt_f)
        hit3_j = (gt_f in top3_f_jer)
        if hit1_j:
            t1_jer += 1
        if hit3_j:
            t3_jer += 1
        conf_jer.append(conf_top1_jer)
        aciertos_jer.append(1 if hit1_j else 0)

        if detallado:
            detalles_casos.append({
                "id": c["id"],
                "gt_falla": gt_f,
                "gt_sistema": gt_s,
                "pred_top1_puro": top1_f_puro,
                "conf_puro": round(conf_top1_puro, 4),
                "hit_top1_puro": hit1_p,
                "hit_top3_puro": hit3_p,
                "pred_top1_jer": top1_f_jer,
                "conf_jer": round(conf_top1_jer, 4),
                "hit_top1_jer": hit1_j,
                "hit_top3_jer": hit3_j,
                "pred_sistema": pred_s,
                "hit_sistema": (pred_s == gt_s),
            })

    n = len(CASOS_DEV_60)
    calib_p = calcular_metricas_calibracion(np.array(conf_puro), np.array(aciertos_puro))
    calib_j = calcular_metricas_calibracion(np.array(conf_jer), np.array(aciertos_jer))

    res = {
        "n_casos": n,
        "top1_puro": round(t1_puro / n, 4),
        "top3_puro": round(t3_puro / n, 4),
        "hits_top1_puro": t1_puro,
        "hits_top3_puro": t3_puro,
        "top1_jer": round(t1_jer / n, 4),
        "top3_jer": round(t3_jer / n, 4),
        "hits_top1_jer": t1_jer,
        "hits_top3_jer": t3_jer,
        "macro_acc": round(macro_hits / n, 4),
        "macro_hits": macro_hits,
        "calib_puro": calib_p,
        "calib_jer": calib_j,
    }
    if detallado:
        res["detalles_casos"] = detalles_casos
    return res

def exportar_artefactos_y_hashes(clf_f, clf_s, vec, mejor_config, holdout_res, dev_res):
    print("\n--- PASO 3: EXPORTACIÓN DE ARTEFACTOS Y CÁLCULO DE HASHES SHA-256 ---")
    F8_CANDIDATA_DIR.mkdir(parents=True, exist_ok=True)

    # Guardar en fase8_candidata/
    ruta_mod_f8 = F8_CANDIDATA_DIR / "modelo_diagnostico.pkl"
    ruta_sist_f8 = F8_CANDIDATA_DIR / "modelo_sistema.pkl"
    ruta_vec_f8 = F8_CANDIDATA_DIR / "vectorizador_tfidf.pkl"

    joblib.dump(clf_f, ruta_mod_f8, compress=3)
    joblib.dump(clf_s, ruta_sist_f8, compress=3)
    joblib.dump(vec, ruta_vec_f8, compress=3)

    # Mantener sincronizado en machine_learning/models/ para backend
    shutil.copy2(ruta_mod_f8, MODEL_DIR / "modelo_diagnostico.pkl")
    shutil.copy2(ruta_sist_f8, MODEL_DIR / "modelo_sistema.pkl")
    shutil.copy2(ruta_vec_f8, MODEL_DIR / "vectorizador_tfidf.pkl")

    # Hashes Candidata Fase 8
    hash_train = calcular_sha256(DATA_TRAIN)
    hash_mod_f8 = calcular_sha256(ruta_mod_f8)
    hash_sist_f8 = calcular_sha256(ruta_sist_f8)
    hash_vec_f8 = calcular_sha256(ruta_vec_f8)

    # Hashes Baseline Fase 7
    hash_base_data = calcular_sha256(DATA_F7) if DATA_F7.exists() else "N/A"
    hash_base_mod = calcular_sha256(F7_BASELINE_DIR / "modelo_diagnostico.pkl") if (F7_BASELINE_DIR / "modelo_diagnostico.pkl").exists() else "N/A"
    hash_base_sist = calcular_sha256(F7_BASELINE_DIR / "modelo_sistema.pkl") if (F7_BASELINE_DIR / "modelo_sistema.pkl").exists() else "N/A"
    hash_base_vec = calcular_sha256(F7_BASELINE_DIR / "vectorizador_tfidf.pkl") if (F7_BASELINE_DIR / "vectorizador_tfidf.pkl").exists() else "N/A"

    reporte_final = {
        "metadata": {
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "iteracion": "Fase 8.1 - Candidata Formal",
            "arquitectura": "Linear SVM + TF-IDF (Puro y Jerárquico Calibrado)",
            "hiperparametros_seleccionados_en_dev": mejor_config,
        },
        "hashes_sha256": {
            "baseline_fase7": {
                "dataset_csv": hash_base_data,
                "modelo_diagnostico_pkl": hash_base_mod,
                "modelo_sistema_pkl": hash_base_sist,
                "vectorizador_tfidf_pkl": hash_base_vec,
            },
            "candidata_fase8": {
                "dataset_csv": hash_train,
                "modelo_diagnostico_pkl": hash_mod_f8,
                "modelo_sistema_pkl": hash_sist_f8,
                "vectorizador_tfidf_pkl": hash_vec_f8,
            }
        },
        "resultados_holdout_interno": holdout_res,
        "resultados_dev_60_casos": dev_res,
    }

    out_path = MODEL_DIR / "reporte_fase8_1_candidata.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reporte_final, f, indent=2, ensure_ascii=False)
    print(f"Reporte completo exportado en: {out_path}")
    return reporte_final

def main():
    print("=" * 80)
    print("EJECUCIÓN ITERACIÓN 8.1: EVALUACIÓN HOLDOUT, DEV Y CALIBRACIÓN DE FASE 8")
    print("=" * 80)

    df = pd.read_csv(DATA_TRAIN, encoding="utf-8").dropna(subset=["sintoma", "falla"])
    df["sintoma"] = df["sintoma"].astype(str).str.strip()
    df["falla"] = df["falla"].astype(str).str.strip()
    df["macro_sistema"] = df["falla"].apply(obtener_macro_sistema)

    holdout_res = evaluar_holdout_interno(df)
    mejor_config, clf_f, clf_s, vec, dev_res = evaluar_y_seleccionar_en_dev(df)
    exportar_artefactos_y_hashes(clf_f, clf_s, vec, mejor_config, holdout_res, dev_res)

    print("\n" + "=" * 80)
    print("RESUMEN CONSOLIDADO FASE 8.1:")
    print(f"  Holdout Top-1: {holdout_res['acc_top1']*100:.2f}% | Top-3: {holdout_res['acc_top3']*100:.2f}%")
    print(f"  DEV Top-1 (Puro): {dev_res['top1_puro']*100:.2f}% ({dev_res['hits_top1_puro']}/60)")
    print(f"  DEV Top-3 (Puro): {dev_res['top3_puro']*100:.2f}% ({dev_res['hits_top3_puro']}/60)")
    print(f"  DEV Top-1 (Jerárquico): {dev_res['top1_jer']*100:.2f}% ({dev_res['hits_top1_jer']}/60)")
    print(f"  DEV Top-3 (Jerárquico): {dev_res['top3_jer']*100:.2f}% ({dev_res['hits_top3_jer']}/60)")
    print(f"  DEV Macro-Sistema: {dev_res['macro_acc']*100:.2f}% ({dev_res['macro_hits']}/60)")
    print(f"  DEV Brier Score: {dev_res['calib_puro']['brier_score']:.4f}")
    print(f"  DEV ECE: {dev_res['calib_puro']['ece']:.4f}")
    print(f"  DEV Accuracy (conf >= 80%): {dev_res['calib_puro']['accuracy_gte_80']*100:.2f}%")
    print(f"  DEV Cobertura (conf >= 80%): {dev_res['calib_puro']['cobertura_gte_80']*100:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
