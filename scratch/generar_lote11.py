"""
Script de ensamblaje para el Lote 11 de Fase 10 (CARROCERIA_NEUMATICA - Camiones).
Une Clases 59, 60 y 61 generando dataset_fase10_lote_11.csv con exactamente 120 registros.
"""

import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath("."))
from scratch.lote11_clases_59_61 import obtener_casos_59_61

COLUMNAS = [
    "id",
    "id_grupo",
    "clase_objetivo",
    "macro_sistema",
    "nivel_informacion",
    "texto_usuario",
    "tipo_lenguaje",
    "condicion_operacion",
    "sintomas_presentes",
    "sintomas_negados",
    "dtc",
    "requiere_pregunta",
    "es_contrastivo",
    "clase_contrastiva",
    "fuente",
    "observaciones"
]

OUTPUT_FILE = "dataset_fase10_lote_11.csv"


def ensamblar_lote11():
    todos = obtener_casos_59_61(offset=1)
    assert len(todos) == 120, f"Error: Se esperaban 120 casos, se obtuvieron {len(todos)}"

    # Verificar IDs consecutivos
    for i, r in enumerate(todos, 1):
        esperado_id = f"F10-L11-{i:04d}"
        assert r["id"] == esperado_id, f"ID discrepante en posicion {i}: {r['id']} != {esperado_id}"

    # Guardar en CSV
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS)
        writer.writeheader()
        writer.writerows(todos)

    print(f"Archivo {OUTPUT_FILE} generado exitosamente.")
    print(f"Total registros: {len(todos)}")

    # Validaciones rapidas
    clases = Counter(r["clase_objetivo"] for r in todos)
    print("\nDistribucion por clase:")
    for c, n in clases.items():
        print(f"  - {c}: {n}")

    niveles = Counter(r["nivel_informacion"] for r in todos)
    print("\nDistribucion por nivel:")
    for niv, n in niveles.items():
        print(f"  - {niv}: {n}")

    dtc_l1 = sum(1 for r in todos if r["nivel_informacion"] == "L1" and r["dtc"].strip())
    dtc_l2 = sum(1 for r in todos if r["nivel_informacion"] == "L2" and r["dtc"].strip())
    dtc_l3 = sum(1 for r in todos if r["nivel_informacion"] == "L3" and r["dtc"].strip())
    print(f"\nDTCs: L1={dtc_l1}, L2={dtc_l2}, L3={dtc_l3}")

    sin_dtc_l2_l3 = sum(1 for r in todos if r["nivel_informacion"] in ("L2", "L3") and not r["dtc"].strip())
    print(f"L2/L3 sin DTC: {sin_dtc_l2_l3} / 90")

    contrastivos = sum(1 for r in todos if r["es_contrastivo"] == "SI")
    print(f"Casos contrastivos: {contrastivos} / 120")

    req_preg_l1 = sum(1 for r in todos if r["nivel_informacion"] == "L1" and r["requiere_pregunta"] == "SI")
    print(f"L1 con requiere_pregunta='SI': {req_preg_l1} / 30")


if __name__ == "__main__":
    ensamblar_lote11()
