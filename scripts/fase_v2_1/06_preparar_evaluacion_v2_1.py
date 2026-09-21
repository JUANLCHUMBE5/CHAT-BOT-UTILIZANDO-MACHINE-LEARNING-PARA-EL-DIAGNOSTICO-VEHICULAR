"""
06_preparar_evaluacion_v2_1.py
FASE EXPERIMENTAL CARBOT V2.1 — FASES 9, 10 Y 11
1. Construye matriz de compatibilidad de combustible para las 61 clases canónicas (Fase 9).
2. Genera lista blanca de candidatos técnicos RAG (Fase 10): RAG_EXTERNAL_WHITELIST_CANDIDATES.csv.
3. Ensambla el Banco Ciego Secundario independiente (Fase 11): TEST_BLIND_V2_1_SECONDARY.csv.
"""
import sys
import os
import csv
import json
import random
from pathlib import Path
from collections import defaultdict
import pandas as pd

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
DATA_DIR = V2_1_DIR / "data"

TAXONOMIA_JSON = V2_1_DIR / "taxonomia_runtime_verificada.json"
DEV_DATASET_CSV = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "dev10_v1_1_macrofix.csv"
MAPEO_EXTERNOS_CSV = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2" / "data" / "MAPEO_EXTERNOS_48_CLASES.csv"

# Reglas de exclusión termodinámica por clase runtime (61 clases)
def clasificar_combustible_clase(clase: str) -> str:
    c_lower = clase.lower()
    # EV / Híbridos
    if any(x in c_lower for x in ["inversor de corriente", "alto voltaje (ev", "refrigeracion de bateria/inversor", "frenado regenerativo"]):
        return "EV_HYBRID"
    # Diésel exclusivo
    if any(x in c_lower for x in ["diesel", "common rail", "dpf / fap", "adblue", "maxi-brake", "frenos neumático", "secador aps"]):
        return "DIESEL_ONLY"
    # Gasolina exclusivo
    if any(x in c_lower for x in ["bujias o bobinas", "bomba de gasolina", "fscm", "gdi", "canister o valvula de purga", "p0420", "valvula iac"]):
        return "GASOLINE_ONLY"
    # Ambos / Universal
    return "BOTH"


def preparar():
    print("Iniciando Preparacion para Evaluacion V2.1 (Fases 9, 10, 11)...")

    # 1. Matriz de Combustible de 61 Clases (Fase 9)
    with open(TAXONOMIA_JSON, "r", encoding="utf-8") as f:
        tax_data = json.load(f)
    clases_61 = tax_data["clases_ordenadas"]

    matriz_combustible = {}
    for c in clases_61:
        compat = clasificar_combustible_clase(c)
        matriz_combustible[c] = {
            "fuel_compatibility": compat,
            "macro_sistema": tax_data["macro_sistemas"].get(c, "MOTOR") if isinstance(tax_data["macro_sistemas"], dict) else "MOTOR"
        }

    out_compat = DATA_DIR / "COMPATIBILIDAD_COMBUSTIBLE_61_CLASES.json"
    with open(out_compat, "w", encoding="utf-8") as f:
        json.dump(matriz_combustible, f, indent=2, ensure_ascii=False)
    print(f"Matriz de combustible de 61 clases guardada: {out_compat.name}")

    # 2. Whitelist de Candidatos RAG Externos de Alta Pureza (Fase 10)
    print("Filtrando candidatos para Whitelist RAG...")
    candidatos_rag = []
    with open(MAPEO_EXTERNOS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            src = r["fuente"]
            if src in ["zenodo_15626055", "mechanicdb_public"] or (src == "indecopi_peru" and float(r["mapping_confidence"]) >= 0.95):
                txt = r["texto"].strip()
                if len(txt) > 40 and not any(w in txt.lower() for w in ["risk of crash", "dealers will"]):
                    candidatos_rag.append({
                        "source": src,
                        "source_record_id": r["source_record_id"],
                        "componente": r["clase_original"],
                        "clase_carbot": r["carbot_class"],
                        "nivel_evidencia": r["evidence_type"],
                        "texto_procedimiento": txt[:180]
                    })

    out_rag_whitelist = V2_1_DIR / "RAG_EXTERNAL_WHITELIST_CANDIDATES.csv"
    with open(out_rag_whitelist, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(candidatos_rag[0].keys()))
        writer.writeheader()
        writer.writerows(candidatos_rag)
    print(f"Candidatos RAG Whitelist guardados: {out_rag_whitelist.name} ({len(candidatos_rag)} procedimientos)")

    # 3. Ensamblar Banco Ciego Secundario (Fase 11)
    # Seleccionar casos balanceados del conjunto dev no visto en train (3 por clase = 183 casos)
    print("Construyendo Banco Ciego Secundario (TEST_BLIND_V2_1_SECONDARY.csv)...")
    df_dev = pd.read_csv(DEV_DATASET_CSV)
    
    # Excluir casos piloto
    casos_piloto = ["ckp termico", "discos alabeados", "misfire bobina", "fuga boost hilux"]
    df_dev_clean = df_dev[~df_dev["texto_usuario"].str.lower().str.contains("|".join(casos_piloto), na=False)].copy()

    # Muestreo estratificado exacto: 3 casos por clase
    random.seed(1234)
    secundario_filas = []
    for c in clases_61:
        sub = df_dev_clean[df_dev_clean["clase_objetivo"] == c]
        if len(sub) >= 3:
            sel = sub.sample(n=3, random_state=42)
        else:
            sel = sub
        for _, r in sel.iterrows():
            secundario_filas.append({
                "id": r["id"],
                "clase_objetivo": r["clase_objetivo"],
                "macro_sistema": r.get("macro_sistema", "MOTOR"),
                "texto_usuario": r["texto_usuario"]
            })

    df_sec = pd.DataFrame(secundario_filas)
    out_sec = V2_1_DIR / "TEST_BLIND_V2_1_SECONDARY.csv"
    df_sec.to_csv(out_sec, index=False, encoding="utf-8")
    print(f"Banco ciego secundario guardado: {out_sec.name} ({len(df_sec)} casos, {df_sec['clase_objetivo'].nunique()} clases)")


if __name__ == "__main__":
    preparar()
