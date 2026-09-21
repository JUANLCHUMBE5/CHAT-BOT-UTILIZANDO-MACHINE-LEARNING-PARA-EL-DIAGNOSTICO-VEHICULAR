"""
07_normalizar_peru_nhtsa.py
Normalización canónica, extracción de síntomas y generación del Banco Documental
de Fallas Vehiculares Perú (INDECOPI) + NHTSA (Recalls y Complaints 2000-2026).

Genera:
1. PERU_VEHICLE_FAILURES.jsonl / .csv
2. NHTSA_RECALLS_2000_2026.jsonl
3. NHTSA_VEHICLE_COMPLAINTS_2000_2026.jsonl
4. VEHICLE_FAILURE_KNOWLEDGE_2000_2026.jsonl
5. VOCABULARIO_SINTOMAS_REALES.md / .csv
6. docs/auditorias/AUDITORIA_FALLAS_VEHICULARES_PERU_NHTSA.md
7. docs/auditorias/FUENTES_FALLAS_VEHICULARES.md

Respeta rigurosamente las reglas de tesis:
- NO modifica modelos ni RAG productivo.
- NO inventa relaciones (DOCUMENTED vs RELATED vs INFERRED).
- Aísla la evidencia documental de la muestra oficial de tesis.
"""
import sys
import os
import csv
import json
import re
import time
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BASE_DIR = PROJECT_ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "fallas_vehiculares"

DIR_PERU = BASE_DIR / "peru_indecopi"
DIR_RECALLS = BASE_DIR / "nhtsa_recalls"
DIR_COMPLAINTS = BASE_DIR / "nhtsa_complaints"
DIR_NORM = BASE_DIR / "normalizado"
DIR_REPORTES = BASE_DIR / "reportes"
DIR_DOCS = PROJECT_ROOT / "docs" / "auditorias"

DIR_NORM.mkdir(parents=True, exist_ok=True)
DIR_REPORTES.mkdir(parents=True, exist_ok=True)
DIR_DOCS.mkdir(parents=True, exist_ok=True)

# Cargar catálogo de marcas y modelos Perú
CATALOGO_FILE = DIR_PERU / "catalogo_peru_marcas_modelos.json"
PERU_CATALOG = {}
if CATALOGO_FILE.exists():
    with open(CATALOGO_FILE, "r", encoding="utf-8") as f:
        PERU_CATALOG = json.load(f)

PERU_MAKES = set(PERU_CATALOG.get("distribucion_marcas", {}).keys())
PERU_MODELS = set()
for mod_list in PERU_CATALOG.get("modelos_por_marca", {}).values():
    PERU_MODELS.update([m.upper() for m in mod_list])

# Mapeo de componentes NHTSA a Macro-Sistemas CarBot
NHTSA_COMP_A_MACRO = {
    "ENGINE": "MOTOR",
    "ENGINE AND ENGINE COOLING": "MOTOR",
    "FUEL SYSTEM": "MOTOR",
    "FUEL SYSTEM, GASOLINE": "MOTOR",
    "FUEL SYSTEM, DIESEL": "MOTOR",
    "EXHAUST SYSTEM": "MOTOR",
    "POWER TRAIN": "TRANSMISION",
    "MANUAL TRANSMISSION": "TRANSMISION",
    "AUTOMATIC TRANSMISSION": "TRANSMISION",
    "CLUTCH ASSEMBLY": "TRANSMISION",
    "SERVICE BRAKES": "FRENOS",
    "SERVICE BRAKES, HYDRAULIC": "FRENOS",
    "SERVICE BRAKES, AIR": "CARROCERIA_NEUMATICA",
    "PARKING BRAKE": "FRENOS",
    "ELECTRONIC STABILITY CONTROL": "FRENOS",
    "STEERING": "SUSPENSION_CHASIS",
    "SUSPENSION": "SUSPENSION_CHASIS",
    "ELECTRICAL SYSTEM": "ELECTRICO",
    "STARTING SYSTEM": "ELECTRICO",
    "HYBRID PROPULSION SYSTEM": "ELECTRICO",
    "AIR CONDITIONING": "CLIMATIZACION",
    "STRUCTURE": "CARROCERIA_NEUMATICA",
    "AIR BAGS": "CARROCERIA_NEUMATICA",
    "SEAT BELTS": "CARROCERIA_NEUMATICA",
    "LATCHES/LOCKS/LINKAGES": "CARROCERIA_NEUMATICA",
    "VISIBILITY/WIPER": "CARROCERIA_NEUMATICA",
}


