import json
from pathlib import Path

with open("docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data_rep = json.load(f)

casos = [c for c in data_rep["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"]

output_file = Path("scratch/inspeccion_50_completa.txt")
with open(output_file, "w", encoding="utf-8") as out:
    for c in casos:
        cid = c["id"]
        out.write("=" * 80 + "\n")
        out.write(f"CASO: {cid}\n")
        out.write(f"Texto: {c['texto_usuario']}\n")
        out.write(f"Macro: {c.get('macro_sistema')}\n")
        out.write(f"Top-1: {c.get('diagnostico_ml')} ({c.get('confianza_ml'):.3f})\n")
        preds = c.get("predicciones_ml", [])
        out.write(f"Top-2: {preds[1]['falla'] if len(preds)>1 else 'N/A'}\n")
        out.write(f"Top-3: {preds[2]['falla'] if len(preds)>2 else 'N/A'}\n")
        out.write(f"Interactivo: {c.get('es_interactivo')}\n")
        if c.get("es_interactivo"):
            t2 = c.get("interaccion_turno2", {})
            out.write(f"Turno 2 Final: {t2.get('diagnostico_final')}\n")
        else:
            out.write(f"Final: {c.get('diagnostico_ml')}\n")
        out.write(f"RAG: {c.get('titulo_rag')}\n")

print(f"50 casos guardados en {output_file}")
