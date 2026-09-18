import json
from pathlib import Path

BASE_DIR = Path(".")

with open("docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data_rep = json.load(f)

casos = [c for c in data_rep["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"]

casos_revisar = [
    "G1_01", "G1_06", "G1_07", "G1_09", "G1_11", "G1_12", "G1_13", "G1_18", "G1_19",
    "G1_25", "G1_28", "G1_29", "G1_33", "G1_34", "G1_41", "G1_43", "G1_44", "G1_45",
    "G1_49", "G1_50"
]

import sys
sys.stdout.reconfigure(encoding='utf-8')
output_file = Path("scratch/inspeccion_salida.txt")
with open(output_file, "w", encoding="utf-8") as out:
    for c in casos:
        cid = c["id"]
        if cid in casos_revisar:
            out.write("=" * 80 + "\n")
            out.write(f"CASO: {cid}\n")
            out.write(f"Usuario: {c['texto_usuario']}\n")
            out.write(f"Macro: {c.get('macro_sistema')}\n")
            out.write(f"Top-1 ML: {c.get('diagnostico_ml')} ({c.get('confianza_ml')})\n")
            out.write("Top-3 Preds:\n")
            for i, p in enumerate(c.get("predicciones_ml", [])[:3], 1):
                out.write(f"   {i}. {p['falla']} ({p.get('probabilidad', 0):.3f})\n")
            out.write(f"Interactivo: {c.get('es_interactivo')}\n")
            if c.get("es_interactivo"):
                out.write(f"Turno 1 Bot: {c.get('respuesta_inmediata_bot')[:150]}\n")
                t2 = c.get("interaccion_turno2", {})
                out.write(f"Turno 2 Final: {t2.get('diagnostico_final')} | Modo: {t2.get('modo_final')}\n")
            rep = c.get("reporte_tecnico_completo", "")
            out.write(f"Longitud reporte técnico: {len(rep)}\n")
            sec1_idx = rep.find("1. Posible Falla")
            sec2_idx = rep.find("2. Procedimiento")
            if sec1_idx != -1 and sec2_idx != -1:
                out.write("Sección 1 Diagnóstico Diferencial en Reporte:\n")
                out.write(rep[sec1_idx:sec2_idx].strip() + "\n")
            elif sec1_idx != -1:
                out.write(rep[sec1_idx:sec1_idx+400].strip() + "\n")
            else:
                out.write("Reporte directo:\n" + rep[:300].strip() + "\n")

print("Inspección guardada en scratch/inspeccion_salida.txt")

