import pandas as pd

df = pd.read_csv("dataset_fase10_lote_08.csv")
aud = pd.read_csv("fase10_auditoria_lote08.csv")
rev_ids = aud[aud['estado_auditoria'] == 'REVISAR']['id'].tolist()

for r_id in rev_ids:
    row = df[df['id'] == r_id].iloc[0]
    print(f"[{row['id']}] ({row['nivel_informacion']}) {row['clase_objetivo']}")
    print(f"  Texto: {row['texto_usuario']}")
    print("-" * 60)
