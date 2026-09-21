"""
09_curacion_mapeo_v2.py
FASE EXPERIMENTAL — CARBOT ML + RAG V2
Curación forense de fuentes externas, categorización estricta de uso y mapeo
contra las 48 clases canónicas de auditoría y clases objetivo de CarBot.

Categorías de salida:
- ML_HIGH_CONFIDENCE (confianza >= 0.85, relación síntoma -> falla confirmada físicamente/documentalmente)
- ML_REVIEW_REQUIRED (0.70 <= confianza < 0.85, casos plausibles pero ambiguos)
- RAG_TECHNICAL (DTCs, manuales, boletines, causas técnicas, procedimientos)
- RAG_SYMPTOM_LANGUAGE (narrativas de usuarios, quejas subjetivas NHTSA complaints)
- TELEMETRY_ONLY (EngineFaultDB, LEVIN, carOBD)
- EVALUATION_ONLY (reservados para pruebas, no training)
- REJECTED (<0.70 o sin información vehicular útil)

Genera:
machine_learning/experimentos/carbot_v2/data/MAPEO_EXTERNOS_48_CLASES.csv
"""
import sys
import os
import csv
import json
import re
import time
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple

# Forzar flush inmediato en stdout
sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BASE_V2 = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2"
DATA_V2 = BASE_V2 / "data"
DATA_V2.mkdir(parents=True, exist_ok=True)

MASTER_KNOWLEDGE_FILE = PROJECT_ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "fallas_vehiculares" / "normalizado" / "VEHICLE_FAILURE_KNOWLEDGE_2000_2026.jsonl"
NORMALIZED_OPEN_DATA = PROJECT_ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "normalizado" / "dataset_normalizado.jsonl"
COBERTURA_CSV_ORIG = PROJECT_ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "auditoria" / "cobertura_clases.csv"

