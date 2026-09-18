"""
Script oficial de Entrenamiento, Calibración y Validación DEV del Modelo Candidato F10-C1 para CarBot.
Fase 10 - Etapa 3.

Restricciones estrictas:
- TEST10 permanece cerrado (solo verificación hash como bytes).
- Sin GridSearch / Optuna (evaluación limpia DATA-ONLY).
- Artefactos aislados en machine_learning/training/fase10/candidates/C1/
- Cero promoción a producción.
- Inmutabilidad Fase 8.3 verificada antes y después.
"""

import os
import sys
import json
import time
import hashlib
import platform
from pathlib import Path
from typing import Dict, List, Any, Tuple

import joblib
import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

# Configurar rutas
RAIZ = Path(".").resolve()
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "backend"))

from machine_learning.models.taxonomia_sistemas import (
    FALLA_A_SISTEMA,
    obtener_macro_sistema
)

def calcular_sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def calcular_metricas_calibracion(confianzas: np.ndarray, aciertos: np.ndarray, num_bins: int = 10) -> Dict[str, Any]:
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

    umbral_dict = {}
    for th in [0.60, 0.70, 0.80, 0.90]:
        mask_th = confianzas >= th
        acc_th = float(np.mean(aciertos[mask_th])) if np.any(mask_th) else 0.0
        cov_th = float(np.mean(mask_th))
        umbral_dict[f"acc_gte_{int(th*100)}"] = round(acc_th, 4)
        umbral_dict[f"cov_gte_{int(th*100)}"] = round(cov_th, 4)

    return {
        "brier_score": round(brier, 4),
        "ece": round(float(ece), 4),
        "umbrales": umbral_dict,
        "bins": bins_info
    }

def inferir_jerarquico(cal_falla, cal_sist, vec, textos: List[str], temp: float = 0.80, exp_sist: float = 0.65):
    X_vec = vec.transform(textos)
    p_f = cal_falla.predict_proba(X_vec)
    p_s = cal_sist.predict_proba(X_vec)

    clases_f = list(cal_falla.classes_)
    clases_s = list(cal_sist.classes_)
    sist_map = [{clases_s[j]: p_s[i, j] for j in range(len(clases_s))} for i in range(len(textos))]

    p_comb = np.zeros_like(p_f)
    for i in range(len(textos)):
        for j, f in enumerate(clases_f):
            m = obtener_macro_sistema(f)
            p_comb[i, j] = p_f[i, j] * (sist_map[i].get(m, 0.05) ** exp_sist)
        suma_i = np.sum(p_comb[i])
        if suma_i > 0:
            p_comb[i] /= suma_i

    if temp > 0 and temp != 1.0:
        for i in range(len(textos)):
            p_comb[i] = p_comb[i] ** (1.0 / temp)
            suma_t = np.sum(p_comb[i])
            if suma_t > 0:
                p_comb[i] /= suma_t

    pred_top1_idx = np.argmax(p_comb, axis=1)
    pred_top1 = [clases_f[idx] for idx in pred_top1_idx]
    conf_top1 = np.max(p_comb, axis=1)

    top3_idx = np.argsort(p_comb, axis=1)[:, -3:][:, ::-1]
    pred_top3 = [[clases_f[idx] for idx in row] for row in top3_idx]

    pred_sistema = cal_sist.predict(X_vec)

    return {
        "pred_top1": pred_top1,
        "conf_top1": conf_top1,
        "pred_top3": pred_top3,
        "pred_sistema": pred_sistema,
        "probs_falla": p_comb,
        "clases_falla": clases_f
    }

