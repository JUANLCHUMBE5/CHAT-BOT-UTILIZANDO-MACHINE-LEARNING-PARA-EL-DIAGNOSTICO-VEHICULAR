"""
Script de ensamblaje para el Lote 09 de Fase 10 (ELECTRICO).
Une Parte 1 (clases 47 a 49) y Parte 2 (clases 50 a 53)
generando dataset_fase10_lote_09.csv con exactamente 280 registros.
"""

import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath("."))
from scratch.lote09_clases_47_49 import obtener_casos_47_49
from scratch.lote09_clases_50_53 import obtener_casos_50_53

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

OUTPUT_FILE = "dataset_fase10_lote_09.csv"


def ensamblar_lote09():
    parte1 = obtener_casos_47_49(offset=1)
    parte2 = obtener_casos_50_53(offset=121)

    todos = parte1 + parte2
    assert len(todos) == 280, f"Error: Se esperaban 280 casos, se obtuvieron {len(todos)}"

    # Verificar IDs consecutivos
    for i, r in enumerate(todos, 1):
        esperado_id = f"F10-L09-{i:04d}"
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
    print(f"L2/L3 sin DTC: {sin_dtc_l2_l3} / 210")

    contrastivos = sum(1 for r in todos if r["es_contrastivo"] == "SI")
    print(f"Casos contrastivos: {contrastivos} / 280")

    req_preg_l1 = sum(1 for r in todos if r["nivel_informacion"] == "L1" and r["requiere_pregunta"] == "SI")
    print(f"L1 con requiere_pregunta='SI': {req_preg_l1} / 70")


if __name__ == "__main__":
    ensamblar_lote09()
