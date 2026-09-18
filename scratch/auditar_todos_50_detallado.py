import json
from pathlib import Path

with open("docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data = json.load(f)

casos = [c for c in data["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"]

out_path = Path("scratch/salida_50_detallada.txt")
with open(out_path, "w", encoding="utf-8") as out:
    for c in casos:
        cid = c["id"]
        txt = c["texto_usuario"]
        macro = c.get("macro_sistema")
        top1 = c.get("diagnostico_ml")
        conf1 = c.get("confianza_ml", 0)
        preds = c.get("predicciones_ml", [])
        p2 = preds[1]["falla"] if len(preds) > 1 else "N/A"
        p3 = preds[2]["falla"] if len(preds) > 2 else "N/A"
        inter = c.get("es_interactivo", False)
        t2 = c.get("interaccion_turno2", {}).get("diagnostico_final") if inter else top1
        rag = c.get("titulo_rag")
        sim = c.get("similitud_rag", 0)
        out.write(f"[{cid}] Macro={macro} | Top1={top1} ({conf1:.2f}) | Top2={p2} | Top3={p3} | Inter={inter} | Final={t2}\n")

print(f"Salida escrita en {out_path} en UTF-8")
