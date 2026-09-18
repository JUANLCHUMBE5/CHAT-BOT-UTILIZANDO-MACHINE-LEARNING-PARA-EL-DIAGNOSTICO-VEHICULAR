"""
Generador del Lote 06 de Fase 10 para CarBot.
Genera exactamente 280 registros de alta fidelidad automotriz para las Clases 27 a 33 (FRENOS):
- Clase 27: Desgaste de pastillas y zapatas de freno
- Clase 28: Discos de freno alabeados o desgastados
- Clase 29: Falla en servofreno (booster) o linea de vacio
- Clase 30: Fuga hidraulica o aire en el sistema de frenos
- Clase 31: Falla en sensor de velocidad de rueda ABS
- Clase 32: Falla en sistema de frenado regenerativo (EV / Hibridos)
- Clase 33: Caliper de freno trabado o mordaza pegada (piston agarrotado)

Estructura: 40 por clase (10 L1, 15 L2, 15 L3) = 280 registros.
Distribución global obligatoria: 70 L1, 105 L2, 105 L3.
"""

import csv
import sys
from pathlib import Path

# Agregar raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scratch.lote06_clases_27_29 import obtener_casos_27_29
from scratch.lote06_clases_30_33 import obtener_casos_30_33


def generar_datos_lote06():
    casos_27_29 = obtener_casos_27_29(offset=1)
    casos_30_33 = obtener_casos_30_33(offset=121)

    todos = casos_27_29 + casos_30_33
    return todos


def main():
    casos = generar_datos_lote06()
    print(f"Total registros generados: {len(casos)}")
    assert len(casos) == 280, f"Error: se esperaban 280 registros, se obtuvieron {len(casos)}"

    out_file = Path("dataset_fase10_lote_06.csv")
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
