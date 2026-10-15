import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from machine_learning.training.incorporar_casos_taller_400 import MAPA_DIAGNOSTICO_A_CANONICO

df = pd.read_csv('machine_learning/data/casos_taller_400_raw.csv', encoding='utf-8')

for cat, group in df.groupby('categoria'):
    print(f"=== {cat} ({len(group)} casos) ===")
    diags = group['diagnostico_principal'].unique()
    for d in diags[:4]:
        canon = MAPA_DIAGNOSTICO_A_CANONICO.get(d, '¡SIN MAPEO!')
        print(f"  • {d} -> [{canon}]")
    if len(diags) > 4:
        print(f"  ... (+{len(diags)-4} tipos más)")
    print()
