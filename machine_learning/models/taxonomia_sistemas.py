"""
Taxonomía Canónica de Macro-Sistemas Automotrices, Subáreas y Contrato de Inferencia ML.
Fuente única de verdad (Single Source of Truth) para las 61 clases entrenadas del SVM
y la jerarquía oficial en dos niveles (Macro-Sistema -> Falla).
Cumple con la Regla 1 de Arquitectura de Tesis (Linear SVM + TF-IDF).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

MODEL_VERSION: str = "c1_fase10_final"
TAXONOMY_VERSION: str = "61_clases_7_macrosistemas_v2"

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
    ],
}

# Mapeo inverso: Falla -> Macro-Sistema y Class ID determinista (C01..C61)
FALLA_A_SISTEMA: Dict[str, str] = {}
CLASS_ID_POR_FALLA: Dict[str, str] = {}
FALLA_POR_CLASS_ID: Dict[str, str] = {}
_idx_global = 1
for _sistema, _fallas in TAXONOMIA_MACRO_SISTEMAS.items():
    for _f in _fallas:
        FALLA_A_SISTEMA[_f] = _sistema
        _cid = f"C{_idx_global:02d}"
        CLASS_ID_POR_FALLA[_f] = _cid
        FALLA_POR_CLASS_ID[_cid] = _f
        _idx_global += 1

CLASES_ENTRENADAS_61: Tuple[str, ...] = tuple(FALLA_A_SISTEMA.keys())

# Mapeo exhaustivo de cada una de las 61 clases entrenadas a las subáreas técnicas del enrutador.
# Evita que listas blancas manuales incompletas descarten clases legítimas del SVM.
SUBAREAS_POR_CLASE: Dict[str, Set[str]] = {
    # MOTOR (26)
    "Falla en bujias o bobinas de encendido (misfire)": {"motor_encendido", "combustible_admision"},
    "Bomba de gasolina quemada o con baja presion": {"combustible_admision", "motor_encendido", "electrico_carga"},
    "Inyectores sucios o filtro de combustible obstruido": {"combustible_admision", "motor_encendido", "admision_map"},
    "Falla en sensor de oxigeno o mezcla rica": {"combustible_admision", "emisiones_escape", "motor_encendido", "admision_map"},
    "Cuerpo de aceleracion o valvula IAC sucia": {"combustible_admision", "motor_encendido", "admision_map"},
    "Empaque de culata soplado o danado": {"refrigeracion", "lubricacion", "motor_encendido"},
    "Falla en termostato o motoventilador de radiador": {"refrigeracion", "electrico_carga"},
    "Fuga en mangueras de refrigerante o radiador picado": {"refrigeracion"},
    "Consumo de aceite por desgaste de anillos o retenes": {"lubricacion", "motor_encendido", "emisiones_escape"},
    "Baja presion de aceite o bomba de aceite defectuosa": {"lubricacion", "motor_encendido"},
    "Faja o cadena de distribucion destensada o con salto de punto": {"distribucion_sincronizacion", "motor_encendido"},
    "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)": {"distribucion_sincronizacion", "motor_encendido", "lubricacion"},
    "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)": {"combustible_admision", "motor_encendido", "admision_map"},
    "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI": {"combustible_admision", "admision_map", "motor_encendido", "emisiones_escape"},
    "Fuga en mangueras de intercooler o turbocompresor danado": {"combustible_admision", "admision_map", "motor_encendido", "emisiones_escape", "lubricacion"},
    "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)": {"distribucion_sincronizacion", "lubricacion", "motor_encendido"},
    "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)": {"combustible_admision", "electrico_carga", "electrico_ecu", "motor_encendido"},
    "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)": {"emisiones_escape", "combustible_admision", "motor_encendido"},
    "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)": {"combustible_admision", "motor_encendido", "emisiones_escape"},
    "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)": {"combustible_admision", "motor_encendido"},
    "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)": {"motor_encendido", "distribucion_sincronizacion", "electrico_ecu", "combustible_admision"},
    "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)": {"emisiones_escape", "combustible_admision"},
    "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)": {"emisiones_escape", "combustible_admision", "motor_encendido"},
    "Falla en regulador de presion de combustible o diafragma roto": {"combustible_admision", "motor_encendido"},
    "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)": {"combustible_admision", "motor_encendido", "electrico_ecu"},
    "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados": {"motor_encendido", "lubricacion", "distribucion_sincronizacion"},
    # FRENOS (7)
    "Desgaste de pastillas y zapatas de freno": {"frenos"},
    "Discos de freno alabeados o desgastados": {"frenos", "suspension_direccion"},
    "Falla en servofreno (booster) o linea de vacio": {"frenos", "combustible_admision", "admision_map"},
    "Fuga hidraulica o aire en el sistema de frenos": {"frenos"},
    "Falla en sensor de velocidad de rueda ABS": {"frenos", "electrico_ecu", "suspension_direccion"},
    "Falla en sistema de frenado regenerativo (EV / Hibridos)": {"frenos", "electrico_carga", "electrico_ecu"},
    "Caliper de freno trabado o mordaza pegada (piston agarrotado)": {"frenos", "suspension_direccion"},
    # TRANSMISION (8)
    "Disco de embrague desgastado o patinando": {"transmision"},
    "Falla en bombin o bomba hidraulica de embrague": {"transmision", "frenos"},
    "Falta o degradacion de aceite de caja de cambios": {"transmision", "lubricacion"},
    "Rodajes de caja mecanica o diferencial gastados": {"transmision", "suspension_direccion"},
    "Sobrecalentamiento o solenoides en caja automatica CVT / DSG": {"transmision", "refrigeracion", "electrico_ecu"},
    "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)": {"transmision", "electrico_ecu"},
    "Desgaste en collarin de empuje o crapodina de embrague": {"transmision"},
    "Rodajes de transmision manual o eje primario gastados": {"transmision"},
    # SUSPENSION_CHASIS (5)
    "Amortiguadores reventados o bujes de suspension gastados": {"suspension_direccion"},
    "Juntas homocineticas o palieres danados": {"suspension_direccion", "transmision"},
    "Llantas desbalanceadas o desalineadas": {"suspension_direccion", "frenos"},
    "Cremallera de direccion asistida con holgura o fuga": {"suspension_direccion", "lubricacion"},
    "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)": {"suspension_direccion", "frenos"},
    # ELECTRICO (7)
    "Alternador defectuoso o placa de diodos quemada": {"electrico_carga", "electrico_ecu"},
    "Bateria descargada o bornes sulfatados": {"electrico_carga", "electrico_ecu"},
    "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)": {"electrico_carga", "electrico_ecu"},
    "Fallo en inversor de corriente IGBT o motor electrico (EV)": {"electrico_carga", "electrico_ecu", "transmision"},
    "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)": {"refrigeracion", "electrico_carga", "electrico_ecu"},
    "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)": {"electrico_carga", "motor_encendido"},
    "Fuga parasita de corriente en reposo (consumo nocturno de bateria)": {"electrico_carga", "electrico_ecu"},
    # CLIMATIZACION (1)
    "Falla en compresor de aire acondicionado o fuga de gas R134a": {"climatizacion", "refrigeracion", "electrico_carga"},
    # CARROCERIA_NEUMATICA (7)
    "Falla electrica del cierre centralizado o actuador de puerta": {"carroceria", "electrico_carga"},
    "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado": {"carroceria"},
    "Elevalunas electrico o guaya de alzacristales rota o trabada": {"carroceria", "electrico_carga"},
    "Limpiaparabrisas o motor pluma quemado": {"carroceria", "electrico_carga"},
    "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)": {"frenos", "carroceria"},
    "Válvula de freno de aire o secador APS obstruido (Camiones)": {"frenos", "carroceria"},
    "Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)": {"frenos", "carroceria"},
}

# Mapeo de códigos DTC OBD-II a Macro-Sistemas y clases entrenadas asociadas
DTC_A_SISTEMA: Dict[str, Tuple[str, List[str]]] = {
    # Misfire P0300 - P0312
    "P0300": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0301": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0302": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0303": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0304": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"]),
    "P0305": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0306": ("MOTOR", ["Falla en bujias o bobinas de encendido (misfire)", "Inyectores sucios o filtro de combustible obstruido"]),
    # Circuitos de inyector y presión de combustible
    "P0201": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0202": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0203": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0204": ("MOTOR", ["Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0087": ("MOTOR", ["Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", "Bomba de gasolina quemada o con baja presion", "Falla en regulador de presion de combustible o diafragma roto"]),
    "P0088": ("MOTOR", ["Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", "Falla en regulador de presion de combustible o diafragma roto"]),
    "P0190": ("MOTOR", ["Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", "Falla en regulador de presion de combustible o diafragma roto"]),
    "P0230": ("MOTOR", ["Bomba de gasolina quemada o con baja presion", "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)"]),
    # Sensores MAF / MAP / TPS / ECT
    "P0100": ("MOTOR", ["Inyectores sucios o filtro de combustible obstruido", "Cuerpo de aceleracion o valvula IAC sucia", "Falla en sensor de oxigeno o mezcla rica"]),
    "P0101": ("MOTOR", ["Inyectores sucios o filtro de combustible obstruido", "Cuerpo de aceleracion o valvula IAC sucia", "Falla en sensor de oxigeno o mezcla rica"]),
    "P0102": ("MOTOR", ["Inyectores sucios o filtro de combustible obstruido", "Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0103": ("MOTOR", ["Inyectores sucios o filtro de combustible obstruido", "Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0105": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia", "Falla en servofreno (booster) o linea de vacio"]),
    "P0106": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia", "Falla en servofreno (booster) o linea de vacio"]),
    "P0115": ("MOTOR", ["Falla en termostato o motoventilador de radiador"]),
    "P0116": ("MOTOR", ["Falla en termostato o motoventilador de radiador"]),
    "P0117": ("MOTOR", ["Falla en termostato o motoventilador de radiador"]),
    "P0118": ("MOTOR", ["Falla en termostato o motoventilador de radiador"]),
    "P0120": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0121": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0122": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0123": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P2135": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    # Turbo / Sobrealimentación
    "P0234": ("MOTOR", ["Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI", "Fuga en mangueras de intercooler o turbocompresor danado"]),
    "P0299": ("MOTOR", ["Fuga en mangueras de intercooler o turbocompresor danado", "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI"]),
    # Mezcla y Emisiones
    "P0171": ("MOTOR", ["Falla en sensor de oxigeno o mezcla rica", "Falla en servofreno (booster) o linea de vacio", "Bomba de gasolina quemada o con baja presion", "Falla en regulador de presion de combustible o diafragma roto", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0172": ("MOTOR", ["Falla en sensor de oxigeno o mezcla rica", "Falla en regulador de presion de combustible o diafragma roto", "Inyectores sucios o filtro de combustible obstruido"]),
    "P0400": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)", "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)"]),
    "P0401": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)", "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)"]),
    "P0402": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)", "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)"]),
    "P0420": ("MOTOR", ["Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)", "Falla en sensor de oxigeno o mezcla rica"]),
    "P0430": ("MOTOR", ["Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)", "Falla en sensor de oxigeno o mezcla rica"]),
    "P2002": ("MOTOR", ["Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)"]),
    "P2463": ("MOTOR", ["Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)"]),
    # EVAP
    "P0440": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"]),
    "P0442": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"]),
    "P0455": ("MOTOR", ["Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"]),
    # Ralentí y aceleración
    "P0505": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0506": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    "P0507": ("MOTOR", ["Cuerpo de aceleracion o valvula IAC sucia"]),
    # Eléctrico / Alternador / Batería / ECU
    "P0562": ("ELECTRICO", ["Alternador defectuoso o placa de diodos quemada", "Bateria descargada o bornes sulfatados", "Fuga parasita de corriente en reposo (consumo nocturno de bateria)"]),
    "P0563": ("ELECTRICO", ["Alternador defectuoso o placa de diodos quemada"]),
    "P0620": ("ELECTRICO", ["Alternador defectuoso o placa de diodos quemada"]),
    "U0100": ("ELECTRICO", ["Bateria descargada o bornes sulfatados", "Alternador defectuoso o placa de diodos quemada"]),
    "U0101": ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)"]),
    "U0121": ("FRENOS", ["Falla en sensor de velocidad de rueda ABS"]),
    # Transmisión / CVT / DSG
    "P0700": ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "Falta o degradacion de aceite de caja de cambios"]),
    "P0841": ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG"]),
    "P0730": ("TRANSMISION", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "Falta o degradacion de aceite de caja de cambios"]),
    "P0810": ("TRANSMISION", ["Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)", "Falla en bombin o bomba hidraulica de embrague"]),
    # Termostato
    "P0128": ("MOTOR", ["Falla en termostato o motoventilador de radiador", "Fuga en mangueras de refrigerante o radiador picado"]),
    # Sensor CKP / CMP y VVT
    "P0011": ("MOTOR", ["Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)", "Faja o cadena de distribucion destensada o con salto de punto"]),
    "P0016": ("MOTOR", ["Faja o cadena de distribucion destensada o con salto de punto", "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)"]),
    "P0335": ("MOTOR", ["Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)", "Faja o cadena de distribucion destensada o con salto de punto"]),
    "P0336": ("MOTOR", ["Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)"]),
    "P0340": ("MOTOR", ["Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)", "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)"]),
    "P0341": ("MOTOR", ["Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)"]),
    # ABS
    "C0035": ("FRENOS", ["Falla en sensor de velocidad de rueda ABS"]),
    "C0040": ("FRENOS", ["Falla en sensor de velocidad de rueda ABS", "Fuga hidraulica o aire en el sistema de frenos"]),
}


@dataclass(frozen=True)
class ContratoPrediccionML:
    """Contrato versionado de inferencia entre el módulo ML y el Backend."""

    model_version: str
    taxonomy_version: str
    class_id: str
    class_label: str
    subsystem: str
    top_k: List[Dict[str, Any]]
    raw_svm_score: float
    calibrated_probability: float
    prediction_source: str
    abstention_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def es_clase_entrenada_svm(falla: str) -> bool:
    """Indica si una etiqueta pertenece exactamente a las 61 clases entrenadas del SVM."""
    return str(falla or "").strip() in FALLA_A_SISTEMA


def obtener_class_id(falla: str) -> str:
    """Devuelve el identificador canónico C01..C61 o un marcador explícito para reglas/abstenciones."""
    limpia = str(falla or "").strip()
    if limpia in CLASS_ID_POR_FALLA:
        return CLASS_ID_POR_FALLA[limpia]
    if not limpia or "indeterminado" in limpia.lower() or "fuera" in limpia.lower() or "auto-pregunta" in limpia.lower():
        return "ABSTENCION"
    return "HIPOTESIS_REGLA"


def obtener_subareas_de_clase(falla: str) -> Set[str]:
    """Devuelve las subáreas técnicas asociadas a una clase de las 61 entrenadas."""
    return set(SUBAREAS_POR_CLASE.get(str(falla or "").strip(), set()))


def obtener_macro_sistema(falla: str) -> str:
    """Devuelve el Macro-Sistema correspondiente a una falla específica."""
    if falla in FALLA_A_SISTEMA:
        return FALLA_A_SISTEMA[falla]
    falla_baja = falla.lower()
    if any(k in falla_baja for k in ("freno", "pastilla", "disco", "booster", "abs", "caliper", "mordaza")):
        return "FRENOS"
    if any(k in falla_baja for k in ("embrague", "caja", "cvt", "dsg", "dualogic", "collarin", "crapodina")):
        return "TRANSMISION"
    if any(k in falla_baja for k in ("amortiguador", "palier", "llanta", "direccion", "buje", "rodamiento", "maza", "rodaje", "rotula", "bieleta")):
        return "SUSPENSION_CHASIS"
    if any(k in falla_baja for k in ("bateria", "alternador", "inversor", "arranque", "arrancador", "solenoide", "fuga parasita", "consumo nocturno", "ecu", "inmovilizador", "red can", "arnes")):
        return "ELECTRICO"
    if "aire acondicionado" in falla_baja:
        return "CLIMATIZACION"
    if any(k in falla_baja for k in ("camion", "puerta", "cierre", "limpiaparabrisas", "elevador", "maxi-brake", "resorte", "chapa", "pestillo", "alzacristales")):
        return "CARROCERIA_NEUMATICA"
    return "MOTOR"


def obtener_sistema_por_dtc(codigo_dtc: str) -> Optional[Tuple[str, List[str]]]:
    """Devuelve el sistema y las fallas prioritarias asociadas a un código OBD-II."""
    codigo = codigo_dtc.strip().upper()
    if codigo in DTC_A_SISTEMA:
        return DTC_A_SISTEMA[codigo]
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


def construir_contrato_prediccion(
    *,
    class_label: str,
    raw_svm_score: float,
    calibrated_probability: float,
    prediction_source: str,
    top_k: Optional[List[Dict[str, Any]]] = None,
    abstention_reason: Optional[str] = None,
) -> ContratoPrediccionML:
    """Construye una instancia validada del contrato de inferencia ML."""
    fuente = str(prediction_source or "SVM").upper()
    es_svm = es_clase_entrenada_svm(class_label) and fuente in {"SVM", "SVM_JERARQUICO", "SVM_DTC"}
    prob_calibrada = float(calibrated_probability) if es_svm else 0.0
    return ContratoPrediccionML(
        model_version=MODEL_VERSION,
        taxonomy_version=TAXONOMY_VERSION,
        class_id=obtener_class_id(class_label),
        class_label=str(class_label),
        subsystem=obtener_macro_sistema(class_label),
        top_k=list(top_k or []),
        raw_svm_score=round(float(raw_svm_score), 4),
        calibrated_probability=round(prob_calibrada, 4),
        prediction_source=fuente,
        abstention_reason=abstention_reason,
    )
