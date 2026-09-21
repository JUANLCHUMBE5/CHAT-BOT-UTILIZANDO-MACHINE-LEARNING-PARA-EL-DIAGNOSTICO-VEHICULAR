"""
Entrenamiento del Clasificador Jerárquico V3 (Sistema -> Falla).
Cumple estrictamente con la Regla 1 de Arquitectura de Tesis:
- Nivel 1: Linear SVM (CalibratedClassifierCV con LinearSVC) + TF-IDF para Macro-Sistemas.
- Nivel 2: Linear SVM (CalibratedClassifierCV con LinearSVC) + TF-IDF para las 48 Fallas Canónicas.
"""

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema

DATA_PATH = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
DATA_EXTERNO = BASE_DIR / "machine_learning" / "data" / "dataset_externo_auditado.csv"
MODEL_DIR = BASE_DIR / "machine_learning" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def cargar_y_preparar_datos():
    print(f"Cargando dataset canónico desde: {DATA_PATH}")
    df_base = pd.read_csv(DATA_PATH, encoding="utf-8")
    
    if DATA_EXTERNO.exists():
        print(f"Cargando dataset externo auditado desde: {DATA_EXTERNO}")
        df_ext = pd.read_csv(DATA_EXTERNO, encoding="utf-8-sig")
        df_total = pd.concat([df_base, df_ext], ignore_index=True)
    else:
        df_total = df_base.copy()
        
    df_total = df_total.dropna(subset=["sintoma", "falla"])
    df_total["sintoma"] = df_total["sintoma"].astype(str).str.strip()
    df_total["falla"] = df_total["falla"].astype(str).str.strip()
    df_total = df_total.drop_duplicates(subset=["sintoma"])
    
    # Asignar Macro-Sistema canónico
    df_total["macro_sistema"] = df_total["falla"].apply(obtener_macro_sistema)
    
    print(f"Total registros únicos para entrenamiento: {len(df_total)}")
    print(f"Distribución de Macro-Sistemas:\n{df_total['macro_sistema'].value_counts()}\n")
    print(f"Total clases específicas de falla: {df_total['falla'].nunique()}")
    
    return df_total

def entrenar():
    df = cargar_y_preparar_datos()
    
    X = df["sintoma"].values
    y_falla = df["falla"].values
    y_sistema = df["macro_sistema"].values
    
    # 1. División estratificada Train/Test 80/20
    X_train, X_test, y_f_train, y_f_test, y_s_train, y_s_test = train_test_split(
        X, y_falla, y_sistema, test_size=0.20, random_state=42, stratify=y_falla
    )
    
    # 2. Vectorizador TF-IDF (TfidfVectorizer estándar conforme a Regla 1)
    vectorizador = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
        max_features=25000
    )
    
    print("Vectorizando texto...")
    X_train_vec = vectorizador.fit_transform(X_train)
    X_test_vec = vectorizador.transform(X_test)
    
    # 3. Nivel 1: Linear SVM para Macro-Sistemas
    print("\n--- Entrenando Nivel 1: Clasificador de Macro-Sistemas (Linear SVM) ---")
    base_svc_sist = LinearSVC(C=1.0, random_state=42, max_iter=2500)
    modelo_sistema = CalibratedClassifierCV(estimator=base_svc_sist, method="sigmoid", cv=3)
    modelo_sistema.fit(X_train_vec, y_s_train)
    
    pred_s_test = modelo_sistema.predict(X_test_vec)
    acc_s = accuracy_score(y_s_test, pred_s_test)
    f1_s = f1_score(y_s_test, pred_s_test, average="macro")
    print(f"Nivel 1 (Macro-Sistemas) -> Accuracy: {acc_s*100:.2f}% | F1-Macro: {f1_s*100:.2f}%")
    
    # 4. Nivel 2: Linear SVM para 48 Fallas Canónicas
    print("\n--- Entrenando Nivel 2: Clasificador de Fallas Específicas (Linear SVM) ---")
    base_svc_falla = LinearSVC(C=1.2, random_state=42, max_iter=3000)
    modelo_falla = CalibratedClassifierCV(estimator=base_svc_falla, method="sigmoid", cv=3)
    modelo_falla.fit(X_train_vec, y_f_train)
    
    pred_f_test = modelo_falla.predict(X_test_vec)
    acc_f = accuracy_score(y_f_test, pred_f_test)
    f1_f = f1_score(y_f_test, pred_f_test, average="macro")
    print(f"Nivel 2 (Fallas Específicas) -> Accuracy: {acc_f*100:.2f}% | F1-Macro: {f1_f*100:.2f}%")
    
    # 5. Evaluación Combinada Jerárquica en Test Holdout
    probs_f = modelo_falla.predict_proba(X_test_vec)
    probs_s = modelo_sistema.predict_proba(X_test_vec)
    
    clases_f = list(modelo_falla.classes_)
    clases_s = list(modelo_sistema.classes_)
    sist_indices = {s: i for i, s in enumerate(clases_s)}
    
    aciertos_jerarquicos = 0
    top3_jerarquicos = 0
    
    for i in range(len(X_test)):
        pf = probs_f[i]
        ps = probs_s[i]
        
        # Ponderación jerárquica: P(F_j) * P(Sistema_k)^0.6
        scores = np.zeros_like(pf)
        for j, f_nom in enumerate(clases_f):
            s_nom = obtener_macro_sistema(f_nom)
            s_idx = sist_indices.get(s_nom, 0)
            scores[j] = pf[j] * (ps[s_idx] ** 0.6)
            
        top_idx = np.argmax(scores)
        if clases_f[top_idx] == y_f_test[i]:
            aciertos_jerarquicos += 1
            
        top3_indices = scores.argsort()[::-1][:3]
        if y_f_test[i] in [clases_f[idx] for idx in top3_indices]:
            top3_jerarquicos += 1
            
    acc_jerarquica = aciertos_jerarquicos / len(X_test)
    top3_jerarquica = top3_jerarquicos / len(X_test)
    print(f"\nClasificación Jerárquica Combinada -> Accuracy: {acc_jerarquica*100:.2f}% | Top-3 Accuracy: {top3_jerarquica*100:.2f}%")
    
    # 6. Guardar modelos canónicos
    ruta_modelo = MODEL_DIR / "modelo_diagnostico.pkl"
    ruta_sistema = MODEL_DIR / "modelo_sistema.pkl"
    ruta_vec = MODEL_DIR / "vectorizador_tfidf.pkl"
    
    joblib.dump(modelo_falla, ruta_modelo)
    joblib.dump(modelo_sistema, ruta_sistema)
    joblib.dump(vectorizador, ruta_vec)
    
    metricas = {
        "fecha_entrenamiento": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_muestras": len(df),
        "total_clases": len(clases_f),
        "total_macro_sistemas": len(clases_s),
        "holdout_test": {
            "accuracy_nivel_1_sistemas": round(acc_s, 4),
            "f1_macro_nivel_1": round(f1_s, 4),
            "accuracy_nivel_2_fallas": round(acc_f, 4),
            "f1_macro_nivel_2": round(f1_f, 4),
            "accuracy_jerarquica": round(acc_jerarquica, 4),
            "top3_accuracy_jerarquica": round(top3_jerarquica, 4)
        }
    }
    
    with open(MODEL_DIR / "metricas_jerarquicas.json", "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
        
    print(f"\nModelos guardados con éxito en {MODEL_DIR}")
    print(f"Metadatos guardados en {MODEL_DIR / 'metricas_jerarquicas.json'}")

if __name__ == "__main__":
    entrenar()
