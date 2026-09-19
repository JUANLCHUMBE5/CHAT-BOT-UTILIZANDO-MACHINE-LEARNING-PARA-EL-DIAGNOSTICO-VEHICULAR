"""
Taxonomía Canónica de Macro-Sistemas Automotrices y Mapeo de Fallas.
Define la jerarquía oficial para la clasificación en dos niveles (Sistema -> Falla).
Cumple con la Regla 1 de Arquitectura de Tesis (Linear SVM + TF-IDF).
"""

from typing import Dict, List, Optional, Tuple

TAXONOMIA_MACRO_SISTEMAS: Dict[str, List[str]] = {
    "MOTOR": [
        "Falla en bujias o bobinas de encendido (misfire)",
        "Bomba de gasolina quemada o con baja presion",
        "Inyectores sucios o filtro de combustible obstruido",
        "Falla en sensor de oxigeno o mezcla rica",
        "Cuerpo de aceleracion o valvula IAC sucia",
        "Empaque de culata soplado o danado",
        "Falla en termostato o motoventilador de radiador",
        "Fuga en mangueras de refrigerante o radiador picado",
        "Consumo de aceite por desgaste de anillos o retenes",
        "Baja presion de aceite o bomba de aceite defectuosa",
        "Faja o cadena de distribucion destensada o con salto de punto",
        "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
        "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
        "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
        "Fuga en mangueras de intercooler o turbocompresor danado",
        "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)",
        "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)",
        "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
        "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
        "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)",
        "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
        "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)",
        "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
        "Falla en regulador de presion de combustible o diafragma roto",
        "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)",
        "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados",
    ],
    "FRENOS": [
        "Desgaste de pastillas y zapatas de freno",
        "Discos de freno alabeados o desgastados",
        "Falla en servofreno (booster) o linea de vacio",
        "Fuga hidraulica o aire en el sistema de frenos",
        "Falla en sensor de velocidad de rueda ABS",
        "Falla en sistema de frenado regenerativo (EV / Hibridos)",
        "Caliper de freno trabado o mordaza pegada (piston agarrotado)",
    ],
    "TRANSMISION": [
        "Disco de embrague desgastado o patinando",
        "Falla en bombin o bomba hidraulica de embrague",
        "Falta o degradacion de aceite de caja de cambios",
        "Rodajes de caja mecanica o diferencial gastados",
        "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        "Desgaste en collarin de empuje o crapodina de embrague",
        "Rodajes de transmision manual o eje primario gastados",
    ],
    "SUSPENSION_CHASIS": [
        "Amortiguadores reventados o bujes de suspension gastados",
        "Juntas homocineticas o palieres danados",
        "Llantas desbalanceadas o desalineadas",
        "Cremallera de direccion asistida con holgura o fuga",
        "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)",
    ],
    "ELECTRICO": [
        "Alternador defectuoso o placa de diodos quemada",
        "Bateria descargada o bornes sulfatados",
        "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
        "Fallo en inversor de corriente IGBT o motor electrico (EV)",
        "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)",
        "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
        "Fuga parasita de corriente en reposo (consumo nocturno de bateria)",
    ],
    "CLIMATIZACION": [
        "Falla en compresor de aire acondicionado o fuga de gas R134a",
    ],
    "CARROCERIA_NEUMATICA": [
        "Falla electrica del cierre centralizado o actuador de puerta",
        "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado",
        "Elevalunas electrico o guaya de alzacristales rota o trabada",
        "Limpiaparabrisas o motor pluma quemado",
        "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
        "Válvula de freno de aire o secador APS obstruido (Camiones)",
        "Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)",
    ]
}

# Mapeo inverso: Falla -> Macro-Sistema
FALLA_A_SISTEMA: Dict[str, str] = {}
for _sistema, _fallas in TAXONOMIA_MACRO_SISTEMAS.items():
    for _f in _fallas:
        FALLA_A_SISTEMA[_f] = _sistema

