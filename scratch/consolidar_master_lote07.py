"""
Consolidación de Fase 10 Lote 07 en dataset_fase10_master.csv.
Agrega los 320 registros aprobados de Lote 07 al Master existente de 1320 registros,
alcanzando exactamente 1640 registros y cubriendo 41 de las 61 clases.
"""

from pathlib import Path
import pandas as pd


def main():
    master_path = Path("machine_learning/data/fase10/dataset_fase10_master.csv")
    lote07_path = Path("dataset_fase10_lote_07.csv")

    print(f"Leyendo master actual: {master_path}")
    df_master = pd.read_csv(master_path, encoding="utf-8")
    print(f"Registros previos en Master: {len(df_master)}")
    assert len(df_master) == 1320, f"Error: esperados 1320 registros previos, hay {len(df_master)}"

    print(f"Leyendo lote 07: {lote07_path}")
    df_l7 = pd.read_csv(lote07_path, encoding="utf-8")
    assert len(df_l7) == 320, f"Error: esperados 320 registros en Lote 07, hay {len(df_l7)}"

    # Crear campos de linaje y trazabilidad
    df_l7_consolidado = df_l7.copy()
    df_l7_consolidado["source_dataset"] = "dataset_fase10_lote_07.csv"
    df_l7_consolidado["source_row_id"] = df_l7["id"]
    df_l7_consolidado["source_type"] = "LOTE_ESTRATIFICADO_L1_L2_L3"
    df_l7_consolidado["specificity_level"] = df_l7["nivel_informacion"]
    df_l7_consolidado["synthetic_or_original"] = df_l7["fuente"]

    # Verificar coincidencia de columnas
    assert set(df_master.columns) == set(df_l7_consolidado.columns), "Las columnas no coinciden con el Master"

    # Reordenar columnas exactamente igual al Master
    df_l7_consolidado = df_l7_consolidado[df_master.columns]

    # Concatenar
    df_master_actualizado = pd.concat([df_master, df_l7_consolidado], ignore_index=True)

    total_reg = len(df_master_actualizado)
    print(f"Total registros tras consolidación: {total_reg}")
    assert total_reg == 1640, f"Error: esperados 1640 registros, hay {total_reg}"

    clases_unicas = df_master_actualizado["clase_objetivo"].nunique()
    print(f"Clases únicas cubiertas: {clases_unicas} / 61")
    assert clases_unicas == 41, f"Error: esperadas 41 clases, hay {clases_unicas}"

    # Verificación de 40 registros por clase
    conteo_clases = df_master_actualizado["clase_objetivo"].value_counts()
    for c, cnt in conteo_clases.items():
        assert cnt == 40, f"Error: clase {c} tiene {cnt} != 40 registros"
    print("[OK] Las 41 clases tienen exactamente 40 registros cada una.")

    # Verificación de distribución acumulada de niveles
    conteo_niveles = df_master_actualizado["nivel_informacion"].value_counts().to_dict()
    print(f"Distribución acumulada de niveles: {conteo_niveles}")
    assert conteo_niveles.get("L1") == 410, f"L1 tiene {conteo_niveles.get('L1')} != 410"
    assert conteo_niveles.get("L2") == 615, f"L2 tiene {conteo_niveles.get('L2')} != 615"
    assert conteo_niveles.get("L3") == 615, f"L3 tiene {conteo_niveles.get('L3')} != 615"
    print("[OK] Distribución acumulada conforme: L1=410, L2=615, L3=615 (TOTAL=1640).")

    # Verificación de IDs únicos
    assert df_master_actualizado["id"].nunique() == 1640, "Error: Existen IDs duplicados en el Master"
    print("[OK] 1640 IDs únicos en el Master.")

    # Guardar master actualizado con codificación UTF-8
    df_master_actualizado.to_csv(master_path, index=False, encoding="utf-8")
    print(f"[EXITO] Master actualizado guardado en {master_path}")

    # Desglose por lote
    print("\nDesglose por lote:")
    print(df_master_actualizado["source_dataset"].value_counts())


if __name__ == "__main__":
    main()
