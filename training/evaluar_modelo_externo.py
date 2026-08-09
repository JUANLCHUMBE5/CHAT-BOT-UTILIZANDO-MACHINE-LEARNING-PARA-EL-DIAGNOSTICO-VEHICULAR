"""Evalua casos externos sin confundir columnas declaradas con evidencia verificable."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA, MAPA_UNIFICACION_ETIQUETAS


COLUMNAS_PROVENIENCIA = {
    "tipo_vehiculo",
    "metodo_confirmacion",
    "mecanico_validador",
    "fecha",
    "codigo_falla",
    "id_evidencia",
    "archivo_evidencia",
    "estado_validacion",
}


def normalizar_etiqueta_falla(falla: str) -> str:
    """Mapea una etiqueta hacia la falla principal canonica."""
    limpia = str(falla).strip()
    if limpia in CATALOGO_TAXONOMIA:
        return CATALOGO_TAXONOMIA[limpia].falla_principal
    codigo = MAPA_UNIFICACION_ETIQUETAS.get(limpia)
    if codigo and codigo in CATALOGO_TAXONOMIA:
        return CATALOGO_TAXONOMIA[codigo].falla_principal
    return limpia


def validar_proveniencia(
    datos: pd.DataFrame, evidencias_dir: Path
) -> tuple[bool, list[str]]:
    """Valida contenido, unicidad y existencia de cada respaldo fuera del CSV."""
    problemas: list[str] = []
    faltantes = sorted(COLUMNAS_PROVENIENCIA - set(datos.columns))
    if faltantes:
        return False, [f"Faltan columnas de proveniencia: {', '.join(faltantes)}"]

    for columna in sorted(COLUMNAS_PROVENIENCIA):
        vacias = datos[columna].fillna("").astype(str).str.strip().eq("")
        if vacias.any():
            problemas.append(f"{columna}: {int(vacias.sum())} valores vacios")

    ids = datos["id_evidencia"].fillna("").astype(str).str.strip()
    duplicados = int(ids[ids.ne("")].duplicated().sum())
    if duplicados:
        problemas.append(f"id_evidencia: {duplicados} identificadores duplicados")

    fechas = pd.to_datetime(datos["fecha"], errors="coerce", utc=True)
    if fechas.isna().any():
        problemas.append(f"fecha: {int(fechas.isna().sum())} fechas invalidas")

    estados = datos["estado_validacion"].fillna("").astype(str).str.lower().str.strip()
    no_validados = ~estados.isin({"validado", "aprobado"})
    if no_validados.any():
        problemas.append(f"estado_validacion: {int(no_validados.sum())} casos no validados")

    validadores = datos["mecanico_validador"].fillna("").astype(str).str.strip()
    if validadores[validadores.ne("")].nunique() < 2:
        problemas.append("Se requieren al menos dos mecanicos validadores independientes")

    raiz = evidencias_dir.resolve()
    archivos_faltantes = 0
    rutas_invalidas = 0
    for valor in datos["archivo_evidencia"].fillna("").astype(str):
        if not valor.strip():
            continue
        ruta = (raiz / valor.strip()).resolve()
        try:
            ruta.relative_to(raiz)
        except ValueError:
            rutas_invalidas += 1
            continue
        if not ruta.is_file():
            archivos_faltantes += 1
    if rutas_invalidas:
        problemas.append(f"archivo_evidencia: {rutas_invalidas} rutas fuera del directorio permitido")
    if archivos_faltantes:
        problemas.append(f"archivo_evidencia: {archivos_faltantes} respaldos no encontrados")

    return not problemas, problemas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, help="CSV externo con columnas sintoma y falla")
    default_vec = (
        Path("models/vectorizador_tfidf.pkl")
        if Path("models/vectorizador_tfidf.pkl").exists()
        else Path("models/vectorizador.pkl")
    )
    parser.add_argument("--modelo", type=Path, default=Path("models/modelo_diagnostico.pkl"))
    parser.add_argument("--vectorizador", type=Path, default=default_vec)
    parser.add_argument("--salida", type=Path, default=Path("models/metricas_externas.json"))
    parser.add_argument(
        "--evidencias-dir",
        type=Path,
        default=Path("data/evidencias_evaluacion"),
        help="Directorio privado con ordenes, fotos o actas referenciadas por el CSV",
    )
    args = parser.parse_args()

    datos = pd.read_csv(args.csv)
    if not {"sintoma", "falla"}.issubset(datos.columns) or len(datos) < 30:
        raise SystemExit("Se requieren >=30 casos externos y columnas: sintoma,falla")

    modelo = joblib.load(args.modelo)
    vectorizador = joblib.load(args.vectorizador)
    y_real = datos["falla"].apply(normalizar_etiqueta_falla)
    pred_raw = modelo.predict(vectorizador.transform(datos["sintoma"].astype(str)))
    y_pred = pd.Series(pred_raw).apply(normalizar_etiqueta_falla)

    proveniencia_verificable, problemas_proveniencia = validar_proveniencia(
        datos, args.evidencias_dir
    )
    minimo_por_clase = int(y_real.value_counts().min())

    entrenamiento = Path("data/dataset_sintomas_limpio.csv")
    solapamientos_exactos = 0
    if entrenamiento.exists():
        sintomas_train = set(
            pd.read_csv(entrenamiento)["sintoma"].astype(str).str.lower().str.strip()
        )
        solapamientos_exactos = int(
            datos["sintoma"].astype(str).str.lower().str.strip().isin(sintomas_train).sum()
        )

    etiquetas = sorted(y_real.unique())
    reporte = classification_report(
        y_real, y_pred, labels=etiquetas, output_dict=True, zero_division=0
    )
    acc = accuracy_score(y_real, y_pred)
    f1_macro = f1_score(y_real, y_pred, labels=etiquetas, average="macro", zero_division=0)
    f1_weighted = f1_score(
        y_real, y_pred, labels=etiquetas, average="weighted", zero_division=0
    )
    peor_f1_clase = min(float(reporte[etiqueta]["f1-score"]) for etiqueta in etiquetas)
    clases_modelo = set(map(str, getattr(modelo, "classes_", [])))
    clases_no_evaluadas = sorted(clases_modelo - set(etiquetas))

    bloqueos: list[str] = list(problemas_proveniencia)
    if len(datos) < 100:
        bloqueos.append("Se requieren al menos 100 casos externos")
    if minimo_por_clase < 10:
        bloqueos.append("Se requieren al menos 10 casos por clase evaluada")
    if clases_no_evaluadas:
        bloqueos.append(f"Faltan {len(clases_no_evaluadas)} clases activas por evaluar")
    if f1_macro < 0.80:
        bloqueos.append("F1-Macro externo inferior a 0.80")
    if peor_f1_clase < 0.60:
        bloqueos.append("Existe al menos una clase con F1 inferior a 0.60")
    if solapamientos_exactos:
        bloqueos.append("Existen sintomas externos repetidos en entrenamiento")

    aprobado = not bloqueos
    metricas = {
        "casos": int(len(datos)),
        "accuracy": float(acc),
        "f1_macro": float(f1_macro),
        "f1_weighted": float(f1_weighted),
        "peor_f1_por_clase": peor_f1_clase,
        "minimo_casos_por_clase": minimo_por_clase,
        "clases_evaluadas": len(etiquetas),
        "clases_modelo": len(clases_modelo),
        "clases_no_evaluadas": clases_no_evaluadas,
        "proveniencia_verificable": proveniencia_verificable,
        "problemas_proveniencia": problemas_proveniencia,
        "solapamientos_exactos_entrenamiento": solapamientos_exactos,
        "aprobado_produccion": aprobado,
        "bloqueos_produccion": bloqueos,
        "reporte": reporte,
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(
        json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n--- REPORTE DE EVALUACION EXTERNA ---")
    print(f"Casos evaluados: {len(datos)}")
    print(f"F1-Macro: {f1_macro * 100:.2f}%")
    print(f"Proveniencia verificable: {proveniencia_verificable}")
    print(f"Aprobado para produccion: {aprobado}")
    for bloqueo in bloqueos:
        print(f"- {bloqueo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
