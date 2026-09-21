"""
Script de muestreo y auditoría técnica manual/semántica estratificada de 30 casos para Lote 05.
5 por clase: 1 L1, 2 L2, 2 L3.
"""
import pandas as pd

df = pd.read_csv("dataset_fase10_lote_05.csv")

sample_ids = [
    # Clase 21 (CKP/CMP): L1, L2, L2, L3, L3
    'F10-L05-0001', 'F10-L05-0011', 'F10-L05-0015', 'F10-L05-0026', 'F10-L05-0037',
    # Clase 22 (EVAP): L1, L2, L2, L3, L3
    'F10-L05-0041', 'F10-L05-0051', 'F10-L05-0055', 'F10-L05-0066', 'F10-L05-0077',
    # Clase 23 (Catalizador): L1, L2, L2, L3, L3
    'F10-L05-0081', 'F10-L05-0091', 'F10-L05-0095', 'F10-L05-0106', 'F10-L05-0117',
    # Clase 24 (Regulador presion): L1, L2, L2, L3, L3
    'F10-L05-0121', 'F10-L05-0131', 'F10-L05-0135', 'F10-L05-0146', 'F10-L05-0157',
    # Clase 25 (Inyector individual): L1, L2, L2, L3, L3
    'F10-L05-0161', 'F10-L05-0171', 'F10-L05-0175', 'F10-L05-0186', 'F10-L05-0197',
    # Clase 26 (Perdida compresion): L1, L2, L2, L3, L3
    'F10-L05-0201', 'F10-L05-0211', 'F10-L05-0215', 'F10-L05-0226', 'F10-L05-0237'
]

sample = df[df['id'].isin(sample_ids)]
print(f"Total muestra seleccionada: {len(sample)} registros\n")

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
