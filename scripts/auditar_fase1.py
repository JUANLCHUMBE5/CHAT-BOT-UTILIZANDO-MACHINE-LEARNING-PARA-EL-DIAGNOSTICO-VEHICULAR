"""
FASE 1: Auditoría Exhaustiva del Dataset y Clasificador Linear SVM
Tareas 1 a 5:
1. Distribución de registros por clase (4,959 casos).
2. Detección de duplicados, datos idénticos y análisis de fuga.
3. Evaluación detallada de Train Accuracy, Test Accuracy, Precision, Recall y F1 por clase.
4. Matriz de confusión completa y extracción de pares de confusión principales.
5. Identificación de clases débiles y causas raíz.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
import joblib

# Ubicación de datos y modelos
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
MODEL_PATH = BASE_DIR / "machine_learning" / "models" / "modelo_diagnostico.pkl"
VEC_PATH = BASE_DIR / "machine_learning" / "models" / "vectorizador_tfidf.pkl"

sys.path.insert(0, str(BASE_DIR / "machine_learning" / "training"))
from entrenar_y_comparar_modelos import normalizar_grupo

def main():
    print("================================================================================")
    print("FASE 1: AUDITORÍA DE DATASET Y EVALUACIÓN DEL MODELO LINEAR SVM (48 CLASES)")
    print("================================================================================\n")

    # 1. Cargar Dataset
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    total_registros = len(df)
    print(f"Total de registros en dataset: {total_registros}")
    print(f"Total de clases únicas: {df['falla'].nunique()}\n")

    # ==========================================================================
    # TAREA 1: DISTRIBUCIÓN DEL DATASET
    # ==========================================================================
    conteo_clases = df["falla"].value_counts()
    print("=== TAREA 1: DISTRIBUCIÓN DEL DATASET (REGISTROS POR CLASE) ===")
    print(f"{'Clase / Falla Automotriz':<75} {'Registros':>10} {'% del Total':>12}")
    print("-" * 100)
    for clase, cant in conteo_clases.items():
        pct = (cant / total_registros) * 100
        print(f"{clase:<75} {cant:>10} {pct:>11.2f}%")
    print("-" * 100)
    print(f"{'TOTAL':<75} {total_registros:>10} {100.00:>11.2f}%\n")

    # ==========================================================================
    # TAREA 2: BÚSQUEDA DE DUPLICADOS Y ANÁLISIS DE FUGA
    # ==========================================================================
    print("=== TAREA 2: DUPLICADOS Y ANÁLISIS DE FUGA ===")
    duplicados_exactos = df.duplicated(subset=["sintoma"]).sum()
    duplicados_con_etiqueta = df.duplicated(subset=["sintoma", "falla"]).sum()
    
    # Textos con etiquetas contradictorias
    sintomas_contradictorios = df.groupby("sintoma")["falla"].nunique()
    contradictorios = sintomas_contradictorios[sintomas_contradictorios > 1]
    
    print(f"Duplicados exactos de síntoma: {duplicados_exactos}")
    print(f"Duplicados exactos síntoma + falla: {duplicados_con_etiqueta}")
    print(f"Síntomas con etiquetas contradictorias (distinta clase): {len(contradictorios)}")
    if len(contradictorios) > 0:
        print("  Ejemplos de contradicción:")
        for s in contradictorios.index[:5]:
            clases_conflictivas = df[df["sintoma"] == s]["falla"].unique()
            print(f"    - '{s}' -> {list(clases_conflictivas)}")

    # Análisis de familias (StratifiedGroupKFold)
    df["grupo"] = df["sintoma"].map(normalizar_grupo)
    print(f"Familias sintomáticas únicas (para evitar fuga entre train/test): {df['grupo'].nunique()}\n")

    # ==========================================================================
    # TAREA 3: EVALUACIÓN DEL SVM POR CLASE (TRAIN vs TEST)
    # ==========================================================================
    print("=== TAREA 3: EVALUACIÓN DE LINEAR SVM (TRAIN VS TEST) ===")
    
    # Replicar partición canónica StratifiedGroupKFold (80/20)
    separador = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    idx_train, idx_test = next(separador.split(df["sintoma"], df["falla"], df["grupo"]))
    
    train_df = df.iloc[idx_train]
    test_df = df.iloc[idx_test]
    
    print(f"Registros en Train (80%): {len(train_df)}")
    print(f"Registros en Test (20%):  {len(test_df)}")

    # Para evaluar la VERDADERA capacidad de generalización sin fuga,
    # ajustamos el vectorizador y el estimador ÚNICAMENTE sobre train_df
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
    from sklearn.calibration import CalibratedClassifierCV

    vec_split = TfidfVectorizer(
        ngram_range=(1, 2),
        lowercase=True,
        sublinear_tf=True,
        min_df=1,
    )
    x_train_vec = vec_split.fit_transform(train_df["sintoma"])
    x_test_vec = vec_split.transform(test_df["sintoma"])

    base_svc = LinearSVC(C=1.0, random_state=42, dual=False, max_iter=3000)
    modelo_split = CalibratedClassifierCV(base_svc, method="sigmoid", cv=3)
    modelo_split.fit(x_train_vec, train_df["falla"])

    y_train_pred = modelo_split.predict(x_train_vec)
    y_test_pred = modelo_split.predict(x_test_vec)
    
    acc_train = accuracy_score(train_df["falla"], y_train_pred)
    acc_test = accuracy_score(test_df["falla"], y_test_pred)
    
    print(f"\nExactitud en Entrenamiento (Train Accuracy): {acc_train*100:.2f}%")
    print(f"Exactitud en Conjunto de Prueba Holdout (Test Accuracy): {acc_test*100:.2f}%\n")
    
    # Reporte de Clasificación en Test
    reporte_dict = classification_report(test_df["falla"], y_test_pred, output_dict=True, zero_division=0)
    
    # Ordenar clases por F1-Score ascendente (de menor a mayor para ver las débiles primero)
    metricas_clases = []
    for clase, m in reporte_dict.items():
        if clase in {"accuracy", "macro avg", "weighted avg"}:
            continue
        metricas_clases.append({
            "clase": clase,
            "precision": m["precision"],
            "recall": m["recall"],
            "f1": m["f1-score"],
            "soporte_test": int(m["support"]),
            "soporte_total": int(conteo_clases.get(clase, 0))
        })
    
    metricas_clases.sort(key=lambda x: x["f1"])

    print("=== MÉTRICAS DETALLADAS POR CLASE EN TEST (ORDENADAS DE MENOR A MAYOR F1) ===")
    print(f"{'Clase / Falla':<70} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Test':>6} {'Total':>6}")
    print("-" * 105)
    for m in metricas_clases:
        print(f"{m['clase']:<70} {m['precision']:>7.2f} {m['recall']:>7.2f} {m['f1']:>7.2f} {m['soporte_test']:>6} {m['soporte_total']:>6}")
    print("-" * 105)
    macro_avg = reporte_dict["macro avg"]
    print(f"{'PROMEDIO MACRO':<70} {macro_avg['precision']:>7.2f} {macro_avg['recall']:>7.2f} {macro_avg['f1-score']:>7.2f} {len(test_df):>6} {total_registros:>6}\n")

    # ==========================================================================
    # TAREA 4: MATRIZ DE CONFUSIÓN Y PARES DE CONFUSIÓN FRECUENTES
    # ==========================================================================
    print("=== TAREA 4: MATRIZ DE CONFUSIÓN Y PARES DE CONFUSIÓN MÁS FRECUENTES ===")
    clases_ordenadas = sorted(df["falla"].unique())
    cm = confusion_matrix(test_df["falla"], y_test_pred, labels=clases_ordenadas)
    
    # Extraer errores (fuera de diagonal)
    confusiones = []
    for i, real in enumerate(clases_ordenadas):
        for j, pred in enumerate(clases_ordenadas):
            if i != j and cm[i, j] > 0:
                confusiones.append({
                    "real": real,
                    "predicha": pred,
                    "casos": int(cm[i, j])
                })
    
    confusiones.sort(key=lambda x: x["casos"], reverse=True)
    
    print(f"Total de pares de confusión encontrados en test: {len(confusiones)}")
    print(f"Total de predicciones incorrectas en test: {sum(c['casos'] for c in confusiones)} / {len(test_df)}\n")
    print("Top 20 mayores confusiones del modelo:")
    print(f"{'Clase Real':<50} -> {'Clase Confundida (Predicha)':<50} {'Casos':>6}")
    print("-" * 110)
    for c in confusiones[:20]:
        print(f"{c['real']:<50} -> {c['predicha']:<50} {c['casos']:>6}")
    print("-" * 110 + "\n")

    # ==========================================================================
    # TAREA 5: IDENTIFICAR CLASES DÉBILES
    # ==========================================================================
    print("=== TAREA 5: CLASES DÉBILES Y DIAGNÓSTICO DE CAUSA RAÍZ ===")
    debiles = [m for m in metricas_clases if m["f1"] < 0.90]
    print(f"Clases con F1 < 0.90: {len(debiles)} de 48 clases\n")
    
    for d in debiles:
        clase_nom = d["clase"]
        # Buscar con quién se confunde más esta clase
        conf_de_esta = [c for c in confusiones if c["real"] == clase_nom]
        conf_hacia_esta = [c for c in confusiones if c["predicha"] == clase_nom]
        
        print(f"[*] CLASE DEBIL: '{clase_nom}'")
        print(f"   Metricas: Precision={d['precision']:.2f} | Recall={d['recall']:.2f} | F1={d['f1']:.2f} | Soporte Total={d['soporte_total']} (Test={d['soporte_test']})")
        if conf_de_esta:
            print("   Falsos Negativos (se confunde con):")
            for c in conf_de_esta:
                print(f"     -> {c['casos']} casos predichos como '{c['predicha']}'")
        if conf_hacia_esta:
            print("   Falsos Positivos (otras clases predichas erroneamente como esta):")
            for c in conf_hacia_esta:
                print(f"     <- {c['casos']} casos provenientes de '{c['real']}'")
        print()

if __name__ == "__main__":
    main()
