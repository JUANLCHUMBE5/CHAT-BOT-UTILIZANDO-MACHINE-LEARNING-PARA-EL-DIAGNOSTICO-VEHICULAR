"""Entrena y evalua GemaCar sin reemplazar automaticamente el modelo operativo."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
from entrenar_y_comparar_modelos import (
    error_calibracion_esperado,
    estimadores,
    normalizar_grupo,
    vectorizador,
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "models/experimentos/gemacar"


def sha256(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def evaluar(
    x_ajuste: pd.Series,
    y_ajuste: pd.Series,
    x_prueba: pd.Series,
    y_prueba: pd.Series,
    algoritmo: str,
) -> dict[str, object]:
    vec = vectorizador()
    x_ajuste_vec = vec.fit_transform(x_ajuste)
    x_prueba_vec = vec.transform(x_prueba)
    modelo = CalibratedClassifierCV(estimadores()[algoritmo], method="sigmoid", cv=3)
    modelo.fit(x_ajuste_vec, y_ajuste)
    predicciones = modelo.predict(x_prueba_vec)
    probabilidades = modelo.predict_proba(x_prueba_vec)
    reporte = classification_report(y_prueba, predicciones, output_dict=True, zero_division=0)
    return {
        "vectorizador": vec,
        "modelo": modelo,
        "exactitud": float(accuracy_score(y_prueba, predicciones)),
        "f1_macro": float(f1_score(y_prueba, predicciones, average="macro", zero_division=0)),
        "f1_weighted": float(
            f1_score(y_prueba, predicciones, average="weighted", zero_division=0)
        ),
        "ece": error_calibracion_esperado(
            probabilidades, y_prueba.to_numpy(), modelo.classes_
        ),
        "f1_por_clase": {
            clase: float(valores["f1-score"])
            for clase, valores in reporte.items()
            if clase not in {"accuracy", "macro avg", "weighted avg"}
        },
    }


def entrenar_experimento() -> dict[str, object]:
    base = pd.read_csv(DATA_DIR / "dataset_sintomas_limpio.csv", encoding="utf-8")
    zenodo = pd.read_csv(DATA_DIR / "dataset_externo_auditado.csv", encoding="utf-8-sig")
    gemacar = pd.read_csv(DATA_DIR / "dataset_gemacar_experimental.csv", encoding="utf-8-sig")

    etiquetas_base = set(base["falla"].astype(str).unique())
    zenodo = zenodo[zenodo["falla"].isin(etiquetas_base)].copy()
    gemacar = gemacar[gemacar["falla"].isin(etiquetas_base)].copy()

    x = base["sintoma"].astype(str).reset_index(drop=True)
    y = base["falla"].astype(str).reset_index(drop=True)
    grupos = x.map(normalizar_grupo)
    separador = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    indices_train, indices_test = next(separador.split(x, y, grupos))
    x_train, x_test = x.iloc[indices_train].reset_index(drop=True), x.iloc[indices_test]
    y_train, y_test = y.iloc[indices_train].reset_index(drop=True), y.iloc[indices_test]

    x_referencia = pd.concat([x_train, zenodo["sintoma"].astype(str)], ignore_index=True)
    y_referencia = pd.concat([y_train, zenodo["falla"].astype(str)], ignore_index=True)
    x_candidato = pd.concat(
        [x_referencia, gemacar["sintoma"].astype(str)], ignore_index=True
    )
    y_candidato = pd.concat(
        [y_referencia, gemacar["falla"].astype(str)], ignore_index=True
    )

    algoritmo = "Linear_SVM"
    referencia = evaluar(x_referencia, y_referencia, x_test, y_test, algoritmo)
    candidato = evaluar(x_candidato, y_candidato, x_test, y_test, algoritmo)
    variaciones = {
        clase: candidato["f1_por_clase"][clase] - referencia["f1_por_clase"][clase]
        for clase in referencia["f1_por_clase"]
    }
    peor_variacion = min(variaciones.values(), default=0.0)
    mejora_metricas = bool(
        candidato["f1_macro"] > referencia["f1_macro"]
        and candidato["exactitud"] >= referencia["exactitud"] - 0.002
        and candidato["ece"] <= referencia["ece"] + 0.02
        and peor_variacion >= -0.10
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ruta_modelo = OUTPUT_DIR / "modelo_diagnostico_experimental.pkl"
    ruta_vectorizador = OUTPUT_DIR / "vectorizador_tfidf_experimental.pkl"
    joblib.dump(candidato["modelo"], ruta_modelo, compress=3)
    joblib.dump(candidato["vectorizador"], ruta_vectorizador, compress=3)

    resultado = {
        "version": "experimento-gemacar-1.0",
        "algoritmo": algoritmo,
        "registros_base": int(len(base)),
        "registros_zenodo": int(len(zenodo)),
        "registros_gemacar_univocos": int(len(gemacar)),
        "grupos_gemacar_excluidos_por_multicausa": 21,
        "referencia_base_mas_zenodo": {
            clave: referencia[clave]
            for clave in ("exactitud", "f1_macro", "f1_weighted", "ece")
        },
        "candidato_con_gemacar": {
            clave: candidato[clave]
            for clave in ("exactitud", "f1_macro", "f1_weighted", "ece")
        },
        "peor_variacion_f1_por_clase": peor_variacion,
        "mejora_metricas": mejora_metricas,
        "promovido_a_produccion": False,
        "bloqueo_promocion": (
            "Pendiente de licencia reutilizable y validacion por mecanico; "
            "el artefacto queda entrenado solo para evaluacion."
        ),
        "sha256_modelo_experimental": sha256(ruta_modelo),
        "sha256_vectorizador_experimental": sha256(ruta_vectorizador),
    }
    (OUTPUT_DIR / "metricas_experimento.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resultado


if __name__ == "__main__":
    print(json.dumps(entrenar_experimento(), ensure_ascii=False, indent=2))