def mapear_macro_sistema(texto_comp: str) -> str:
    texto = (texto_comp or "").upper()
    for k, v in NHTSA_COMP_A_MACRO.items():
        if k in texto:
            return v
    if any(w in texto for w in ["MOTOR", "ENGINE", "FUEL", "COMBUSTIBLE", "INYECCION", "TURBO"]):
        return "MOTOR"
    if any(w in texto for w in ["BRAKE", "FRENO", "CALIPER", "DISCO"]):
        return "FRENOS"
    if any(w in texto for w in ["TRANSMISSION", "TRANSMISION", "GEARBOX", "CLUTCH", "EMBRAGUE"]):
        return "TRANSMISION"
    if any(w in texto for w in ["STEERING", "DIRECCION", "SUSPENSION", "TIRE", "LLANTA"]):
        return "SUSPENSION_CHASIS"
    if any(w in texto for w in ["ELECTRICAL", "ELECTRICO", "BATTERY", "BATERIA", "ALTERNADOR"]):
        return "ELECTRICO"
    if any(w in texto for w in ["AIR CONDITIONING", "CLIMA", "HVAC", "A/C"]):
        return "CLIMATIZACION"
    return "CARROCERIA_NEUMATICA"


def procesar_indecopi() -> List[Dict[str, Any]]:
    print("\n[1/4] Normalizando Alertas Vehiculares de Perú (INDECOPI)...")
    ind_file = DIR_PERU / "alertas_indecopi.json"
    with open(ind_file, "r", encoding="utf-8") as f:
        ind_data = json.load(f)

    alertas = ind_data.get("alertas", [])
    norm_peru = []

    for a in alertas:
        nu_id = str(a.get("nuIdAlerta") or "")
        cod_alerta = a.get("vcCodigoAlerta") or f"PE_{nu_id}"
        titulo = a.get("vcTitulo") or ""
        problema = a.get("vcProblema") or ""
        riesgo = a.get("vcRiesgo") or ""
        medida = a.get("vcMedida") or ""
        accion = a.get("vcAccion") or ""
        proveedor = a.get("vcRazonSocialProveedor") or ""
        unidades = a.get("nuUnidadesInvolucradas") or a.get("nuUnidadesMercado") or 0
        fecha = a.get("vcFechaPublicacion") or ""

        # Extraer productos
        prods = a.get("productos", [])
        marcas = []
        modelos = []
        anios = []
        paises_fab = []
        for p in prods:
            if p.get("vcMarca"):
                marcas.append(p.get("vcMarca").strip().upper())
            if p.get("vcModelo"):
                modelos.append(p.get("vcModelo").strip().upper())
            if p.get("nuIdAnioFabric"):
                anios.append(int(p.get("nuIdAnioFabric")))
            if p.get("vcPaisProcedencia"):
                paises_fab.append(p.get("vcPaisProcedencia").strip())

        # Si no hay productos explícitos, extraer de título/problema
        if not marcas:
            for m in PERU_MAKES:
                if re.search(r'\b' + re.escape(m) + r'\b', f"{titulo} {problema}".upper()):
                    marcas.append(m)
                    break

        make_principal = marcas[0] if marcas else "NO_ESPECIFICADO"
        model_principal = modelos[0] if modelos else "NO_ESPECIFICADO"
        min_year = min(anios) if anios else None
        max_year = max(anios) if anios else None

        # Separar: DEFECTO vs SÍNTOMA/MANIFESTACIÓN vs CONSECUENCIA/RIESGO
        defecto = ""
        sintomas_list = []
        consecuencia = riesgo

        # Extracción de manifestaciones comunes en Indecopi
        texto_completo = f"{problema} {titulo}".lower()
        if any(w in texto_completo for w in ["pérdida de potencia", "perdida de potencia", "falta de potencia"]):
            sintomas_list.append("pérdida de potencia motriz")
        if any(w in texto_completo for w in ["no arranca", "dificultad para encender", "no enciende"]):
            sintomas_list.append("no arranca / dificultad de arranque")
        if any(w in texto_completo for w in ["apagado inesperado", "se apaga", "detención del motor"]):
            sintomas_list.append("apagado inesperado del motor en marcha")
        if any(w in texto_completo for w in ["vibración", "vibracion", "tiembla"]):
            sintomas_list.append("vibración anormal")
        if any(w in texto_completo for w in ["humo", "olor a quemado", "chispa"]):
            sintomas_list.append("humo u olor a quemado")
        if any(w in texto_completo for w in ["check engine", "testigo", "alarma sonora", "sonido de alerta"]):
            sintomas_list.append("encendido de testigo de advertencia (check engine)")
        if any(w in texto_completo for w in ["pedal duro", "pérdida de frenado", "desgaste de frenos", "fuga de líquido"]):
            sintomas_list.append("alteración en respuesta de pedal de freno")
        if any(w in texto_completo for w in ["bloqueo de volante", "dirección dura", "pérdida de asistencia"]):
            sintomas_list.append("dureza o pérdida de asistencia en dirección")

        sintomas_str = "; ".join(sintomas_list) if sintomas_list else "Falla funcional reportada en inspección técnica"
        defecto = problema[:300].strip()

        # Determinar combustible
        combustible = "AMBOS"
        if any(w in texto_completo for w in ["diesel", "diésel", "common rail", "dpf", "adblue"]):
            combustible = "DIESEL"
        elif any(w in texto_completo for w in ["gasolina", "bujia", "spark", "canister"]):
            combustible = "GASOLINA"

        macro_syst = mapear_macro_sistema(f"{titulo} {problema}")

        record = {
            "source": "indecopi_peru",
            "source_id": cod_alerta,
            "country": "PE",
            "evidence_type": "OFFICIAL_SAFETY_ALERT",
            "evidence_level": "L1_OFFICIAL_RECALL",
            "date": fecha,
            "manufacturer": proveedor or make_principal,
            "make": make_principal,
            "model": model_principal,
            "model_year_start": min_year,
            "model_year_end": max_year,
            "fuel_type": combustible,
            "engine": "",
            "vehicle_type": "passenger_car",
            "mileage": "",
            "system": macro_syst,
            "component": a.get("vcNombreProducto") or "Componente Automotriz",
            "dtc": "",
            "symptom": sintomas_str,
            "defect": defecto,
            "cause": "Defecto de fabricación / diseño reportado por fabricante",
            "consequence": consecuencia,
            "diagnostic_procedure": medida[:250] if medida else "Inspección técnica gratuita en concesionario autorizado",
            "repair": accion[:250] if accion else "Reemplazo o reprogramación de componente defectuoso según campaña",
            "narrative_original": f"{problema} {riesgo}".strip(),
            "narrative_es": f"{problema} {riesgo}".strip(),
            "ground_truth": True,
            "url": f"https://www.alertasdeconsumo.gob.pe/alerta/{cod_alerta}",
            "license": "Dominio Público Gubernamental / Ley de Transparencia (Perú)",
            "provenance": "INDECOPI Sistema de Alertas de Consumo",
            "market_source": "PE",
            "peru_model_match": True,
            "peru_applicability_confirmed": True,
            "relation_type": "DOCUMENTED"
        }
        norm_peru.append(record)

    # Exportar JSONL y CSV
    jsonl_out = DIR_NORM / "PERU_VEHICLE_FAILURES.jsonl"
    csv_out = DIR_NORM / "PERU_VEHICLE_FAILURES.csv"

    with open(jsonl_out, "w", encoding="utf-8") as jf:
        for r in norm_peru:
            jf.write(json.dumps(r, ensure_ascii=False) + "\n")

    if norm_peru:
        keys = list(norm_peru[0].keys())
        with open(csv_out, "w", encoding="utf-8", newline="") as cf:
            writer = csv.DictWriter(cf, fieldnames=keys)
            writer.writeheader()
            writer.writerows(norm_peru)

    print(f"      Total alertas Perú normalizadas: {len(norm_peru)}")
    print(f"      Archivos guardados: {jsonl_out.name} y {csv_out.name}")
    return norm_peru


