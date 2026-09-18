import pandas as pd

df = pd.read_csv('test10_f83_vs_c1_by_class.csv')

print("Classes 59, 60, 61:")
targets_comfort = [
    'Elevalunas electrico o guaya de alzacristales rota o trabada',
    'Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado',
    'Falla electrica del cierre centralizado o actuador de puerta'
]
for c in targets_comfort:
    sub = df[df['clase'] == c]
    if not sub.empty:
        r = sub.iloc[0]
        print(f"  {r['clase'][:40]}: F8.3={r['f83_correct_top1']}/6, C1={r['c1_correct_top1']}/6, C1_T3={r['c1_top3_hits']}/6 | F1: {r['f83_f1']:.2f} -> {r['c1_f1']:.2f}")

print("\nClases degradadas en DEV10 (desempeño en TEST10):")
degraded = [
    'Falla de descarbonizacion e inyeccion directa GDI',
    'Fugas de aire o fallos en el sistema de frenos',
    'Limpiaparabrisas o motor pluma quemado'
]
for d in degraded:
    sub = df[df['clase'].str.contains(d, case=False, regex=False)]
    if not sub.empty:
        r = sub.iloc[0]
        print(f"  {r['clase'][:40]}: F8.3={r['f83_correct_top1']}/6, C1={r['c1_correct_top1']}/6, C1_T3={r['c1_top3_hits']}/6 | F1: {r['f83_f1']:.2f} -> {r['c1_f1']:.2f}")
