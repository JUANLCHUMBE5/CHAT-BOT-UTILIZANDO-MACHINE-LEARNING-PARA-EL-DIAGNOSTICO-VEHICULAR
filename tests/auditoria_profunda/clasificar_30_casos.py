"""Análisis y clasificación de los 30 casos de la auditoría profunda para la Fase 4."""

import joblib

from src.config import settings

try:
    from tests.auditoria_profunda.casos_01_a_10 import CASOS_01_A_10
    from tests.auditoria_profunda.casos_11_a_20 import CASOS_11_A_20
    from tests.auditoria_profunda.casos_21_a_30 import CASOS_21_A_30
except ImportError:
    from scratch.auditoria_profunda.casos_01_a_10 import CASOS_01_A_10
    from scratch.auditoria_profunda.casos_11_a_20 import CASOS_11_A_20
    from scratch.auditoria_profunda.casos_21_a_30 import CASOS_21_A_30

# Cargar modelo y clases
modelo = joblib.load(settings.paths.model_pkl)
vectorizador = joblib.load(settings.paths.vectorizer_pkl)
clases_entrenadas = list(modelo.classes_)

todos_los_casos = CASOS_01_A_10 + CASOS_11_A_20 + CASOS_21_A_30

print(f"Total casos cargados: {len(todos_los_casos)}")
print(f"Total clases entrenadas en SVM: {len(clases_entrenadas)}")

resultados = []

for c in todos_los_casos:
    cid = c.get("id")
    area = c.get("area")
    falla_confirmada = c.get("falla_confirmada")
    turnos = c.get("turnos", [])
    
    # Texto representativo del caso (primeros 3 turnos + DTC si existe)
    texto_eval = " ".join(turnos[:3])
    
    # Inferencia SVM con el vectorizador
    vec = vectorizador.transform([texto_eval])
    probs = modelo.predict_proba(vec)[0]
    top_indices = probs.argsort()[::-1][:5]
    top_predicciones = [
        {"clase": str(clases_entrenadas[idx]), "prob": round(float(probs[idx]), 4)}
        for idx in top_indices
    ]
    
    resultados.append({
        "id": cid,
        "area": area,
        "falla_confirmada": falla_confirmada,
        "top_1": top_predicciones[0],
        "top_3": top_predicciones[:3],
    })

for r in resultados:
    print(f"\n{r['id']}: Falla confirmada: '{r['falla_confirmada']}'")
    print(f"  Top 1: {r['top_1']['clase']} ({r['top_1']['prob']:.2%})")
    print(f"  Top 2: {r['top_3'][1]['clase']} ({r['top_3'][1]['prob']:.2%})")
    print(f"  Top 3: {r['top_3'][2]['clase']} ({r['top_3'][2]['prob']:.2%})")
