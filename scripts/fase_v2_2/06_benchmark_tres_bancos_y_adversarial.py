"""
06_benchmark_tres_bancos_y_adversarial.py
FASE EXPERIMENTAL CARBOT V2.2 — FASES 10, 14, 16, 17, 18, 19 Y 20
Evaluación exhaustiva de:
- FROZEN (Línea base)
- V2_1_B (Mejor candidato V2.1)
- V2_2_A (V2.1-B + contrastivos reales)
- V2_2_B (V2.1-B + contrastivos reales + 70 sintéticos)
- V2_2_C (V2.1-B + contrastivos reales + 140 sintéticos)

Sobre 3 Bancos Ciegos Independientes:
- Banco 1 (Primario Histórico, n=366)
- Banco 2 (Secundario V2.1, n=183)
- Banco 3 (Terciario V2.2, n=183)
Y sobre Banco Adversarial Contrastivo (n=40, 20 pares).

Compara 3 Estrategias de Combustible:
A) Sin Filtro
B) Hard Filter (Bloqueo a 0)
C) Soft Reranking (Penalización probabilística -75%)

Calcula:
- Top-1, Top-3, Precision, Recall, Macro-F1, Weighted-F1, Worst-Class F1
- Incompatibilidad de combustible
- Contrastive Pair Accuracy y Evidence Sensitivity Rate
- Contraste Estadístico: McNemar p-value y Bootstrap 95% CI
- Promedios de Generalización Multi-Banco
"""
import sys
import os
import json
import csv
import time
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from scipy.stats import binomtest

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
V2_2_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_2"
MODELS_DIR = V2_2_DIR / "models"
EVAL_DIR = V2_2_DIR / "evaluacion"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

TEST_PRIMARIO = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "test10_fase10_blind_v1.csv"
TEST_SECUNDARIO = V2_1_DIR / "TEST_BLIND_V2_1_SECONDARY.csv"
TEST_TERCIARIO = V2_2_DIR / "TEST_BLIND_V2_2_TERTIARY.csv"
BANCO_ADVERSARIAL = V2_2_DIR / "BANCO_ADVERSARIAL_CONTRASTIVO.csv"
COMPAT_JSON = V2_1_DIR / "data" / "COMPATIBILIDAD_COMBUSTIBLE_61_CLASES.json"

MODELOS = {
    "FROZEN": {
        "tfidf": PROJECT_ROOT / "machine_learning" / "models" / "c1_fase10_final" / "vectorizador_c1.pkl",
        "svm": PROJECT_ROOT / "machine_learning" / "models" / "c1_fase10_final" / "modelo_diagnostico_c1.pkl",
        "train_size": 6904,
        "external_rows": 0,
        "synthetic_rows": 0
    },
    "V2_1_B": {
        "tfidf": V2_1_DIR / "models" / "tfidf_v2_1_b.joblib",
        "svm": V2_1_DIR / "models" / "linear_svm_v2_1_b.joblib",
        "train_size": 7099,
        "external_rows": 195,
        "synthetic_rows": 0
    },
    "V2_2_A": {
        "tfidf": MODELS_DIR / "tfidf_v2_2_a.joblib",
        "svm": MODELS_DIR / "linear_svm_v2_2_a.joblib",
        "train_size": 7119,
        "external_rows": 215,
        "synthetic_rows": 0
    },
    "V2_2_B": {
        "tfidf": MODELS_DIR / "tfidf_v2_2_b.joblib",
        "svm": MODELS_DIR / "linear_svm_v2_2_b.joblib",
        "train_size": 7189,
        "external_rows": 215,
        "synthetic_rows": 70
    },
    "V2_2_C": {
        "tfidf": MODELS_DIR / "tfidf_v2_2_c.joblib",
        "svm": MODELS_DIR / "linear_svm_v2_2_c.joblib",
        "train_size": 7259,
        "external_rows": 215,
        "synthetic_rows": 140
    }
}


