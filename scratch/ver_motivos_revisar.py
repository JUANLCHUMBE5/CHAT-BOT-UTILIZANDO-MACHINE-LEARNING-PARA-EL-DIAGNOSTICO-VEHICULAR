import pandas as pd

df = pd.read_csv("fase10_auditoria_lote08.csv")
rev = df[df['estado_auditoria'] == 'REVISAR']
print(f"Total en REVISAR: {len(rev)}")
for idx, row in rev.iterrows():
    print(f"{row['id']} ({row['nivel_informacion']}) {row['clase_objetivo']}: {row['motivos']}")
