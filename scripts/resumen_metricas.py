import json

with open("docs/graficas/reporte_evaluacion_100_casos.json", encoding="utf-8") as f:
    d = json.load(f)

for g_key, label in [("grupo_1", "1MER GRUPO (Flota Real Taller)"), ("grupo_2", "2DO GRUPO (Sintomatología Clínica Diversa)")]:
    g = d[g_key]
    print(f"=== {label} ===")
    confs = sorted([r["confianza_top1"] for r in g["resultados"]])
    p50 = confs[len(confs)//2]
    print(f"Promedio: {g['promedio_confianza']*100:.2f}% | Mediana: {p50*100:.2f}% | Min: {g['min_confianza']*100:.1f}% | Max: {g['max_confianza']*100:.1f}%")
    print(f">=80%: {g['casos_ge_80']}/50 ({g['casos_ge_80']*2}%) | >=70%: {g['casos_ge_70']}/50 ({g['casos_ge_70']*2}%) | >=60%: {g['casos_ge_60']}/50 ({g['casos_ge_60']*2}%)")
    print(f"Latencia ML: {g['prom_t_ml']:.2f} ms | Latencia RAG: {g['prom_t_rag']:.2f} ms\n")
