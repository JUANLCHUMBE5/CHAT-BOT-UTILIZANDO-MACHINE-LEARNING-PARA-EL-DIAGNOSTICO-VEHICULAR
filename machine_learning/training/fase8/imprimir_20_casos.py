import json

with open("machine_learning/models/auditoria_fase8_50_casos_test.json", "r", encoding="utf-8") as f:
    data = json.load(f)

casos = [
    'G1_01', 'G1_06', 'G1_07', 'G1_09', 'G1_11', 'G1_12', 'G1_13', 'G1_18',
    'G1_19', 'G1_25', 'G1_28', 'G1_29', 'G1_33', 'G1_34', 'G1_41', 'G1_43',
    'G1_44', 'G1_45', 'G1_49', 'G1_50'
]
filas = {r['id']: r for r in data['filas']}
for cid in casos:
    r = filas[cid]
    t1_s = "OK" if r["top1_ok"] else "FAIL"
    t3_s = "OK" if r["top3_ok"] else "FAIL"
    e2_s = "OK" if r["e2e_ok"] else "FAIL"
    print(f"{cid} | T1:{t1_s} | T3:{t3_s} | E2E:{e2_s} | Esp: '{r['esperada']}'")
    print(f"     Top1: '{r['top1_ml']}' ({r['top1_conf']})")
    print(f"     Top2: '{r['top2_ml']}' ({r['top2_conf']})")
    print(f"     Top3: '{r['top3_ml']}' ({r['top3_conf']})")
    print(f"     E2E : '{r['diag_e2e']}'")
    print()
