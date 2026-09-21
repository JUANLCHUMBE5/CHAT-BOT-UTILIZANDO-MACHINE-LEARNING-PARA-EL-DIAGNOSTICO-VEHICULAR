import json

data = json.load(open("docs/graficas/reporte_evaluacion_nuevos_100_casos.json", encoding="utf-8"))

print("="*90)
print("REPORTE GRUPO 1: 50 CASOS")
print("="*90)
for r in data["grupo_1"]["resultados"]:
    dtc = f" [DTC: {len(r['dtc_detectados'])}]" if r['dtc_detectados'] else ""
    print(f"#{r['idx']:02d} [{r['confianza_top1']*100:4.1f}%] {r['falla_top1']:<40} | Top2: {r['top2_falla']} ({r['top2_conf']*100:4.1f}%){dtc}")
    print(f"     Sintoma: {r['caso']}")

print("\n" + "="*90)
print("REPORTE GRUPO 2: 50 CASOS")
print("="*90)
for r in data["grupo_2"]["resultados"]:
    dtc = f" [DTC: {len(r['dtc_detectados'])}]" if r['dtc_detectados'] else ""
    print(f"#{r['idx']:02d} [{r['confianza_top1']*100:4.1f}%] {r['falla_top1']:<40} | Top2: {r['top2_falla']} ({r['top2_conf']*100:4.1f}%){dtc}")
    print(f"     Sintoma: {r['caso']}")
