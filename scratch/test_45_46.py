import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.path.insert(0, str(Path("backend").resolve()))
from src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA
from scratch.lote08_clases_45_46 import obtener_casos_45_46

tax = set(FALLA_A_SISTEMA.keys())
casos = obtener_casos_45_46(121)
print(f"Total casos: {len(casos)}")
print(f"First ID: {casos[0]['id']}")
print(f"Last ID: {casos[-1]['id']}")

colisiones = []
for c in casos:
    assert c['clase_objetivo'] in tax, f"Clase invalida en {c['id']}: {c['clase_objetivo']}"
    assert c['macro_sistema'] == 'SUSPENSION_CHASIS', f"Macro invalido en {c['id']}"
    if c['nivel_informacion'] == 'L1':
        assert c['dtc'] == '', f"L1 con DTC en {c['id']}"
        assert c['requiere_pregunta'] == 'SI', f"L1 requiere_pregunta != SI en {c['id']}"
    if c['es_contrastivo'] == 'SI':
        assert c['clase_contrastiva'] in tax, f"Contrastiva invalida en {c['id']}: {c['clase_contrastiva']}"
        if c['clase_contrastiva'] == c['clase_objetivo']:
            colisiones.append((c['id'], c['clase_objetivo'], c['clase_contrastiva']))
    elif c['es_contrastivo'] == 'NO':
        assert c['clase_contrastiva'] == '', f"Contrastiva con NO en {c['id']}"

print(f"Colisiones encontradas: {len(colisiones)}")
for col in colisiones:
    print(col)

assert len(colisiones) == 0, "Hay colisiones contrastivas!"
print("Validacion completa 45-46 OK!")
