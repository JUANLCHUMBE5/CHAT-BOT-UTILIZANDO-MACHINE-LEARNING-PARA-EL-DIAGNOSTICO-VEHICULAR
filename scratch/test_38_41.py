import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.path.insert(0, str(Path("backend").resolve()))
from src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA
from scratch.lote07_clases_38_41 import obtener_casos_38_41

tax = set(FALLA_A_SISTEMA.keys())

casos = obtener_casos_38_41(161)
print(f"Total casos: {len(casos)}")
print(f"First ID: {casos[0]['id']}")
print(f"Last ID: {casos[-1]['id']}")

for c in casos:
    assert c['clase_objetivo'] in tax, f"Clase invalida en {c['id']}: {c['clase_objetivo']}"
    if c['nivel_informacion'] == 'L1':
        assert c['dtc'] == '', f"L1 con DTC en {c['id']}"
        assert c['requiere_pregunta'] == 'SI', f"L1 requiere_pregunta != SI en {c['id']}"
    if c['es_contrastivo'] == 'SI':
        assert c['clase_contrastiva'] in tax, f"Contrastiva invalida en {c['id']}: {c['clase_contrastiva']}"
        assert c['clase_contrastiva'] != c['clase_objetivo'], f"Contrastiva igual a objetivo en {c['id']}"
    elif c['es_contrastivo'] == 'NO':
        assert c['clase_contrastiva'] == '', f"Contrastiva con NO en {c['id']}"

print("Validacion 38-41 OK!")
