"""
Comparación experimental:
MODELO A: TF-IDF palabras (1, 2) + Linear SVM
MODELO B: TF-IDF híbrido (palabras 1, 2 + caracteres char_wb 3, 5) + Linear SVM
Evaluación con StratifiedGroupKFold sobre 5,199 casos.
"""

import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "machine_learning" / "training"))
from entrenar_y_comparar_modelos import normalizar_grupo

DATA_PATH = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

def main():
    print("================================================================================")
    print("COMPARACIÓN EXPERIMENTAL TF-IDF: PALABRAS vs. HÍBRIDO (PALABRAS + CARACTERES)")
    print("================================================================================\n")

    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    df["grupo"] = df["sintoma"].map(normalizar_grupo)
    
    separador = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    idx_train, idx_test = next(separador.split(df["sintoma"], df["falla"], df["grupo"]))
    
    x_train, y_train = df["sintoma"].iloc[idx_train], df["falla"].iloc[idx_train]
    x_test, y_test = df["sintoma"].iloc[idx_test], df["falla"].iloc[idx_test]
    
    print(f"Dataset Total: {len(df)} registros | Train: {len(x_train)} | Test: {len(x_test)}\n")

    # 1. MODELO A: TF-IDF Palabras
    print("Entrenando MODELO A (TF-IDF Palabras n-gramas 1-2)...")
    t0_a = time.perf_counter()
    vec_a = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True, min_df=1)
    x_train_a = vec_a.fit_transform(x_train)
    x_test_a = vec_a.transform(x_test)
    
    clf_a = CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42, dual=False, max_iter=3000), method="sigmoid", cv=3)
    clf_a.fit(x_train_a, y_train)
    t_a = time.perf_counter() - t0_a
    
    pred_a = clf_a.predict(x_test_a)
    acc_a = accuracy_score(y_test, pred_a)
    f1_macro_a = f1_score(y_test, pred_a, average="macro", zero_division=0)
    f1_weighted_a = f1_score(y_test, pred_a, average="weighted", zero_division=0)

    # 2. MODELO B: TF-IDF Híbrido (Palabras + Caracteres char_wb)
    print("Entrenando MODELO B (TF-IDF Híbrido Palabras + Char_wb 3-5)...")
    t0_b = time.perf_counter()
    vec_b = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True, min_df=1)),
        ("char", TfidfVectorizer(ngram_range=(3, 5), analyzer="char_wb", lowercase=True, sublinear_tf=True, min_df=2))
    ])
    x_train_b = vec_b.fit_transform(x_train)
    x_test_b = vec_b.transform(x_test)
    
    clf_b = CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42, dual=False, max_iter=3000), method="sigmoid", cv=3)
    clf_b.fit(x_train_b, y_train)
    t_b = time.perf_counter() - t0_b
    
    pred_b = clf_b.predict(x_test_b)
    acc_b = accuracy_score(y_test, pred_b)
    f1_macro_b = f1_score(y_test, pred_b, average="macro", zero_division=0)
    f1_weighted_b = f1_score(y_test, pred_b, average="weighted", zero_division=0)

    print("\n--------------------------------------------------------------------------------")
    print("RESULTADOS COMPARATIVOS EN CONJUNTO DE PRUEBA HOLDOUT (DATOS NO VISTOS):")
    print(f"{'Métrica':<35} {'Modelo A (Palabras)':>20} {'Modelo B (Palabras + Char)':>25}")
    print("-" * 85)
    print(f"{'Dimensión Vocabulario (Features)':<35} {x_train_a.shape[1]:>20} {x_train_b.shape[1]:>25}")
    print(f"{'Tiempo de Ajuste + CV (seg)':<35} {t_a:>20.2f} {t_b:>25.2f}")
    print(f"{'Holdout Test Accuracy':<35} {acc_a*100:>19.2f}% {acc_b*100:>24.2f}%")
    print(f"{'Holdout F1-Macro':<35} {f1_macro_a*100:>19.2f}% {f1_macro_b*100:>24.2f}%")
    print(f"{'Holdout F1-Weighted':<35} {f1_weighted_a*100:>19.2f}% {f1_weighted_b*100:>24.2f}%")
    print("--------------------------------------------------------------------------------\n")

    # 3. Test de Robustez ante Errores Tipográficos y Variaciones de Mecánicos
    casos_robustez = [
        ("rueda delantera suena cla cla al doblar todo homosinetica rota", "Juntas homocineticas o palieres danados"),
        ("pedal durisimo como palo sin vacio al pisar freno", "Falla en servofreno (booster) o linea de vacio"),
        ("bateria descargada en las mananas claquea al dar arranque", "Bateria descargada o bornes sulfatados"),
        ("cascabelea en subida y pistonea con gasolina corriente", "Bujias desgastadas o gasolina de bajo octanaje (preignicion)"),
        ("caja zvt entra en modo limp y patina banda conica", "Sobrecalentamiento o solenoides en caja automatica CVT / DSG"),
        ("actuador de pestilos electricos suena traca traca y no traba", "Falla electrica del cierre centralizado o actuador de puerta"),
        ("zumbido agudo en tanque bajo aciento y tirones bajo carga", "Bomba de gasolina quemada o con baja presion")
    ]

    print("PRUEBA DE ROBUSTEZ ANTE ERRORES TIPOGRÁFICOS Y JERGA:")
    for texto, esperado in casos_robustez:
        pred_a_caso = clf_a.predict(vec_a.transform([texto]))[0]
        prob_a = max(clf_a.predict_proba(vec_a.transform([texto]))[0])
        
        pred_b_caso = clf_b.predict(vec_b.transform([texto]))[0]
        prob_b = max(clf_b.predict_proba(vec_b.transform([texto]))[0])
        
        ok_a = "OK" if pred_a_caso == esperado else "FAIL"
        ok_b = "OK" if pred_b_caso == esperado else "FAIL"
        
        print(f"\nCaso: '{texto}'")
        print(f"  Esperado: {esperado}")
        print(f"  Modelo A [{ok_a}]: {pred_a_caso} (Conf: {prob_a*100:.1f}%)")
        print(f"  Modelo B [{ok_b}]: {pred_b_caso} (Conf: {prob_b*100:.1f}%)")

if __name__ == "__main__":
    main()