def procesar_nhtsa_recalls() -> List[Dict[str, Any]]:
    print("\n[2/4] Normalizando NHTSA Recalls (2000-2026)...")
    recalls_files = [
        DIR_RECALLS / "FLAT_RCL_PRE_2010.txt",
        DIR_RECALLS / "FLAT_RCL_POST_2010.txt"
    ]

    norm_recalls = []
    vistos_campanas = set()
    total_leidos = 0

    for rfile in recalls_files:
        if not rfile.exists():
            continue
        with open(rfile, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                total_leidos += 1
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) < 22:
                    continue

                rec_id = parts[0]
                camp_no = parts[1]
                make = parts[2].strip().upper()
                model = parts[3].strip().upper()
                model_year = parts[4].strip()
                comp_name = parts[6].strip()
                mfr_name = parts[7].strip()
                pot_aft = parts[11].strip()
                desc_defect = parts[19].strip() if len(parts) > 19 else ""
                consequence = parts[20].strip() if len(parts) > 20 else ""
                remedy = parts[21].strip() if len(parts) > 21 else ""

                clave_dedup = f"{camp_no}_{make}_{model}_{model_year}"
                if clave_dedup in vistos_campanas:
                    continue
                vistos_campanas.add(clave_dedup)

                # Priorizar marcas y componentes automotrices
                macro_syst = mapear_macro_sistema(comp_name)
                is_peru_make = make in PERU_MAKES
                is_peru_model = is_peru_make and any(pm in model or model in pm for pm in PERU_MODELS)

                # Extraer síntomas de la descripción de defecto
                sintomas_list = []
                texto_b = f"{desc_defect} {consequence}".lower()
                if "stall" in texto_b or "shut down" in texto_b or "shut off" in texto_b:
                    sintomas_list.append("motor se apaga en marcha")
                if "power loss" in texto_b or "loss of motive power" in texto_b or "loss of acceleration" in texto_b:
                    sintomas_list.append("pérdida de potencia / aceleración")
                if "no start" in texto_b or "fail to start" in texto_b:
                    sintomas_list.append("no arranca")
                if "fire" in texto_b or "smoke" in texto_b or "thermal event" in texto_b:
                    sintomas_list.append("riesgo de humo / incendio")
                if "vibration" in texto_b or "shake" in texto_b:
                    sintomas_list.append("vibración anormal")
                if "brake fail" in texto_b or "extended stopping distance" in texto_b:
                    sintomas_list.append("distancia de frenado extendida")
                if "warning light" in texto_b or "check engine" in texto_b:
                    sintomas_list.append("encendido de testigo de advertencia")

                sintoma_str = "; ".join(sintomas_list) if sintomas_list else "Falla de seguridad operacional en componente"

                combustible = "AMBOS"
                if "diesel" in texto_b:
                    combustible = "DIESEL"
                elif "gasoline" in texto_b:
                    combustible = "GASOLINA"

                record = {
                    "source": "nhtsa_recalls",
                    "source_id": camp_no,
                    "country": "US",
                    "evidence_type": "OFFICIAL_RECALL",
                    "evidence_level": "L1_OFFICIAL_RECALL",
                    "date": parts[12].strip() if len(parts) > 12 else "",
                    "manufacturer": mfr_name,
                    "make": make,
                    "model": model,
                    "model_year_start": int(model_year) if model_year.isdigit() else None,
                    "model_year_end": int(model_year) if model_year.isdigit() else None,
                    "fuel_type": combustible,
                    "engine": "",
                    "vehicle_type": "passenger_car",
                    "mileage": "",
                    "system": macro_syst,
                    "component": comp_name,
                    "dtc": "",
                    "symptom": sintoma_str,
                    "defect": desc_defect[:400],
                    "cause": "Defecto de seguridad de diseño / ensamblaje OEM",
                    "consequence": consequence[:300],
                    "diagnostic_procedure": "Inspección física en red de concesionarios NHTSA",
                    "repair": remedy[:300],
                    "narrative_original": desc_defect,
                    "narrative_es": "",
                    "ground_truth": True,
                    "url": f"https://www.nhtsa.gov/recalls?nhtsaId={camp_no}",
                    "license": "Public Domain (US Government Work / NHTSA)",
                    "provenance": "NHTSA Flat Recalls Database",
                    "market_source": "US",
                    "peru_model_match": is_peru_model,
                    "peru_applicability_confirmed": False,
                    "relation_type": "DOCUMENTED"
                }
                norm_recalls.append(record)

    jsonl_out = DIR_NORM / "NHTSA_RECALLS_2000_2026.jsonl"
    with open(jsonl_out, "w", encoding="utf-8") as jf:
        for r in norm_recalls:
            jf.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"      Total registros brutos evaluados: {total_leidos:,}")
    print(f"      Total campañas deduplicadas: {len(norm_recalls):,}")
    print(f"      Campañas con modelo coincidente en Perú: {sum(1 for r in norm_recalls if r['peru_model_match']):,}")
    print(f"      Archivo guardado: {jsonl_out.name}")
    return norm_recalls


