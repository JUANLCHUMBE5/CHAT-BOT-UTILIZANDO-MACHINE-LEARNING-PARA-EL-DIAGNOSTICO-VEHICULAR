"""Entrena, compara y calibra modelos evitando fuga entre variantes del mismo sintoma."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_score
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PREFIJOS_CONTEXTO = re.compile(
    r"\b(amigo una consulta|tengo un problema con mi auto|tengo un problema|"
    r"resulta que en mi carro|resulta que|sabes que|mi carro presenta|"
    r"amigo mi auto presenta|maestro una consulta|buenas tardes mecanico|"
    r"en mi vehiculo noto que|hace dos dias noto que)\b"
)
SUFIJOS_CONTEXTO = re.compile(
    r"\b(ultimamente|desde ayer|en carabayllo|en la pista|en las mananas|"
    r"cuando voy manejando|cuando salgo a trabajar|al pasar un rompemuelles|"
    r"de la nada|al acelerar|al andar a \d+ km(?:/h| por hora)?)\b"
)


def normalizar_grupo(texto: str) -> str:
    """Agrupa para que parafrasis generadas del mismo sintoma no crucen folds."""
    texto = unicodedata.normalize("NFKD", str(texto).lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = PREFIJOS_CONTEXTO.sub(" ", texto)
    texto = SUFIJOS_CONTEXTO.sub(" ", texto)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", texto)).strip()


def vectorizador() -> TfidfVectorizer:
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    )


def estimadores() -> dict[str, object]:
    return {
        "Random_Forest": RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight="balanced", n_jobs=1
        ),
        "Logistic_Regression": LogisticRegression(
            C=5.0, max_iter=1500, random_state=42, class_weight="balanced"
        ),
        "Linear_SVM": LinearSVC(C=1.0, random_state=42, dual=False, max_iter=3000),
        "Complement_Naive_Bayes": ComplementNB(alpha=0.5),
    }


def sha256(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def error_calibracion_esperado(probabilidades: np.ndarray, y_real: np.ndarray, clases) -> float:
    confianza = probabilidades.max(axis=1)
    predichas = np.asarray(clases)[probabilidades.argmax(axis=1)]
    correctas = predichas == y_real
    ece = 0.0
    for inferior in np.linspace(0.0, 0.9, 10):
        superior = inferior + 0.1
        mascara = (confianza > inferior) & (confianza <= superior)
        if mascara.any():
            ece += mascara.mean() * abs(correctas[mascara].mean() - confianza[mascara].mean())
    return float(ece)


def umbral_seguro(probabilidades: np.ndarray, y_real: np.ndarray, clases) -> float:
    confianza = probabilidades.max(axis=1)
    predichas = np.asarray(clases)[probabilidades.argmax(axis=1)]
    for umbral in np.arange(0.50, 0.91, 0.05):
        mascara = confianza >= umbral
        if mascara.mean() >= 0.20 and (predichas[mascara] == y_real[mascara]).mean() >= 0.80:
            return float(round(umbral, 2))
    return 0.70


def entrenar_y_comparar() -> None:
    ruta_dataset = Path("data/dataset_sintomas_limpio.csv")
    datos = pd.read_csv(ruta_dataset, encoding="utf-8")
    ruta_dataset_externo = Path("data/dataset_externo_auditado.csv")
    datos_externos = (
        pd.read_csv(ruta_dataset_externo, encoding="utf-8-sig")
        if ruta_dataset_externo.exists()
        else pd.DataFrame(columns=["sintoma", "falla"])
    )
    x = datos["sintoma"].astype(str).reset_index(drop=True)
    y = datos["falla"].astype(str).reset_index(drop=True)
    datos_externos = datos_externos[datos_externos["falla"].isin(set(y.unique()))].copy()
    x_externo = datos_externos["sintoma"].astype(str).reset_index(drop=True)
    y_externo = datos_externos["falla"].astype(str).reset_index(drop=True)
    grupos = x.map(normalizar_grupo)

    if grupos.nunique() < 10:
        raise RuntimeError("No existen suficientes familias independientes de sintomas.")

    separador = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    indices_train, indices_test = next(separador.split(x, y, grupos))
    x_train, x_test = x.iloc[indices_train], x.iloc[indices_test]
    y_train, y_test = y.iloc[indices_train], y.iloc[indices_test]
    grupos_train = grupos.iloc[indices_train]

    cv = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=43)
    soporte_particiones_cv = []
    clases_entrenamiento = set(y_train.unique())
    for numero, (idx_ajuste, idx_validacion) in enumerate(
        cv.split(x_train, y_train, grupos_train), start=1
    ):
        y_ajuste = y_train.iloc[idx_ajuste]
        y_validacion = y_train.iloc[idx_validacion]
        soporte_particiones_cv.append(
            {
                "fold": numero,
                "clases_ajuste": int(y_ajuste.nunique()),
                "clases_validacion": int(y_validacion.nunique()),
                "minimo_soporte_validacion": int(y_validacion.value_counts().min()),
                "clases_ausentes_validacion": sorted(
                    clases_entrenamiento - set(y_validacion.unique())
                ),
            }
        )
    resultados_cv: dict[str, dict[str, float]] = {}
    candidatos = estimadores()
    for nombre, estimador in candidatos.items():
        pipeline = Pipeline([("tfidf", vectorizador()), ("clasificador", estimador)])
        scores = cross_val_score(
            pipeline,
            x_train,
            y_train,
            groups=grupos_train,
            cv=cv,
            scoring="f1_macro",
            n_jobs=1,
        )
        resultados_cv[nombre] = {
            "media_f1_macro": float(scores.mean()),
            "desviacion_std": float(scores.std()),
        }

    ganador = max(
        resultados_cv,
        key=lambda nombre: (
            resultados_cv[nombre]["media_f1_macro"],
            -resultados_cv[nombre]["desviacion_std"],
        ),
    )

    y_test_array = y_test.to_numpy()

    def ajustar_y_evaluar(x_ajuste: pd.Series, y_ajuste: pd.Series) -> dict[str, object]:
        vec = vectorizador()
        x_ajuste_vec = vec.fit_transform(x_ajuste)
        x_prueba_vec = vec.transform(x_test)
        modelo = CalibratedClassifierCV(estimadores()[ganador], method="sigmoid", cv=3)
        modelo.fit(x_ajuste_vec, y_ajuste)
        pred = modelo.predict(x_prueba_vec)
        proba = modelo.predict_proba(x_prueba_vec)
        reporte = classification_report(
            y_test, pred, output_dict=True, zero_division=0
        )
        f1_por_clase = {
            clase: float(valores["f1-score"])
            for clase, valores in reporte.items()
            if clase not in {"accuracy", "macro avg", "weighted avg"}
        }
        return {
            "vectorizador": vec,
            "modelo": modelo,
            "predicciones": pred,
            "probabilidades": proba,
            "exactitud": float(accuracy_score(y_test, pred)),
            "f1_macro": float(f1_score(y_test, pred, average="macro", zero_division=0)),
            "f1_weighted": float(f1_score(y_test, pred, average="weighted", zero_division=0)),
            "ece": error_calibracion_esperado(proba, y_test_array, modelo.classes_),
            "f1_por_clase": f1_por_clase,
        }

    evaluacion_base = ajustar_y_evaluar(x_train.reset_index(drop=True), y_train.reset_index(drop=True))
    if len(datos_externos):
        x_train_enriquecido = pd.concat([x_train.reset_index(drop=True), x_externo], ignore_index=True)
        y_train_enriquecido = pd.concat([y_train.reset_index(drop=True), y_externo], ignore_index=True)
        evaluacion_enriquecida = ajustar_y_evaluar(x_train_enriquecido, y_train_enriquecido)
    else:
        evaluacion_enriquecida = evaluacion_base

    variacion_f1_por_clase = {
        clase: evaluacion_enriquecida["f1_por_clase"][clase]
        - evaluacion_base["f1_por_clase"][clase]
        for clase in evaluacion_base["f1_por_clase"]
    }
    peor_variacion_f1_clase = min(variacion_f1_por_clase.values(), default=0.0)

    usar_externos = bool(
        len(datos_externos)
        and evaluacion_enriquecida["f1_macro"] > evaluacion_base["f1_macro"]
        and evaluacion_enriquecida["exactitud"] >= evaluacion_base["exactitud"] - 0.002
        and evaluacion_enriquecida["ece"] <= evaluacion_base["ece"] + 0.02
        and peor_variacion_f1_clase >= -0.10
    )
    evaluacion_seleccionada = evaluacion_enriquecida if usar_externos else evaluacion_base
    modelo_evaluacion = evaluacion_seleccionada["modelo"]
    predicciones = evaluacion_seleccionada["predicciones"]
    probabilidades = evaluacion_seleccionada["probabilidades"]

    umbral = umbral_seguro(probabilidades, y_test_array, modelo_evaluacion.classes_)
    ece = error_calibracion_esperado(
        probabilidades, y_test_array, modelo_evaluacion.classes_
    )
    indices_clase = {clase: i for i, clase in enumerate(modelo_evaluacion.classes_)}
    one_hot = np.zeros_like(probabilidades)
    for fila, etiqueta in enumerate(y_test_array):
        one_hot[fila, indices_clase[etiqueta]] = 1.0
    brier_multiclase = float(np.mean(np.sum((probabilidades - one_hot) ** 2, axis=1)))
    reporte_holdout = classification_report(
        y_test, predicciones, output_dict=True, zero_division=0
    )
    soporte_holdout = y_test.value_counts()
    f1_por_clase = {
        clase: float(valores["f1-score"])
        for clase, valores in reporte_holdout.items()
        if clase not in {"accuracy", "macro avg", "weighted avg"}
    }
    peor_f1_holdout = min(f1_por_clase.values())
    bloqueos_produccion = []
    if int(soporte_holdout.min()) < 5:
        bloqueos_produccion.append("Hay clases con menos de 5 casos en holdout")
    if peor_f1_holdout < 0.60:
        bloqueos_produccion.append("Hay clases con F1 inferior a 0.60 en holdout")
    if ece > 0.10:
        bloqueos_produccion.append("El error de calibracion ECE supera 0.10")
    if any(fold["clases_ausentes_validacion"] for fold in soporte_particiones_cv):
        bloqueos_produccion.append("Hay clases ausentes en particiones de validacion cruzada")

    x_final = pd.concat([x, x_externo], ignore_index=True) if usar_externos else x
    y_final = pd.concat([y, y_externo], ignore_index=True) if usar_externos else y
    vec_final = vectorizador()
    x_completo = vec_final.fit_transform(x_final)
    modelo_final = CalibratedClassifierCV(estimadores()[ganador], method="sigmoid", cv=3)
    modelo_final.fit(x_completo, y_final)

    directorio = Path("models")
    directorio.mkdir(exist_ok=True)
    ruta_modelo = directorio / "modelo_diagnostico.pkl"
    ruta_vectorizador = directorio / "vectorizador_tfidf.pkl"
    joblib.dump(modelo_final, ruta_modelo, compress=3)
    joblib.dump(vec_final, ruta_vectorizador, compress=3)

    metricas = {
        "version": "2.2.0-external-audited",
        "algoritmo_ganador_cv": ganador,
        "exactitud_holdout_agrupado": float(accuracy_score(y_test, predicciones)),
        "f1_macro_holdout_agrupado": float(
            f1_score(y_test, predicciones, average="macro", zero_division=0)
        ),
        "f1_weighted_holdout_agrupado": float(
            f1_score(y_test, predicciones, average="weighted", zero_division=0)
        ),
        "cv_4fold_agrupado": resultados_cv,
        "soporte_particiones_cv": soporte_particiones_cv,
        "soporte_holdout_por_clase": {
            str(clase): int(soporte) for clase, soporte in soporte_holdout.items()
        },
        "clases_holdout_soporte_menor_5": sorted(
            str(clase) for clase, soporte in soporte_holdout.items() if soporte < 5
        ),
        "reporte_holdout_por_clase": reporte_holdout,
        "peor_f1_holdout_por_clase": peor_f1_holdout,
        "aprobado_modelo_para_produccion": not bloqueos_produccion,
        "bloqueos_produccion": bloqueos_produccion,
        "error_calibracion_esperado": ece,
        "brier_multiclase": brier_multiclase,
        "umbral_baja_confianza": umbral,
        "registros": int(len(x_final)),
        "registros_base": int(len(datos)),
        "registros_externos_disponibles": int(len(datos_externos)),
        "registros_externos_incorporados": int(len(datos_externos) if usar_externos else 0),
        "dataset_externo_seleccionado": usar_externos,
        "comparacion_enriquecimiento_externo": {
            "base": {
                "exactitud": evaluacion_base["exactitud"],
                "f1_macro": evaluacion_base["f1_macro"],
                "f1_weighted": evaluacion_base["f1_weighted"],
                "ece": evaluacion_base["ece"],
            },
            "enriquecido": {
                "exactitud": evaluacion_enriquecida["exactitud"],
                "f1_macro": evaluacion_enriquecida["f1_macro"],
                "f1_weighted": evaluacion_enriquecida["f1_weighted"],
                "ece": evaluacion_enriquecida["ece"],
            },
            "criterio": (
                "Solo incorporar si mejora F1 macro, mantiene exactitud y calibracion, "
                "y ninguna clase pierde mas de 0.10 de F1."
            ),
            "peor_variacion_f1_clase": peor_variacion_f1_clase,
            "clases_mejoradas": {
                clase: delta
                for clase, delta in variacion_f1_por_clase.items()
                if delta > 0.001
            },
            "clases_empeoradas": {
                clase: delta
                for clase, delta in variacion_f1_por_clase.items()
                if delta < -0.001
            },
        },
        "familias_sintoma": int(grupos.nunique()),
        "clases": int(y.nunique()),
        "sha256_modelo": sha256(ruta_modelo),
        "sha256_vectorizador": sha256(ruta_vectorizador),
    }
    (directorio / "metricas_modelo.json").write_text(
        json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    etiquetas = sorted(y.unique())
    matriz = confusion_matrix(y_test, predicciones, labels=etiquetas)
    figura, eje = plt.subplots(figsize=(18, 16))
    eje.imshow(matriz, interpolation="nearest", cmap="Blues")
    eje.set_title("Matriz de confusion - holdout agrupado por familia de sintoma")
    eje.set_xlabel("Prediccion")
    eje.set_ylabel("Real")
    figura.tight_layout()
    salida = Path("../docs/graficas/matriz_confusion_ml.png")
    salida.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(salida, dpi=160)
    plt.close(figura)

    print(json.dumps(metricas, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    entrenar_y_comparar()
