import json

with open("machine_learning/models/auditoria_fase8_50_casos_test.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== Casos Clave Solicitados por el Usuario ===")
casos_clave = [
    'G1_01', 'G1_06', 'G1_07', 'G1_09', 'G1_11', 'G1_12', 'G1_13', 'G1_18',
    'G1_19', 'G1_25', 'G1_28', 'G1_29', 'G1_33', 'G1_34', 'G1_41', 'G1_43',
    'G1_44', 'G1_45', 'G1_49', 'G1_50'
]
for row in data["filas"]:
    if row["id"] in casos_clave:
        t1_icon = "ACIERTO" if row["top1_ok"] else "FALLO"
        t3_icon = "ACIERTO" if row["top3_ok"] else "FALLO"
        e2e_icon = "ACIERTO" if row["e2e_ok"] else "FALLO"
        print(f"\n[{row['id']}] Esperada: '{row['esperada']}'")
        print(f"   Top-1 ML: '{row['top1_ml']}' ({row['top1_conf']}) -> {t1_icon}")
        print(f"   Top-2 ML: '{row['top2_ml']}' ({row['top2_conf']})")
        print(f"   Top-3 ML: '{row['top3_ml']}' ({row['top3_conf']}) -> Top-3: {t3_icon}")
        print(f"   E2E:      '{row['diag_e2e']}' -> {e2e_icon}")

print("\n--- Casos donde Top-1 ML falló pero Top-3 fue OK ---")
for row in data["filas"]:
    if not row["top1_ok"] and row["top3_ok"]:
        print(f"{row['id']}: Esperada='{row['esperada']}'\n   ML1='{row['top1_ml']}' (conf={row['top1_conf']})\n   ML2='{row['top2_ml']}' (conf={row['top2_conf']})\n   ML3='{row['top3_ml']}' (conf={row['top3_conf']})\n   E2E='{row['diag_e2e']}' (OK: {row['e2e_ok']})")

print("\n--- Casos donde Top-3 ML falló (los 5 fallos totales) ---")
for row in data["filas"]:
    if not row["top3_ok"]:
        print(f"{row['id']}: Esperada='{row['esperada']}'\n   ML1='{row['top1_ml']}' (conf={row['top1_conf']})\n   ML2='{row['top2_ml']}' (conf={row['top2_conf']})\n   ML3='{row['top3_ml']}' (conf={row['top3_conf']})\n   E2E='{row['diag_e2e']}'")
