"""
Ensamblador del Dataset de Entrenamiento Canónico Fase 8.
Combina la línea base Fase 7 (5,374 registros) con los nuevos casos independientes.
Garantiza 0% de solapamiento con DEV (60 casos) y TEST (G1_01-G1_50).
"""

import json
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))

from machine_learning.training.fase8.generador_expansiones_fase8 import generar_dataset_expansiones_fase8
from machine_learning.training.fase8.generar_casos_motor_fase8 import obtener_casos_motor_fase8
from machine_learning.training.fase8.generar_casos_chasis_frenos_fase8 import obtener_casos_chasis_frenos_fase8
from machine_learning.training.fase8.generar_casos_transmision_electrico_fase8 import obtener_casos_transmision_electrico_fase8
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema, FALLA_A_SISTEMA

def ensamblar():
    ruta_baseline = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_fase7_baseline.csv"
    ruta_out = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

    print(f"Cargando dataset baseline Fase 7 desde: {ruta_baseline}")
    df_base = pd.read_csv(ruta_baseline, encoding="utf-8")
    print(f"Filas baseline: {len(df_base)}")

    # Recopilar todos los casos nuevos independientes
    nuevos = []
    nuevos.extend(generar_dataset_expansiones_fase8())
    nuevos.extend(obtener_casos_motor_fase8())
    nuevos.extend(obtener_casos_chasis_frenos_fase8())
    nuevos.extend(obtener_casos_transmision_electrico_fase8())

    print(f"Total casos independientes recopilados para Fase 8: {len(nuevos)}")

    df_nuevos = pd.DataFrame(nuevos)
    df_nuevos["sintoma"] = df_nuevos["sintoma"].astype(str).str.strip()
    df_nuevos["falla"] = df_nuevos["falla"].astype(str).str.strip()
    df_nuevos["sistema"] = df_nuevos["falla"].apply(obtener_macro_sistema)
    df_nuevos["codigo_falla"] = "FASE8_AUTO"
    df_nuevos["severidad"] = "media"

    # Verificar que todas las fallas existan en la taxonomía
    invalidas = set(df_nuevos["falla"]) - set(FALLA_A_SISTEMA.keys())
    assert not invalidas, f"Fallas no reconocidas en taxonomia: {invalidas}"

    # Concatenar y deduplicar por síntoma
    df_final = pd.concat([df_base, df_nuevos], ignore_index=True)
    df_final = df_final.dropna(subset=["sintoma", "falla"])
    df_final["sintoma"] = df_final["sintoma"].astype(str).str.strip()
    df_final = df_final.drop_duplicates(subset=["sintoma"])

    # Cargar DEV y G1 para verificar solapamiento
    from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
    with open(BASE_DIR / "docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
        data_g1 = json.load(f)
    g1_casos = [c for c in data_g1["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"]

    dev_set = {c["sintoma"].lower().strip() for c in CASOS_DEV_60}
    g1_set = {c["texto_usuario"].lower().strip() for c in g1_casos}
    train_set = set(df_final["sintoma"].str.lower().str.strip())

    solap_dev = train_set.intersection(dev_set)
    solap_g1 = train_set.intersection(g1_set)

    assert len(solap_dev) == 0, f"Error: {len(solap_dev)} sintomas de TRAIN colisionan con DEV!"
    assert len(solap_g1) == 0, f"Error: {len(solap_g1)} sintomas de TRAIN colisionan con TEST G1!"

    print(f"Verificación de blindaje completada: 0 colisiones con DEV, 0 colisiones con TEST G1.")
    print(f"Total registros finales de entrenamiento para Fase 8: {len(df_final)}")
    print(f"Total clases únicas representadas: {df_final['falla'].nunique()} de {len(FALLA_A_SISTEMA)}")

    df_final.to_csv(ruta_out, index=False, encoding="utf-8")
    print(f"Dataset canónico actualizado en: {ruta_out}")

if __name__ == "__main__":
    ensamblar()
