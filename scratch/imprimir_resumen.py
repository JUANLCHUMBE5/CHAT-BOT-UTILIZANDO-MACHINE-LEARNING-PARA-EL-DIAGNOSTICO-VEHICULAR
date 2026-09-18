import json

with open("docs/graficas/reporte_auditoria_50_casos_ground_truth.json", encoding="utf-8") as f:
    d = json.load(f)

print("=== METRICAS GLOBALES ===")
for k, v in d["metricas_globales"].items():
    print(f"{k}: {v}")

print("\n=== CASOS NO ESTRICTOS (Diferenciales o Incorrectos) ===")
for c in d["detalle_por_caso"]:
    if c["clasificacion_final_e2e"] != "CORRECTO ESTRICTO" or c["top1_ml_acierto"] != "SÍ":
        print(f"[{c['id']}] GT: {c['diagnostico_esperado']}")
        print(f"       Top-1: {c['top1_ml']} | Match: {c['top1_ml_acierto']}")
        print(f"       Top-2: {c['top2_ml']} | Top-3: {c['top3_ml']} | Top3 Match: {c['top3_ml_acierto']}")
        print(f"       Final E2E: {c['diagnostico_final_e2e']} | Clf: {c['clasificacion_final_e2e']}")
        print(f"       Macro: {c['macro_sistema_esperado']} -> {c['macro_sistema_predicho']} ({c['macro_sistema_correcto']})")
        print(f"       Interrogador: {c['auto_interrogador_status']}")
        print(f"       RAG: {c['documento_rag_utilizado']}")
        print(f"       Doc: {c['respaldo_documental_valores']}\n")
