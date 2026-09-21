"""
Generador del Lote 07 de Fase 10 para CarBot.
Genera exactamente 320 registros de alta fidelidad automotriz para las Clases 34 a 41 (TRANSMISION):
- Clase 34: Disco de embrague desgastado o patinando
- Clase 35: Falla en bombin o bomba hidraulica de embrague
- Clase 36: Falta o degradacion de aceite de caja de cambios
- Clase 37: Rodajes de caja mecanica o diferencial gastados
- Clase 38: Sobrecalentamiento o solenoides en caja automatica CVT / DSG
- Clase 39: Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)
- Clase 40: Desgaste en collarin de empuje o crapodina de embrague
- Clase 41: Rodajes de transmision manual o eje primario gastados

Estructura: 40 por clase (10 L1, 15 L2, 15 L3) = 320 registros.
Distribución global obligatoria: 80 L1, 120 L2, 120 L3.
"""

import csv
import sys
from pathlib import Path

# Agregar raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scratch.lote07_clases_34_37 import obtener_casos_34_37
from scratch.lote07_clases_38_41 import obtener_casos_38_41


def generar_datos_lote07():
    casos_34_37 = obtener_casos_34_37(offset=1)
    casos_38_41 = obtener_casos_38_41(offset=161)

    todos = casos_34_37 + casos_38_41
    return todos


def main():
    casos = generar_datos_lote07()
    print(f"Total registros generados: {len(casos)}")
    assert len(casos) == 320, f"Error: se esperaban 320 registros, se obtuvieron {len(casos)}"

    out_file = Path("dataset_fase10_lote_07.csv")
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
