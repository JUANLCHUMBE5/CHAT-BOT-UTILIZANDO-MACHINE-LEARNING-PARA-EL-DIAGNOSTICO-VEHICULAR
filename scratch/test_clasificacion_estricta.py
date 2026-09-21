import json
import sys
from pathlib import Path

BASE_DIR = Path(".")
sys.path.insert(0, str(BASE_DIR))
from scripts.ground_truth_50_casos_data import GROUND_TRUTH_50

with open("docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data_rep = json.load(f)

casos_rep = {c["id"]: c for c in data_rep["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"}

for gt in GROUND_TRUTH_50:
    cid = gt["id"]
    c_rep = casos_rep[cid]
    preds = c_rep.get("predicciones_ml", [])
    top1 = preds[0]["falla"] if len(preds) > 0 else c_rep["diagnostico_ml"]
    top2 = preds[1]["falla"] if len(preds) > 1 else "Ninguno"
    top3 = preds[2]["falla"] if len(preds) > 2 else "Ninguno"
    
    if c_rep["es_interactivo"] and "interaccion_turno2" in c_rep:
        diag_final = c_rep["interaccion_turno2"]["diagnostico_final"]
    else:
        diag_final = top1
        
    top1_low = top1.lower()
    diag_final_low = diag_final.lower()
    
    # Evaluar estricto Top-1 ML
    top1_match = any(k.lower() in top1_low for k in gt["claves_estrictas"])
    
    # Evaluar estricto Final E2E
    final_strict = any(k.lower() in diag_final_low for k in gt["claves_estrictas"])
    
    # Evaluar Top-3 ML
    top3_match = any(
        any(k.lower() in p["falla"].lower() for k in gt["claves_estrictas"] + gt["claves_diferenciales"])
        for p in preds[:3]
    )
    
    # Determinar clasificación
    if final_strict:
        clf = "CORRECTO ESTRICTO"
    elif top3_match:
        clf = "DIFERENCIAL ACEPTABLE"
    else:
        clf = "INCORRECTO"
        
    if not final_strict and not top3_match:
        print(f"INCORRECTO -> {cid}: GT={gt['falla_esperada']} | Top1={top1} | Final={diag_final}")

