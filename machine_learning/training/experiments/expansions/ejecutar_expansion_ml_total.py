import re
from pathlib import Path

import pandas as pd
from machine_learning.training.expandir_ml_bloque2 import casos_bloque2
from machine_learning.training.expandir_ml_bloque3 import casos_bloque3
from machine_learning.training.expandir_ml_masivo_350 import casos_por_categoria

BASE_DIR = Path(r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data")
LIMPIO_CSV = BASE_DIR / "dataset_sintomas_limpio.csv"
DATASET_CSV = BASE_DIR / "dataset_sintomas.csv"

def main():
    df_limpio = pd.read_csv(LIMPIO_CSV)
    clases_existentes = list(df_limpio["falla"].unique())
    print(f"Dataset limpio inicial: {len(df_limpio)} filas, {len(clases_existentes)} clases.")

    todos_los_bloques = {}
    todos_los_bloques.update(casos_por_categoria)
    todos_los_bloques.update(casos_bloque2)
    todos_los_bloques.update(casos_bloque3)

    print(f"Total categorias definidas en los 3 bloques: {len(todos_los_bloques)}")

    nuevas_filas = []
    textos_existentes = set(df_limpio["sintoma"].dropna().str.strip().str.lower())

    for cat_key, cat_data in todos_los_bloques.items():
        patron = cat_data["patron"]
        casos = cat_data["casos"]
        
        # Buscar clase correspondiente
        clase_target = None
        for c in clases_existentes:
            if re.search(patron, c, re.IGNORECASE):
                clase_target = c
                break
        
        if not clase_target:
            print(f"[ALERTA] No se encontro clase para patron: '{patron}' (clave: {cat_key})")
            continue

        for texto in casos:
            t_clean = texto.strip()
            if t_clean.lower() in textos_existentes:
                continue
            
            nuevas_filas.append({
                "sintoma": t_clean,
                "falla": clase_target,
                "codigo_falla": "N/A",
                "sistema": "General",
                "severidad": "media"
            })
            textos_existentes.add(t_clean.lower())

    print(f"Nuevas filas unicas a incorporar: {len(nuevas_filas)}")

    if not nuevas_filas:
        print("No hay nuevas filas para agregar.")
        return

    df_nuevas = pd.DataFrame(nuevas_filas)
    df_limpio_actualizado = pd.concat([df_limpio, df_nuevas], ignore_index=True)
    df_limpio_actualizado.to_csv(LIMPIO_CSV, index=False)
    print(f"[EXITO] Guardado {LIMPIO_CSV}. Total filas ahora: {len(df_limpio_actualizado)}")

    # Sincronizar dataset_sintomas.csv si existe
    if DATASET_CSV.exists():
        df_raw = pd.read_csv(DATASET_CSV)
        raw_textos = set(df_raw["sintoma"].dropna().str.strip().str.lower())
        filas_para_raw = []
        for nf in nuevas_filas:
            if nf["sintoma"].lower() not in raw_textos:
                filas_para_raw.append({"sintoma": nf["sintoma"], "falla": nf["falla"]})
                raw_textos.add(nf["sintoma"].lower())
        
        if filas_para_raw:
            df_nuevas_raw = pd.DataFrame(filas_para_raw)
            df_raw_actualizado = pd.concat([df_raw, df_nuevas_raw], ignore_index=True)
            df_raw_actualizado.to_csv(DATASET_CSV, index=False)
            print(f"[EXITO] Guardado {DATASET_CSV}. Total filas ahora: {len(df_raw_actualizado)}")

if __name__ == "__main__":
    main()
