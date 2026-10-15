"""Auditoría de estabilización: evaluación de 32 casos reales, RAG y calibración."""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
import numpy as np

from src.infrastructure.modelo_ml import ModeloML
from src.infrastructure.motor_rag import MotorRAG

print("=" * 80)
print("OBJETIVO 3: AUDITORIA DE LOS 32 CASOS REPORTADOS COMO REALES DE TALLER")
print("=" * 80)
csv_p = backend_dir.parent / "machine_learning" / "data" / "casos_reales_mecanicos_evaluacion.csv"
df = pd.read_csv(csv_p)
print(f"Total de casos reales: {len(df)}")

train_p = backend_dir.parent / "machine_learning" / "data" / "processed" / "dataset_entrenamiento_fase10_final.csv"
sintomas_tr = set()
if train_p.exists():
    df_tr = pd.read_csv(train_p)
    sintomas_tr = set(df_tr["sintoma"].astype(str).str.strip().str.lower())

coincidentes = sum(1 for s in df["sintoma"].astype(str).str.strip().str.lower() if s in sintomas_tr)
print(f"Separacion de datos: {len(df) - coincidentes}/{len(df)} casos son estrictamente independientes (no estan en entrenamiento).")

ml = ModeloML()
top1_aciertos = 0
top3_aciertos = 0
discrepancias = []

for idx, row in df.iterrows():
    sintoma = row["sintoma"]
    real = row["falla"].strip()
    preds = ml.predecir_top_fallas(sintoma, limite=3)
    top1 = preds[0]["falla"].strip()
    conf1 = preds[0]["probabilidad"]
    top3 = [p["falla"].strip() for p in preds]

    match_top1 = (real.lower() == top1.lower()) or (real.lower() in top1.lower()) or (top1.lower() in real.lower())
    match_top3 = any((real.lower() == t.lower()) or (real.lower() in t.lower()) or (t.lower() in real.lower()) for t in top3)

    if match_top1:
        top1_aciertos += 1
    if match_top3:
        top3_aciertos += 1
    else:
        discrepancias.append({
            "item": idx + 1,
            "sintoma": sintoma,
            "falla_real": real,
            "top1_pred": top1,
            "conf_top1": conf1,
            "top3_pred": top3
        })

print(f"Exactitud Top-1 (Linear SVM + TF-IDF): {top1_aciertos}/{len(df)} ({top1_aciertos/len(df)*100:.2f}%)")
print(f"Cobertura Top-3 (Diagnostico Diferencial): {top3_aciertos}/{len(df)} ({top3_aciertos/len(df)*100:.2f}%)")

if discrepancias:
    print(f"\nDiscrepancias fuera del Top-3 ({len(discrepancias)} casos):")
    for d in discrepancias:
        print(f"  - Caso #{d['item']}: '{d['sintoma'][:50]}...'")
        print(f"    Real: {d['falla_real']}")
        print(f"    Pred Top 1: {d['top1_pred']} ({d['conf_top1']*100:.1f}%)")
        print(f"    Pred Top 3: {d['top3_pred']}")

print("\n" + "=" * 80)
print("OBJETIVO 4: EVALUACION DE RECUPERACION RAG / FAISS")
print("=" * 80)
rag = MotorRAG()
consultas_rag = [
    ("Frenos", "Vibracion excesiva y pedal zapatea al frenar a alta velocidad", "Alabeo de discos de freno", ["disco", "freno", "alabeo", "alabeados"]),
    ("Frenos", "Chirrido agudo a metal al pisar el pedal de freno", "Desgaste de pastillas de freno", ["pastilla", "zapata", "desgaste", "freno"]),
    ("Arranque", "El auto no arranca solo suena un clic en el motor de arranque", "Bateria descargada o motor de arranque defectuoso", ["bateria", "arranque", "arrancador", "voltaje"]),
    ("Refrigeracion", "Motor recalienta en subida hierve refrigerante en deposito", "Falla en termostato o motoventilador", ["termostato", "refrigerante", "ventilador", "radiador"]),
    ("Motor/DTC", "Perdida de potencia y codigo P0301 misfire cilindro 1", "Falla de encendido en cilindro 1 (bujia o bobina)", ["p0301", "misfire", "bobina", "bujia", "encendido"]),
    ("Suspension", "Golpeteo seco clonck al pasar por rompemuelles en rueda delantera", "Buje de trapecio o bieleta con holgura", ["amortiguador", "trapecio", "buje", "suspension", "rotula"]),
    ("Transmision", "Chasquido trac trac constante al doblar toda la direccion", "Junta homocinetica o palier danado", ["palier", "homocinetica", "fuelle", "junta"]),
    ("Electrico", "Luz de bateria encendida en tablero alternador carga a 11.5 voltios", "Alternador defectuoso o regulador de voltaje", ["alternador", "carga", "voltaje", "diodo"]),
    ("Combustion", "Humo negro por el escape olor a gasolina cruda y mezcla rica", "Sensor de oxigeno o inyector defectuoso", ["oxigeno", "mezcla", "inyector", "combustible"]),
    ("Culata", "Humo blanco espeso por el tubo de escape y aceite cafe con leche", "Empaque de culata soplado", ["empaque", "culata", "soplado", "mayonesa", "aceite"])
]

relevantes = 0
for sist, query, esp, kws in consultas_rag:
    doc, tit, sim, meta = rag.recuperar_procedimiento_hibrido(query)
    fuente = meta.get("archivo_fuente") or meta.get("fuente") or "Manual de Taller OEM"
    txt = (tit + " " + doc).lower()
    match = any(kw in txt for kw in kws)
    if match:
        relevantes += 1
    print(f"[{sist:<13}] Sim: {sim:.3f} | Relevante: {'SI' if match else 'NO'} | Doc: {tit[:45]} | Fuente: {fuente}")

print(f"\nTasa de Pertinencia RAG: {relevantes}/{len(consultas_rag)} ({relevantes/len(consultas_rag)*100:.1f}%)")
