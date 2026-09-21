"""
Script perfeccionado para clasificar con máxima precisión técnica los metadatos RAG.
Asigna cada procedimiento a su Macro-Sistema y Falla canónica exactos basándose en su título y DTC.
"""

import json
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METADATOS_JSON = BASE_DIR / "machine_learning" / "manuals" / "metadatos_manuales.json"

def norm_txt(t):
    if not t:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(c) != 'Mn')

def clasificar_procedimiento(tit: str, dtcs: list) -> tuple[str, str]:
    t = norm_txt(tit)
    dtc_str = " ".join(dtcs).upper()

    # 1. CARROCERÍA Y NEUMÁTICA
    if any(k in t for k in ["limpiaparabrisas", "plumas", "varillaje"]):
        return "CARROCERIA_NEUMATICA", "Falla en motor o varillaje de limpiaparabrisas"
    if any(k in t for k in ["elevalunas", "alzacristales", "vidrio", "luna"]):
        return "CARROCERIA_NEUMATICA", "Falla en mecanismo elevalunas"
    if any(k in t for k in ["chapa", "pestillo", "cierre centralizado", "puerta"]):
        return "CARROCERIA_NEUMATICA", "Falla electrica del cierre centralizado o actuador"
    if any(k in t for k in ["camion", "frenos de aire", "secador", "aps", "calderin"]):
        return "CARROCERIA_NEUMATICA", "Fugas de aire o fallos en el sistema de frenos de aire (camiones)"

    # 2. CLIMATIZACIÓN
    if any(k in t for k in ["aire acondicionado", "climatizacion", "r134a", "r1234yf", "hvac", "evaporador", "valvula de expansion"]):
        return "CLIMATIZACION", "Falla en compresor de aire acondicionado o fuga de gas"

    # 3. FRENOS
    if any(k in t for k in ["abs", "c0035", "c0040", "c0221"]):
        return "FRENOS", "Falla en sensor de velocidad de rueda ABS"
    if any(k in t for k in ["alabeo", "disco", "dtv", "variacion de espesor"]):
        return "FRENOS", "Desgaste o alabeo de discos y pastillas de freno"
    if any(k in t for k in ["pastilla", "zapata", "tambor"]):
        return "FRENOS", "Desgaste de pastillas y zapatas de freno"
    if any(k in t for k in ["liquido del sistema hidraulico", "pedal esponjoso", "purga y cambio de liquido"]):
        return "FRENOS", "Fuga de liquido de frenos o aire en el sistema hidraulico"
    if any(k in t for k in ["caliper", "mordaza"]):
        return "FRENOS", "Caliper de freno pegado o trabado"
    if any(k in t for k in ["servofreno", "booster"]):
        return "FRENOS", "Falla en servofreno (booster) o linea de vacio"
    if any(k in t for k in ["freno de estacionamiento", "epb"]):
        return "FRENOS", "Desgaste de pastillas y zapatas de freno"

    # 4. TRANSMISIÓN
    if any(k in t for k in ["dualogic", "i-motion", "freechoice", "robotizada", "p0841", "p0919"]):
        return "TRANSMISION", "Falla en caja robotizada Dualogic / I-Motion"
    if any(k in t for k in ["embrague", "clutch", "bombin", "calado"]):
        return "TRANSMISION", "Disco de embrague desgastado o patinando"
    if any(k in t for k in ["cvt", "ns3", "poleas"]):
        return "TRANSMISION", "Falla o degradacion de aceite en caja automatica CVT"
    if any(k in t for k in ["caja de cambios mecanica", "valvolina", "atf", "convertidor", "tcc"]):
        return "TRANSMISION", "Falta o degradacion de aceite de caja de cambios"
    if any(k in t for k in ["diferencial", "corona-pinon", "awd", "4wd", "cruceta", "cardan"]):
        return "TRANSMISION", "Rodajes de caja mecanica o diferencial gastados"

    # 5. SUSPENSIÓN Y CHASIS
    if any(k in t for k in ["balanceo", "alineacion", "convergencia", "camber", "laser de direccion"]):
        return "SUSPENSION_CHASIS", "Llantas desbalanceadas o desalineadas"
    if any(k in t for k in ["palier", "homocinetica", "semieje", "fuelle", "apoyo intermedio"]):
        return "SUSPENSION_CHASIS", "Juntas homocineticas o palieres danados"
    if any(k in t for k in ["cremallera", "bomba hidraulica de direccion", "caja de direccion", "sas", "angulo de direccion"]):
        return "SUSPENSION_CHASIS", "Cremallera de direccion o bomba hidraulica danada"
    if any(k in t for k in ["rotula", "terminal"]):
        return "SUSPENSION_CHASIS", "Rotulas o terminales de direccion con juego"
    if any(k in t for k in ["amortiguador", "bujes de trapecio", "suspension mc pherson", "bieletas", "buje"]):
        return "SUSPENSION_CHASIS", "Amortiguadores reventados o bujes de suspension"
    if any(k in t for k in ["rodamientos de rueda", "bocina", "buje de rueda"]):
        return "SUSPENSION_CHASIS", "Rodajes de caja mecanica o diferencial gastados"

    # 6. ELÉCTRICO
    if any(k in t for k in ["alternador", "p0562", "placa portadiodos", "diodos", "lin"]):
        return "ELECTRICO", "Alternador defectuoso o placa de diodos quemada"
    if any(k in t for k in ["motor de arranque", "arrancador", "solenoide"]):
        return "ELECTRICO", "Motor de arranque o solenoide defectuoso"
    if any(k in t for k in ["bateria", "bornes", "aislamiento", "inversor", "alto voltaje", "bujias de incandescencia"]):
        return "ELECTRICO", "Bateria descargada o bornes sulfatados"
    if any(k in t for k in ["relevador", "relay", "fusible", "can bus", "can-bus", "red de comunicacion"]):
        return "ELECTRICO", "Fusible quemado o rele principal danado"

    # 7. MOTOR
    if any(k in t for k in ["misfire", "bujia", "bobina", "p0300", "p0301", "p0302", "p0303", "p0304", "chispa"]):
        return "MOTOR", "Falla en bujias o bobinas de encendido (misfire)"
    if any(k in t for k in ["distribucion", "cadena", "faja", "desfase", "p0016", "p0017", "salto de diente"]):
        return "MOTOR", "Faja o cadena de distribucion destensada o corrida"
    if any(k in t for k in ["vvt", "p0011", "p0012", "sincronizacion variable", "ocv"]):
        return "MOTOR", "Falla en sincronizacion variable VVT"
    if any(k in t for k in ["ckp", "p0335", "ciguenal", "cmp", "p0340"]):
        return "MOTOR", "Falla en sensor de posicion ciguenal CKP"
    if any(k in t for k in ["inyector", "inyectores", "scv"]):
        return "MOTOR", "Inyectores obstruidos o sucios"
    if any(k in t for k in ["bomba de combustible", "presion de combustible", "caudal", "tanque", "aforador", "p0087", "hpfp", "alta presion gdi"]):
        return "MOTOR", "Bomba de gasolina quemada o con baja presion"
    if any(k in t for k in ["catalizador", "p0420", "contraprestion", "dpf", "fap", "adblue", "scr"]):
        return "MOTOR", "Catalizador obstruido o danado"
    if any(k in t for k in ["sensor de oxigeno", "sonda lambda", "mezcla", "p0171", "p0172", "maf", "map", "sensor a/f"]):
        return "MOTOR", "Falla en sensor de oxigeno o mezcla rica"
    if any(k in t for k in ["cuerpo de aceleracion", "valvula iac", "ralenti", "marcha minima", "p0505", "tps", "mariposa"]):
        return "MOTOR", "Valvula IAC o cuerpo de aceleracion sucio/descalibrado"
    if any(k in t for k in ["culata", "empaquetadura", "compresion", "leak-down", "co2", "estanqueidad"]):
        return "MOTOR", "Empaque de culata soplado o danado"
    if any(k in t for k in ["termostato", "motoventilador", "refrigerante", "radiador", "temperatura", "p0128"]):
        return "MOTOR", "Falla en termostato o motoventilador de radiador"
    if any(k in t for k in ["aceite", "presion de aceite", "pcv", "humo azul", "punterias", "taque"]):
        return "MOTOR", "Baja presion de aceite o bomba de aceite defectuosa"
    if any(k in t for k in ["turbo", "wastegate", "vgt", "intercooler"]):
        return "MOTOR", "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI"

    return "MOTOR", "Falla en bujias o bobinas de encendido (misfire)"

def ejecutar_reclasificacion():
    print("Reclasificando metadatos_manuales.json con máxima precisión técnica...")
    with open(METADATOS_JSON, "r", encoding="utf-8") as f:
        metadatos = json.load(f)

    conteo_sistemas = {}
    for item in metadatos:
        tit = item.get("titulo", "")
        dtcs = item.get("codigos_dtc", [])
        sis, fal = clasificar_procedimiento(tit, dtcs)
        item["sistema"] = sis
        item["falla"] = fal
        conteo_sistemas[sis] = conteo_sistemas.get(sis, 0) + 1

    with open(METADATOS_JSON, "w", encoding="utf-8") as f:
        json.dump(metadatos, f, indent=2, ensure_ascii=False)

    print("Distribución por Macro-Sistema:")
    for s, c in sorted(conteo_sistemas.items()):
        print(f"  • {s:<25}: {c} procedimientos")
    print("Reclasificación finalizada exitosamente.")

if __name__ == "__main__":
    ejecutar_reclasificacion()
