import json
from pathlib import Path

with open("docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data = json.load(f)

casos = {c["id"]: c for c in data["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"}

casos_revisar = ["G1_11", "G1_12", "G1_25", "G1_28", "G1_33", "G1_39", "G1_41"]

print("=== REVISIÓN LITERAL DE LOS 7 CASOS FLAG ===\n")
for cid in casos_revisar:
    c = casos[cid]
    preds = c.get("predicciones_ml", [])
    p1 = preds[0]["falla"] if len(preds) > 0 else c.get("diagnostico_ml")
    p2 = preds[1]["falla"] if len(preds) > 1 else "N/A"
    p3 = preds[2]["falla"] if len(preds) > 2 else "N/A"
    
    inter = c.get("es_interactivo", False)
    if inter and "interaccion_turno2" in c:
        diag_final = c["interaccion_turno2"].get("diagnostico_final")
    else:
        diag_final = c.get("diagnostico_ml")
        
    rep = c.get("reporte_tecnico_completo", "")
    rag = c.get("titulo_rag", "")
    
    print(f"[{cid}]")
    print(f"  Usuario: {c['texto_usuario']}")
    print(f"  ML Top-1: '{p1}'")
    print(f"  ML Top-2: '{p2}'")
    print(f"  ML Top-3: '{p3}'")
    print(f"  Interactivo: {inter}")
    print(f"  Diag Final E2E: '{diag_final}'")
    print(f"  RAG Doc: '{rag}'")
    print("-" * 70)
