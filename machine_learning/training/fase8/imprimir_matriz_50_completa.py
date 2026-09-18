"""Verificación exhaustiva de las 50 filas de la auditoría externa TEST."""

import json

with open("machine_learning/models/auditoria_fase8_50_casos_test.json", "r", encoding="utf-8") as f:
    data = json.load(f)

filas = data["filas"]
print(f"Total filas: {len(filas)}")

c_top1 = 0
c_top3 = 0
c_macro = 0
c_e2e = 0

for r in filas:
    t1 = r["top1_ok"]
    t3 = r["top3_ok"]
    mac = r["macro_ok"]
    e2e = r["e2e_ok"]
    if t1:
        c_top1 += 1
    if t3:
        c_top3 += 1
    if mac:
        c_macro += 1
    if e2e:
        c_e2e += 1

print("Recalculo desde las 50 filas:")
print(f"Top-1 ML:      {c_top1}/50 ({c_top1*2.0:.1f}%)")
print(f"Top-3 ML:      {c_top3}/50 ({c_top3*2.0:.1f}%)")
print(f"Macro-Sistema: {c_macro}/50 ({c_macro*2.0:.1f}%)")
print(f"E2E Final:     {c_e2e}/50 ({c_e2e*2.0:.1f}%)")
