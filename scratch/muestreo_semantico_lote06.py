"""
Script de muestreo y auditoría técnica manual/semántica estratificada de 38 casos para Lote 06 (FRENOS).
5 por clase (1 L1, 2 L2, 2 L3) + 3 casos extra para Clase 32 (Frenado regenerativo) = 38 casos.
"""
import pandas as pd

df = pd.read_csv("dataset_fase10_lote_06.csv")

sample_ids = [
    # Clase 27 (Pastillas/Zapatas): L1, L2, L2, L3, L3 (5)
    'F10-L06-0001', 'F10-L06-0011', 'F10-L06-0015', 'F10-L06-0026', 'F10-L06-0037',
    # Clase 28 (Discos alabeados): L1, L2, L2, L3, L3 (5)
    'F10-L06-0041', 'F10-L06-0051', 'F10-L06-0055', 'F10-L06-0066', 'F10-L06-0077',
    # Clase 29 (Servofreno / Booster): L1, L2, L2, L3, L3 (5)
    'F10-L06-0081', 'F10-L06-0091', 'F10-L06-0095', 'F10-L06-0106', 'F10-L06-0117',
    # Clase 30 (Fuga hidraulica / aire): L1, L2, L2, L3, L3 (5)
    'F10-L06-0121', 'F10-L06-0131', 'F10-L06-0135', 'F10-L06-0146', 'F10-L06-0157',
    # Clase 31 (Sensor ABS): L1, L2, L2, L3, L3 (5)
    'F10-L06-0161', 'F10-L06-0171', 'F10-L06-0175', 'F10-L06-0186', 'F10-L06-0197',
    # Clase 32 (Frenado regenerativo): L1, L2, L2, L2, L3, L3, L3, L3 (8 - incluye 3 extra)
    'F10-L06-0201', 'F10-L06-0211', 'F10-L06-0212', 'F10-L06-0215', 'F10-L06-0226', 'F10-L06-0227', 'F10-L06-0230', 'F10-L06-0237',
    # Clase 33 (Caliper trabado): L1, L2, L2, L3, L3 (5)
    'F10-L06-0241', 'F10-L06-0251', 'F10-L06-0255', 'F10-L06-0266', 'F10-L06-0277'
]

sample = df[df['id'].isin(sample_ids)]
print(f"Total muestra seleccionada: {len(sample)} registros\n")
assert len(sample) == 38, f"Esperados 38 registros, obtenidos {len(sample)}"

for i, r in sample.iterrows():
    print("=" * 80)
    print(f"ID: {r['id']} | Nivel: {r['nivel_informacion']} | Lenguaje: {r['tipo_lenguaje']}")
    print(f"Clase Objetivo:   {r['clase_objetivo']}")
    print(f"DTC:              {r['dtc']} | Req Pregunta: {r['requiere_pregunta']}")
    print(f"Contrastivo:      {r['es_contrastivo']} -> {r['clase_contrastiva']}")
    print(f"Condicion:        {r['condicion_operacion']}")
    print(f"Texto Usuario:\n  \"{r['texto_usuario']}\"")
    print(f"Sintomas Presentes: {r['sintomas_presentes']}")
    print(f"Sintomas Negados:   {r['sintomas_negados']}")
    print(f"Observaciones:      {r['observaciones']}")
