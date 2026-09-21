import json
import sys

data = json.load(open("docs/graficas/reporte_evaluacion_nuevos_100_casos.json", encoding="utf-8"))

start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end = int(sys.argv[2]) if len(sys.argv) > 2 else 50

print("="*90)
print(f"REPORTE GRUPO 2: CASOS {start} AL {end}")
print("="*90)
for r in data["grupo_2"]["resultados"][start-1:end]:
    dtcs = ", ".join(r['dtc_detectados']) if r['dtc_detectados'] else "Sin DTC"
    print(f"#{r['idx']:02d} [{r['confianza_top1']*100:4.1f}%] {r['falla_top1']}")
    print(f"    Top 2: {r['top2_falla']} ({r['top2_conf']*100:4.1f}%) | Top 3: {r['top3_falla']} ({r['top3_conf']*100:4.1f}%)")
    print(f"    RAG: {r['similitud_rag']*100:4.1f}% -> {r['titulo_rag']}")
    print(f"    DTC: {dtcs}")
    print(f"    Caso: {r['caso']}\n")
