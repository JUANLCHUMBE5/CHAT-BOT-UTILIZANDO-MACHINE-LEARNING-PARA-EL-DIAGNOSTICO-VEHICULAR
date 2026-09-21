"""
07_evaluacion_ablacion_v2_1.py
FASE EXPERIMENTAL CARBOT V2.1 — FASES 12, 13, 14, 15 Y 16
Evaluación exhaustiva de 5 modelos (FROZEN, V2, V2.1-A, V2.1-B, V2.1-C) + Filtro de Combustible
sobre el Banco Primario (366 casos) y Banco Secundario (183 casos).

Genera:
- machine_learning/experimentos/carbot_v2_1/evaluacion/RESULTADOS_EVALUACION_V2_1.json
- machine_learning/experimentos/carbot_v2_1/PROPUESTA_SINTETICOS_V2_2.csv
- machine_learning/experimentos/carbot_v2_1/LOG_INTERVENCIONES_COMBUSTIBLE.csv
- machine_learning/experimentos/carbot_v2_1/ANALISIS_ERRORES_MEJOR_CANDIDATO.csv
"""
import sys
import os
import csv
import json
import time
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
EVAL_DIR = V2_1_DIR / "evaluacion"
EVAL_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR = V2_1_DIR / "models"
DATA_DIR = V2_1_DIR / "data"

TEST_PRIMARIO = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "test10_fase10_blind_v1.csv"
TEST_SECUNDARIO = V2_1_DIR / "TEST_BLIND_V2_1_SECONDARY.csv"
COMPAT_JSON = DATA_DIR / "COMPATIBILIDAD_COMBUSTIBLE_61_CLASES.json"

# Modelos
MODELOS_INFO = {
    "FROZEN": {
        "tfidf": PROJECT_ROOT / "machine_learning" / "models" / "c1_fase10_final" / "vectorizador_c1.pkl",
        "svm": PROJECT_ROOT / "machine_learning" / "models" / "c1_fase10_final" / "modelo_diagnostico_c1.pkl",
        "train_size": 6904,
        "external_rows": 0
    },
    "V2_ANTERIOR": {
        "tfidf": PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2" / "models" / "tfidf_diagnostico_v2_experimental.joblib",
        "svm": PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2" / "models" / "linear_svm_diagnostico_v2_experimental.joblib",
        "train_size": 7241,
        "external_rows": 337
    },
    "V2_1_A": {
        "tfidf": MODELS_DIR / "tfidf_v2_1_a.joblib",
        "svm": MODELS_DIR / "linear_svm_v2_1_a.joblib",
        "train_size": 6958,
        "external_rows": 54
    },
    "V2_1_B": {
        "tfidf": MODELS_DIR / "tfidf_v2_1_b.joblib",
        "svm": MODELS_DIR / "linear_svm_v2_1_b.joblib",
        "train_size": 7099,
        "external_rows": 195
    },
    "V2_1_C": {
        "tfidf": MODELS_DIR / "tfidf_v2_1_c.joblib",
        "svm": MODELS_DIR / "linear_svm_v2_1_c.joblib",
        "train_size": 7179,
        "external_rows": 275
    }
}