# Mapeo de prefijos y códigos DTC a Macro-Sistemas
DTC_A_SISTEMA: Dict[str, Tuple[str, List[str]]] = {
    # Misfire P0300 - P0312
    "P0300": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0301": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0302": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0303": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0304": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0305": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0306": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Inyectores sucios o filtro de combustible obstruido"]),
    # Circuitos de inyector
    "P0201": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0202": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0203": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0204": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    # Mezcla y Emisiones
    "P0171": ("MOTOR", ["Falla en servofreno (booster) o linea de vacio", "Cuerpo de aceleracion o valvula IAC sucia", "Falla en regulador de presion de combustible o diafragma roto", "Falla en sensor de oxigeno o mezcla rica"]),
    "P0172": ("MOTOR", ["Falla en regulador de presion de combustible o diafragma roto", "Falla en sensor de oxigeno o mezcla rica", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0420": ("MOTOR", ["Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)", "Falla en sensor de oxigeno o mezcla rica"]),
    "P0430": ("MOTOR", ["Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)", "Falla en sensor de oxigeno o mezcla rica"]),
    # EVAP
    "P0440": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"]),
    "P0442": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"]),
    "P0455": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"]),
    # Ralentí y aceleración
    "P0505": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0506": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0507": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    # Eléctrico / Alternador / Batería
    "P0562": ("ELECTRICO", ["Alternador defectuoso o placa de diodos quemada", "Bateria descargada o bornes sulfatados", "Fuga parasita de corriente en reposo (consumo nocturno de bateria)"]),
    "P0563": ("ELECTRICO", ["Alternador defectuoso o placa de diodos quemada"]),
    "P0620": ("ELECTRICO", ["Alternador defectuoso o placa de diodos quemada"]),
    # Transmisión / CVT / DSG
    "P0700": ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "Falta o degradacion de aceite de caja de cambios"]),
    "P0841": ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG"]),
    "P0730": ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "Falta o degradacion de aceite de caja de cambios"]),
    "P0810": ("TRANSMISION", ["Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)", "Falla en bombin o bomba hidraulica de embrague"]),
    # Termostato
    "P0128": ("MOTOR", ["Falla en termostato o motoventilador de radiador", "Fuga en mangueras de refrigerante o radiador picado"]),
    # Sensor CKP / CMP
    "P0335": ("MOTOR", ["Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)", "Faja o cadena de distribucion destensada o con salto de punto"]),
    "P0336": ("MOTOR", ["Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)"]),
    "P0340": ("MOTOR", ["Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)", "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)"]),
    # ABS
    "C0035": ("FRENOS", ["Falla en sensor de velocidad de rueda ABS"]),
    "C0040": ("FRENOS", ["Falla en sensor de velocidad de rueda ABS", "Fuga hidraulica o aire en el sistema de frenos"]),
}

def obtener_macro_sistema(falla: str) -> str:
    """Devuelve el Macro-Sistema correspondiente a una falla específica."""
    if falla in FALLA_A_SISTEMA:
        return FALLA_A_SISTEMA[falla]
    falla_baja = falla.lower()
    if any(k in falla_baja for k in ("freno", "pastilla", "disco", "booster", "abs", "caliper", "mordaza")):
        return "FRENOS"
    if any(k in falla_baja for k in ("embrague", "caja", "cvt", "dsg", "dualogic", "collarin", "crapodina")):
        return "TRANSMISION"
    if any(k in falla_baja for k in ("amortiguador", "palier", "llanta", "direccion", "buje", "rodamiento", "maza", "rodaje")):
        return "SUSPENSION_CHASIS"
    if any(k in falla_baja for k in ("bateria", "alternador", "inversor", "arranque", "arrancador", "solenoide", "fuga parasita", "consumo nocturno")):
        return "ELECTRICO"
    if "aire acondicionado" in falla_baja:
        return "CLIMATIZACION"
    if any(k in falla_baja for k in ("camion", "puerta", "cierre", "limpiaparabrisas", "elevador", "maxi-brake", "resorte")):
        return "CARROCERIA_NEUMATICA"
    return "MOTOR"

def obtener_sistema_por_dtc(codigo_dtc: str) -> Optional[Tuple[str, List[str]]]:
    """Devuelve el sistema y las fallas prioritarias asociadas a un código OBD-II."""
    codigo = codigo_dtc.strip().upper()
    if codigo in DTC_A_SISTEMA:
        return DTC_A_SISTEMA[codigo]
    # Regla por letra inicial OBD-II
    if codigo.startswith("P"):
        num = codigo[1:]
        if num.startswith("07") or num.startswith("08") or num.startswith("09"):
            return ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "Falta o degradacion de aceite de caja de cambios"])
        return ("MOTOR", [])
    elif codigo.startswith("C"):
        return ("FRENOS", ["Falla en sensor de velocidad de rueda ABS", "Desgaste de pastillas y zapatas de freno"])
    elif codigo.startswith("B"):
        return ("CARROCERIA_NEUMATICA", ["Falla electrica del cierre centralizado o actuador de puerta"])
    elif codigo.startswith("U"):
        return ("ELECTRICO", ["Alternador defectuoso o placa de diodos quemada", "Bateria descargada o bornes sulfatados"])
    return None
