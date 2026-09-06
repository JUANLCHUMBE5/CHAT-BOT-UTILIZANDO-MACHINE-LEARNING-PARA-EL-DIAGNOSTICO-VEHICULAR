"""Experimento reproducible y aislado: fuentes admitidas, sin publicar modelos.

Ejecutar desde machine_learning: ../.venv/Scripts/python.exe -m
training.entrenar_fuentes_auditadas. No modifica el modelo ni el RAG operativos.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from training.entrenar_y_comparar_modelos import (
    error_calibracion_esperado,
    normalizar_grupo,
    vectorizador,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIGURACIONES = {
    "palabras_base": (False, False),
    "palabras_zenodo": (False, True),
    "palabras_caracteres_base": (True, False),
    "palabras_caracteres_zenodo": (True, True),
}


def huella(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def validar_datos(base: pd.DataFrame, externo: pd.DataFrame) -> None:
    for datos in (base, externo):
        for campo in ("sintoma", "falla"):
            if datos[campo].isna().any() or datos[campo].astype(str).str.strip().eq("").any():
                raise ValueError(f"Campo obligatorio vacio: {campo}")
    requisitos = {
        "origen": "ZENODO_ACADEMICO",
        "doi": "10.5281/zenodo.15626055",
        "licencia": "CC BY 4.0",
        "estado_validacion": "AUDITADO_TAXONOMIA_NO_CASO_TALLER",
    }
    for campo, esperado in requisitos.items():
        if not externo[campo].eq(esperado).all():
            raise ValueError(f"Fuente externa no admitida: {campo}")
    catalogo = base[["codigo_falla", "falla"]].drop_duplicates()
    pares = set(catalogo.itertuples(index=False, name=None))
    if any(par not in pares for par in externo[["codigo_falla", "falla"]].itertuples(
        index=False, name=None
    )):
        raise ValueError("Etiqueta externa fuera de la taxonomia")


def sin_solapamientos(externo: pd.DataFrame, *reservados: pd.DataFrame) -> pd.DataFrame:
    """Excluye coincidencias normalizadas con base o evaluacion, aun con otra etiqueta."""
    grupos = {
        normalizar_grupo(texto)
        for datos in reservados
        for texto in datos["sintoma"]
    }
    copia = externo.copy()
    copia["_grupo"] = copia["sintoma"].map(normalizar_grupo)
    ambiguos = copia.groupby("_grupo")["falla"].nunique()
    copia = copia[~copia["_grupo"].isin(grupos | set(ambiguos[ambiguos > 1].index))]
    return copia.drop_duplicates("_grupo").drop(columns="_grupo").reset_index(drop=True)


def particiones(datos: pd.DataFrame, n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    grupos = datos["sintoma"].map(normalizar_grupo)
    cv = StratifiedGroupKFold(n_splits=n, shuffle=True, random_state=seed)
    partes = list(cv.split(datos["sintoma"], datos["falla"], grupos))
    for ajuste, validacion in partes:
        if set(grupos.iloc[ajuste]) & set(grupos.iloc[validacion]):
            raise ValueError("Fuga de familias entre particiones")
        if set(datos.iloc[ajuste]["falla"]) != set(datos["falla"]):
            raise ValueError("Faltan clases en ajuste; se necesitan mas familias independientes")
    return partes


def ajustar(datos: pd.DataFrame, caracteres: bool) -> CalibratedClassifierCV:
    features = vectorizador()
    if caracteres:
        features = FeatureUnion([
            ("palabras", vectorizador()),
            ("caracteres", TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5), strip_accents="unicode",
                sublinear_tf=True, min_df=2, max_features=40000,
            )),
        ])
    pipeline = Pipeline([
        ("texto", features),
        ("clasificador", LinearSVC(C=1.0, random_state=42, dual=False, max_iter=5000)),
    ])
    # Tanto el vocabulario como el clasificador se ajustan dentro de cada fold.
    modelo = CalibratedClassifierCV(
        pipeline, method="sigmoid", cv=particiones(datos, 3, 44), n_jobs=1,
    )
    modelo.fit(datos["sintoma"], datos["falla"])
    return modelo


def evaluar(modelo: CalibratedClassifierCV, datos: pd.DataFrame) -> dict:
    proba = modelo.predict_proba(datos["sintoma"])
    pred = modelo.classes_[proba.argmax(axis=1)]
    reporte = classification_report(
        datos["falla"], pred, labels=modelo.classes_, output_dict=True, zero_division=0,
    )
    return {
        "exactitud": float(accuracy_score(datos["falla"], pred)),
        "f1_macro": float(f1_score(
            datos["falla"], pred, labels=modelo.classes_, average="macro", zero_division=0,
        )),
        "ece": error_calibracion_esperado(proba, datos["falla"].to_numpy(), modelo.classes_),
        "por_clase": {str(clase): reporte[clase] for clase in modelo.classes_},
    }


def cumple_mejora(base: dict, candidato: dict) -> bool:
    return bool(
        candidato["f1_macro"] > base["f1_macro"]
        and candidato["exactitud"] >= base["exactitud"]
        and candidato["ece"] <= base["ece"] + 0.02
        and all(
            candidato["por_clase"][clase]["f1-score"] >= valores["f1-score"] - 0.10
            for clase, valores in base["por_clase"].items()
        )
    )


def bloqueos_produccion(metricas: dict) -> list[str]:
    bloqueos = [
        "Falta evaluacion independiente con nuevos casos confirmados por mecanicos.",
        "Pipeline experimental de texto: requiere adaptador y pruebas antes de usarlo en el backend.",
    ]
    if metricas["ece"] > 0.10:
        bloqueos.append("Error de calibracion ECE superior a 0.10.")
    if any(clase["support"] < 5 for clase in metricas["por_clase"].values()):
        bloqueos.append("Hay clases con menos de 5 ejemplos en la reserva historica.")
    if any(clase["f1-score"] < 0.60 for clase in metricas["por_clase"].values()):
        bloqueos.append("Hay clases con F1 inferior a 0.60.")
    return bloqueos


def entrenar(salida: Path) -> dict:
    salida = salida.resolve()
    raiz_experimentos = (ROOT / "models/experimentos").resolve()
    if not salida.is_relative_to(raiz_experimentos) or salida == raiz_experimentos:
        raise ValueError("La salida debe ser una subcarpeta nueva de models/experimentos")
    if salida.exists():
        raise ValueError("La salida ya existe; no se sobrescriben experimentos")

    rutas = {
        "base": ROOT / "data/dataset_sintomas_limpio.csv",
        "externo": ROOT / "data/dataset_externo_auditado.csv",
        "fuente_zenodo": ROOT / "data/fuentes_abiertas/zenodo_15626055.json",
    }
    md5 = hashlib.md5(rutas["fuente_zenodo"].read_bytes(), usedforsecurity=False).hexdigest()
    if md5 != "cb44431ef6b32f6ea9cf00dbe35f020c":
        raise ValueError("Checksum de la fuente Zenodo inesperado")
    originales = {
        nombre: huella(ROOT / "models" / nombre)
        for nombre in ("modelo_diagnostico.pkl", "vectorizador_tfidf.pkl", "metricas_modelo.json")
    }
    base = pd.read_csv(rutas["base"])
    externo = pd.read_csv(rutas["externo"], encoding="utf-8-sig")
    validar_datos(base, externo)
    externos_disponibles = len(externo)
    externo = sin_solapamientos(externo, base)
    indices_train, indices_test = particiones(base, 5, 42)[0]
    desarrollo = base.iloc[indices_train].reset_index(drop=True)
    holdout = base.iloc[indices_test].reset_index(drop=True)
    cv = particiones(desarrollo, 4, 43)
    resultados_cv = {}
    for nombre, (caracteres, enriquecer) in CONFIGURACIONES.items():
        scores = []
        print(f"Evaluando {nombre} (4 folds)...", flush=True)
        for ajuste, validacion in cv:
            datos = desarrollo.iloc[ajuste].reset_index(drop=True)
            if enriquecer:
                datos = pd.concat([datos, externo], ignore_index=True)
            modelo = ajustar(datos, caracteres)
            scores.append(evaluar(modelo, desarrollo.iloc[validacion])["f1_macro"])
        resultados_cv[nombre] = {
            "f1_macro_media": float(np.mean(scores)),
            "desviacion": float(np.std(scores)), "folds": scores,
        }
    ganador = max(resultados_cv, key=lambda nombre: (
        resultados_cv[nombre]["f1_macro_media"], -resultados_cv[nombre]["desviacion"],
    ))
    print(f"Seleccion por CV: {ganador}. Evaluando reserva historica...", flush=True)
    referencia = ajustar(desarrollo, False)
    datos_candidato = desarrollo
    caracteres, enriquecer = CONFIGURACIONES[ganador]
    if enriquecer:
        datos_candidato = pd.concat([desarrollo, externo], ignore_index=True)
    candidato = referencia if ganador == "palabras_base" else ajustar(datos_candidato, caracteres)
    met_base, met_candidato = evaluar(referencia, holdout), evaluar(candidato, holdout)
    # El modelo guardado tampoco ha visto el holdout: puede reproducir estas metricas.
    salida.mkdir(parents=True, exist_ok=False)
    joblib.dump(candidato, salida / "pipeline_experimental.joblib", compress=3)
    filas_holdout = set(indices_test)
    particion = pd.DataFrame({
        "fila_base": np.arange(len(base)),
        "familia_sha256": base["sintoma"].map(
            lambda texto: hashlib.sha256(normalizar_grupo(texto).encode()).hexdigest()
        ),
        "particion": ["holdout" if i in filas_holdout else "desarrollo" for i in range(len(base))],
    })
    particion.to_csv(salida / "particiones.csv", index=False)
    externo.to_csv(salida / "externos_admitidos.csv", index=False, encoding="utf-8-sig")
    sin_cambios = all(huella(ROOT / "models" / nombre) == sha for nombre, sha in originales.items())
    reporte = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "sklearn": sklearn.__version__, "seleccionado_cv": ganador,
        "registros_base": len(base), "desarrollo": len(desarrollo), "holdout": len(holdout),
        "externos_disponibles": externos_disponibles, "externos_sin_solapamientos": len(externo),
        "externos_en_candidato": len(externo) if enriquecer else 0,
        "nuevos_casos_externos_respecto_dataset_preexistente": 0,
        "cv_4fold": resultados_cv, "referencia_base": met_base, "candidato": met_candidato,
        "cumple_mejora_interna": cumple_mejora(met_base, met_candidato),
        "aprobado_modelo_para_produccion": False,
        "bloqueos_produccion": bloqueos_produccion(met_candidato),
        "promovido_a_produccion": False, "artefactos_operativos_intactos": sin_cambios,
        "sha256_operativos": originales,
        "sha256_entradas": {nombre: huella(ruta) for nombre, ruta in rutas.items()},
        "sha256_pipeline": huella(salida / "pipeline_experimental.joblib"),
        "sha256_script": huella(Path(__file__)),
        "limitaciones": [
            "Reserva historica reutilizada: no es una nueva prueba externa independiente.",
            "Agrupacion por normalizacion; no garantiza detectar todas las parafrasis semanticas.",
            "Zenodo tiene auditoria taxonomica, no confirmacion del taller local.",
            "Falta validar con casos reales nuevos y confirmados, excluidos del entrenamiento.",
            "No comparar con el modelo operativo sobre datos que este ya vio al entrenar.",
        ],
        "fuentes_no_admitidas": {
            "NHTSA": "Quejas sin causa confirmada: requieren etiquetado tecnico previo.",
            "Kaggle_Car_Diagnostic_Agent": "Licencia Unknown y procedencia no corroborada.",
            "UCI_APS_Scania": "Sensores numericos de camiones; no es clasificacion de texto.",
            "Scania_452071_textos": "Datos no publicados.",
            "GemaCar": "Sin licencia abierta declarada y pendiente validacion mecanica.",
        },
    }
    (salida / "reporte.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    if not sin_cambios:
        raise RuntimeError("Los artefactos operativos cambiaron durante el experimento")
    print(json.dumps({k: reporte[k] for k in (
        "seleccionado_cv", "cumple_mejora_interna", "promovido_a_produccion",
        "artefactos_operativos_intactos",
    )}, ensure_ascii=False, indent=2), flush=True)
    print(f"Reporte: {salida / 'reporte.json'}", flush=True)
    return reporte


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=ROOT / "models/experimentos" / (
        "fuentes_auditadas_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    ))
    entrenar(parser.parse_args().salida)
