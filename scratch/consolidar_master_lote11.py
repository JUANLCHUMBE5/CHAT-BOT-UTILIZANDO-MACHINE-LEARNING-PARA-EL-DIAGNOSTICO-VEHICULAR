"""
Consolidación de Lote 11 en el Dataset Master de Fase 10 con trazabilidad y linaje completos.
Lleva el Master de 2320 a 2440 registros (61 de 61 clases completadas).
"""

import pandas as pd
from pathlib import Path
from collections import Counter

MASTER_PATH = Path("machine_learning/data/fase10/dataset_fase10_master.csv")
LOTE11_PATH = Path("dataset_fase10_lote_11.csv")


def consolidar_lote11():
    print(f"Leyendo Master actual desde: {MASTER_PATH}")
    df_master = pd.read_csv(MASTER_PATH)
    print(f"Master actual: {len(df_master)} filas, {df_master['clase_objetivo'].nunique()} clases.")

    # Si ya tiene 2440 filas porque se corrió antes, reajustamos a los primeros 2320 para re-consolidar limpiamente
    if len(df_master) == 2440:
        df_master = df_master.iloc[:2320].copy()
        print("Reajustado a los 2320 registros previos para consolidación canónica con linaje.")

    assert len(df_master) == 2320, f"Se esperaban 2320 filas previas, hay {len(df_master)}"

    print(f"Leyendo Lote 11 desde: {LOTE11_PATH}")
    df_l11 = pd.read_csv(LOTE11_PATH)
    print(f"Lote 11: {len(df_l11)} filas, {df_l11['clase_objetivo'].nunique()} clases.")
    assert len(df_l11) == 120, f"Se esperaban 120 filas en Lote 11, hay {len(df_l11)}"

    # Crear campos de linaje y trazabilidad idénticos a los lotes anteriores
    df_l11_consolidado = df_l11.copy()
    df_l11_consolidado["source_dataset"] = "dataset_fase10_lote_11.csv"
    df_l11_consolidado["source_row_id"] = df_l11["id"]
    df_l11_consolidado["source_type"] = "LOTE_ESTRATIFICADO_L1_L2_L3"
    df_l11_consolidado["specificity_level"] = df_l11["nivel_informacion"]
    df_l11_consolidado["synthetic_or_original"] = df_l11["fuente"]

    # Reordenar columnas exactamente igual al Master
    df_l11_consolidado = df_l11_consolidado[df_master.columns]

    # Concatenar
    df_nuevo_master = pd.concat([df_master, df_l11_consolidado], ignore_index=True)
    assert len(df_nuevo_master) == 2440, f"Error: esperadas 2440 filas, se obtuvieron {len(df_nuevo_master)}"

    # Validar distribución
    conteo_clases = df_nuevo_master["clase_objetivo"].value_counts()
    assert len(conteo_clases) == 61, f"Error: se esperaban 61 clases, hay {len(conteo_clases)}"
    for c, cnt in conteo_clases.items():
        assert cnt == 40, f"Clase {c} tiene {cnt} != 40 registros"

    conteo_niv = df_nuevo_master["nivel_informacion"].value_counts()
    assert conteo_niv["L1"] == 610, f"L1 = {conteo_niv['L1']} != 610"
    assert conteo_niv["L2"] == 915, f"L2 = {conteo_niv['L2']} != 915"
    assert conteo_niv["L3"] == 915, f"L3 = {conteo_niv['L3']} != 915"

    # Validar que los 2440 tengan linaje
    for col_lin in ["source_dataset", "source_row_id", "source_type", "specificity_level", "synthetic_or_original"]:
        assert df_nuevo_master[col_lin].isnull().sum() == 0, f"Hay valores nulos en {col_lin}"

    # Guardar
    df_nuevo_master.to_csv(MASTER_PATH, index=False, encoding="utf-8")
    print(f"\n[OK] Master consolidado con linaje completo exitosamente en: {MASTER_PATH}")
    print(f"Total registros: {len(df_nuevo_master)}")
    print(f"Total clases:    {len(conteo_clases)} / 61")
    print(f"Distribución:    L1={conteo_niv['L1']}, L2={conteo_niv['L2']}, L3={conteo_niv['L3']}")
    print(f"Columnas Master: {len(df_nuevo_master.columns)} (16 canónicas + 5 de linaje)")


if __name__ == "__main__":
    consolidar_lote11()
