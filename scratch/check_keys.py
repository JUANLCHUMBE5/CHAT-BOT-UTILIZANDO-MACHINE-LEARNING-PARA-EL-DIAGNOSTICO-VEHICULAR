import sys
from pathlib import Path
sys.path.insert(0, ".")
from scripts.ground_truth_50_casos_data import GROUND_TRUTH_50

for gt in GROUND_TRUTH_50:
    print(f"{gt['id']}: GT='{gt['falla_esperada'][:35]}' | Estrictas={gt['claves_estrictas']} | Dif={gt['claves_diferenciales']}")
