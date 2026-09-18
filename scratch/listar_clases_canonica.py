import sys
import re
import pandas as pd
from pathlib import Path

base_dir = Path('.').resolve()

# Let's inspect dataset_fase10_master_v1_1_2440.csv to get the exact class list in chronological order of lote insertion
df_f10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv")

# Each class in df_f10 has 40 rows. Let's see the order of appearance
unique_f10_ordered = []
for c in df_f10['clase_objetivo']:
    if c not in unique_f10_ordered:
        unique_f10_ordered.append(c)

print(f"Total unique classes in Fase 10 master in insertion order: {len(unique_f10_ordered)}")
for idx, c in enumerate(unique_f10_ordered, 1):
    macro = df_f10[df_f10['clase_objetivo'] == c]['macro_sistema'].iloc[0]
    print(f"{idx:02d}. [{macro}] {c}")
