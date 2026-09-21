"""
Verificación de Cero Contaminación y Hashing Criptográfico a Priori
del Benchmark TEST FINAL CIEGO (100 Casos).
"""

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.data.benchmark_test_ciego_100 import BENCHMARK_TEST_CIEGO_100
from scripts.datos_prueba_grupo1 import GRUPO_1_CASOS

DATA_TRAIN = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

def norm(t: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", str(t).lower())
        if unicodedata.category(c) != "Mn"
    ).strip()

def main():
    print("=" * 90)
    print("AUDITORÍA DE INTEGRIDAD Y NO CONTAMINACIÓN — TEST FINAL CIEGO (100 CASOS)")
    print("=" * 90)

    # 1. Total de casos
    assert len(BENCHMARK_TEST_CIEGO_100) == 100, f"Error: esperados 100 casos, encontrados {len(BENCHMARK_TEST_CIEGO_100)}"
    print(f"Total de casos cargados: {len(BENCHMARK_TEST_CIEGO_100)}")

    # 2. Cargar TRAIN
    df_train = pd.read_csv(DATA_TRAIN)
    train_texts = set(norm(t) for t in df_train["sintoma"].values)
    clases_validas = set(df_train["falla"].unique())

    # 3. Cargar DEV y G1
    dev_texts = set(norm(c["sintoma"]) for c in CASOS_DEV_60)
    g1_texts = set(norm(c["texto"]) for c in GRUPO_1_CASOS)

    # 4. Verificar clases válidas y solapamiento
    solapamientos_train = 0
    solapamientos_dev = 0
    solapamientos_g1 = 0
    clases_invalidas = 0

    for c in BENCHMARK_TEST_CIEGO_100:
        cid = c["id"]
        s_norm = norm(c["sintoma"])
        falla = c["falla_esperada"]

        if falla not in clases_validas:
            print(f"[ERROR CLASE] {cid}: clase '{falla}' no está en las 61 clases válidas de TRAIN")
            clases_invalidas += 1

        if s_norm in train_texts:
            print(f"[CONTAMINACIÓN TRAIN] {cid}: texto coincide exactamente con TRAIN")
            solapamientos_train += 1

        if s_norm in dev_texts:
            print(f"[CONTAMINACIÓN DEV] {cid}: texto coincide exactamente con DEV")
            solapamientos_dev += 1

        if s_norm in g1_texts:
            print(f"[CONTAMINACIÓN G1] {cid}: texto coincide exactamente con G1")
            solapamientos_g1 += 1

    print(f"Clases inválidas: {clases_invalidas}")
    print(f"Solapamientos con TRAIN: {solapamientos_train}")
    print(f"Solapamientos con DEV:   {solapamientos_dev}")
    print(f"Solapamientos con G1:    {solapamientos_g1}")

    assert clases_invalidas == 0, "Hay clases inválidas"
    assert solapamientos_train == 0, "Contaminación detectada con TRAIN"
    assert solapamientos_dev == 0, "Contaminación detectada con DEV"
    assert solapamientos_g1 == 0, "Contaminación detectada con G1"

    print("\n[OK] VERIFICACIÓN DE CONTAMINACIÓN EXITOSA: 0.0% DE SOLAPAMIENTO.")

    # 5. Calcular Hash SHA-256 a priori
    ruta_archivo = BASE_DIR / "machine_learning" / "data" / "benchmark_test_ciego_100.py"
    h = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    sha = h.hexdigest()

    print(f"\nHASH SHA-256 A PRIORI DEL TEST CIEGO:\n{sha}")
    print(f"Ruta: {ruta_archivo}")
    print("=" * 90)

    # Guardar comprobante de hash previo
    comprobante = {
        "benchmark": "TEST_FINAL_CIEGO_100",
        "archivo": "machine_learning/data/benchmark_test_ciego_100.py",
        "sha256": sha,
        "total_casos": 100,
        "solapamiento_train": 0,
        "solapamiento_dev": 0,
        "solapamiento_g1": 0,
        "estado": "GROUND_TRUTH_FIJADO_A_PRIORI",
    }
    salida = BASE_DIR / "machine_learning" / "models" / "comprobante_hash_test_ciego_100.json"
    salida.write_text(json.dumps(comprobante, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Comprobante guardado en: {salida}")

if __name__ == "__main__":
    main()