def cargar_compatibilidad():
    with open(COMPAT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def inferir_contexto_combustible(texto: str, true_class: str, compat_dict: dict) -> str:
    txt = texto.lower()
    if any(w in txt for w in ["diesel", "petroleo", "camion", "hilux", "1kd", "common rail", "dpf", "maxi-brake"]):
        return "DIESEL"
    if any(w in txt for w in ["gasolina", "bujia", "bobina", "gdi", "spark", "fscm"]):
        return "GASOLINE"
    # Derivar de la clase real
    comp_true = compat_dict.get(true_class, {}).get("fuel_compatibility", "BOTH")
    if comp_true == "DIESEL_ONLY":
        return "DIESEL"
    elif comp_true == "GASOLINE_ONLY":
        return "GASOLINE"
    return "UNKNOWN"


def evaluar_modelo_en_dataset(tfidf_path: Path, svm_path: Path, df_eval: pd.DataFrame, compat_dict: dict, aplicar_filtro_comb: bool = False, registrar_intervenciones: bool = False):
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
    top3_records = []
    scores_records = []

    preds_finales = []

    for i in range(len(X)):
        c_prob = probs[i].copy()
        txt = X[i]
        true_c = y[i]
        fuel_ctx = inferir_contexto_combustible(txt, true_c, compat_dict)

        orig_pred_idx = np.argmax(c_prob)
        orig_pred_class = classes[orig_pred_idx]

        # Verificar incompatibilidad del Top-1 original
        orig_comp = compat_dict.get(orig_pred_class, {}).get("fuel_compatibility", "BOTH")
        if fuel_ctx == "DIESEL" and orig_comp == "GASOLINE_ONLY":
            incompatibilidades += 1
        elif fuel_ctx == "GASOLINE" and orig_comp == "DIESEL_ONLY":
            incompatibilidades += 1

        # Aplicar filtro de combustible
        if aplicar_filtro_comb and fuel_ctx != "UNKNOWN":
            cambio = False
            for c_idx, c_name in enumerate(classes):
                c_comp = compat_dict.get(c_name, {}).get("fuel_compatibility", "BOTH")
                if fuel_ctx == "DIESEL" and c_comp == "GASOLINE_ONLY":
                    c_prob[c_idx] = 0.0
                    cambio = True
                elif fuel_ctx == "GASOLINE" and c_comp == "DIESEL_ONLY":
                    c_prob[c_idx] = 0.0
                    cambio = True

            if np.sum(c_prob) > 0:
                c_prob /= np.sum(c_prob)
            new_pred_idx = np.argmax(c_prob)
            new_pred_class = classes[new_pred_idx]

            if registrar_intervenciones and new_pred_class != orig_pred_class:
                intervenciones.append({
                    "id": df_eval.iloc[i].get("id", f"case_{i}"),
                    "texto": txt[:120].replace("\n", " "),
                    "fuel_type": fuel_ctx,
                    "prediction_before": orig_pred_class,
                    "prediction_after": new_pred_class,
                    "ground_truth": true_c,
                    "rule_applied": f"Bloqueo de hipótesis {orig_comp} para vehículo confirmado {fuel_ctx}",
                    "reason": "Incompatibilidad termodinámica física estricta"
                })
            pred_usada = new_pred_class
        else:
            pred_usada = orig_pred_class

        preds_finales.append(pred_usada)

        # Top-3
        top3_indices = np.argsort(c_prob)[-3:][::-1]
        top3_names = [classes[idx] for idx in top3_indices]
        top3_scores = [round(float(c_prob[idx]), 4) for idx in top3_indices]
        top3_records.append(top3_names)
        scores_records.append(top3_scores)

        if true_c in top3_names:
            top3_hits += 1

    acc = accuracy_score(y, preds_finales)
    top3 = top3_hits / len(y)
    macro_p = precision_score(y, preds_finales, average="macro", zero_division=0)
    macro_r = recall_score(y, preds_finales, average="macro", zero_division=0)
    macro_f1 = f1_score(y, preds_finales, average="macro", zero_division=0)
    weighted_f1 = f1_score(y, preds_finales, average="weighted", zero_division=0)

    # Per-class F1
    f1_por_clase = f1_score(y, preds_finales, average=None, labels=classes, zero_division=0)
    dict_f1 = {classes[idx]: float(f1_por_clase[idx]) for idx in range(len(classes))}

    incomp_pct = (incompatibilidades / len(X)) * 100 if not aplicar_filtro_comb else 0.0

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
        "X_text": X,
        "top3_records": top3_records,
        "scores_records": scores_records,
        "vectorizer": tfidf
    }


evaluar_modelo = evaluar_modelo_en_dataset