# Cargar las 48 clases de auditoría
CLASES_48 = []
with open(COBERTURA_CSV_ORIG, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        CLASES_48.append(row["clase_carbot"])

# Mapeo biyectivo de las 48 clases hacia las clases canónicas de entrenamiento C1
MAP_48_TO_C1 = {
    "Falla en bujias o bobinas de encendido (fallo de encendido)": "Falla en bujias o bobinas de encendido (misfire)",
    "Falla en inyectores de combustible (obstruccion o fuga)": "Inyectores sucios o filtro de combustible obstruido",
    "Bomba de combustible defectuosa o baja presion": "Bomba de gasolina quemada o con baja presion",
    "Filtro de combustible obstruido": "Inyectores sucios o filtro de combustible obstruido",
    "Cuerpo de aceleracion o valvula IAC sucia": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor de flujo de masa de aire (MAF) defectuoso o sucio": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de presion absoluta del multiple (MAP) defectuoso": "Falla en regulador de presion de combustible o diafragma roto",
    "Sensor de oxigeno defectuoso": "Falla en sensor de oxigeno o mezcla rica",
    "Convertidor catalitico obstruido o degradado": "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
    "Fuga de vacio en el multiple de admision": "Cuerpo de aceleracion o valvula IAC sucia",
    "Valvula EGR atascada o defectuosa": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de posicion del ciguenal (CKP) defectuoso": "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
    "Sensor de posicion del arbol de levas (CMP) defectuoso": "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
    "Falla en sensor de temperatura del refrigerante (ECT)": "Falla en termostato o motoventilador de radiador",
    "Falla en sensor de posicion del acelerador (TPS)": "Cuerpo de aceleracion o valvula IAC sucia",
    "Bateria descargada o en mal estado": "Bateria descargada o bornes sulfatados",
    "Alternador defectuoso o con baja carga": "Alternador defectuoso o placa de diodos quemada",
    "Motor de arranque defectuoso o solenoide pegado": "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
    "Falla en relay o fusible del sistema de encendido/inyeccion": "Falla en bujias o bobinas de encendido (misfire)",
    "Falla en termostato o motoventilador de radiador": "Falla en termostato o motoventilador de radiador",
    "Fuga de liquido refrigerante (manguera, radiador o bomba de agua)": "Fuga en mangueras de refrigerante o radiador picado",
    "Bomba de agua defectuosa": "Fuga en mangueras de refrigerante o radiador picado",
    "Fuga de aceite de motor (empaquetadura o reten)": "Consumo de aceite por desgaste de anillos o retenes",
    "Consumo de aceite por desgaste de anillos o retenes": "Consumo de aceite por desgaste de anillos o retenes",
    "Desgaste de pastillas o zapatas de freno": "Desgaste de pastillas y zapatas de freno",
    "Discos o tambores de freno desgastados o deformados": "Discos de freno alabeados o desgastados",
    "Fuga de liquido de frenos o aire en el circuito": "Fuga hidraulica o aire en el sistema de frenos",
    "Bomba principal de freno defectuosa": "Fuga hidraulica o aire en el sistema de frenos",
    "Desgaste en rotulas o terminales de direccion": "Cremallera de direccion asistida con holgura o fuga",
    "Amortiguadores desgastados o con fuga": "Amortiguadores reventados o bujes de suspension gastados",
    "Desalineacion o desbalanceo de ruedas": "Llantas desbalanceadas o desalineadas",
    "Embrague desgastado o patinando (transmision manual)": "Disco de embrague desgastado o patinando",
    "Bajo nivel de liquido de transmision o fuga": "Falta o degradacion de aceite de caja de cambios",
    "Falla en solenoides de transmision automatica": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
    "Desgaste en junta homocinetica (palier)": "Juntas homocineticas o palieres danados",
    "Soporte de motor o transmision roto o vencido": "Rodajes de transmision manual o eje primario gastados",
    "Falla en sensor de detonacion (Knock Sensor)": "Falla en sensor de oxigeno o mezcla rica",
    "Falla en sensor de velocidad del vehiculo (VSS)": "Falla en sensor de velocidad de rueda ABS",
    "Falla en sensor de pedal de freno o embrague": "Fuga hidraulica o aire en el sistema de frenos",
    "Filtro de aire obstruido o sucio": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de cabina obstruido o ventilador defectuoso": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Fuga en sistema de escape o silenciador roto": "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
    "Falla en valvula PCV": "Consumo de aceite por desgaste de anillos o retenes",
    "Falla en canister o valvula de purga EVAP": "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)",
    "Falla en compresor o fuga de gas de aire acondicionado": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Falla en cableado o sulfatacion de tierras de chasis": "Fuga parasita de corriente en reposo (consumo nocturno de bateria)",
    "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
    "Fuga en conducto de sobrealimentacion o manguera de turbo rajada": "Fuga en mangueras de intercooler o turbocompresor danado"
}

# Reglas optimizadas de coincidencia rápida (palabra clave -> clase 48, confianza, motivo)
REGLAS_INEQUIVOCAS = [
    # Misfire y encendido
    ("ignition coil", "Falla en bujias o bobinas de encendido (fallo de encendido)", 0.95, "Bobina de encendido explicita"),
    ("spark plug", "Falla en bujias o bobinas de encendido (fallo de encendido)", 0.95, "Bujia de encendido explicita"),
    ("bobina de encendido", "Falla en bujias o bobinas de encendido (fallo de encendido)", 0.98, "Bobina de encendido explicita"),
    ("bujias", "Falla en bujias o bobinas de encendido (fallo de encendido)", 0.95, "Bujias de encendido explicita"),
    ("misfire", "Falla en bujias o bobinas de encendido (fallo de encendido)", 0.85, "Fallo de encendido misfire"),
    # Inyectores y combustible
    ("fuel injector", "Falla en inyectores de combustible (obstruccion o fuga)", 0.95, "Inyector de combustible explicito"),
    ("inyector de combustible", "Falla en inyectores de combustible (obstruccion o fuga)", 0.98, "Inyector de combustible explicito"),
    ("fuel pump", "Bomba de combustible defectuosa o baja presion", 0.95, "Bomba de combustible explicita"),
    ("bomba de combustible", "Bomba de combustible defectuosa o baja presion", 0.98, "Bomba de combustible explicita"),
    ("bomba de gasolina", "Bomba de combustible defectuosa o baja presion", 0.98, "Bomba de gasolina explicita"),
    ("fuel filter", "Filtro de combustible obstruido", 0.95, "Filtro de combustible explicito"),
    ("filtro de combustible", "Filtro de combustible obstruido", 0.98, "Filtro de combustible explicito"),
    # Admisión y aceleración
    ("throttle body", "Cuerpo de aceleracion o valvula IAC sucia", 0.95, "Cuerpo de aceleracion"),
    ("cuerpo de aceleracion", "Cuerpo de aceleracion o valvula IAC sucia", 0.98, "Cuerpo de aceleracion"),
    ("idle air control", "Cuerpo de aceleracion o valvula IAC sucia", 0.95, "Valvula IAC"),
    ("valvula iac", "Cuerpo de aceleracion o valvula IAC sucia", 0.98, "Valvula IAC"),
    ("mass air flow", "Sensor de flujo de masa de aire (MAF) defectuoso o sucio", 0.95, "Sensor MAF"),
    ("sensor maf", "Sensor de flujo de masa de aire (MAF) defectuoso o sucio", 0.98, "Sensor MAF"),
    ("manifold absolute pressure", "Sensor de presion absoluta del multiple (MAP) defectuoso", 0.95, "Sensor MAP"),
    ("sensor map", "Sensor de presion absoluta del multiple (MAP) defectuoso", 0.98, "Sensor MAP"),
    # Emisiones y escape
    ("oxygen sensor", "Sensor de oxigeno defectuoso", 0.95, "Sensor de oxigeno"),
    ("sensor de oxigeno", "Sensor de oxigeno defectuoso", 0.98, "Sensor de oxigeno"),
    ("sonda lambda", "Sensor de oxigeno defectuoso", 0.98, "Sonda lambda"),
    ("catalytic converter", "Convertidor catalitico obstruido o degradado", 0.95, "Convertidor catalitico"),
    ("convertidor catalitico", "Convertidor catalitico obstruido o degradado", 0.98, "Convertidor catalitico"),
    ("egr valve", "Valvula EGR atascada o defectuosa", 0.95, "Valvula EGR"),
    ("valvula egr", "Valvula EGR atascada o defectuosa", 0.98, "Valvula EGR"),
    ("evap canister", "Falla en canister o valvula de purga EVAP", 0.95, "Canister EVAP"),
    ("purge valve", "Falla en canister o valvula de purga EVAP", 0.95, "Valvula de purga EVAP"),
    # Sensores de sincronización
    ("crankshaft position sensor", "Sensor de posicion del ciguenal (CKP) defectuoso", 0.95, "Sensor CKP"),
    ("sensor ckp", "Sensor de posicion del ciguenal (CKP) defectuoso", 0.98, "Sensor CKP"),
    ("sensor de posicion del ciguenal", "Sensor de posicion del ciguenal (CKP) defectuoso", 0.98, "Sensor CKP"),
    ("camshaft position sensor", "Sensor de posicion del arbol de levas (CMP) defectuoso", 0.95, "Sensor CMP"),
    ("sensor cmp", "Sensor de posicion del arbol de levas (CMP) defectuoso", 0.98, "Sensor CMP"),
    ("engine coolant temperature", "Falla en sensor de temperatura del refrigerante (ECT)", 0.95, "Sensor ECT"),
    ("sensor ect", "Falla en sensor de temperatura del refrigerante (ECT)", 0.98, "Sensor ECT"),
    ("throttle position sensor", "Falla en sensor de posicion del acelerador (TPS)", 0.95, "Sensor TPS"),
    ("sensor tps", "Falla en sensor de posicion del acelerador (TPS)", 0.98, "Sensor TPS"),
    ("knock sensor", "Falla en sensor de detonacion (Knock Sensor)", 0.95, "Knock sensor"),
    ("vehicle speed sensor", "Falla en sensor de velocidad del vehiculo (VSS)", 0.95, "Sensor VSS"),
    # Sistema eléctrico y arranque
    ("alternator", "Alternador defectuoso o con baja carga", 0.95, "Alternador"),
    ("alternador", "Alternador defectuoso o con baja carga", 0.98, "Alternador"),
    ("starter motor", "Motor de arranque defectuoso o solenoide pegado", 0.95, "Motor de arranque"),
    ("motor de arranque", "Motor de arranque defectuoso o solenoide pegado", 0.98, "Motor de arranque"),
    ("battery", "Bateria descargada o en mal estado", 0.90, "Bateria"),
    ("bateria", "Bateria descargada o en mal estado", 0.95, "Bateria"),
    # Refrigeración
    ("thermostat", "Falla en termostato o motoventilador de radiador", 0.95, "Termostato"),
    ("termostato", "Falla en termostato o motoventilador de radiador", 0.98, "Termostato"),
    ("cooling fan", "Falla en termostato o motoventilador de radiador", 0.95, "Motoventilador"),
    ("motoventilador", "Falla en termostato o motoventilador de radiador", 0.98, "Motoventilador"),
    ("water pump", "Bomba de agua defectuosa", 0.95, "Bomba de agua"),
    ("bomba de agua", "Bomba de agua defectuosa", 0.98, "Bomba de agua"),
    ("fuga de refrigerante", "Fuga de liquido refrigerante (manguera, radiador o bomba de agua)", 0.98, "Fuga refrigerante"),
    # Frenos
    ("brake rotor", "Discos o tambores de freno desgastados o deformados", 0.95, "Discos de freno"),
    ("brake disc", "Discos o tambores de freno desgastados o deformados", 0.95, "Discos de freno"),
    ("discos de freno", "Discos o tambores de freno desgastados o deformados", 0.98, "Discos de freno"),
    ("brake pads", "Desgaste de pastillas o zapatas de freno", 0.95, "Pastillas de freno"),
    ("pastillas de freno", "Desgaste de pastillas o zapatas de freno", 0.98, "Pastillas de freno"),
    ("brake master cylinder", "Bomba principal de freno defectuosa", 0.95, "Bomba principal de freno"),
    ("brake fluid leak", "Fuga de liquido de frenos o aire en el circuito", 0.95, "Fuga liquido de freno"),
    # Suspensión y dirección
    ("shock absorber", "Amortiguadores desgastados o con fuga", 0.95, "Amortiguadores"),
    ("amortiguador", "Amortiguadores desgastados o con fuga", 0.98, "Amortiguadores"),
    ("ball joint", "Desgaste en rotulas o terminales de direccion", 0.95, "Rotulas"),
    ("rotula", "Desgaste en rotulas o terminales de direccion", 0.98, "Rotulas"),
    ("cv joint", "Desgaste en junta homocinetica (palier)", 0.95, "Junta homocinetica"),
    ("junta homocinetica", "Desgaste en junta homocinetica (palier)", 0.98, "Junta homocinetica"),
    # Transmisión y sobrealimentación
    ("clutch", "Embrague desgastado o patinando (transmision manual)", 0.90, "Embrague"),
    ("disco de embrague", "Embrague desgastado o patinando (transmision manual)", 0.98, "Disco de embrague"),
    ("turbocharger", "Fuga en conducto de sobrealimentacion o manguera de turbo rajada", 0.90, "Turbocompresor"),
    ("intercooler hose", "Fuga en conducto de sobrealimentacion o manguera de turbo rajada", 0.98, "Manguera intercooler"),
    ("manguera de turbo", "Fuga en conducto de sobrealimentacion o manguera de turbo rajada", 0.98, "Manguera turbo"),
    ("common rail", "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", 0.95, "Common Rail Diesel"),
    ("a/c compressor", "Falla en compresor o fuga de gas de aire acondicionado", 0.95, "Compresor A/C"),
    ("compresor de aire acondicionado", "Falla en compresor o fuga de gas de aire acondicionado", 0.98, "Compresor A/C")
]

# Casos piloto bloqueados
CASOS_PILOTO_BLOQUEADOS = [
    "ckp termico", "sensor ckp se apaga en caliente",
    "discos alabeados", "vibracion al frenar a alta velocidad",
    "misfire bobina cilindro", "bobina en corto cilindro",
    "fuga boost hilux", "manguera intercooler rajada hilux"
]


def evaluar_registro_rapido(reg: Dict[str, Any]) -> Dict[str, Any]:
    src = reg.get("source", "")
    ev_type = reg.get("evidence_type", "")
    comp = (reg.get("component") or "").lower()
    defect = (reg.get("defect") or "").lower()
    symptom = (reg.get("symptom") or "").lower()
    narr = (reg.get("narrative_original") or "").lower()
    gt = reg.get("ground_truth", False)

    texto_combinado = f"{comp} {defect} {symptom} {narr}"

    # Filtro piloto
    for cp in CASOS_PILOTO_BLOQUEADOS:
        if cp in texto_combinado:
            return {
                "carbot_class": "CASO_PILOTO_RESERVADO",
                "clase_48": "CASO_PILOTO_RESERVADO",
                "mapping_confidence": 0.0,
                "mapping_reason": f"Caso piloto bloqueado ({cp})",
                "evidence_type": "EVALUATION_PILOT",
                "uso_final": "EVALUATION_ONLY"
            }

    # 1. Telemetría pura
    if src in ["engine_fault_db", "levin_opendata", "car_obd_etios_repo"]:
        return {
            "carbot_class": "TELEMETRIA",
            "clase_48": "TELEMETRIA",
            "mapping_confidence": 0.0,
            "mapping_reason": "Telemetria de sensores sin narrativa diagnostica",
            "evidence_type": "TELEMETRY",
            "uso_final": "TELEMETRY_ONLY"
        }

    # 2. NHTSA Complaints (Regla 3 estricta)
    if ev_type == "OWNER_COMPLAINT" or src == "nhtsa_complaints":
        return {
            "carbot_class": "N/A",
            "clase_48": "N/A",
            "mapping_confidence": 0.30,
            "mapping_reason": "Queja subjetiva no verificada (Regla 3)",
            "evidence_type": "OWNER_COMPLAINT",
            "uso_final": "RAG_SYMPTOM_LANGUAGE"
        }

    # 3. Búsqueda rápida de coincidencias directas
    mejor_clase_48 = None
    mejor_conf = 0.0
    mejor_motivo = "Sin coincidencia inequívoca"

    comp_defect = f"{comp} {defect}"
    for clave, c48, conf_val, motivo in REGLAS_INEQUIVOCAS:
        if clave in comp_defect:
            if conf_val > mejor_conf:
                mejor_clase_48 = c48
                mejor_conf = conf_val
                mejor_motivo = motivo
                if conf_val >= 0.98:
                    break

    if not mejor_clase_48:
        for clave, c48, conf_val, motivo in REGLAS_INEQUIVOCAS:
            if clave in texto_combinado:
                conf_atenuada = conf_val - 0.20
                if conf_atenuada > mejor_conf:
                    mejor_clase_48 = c48
                    mejor_conf = conf_atenuada
                    mejor_motivo = f"Mencion contextual ({motivo})"

    carbot_c1_class = MAP_48_TO_C1.get(mejor_clase_48, "SIN_CLASE_DEFINIDA") if mejor_clase_48 else "SIN_CLASE_DEFINIDA"
    es_fuente_confiable = src in ["indecopi_peru", "nhtsa_recalls", "zenodo_15626055", "mechanicdb_public"]

    if mejor_conf >= 0.85 and (gt or es_fuente_confiable) and carbot_c1_class != "SIN_CLASE_DEFINIDA":
        uso = "ML_HIGH_CONFIDENCE"
    elif mejor_conf >= 0.70:
        uso = "ML_REVIEW_REQUIRED"
    elif any(x in src for x in ["zenodo", "mechanicdb", "obdex", "dtc_database", "indecopi", "recalls"]):
        uso = "RAG_TECHNICAL"
    else:
        uso = "REJECTED"

    return {
        "carbot_class": carbot_c1_class,
        "clase_48": mejor_clase_48 or "SIN_CLASE_DEFINIDA",
        "mapping_confidence": round(mejor_conf, 3),
        "mapping_reason": mejor_motivo,
        "evidence_type": ev_type or "TECHNICAL_DOCUMENT",
        "uso_final": uso
    }


def ejecutar():
    t0 = time.time()
    print("Iniciando Curacion y Mapeo V2 Optimizado...", flush=True)

    registros_a_evaluar = []

    # 1. Cargar Banco Maestro
    if MASTER_KNOWLEDGE_FILE.exists():
        print(f"Leyendo banco maestro: {MASTER_KNOWLEDGE_FILE.name}...", flush=True)
        count_rec = 0
        count_cmpl = 0
        with open(MASTER_KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                src = r.get("source", "")
                if src == "indecopi_peru":
                    registros_a_evaluar.append(r)
                elif src == "nhtsa_recalls":
                    # Tomar todas las alertas/recalls con componente específico
                    count_rec += 1
                    if count_rec <= 35000:
                        registros_a_evaluar.append(r)
                elif src == "nhtsa_complaints":
                    count_cmpl += 1
                    if count_cmpl <= 20000:
                        registros_a_evaluar.append(r)

    # 2. Cargar Open Data (Zenodo, MechanicDB, OBDex, DTC Database, etc.)
    if NORMALIZED_OPEN_DATA.exists():
        print(f"Leyendo open data normalizado: {NORMALIZED_OPEN_DATA.name}...", flush=True)
        with open(NORMALIZED_OPEN_DATA, "r", encoding="utf-8") as f:
            for line in f:
                registros_a_evaluar.append(json.loads(line))

    print(f"Total registros en muestra para mapeo: {len(registros_a_evaluar):,}", flush=True)

    filas_mapeo = []
    conteo_usos = Counter()
    conteo_clases_ml = Counter()

    for idx, reg in enumerate(registros_a_evaluar):
        res = evaluar_registro_rapido(reg)
        uso = res["uso_final"]
        conteo_usos[uso] += 1

        if uso == "ML_HIGH_CONFIDENCE":
            conteo_clases_ml[res["carbot_class"]] += 1

        filas_mapeo.append({
            "fuente": reg.get("source", ""),
            "source_record_id": reg.get("source_id") or reg.get("source_record_id", f"rec_{idx}"),
            "texto": (reg.get("defect") or reg.get("symptom") or reg.get("narrative_original", ""))[:150].replace("\n", " ").replace("\r", ""),
            "clase_original": reg.get("component", ""),
            "carbot_class": res["carbot_class"],
            "clase_48": res["clase_48"],
            "mapping_confidence": res["mapping_confidence"],
            "mapping_reason": res["mapping_reason"],
            "evidence_type": res["evidence_type"],
            "uso_final": uso
        })

    csv_mapeo_out = DATA_V2 / "MAPEO_EXTERNOS_48_CLASES.csv"
    fieldnames = [
        "fuente", "source_record_id", "texto", "clase_original", 
        "carbot_class", "clase_48", "mapping_confidence", 
        "mapping_reason", "evidence_type", "uso_final"
    ]
    with open(csv_mapeo_out, "w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filas_mapeo)

    print("\n========================================================", flush=True)
    print(f"RESULTADOS DE CLASIFICACION DE USO (TOTAL: {len(filas_mapeo):,})", flush=True)
    print("========================================================", flush=True)
    for uso, cnt in conteo_usos.most_common():
        print(f"  {uso:<22}: {cnt:>8,} ({cnt/len(filas_mapeo)*100:.1f}%)", flush=True)

    print(f"\nTotal candidatos ML_HIGH_CONFIDENCE (conf >= 0.85): {conteo_usos['ML_HIGH_CONFIDENCE']:,}", flush=True)
    print(f"Clases CarBot cubiertas con evidencia ML: {len(conteo_clases_ml)}", flush=True)
    for cls_name, cnt in conteo_clases_ml.most_common(10):
        print(f"  - {cls_name}: {cnt:,} candidatos", flush=True)

    print(f"\nArchivo guardado: {csv_mapeo_out}", flush=True)
    print(f"Tiempo total: {time.time() - t0:.2f} s", flush=True)


if __name__ == "__main__":
    ejecutar()
