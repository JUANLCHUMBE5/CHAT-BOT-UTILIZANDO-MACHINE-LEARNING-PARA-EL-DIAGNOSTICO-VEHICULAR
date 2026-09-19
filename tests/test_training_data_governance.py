from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from machine_learning.training.entrenar_experimento_extendido import (  # noqa: E402
    _validar_aumento,
    crear_particiones_agrupadas,
)
from machine_learning.training.pipeline.preparar_correcciones_taller import (  # noqa: E402
    seleccionar_correcciones_confirmadas,
)


def test_aumento_sintetico_declara_origen_y_no_validacion_mecanica():
    datos = pd.read_csv(
        ROOT / "machine_learning" / "data" / "dataset_sintomas_aumento_taller.csv",
        encoding="utf-8",
    )
    _validar_aumento(datos)
    assert datos["grupo_origen"].nunique() < len(datos)


def test_holdout_agrupado_no_comparte_variantes():
    datos = pd.DataFrame(
        {
            "sintoma": [f"sintoma {clase} {grupo} {variante}" for clase in "ab" for grupo in range(5) for variante in range(2)],
            "falla": [f"falla-{clase}" for clase in "ab" for _grupo in range(5) for _variante in range(2)],
            "grupo_origen": [f"{clase}-{grupo}" for clase in "ab" for grupo in range(5) for _variante in range(2)],
        }
    )
    train_idx, test_idx = crear_particiones_agrupadas(datos)
    assert set(datos.iloc[train_idx]["grupo_origen"]).isdisjoint(
        set(datos.iloc[test_idx]["grupo_origen"])
    )


def test_correccion_whatsapp_no_entrena_sin_revision_y_evidencia():
    base = {
        "sintoma": "el motor vibra en neutro y golpea al acelerar",
        "falla_real": "Soportes de motor defectuosos",
        "metodo_confirmacion": "Inspección física",
        "evidencia_ref": "OT-001",
        "validado_por_id": "mecanico-1",
        "fecha_validacion": "2026-09-14T10:00:00-05:00",
        "origen_dato": "taller",
    }
    filas = [
        {**base, "estado_registro": "borrador"},
        {**base, "estado_registro": "verificado", "evidencia_ref": ""},
        {**base, "estado_registro": "verificado"},
    ]
    admitidas, rechazadas = seleccionar_correcciones_confirmadas(
        filas, {"Soportes de motor defectuosos"}
    )
    assert len(admitidas) == 1
    assert len(rechazadas) == 2
    assert admitidas[0]["estado_admision"] == "candidato_revision_ml"
    assert admitidas[0]["prioridad_validacion"] == "normal"