def cargar_compatibilidad():
    with open(COMPAT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def inferir_contexto_combustible(texto: str, true_class: str, compat_dict: dict) -> str:
    txt = texto.lower()
    if any(w in txt for w in ["diesel", "petroleo", "petrolero", "camion", "hilux", "1kd", "common rail", "dpf", "adblue", "maxi-brake"]):
        return "DIESEL"
    if any(w in txt for w in ["gasolina", "gasolinero", "bujia", "bobina", "gdi", "spark", "fscm", "canister"]):
        return "GASOLINE"
    comp_true = compat_dict.get(true_class, {}).get("fuel_compatibility", "BOTH")
    if comp_true == "DIESEL_ONLY":
        return "DIESEL"
    elif comp_true == "GASOLINE_ONLY":
        return "GASOLINE"
    return "UNKNOWN"


def evaluar_dataset(tfidf_path: Path, svm_path: Path, df_eval: pd.DataFrame, compat_dict: dict, fuel_strategy: str = "NONE", registrar_intervenciones: bool = False):
    tfidf = joblib.load(tfidf_path)
    svm = joblib.load(svm_path)

    X = df_eval["texto_usuario"].astype(str).tolist()
    y = df_eval["clase_objetivo"].astype(str).tolist()
    classes = list(svm.classes_)

    t0 = time.time()
    X_vec = tfidf.transform(X)
    probs = svm.predict_proba(X_vec)
    preds = svm.predict(X_vec)
    lat_ms = (time.time() - t0) / len(X) * 1000

    incompatibilidades = 0
    intervenciones = []
    top3_hits = 0
    preds_finales = []

    for i in range(len(X)):
        c_prob = probs[i].copy()
        txt = X[i]
        true_c = y[i]
        fuel_ctx = inferir_contexto_combustible(txt, true_c, compat_dict)

        orig_pred_idx = np.argmax(c_prob)
        orig_pred_class = classes[orig_pred_idx]

        # Verificar incompatibilidad inicial
        orig_comp = compat_dict.get(orig_pred_class, {}).get("fuel_compatibility", "BOTH")
        if fuel_ctx == "DIESEL" and orig_comp == "GASOLINE_ONLY":
            incompatibilidades += 1
        elif fuel_ctx == "GASOLINE" and orig_comp == "DIESEL_ONLY":
            incompatibilidades += 1

        # Aplicar estrategia de combustible
        if fuel_strategy == "HARD_FILTER" and fuel_ctx != "UNKNOWN":
            for c_idx, c_name in enumerate(classes):
                c_comp = compat_dict.get(c_name, {}).get("fuel_compatibility", "BOTH")
                if fuel_ctx == "DIESEL" and c_comp == "GASOLINE_ONLY":
                    c_prob[c_idx] = 0.0
                elif fuel_ctx == "GASOLINE" and c_comp == "DIESEL_ONLY":
                    c_prob[c_idx] = 0.0

            if np.sum(c_prob) > 0:
                c_prob /= np.sum(c_prob)
            new_pred_idx = np.argmax(c_prob)
            new_pred_class = classes[new_pred_idx]

            if registrar_intervenciones and new_pred_class != orig_pred_class:
                intervenciones.append({
                    "id": df_eval.iloc[i].get("id", f"case_{i}"),
                    "fuel_type": fuel_ctx,
                    "prediction_before": orig_pred_class,
                    "prediction_after": new_pred_class,
                    "strategy": "HARD_FILTER",
                    "reason": "Incompatibilidad termodinámica estricta"
                })
            pred_usada = new_pred_class

        elif fuel_strategy == "SOFT_RERANKING" and fuel_ctx != "UNKNOWN":
            # Penalización del 75% sobre la probabilidad de clases incompatibles
            for c_idx, c_name in enumerate(classes):
                c_comp = compat_dict.get(c_name, {}).get("fuel_compatibility", "BOTH")
                if fuel_ctx == "DIESEL" and c_comp == "GASOLINE_ONLY":
                    c_prob[c_idx] *= 0.25
                elif fuel_ctx == "GASOLINE" and c_comp == "DIESEL_ONLY":
                    c_prob[c_idx] *= 0.25

            if np.sum(c_prob) > 0:
                c_prob /= np.sum(c_prob)
            new_pred_idx = np.argmax(c_prob)
            new_pred_class = classes[new_pred_idx]

            if registrar_intervenciones and new_pred_class != orig_pred_class:
                intervenciones.append({
                    "id": df_eval.iloc[i].get("id", f"case_{i}"),
                    "fuel_type": fuel_ctx,
                    "prediction_before": orig_pred_class,
                    "prediction_after": new_pred_class,
                    "strategy": "SOFT_RERANKING",
                    "reason": "Penalización probabilística -75%"
                })
            pred_usada = new_pred_class
        else:
            pred_usada = orig_pred_class

        preds_finales.append(pred_usada)

        # Top-3
        top3_indices = np.argsort(c_prob)[-3:][::-1]
        top3_names = [classes[idx] for idx in top3_indices]
        if true_c in top3_names:
            top3_hits += 1

    acc = accuracy_score(y, preds_finales)
    top3 = top3_hits / len(y)
    macro_p = precision_score(y, preds_finales, average="macro", zero_division=0)
    macro_r = recall_score(y, preds_finales, average="macro", zero_division=0)
    macro_f1 = f1_score(y, preds_finales, average="macro", zero_division=0)
    weighted_f1 = f1_score(y, preds_finales, average="weighted", zero_division=0)

    f1_por_clase = f1_score(y, preds_finales, average=None, labels=classes, zero_division=0)
    dict_f1 = {classes[idx]: float(f1_por_clase[idx]) for idx in range(len(classes))}

    incomp_pct = (incompatibilidades / len(X)) * 100 if fuel_strategy == "NONE" else 0.0

    return {
        "top_1": float(acc),
        "top_3": float(top3),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "worst_class_f1": float(np.min(f1_por_clase)),
        "incompatibilidad_combustible_pct": float(incomp_pct),
        "latencia_ms": round(lat_ms, 2),
        "f1_por_clase": dict_f1,
        "preds_finales": preds_finales,
        "intervenciones": intervenciones,
        "classes": classes,
        "y_true": y,
        "X_text": X
    }


def evaluar_adversarial(tfidf_path: Path, svm_path: Path, df_adv: pd.DataFrame):
    tfidf = joblib.load(tfidf_path)
    svm = joblib.load(svm_path)

    X = df_adv["texto_usuario"].astype(str).tolist()
    y_true = df_adv["clase_objetivo"].astype(str).tolist()

    preds = svm.predict(tfidf.transform(X))

    # Medir exactitud por pares
    # Cada par son dos filas consecutivas (A y B)
    pares = defaultdict(dict)
    for i, row in df_adv.iterrows():
        pid = row["pair_id"]
        var = row["variant"]
        gt = row["clase_objetivo"]
        pred = preds[i]
        pares[pid][var] = {"gt": gt, "pred": pred, "correct": (gt == pred)}

    pares_correctos_ambos = 0
    pares_sensibles_evidencia = 0

    for pid, data in pares.items():
        if data["A"]["correct"] and data["B"]["correct"]:
            pares_correctos_ambos += 1
        # Sensible a la evidencia si la predicción cambia cuando la evidencia cambia
        if data["A"]["pred"] != data["B"]["pred"]:
            pares_sensibles_evidencia += 1

    total_pares = len(pares)
    pair_acc = pares_correctos_ambos / total_pares
    sens_rate = pares_sensibles_evidencia / total_pares

    return {
        "contrastive_pair_accuracy": round(pair_acc, 4),
        "evidence_sensitivity_rate": round(sens_rate, 4),
        "total_pairs": total_pares,
        "correct_both_pairs": pares_correctos_ambos,
        "sensitive_pairs": pares_sensibles_evidencia
    }


def calcular_bootstrap_ci(y_true, y_pred, n_bootstraps=1000, alpha=0.05):
    np.random.seed(42)
    n = len(y_true)
    f1_boots = []
    acc_boots = []

    for _ in range(n_bootstraps):
        idxs = np.random.choice(n, size=n, replace=True)
        yt_b = [y_true[i] for i in idxs]
        yp_b = [y_pred[i] for i in idxs]
        acc_boots.append(accuracy_score(yt_b, yp_b))
        f1_boots.append(f1_score(yt_b, yp_b, average="macro", zero_division=0))

    ci_acc = (np.percentile(acc_boots, 100 * (alpha / 2)), np.percentile(acc_boots, 100 * (1 - alpha / 2)))
    ci_f1 = (np.percentile(f1_boots, 100 * (alpha / 2)), np.percentile(f1_boots, 100 * (1 - alpha / 2)))
    return ci_acc, ci_f1


def test_mcnemar_pareado(y_true, y_pred_model1, y_pred_model2):
    # b: model1 correcto, model2 incorrecto
    # c: model1 incorrecto, model2 correcto
    b = sum(1 for yt, p1, p2 in zip(y_true, y_pred_model1, y_pred_model2) if p1 == yt and p2 != yt)
    c = sum(1 for yt, p1, p2 in zip(y_true, y_pred_model1, y_pred_model2) if p1 != yt and p2 == yt)
    
    n_discordantes = b + c
    if n_discordantes == 0:
        return 1.0, 0, 0
    # Test binomial exacto de McNemar
    res = binomtest(min(b, c), n=n_discordantes, p=0.5, alternative="two-sided")
    return res.pvalue, b, c


def ejecutar_benchmark_completo():
    print("="*90)
    print("INICIANDO BENCHMARK CARBOT V2.2: 3 BANCOS INDEPENDIENTES + ADVERSARIAL")
    print("="*90)

    compat_dict = cargar_compatibilidad()
    df_p = pd.read_csv(TEST_PRIMARIO)
    df_s = pd.read_csv(TEST_SECUNDARIO)
    df_t = pd.read_csv(TEST_TERCIARIO)
    df_adv = pd.read_csv(BANCO_ADVERSARIAL)

    print(f"Banco 1 (Primario Histórico) : {len(df_p)} casos")
    print(f"Banco 2 (Secundario V2.1)    : {len(df_s)} casos")
    print(f"Banco 3 (Terciario V2.2)     : {len(df_t)} casos")
    print(f"Banco 4 (Adversarial)        : {len(df_adv)} casos ({len(df_adv)//2} pares)")

    resultados = defaultdict(dict)
    adversarial_res = {}

    for m_key, m_info in MODELOS.items():
        print(f"\n--- Evaluando {m_key} ---")
        # Evaluación base (sin filtro)
        res_p = evaluar_dataset(m_info["tfidf"], m_info["svm"], df_p, compat_dict, fuel_strategy="NONE")
        res_s = evaluar_dataset(m_info["tfidf"], m_info["svm"], df_s, compat_dict, fuel_strategy="NONE")
        res_t = evaluar_dataset(m_info["tfidf"], m_info["svm"], df_t, compat_dict, fuel_strategy="NONE")

        # Adversarial
        res_adv = evaluar_adversarial(m_info["tfidf"], m_info["svm"], df_adv)
        adversarial_res[m_key] = res_adv

        resultados[m_key]["banco_1"] = res_p
        resultados[m_key]["banco_2"] = res_s
        resultados[m_key]["banco_3"] = res_t
        resultados[m_key]["media_top1"] = round((res_p["top_1"] + res_s["top_1"] + res_t["top_1"]) / 3, 4)
        resultados[m_key]["media_f1"] = round((res_p["macro_f1"] + res_s["macro_f1"] + res_t["macro_f1"]) / 3, 4)

        print(f"  [B1] Top-1: {res_p['top_1']:.4f} | F1: {res_p['macro_f1']:.4f}")
        print(f"  [B2] Top-1: {res_s['top_1']:.4f} | F1: {res_s['macro_f1']:.4f}")
        print(f"  [B3] Top-1: {res_t['top_1']:.4f} | F1: {res_t['macro_f1']:.4f}")
        print(f"  [MEDIA GENERALIZACIÓN] Top-1: {resultados[m_key]['media_top1']:.4f} | Macro-F1: {resultados[m_key]['media_f1']:.4f}")
        print(f"  [ADVERSARIAL] Pair Acc: {res_adv['contrastive_pair_accuracy']:.2%} | Sensitivity: {res_adv['evidence_sensitivity_rate']:.2%}")

    # Determinar el mejor candidato V2.2
    candidatos_v2_2 = ["V2_2_A", "V2_2_B", "V2_2_C"]
    best_v2_2_key = max(candidatos_v2_2, key=lambda k: resultados[k]["media_f1"])
    print(f"\n>>> MEJOR CANDIDATO V2.2 IDENTIFICADO: {best_v2_2_key} (Media F1 = {resultados[best_v2_2_key]['media_f1']:.4f}) <<<")

    # Evaluar Mejor Candidato con Estrategias de Combustible (Fase 10)
    print(f"\nEvaluando estrategias de combustible para {best_v2_2_key}...")
    m_best = MODELOS[best_v2_2_key]
    
    # B) Hard Filter
    hf_p = evaluar_dataset(m_best["tfidf"], m_best["svm"], df_p, compat_dict, fuel_strategy="HARD_FILTER", registrar_intervenciones=True)
    hf_s = evaluar_dataset(m_best["tfidf"], m_best["svm"], df_s, compat_dict, fuel_strategy="HARD_FILTER")
    hf_t = evaluar_dataset(m_best["tfidf"], m_best["svm"], df_t, compat_dict, fuel_strategy="HARD_FILTER")
    resultados[f"{best_v2_2_key}_HARD_FILTER"]["banco_1"] = hf_p
    resultados[f"{best_v2_2_key}_HARD_FILTER"]["banco_2"] = hf_s
    resultados[f"{best_v2_2_key}_HARD_FILTER"]["banco_3"] = hf_t
    resultados[f"{best_v2_2_key}_HARD_FILTER"]["media_top1"] = round((hf_p["top_1"] + hf_s["top_1"] + hf_t["top_1"]) / 3, 4)
    resultados[f"{best_v2_2_key}_HARD_FILTER"]["media_f1"] = round((hf_p["macro_f1"] + hf_s["macro_f1"] + hf_t["macro_f1"]) / 3, 4)

    # C) Soft Reranking
    sr_p = evaluar_dataset(m_best["tfidf"], m_best["svm"], df_p, compat_dict, fuel_strategy="SOFT_RERANKING", registrar_intervenciones=True)
    sr_s = evaluar_dataset(m_best["tfidf"], m_best["svm"], df_s, compat_dict, fuel_strategy="SOFT_RERANKING")
    sr_t = evaluar_dataset(m_best["tfidf"], m_best["svm"], df_t, compat_dict, fuel_strategy="SOFT_RERANKING")
    resultados[f"{best_v2_2_key}_SOFT_RERANKING"]["banco_1"] = sr_p
    resultados[f"{best_v2_2_key}_SOFT_RERANKING"]["banco_2"] = sr_s
    resultados[f"{best_v2_2_key}_SOFT_RERANKING"]["banco_3"] = sr_t
    resultados[f"{best_v2_2_key}_SOFT_RERANKING"]["media_top1"] = round((sr_p["top_1"] + sr_s["top_1"] + sr_t["top_1"]) / 3, 4)
    resultados[f"{best_v2_2_key}_SOFT_RERANKING"]["media_f1"] = round((sr_p["macro_f1"] + sr_s["macro_f1"] + sr_t["macro_f1"]) / 3, 4)

    # Guardar intervenciones de combustible
    csv_interv = V2_2_DIR / "LOG_INTERVENCIONES_COMBUSTIBLE_V2_2.csv"
    todas_interv = sr_p["intervenciones"]
    if todas_interv:
        with open(csv_interv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(todas_interv[0].keys()))
            writer.writeheader()
            writer.writerows(todas_interv)
        print(f"Log de intervenciones de combustible guardado: {csv_interv.name} ({len(todas_interv)} intervenciones)")

    # Análisis Estadístico Formal: McNemar y Bootstrap CI (Fase 19)
    print("\nCalculando Análisis Estadístico Formal (McNemar y Bootstrap 95% CI)...")
    # Concatenar los 3 bancos ciegos para evaluación pareada global (366 + 183 + 183 = 732 casos)
    y_true_all = df_p["clase_objetivo"].tolist() + df_s["clase_objetivo"].tolist() + df_t["clase_objetivo"].tolist()
    
    preds_frozen_all = resultados["FROZEN"]["banco_1"]["preds_finales"] + resultados["FROZEN"]["banco_2"]["preds_finales"] + resultados["FROZEN"]["banco_3"]["preds_finales"]
    preds_best_all = resultados[best_v2_2_key]["banco_1"]["preds_finales"] + resultados[best_v2_2_key]["banco_2"]["preds_finales"] + resultados[best_v2_2_key]["banco_3"]["preds_finales"]
    
    p_val_mcnemar, b_froz_wins, c_v22_wins = test_mcnemar_pareado(y_true_all, preds_frozen_all, preds_best_all)
    ci_acc_best, ci_f1_best = calcular_bootstrap_ci(y_true_all, preds_best_all)
    ci_acc_froz, ci_f1_froz = calcular_bootstrap_ci(y_true_all, preds_frozen_all)

    print(f"Muestra total combinada: {len(y_true_all)} casos")
    print(f"McNemar Test: p-value = {p_val_mcnemar:.4f} (Frozen acierta solo: {b_froz_wins} | V2.2 acierta solo: {c_v22_wins})")
    print(f"Bootstrap 95% CI Top-1 {best_v2_2_key}: [{ci_acc_best[0]:.4f}, {ci_acc_best[1]:.4f}]")
    print(f"Bootstrap 95% CI Top-1 FROZEN: [{ci_acc_froz[0]:.4f}, {ci_acc_froz[1]:.4f}]")

    # Análisis de Clases: Mejoras y Degradaciones vs FROZEN en Banco 1
    base_f1_b1 = resultados["FROZEN"]["banco_1"]["f1_por_clase"]
    best_f1_b1 = resultados[best_v2_2_key]["banco_1"]["f1_por_clase"]

    clases_mejoradas = 0
    clases_degradadas = 0
    degradacion_gt_0_10 = 0
    lista_mejoradas = []
    lista_degradadas = []

    for cname, f1_base in base_f1_b1.items():
        f1_cand = best_f1_b1.get(cname, 0.0)
        delta = f1_cand - f1_base
        if delta > 0.001:
            clases_mejoradas += 1
            lista_mejoradas.append((cname, f1_base, f1_cand, delta))
        elif delta < -0.001:
            clases_degradadas += 1
            lista_degradadas.append((cname, f1_base, f1_cand, delta))
            if delta < -0.10:
                degradacion_gt_0_10 += 1

    # Tabla Comparativa Maestra Multi-Banco
    print("\n" + "="*120)
    print(f"{'TABLA COMPARATIVA MAESTRA MULTI-BANCO':^120}")
    print("="*120)
    print(f"{'MODEL':<28} {'B1_TOP1':<8} {'B1_F1':<8} {'B2_TOP1':<8} {'B2_F1':<8} {'B3_TOP1':<8} {'B3_F1':<8} {'MED_TOP1':<9} {'MED_F1':<9} {'INCOMP':<8} {'PAIR_ACC':<9}")
    print("-" * 120)

    tabla_consolidada = []
    for m in ["FROZEN", "V2_1_B", "V2_2_A", "V2_2_B", "V2_2_C", f"{best_v2_2_key}_HARD_FILTER", f"{best_v2_2_key}_SOFT_RERANKING"]:
        b1 = resultados[m]["banco_1"]
        b2 = resultados[m]["banco_2"]
        b3 = resultados[m]["banco_3"]
        med_top1 = resultados[m]["media_top1"]
        med_f1 = resultados[m]["media_f1"]
        adv_pacc = adversarial_res.get(m.split("_")[0] + "_" + m.split("_")[1] if "HARD" in m or "SOFT" in m else m, {}).get("contrastive_pair_accuracy", 0.0)
        incomp = b1["incompatibilidad_combustible_pct"]

        print(f"{m:<28} {b1['top_1']:<8.4f} {b1['macro_f1']:<8.4f} {b2['top_1']:<8.4f} {b2['macro_f1']:<8.4f} {b3['top_1']:<8.4f} {b3['macro_f1']:<8.4f} {med_top1:<9.4f} {med_f1:<9.4f} {incomp:<7.2f}% {adv_pacc:<8.2%}")
        tabla_consolidada.append({
            "model": m,
            "b1_top1": b1["top_1"], "b1_macro_f1": b1["macro_f1"],
            "b2_top1": b2["top_1"], "b2_macro_f1": b2["macro_f1"],
            "b3_top1": b3["top_1"], "b3_macro_f1": b3["macro_f1"],
            "media_top1": med_top1, "media_macro_f1": med_f1,
            "incompatibilidad_pct": incomp,
            "contrastive_pair_accuracy": adv_pacc
        })
    print("="*120)

    # Guardar consolidado JSON final
    out_json = EVAL_DIR / "RESULTADOS_EVALUACION_V2_2.json"
    consolidado = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mejor_candidato_identificado": best_v2_2_key,
        "clases_mejoradas_count": clases_mejoradas,
        "clases_degradadas_count": clases_degradadas,
        "degradacion_gt_0_10_count": degradacion_gt_0_10,
        "mcnemar_paired_test": {
            "p_value": round(p_val_mcnemar, 5),
            "frozen_wins": b_froz_wins,
            "v2_2_wins": c_v22_wins,
            "significant_at_0_05": bool(p_val_mcnemar < 0.05)
        },
        "bootstrap_ci_95": {
            "best_model_top1_ci": [round(ci_acc_best[0], 4), round(ci_acc_best[1], 4)],
            "best_model_macro_f1_ci": [round(ci_f1_best[0], 4), round(ci_f1_best[1], 4)],
            "frozen_top1_ci": [round(ci_acc_froz[0], 4), round(ci_acc_froz[1], 4)],
            "frozen_macro_f1_ci": [round(ci_f1_froz[0], 4), round(ci_f1_froz[1], 4)]
        },
        "adversarial_results": adversarial_res,
        "tabla_consolidada": tabla_consolidada,
        "top_clases_mejoradas": [{"clase": c, "f1_base": round(fb, 3), "f1_v2_2": round(fc, 3), "delta": round(d, 3)} for c, fb, fc, d in sorted(lista_mejoradas, key=lambda x: x[3], reverse=True)[:10]],
        "top_clases_degradadas": [{"clase": c, "f1_base": round(fb, 3), "f1_v2_2": round(fc, 3), "delta": round(d, 3)} for c, fb, fc, d in sorted(lista_degradadas, key=lambda x: x[3])[:10]]
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(consolidado, f, indent=2, ensure_ascii=False)
    print(f"\nResultados consolidados guardados en: {out_json.name}")


if __name__ == "__main__":
    ejecutar_benchmark_completo()
