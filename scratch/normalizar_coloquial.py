"""
Normalización controlada de la etiqueta COLOQUIAL -> COTIDIANO para Fase 10.
Crea el dataset derivado dataset_fase10_master_v1_1_2440.csv sin alterar el snapshot v1 original.
Registra los 153 IDs afectados y genera el reporte de normalización.
"""

import pandas as pd
import hashlib
from pathlib import Path

V1_PATH = Path("machine_learning/data/fase10/dataset_fase10_master_v1_2440.csv")
V1_1_PATH = Path("machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv")
REPORTE_NORMALIZACION = Path("fase10_reporte_normalizacion_coloquial.csv")


def normalizar_coloquial():
    print(f"Leyendo snapshot original: {V1_PATH}")
    df = pd.read_csv(V1_PATH)
    assert len(df) == 2440, f"Error: esperados 2440 registros, hay {len(df)}"

    mask_coloquial = df["tipo_lenguaje"] == "COLOQUIAL"
    total_afectados = mask_coloquial.sum()
    print(f"Total registros con COLOQUIAL encontrados: {total_afectados}")
    assert total_afectados == 153, f"Se esperaban 153 registros, hay {total_afectados}"

    df_afectados = df[mask_coloquial][["id", "id_grupo", "clase_objetivo", "nivel_informacion", "source_dataset", "texto_usuario"]].copy()
    df_afectados["tipo_lenguaje_anterior"] = "COLOQUIAL"
    df_afectados["tipo_lenguaje_nuevo"] = "COTIDIANO"
    df_afectados.to_csv(REPORTE_NORMALIZACION, index=False, encoding="utf-8")
    print(f"Registro de 153 IDs guardado en: {REPORTE_NORMALIZACION}")

    # Aplicar normalización únicamente sobre tipo_lenguaje
    df_v1_1 = df.copy()
    df_v1_1.loc[mask_coloquial, "tipo_lenguaje"] = "COTIDIANO"

    # Verificar que no cambió ninguna otra columna
    for col in df.columns:
        if col != "tipo_lenguaje":
            assert (df[col].fillna("") == df_v1_1[col].fillna("")).all(), f"Discrepancia no autorizada en columna: {col}"

    assert (df_v1_1["tipo_lenguaje"] == "COLOQUIAL").sum() == 0, "Aún quedan registros con COLOQUIAL"
    conteo_cotidiano = (df_v1_1["tipo_lenguaje"] == "COTIDIANO").sum()
    print(f"Nuevo total de registros COTIDIANO: {conteo_cotidiano} (459 + 153 = 612)")
    assert conteo_cotidiano == 612, f"Error en conteo COTIDIANO: {conteo_cotidiano}"

    # Guardar en v1_1
    df_v1_1.to_csv(V1_1_PATH, index=False, encoding="utf-8")
    print(f"Nuevo dataset derivado guardado en: {V1_1_PATH}")

    # Hashes
    h_v1 = hashlib.sha256(open(V1_PATH, "rb").read()).hexdigest()
    h_v1_1 = hashlib.sha256(open(V1_1_PATH, "rb").read()).hexdigest()
    print(f"SHA-256 Snapshot v1 (INTACTO): {h_v1}")
    print(f"SHA-256 Snapshot v1.1 (TRABAJO): {h_v1_1}")
    assert h_v1 == "a645c7198faf7d3fad0af9cb681477f75e5f72292e09c442d899c286073bb232", "Snapshot v1 fue modificado!"


if __name__ == "__main__":
    normalizar_coloquial()
