"""
Generador del Lote 05 de Fase 10 para CarBot.
Genera exactamente 240 registros de alta fidelidad automotriz para las Clases 21 a 26:
- Clase 21: Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)
- Clase 22: Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)
- Clase 23: Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)
- Clase 24: Falla en regulador de presion de combustible o diafragma roto
- Clase 25: Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)
- Clase 26: Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados

Estructura: 40 por clase (10 L1, 15 L2, 15 L3) = 240 registros.
Distribución global obligatoria: 60 L1, 90 L2, 90 L3.
"""

import csv
import sys
from pathlib import Path

# Agregar raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scratch.lote05_clases_21_23 import obtener_casos_21_23
from scratch.lote05_clases_24_26 import obtener_casos_24_26


def generar_datos_lote05():
    casos_21_23 = obtener_casos_21_23(offset=1)
    casos_24_26 = obtener_casos_24_26(offset=121)

    todos = casos_21_23 + casos_24_26
    return todos


def main():
    casos = generar_datos_lote05()
    print(f"Total registros generados: {len(casos)}")
    assert len(casos) == 240, f"Error: se esperaban 240 registros, se obtuvieron {len(casos)}"

    out_file = Path("dataset_fase10_lote_05.csv")
    cols = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones"
    ]

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(casos)

    print(f"[OK] Archivo {out_file} guardado exitosamente con {len(casos)} registros.")


if __name__ == "__main__":
    main()
