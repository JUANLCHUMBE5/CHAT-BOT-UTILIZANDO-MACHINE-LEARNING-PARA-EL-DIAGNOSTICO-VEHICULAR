"""Prepara candidatos externos auditables sin contaminar el dataset de entrenamiento.

Fuente: Automotive Faults Dataset for Diagnostic and Maintenance Systems
DOI: 10.5281/zenodo.15626055
Licencia: CC BY 4.0

El script NO modifica ``dataset_sintomas_limpio.csv``. Produce una bandeja de
revisión para que un mecánico valide cada correspondencia antes de entrenar.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


DOI = "10.5281/zenodo.15626055"
LICENCIA = "CC BY 4.0"
MD5_ESPERADO = "cb44431ef6b32f6ea9cf00dbe35f020c"

# Solo se proponen equivalencias conservadoras con clases que ya existen.
# Los componentes que requieren otra taxonomía quedan explícitamente pendientes.
MAPEO_SEGURO: dict[tuple[str, str], str] = {
    ("ABS System", "ABS Wheel Speed Sensor"): "FRENO_005",
    ("ABS System", "Brake Booster"): "FRENO_004",
    ("ABS System", "Brake Hose"): "FRENO_002",
    ("ABS System", "Brake Master Cylinder"): "FRENO_002",
    ("ABS System", "Brake Pad"): "FRENO_001",
    ("ABS System", "Brake Rotor"): "FRENO_003",
    ("ABS System", "Brake Shoe & Drum"): "FRENO_001",
    ("Air Conditioning System", "AC Compressor"): "CLIMA_001",
    ("Cooling System", "Coolant/Antifreeze"): "REFRIGERACION_002",
    ("Cooling System", "Coolant Leak Diagnosis"): "REFRIGERACION_002",
    ("Cooling System", "Engine Cooling System"): "REFRIGERACION_001",
    ("Cooling System", "Radiator/Cooling Fan"): "REFRIGERACION_001",
    ("Cooling System", "Radiator Hose"): "REFRIGERACION_002",
    ("Cooling System", "Water Pump"): "REFRIGERACION_001",
    ("Drivetrain", "Bevel Gears"): "TRANSMISION_002",
    ("Drivetrain", "Clutch Cable"): "EMBRAGUE_002",
    ("Drivetrain", "Clutch Slave Cylinder"): "EMBRAGUE_002",
    ("Drivetrain", "Differential"): "TRANSMISION_002",
    ("Drivetrain", "Slushbox"): "TRANSMISION_001",
    ("Electrical System", "Battery Replacement"): "ELECTRICO_002",
    ("Electrical System", "Battery Charging"): "ELECTRICO_001",
    ("Electrical System", "Charging System"): "ELECTRICO_001",
    ("Electrical System", "Door Window Motor"): "CARROCERIA_003",
    ("Electrical System", "Door Window Regulator"): "CARROCERIA_003",
    ("Electrical System", "Ignition Distributor Cap"): "MOTOR_001",
    ("Electrical System", "Ignition Wire Set"): "MOTOR_001",
    ("Electrical System", "Power Door Lock Actuator"): "CARROCERIA_001",
    ("Electrical System", "Starter Motor"): "ELECTRICO_002",
    ("Electrical System", "Wiper Motor"): "CARROCERIA_004",
    ("Emissions System", "Oxygen Sensor"): "COMBUSTIBLE_004",
    ("Engine Components", "Boost Pressure"): "TURBO_001",
    ("Engine Components", "Diesel Injection Pump"): "COMBUSTIBLE_005",
    ("Engine Components", "Fuel Injector"): "COMBUSTIBLE_001",
    ("Engine Components", "Idle Air Control Valve"): "COMBUSTIBLE_003",
    ("Engine Components", "Oil Pump"): "MOTOR_004",
    ("Engine Components", "Piston Rings"): "MOTOR_002",
    ("Engine Components", "Timing Belt"): "MOTOR_005",
    ("Engine Compartment", "Engine Oil"): "MOTOR_004",
    ("Engine Compartment", "Fuel Filter"): "COMBUSTIBLE_001",
    ("Engine Compartment", "Throttle Body"): "COMBUSTIBLE_003",
    ("Fuel System", "Fuel Injector"): "COMBUSTIBLE_001",
    ("Fuel System", "Fuel Pump"): "COMBUSTIBLE_002",
    ("Transmission", "Clutch Master Cylinder"): "EMBRAGUE_002",
    ("Transmission", "Transmission Fluid"): "TRANSMISION_003",
    ("Transmission", "Transmission Filter"): "TRANSMISION_001",
    ("Transmission", "Transmission Solenoid"): "TRANSMISION_001",
}

# Síntomas que no demuestran por sí solos la subcategoría indicada por la
# fuente. Se conservan para revisión, pero nunca deben pasar automáticamente al
# entrenamiento con esa etiqueta.
COMBINACIONES_AMBIGUAS: set[tuple[str, str, str]] = {
    ("ABS System", "Brake Booster", "Spongy brake pedal"),
    ("ABS System", "Brake Pad", "Brake pedal pulsation"),
    ("ABS System", "Brake Shoe & Drum", "Spongy brake pedal"),
    ("Drivetrain", "Bevel Gears", "Difficulty shifting gears"),
    ("Drivetrain", "Differential", "Vehicle vibration at high speeds"),
    ("Electrical System", "Battery Replacement", "Clicking sound when starting"),
    ("Electrical System", "Ignition Wire Set", "Poor fuel economy"),
    ("Emissions System", "Oxygen Sensor", "Check engine light on"),
    ("Engine Components", "Diesel Injection Pump", "Engine misfires"),
    ("Engine Components", "Timing Belt", "Engine misfires"),
    ("Engine Compartment", "Engine Oil", "Loud engine noise"),
    ("Transmission", "Clutch Master Cylinder", "Clutch slipping"),
}


def md5_archivo(ruta: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def preparar(entrada: Path, salida: Path, reporte: Path) -> dict[str, object]:
    checksum = md5_archivo(entrada)
    if checksum != MD5_ESPERADO:
        raise ValueError(
            f"El MD5 no coincide con Zenodo: esperado={MD5_ESPERADO}, obtenido={checksum}"
        )

    registros = json.loads(entrada.read_text(encoding="utf-8"))
    if not isinstance(registros, list) or len(registros) != 99:
        raise ValueError("La fuente no contiene los 99 registros esperados.")

    salida.parent.mkdir(parents=True, exist_ok=True)
    conteo = Counter()
    filas = []
    for registro in registros:
        categoria = str(registro.get("category", "")).strip()
        subcategoria = str(registro.get("subcategory", "")).strip()
        codigo = MAPEO_SEGURO.get((categoria, subcategoria), "")
        for sintoma in registro.get("symptoms", []):
            sintoma = str(sintoma).strip()
            es_ambiguo = (categoria, subcategoria, sintoma) in COMBINACIONES_AMBIGUAS
            if not codigo:
                decision = "REQUIERE_NUEVA_CLASE_O_DESCARTE"
            elif es_ambiguo:
                decision = "REQUIERE_REVISION_AMBIGUEDAD"
            else:
                decision = "MAPEO_PROPUESTO"
            conteo[decision] += 1
            filas.append(
                {
                    "sintoma_fuente_ingles": sintoma,
                    "categoria_fuente": categoria,
                    "subcategoria_fuente": subcategoria,
                    "codigo_canonico_propuesto": codigo,
                    "decision": decision,
                    "traduccion_espanol_validada": "",
                    "validado_por_mecanico": "NO",
                    "observaciones_revision": "",
                    "doi_fuente": DOI,
                    "licencia": LICENCIA,
                }
            )

    with salida.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    resumen = {
        "fuente": f"https://doi.org/{DOI}",
        "licencia": LICENCIA,
        "md5_verificado": checksum,
        "registros_fuente": len(registros),
        "sintomas_candidatos": len(filas),
        "sintomas_con_mapeo_propuesto": conteo["MAPEO_PROPUESTO"],
        "sintomas_con_mapeo_ambiguo": conteo["REQUIERE_REVISION_AMBIGUEDAD"],
        "sintomas_pendientes_nueva_clase_o_descarte": conteo[
            "REQUIERE_NUEVA_CLASE_O_DESCARTE"
        ],
        "incorporado_al_entrenamiento": False,
        "motivo": "Pendiente de traducción y validación por mecánico.",
    }
    reporte.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("entrada", type=Path, help="JSON original descargado desde Zenodo")
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("data/candidatos_revision/zenodo_15626055.csv"),
    )
    parser.add_argument(
        "--reporte",
        type=Path,
        default=Path("data/candidatos_revision/zenodo_15626055_reporte.json"),
    )
    args = parser.parse_args()
    resumen = preparar(args.entrada, args.salida, args.reporte)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
