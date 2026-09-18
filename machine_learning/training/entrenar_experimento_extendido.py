"""Evalúa un aumento lingüístico sintético sin contaminar el modelo canónico.

Los registros generados amplían vocabulario, pero no representan observaciones
reales ni resultados oficiales de la tesis. Las particiones se construyen por
familias para impedir que variantes de una misma plantilla crucen al holdout.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from machine_learning.training.entrenar_y_comparar_modelos import normalizar_grupo  # noqa: E402

DATA_DIR = ROOT / "machine_learning" / "data"
EXP_DIR = ROOT / "machine_learning" / "models" / "experimentos" / "modelo_extendido_taller"
OFFICIAL_DATA = DATA_DIR / "dataset_sintomas_limpio.csv"
SYNTHETIC_DATA = DATA_DIR / "dataset_sintomas_aumento_taller.csv"
METRICS_OUTPUT = EXP_DIR / "metricas_modelo_extendido.json"
MODEL_OUTPUT = EXP_DIR / "modelo_extendido_taller.joblib"


def _validar_aumento(datos: pd.DataFrame) -> None:
    columnas = {
        "sintoma",
        "falla",
        "codigo_falla",
        "origen_dato",
        "grupo_origen",
        "estado_revision",
        "validado_mecanico",
    }
    faltantes = columnas - set(datos.columns)
    if faltantes:
        raise ValueError(
            "El aumento sintético carece de trazabilidad: " + ", ".join(sorted(faltantes))
        )
    if set(datos["origen_dato"].dropna().unique()) != {"sintetico_aumentado"}:
        raise ValueError("El archivo de aumento contiene un origen no sintético.")
    if (datos["validado_mecanico"].astype(str).str.upper() != "NO").any():
        raise ValueError("Un registro sintético no puede declararse validado por un mecánico.")
    if (datos["estado_revision"] != "solo_experimento").any():
        raise ValueError("El aumento sintético debe permanecer aislado como experimento.")


def cargar_y_conectar_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Carga la base curada y el aumento sintético conservando su procedencia."""
    if not OFFICIAL_DATA.exists() or not SYNTHETIC_DATA.exists():
        raise FileNotFoundError("Falta el dataset curado o el aumento sintético.")

    oficial = pd.read_csv(OFFICIAL_DATA, encoding="utf-8-sig")
    aumento = pd.read_csv(SYNTHETIC_DATA, encoding="utf-8")
    _validar_aumento(aumento)

    columnas = ["sintoma", "falla", "codigo_falla"]
    oficial_modelo = oficial[columnas].copy()
    oficial_modelo["origen_dato"] = "base_curada"
    oficial_modelo["grupo_origen"] = oficial_modelo["sintoma"].map(
        lambda texto: f"BASE-{normalizar_grupo(texto)}"
    )
    aumento_modelo = aumento[[*columnas, "origen_dato", "grupo_origen"]].copy()
    combinado = pd.concat([oficial_modelo, aumento_modelo], ignore_index=True)
    combinado["sintoma"] = combinado["sintoma"].astype(str).str.strip()
    combinado["falla"] = combinado["falla"].astype(str).str.strip()
    combinado = combinado.dropna(subset=["sintoma", "falla", "grupo_origen"])
    antes_duplicados = len(combinado)
    combinado = combinado.drop_duplicates(subset=["sintoma", "falla"])

    etiquetas_por_grupo = combinado.groupby("grupo_origen")["falla"].nunique()
    grupos_ambiguos = set(etiquetas_por_grupo[etiquetas_por_grupo > 1].index)
    antes_ambiguos = len(combinado)
    combinado = combinado[~combinado["grupo_origen"].isin(grupos_ambiguos)].copy()

    auditoria = {
        "duplicados_exactos_excluidos": antes_duplicados - antes_ambiguos,
        "familias_ambiguas_excluidas": len(grupos_ambiguos),
        "registros_ambiguos_excluidos": antes_ambiguos - len(combinado),
        "datos_base_curada": int((combinado["origen_dato"] == "base_curada").sum()),
        "datos_sinteticos": int((combinado["origen_dato"] == "sintetico_aumentado").sum()),
    }
    return oficial_modelo, aumento_modelo, combinado, auditoria


def crear_particiones_agrupadas(
    datos: pd.DataFrame, random_state: int = 42
) -> tuple[pd.Index, pd.Index]:
    """Crea un holdout sin familias compartidas con el entrenamiento."""
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=random_state)
    train_idx, test_idx = next(
        splitter.split(datos["sintoma"], datos["falla"], datos["grupo_origen"])
    )
    grupos_train = set(datos.iloc[train_idx]["grupo_origen"])
    grupos_test = set(datos.iloc[test_idx]["grupo_origen"])
    if grupos_train & grupos_test:
        raise RuntimeError("Se detectó fuga de familias entre entrenamiento y prueba.")
    return pd.Index(train_idx), pd.Index(test_idx)


