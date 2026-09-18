"""
Consolidación de Fase 10 Lote 03 en dataset_fase10_master.csv.
Agrega los 200 registros aprobados de Lote 03 al Master existente de 400 registros,
alcanzando exactamente 600 registros y cubriendo 15 de las 61 clases.
"""

from pathlib import Path
import pandas as pd

def main():
    master_path = Path("machine_learning/data/fase10/dataset_fase10_master.csv")
    lote03_path = Path("dataset_fase10_lote_03.csv")
    
    print(f"Leyendo master actual: {master_path}")
    df_master = pd.read_csv(master_path, encoding="utf-8")
    print(f"Registros previos en Master: {len(df_master)}")
    assert len(df_master) == 400, f"Error: esperados 400 registros previos, hay {len(df_master)}"

    print(f"Leyendo lote 03: {lote03_path}")
    df_l3 = pd.read_csv(lote03_path, encoding="utf-8")
    assert len(df_l3) == 200, f"Error: esperados 200 registros en Lote 03, hay {len(df_l3)}"

    # Crear campos de linaje y trazabilidad
    df_l3_consolidado = df_l3.copy()
    df_l3_consolidado["source_dataset"] = "dataset_fase10_lote_03.csv"
    df_l3_consolidado["source_row_id"] = df_l3["id"]
    df_l3_consolidado["source_type"] = "LOTE_ESTRATIFICADO_L1_L2_L3"
    df_l3_consolidado["specificity_level"] = df_l3["nivel_informacion"]
    df_l3_consolidado["synthetic_or_original"] = df_l3["fuente"]

    # Verificar coincidencia de columnas
    assert set(df_master.columns) == set(df_l3_consolidado.columns), "Las columnas no coinciden con el Master"
    
    # Reordenar columnas exactamente igual al Master
    df_l3_consolidado = df_l3_consolidado[df_master.columns]

    # Concatenar
    df_master_actualizado = pd.concat([df_master, df_l3_consolidado], ignore_index=True)
    
    print(f"Total registros tras consolidación: {len(df_master_actualizado)}")
    assert len(df_master_actualizado) == 600, f"Error: esperados 600 registros, hay {len(df_master_actualizado)}"

    clases_unicas = df_master_actualizado["clase_objetivo"].nunique()
    print(f"Clases únicas cubiertas: {clases_unicas} / 61")
    assert clases_unicas == 15, f"Error: esperadas 15 clases, hay {clases_unicas}"

    # Guardar master actualizado con codificación UTF-8
    df_master_actualizado.to_csv(master_path, index=False, encoding="utf-8")
    print(f"[EXITO] Master actualizado guardado en {master_path}")

    # Desglose por lote
    print("\nDesglose por lote:")
    print(df_master_actualizado["source_dataset"].value_counts())

if __name__ == "__main__":
    main()
