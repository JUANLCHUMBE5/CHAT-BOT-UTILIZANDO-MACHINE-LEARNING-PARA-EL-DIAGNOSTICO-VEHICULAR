import json
import re
import unicodedata
import pandas as pd
from scratch.audit_l1_l2_l3_train import clasificar_ejemplo, normalizar_texto

df = pd.read_csv("machine_learning/data/dataset_sintomas_limpio.csv")

JERGA_TALLER = [
    "caña", "chancho", "chanchea", "se chupa", "no jala", "amarrado", "aguanta",
    "pata a fondo", "zapatea", "ratea", "cabecea", "corcovea", "chilla", "cascabelea",
    "muelle", "rompemuelle", "bache", "fierro", "patina", "bota el cambio", "se muere",
    "clac", "tac", "chirrido", "hierve", "esponjoso", "duro", "pesado"
]

clases_resumen = []

for falla, grupo in df.groupby("falla"):
    total = len(grupo)
    niveles = [clasificar_ejemplo(s) for s in grupo["sintoma"]]
    
    n_l1 = sum(1 for x in niveles if x["nivel"] == "L1")
    n_l2 = sum(1 for x in niveles if x["nivel"] == "L2")
    n_l3 = sum(1 for x in niveles if x["nivel"] == "L3")
    
    p_l1 = round((n_l1 / total) * 100, 1)
    p_l2 = round((n_l2 / total) * 100, 1)
    p_l3 = round((n_l3 / total) * 100, 1)
    
    sintomas_set = set()
    cond_set = set()
    disc_set = set()
    jerga_encontrada = set()
    
    for x in niveles:
        sintomas_set.update(x["sintomas"])
        cond_set.update(x["cond_op"])
        disc_set.update(x["disc_tec"])
        
    for s in grupo["sintoma"]:
        s_norm = normalizar_texto(s)
        for j in JERGA_TALLER:
            if j in s_norm:
                jerga_encontrada.add(j)
                
    # Variaciones lingüísticas: ratio de vocabulario único vs total palabras
    palabras_totales = [w for s in grupo["sintoma"] for w in normalizar_texto(s).split()]
    vocab_unico = len(set(palabras_totales))
    ratio_variacion = round(vocab_unico / max(1, len(palabras_totales)), 3)
    
    # Diagnóstico de cobertura
    # Criterio:
    # - Subrepresentada en L3: p_l3 < 2.0% o n_l3 == 0
    # - Subrepresentada en L1: p_l1 < 25% o n_l1 < 10
    # - Subrepresentada en L2: p_l2 < 20% o n_l2 < 10
    # - Bien cubierta: tiene presencia representativa en L1, L2 y L3
    estados = []
    if n_l3 == 0 or p_l3 < 1.0:
        estados.append("SUBREPRESENTADA EN L3")
    if n_l1 < 15 or p_l1 < 30.0:
        estados.append("SUBREPRESENTADA EN L1")
    if n_l2 < 10 or p_l2 < 20.0:
        estados.append("SUBREPRESENTADA EN L2")
    if not estados:
        estados.append("BIEN CUBIERTA")
        
    clases_resumen.append({
        "falla": falla,
        "total": total,
        "n_l1": n_l1,
        "p_l1": p_l1,
        "n_l2": n_l2,
        "p_l2": p_l2,
        "n_l3": n_l3,
        "p_l3": p_l3,
        "sintomas": sorted(list(sintomas_set)),
        "condiciones": sorted(list(cond_set)),
        "discriminadores": sorted(list(disc_set)),
        "jerga": sorted(list(jerga_encontrada)),
        "vocab_unico": vocab_unico,
        "ratio_variacion": ratio_variacion,
        "estado_cobertura": ", ".join(estados)
    })

# Guardar en archivo estructurado
with open("scratch/resumen_61_clases.json", "w", encoding="utf-8") as f:
    json.dump(clases_resumen, f, ensure_ascii=False, indent=2)

print(f"Auditoría de las {len(clases_resumen)} clases completada.")

# Resumen de estados
estados_conteo = {}
for c in clases_resumen:
    for e in c["estado_cobertura"].split(", "):
        estados_conteo[e] = estados_conteo.get(e, 0) + 1
print("\nResumen de estados de cobertura:")
for e, cnt in estados_conteo.items():
    print(f"  {e}: {cnt} clases")