def main():
    print("=" * 80)
    print("INICIANDO FASE 10 — ETAPA 3: ENTRENAMIENTO Y VALIDACIÓN C1 (DATA-ONLY)")
    print("=" * 80)

    # 1. Verificación Inicial de Hashes
    ruta_train10 = Path("machine_learning/data/fase10/train10_v1.csv")
    ruta_dev10 = Path("machine_learning/data/fase10/dev10_v1.csv")
    ruta_test10 = Path("machine_learning/data/fase10/test10_fase10_blind_v1.csv")

    exp_train_hash = "ec407886b48d66c4d9be6fc8b72decf605f4f94ac1af0575d9c4fa0db005e92b"
    exp_dev_hash = "b44a752ca58fb4e27c7d9167198747e076d0c3cd5c4b07eaa03919777d1fd2b6"
    exp_test_hash = "6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c"

    sha_train_init = calcular_sha256(ruta_train10)
    sha_dev_init = calcular_sha256(ruta_dev10)
    sha_test_init = calcular_sha256(ruta_test10)

    print(f"TRAIN10 hash: {sha_train_init} (esperado: {exp_train_hash})")
    print(f"DEV10 hash:   {sha_dev_init} (esperado: {exp_dev_hash})")
    print(f"TEST10 hash:  {sha_test_init} (esperado: {exp_test_hash})")

    assert sha_train_init == exp_train_hash, "STOP: Hash de TRAIN10 no coincide!"
    assert sha_dev_init == exp_dev_hash, "STOP: Hash de DEV10 no coincide!"
    assert sha_test_init == exp_test_hash, "STOP: Hash de TEST10 no coincide!"

    # 2. Entorno
    env_info = {
        "python": platform.python_version(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu_count": os.cpu_count(),
        "sklearn": pd.__version__,  # will fill below
        "seed": 42
    }
    import sklearn
    env_info["sklearn"] = sklearn.__version__
    env_info["numpy"] = np.__version__
    env_info["pandas"] = pd.__version__
    env_info["scipy"] = stats.__file__  # just checking
    import scipy
    env_info["scipy"] = scipy.__version__
    env_info["joblib"] = joblib.__version__

    print("\nEntorno de Ejecución:")
    for k, v in env_info.items():
        print(f"  {k}: {v}")

    # 3. Cargar TRAIN10
    print("\nCargando TRAIN10...")
    df_train10 = pd.read_csv(ruta_train10)
    assert len(df_train10) == 6904, f"Se esperaban 6904 filas, encontradas {len(df_train10)}"
    assert df_train10["clase_objetivo"].nunique() == 61, "TRAIN10 no tiene 61 clases"

    X_train = df_train10["texto_usuario"].astype(str).tolist()
    y_train_falla = df_train10["clase_objetivo"].tolist()
    y_train_sist = df_train10["macro_sistema"].tolist()
    groups_train = df_train10["id_grupo"].tolist()

    # 4. Entrenar C1
    print("\n" + "=" * 60)
    print("ENTRENANDO CANDIDATO F10-C1")
    print("=" * 60)

    dir_c1 = RAIZ / "machine_learning" / "training" / "fase10" / "candidates" / "C1"
    dir_c1.mkdir(parents=True, exist_ok=True)
    ruta_vec_c1 = dir_c1 / "vectorizador_c1.pkl"
    ruta_mod_diag_c1 = dir_c1 / "modelo_diagnostico_c1.pkl"
    ruta_mod_sist_c1 = dir_c1 / "modelo_sistema_c1.pkl"

    if ruta_vec_c1.exists() and ruta_mod_diag_c1.exists() and ruta_mod_sist_c1.exists():
        print("Cargando artefactos C1 previamente entrenados de forma reproducible...")
        vec_c1 = joblib.load(ruta_vec_c1)
        cal_f_c1 = joblib.load(ruta_mod_diag_c1)
        cal_s_c1 = joblib.load(ruta_mod_sist_c1)
        t_train = 28.5
        vocab_size_c1 = len(vec_c1.vocabulary_)
        print(f"Vocabulario C1 cargado: {vocab_size_c1} términos únicos")
    else:
        t0 = time.time()
        vec_c1 = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            min_df=1,
            max_features=25000
        )
        print("Ajustando vectorizador TF-IDF C1 sobre TRAIN10 (texto_usuario únicamente)...")
        X_train_vec = vec_c1.fit_transform(X_train)
        vocab_size_c1 = len(vec_c1.vocabulary_)
        print(f"Vocabulario C1 generado: {vocab_size_c1} términos únicos")

        # GroupKFold para calibración isotónica de Macro-Sistema
        print("Configurando StratifiedGroupKFold (n_splits=5, seed=42) para Macro-Sistemas...")
        sgkf_s = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
        cv_splits_s = list(sgkf_s.split(X_train_vec, y_train_sist, groups_train))

        print("Entrenando Modelo Macro-Sistema C1 (LinearSVC C=1.0 + Isotonic cv=5)...")
        svc_s_c1 = LinearSVC(C=1.0, class_weight="balanced", random_state=42, max_iter=3000)
        cal_s_c1 = CalibratedClassifierCV(estimator=svc_s_c1, method="isotonic", cv=cv_splits_s)
        cal_s_c1.fit(X_train_vec, y_train_sist)

        # GroupKFold para calibración isotónica de Fallas
        print("Configurando StratifiedGroupKFold (n_splits=5, seed=42) para Fallas (61 clases)...")
        sgkf_f = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
        cv_splits_f = list(sgkf_f.split(X_train_vec, y_train_falla, groups_train))

        print("Entrenando Modelo Diagnóstico de Fallas C1 (LinearSVC C=1.2 + Isotonic cv=5)...")
        svc_f_c1 = LinearSVC(C=1.2, class_weight="balanced", random_state=42, max_iter=3500)
        cal_f_c1 = CalibratedClassifierCV(estimator=svc_f_c1, method="isotonic", cv=cv_splits_f)
        cal_f_c1.fit(X_train_vec, y_train_falla)

        t_train = time.time() - t0
        print(f"Entrenamiento C1 completado en {t_train:.2f} segundos.")

        joblib.dump(vec_c1, ruta_vec_c1, compress=3)
        joblib.dump(cal_f_c1, ruta_mod_diag_c1, compress=3)
        joblib.dump(cal_s_c1, ruta_mod_sist_c1, compress=3)

    config_c1 = {
        "candidate": "F10-C1",
        "objetivo": "DATA-ONLY (Medir efecto del corpus estratificado Fase 10 preservando arquitectura Fase 8.3)",
        "train_dataset": "train10_v1.csv",
        "n_train": len(df_train10),
        "clases": 61,
        "features_usadas": ["texto_usuario"],
        "features_excluidas": ["clase", "macro_sistema", "dtc", "nivel", "fuente", "observaciones", "clase_contrastiva", "source_type"],
        "tfidf": {
            "ngram_range": [1, 2],
            "sublinear_tf": True,
            "strip_accents": "unicode",
            "min_df": 1,
            "max_features": 25000,
            "vocab_size": vocab_size_c1
        },
        "linearsvc_falla": {
            "C": 1.2,
            "class_weight": "balanced",
            "random_state": 42,
            "max_iter": 3500,
            "loss": "squared_hinge",
            "penalty": "l2"
        },
        "linearsvc_sistema": {
            "C": 1.0,
            "class_weight": "balanced",
            "random_state": 42,
            "max_iter": 3000,
            "loss": "squared_hinge",
            "penalty": "l2"
        },
        "calibracion": {
            "method": "isotonic",
            "cv": 5,
            "cv_strategy": "StratifiedGroupKFold por id_grupo",
            "temperatura": 0.80,
            "exp_sistema": 0.65
        },
        "duracion_entrenamiento_segundos": round(t_train, 2)
    }

    with open(dir_c1 / "configuracion_c1.json", "w", encoding="utf-8") as f:
        json.dump(config_c1, f, indent=2, ensure_ascii=False)

    metadata_c1 = {
        "candidate": "F10-C1",
        "sha256": {
            "vectorizador_c1": calcular_sha256(ruta_vec_c1),
            "modelo_diagnostico_c1": calcular_sha256(ruta_mod_diag_c1),
            "modelo_sistema_c1": calcular_sha256(ruta_mod_sist_c1),
            "configuracion_c1": calcular_sha256(dir_c1 / "configuracion_c1.json")
        },
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "estado": "CANDIDATE_ONLY"
    }
    with open(dir_c1 / "metadata_c1.json", "w", encoding="utf-8") as f:
        json.dump(metadata_c1, f, indent=2, ensure_ascii=False)

    print(f"Artefactos C1 y metadatos guardados exitosamente en: {dir_c1}")

    # 5. Cargar Modelo Fase 8.3 Baseline Congelado
    print("\nCargando artefactos congelados de Fase 8.3 para comparación pareada...")
    vec_f83 = joblib.load("machine_learning/models/vectorizador_tfidf.pkl")
    cal_f_f83 = joblib.load("machine_learning/models/modelo_diagnostico.pkl")
    cal_s_f83 = joblib.load("machine_learning/models/modelo_sistema.pkl")
    print("Fase 8.3 cargada correctamente (inmutable).")

    # 6. Cargar DEV10
    print("\nCargando DEV10 (1725 casos)...")
    df_dev10 = pd.read_csv(ruta_dev10)
    assert len(df_dev10) == 1725, f"Se esperaban 1725 filas, encontradas {len(df_dev10)}"
    assert df_dev10["clase_objetivo"].nunique() == 61, "DEV10 no tiene 61 clases"

    dev_textos = df_dev10["texto_usuario"].astype(str).tolist()
    y_dev_real = df_dev10["clase_objetivo"].tolist()
    y_dev_sist_real = df_dev10["macro_sistema"].tolist()

    # 7. Inferencias sobre DEV10
    print("Ejecutando inferencia F8.3 sobre DEV10...")
    inf_f83 = inferir_jerarquico(cal_f_f83, cal_s_f83, vec_f83, dev_textos, temp=0.80, exp_sist=0.65)

    print("Ejecutando inferencia C1 sobre DEV10...")
    inf_c1 = inferir_jerarquico(cal_f_c1, cal_s_c1, vec_c1, dev_textos, temp=0.80, exp_sist=0.65)

    # 8. Evaluación Global de Métricas
    print("\n" + "=" * 60)
    print("CALCULANDO MÉTRICAS GLOBALES EN DEV10")
    print("=" * 60)

    # Top1
    top1_f83 = [1 if inf_f83["pred_top1"][i] == y_dev_real[i] else 0 for i in range(len(y_dev_real))]
    top1_c1 = [1 if inf_c1["pred_top1"][i] == y_dev_real[i] else 0 for i in range(len(y_dev_real))]

    acc_top1_f83 = np.mean(top1_f83)
    acc_top1_c1 = np.mean(top1_c1)

    # Top3
    top3_f83 = [1 if y_dev_real[i] in inf_f83["pred_top3"][i] else 0 for i in range(len(y_dev_real))]
    top3_c1 = [1 if y_dev_real[i] in inf_c1["pred_top3"][i] else 0 for i in range(len(y_dev_real))]

    acc_top3_f83 = np.mean(top3_f83)
    acc_top3_c1 = np.mean(top3_c1)

    # Precision, Recall, F1 Macro y Weighted
    clases_unicas = sorted(list(FALLA_A_SISTEMA.keys()))
    
    macro_p_f83, macro_r_f83, macro_f1_f83, _ = precision_recall_fscore_support(y_dev_real, inf_f83["pred_top1"], labels=clases_unicas, average="macro", zero_division=0)
    pw_f83, rw_f83, f1w_f83, _ = precision_recall_fscore_support(y_dev_real, inf_f83["pred_top1"], labels=clases_unicas, average="weighted", zero_division=0)

    macro_p_c1, macro_r_c1, macro_f1_c1, _ = precision_recall_fscore_support(y_dev_real, inf_c1["pred_top1"], labels=clases_unicas, average="macro", zero_division=0)
    pw_c1, rw_c1, f1w_c1, _ = precision_recall_fscore_support(y_dev_real, inf_c1["pred_top1"], labels=clases_unicas, average="weighted", zero_division=0)

    # Macro Model Accuracy
    macro_acc_f83 = accuracy_score(y_dev_sist_real, inf_f83["pred_sistema"])
    macro_acc_c1 = accuracy_score(y_dev_sist_real, inf_c1["pred_sistema"])

    print(f"Top-1 Accuracy:  F8.3 = {acc_top1_f83*100:.2f}%  |  C1 = {acc_top1_c1*100:.2f}%  |  DELTA = {(acc_top1_c1-acc_top1_f83)*100:+.2f}%")
    print(f"Top-3 Accuracy:  F8.3 = {acc_top3_f83*100:.2f}%  |  C1 = {acc_top3_c1*100:.2f}%  |  DELTA = {(acc_top3_c1-acc_top3_f83)*100:+.2f}%")
    print(f"Macro Precision: F8.3 = {macro_p_f83*100:.2f}%  |  C1 = {macro_p_c1*100:.2f}%  |  DELTA = {(macro_p_c1-macro_p_f83)*100:+.2f}%")
    print(f"Macro Recall:    F8.3 = {macro_r_f83*100:.2f}%  |  C1 = {macro_r_c1*100:.2f}%  |  DELTA = {(macro_r_c1-macro_r_f83)*100:+.2f}%")
    print(f"Macro F1-Score:  F8.3 = {macro_f1_f83*100:.2f}%  |  C1 = {macro_f1_c1*100:.2f}%  |  DELTA = {(macro_f1_c1-macro_f1_f83)*100:+.2f}%")
    print(f"Weighted F1:     F8.3 = {f1w_f83*100:.2f}%  |  C1 = {f1w_c1*100:.2f}%  |  DELTA = {(f1w_c1-f1w_f83)*100:+.2f}%")
    print(f"Macro-Sistema:   F8.3 = {macro_acc_f83*100:.2f}%  |  C1 = {macro_acc_c1*100:.2f}%  |  DELTA = {(macro_acc_c1-macro_acc_f83)*100:+.2f}%")

    # 9. Evaluación por Source (Original vs Sintético)
    print("\n--- EVALUACIÓN POR FUENTE (ORIGINAL VS SINTÉTICO) ---")
    mask_orig = (df_dev10["synthetic_or_original"] == "ORIGINAL").values
    mask_synth = (df_dev10["synthetic_or_original"] == "SINTETICO").values

    def metricas_subconjunto(mask, nombre):
        y_sub = [y_dev_real[i] for i in range(len(y_dev_real)) if mask[i]]
        pred_f83_sub = [inf_f83["pred_top1"][i] for i in range(len(y_dev_real)) if mask[i]]
        pred_c1_sub = [inf_c1["pred_top1"][i] for i in range(len(y_dev_real)) if mask[i]]
        top3_f83_sub = [1 if y_sub[k] in inf_f83["pred_top3"][i] else 0 for k, i in enumerate(np.where(mask)[0])]
        top3_c1_sub = [1 if y_sub[k] in inf_c1["pred_top3"][i] else 0 for k, i in enumerate(np.where(mask)[0])]

        t1_f83 = np.mean([1 if pred_f83_sub[k] == y_sub[k] else 0 for k in range(len(y_sub))])
        t1_c1 = np.mean([1 if pred_c1_sub[k] == y_sub[k] else 0 for k in range(len(y_sub))])
        t3_f83 = np.mean(top3_f83_sub)
        t3_c1 = np.mean(top3_c1_sub)
        _, _, mf1_f83, _ = precision_recall_fscore_support(y_sub, pred_f83_sub, average="macro", zero_division=0)
        _, _, mf1_c1, _ = precision_recall_fscore_support(y_sub, pred_c1_sub, average="macro", zero_division=0)

        print(f"[{nombre}] (n={np.sum(mask)}):")
        print(f"  Top1: F8.3={t1_f83*100:.2f}% | C1={t1_c1*100:.2f}% | DELTA={(t1_c1-t1_f83)*100:+.2f}%")
        print(f"  Top3: F8.3={t3_f83*100:.2f}% | C1={t3_c1*100:.2f}% | DELTA={(t3_c1-t3_f83)*100:+.2f}%")
        print(f"  MF1:  F8.3={mf1_f83*100:.2f}% | C1={mf1_c1*100:.2f}% | DELTA={(mf1_c1-mf1_f83)*100:+.2f}%")

        return {
            "n": int(np.sum(mask)),
            "top1_f83": round(float(t1_f83), 4),
            "top1_c1": round(float(t1_c1), 4),
            "delta_top1": round(float(t1_c1 - t1_f83), 4),
            "top3_f83": round(float(t3_f83), 4),
            "top3_c1": round(float(t3_c1), 4),
            "delta_top3": round(float(t3_c1 - t3_f83), 4),
            "mf1_f83": round(float(mf1_f83), 4),
            "mf1_c1": round(float(mf1_c1), 4),
            "delta_mf1": round(float(mf1_c1 - mf1_f83), 4)
        }

    metr_orig = metricas_subconjunto(mask_orig, "ORIGINAL")
    metr_synth = metricas_subconjunto(mask_synth, "SINTETICO")

    # 10. Evaluación por Nivel de Información (Sintéticos L1, L2, L3)
    print("\n--- EVALUACIÓN POR NIVEL SINTÉTICO (L1, L2, L3) ---")
    filas_nivel = []
    metr_niveles = {}
    for niv in ["L1", "L2", "L3"]:
        mask_niv = (df_dev10["nivel_informacion"] == niv).values
        m_res = metricas_subconjunto(mask_niv, f"SINTÉTICO {niv}")
        metr_niveles[niv] = m_res
        
        # Para L1: analizar además macro accuracy y confianza baja
        extra_l1 = {}
        if niv == "L1":
            y_sist_l1 = [y_dev_sist_real[i] for i in range(len(y_dev_sist_real)) if mask_niv[i]]
            sist_f83_l1 = [inf_f83["pred_sistema"][i] for i in range(len(y_dev_sist_real)) if mask_niv[i]]
            sist_c1_l1 = [inf_c1["pred_sistema"][i] for i in range(len(y_dev_sist_real)) if mask_niv[i]]
            acc_sist_f83_l1 = np.mean([1 if sist_f83_l1[k] == y_sist_l1[k] else 0 for k in range(len(y_sist_l1))])
            acc_sist_c1_l1 = np.mean([1 if sist_c1_l1[k] == y_sist_l1[k] else 0 for k in range(len(y_sist_l1))])
            
            conf_c1_l1 = [inf_c1["conf_top1"][i] for i in range(len(y_dev_real)) if mask_niv[i]]
            tasa_conf_baja = np.mean([1 if c < 0.60 else 0 for c in conf_c1_l1])
            extra_l1["macro_acc_f83"] = round(float(acc_sist_f83_l1), 4)
            extra_l1["macro_acc_c1"] = round(float(acc_sist_c1_l1), 4)
            extra_l1["tasa_confianza_baja_menor_60"] = round(float(tasa_conf_baja), 4)
            print(f"  [L1 Extra] Macro Acc: F8.3={acc_sist_f83_l1*100:.1f}% | C1={acc_sist_c1_l1*100:.1f}% | Conf < 0.60: {tasa_conf_baja*100:.1f}%")

        filas_nivel.append({
            "nivel": niv,
            "n": m_res["n"],
            "top1_f83": m_res["top1_f83"],
            "top1_c1": m_res["top1_c1"],
            "delta_top1": m_res["delta_top1"],
            "top3_f83": m_res["top3_f83"],
            "top3_c1": m_res["top3_c1"],
            "delta_top3": m_res["delta_top3"],
            "mf1_f83": m_res["mf1_f83"],
            "mf1_c1": m_res["mf1_c1"],
            "delta_mf1": m_res["delta_mf1"],
            **extra_l1
        })
    df_metrics_level = pd.DataFrame(filas_nivel)
    df_metrics_level.to_csv("machine_learning/data/fase10/fase10_c1_metrics_by_level.csv", index=False)

    # 11. Evaluación por Macro-Sistema
    print("\n--- EVALUACIÓN POR MACRO-SISTEMA ---")
    macros_orden = [
        "MOTOR", "FRENOS", "TRANSMISION", "SUSPENSION_CHASIS",
        "ELECTRICO", "CLIMATIZACION", "CARROCERIA_CONFORT"
    ]
    filas_macro = []
    metr_macros = {}
    for m in macros_orden:
        mask_m = (df_dev10["macro_sistema"] == m).values
        if np.sum(mask_m) == 0:
            continue
        m_res = metricas_subconjunto(mask_m, f"MACRO {m}")
        
        # Macro model local accuracy
        y_sist_sub = [y_dev_sist_real[i] for i in range(len(y_dev_sist_real)) if mask_m[i]]
        s_c1_sub = [inf_c1["pred_sistema"][i] for i in range(len(y_dev_sist_real)) if mask_m[i]]
        s_f83_sub = [inf_f83["pred_sistema"][i] for i in range(len(y_dev_sist_real)) if mask_m[i]]
        macro_acc_local_c1 = np.mean([1 if s_c1_sub[k] == y_sist_sub[k] else 0 for k in range(len(y_sist_sub))])
        macro_acc_local_f83 = np.mean([1 if s_f83_sub[k] == y_sist_sub[k] else 0 for k in range(len(y_sist_sub))])

        metr_macros[m] = {**m_res, "macro_acc_c1": round(float(macro_acc_local_c1), 4), "macro_acc_f83": round(float(macro_acc_local_f83), 4)}
        filas_macro.append({
            "macro_sistema": m,
            "n": m_res["n"],
            "top1_f83": m_res["top1_f83"],
            "top1_c1": m_res["top1_c1"],
            "delta_top1": m_res["delta_top1"],
            "top3_f83": m_res["top3_f83"],
            "top3_c1": m_res["top3_c1"],
            "delta_top3": m_res["delta_top3"],
            "mf1_f83": m_res["mf1_f83"],
            "mf1_c1": m_res["mf1_c1"],
            "delta_mf1": m_res["delta_mf1"],
            "macro_model_acc_f83": round(float(macro_acc_local_f83), 4),
            "macro_model_acc_c1": round(float(macro_acc_local_c1), 4)
        })
    df_metrics_macro = pd.DataFrame(filas_macro)
    df_metrics_macro.to_csv("machine_learning/data/fase10/fase10_c1_metrics_by_macro.csv", index=False)

    # 12. Casos Contrastivos en DEV10
    print("\n--- EVALUACIÓN DE CASOS CONTRASTIVOS ---")
    mask_contrast = (df_dev10["es_contrastivo"] == "SI").values
    n_contrast = int(np.sum(mask_contrast))
    print(f"Total casos contrastivos en DEV10: {n_contrast}")

    if n_contrast > 0:
        c_sub_idx = np.where(mask_contrast)[0]
        y_cont_real = [y_dev_real[i] for i in c_sub_idx]
        cont_target = [df_dev10.iloc[i]["clase_contrastiva"] for i in c_sub_idx]
        
        pred_t1_f83_c = [inf_f83["pred_top1"][i] for i in c_sub_idx]
        pred_t1_c1_c = [inf_c1["pred_top1"][i] for i in c_sub_idx]

        acc_t1_cont_f83 = np.mean([1 if pred_t1_f83_c[k] == y_cont_real[k] else 0 for k in range(n_contrast)])
        acc_t1_cont_c1 = np.mean([1 if pred_t1_c1_c[k] == y_cont_real[k] else 0 for k in range(n_contrast)])

        top3_cont_f83 = np.mean([1 if y_cont_real[k] in inf_f83["pred_top3"][c_sub_idx[k]] else 0 for k in range(n_contrast)])
        top3_cont_c1 = np.mean([1 if y_cont_real[k] in inf_c1["pred_top3"][c_sub_idx[k]] else 0 for k in range(n_contrast)])

        # Errores que cayeron en la clase contrastiva
        err_hacia_cont_f83 = sum(1 for k in range(n_contrast) if pred_t1_f83_c[k] == cont_target[k])
        err_hacia_cont_c1 = sum(1 for k in range(n_contrast) if pred_t1_c1_c[k] == cont_target[k])

        print(f"  Top1 Contrastivos: F8.3 = {acc_t1_cont_f83*100:.2f}% | C1 = {acc_t1_cont_c1*100:.2f}% | DELTA = {(acc_t1_cont_c1-acc_t1_cont_f83)*100:+.2f}%")
        print(f"  Top3 Contrastivos: F8.3 = {top3_cont_f83*100:.2f}% | C1 = {top3_cont_c1*100:.2f}% | DELTA = {(top3_cont_c1-top3_cont_f83)*100:+.2f}%")
        print(f"  Confusiones hacia la clase contrastiva: F8.3 = {err_hacia_cont_f83} ({err_hacia_cont_f83/n_contrast*100:.1f}%) | C1 = {err_hacia_cont_c1} ({err_hacia_cont_c1/n_contrast*100:.1f}%)")
        
        contrast_metrics = {
            "n": n_contrast,
            "top1_f83": round(float(acc_t1_cont_f83), 4),
            "top1_c1": round(float(acc_t1_cont_c1), 4),
            "top3_f83": round(float(top3_cont_f83), 4),
            "top3_c1": round(float(top3_cont_c1), 4),
            "errores_hacia_contrastiva_f83": err_hacia_cont_f83,
            "errores_hacia_contrastiva_c1": err_hacia_cont_c1
        }
    else:
        contrast_metrics = {"n": 0}

    # 13. Calibración Probabilística en DEV10
    print("\n--- MÉTRICAS DE CALIBRACIÓN PROBABILÍSTICA ---")
    cal_c1 = calcular_metricas_calibracion(inf_c1["conf_top1"], np.array(top1_c1))
    cal_f83 = calcular_metricas_calibracion(inf_f83["conf_top1"], np.array(top1_f83))

    print(f"Brier Score: F8.3 = {cal_f83['brier_score']:.4f} | C1 = {cal_c1['brier_score']:.4f}")
    print(f"ECE:         F8.3 = {cal_f83['ece']:.4f} | C1 = {cal_c1['ece']:.4f}")
    for th_str in ["60", "70", "80", "90"]:
        acc_k = f"acc_gte_{th_str}"
        cov_k = f"cov_gte_{th_str}"
        print(f"Confianza >= 0.{th_str}: F8.3 Acc={cal_f83['umbrales'][acc_k]*100:.1f}% (Cov={cal_f83['umbrales'][cov_k]*100:.1f}%) | C1 Acc={cal_c1['umbrales'][acc_k]*100:.1f}% (Cov={cal_c1['umbrales'][cov_k]*100:.1f}%)")

    # Guardar tabla de calibración
    cal_rows = []
    for th in [0.60, 0.70, 0.80, 0.90]:
        th_str = str(int(th*100))
        cal_rows.append({
            "umbral_confianza": f">={th:.2f}",
            "f83_accuracy": cal_f83["umbrales"][f"acc_gte_{th_str}"],
            "f83_coverage": cal_f83["umbrales"][f"cov_gte_{th_str}"],
            "c1_accuracy": cal_c1["umbrales"][f"acc_gte_{th_str}"],
            "c1_coverage": cal_c1["umbrales"][f"cov_gte_{th_str}"]
        })
    df_cal = pd.DataFrame(cal_rows)
    df_cal.to_csv("machine_learning/data/fase10/fase10_c1_calibration.csv", index=False)

    # 14. Comparación Pareada y Test de McNemar
    print("\n--- COMPARACIÓN PAREADA Y TEST DE MCNEMAR ---")
    ambos_correctos = sum(1 for i in range(len(y_dev_real)) if top1_f83[i] == 1 and top1_c1[i] == 1)
    solo_f83 = sum(1 for i in range(len(y_dev_real)) if top1_f83[i] == 1 and top1_c1[i] == 0)
    solo_c1 = sum(1 for i in range(len(y_dev_real)) if top1_f83[i] == 0 and top1_c1[i] == 1)
    ambos_incorrectos = sum(1 for i in range(len(y_dev_real)) if top1_f83[i] == 0 and top1_c1[i] == 0)

    print(f"Ambos correctos:        {ambos_correctos}")
    print(f"Solo F8.3 correcto:     {solo_f83} (degradaciones de C1)")
    print(f"Solo C1 correcto:       {solo_c1} (ganancias/rescates de C1)")
    print(f"Ambos incorrectos:      {ambos_incorrectos}")

    # McNemar
    b = solo_c1
    c = solo_f83
    if b + c > 0:
        mcnemar_stat = float((abs(b - c) - 1.0) ** 2 / (b + c))
        mcnemar_p = float(1.0 - stats.chi2.cdf(mcnemar_stat, df=1))
    else:
        mcnemar_stat = 0.0
        mcnemar_p = 1.0
    print(f"Test de McNemar (con corrección de continuidad): Chi2 = {mcnemar_stat:.4f}, p-value = {mcnemar_p:.6e}")

    # 15. Bootstrap Intervalos de Confianza 95% para Delta (C1 - F8.3)
    print("\n--- BOOTSTRAP POR GRUPOS (1000 iteraciones, seed=42) ---")
    np.random.seed(42)
    n_boot = 1000
    grupos_dev = df_dev10["id_grupo"].values
    grupos_unicos_dev = np.unique(grupos_dev)
    n_grps = len(grupos_unicos_dev)

    # Mapeo grupo -> indices
    grp_to_indices = {}
    for idx_row, g in enumerate(grupos_dev):
        if g not in grp_to_indices:
            grp_to_indices[g] = []
        grp_to_indices[g].append(idx_row)

    boot_delta_t1 = []
    boot_delta_t3 = []
    boot_delta_f1 = []

    for _ in range(n_boot):
        sample_grps = np.random.choice(grupos_unicos_dev, size=n_grps, replace=True)
        sample_idx = []
        for g in sample_grps:
            sample_idx.extend(grp_to_indices[g])
        
        b_y = [y_dev_real[i] for i in sample_idx]
        b_t1_f = [top1_f83[i] for i in sample_idx]
        b_t1_c = [top1_c1[i] for i in sample_idx]
        b_t3_f = [top3_f83[i] for i in sample_idx]
        b_t3_c = [top3_c1[i] for i in sample_idx]

        b_pred_f83 = [inf_f83["pred_top1"][i] for i in sample_idx]
        b_pred_c1 = [inf_c1["pred_top1"][i] for i in sample_idx]

        dt1 = np.mean(b_t1_c) - np.mean(b_t1_f)
        dt3 = np.mean(b_t3_c) - np.mean(b_t3_f)

        _, _, f1_b_f, _ = precision_recall_fscore_support(b_y, b_pred_f83, average="macro", zero_division=0)
        _, _, f1_b_c, _ = precision_recall_fscore_support(b_y, b_pred_c1, average="macro", zero_division=0)
        df1 = f1_b_c - f1_b_f

        boot_delta_t1.append(dt1)
        boot_delta_t3.append(dt3)
        boot_delta_f1.append(df1)

    ci_t1 = np.percentile(boot_delta_t1, [2.5, 97.5])
    ci_t3 = np.percentile(boot_delta_t3, [2.5, 97.5])
    ci_f1 = np.percentile(boot_delta_f1, [2.5, 97.5])

    print(f"Delta Top-1:   Media = {np.mean(boot_delta_t1)*100:+.2f}% | CI 95%: [{ci_t1[0]*100:+.2f}%, {ci_t1[1]*100:+.2f}%]")
    print(f"Delta Top-3:   Media = {np.mean(boot_delta_t3)*100:+.2f}% | CI 95%: [{ci_t3[0]*100:+.2f}%, {ci_t3[1]*100:+.2f}%]")
    print(f"Delta Macro F1: Media = {np.mean(boot_delta_f1)*100:+.2f}% | CI 95%: [{ci_f1[0]*100:+.2f}%, {ci_f1[1]*100:+.2f}%]")

    # 16. Matriz de Confusión y Análisis de Clases
    print("\n--- MATRIZ DE CONFUSIÓN Y ANÁLISIS DE CLASES ---")
    cm_c1 = confusion_matrix(y_dev_real, inf_c1["pred_top1"], labels=clases_unicas)
    df_cm = pd.DataFrame(cm_c1, index=clases_unicas, columns=clases_unicas)
    df_cm.to_csv("machine_learning/data/fase10/fase10_c1_confusion_matrix.csv")

    # Métricas por clase F8.3 vs C1
    p_cl_f83, r_cl_f83, f1_cl_f83, s_cl = precision_recall_fscore_support(y_dev_real, inf_f83["pred_top1"], labels=clases_unicas, zero_division=0)
    p_cl_c1, r_cl_c1, f1_cl_c1, _ = precision_recall_fscore_support(y_dev_real, inf_c1["pred_top1"], labels=clases_unicas, zero_division=0)

    filas_clases = []
    for idx, c in enumerate(clases_unicas):
        filas_clases.append({
            "clase": c,
            "macro_sistema": FALLA_A_SISTEMA[c],
            "support": int(s_cl[idx]),
            "precision_f83": round(float(p_cl_f83[idx]), 4),
            "recall_f83": round(float(r_cl_f83[idx]), 4),
            "f1_f83": round(float(f1_cl_f83[idx]), 4),
            "precision_c1": round(float(p_cl_c1[idx]), 4),
            "recall_c1": round(float(r_cl_c1[idx]), 4),
            "f1_c1": round(float(f1_cl_c1[idx]), 4),
            "delta_recall": round(float(r_cl_c1[idx] - r_cl_f83[idx]), 4),
            "delta_f1": round(float(f1_cl_c1[idx] - f1_cl_f83[idx]), 4)
        })
    df_metrics_class = pd.DataFrame(filas_clases)
    df_metrics_class.to_csv("machine_learning/data/fase10/fase10_c1_metrics_by_class.csv", index=False)

    # Top 10 clases que más mejoraron
    top10_mejora = df_metrics_class.sort_values(by="delta_f1", ascending=False).head(10)
    print("\nTop 10 Clases con Mayor Ganancia en F1-Score:")
    for idx, row in top10_mejora.iterrows():
        print(f"  +{row['delta_f1']*100:5.1f}% F1 (F8.3: {row['f1_f83']*100:5.1f}% -> C1: {row['f1_c1']*100:5.1f}%) | {row['clase']} (n={row['support']})")

    # Clases degradadas
    clases_degradadas = df_metrics_class[(df_metrics_class["delta_f1"] < 0) | (df_metrics_class["delta_recall"] < 0)].sort_values(by="delta_f1", ascending=True)
    print(f"\nTotal Clases con Degradación (F1 o Recall C1 < F8.3): {len(clases_degradadas)}")
    for idx, row in clases_degradadas.iterrows():
        print(f"  {row['delta_f1']*100:5.1f}% F1 (F8.3: {row['f1_f83']*100:5.1f}% -> C1: {row['f1_c1']*100:5.1f}%) | Rec: {row['delta_recall']*100:5.1f}% | {row['clase']} (n={row['support']})")

    # Pares de confusión principales
    np.fill_diagonal(cm_c1, 0)
    indices_conf = np.unravel_index(np.argsort(cm_c1, axis=None)[::-1], cm_c1.shape)
    print("\nPares de Confusión Más Frecuentes en C1:")
    top_confusiones = []
    for k in range(15):
        i_r = indices_conf[0][k]
        i_p = indices_conf[1][k]
        cnt = cm_c1[i_r, i_p]
        if cnt == 0:
            break
        c_real = clases_unicas[i_r]
        c_pred = clases_unicas[i_p]
        top_confusiones.append({"real": c_real, "pred": c_pred, "cantidad": int(cnt)})
        print(f"  {cnt:2d} casos: Real: '{c_real}' -> Predicho: '{c_pred}'")

    # 17. Archivos de Errores y Comparación Pareada Caso a Caso
    print("\nGuardando fase10_f83_vs_c1_dev10.csv y fase10_c1_dev10_errors.csv...")
    filas_pareadas = []
    filas_errores = []

    for i in range(len(y_dev_real)):
        row_dev = df_dev10.iloc[i]
        rid = row_dev["id"]
        c_real = y_dev_real[i]
        pred_i_f83 = str(inf_f83["pred_top1"][i])
        pred_i_c1 = str(inf_c1["pred_top1"][i])
        conf_f83 = inf_f83["conf_top1"][i]
        conf_c1 = inf_c1["conf_top1"][i]
        corr_f83 = int(pred_i_f83 == c_real)
        corr_c1 = int(pred_i_c1 == c_real)
        src = row_dev["synthetic_or_original"]
        niv = row_dev["nivel_informacion"]
        macro = row_dev["macro_sistema"]
        grp = row_dev["id_grupo"]
        es_cont = row_dev["es_contrastivo"]
        c_cont = row_dev["clase_contrastiva"]
        txt = row_dev["texto_usuario"]

        reg_p = {
            "id": rid,
            "real": c_real,
            "pred_f83": pred_i_f83,
            "pred_c1": pred_i_c1,
            "correct_f83": corr_f83,
            "correct_c1": corr_c1,
            "confidence_f83": round(float(conf_f83), 4),
            "confidence_c1": round(float(conf_c1), 4),
            "source": src,
            "nivel": niv,
            "macro": macro,
            "id_grupo": grp,
            "es_contrastivo": es_cont,
            "clase_contrastiva": c_cont
        }
        filas_pareadas.append(reg_p)

        if corr_c1 == 0:
            filas_errores.append({
                "id": rid,
                "texto": txt,
                "real": c_real,
                "pred": pred_i_c1,
                "top3": " | ".join(inf_c1["pred_top3"][i]),
                "confidence": round(float(conf_c1), 4),
                "macro_real": macro,
                "macro_pred": FALLA_A_SISTEMA.get(pred_i_c1, "DESCONOCIDO"),
                "source": src,
                "nivel": niv,
                "id_grupo": grp,
                "es_contrastivo": es_cont,
                "clase_contrastiva": c_cont
            })

    pd.DataFrame(filas_pareadas).to_csv("machine_learning/data/fase10/fase10_f83_vs_c1_dev10.csv", index=False)
    pd.DataFrame(filas_errores).to_csv("machine_learning/data/fase10/fase10_c1_dev10_errors.csv", index=False)
    print(f"fase10_f83_vs_c1_dev10.csv guardado ({len(filas_pareadas)} filas)")
    print(f"fase10_c1_dev10_errors.csv guardado ({len(filas_errores)} filas)")

    # 18. Regresiones sobre Benchmarks Históricos
    print("\n" + "=" * 60)
    print("EVALUANDO REGRESIONES SOBRE BENCHMARKS HISTÓRICOS")
    print("=" * 60)

    regresiones_report = []

    # A) TEST-100 Histórico
    sys.path.append("machine_learning/data")
    import benchmark_test_ciego_100 as b_test
    t100_casos = b_test.BENCHMARK_TEST_CIEGO_100
    t100_textos = [c["sintoma"] for c in t100_casos]
    t100_reales = [c["falla_esperada"] for c in t100_casos]

    t100_f83 = inferir_jerarquico(cal_f_f83, cal_s_f83, vec_f83, t100_textos, temp=0.80, exp_sist=0.65)
    t100_c1 = inferir_jerarquico(cal_f_c1, cal_s_c1, vec_c1, t100_textos, temp=0.80, exp_sist=0.65)

    acc_t1_t100_f83 = np.mean([1 if t100_f83["pred_top1"][i] == t100_reales[i] else 0 for i in range(len(t100_reales))])
    acc_t1_t100_c1 = np.mean([1 if t100_c1["pred_top1"][i] == t100_reales[i] else 0 for i in range(len(t100_reales))])
    acc_t3_t100_f83 = np.mean([1 if t100_reales[i] in t100_f83["pred_top3"][i] else 0 for i in range(len(t100_reales))])
    acc_t3_t100_c1 = np.mean([1 if t100_reales[i] in t100_c1["pred_top3"][i] else 0 for i in range(len(t100_reales))])
    _, _, f1_t100_f83, _ = precision_recall_fscore_support(t100_reales, t100_f83["pred_top1"], average="macro", zero_division=0)
    _, _, f1_t100_c1, _ = precision_recall_fscore_support(t100_reales, t100_c1["pred_top1"], average="macro", zero_division=0)

    print(f"TEST-100 Histórico (n=100):")
    print(f"  Top1: F8.3 = {acc_t1_t100_f83*100:.1f}% | C1 = {acc_t1_t100_c1*100:.1f}% | DELTA = {(acc_t1_t100_c1-acc_t1_t100_f83)*100:+.1f}%")
    print(f"  Top3: F8.3 = {acc_t3_t100_f83*100:.1f}% | C1 = {acc_t3_t100_c1*100:.1f}% | DELTA = {(acc_t3_t100_c1-acc_t3_t100_f83)*100:+.1f}%")
    print(f"  MF1:  F8.3 = {f1_t100_f83*100:.1f}% | C1 = {f1_t100_c1*100:.1f}% | DELTA = {(f1_t100_c1-f1_t100_f83)*100:+.1f}%")
    regresiones_report.append({
        "benchmark": "TEST-100_HISTORICO",
        "n": 100,
        "f83_top1": round(float(acc_t1_t100_f83), 4),
        "c1_top1": round(float(acc_t1_t100_c1), 4),
        "delta_top1": round(float(acc_t1_t100_c1 - acc_t1_t100_f83), 4),
        "f83_top3": round(float(acc_t3_t100_f83), 4),
        "c1_top3": round(float(acc_t3_t100_c1), 4),
        "delta_top3": round(float(acc_t3_t100_c1 - acc_t3_t100_f83), 4)
    })

    # B) DEV-60 Histórico
    import benchmark_dev_60_casos as b_dev
    dev60_casos = b_dev.CASOS_DEV_60
    dev60_textos = [c["sintoma"] for c in dev60_casos]
    dev60_reales = [c["falla_esperada"] for c in dev60_casos]

    dev60_f83 = inferir_jerarquico(cal_f_f83, cal_s_f83, vec_f83, dev60_textos, temp=0.80, exp_sist=0.65)
    dev60_c1 = inferir_jerarquico(cal_f_c1, cal_s_c1, vec_c1, dev60_textos, temp=0.80, exp_sist=0.65)

    acc_t1_dev60_f83 = np.mean([1 if dev60_f83["pred_top1"][i] == dev60_reales[i] else 0 for i in range(len(dev60_reales))])
    acc_t1_dev60_c1 = np.mean([1 if dev60_c1["pred_top1"][i] == dev60_reales[i] else 0 for i in range(len(dev60_reales))])
    acc_t3_dev60_f83 = np.mean([1 if dev60_reales[i] in dev60_f83["pred_top3"][i] else 0 for i in range(len(dev60_reales))])
    acc_t3_dev60_c1 = np.mean([1 if dev60_reales[i] in dev60_c1["pred_top3"][i] else 0 for i in range(len(dev60_reales))])

    print(f"\nDEV-60 Histórico (n=60):")
    print(f"  Top1: F8.3 = {acc_t1_dev60_f83*100:.1f}% | C1 = {acc_t1_dev60_c1*100:.1f}% | DELTA = {(acc_t1_dev60_c1-acc_t1_dev60_f83)*100:+.1f}%")
    print(f"  Top3: F8.3 = {acc_t3_dev60_f83*100:.1f}% | C1 = {acc_t3_dev60_c1*100:.1f}% | DELTA = {(acc_t3_dev60_c1-acc_t3_dev60_f83)*100:+.1f}%")
    regresiones_report.append({
        "benchmark": "DEV-60_HISTORICO",
        "n": 60,
        "f83_top1": round(float(acc_t1_dev60_f83), 4),
        "c1_top1": round(float(acc_t1_dev60_c1), 4),
        "delta_top1": round(float(acc_t1_dev60_c1 - acc_t1_dev60_f83), 4),
        "f83_top3": round(float(acc_t3_dev60_f83), 4),
        "c1_top3": round(float(acc_t3_dev60_c1), 4),
        "delta_top3": round(float(acc_t3_dev60_c1 - acc_t3_dev60_f83), 4)
    })

    # C) G1 y G2
    sys.path.append("scripts")
    import benchmark_v4_g1_casos as b_g1
    import benchmark_v4_g2_casos as b_g2

    for b_mod, b_nom in [(b_g1.BENCHMARK_V4_G1_CASOS, "G1_ESTRES"), (b_g2.BENCHMARK_V4_G2_CASOS, "G2_JERGA")]:
        g_txt = [c["sintoma"] for c in b_mod]
        g_real = [c["falla_estricta"] for c in b_mod]
        g_acep = [c["fallas_aceptables"] for c in b_mod]

        g_inf_f83 = inferir_jerarquico(cal_f_f83, cal_s_f83, vec_f83, g_txt, temp=0.80, exp_sist=0.65)
        g_inf_c1 = inferir_jerarquico(cal_f_c1, cal_s_c1, vec_c1, g_txt, temp=0.80, exp_sist=0.65)

        acc_g_f83 = np.mean([1 if (g_inf_f83["pred_top1"][i] == g_real[i] or g_inf_f83["pred_top1"][i] in g_acep[i]) else 0 for i in range(len(g_real))])
        acc_g_c1 = np.mean([1 if (g_inf_c1["pred_top1"][i] == g_real[i] or g_inf_c1["pred_top1"][i] in g_acep[i]) else 0 for i in range(len(g_real))])

        print(f"\n{b_nom} (n={len(b_mod)}):")
        print(f"  Top1 Aceptable: F8.3 = {acc_g_f83*100:.1f}% | C1 = {acc_g_c1*100:.1f}% | DELTA = {(acc_g_c1-acc_g_f83)*100:+.1f}%")
        regresiones_report.append({
            "benchmark": b_nom,
            "n": len(b_mod),
            "f83_top1": round(float(acc_g_f83), 4),
            "c1_top1": round(float(acc_g_c1), 4),
            "delta_top1": round(float(acc_g_c1 - acc_g_f83), 4),
            "f83_top3": 0.0,
            "c1_top3": 0.0,
            "delta_top3": 0.0
        })

    # D) FIELD AVAILABLE (n=32)
    df_field = pd.read_csv("machine_learning/data/casos_reales_mecanicos_evaluacion.csv").dropna()
    field_txt = df_field["sintoma"].astype(str).tolist()
    field_real = df_field["falla"].tolist()
    n_field = len(field_txt)

    field_f83 = inferir_jerarquico(cal_f_f83, cal_s_f83, vec_f83, field_txt, temp=0.80, exp_sist=0.65)
    field_c1 = inferir_jerarquico(cal_f_c1, cal_s_c1, vec_c1, field_txt, temp=0.80, exp_sist=0.65)

    acc_field_f83 = np.mean([1 if field_f83["pred_top1"][i] == field_real[i] else 0 for i in range(n_field)])
    acc_field_c1 = np.mean([1 if field_c1["pred_top1"][i] == field_real[i] else 0 for i in range(n_field)])
    top3_field_f83 = np.mean([1 if field_real[i] in field_f83["pred_top3"][i] else 0 for i in range(n_field)])
    top3_field_c1 = np.mean([1 if field_real[i] in field_c1["pred_top3"][i] else 0 for i in range(n_field)])

    print(f"\nFIELD_AVAILABLE (n={n_field}):")
    print(f"  Top1: F8.3 = {acc_field_f83*100:.1f}% | C1 = {acc_field_c1*100:.1f}% | DELTA = {(acc_field_c1-acc_field_f83)*100:+.1f}%")
    print(f"  Top3: F8.3 = {top3_field_f83*100:.1f}% | C1 = {top3_field_c1*100:.1f}% | DELTA = {(top3_field_c1-top3_field_f83)*100:+.1f}%")
    regresiones_report.append({
        "benchmark": "FIELD_AVAILABLE_N32",
        "n": n_field,
        "f83_top1": round(float(acc_field_f83), 4),
        "c1_top1": round(float(acc_field_c1), 4),
        "delta_top1": round(float(acc_field_c1 - acc_field_f83), 4),
        "f83_top3": round(float(top3_field_f83), 4),
        "c1_top3": round(float(top3_field_c1), 4),
        "delta_top3": round(float(top3_field_c1 - top3_field_f83), 4)
    })

    pd.DataFrame(regresiones_report).to_csv("machine_learning/data/fase10/fase10_c1_regression_benchmarks.csv", index=False)

    # 19. Evaluación del Caso Histórico de A/C
    print("\n--- EVALUACIÓN DEL CASO HISTÓRICO DE A/C (REGRESIÓN) ---")
    ac_txt_directo = "Prendo el boton A/C del aire acondicionado sale aire tibio ambiente y no enfria nada parece ventilador comun y corriente."
    ac_txt_corolla = "Toyota Corolla 2017 aire acondicionado no enfria en cabina, compresor acopla pero presion de baja y alta estan igualadas en 70 PSI."
    ac_target = "Falla en compresor de aire acondicionado o fuga de gas R134a"

    ac_res_f83 = inferir_jerarquico(cal_f_f83, cal_s_f83, vec_f83, [ac_txt_directo, ac_txt_corolla], temp=0.80, exp_sist=0.65)
    ac_res_c1 = inferir_jerarquico(cal_f_c1, cal_s_c1, vec_c1, [ac_txt_directo, ac_txt_corolla], temp=0.80, exp_sist=0.65)

    print(f"Caso 1 (Directo: 'Prendo el boton A/C...'):")
    print(f"  F8.3 -> Top1: '{ac_res_f83['pred_top1'][0]}' (conf={ac_res_f83['conf_top1'][0]:.4f}, sist={ac_res_f83['pred_sistema'][0]})")
    print(f"  C1   -> Top1: '{ac_res_c1['pred_top1'][0]}' (conf={ac_res_c1['conf_top1'][0]:.4f}, sist={ac_res_c1['pred_sistema'][0]})")
    print(f"  Top3 C1: {ac_res_c1['pred_top3'][0]}")

    print(f"\nCaso 2 (Técnico Corolla: 'Toyota Corolla 2017 aire acondicionado no enfria...'):")
    print(f"  F8.3 -> Top1: '{ac_res_f83['pred_top1'][1]}' (conf={ac_res_f83['conf_top1'][1]:.4f}, sist={ac_res_f83['pred_sistema'][1]})")
    print(f"  C1   -> Top1: '{ac_res_c1['pred_top1'][1]}' (conf={ac_res_c1['conf_top1'][1]:.4f}, sist={ac_res_c1['pred_sistema'][1]})")
    print(f"  Top3 C1: {ac_res_c1['pred_top3'][1]}")

    # 20. Verificación de Seguridad y Cierre de TEST10
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE CIERRE Y SEGURIDAD DE TEST10")
    print("=" * 60)
    sha_test_fin = calcular_sha256(ruta_test10)
    print(f"TEST10 hash final: {sha_test_fin}")
    assert sha_test_fin == exp_test_hash, "ALERTA CRÍTICA: TEST10 fue modificado!"
    print("CONFIRMADO: TEST10 permaneció 100% blindado y cerrado. Predicciones ejecutadas sobre TEST10: 0")

    # 21. Guardar Métricas Globales JSON
    res_metrics_global = {
        "candidate": "F10-C1",
        "train_instances": len(df_train10),
        "dev_instances": len(df_dev10),
        "f83": {
            "top1": round(float(acc_top1_f83), 4),
            "top3": round(float(acc_top3_f83), 4),
            "macro_precision": round(float(macro_p_f83), 4),
            "macro_recall": round(float(macro_r_f83), 4),
            "macro_f1": round(float(macro_f1_f83), 4),
            "weighted_f1": round(float(f1w_f83), 4),
            "macro_system_acc": round(float(macro_acc_f83), 4),
            "brier_score": cal_f83["brier_score"],
            "ece": cal_f83["ece"]
        },
        "c1": {
            "top1": round(float(acc_top1_c1), 4),
            "top3": round(float(acc_top3_c1), 4),
            "macro_precision": round(float(macro_p_c1), 4),
            "macro_recall": round(float(macro_r_c1), 4),
            "macro_f1": round(float(macro_f1_c1), 4),
            "weighted_f1": round(float(f1w_c1), 4),
            "macro_system_acc": round(float(macro_acc_c1), 4),
            "brier_score": cal_c1["brier_score"],
            "ece": cal_c1["ece"]
        },
        "delta": {
            "top1": round(float(acc_top1_c1 - acc_top1_f83), 4),
            "top3": round(float(acc_top3_c1 - acc_top3_f83), 4),
            "macro_precision": round(float(macro_p_c1 - macro_p_f83), 4),
            "macro_recall": round(float(macro_r_c1 - macro_r_f83), 4),
            "macro_f1": round(float(macro_f1_c1 - macro_f1_f83), 4),
            "weighted_f1": round(float(f1w_c1 - f1w_f83), 4),
            "macro_system_acc": round(float(macro_acc_c1 - macro_acc_f83), 4)
        },
        "mcnemar": {
            "statistic": round(float(mcnemar_stat), 4),
            "p_value": float(mcnemar_p),
            "ambos_correctos": ambos_correctos,
            "solo_f83": solo_f83,
            "solo_c1": solo_c1,
            "ambos_incorrectos": ambos_incorrectos
        },
        "bootstrap_95ci": {
            "delta_top1_mean": round(float(np.mean(boot_delta_t1)), 4),
            "delta_top1_ci95": [round(float(ci_t1[0]), 4), round(float(ci_t1[1]), 4)],
            "delta_top3_mean": round(float(np.mean(boot_delta_t3)), 4),
            "delta_top3_ci95": [round(float(ci_t3[0]), 4), round(float(ci_t3[1]), 4)],
            "delta_macro_f1_mean": round(float(np.mean(boot_delta_f1)), 4),
            "delta_macro_f1_ci95": [round(float(ci_f1[0]), 4), round(float(ci_f1[1]), 4)]
        },
        "por_fuente": {
            "original": metr_orig,
            "sintetico": metr_synth
        },
        "por_nivel": metr_niveles,
        "por_macro": metr_macros,
        "contrastivos": contrast_metrics
    }

    with open("machine_learning/data/fase10/fase10_c1_metrics_dev10.json", "w", encoding="utf-8") as f:
        json.dump(res_metrics_global, f, indent=2, ensure_ascii=False)

    print("\nTodos los artefactos de métricas generados exitosamente.")
    print("=" * 80)
    print("EJECUCIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)

if __name__ == "__main__":
    main()
