import json
from scripts.fase5_benchmark_v2_ground_truth import GROUND_TRUTH_G1, GROUND_TRUTH_G2

data = json.load(open("docs/graficas/reporte_evaluacion_nuevos_100_casos.json", encoding="utf-8"))
res = data["grupo_1"]["resultados"] + data["grupo_2"]["resultados"]
gts = GROUND_TRUTH_G1 + GROUND_TRUTH_G2

print("=== 14 CASOS PARCIALES (TOP 1 EN DIFERENCIAL ACEPTABLE) ===")
for i, (r, gt) in enumerate(zip(res, gts)):
    pred = r["falla_top1"]
    esp = gt["esperado"]
    acep = gt["aceptables"]
    if pred != esp and pred in acep:
        grp = "G1" if i < 50 else "G2"
        idx = (i % 50) + 1
        conf = r["confianza_top1"] * 100
        print(f"[{grp} #{idx:02d}] Conf: {conf:4.1f}% | Caso: {r['caso']}")
        print(f"       Esperado:  {esp}")
        print(f"       Predicho:  {pred}")
        print(f"       Top 2/3:   {r['top2_falla']} ({r['top2_conf']*100:.1f}%) / {r['top3_falla']} ({r['top3_conf']*100:.1f}%)\n")