def _pipeline_calibrado(random_state: int) -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2), min_df=1, sublinear_tf=True, strip_accents="unicode"
                ),
            ),
            (
                "clf",
                CalibratedClassifierCV(
                    estimator=LinearSVC(
                        C=1.0, class_weight="balanced", random_state=random_state
                    ),
                    method="sigmoid",
                    cv=3,
                ),
            ),
        ]
    )


def entrenar_modelo_extendido(
    datos: pd.DataFrame, random_state: int = 42, auditoria_datos: dict | None = None
) -> dict:
    """Entrena y evalúa el candidato; nunca lo promueve automáticamente."""
    train_idx, test_idx = crear_particiones_agrupadas(datos, random_state)
    x, y, grupos = datos["sintoma"], datos["falla"], datos["grupo_origen"]
    x_train, x_test = x.iloc[train_idx], x.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    grupos_train, grupos_test = grupos.iloc[train_idx], grupos.iloc[test_idx]

    modelo = _pipeline_calibrado(random_state)
    inicio = time.perf_counter()
    modelo.fit(x_train, y_train)
    tiempo_entrenamiento = round(time.perf_counter() - inicio, 3)
    inicio = time.perf_counter()
    modelo.predict_proba(["el timón vibra a 80 km/h pero al frenar no tiembla el pedal"])
    tiempo_inferencia = round((time.perf_counter() - inicio) * 1000, 2)

    predicciones = modelo.predict(x_test)
    cv = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=random_state + 1)
    scores = []
    for ajuste, validacion in cv.split(x_train, y_train, grupos_train):
        modelo_fold = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
                ("clf", LinearSVC(C=1.0, class_weight="balanced", random_state=random_state)),
            ]
        )
        modelo_fold.fit(x_train.iloc[ajuste], y_train.iloc[ajuste])
        scores.append(accuracy_score(y_train.iloc[validacion], modelo_fold.predict(x_train.iloc[validacion])))

    resultado = {
        "modelo": "Linear SVM + TF-IDF (Calibrado)",
        "estado": "experimental_no_promovido",
        "total_registros_combinados": int(len(datos)),
        "registros_entrenamiento": int(len(x_train)),
        "registros_prueba": int(len(x_test)),
        "clases_cubiertas": int(y.nunique()),
        "metodo_evaluacion": "holdout y CV agrupados por familia de síntoma",
        "familias_entrenamiento": int(grupos_train.nunique()),
        "familias_prueba": int(grupos_test.nunique()),
        "familias_compartidas_train_test": 0,
        "auditoria_datos": auditoria_datos or {},
        "tiempo_entrenamiento_segundos": tiempo_entrenamiento,
        "tiempo_inferencia_unitario_ms": tiempo_inferencia,
        "metricas_holdout": {
            "exactitud": round(float(accuracy_score(y_test, predicciones)), 4),
            "f1_macro": round(float(f1_score(y_test, predicciones, average="macro", zero_division=0)), 4),
            "f1_weighted": round(
                float(f1_score(y_test, predicciones, average="weighted", zero_division=0)), 4
            ),
        },
        "validacion_cruzada_4_fold_agrupada": {
            "scores": [round(float(score), 4) for score in scores],
            "media": round(float(np.mean(scores)), 4),
            "desviacion_estandar": round(float(np.std(scores)), 4),
        },
        "reporte_por_clase": classification_report(
            y_test, predicciones, output_dict=True, zero_division=0
        ),
        "aprobado_para_promocion": False,
        "bloqueos_promocion": [
            "El aumento lingüístico es sintético.",
            "Falta evaluación externa con casos reales y confirmación mecánica.",
            "Falta comparación auditada contra el modelo canónico.",
        ],
    }
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, MODEL_OUTPUT)
    METRICS_OUTPUT.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    return resultado


def ejecutar_experimento() -> None:
    oficial, aumento, combinado, auditoria = cargar_y_conectar_datasets()
    print(f"Base curada: {len(oficial)}")
    print(f"Aumento sintético: {len(aumento)}")
    resultados = entrenar_modelo_extendido(combinado, auditoria_datos=auditoria)
    print(json.dumps({
        "estado": resultados["estado"],
        "metricas_holdout": resultados["metricas_holdout"],
        "familias_compartidas_train_test": resultados["familias_compartidas_train_test"],
        "aprobado_para_promocion": resultados["aprobado_para_promocion"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    ejecutar_experimento()
