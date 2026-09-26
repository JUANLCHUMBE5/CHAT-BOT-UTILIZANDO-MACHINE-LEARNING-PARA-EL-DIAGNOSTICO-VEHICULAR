"""Verifica rigurosamente la calidad de los textos extraídos en nhtsa_complaints_unlabeled.jsonl.
Comprueba ausencia de textos vacíos, ausencia de 'IVOQ', longitudes y frases de síntomas reales.
"""
import json
import sys
from pathlib import Path

# La consola clásica de Windows puede seguir usando cp1252. Configurar una
# salida tolerante evita que una muestra Unicode válida interrumpa una auditoría
# de más de 300 mil registros.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "machine_learning" / "data" / "experimental_nhtsa" / "nhtsa_complaints_unlabeled.jsonl"

total = 0
empty_count = 0
ivoq_count = 0
lengths = []
sample_texts = []

check_indices = {0, 1000, 25000, 50000, 100000, 200000, 300000, 393739}

with path.open("r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        total += 1
        rec = json.loads(line)
        t = rec.get("text", "")
        if not t or not t.strip():
            empty_count += 1
        if t.strip() == "IVOQ" or t.strip().startswith("IVOQ"):
            ivoq_count += 1
        lengths.append(len(t))
        if i in check_indices:
            sample_texts.append((i, rec["make"], rec["model"], rec["model_year"], rec["component_reported"], t[:140]))

avg_len = sum(lengths) / len(lengths) if lengths else 0
min_len = min(lengths) if lengths else 0
max_len = max(lengths) if lengths else 0

print("================================================================================")
print("AUDITORÍA DE INTEGRIDAD TEXTUAL NHTSA COMPLAINTS")
print("================================================================================")
print(f"Total registros analizados: {total:,}")
print(f"Textos vacíos o sólo espacios: {empty_count}")
print(f"Textos que son o inician con 'IVOQ': {ivoq_count}")
print(f"Longitud mínima de texto: {min_len} caracteres")
print(f"Longitud promedio de texto: {avg_len:.1f} caracteres")
print(f"Longitud máxima de texto: {max_len:,} caracteres")
print("\nMuestras representativas a lo largo de todo el archivo:")
for idx, make, model, yr, comp, sample in sample_texts:
    clean_sample = sample.replace("\n", " ").replace("\r", " ")
    print(f"  [Reg {idx:,}] {yr} {make} {model} | {comp}\n    -> \"{clean_sample}...\"\n")
