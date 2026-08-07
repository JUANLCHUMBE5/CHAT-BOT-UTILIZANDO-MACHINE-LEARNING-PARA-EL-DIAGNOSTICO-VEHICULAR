import pandas as pd
import numpy as np
import joblib
import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix

def entrenar_evaluar_modelo():
    print("=" * 80)
    print("ENTRENAMIENTO Y EVALUACION DEL MODELO ML (RANDOM FOREST OPTIMIZADO)")
    print("=" * 80)

    # 1. Cargar dataset balanceado
    path_dataset = "data/dataset_sintomas.csv"
    if not os.path.exists(path_dataset):
        print(f"Error: No se encontró '{path_dataset}'. Ejecuta primero 'generar_dataset.py'.")
        return

    df = pd.read_csv(path_dataset, encoding="utf-8")
    print(f"Dataset cargado: {len(df)} ejemplos | {df['falla'].nunique()} clases distintas.")

    X = df['sintoma']
    y = df['falla']

    # 2. Vectorización TF-IDF Optimizada (N-gramas 1-2 + sublinear_tf)
    vectorizador = TfidfVectorizer(
        lowercase=True, 
        strip_accents='unicode', 
        ngram_range=(1, 2),
        sublinear_tf=True
    )
    # 3. Separar ANTES de ajustar TF-IDF para impedir fuga de información del test.
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    X_train = vectorizador.fit_transform(X_train_text)
    X_test = vectorizador.transform(X_test_text)

    # 4. Entrenar Random Forest Classifier sin restricción artificial de profundidad
    modelo = RandomForestClassifier(
        n_estimators=100, 
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        class_weight='balanced',
        n_jobs=1,
    )
    modelo.fit(X_train, y_train)

    # 5. Evaluación en Test Set
    y_pred = modelo.predict(X_test)
    
    exactitud = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')

    print("\n--- REPORTE DE METRICAS DE DESEMPEÑO EN SET DE PRUEBA (TEST SET) ---")
    print(f"Exactitud (Accuracy):           {exactitud * 100:.2f}%")
    print(f"F1-Score Promedio (Macro):      {f1_macro * 100:.2f}%")
    print(f"F1-Score Promedio (Weighted):   {f1_weighted * 100:.2f}%")
    print("\n--- CLASSIFICATION REPORT DETALLADO ---")
    print(classification_report(y_test, y_pred, zero_division=0))

    # 6. Re-entrenar modelo final con 100% de los datos para producción/demo
    modelo_final = RandomForestClassifier(
        n_estimators=100, 
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        class_weight='balanced',
        n_jobs=1,
    )
    vectorizador_final = TfidfVectorizer(
        lowercase=True, strip_accents='unicode', ngram_range=(1, 2), sublinear_tf=True
    )
    X_vec_final = vectorizador_final.fit_transform(X)
    modelo_final.fit(X_vec_final, y)

    # Exportar los modelos .pkl
    os.makedirs("models", exist_ok=True)
    joblib.dump(modelo_final, 'models/modelo_diagnostico.pkl', compress=3)
    joblib.dump(vectorizador_final, 'models/vectorizador_tfidf.pkl', compress=3)
    metricas = {
        "accuracy": float(exactitud),
        "f1_macro": float(f1_macro),
        "f1_weighted": float(f1_weighted),
        "filas": int(len(df)),
        "clases": int(df['falla'].nunique()),
        "random_state": 42,
        "evaluacion": "holdout_estratificado_sin_fuga_tfidf",
    }
    with open("models/metricas_modelo.json", "w", encoding="utf-8") as archivo_metricas:
        json.dump(metricas, archivo_metricas, ensure_ascii=False, indent=2)
    print("\nArchivos exportados exitosamente:")
    print("  - models/modelo_diagnostico.pkl")
    print("  - models/vectorizador_tfidf.pkl")

    # 7. Generar Matriz de Confusión y Guardar Gráfica
    try:
        labels = sorted(list(y.unique()))
        cm = confusion_matrix(y_test, y_pred, labels=labels)

        os.makedirs("documentacion/graficas", exist_ok=True)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=labels, yticklabels=labels)
        plt.title('Matriz de Confusión - Clasificador Random Forest', pad=15, fontsize=12, fontweight='bold')
        plt.xlabel('Predicción del Modelo', labelpad=10, fontweight='bold')
        plt.ylabel('Clase Real (Ground Truth)', labelpad=10, fontweight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=8)
        plt.yticks(rotation=0, fontsize=8)
        plt.tight_layout()
        
        path_cm_graph = "documentacion/graficas/matriz_confusion_ml.png"
        plt.savefig(path_cm_graph, dpi=300)
        plt.close()
        print(f"\n[Graficador] Matriz de confusión exportada en: '{path_cm_graph}'")
    except Exception as e:
        print(f"\n[Aviso Graficador] No se pudo generar la gráfica de matriz de confusión debido a restricciones de seguridad del sistema (Matplotlib DLL): {e}")
    print("=" * 80)

if __name__ == "__main__":
    entrenar_evaluar_modelo()
