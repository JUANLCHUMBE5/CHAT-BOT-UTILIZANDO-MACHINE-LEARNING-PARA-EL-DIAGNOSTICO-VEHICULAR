import pandas as pd

df = pd.read_csv("scratch/muestra_semantica_46_lote07.csv")
print(f"Total en muestra: {len(df)}")

for idx, row in df.iterrows():
    print(f"[{row['id']}] ({row['nivel_informacion']}) {row['clase_objetivo']}")
    print(f"  Texto: {row['texto_usuario'][:130]}...")
    dtc_str = row['dtc'] if pd.notna(row['dtc']) else "None"
    cont_str = f"{row['es_contrastivo']} -> {row['clase_contrastiva']}" if row['es_contrastivo'] == 'SI' else "NO"
    print(f"  DTC: {dtc_str} | Cont: {cont_str}")
    print(f"  Presentes: {row['sintomas_presentes']} | Negados: {row['sintomas_negados']}")
    print("-" * 60)
