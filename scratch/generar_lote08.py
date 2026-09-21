"""
Generador del Lote 08 de Fase 10 para CarBot.
Genera exactamente 200 registros de alta fidelidad automotriz para las Clases 42 a 46 (SUSPENSION_CHASIS):
- Clase 42: Amortiguadores reventados o bujes de suspension gastados (40 casos: 10 L1, 15 L2, 15 L3)
- Clase 43: Juntas homocineticas o palieres danados (40 casos: 10 L1, 15 L2, 15 L3)
- Clase 44: Llantas desbalanceadas o desalineadas (40 casos: 10 L1, 15 L2, 15 L3)
- Clase 45: Cremallera de direccion asistida con holgura o fuga (40 casos: 10 L1, 15 L2, 15 L3)
- Clase 46: Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura) (40 casos: 10 L1, 15 L2, 15 L3)

Estructura: 40 por clase (10 L1, 15 L2, 15 L3) = 200 registros.
Distribución global obligatoria: 50 L1, 75 L2, 75 L3.
"""

import csv
import sys
from pathlib import Path

# Agregar raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scratch.lote08_clases_42_44 import obtener_casos_42_44
from scratch.lote08_clases_45_46 import obtener_casos_45_46


def generar_datos_lote08():
    casos_42_44 = obtener_casos_42_44(offset=1)
    casos_45_46 = obtener_casos_45_46(offset=121)

    todos = casos_42_44 + casos_45_46
    return todos


def main():
    casos = generar_datos_lote08()
    print(f"Total registros generados: {len(casos)}")
    assert len(casos) == 200, f"Error: se esperaban 200 registros, se obtuvieron {len(casos)}"

    out_file = Path("dataset_fase10_lote_08.csv")
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
