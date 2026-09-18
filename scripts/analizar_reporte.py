import json

with open("docs/graficas/reporte_evaluacion_100_casos.json", encoding="utf-8") as f:
    data = json.load(f)

print("=== GRUPO 1: CASOS 1 A 25 ===")
for r in data["grupo_1"]["resultados"][:25]:
    dtc = f" [DTC: {r['dtc_detectados']}]" if r['dtc_detectados'] else ""
    print(f"[{r['idx']:02d}] {r['confianza_top1']*100:5.1f}% | {r['falla_top1']}{dtc}")
    print(f"     Caso: {r['caso']}")
    for alt in r['top_fallas'][1:]:
        print(f"       -> Top alt: {alt['probabilidad']*100:4.1f}% | {alt['falla']}")

