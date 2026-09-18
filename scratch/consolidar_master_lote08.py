"""
Consolidación de Fase 10 Lote 08 en dataset_fase10_master.csv.
Agrega los 200 registros aprobados de Lote 08 al Master existente de 1640 registros,
alcanzando exactamente 1840 registros y cubriendo 46 de las 61 clases.
"""

from pathlib import Path
import pandas as pd


def main():
    master_path = Path("machine_learning/data/fase10/dataset_fase10_master.csv")
    lote08_path = Path("dataset_fase10_lote_08.csv")

    print(f"Leyendo master actual: {master_path}")
    df_master = pd.read_csv(master_path, encoding="utf-8")
    print(f"Registros previos en Master: {len(df_master)}")
    assert len(df_master) == 1640, f"Error: esperados 1640 registros previos, hay {len(df_master)}"

    print(f"Leyendo lote 08: {lote08_path}")
    df_l8 = pd.read_csv(lote08_path, encoding="utf-8")
    assert len(df_l8) == 200, f"Error: esperados 200 registros en Lote 08, hay {len(df_l8)}"

    # Crear campos de linaje y trazabilidad
    df_l8_consolidado = df_l8.copy()
    df_l8_consolidado["source_dataset"] = "dataset_fase10_lote_08.csv"
    df_l8_consolidado["source_row_id"] = df_l8["id"]
    df_l8_consolidado["source_type"] = "LOTE_ESTRATIFICADO_L1_L2_L3"
    df_l8_consolidado["specificity_level"] = df_l8["nivel_informacion"]
    df_l8_consolidado["synthetic_or_original"] = df_l8["fuente"]

    # Verificar coincidencia de columnas
    assert set(df_master.columns) == set(df_l8_consolidado.columns), "Las columnas no coinciden con el Master"

    # Reordenar columnas exactamente igual al Master
    df_l8_consolidado = df_l8_consolidado[df_master.columns]

    # Concatenar
    df_master_actualizado = pd.concat([df_master, df_l8_consolidado], ignore_index=True)

    total_reg = len(df_master_actualizado)
    print(f"Total registros tras consolidación: {total_reg}")
    assert total_reg == 1840, f"Error: esperados 1840 registros, hay {total_reg}"

    clases_unicas = df_master_actualizado["clase_objetivo"].nunique()
    print(f"Clases únicas cubiertas: {clases_unicas} / 61")
    assert clases_unicas == 46, f"Error: esperadas 46 clases, hay {clases_unicas}"

    # Verificación de 40 registros por clase
    conteo_clases = df_master_actualizado["clase_objetivo"].value_counts()
    for c, cnt in conteo_clases.items():
        assert cnt == 40, f"Error: clase {c} tiene {cnt} != 40 registros"
    print("[OK] Las 46 clases tienen exactamente 40 registros cada una.")

    # Verificación de distribución acumulada de niveles
    conteo_niveles = df_master_actualizado["nivel_informacion"].value_counts().to_dict()
    print(f"Distribución acumulada de niveles: {conteo_niveles}")
    assert conteo_niveles.get("L1") == 460, f"L1 tiene {conteo_niveles.get('L1')} != 460"
    assert conteo_niveles.get("L2") == 690, f"L2 tiene {conteo_niveles.get('L2')} != 690"
    assert conteo_niveles.get("L3") == 690, f"L3 tiene {conteo_niveles.get('L3')} != 690"
    print("[OK] Distribución acumulada conforme: L1=460, L2=690, L3=690 (TOTAL=1840).")

    # Verificación de IDs únicos
    assert df_master_actualizado["id"].nunique() == 1840, "Error: Existen IDs duplicados en el Master"
    print("[OK] 1840 IDs únicos en el Master.")

    # Guardar master actualizado con codificación UTF-8
    df_master_actualizado.to_csv(master_path, index=False, encoding="utf-8")
    print(f"[EXITO] Master actualizado guardado en {master_path}")

    # Desglose por lote
    print("\nDesglose por lote:")
    print(df_master_actualizado["source_dataset"].value_counts())


if __name__ == "__main__":
    main()