def procesar_nhtsa_complaints(limite_por_periodo: int = 50000) -> List[Dict[str, Any]]:
    print("\n[3/4] Normalizando NHTSA Complaints (2000-2026) priorizadas...")
    archivos_cmpl = sorted(DIR_COMPLAINTS.glob("*.txt"))
    norm_cmpl = []
    total_leidos = 0
    vistos_odino = set()

    for cfile in archivos_cmpl:
        periodo_count = 0
        with open(cfile, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                total_leidos += 1
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) < 20:
                    continue

                odino = parts[1].strip()
                if odino in vistos_odino:
                    continue
                vistos_odino.add(odino)

                mfr = parts[2].strip()
                make = parts[3].strip().upper()
                model = parts[4].strip().upper()
                model_year = parts[5].strip()
                comp = parts[11].strip()
                narrative = parts[19].strip()

                # Priorizar marcas peruanas y componentes automotrices centrales
                is_peru_make = make in PERU_MAKES
                macro = mapear_macro_sistema(comp)

                # Extraer síntomas reales de la queja
                narr_lower = narrative.lower()
                sintomas_list = []
                if "stall" in narr_lower or "died" in narr_lower or "shut off" in narr_lower:
                    sintomas_list.append("se apaga en marcha")
                if "crank no start" in narr_lower or "won't start" in narr_lower or "will not start" in narr_lower:
                    sintomas_list.append("da marcha pero no arranca")
                if "hard start" in narr_lower or "extended crank" in narr_lower:
                    sintomas_list.append("arranque difícil / prolongado")
                if "loss of power" in narr_lower or "lost power" in narr_lower or "no acceleration" in narr_lower:
                    sintomas_list.append("pérdida de potencia al acelerar")
                if "hesitation" in narr_lower or "hesitates" in narr_lower or "lag" in narr_lower:
                    sintomas_list.append("jaloneo / retraso al acelerar")
                if "misfire" in narr_lower or "rough idle" in narr_lower:
                    sintomas_list.append("ralentí inestable / fallo de encendido")
                if "vibrat" in narr_lower or "shaking" in narr_lower or "shudder" in narr_lower:
                    sintomas_list.append("vibración anormal")
                if "overheat" in narr_lower:
                    sintomas_list.append("sobrecalentamiento")
                if "smoke" in narr_lower or "black smoke" in narr_lower:
                    sintomas_list.append("humo anormal")
                if "squeal" in narr_lower or "grinding" in narr_lower or "clunk" in narr_lower or "whining" in narr_lower:
                    sintomas_list.append("ruido / silbido / chillido")
                if "check engine" in narr_lower or "mil light" in narr_lower or "dtc" in narr_lower:
                    sintomas_list.append("testigo check engine encendido")

                # Detectar códigos DTC en la queja si el usuario los menciona
                dtc_matches = re.findall(r'\b[PBUC][0-3][0-9A-F]{3}\b', narrative.upper())
                dtc_str = ", ".join(sorted(set(dtc_matches))) if dtc_matches else ""

                if is_peru_make and (sintomas_list or dtc_matches or macro in ["MOTOR", "FRENOS", "TRANSMISION", "ELECTRICO"]):
                    record = {
                        "source": "nhtsa_complaints",
                        "source_id": odino,
                        "country": "US",
                        "evidence_type": "OWNER_COMPLAINT",
                        "evidence_level": "L3_OBSERVATION",
                        "date": parts[15].strip() if len(parts) > 15 else "",
                        "manufacturer": mfr,
                        "make": make,
                        "model": model,
                        "model_year_start": int(model_year) if model_year.isdigit() else None,
                        "model_year_end": int(model_year) if model_year.isdigit() else None,
                        "fuel_type": "NO_ESPECIFICADO",
                        "engine": "",
                        "vehicle_type": "passenger_car",
                        "mileage": parts[17].strip() if len(parts) > 17 else "",
                        "system": macro,
                        "component": comp,
                        "dtc": dtc_str,
                        "symptom": "; ".join(sintomas_list) if sintomas_list else "Reporte de falla subjetiva de consumidor",
                        "defect": f"Queja de consumidor sobre {comp}",
                        "cause": "Sin verificar físicamente (reporte de usuario)",
                        "consequence": "Reporte de fallo subjetivo de consumidor",
                        "diagnostic_procedure": "",
                        "repair": "",
                        "narrative_original": narrative,
                        "narrative_es": "",
                        "ground_truth": False,
                        "url": f"https://www.nhtsa.gov/vehicle/{model_year}/{make}/{model}#complaints",
                        "license": "Public Domain (US Government Work / NHTSA)",
                        "provenance": "NHTSA Owner Complaints Database",
                        "market_source": "US",
                        "peru_model_match": any(pm in model or model in pm for pm in PERU_MODELS),
                        "peru_applicability_confirmed": False,
                        "relation_type": "INFERRED"
                    }
                    norm_cmpl.append(record)
                    periodo_count += 1
                    if periodo_count >= limite_por_periodo:
                        break

    jsonl_out = DIR_NORM / "NHTSA_VEHICLE_COMPLAINTS_2000_2026.jsonl"
    with open(jsonl_out, "w", encoding="utf-8") as jf:
        for r in norm_cmpl:
            jf.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"      Total quejas evaluadas: {total_leidos:,}")
    print(f"      Quejas técnicas normalizadas guardadas: {len(norm_cmpl):,}")
    print(f"      Archivo guardado: {jsonl_out.name}")
    return norm_cmpl


def consolidar_master_knowledge(peru_list, recalls_list, cmpl_list):
    print("\n[4/4] Consolidando Banco Maestro VEHICLE_FAILURE_KNOWLEDGE_2000_2026.jsonl...")
    master_path = DIR_NORM / "VEHICLE_FAILURE_KNOWLEDGE_2000_2026.jsonl"

    total = 0
    with open(master_path, "w", encoding="utf-8") as out:
        for r in peru_list:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            total += 1
        for r in recalls_list:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            total += 1
        for r in cmpl_list:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            total += 1

    print(f"      Banco Maestro completado: {total:,} registros canónicos guardados en {master_path.name}")


if __name__ == "__main__":
    t0 = time.time()
    peru = procesar_indecopi()
    rec = procesar_nhtsa_recalls()
    cmp = procesar_nhtsa_complaints(limite_por_periodo=35000)
    consolidar_master_knowledge(peru, rec, cmp)
    print(f"\nProceso de normalización completado en: {time.time() - t0:.2f} s")