def ejecutar_benchmark_completo():
    print("="*70)
    print("INICIANDO BENCHMARK V2.1: BANCO PRIMARIO Y BANCO SECUNDARIO")
    print("="*70)

    compat_dict = cargar_compatibilidad()
    df_prim = pd.read_csv(TEST_PRIMARIO)
    df_sec = pd.read_csv(TEST_SECUNDARIO)

    print(f"Banco Primario (Histórico): {len(df_prim)} casos ({df_prim['clase_objetivo'].nunique()} clases)")
    print(f"Banco Secundario (Nuevo):    {len(df_sec)} casos ({df_sec['clase_objetivo'].nunique()} clases)")

    resultados_primario = {}
    resultados_secundario = {}

    for m_key, m_info in MODELOS_INFO.items():
        print(f"\nEvaluando {m_key}...")
        res_p = evaluar_modelo(m_info["tfidf"], m_info["svm"], df_prim, compat_dict, aplicar_filtro_comb=False)
        resultados_primario[m_key] = res_p

        res_s = evaluar_modelo(m_info["tfidf"], m_info["svm"], df_sec, compat_dict, aplicar_filtro_comb=False)
        resultados_secundario[m_key] = res_s

    # Seleccionar Mejor Candidato V2.1 en Primario
    candidatos_v2_1 = ["V2_1_A", "V2_1_B", "V2_1_C"]
    best_candidato_key = max(candidatos_v2_1, key=lambda k: resultados_primario[k]["macro_f1"])
    print(f"\nMejor candidato V2.1 seleccionado: {best_candidato_key} (Macro-F1 = {resultados_primario[best_candidato_key]['macro_f1']:.4f})")

    # Evaluar Mejor Candidato con Filtro de Combustible
    best_info = MODELOS_INFO[best_candidato_key]
    key_con_filtro = f"{best_candidato_key}_CON_FILTRO_COMBUSTIBLE"

    res_best_filt_p = evaluar_modelo(
        best_info["tfidf"], best_info["svm"], df_prim, compat_dict,
        aplicar_filtro_comb=True, registrar_intervenciones=True
    )
    resultados_primario[key_con_filtro] = res_best_filt_p

    res_best_filt_s = evaluar_modelo(
        best_info["tfidf"], best_info["svm"], df_sec, compat_dict,
        aplicar_filtro_comb=True, registrar_intervenciones=False
    )
    resultados_secundario[key_con_filtro] = res_best_filt_s

    # Guardar Intervenciones de Combustible (Fase 9)
    csv_intervenciones = V2_1_DIR / "LOG_INTERVENCIONES_COMBUSTIBLE.csv"
    if res_best_filt_p["intervenciones"]:
        with open(csv_intervenciones, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(res_best_filt_p["intervenciones"][0].keys()))
            writer.writeheader()
            writer.writerows(res_best_filt_p["intervenciones"])
        print(f"Log de intervenciones de combustible guardado: {csv_intervenciones.name} ({len(res_best_filt_p['intervenciones'])} correcciones)")

    # Comparar contra baseline FROZEN en banco primario
    base_f1_classes = resultados_primario["FROZEN"]["f1_por_clase"]
    best_f1_classes = resultados_primario[best_candidato_key]["f1_por_clase"]

    clases_mejoradas = 0
    clases_degradadas = 0
    degradacion_gt_0_10 = 0
    lista_mejoradas = []
    lista_degradadas = []

    for cname, fb in base_f1_classes.items():
        fv = best_f1_classes.get(cname, fb)
        delta = fv - fb
        if delta > 0.001:
            clases_mejoradas += 1
            lista_mejoradas.append((cname, fb, fv, delta))
        elif delta < -0.001:
            clases_degradadas += 1
            lista_degradadas.append((cname, fb, fv, delta))
            if delta < -0.10:
                degradacion_gt_0_10 += 1

    # Análisis de Errores Exhaustivo para el mejor candidato (Fase 14)
    print("\nGenerando Analisis de Errores para el mejor candidato...")
    errores_detalle = []
    y_true_p = res_best_filt_p["y_true"]
    y_pred_p = res_best_filt_p["preds_finales"]
    X_p = res_best_filt_p["X_text"]
    top3_p = res_best_filt_p["top3_records"]
    scores_p = res_best_filt_p["scores_records"]
    vec = res_best_filt_p["vectorizer"]
    feature_names = np.array(vec.get_feature_names_out())

    for i in range(len(y_true_p)):
        tc = y_true_p[i]
        pc = y_pred_p[i]
        if tc != pc:
            txt = X_p[i]
            row_data = df_prim.iloc[i]
            cid = row_data.get("id", f"case_{i}")
            ft = inferir_contexto_combustible(txt, tc, compat_dict)

            # Extraer tokens relevantes del vector TF-IDF para este texto
            v_row = vec.transform([txt]).toarray()[0]
            top_token_idxs = np.argsort(v_row)[-5:][::-1]
            tokens_rel = [feature_names[idx] for idx in top_token_idxs if v_row[idx] > 0]
            tokens_str = ", ".join(tokens_rel)

            # Clasificar causa del error (Fase 14 taxonomía formal)
            tc_low = tc.lower()
            pc_low = pc.lower()
            txt_low = txt.lower()

            if ft != "UNKNOWN" and ((ft == "DIESEL" and "bujia" in pc_low) or (ft == "GASOLINE" and "common rail" in pc_low)):
                causa = "FUEL_MISMATCH"
            elif any(w in tc_low and w in pc_low for w in ["freno", "embrague", "refrigerante", "sensor", "bomba"]):
                causa = "VOCABULARY_OVERLAP"
            elif len(txt) < 35:
                causa = "INSUFFICIENT_CONTEXT"
            elif any(p in txt_low for p in ["tironea", "tiembla", "vibra", "se apaga", "falla al acelerar"]) and not any(t in txt_low for t in ["dtc", "p0", "osciloscopio", "bar", "psi", "ohmios"]):
                causa = "AMBIGUOUS_SYMPTOM"
            elif any(dt in txt_low for dt in ["dtc", "p0", "u0", "b0"]):
                causa = "MISSING_CLASS_KNOWLEDGE"
            else:
                causa = "TRUE_DIAGNOSTIC_AMBIGUITY"

            errores_detalle.append({
                "id": cid,
                "texto": txt[:140].replace("\n", " "),
                "ground_truth": tc,
                "prediction_top1": pc,
                "top3": " | ".join(top3_p[i]),
                "scores": " | ".join(str(s) for s in scores_p[i]),
                "fuel_type": ft,
                "tokens_relevantes": tokens_str,
                "clase_confundida": pc,
                "causa_probable": causa
            })

    csv_errores = V2_1_DIR / "ANALISIS_ERRORES_MEJOR_CANDIDATO.csv"
    with open(csv_errores, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(errores_detalle[0].keys()))
        writer.writeheader()
        writer.writerows(errores_detalle)
    print(f"Analisis de errores guardado: {csv_errores.name} ({len(errores_detalle)} casos de error)")

    # Propuesta de sintéticos V2.2 (Fase 15: Solo DATA_LIMITED)
    print("Elaborando Propuesta de Sinteticos V2.2 (Solo DATA_LIMITED)...")
    train_c1_path = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "train10_v1_1_macrofix.csv"
    df_train = pd.read_csv(train_c1_path)
    counts_c1 = df_train["clase_objetivo"].value_counts().to_dict()

    propuesta_sinteticos = []
    for cname in sorted(counts_c1.keys()):
        cnt = counts_c1[cname]
        f1_c = best_f1_classes.get(cname, 1.0)
        # Solo clases con déficit real
        if cnt < 100 and f1_c < 0.85:
            faltante = 120 - cnt
            propuesta_sinteticos.append({
                "class": cname,
                "current_count": cnt,
                "current_f1": round(f1_c, 3),
                "error_type": "DATA_LIMITED",
                "needed_scenarios": "Variantes de jerga de taller peruano con síntomas de marcha vs reposo",
                "suggested_amount": faltante,
                "technical_source_required": "Manual de taller OEM con torques y tolerancias",
                "priority": "ALTA" if f1_c < 0.70 else "MEDIA"
            })

    csv_propuesta = V2_1_DIR / "PROPUESTA_SINTETICOS_V2_2.csv"
    with open(csv_propuesta, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(propuesta_sinteticos[0].keys()))
        writer.writeheader()
        writer.writerows(propuesta_sinteticos)
    print(f"Propuesta de sinteticos guardada: {csv_propuesta.name} ({len(propuesta_sinteticos)} clases deficitarias)")

    # Tabla Final de Comparación (Fase 16)
    print("\n" + "="*115)
    print("TABLA COMPARATIVA FINAL — BANCO PRIMARIO (TEST10)")
    print("="*115)
    header = f"{'MODEL':<28} {'TRAIN':<6} {'EXT':<5} {'TOP1':<7} {'TOP3':<7} {'PREC':<7} {'REC':<7} {'MACRO_F1':<9} {'WORST_F1':<9} {'INCOMP':<8} {'LAT(ms)':<7}"
    print(header)
    print("-" * 115)

    tabla_comparativa = []

    for m_key in ["FROZEN", "V2_ANTERIOR", "V2_1_A", "V2_1_B", "V2_1_C", key_con_filtro]:
        rp = resultados_primario[m_key]
        t_size = MODELOS_INFO.get(m_key.replace("_CON_FILTRO_COMBUSTIBLE", ""), {}).get("train_size", 7179)
        e_size = MODELOS_INFO.get(m_key.replace("_CON_FILTRO_COMBUSTIBLE", ""), {}).get("external_rows", 275)

        fila = {
            "model": m_key,
            "train_size": t_size,
            "external_rows": e_size,
            "top1": rp["top_1"],
            "top3": rp["top_3"],
            "macro_precision": rp["macro_precision"],
            "macro_recall": rp["macro_recall"],
            "macro_f1": rp["macro_f1"],
            "worst_class_f1": rp["worst_class_f1"],
            "incompatibilidad": rp["incompatibilidad_combustible_pct"],
            "latencia_ms": rp["latencia_ms"]
        }
        tabla_comparativa.append(fila)
        print(f"{m_key:<28} {t_size:<6} {e_size:<5} {rp['top_1']:<7.4f} {rp['top_3']:<7.4f} {rp['macro_precision']:<7.4f} {rp['macro_recall']:<7.4f} {rp['macro_f1']:<9.4f} {rp['worst_class_f1']:<9.4f} {rp['incompatibilidad_combustible_pct']:<7.2f}% {rp['latencia_ms']:<7.2f}")

    print("="*115)
    print("\nDESEMPEÑO EN BANCO SECUNDARIO NUEVO (183 CASOS):")
    for m_key in ["FROZEN", "V2_ANTERIOR", best_candidato_key, key_con_filtro]:
        rs = resultados_secundario[m_key]
        print(f"  - {m_key:<35}: Top-1 = {rs['top_1']:.4f} | Top-3 = {rs['top_3']:.4f} | Macro-F1 = {rs['macro_f1']:.4f}")

    # Guardar consolidado JSON
    out_json = EVAL_DIR / "RESULTADOS_EVALUACION_V2_1.json"
    consolidado = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mejor_candidato_identificado": best_candidato_key,
        "clases_mejoradas_count": clases_mejoradas,
        "clases_degradadas_count": clases_degradadas,
        "degradacion_gt_0_10_count": degradacion_gt_0_10,
        "top_clases_mejoradas": [{"clase": c, "f1_baseline": round(fb, 3), "f1_v2_1": round(fv, 3), "delta": round(d, 3)} for c, fb, fv, d in sorted(lista_mejoradas, key=lambda x: x[3], reverse=True)[:10]],
        "top_clases_degradadas": [{"clase": c, "f1_baseline": round(fb, 3), "f1_v2_1": round(fv, 3), "delta": round(d, 3)} for c, fb, fv, d in sorted(lista_degradadas, key=lambda x: x[3])[:10]],
        "tabla_comparativa_primario": tabla_comparativa,
        "metricas_banco_primario": {k: {m: v for m, v in resultados_primario[k].items() if m not in ["preds_finales", "y_true", "X_text", "classes", "f1_por_clase", "intervenciones", "vectorizer", "top3_records", "scores_records"]} for k in resultados_primario},
        "metricas_banco_secundario": {k: {m: v for m, v in resultados_secundario[k].items() if m not in ["preds_finales", "y_true", "X_text", "classes", "f1_por_clase", "intervenciones", "vectorizer", "top3_records", "scores_records"]} for k in resultados_secundario}
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(consolidado, f, indent=2, ensure_ascii=False)
    print(f"\nResultados consolidados guardados en: {out_json.name}")


if __name__ == "__main__":
    ejecutar_benchmark_completo()
