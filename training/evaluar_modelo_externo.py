"""Evalúa el modelo con casos externos aplicando la taxonomía normalizada; no entrena ni mezcla datos de entrenamiento."""

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


def normalizar_etiqueta_falla(falla: str) -> str:
    """Mapea una etiqueta hacia la falla principal oficial si existe en la taxonomía."""
    f_limpia = str(falla).strip()
    if f_limpia in CATALOGO_TAXONOMIA:
        return CATALOGO_TAXONOMIA[f_limpia].falla_principal
    cod = MAPA_UNIFICACION_ETIQUETAS.get(f_limpia)
    if cod and cod in CATALOGO_TAXONOMIA:
        return CATALOGO_TAXONOMIA[cod].falla_principal
    return f_limpia


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
    args = parser.parse_args()

    datos = pd.read_csv(args.csv)
    requeridas = {"sintoma", "falla"}
    if not requeridas.issubset(datos.columns) or len(datos) < 30:
        raise SystemExit("Se requieren >=30 casos externos y columnas: sintoma,falla")

    modelo = joblib.load(args.modelo)
    vectorizador = joblib.load(args.vectorizador)

    y_real = datos["falla"].apply(normalizar_etiqueta_falla)
    preds_raw = modelo.predict(vectorizador.transform(datos["sintoma"].astype(str)))
    y_pred = pd.Series(preds_raw).apply(normalizar_etiqueta_falla)

    acc = accuracy_score(y_real, y_pred)
    f1_m = f1_score(y_real, y_pred, average="macro", zero_division=0)
    f1_w = f1_score(y_real, y_pred, average="weighted", zero_division=0)

    metricas = {
        "casos": len(datos),
        "accuracy": float(acc),
        "f1_macro": float(f1_m),
        "f1_weighted": float(f1_w),
        "reporte": classification_report(y_real, y_pred, output_dict=True, zero_division=0),
    }

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print("\n--- REPORTE DE EVALUACION EXTERNA INDEPENDIENTE ---")
    print(f"Casos evaluados:   {len(datos)}")
    print(f"Exactitud (Acc):   {acc * 100:.2f}%")
    print(f"F1-Macro Externo:  {f1_m * 100:.2f}%")
    print(f"F1-Weighted:       {f1_w * 100:.2f}%")
    print(json.dumps({"casos": metricas["casos"], "accuracy": acc, "f1_macro": f1_m}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
