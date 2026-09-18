"""
Script de Ground Truth y Auditoría del Benchmark V2 (100 Casos).
Calcula:
- Accuracy Externa Top-1
- Top-3 Accuracy
- Clasificación de errores: Correcto, Parcial, Incorrecto, Ambiguo
- Precision, Recall, Macro-F1
- Matriz de confusión externa
- Identificación de clases débiles y pares de confusión
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent

# Mapeo de Macro-Sistemas
SISTEMAS = {
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
    ],
    "FRENOS": [
        "Desgaste de pastillas y zapatas de freno",
        "Discos de freno alabeados o desgastados",
        "Falla en servofreno (booster) o linea de vacio",
        "Fuga hidraulica o aire en el sistema de frenos",
        "Falla en sensor de velocidad de rueda ABS",
        "Falla en sistema de frenado regenerativo (EV / Hibridos)",
    ],
    "TRANSMISION": [
        "Disco de embrague desgastado o patinando",
        "Falla en bombin o bomba hidraulica de embrague",
        "Falta o degradacion de aceite de caja de cambios",
        "Rodajes de caja mecanica o diferencial gastados",
        "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
    ],
    "SUSPENSION_CHASIS": [
        "Amortiguadores reventados o bujes de suspension gastados",
        "Juntas homocineticas o palieres danados",
        "Llantas desbalanceadas o desalineadas",
        "Cremallera de direccion asistida con holgura o fuga",
    ],
    "ELECTRICO": [
        "Alternador defectuoso o placa de diodos quemada",
        "Bateria descargada o bornes sulfatados",
        "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
        "Fallo en inversor de corriente IGBT o motor electrico (EV)",
        "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)",
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
    ]
}

def obtener_sistema(falla: str) -> str:
    for sist, fallas in SISTEMAS.items():
        if falla in fallas:
            return sist
    # Búsqueda por similitud de nombres
    if "freno" in falla.lower() or "pastilla" in falla.lower() or "disco" in falla.lower() or "booster" in falla.lower():
        return "FRENOS"
    if "embrague" in falla.lower() or "caja" in falla.lower() or "cvt" in falla.lower() or "dualogic" in falla.lower():
        return "TRANSMISION"
    if "suspension" in falla.lower() or "llanta" in falla.lower() or "direccion" in falla.lower() or "palier" in falla.lower():
        return "SUSPENSION_CHASIS"
    if "bateria" in falla.lower() or "alternador" in falla.lower():
        return "ELECTRICO"
    if "aire acondicionado" in falla.lower():
        return "CLIMATIZACION"
    if "camion" in falla.lower() or "puerta" in falla.lower() or "cierre" in falla.lower():
        return "CARROCERIA_NEUMATICA"
    return "MOTOR"

# GROUND TRUTH OFICIAL DE LOS 100 CASOS
# Cada entrada tiene:
# - esperado_top1: clase principal esperada
# - aceptables_top1: clases alternativas válidas en diagnóstico diferencial de taller
# - notas: razón técnica
GROUND_TRUTH_G1 = [
    # 01
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": "P0302"},
    # 02
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 03
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 04
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 05
    {"esperado": "Falla en servofreno (booster) o linea de vacio", "aceptables": ["Cuerpo de aceleracion o valvula IAC sucia"], "dtc": "P0171"},
    # 06
    {"esperado": "Bateria descargada o bornes sulfatados", "aceptables": ["Alternador defectuoso o placa de diodos quemada"], "dtc": None},
    # 07
    {"esperado": "Alternador defectuoso o placa de diodos quemada", "aceptables": ["Bateria descargada o bornes sulfatados"], "dtc": None},
    # 08
    {"esperado": "Bateria descargada o bornes sulfatados", "aceptables": ["Alternador defectuoso o placa de diodos quemada"], "dtc": None},
    # 09
    {"esperado": "Alternador defectuoso o placa de diodos quemada", "aceptables": ["Bateria descargada o bornes sulfatados"], "dtc": None},
    # 10
    {"esperado": "Alternador defectuoso o placa de diodos quemada", "aceptables": ["Bateria descargada o bornes sulfatados"], "dtc": "P0562"},
    # 11
    {"esperado": "Falla en servofreno (booster) o linea de vacio", "aceptables": [], "dtc": None},
    # 12
    {"esperado": "Fuga hidraulica o aire en el sistema de frenos", "aceptables": ["Desgaste de pastillas y zapatas de freno"], "dtc": None},
    # 13
    {"esperado": "Discos de freno alabeados o desgastados", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
    # 14
    {"esperado": "Llantas desbalanceadas o desalineadas", "aceptables": ["Amortiguadores reventados o bujes de suspension gastados"], "dtc": None},
    # 15
    {"esperado": "Desgaste de pastillas y zapatas de freno", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
    # 16
    {"esperado": "Falla en termostato o motoventilador de radiador", "aceptables": ["Fuga en mangueras de refrigerante o radiador picado"], "dtc": None},
    # 17
    {"esperado": "Empaque de culata soplado o danado", "aceptables": ["Fuga en mangueras de refrigerante o radiador picado"], "dtc": None},
    # 18
    {"esperado": "Falla en termostato o motoventilador de radiador", "aceptables": ["Fuga en mangueras de refrigerante o radiador picado"], "dtc": None},
    # 19
    {"esperado": "Baja presion de aceite o bomba de aceite defectuosa", "aceptables": [], "dtc": None},
    # 20
    {"esperado": "Consumo de aceite por desgaste de anillos o retenes", "aceptables": [], "dtc": None},
    # 21
    {"esperado": "Disco de embrague desgastado o patinando", "aceptables": [], "dtc": None},
    # 22
    {"esperado": "Falla en bombin o bomba hidraulica de embrague", "aceptables": ["Disco de embrague desgastado o patinando"], "dtc": None},
    # 23
    {"esperado": "Falla en bombin o bomba hidraulica de embrague", "aceptables": ["Rodajes de caja mecanica o diferencial gastados"], "dtc": None},
    # 24
    {"esperado": "Disco de embrague desgastado o patinando", "aceptables": ["Falla en bujias o bobinas de encendido (misfire)"], "dtc": None},
    # 25
    {"esperado": "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)", "aceptables": [], "dtc": None},
    # 26
    {"esperado": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "aceptables": [], "dtc": "P0841"},
    # 27
    {"esperado": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "aceptables": ["Falta o degradacion de aceite de caja de cambios"], "dtc": None},
    # 28
    {"esperado": "Falta o degradacion de aceite de caja de cambios", "aceptables": ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG"], "dtc": None},
    # 29
    {"esperado": "Amortiguadores reventados o bujes de suspension gastados", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
    # 30
    {"esperado": "Juntas homocineticas o palieres danados", "aceptables": ["Cremallera de direccion asistida con holgura o fuga"], "dtc": None},
    # 31
    {"esperado": "Amortiguadores reventados o bujes de suspension gastados", "aceptables": [], "dtc": None},
    # 32
    {"esperado": "Llantas desbalanceadas o desalineadas", "aceptables": ["Cremallera de direccion asistida con holgura o fuga"], "dtc": None},
    # 33
    {"esperado": "Llantas desbalanceadas o desalineadas", "aceptables": ["Amortiguadores reventados o bujes de suspension gastados"], "dtc": None},
    # 34
    {"esperado": "Llantas desbalanceadas o desalineadas", "aceptables": ["Discos de freno alabeados o desgastados"], "dtc": None},
    # 35
    {"esperado": "Rodajes de caja mecanica o diferencial gastados", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
    # 36
    {"esperado": "Bomba de gasolina quemada o con baja presion", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 37
    {"esperado": "Bomba de gasolina quemada o con baja presion", "aceptables": [], "dtc": None},
    # 38
    {"esperado": "Bomba de gasolina quemada o con baja presion", "aceptables": ["Falla en bujias o bobinas de encendido (misfire)"], "dtc": None},
    # 39
    {"esperado": "Cuerpo de aceleracion o valvula IAC sucia", "aceptables": ["Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 40
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 41
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Falla en bujias o bobinas de encendido (misfire)"], "dtc": "P0420"},
    # 42
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Falla en sensor de oxigeno o mezcla rica"], "dtc": "P0301"},
    # 43
    {"esperado": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)", "aceptables": ["Válvula de freno de aire o secador APS obstruido (Camiones)"], "dtc": None},
    # 44
    {"esperado": "Válvula de freno de aire o secador APS obstruido (Camiones)", "aceptables": ["Fugas de aire o fallos en el sistema de frenos neumático (Camiones)"], "dtc": None},
    # 45
    {"esperado": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)", "aceptables": ["Válvula de freno de aire o secador APS obstruido (Camiones)"], "dtc": None},
    # 46
    {"esperado": "Falla electrica del cierre centralizado o actuador de puerta", "aceptables": ["Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado"], "dtc": None},
    # 47
    {"esperado": "Falla electrica del cierre centralizado o actuador de puerta", "aceptables": ["Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado"], "dtc": None},
    # 48
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Bomba de gasolina quemada o con baja presion", "Falla en sensor de oxigeno o mezcla rica"], "dtc": None},
    # 49
    {"esperado": "Amortiguadores reventados o bujes de suspension gastados", "aceptables": ["Llantas desbalanceadas o desalineadas", "Juntas homocineticas o palieres danados"], "dtc": None},
    # 50
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Inyectores sucios o filtro de combustible obstruido", "Bomba de gasolina quemada o con baja presion"], "dtc": None},
]

GROUND_TRUTH_G2 = [
    # 01
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 02
    {"esperado": "Bomba de gasolina quemada o con baja presion", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 03
    {"esperado": "Rodajes de caja mecanica o diferencial gastados", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
    # 04
    {"esperado": "Discos de freno alabeados o desgastados", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
    # 05
    {"esperado": "Llantas desbalanceadas o desalineadas", "aceptables": ["Discos de freno alabeados o desgastados"], "dtc": None},
    # 06
    {"esperado": "Fuga hidraulica o aire en el sistema de frenos", "aceptables": ["Desgaste de pastillas y zapatas de freno"], "dtc": None},
    # 07
    {"esperado": "Bateria descargada o bornes sulfatados", "aceptables": ["Alternador defectuoso o placa de diodos quemada"], "dtc": None},
    # 08
    {"esperado": "Falla en bujias o bobinas de encendido (misfire)", "aceptables": ["Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 09
    {"esperado": "Cuerpo de aceleracion o valvula IAC sucia", "aceptables": ["Falla en compresor de aire acondicionado o fuga de gas R134a"], "dtc": None},
    # 10
    {"esperado": "Amortiguadores reventados o bujes de suspension gastados", "aceptables": ["Juntas homocineticas o palieres danados"], "dtc": None},
    # 11
    {"esperado": "Juntas homocineticas o palieres danados", "aceptables": ["Amortiguadores reventados o bujes de suspension gastados"], "dtc": None},
    # 12
    {"esperado": "Disco de embrague desgastado o patinando", "aceptables": [], "dtc": None},
    # 13
    {"esperado": "Alternador defectuoso o placa de diodos quemada", "aceptables": ["Bateria descargada o bornes sulfatados"], "dtc": None},
    # 14
    {"esperado": "Falla en termostato o motoventilador de radiador", "aceptables": ["Fuga en mangueras de refrigerante o radiador picado"], "dtc": None},
    # 15
    {"esperado": "Inyectores sucios o filtro de combustible obstruido", "aceptables": ["Falla en sensor de oxigeno o mezcla rica", "Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 16
    {"esperado": "Cuerpo de aceleracion o valvula IAC sucia", "aceptables": ["Falla en servofreno (booster) o linea de vacio"], "dtc": None},
    # 17
    {"esperado": "Juntas homocineticas o palieres danados", "aceptables": ["Discos de freno alabeados o desgastados"], "dtc": None},
    # 18
    {"esperado": "Amortiguadores reventados o bujes de suspension gastados", "aceptables": [], "dtc": None},
    # 19
    {"esperado": "Rodajes de caja mecanica o diferencial gastados", "aceptables": ["Falla en bombin o bomba hidraulica de embrague"], "dtc": None},
    # 20
    {"esperado": "Amortiguadores reventados o bujes de suspension gastados", "aceptables": ["Disco de embrague desgastado o patinando"], "dtc": None},
    # 21
    {"esperado": "Bateria descargada o bornes sulfatados", "aceptables": ["Alternador defectuoso o placa de diodos quemada"], "dtc": None},
    # 22
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 23
    {"esperado": "Cuerpo de aceleracion o valvula IAC sucia", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 24
    {"esperado": "Falla en termostato o motoventilador de radiador", "aceptables": [], "dtc": None},
    # 25
    {"esperado": "Desgaste de pastillas y zapatas de freno", "aceptables": ["Discos de freno alabeados o desgastados"], "dtc": None},
    # 26
    {"esperado": "Llantas desbalanceadas o desalineadas", "aceptables": ["Amortiguadores reventados o bujes de suspension gastados"], "dtc": None},
    # 27
    {"esperado": "Juntas homocineticas o palieres danados", "aceptables": ["Amortiguadores reventados o bujes de suspension gastados", "Cremallera de direccion asistida con holgura o fuga"], "dtc": None},
    # 28
    {"esperado": "Empaque de culata soplado o danado", "aceptables": ["Fuga en mangueras de refrigerante o radiador picado"], "dtc": None},
    # 29
    {"esperado": "Bomba de gasolina quemada o con baja presion", "aceptables": ["Cuerpo de aceleracion o valvula IAC sucia"], "dtc": None},
    # 30
    {"esperado": "Cremallera de direccion asistida con holgura o fuga", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
    # 31
    {"esperado": "Inyectores sucios o filtro de combustible obstruido", "aceptables": ["Falla en sensor de oxigeno o mezcla rica", "Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 32
    {"esperado": "Cremallera de direccion asistida con holgura o fuga", "aceptables": ["Juntas homocineticas o palieres danados"], "dtc": None},
    # 33
    {"esperado": "Alternador defectuoso o placa de diodos quemada", "aceptables": ["Bateria descargada o bornes sulfatados"], "dtc": None},
    # 34
    {"esperado": "Desgaste de pastillas y zapatas de freno", "aceptables": ["Discos de freno alabeados o desgastados", "Fuga hidraulica o aire en el sistema de frenos"], "dtc": None},
    # 35
    {"esperado": "Fuga hidraulica o aire en el sistema de frenos", "aceptables": ["Falla en servofreno (booster) o linea de vacio"], "dtc": None},
    # 36
    {"esperado": "Faja o cadena de distribucion destensada o con salto de punto", "aceptables": ["Baja presion de aceite o bomba de aceite defectuosa", "Falla en bujias o bobinas de encendido (misfire)"], "dtc": None},
    # 37
    {"esperado": "Llantas desbalanceadas o desalineadas", "aceptables": ["Juntas homocineticas o palieres danados"], "dtc": None},
    # 38
    {"esperado": "Faja o cadena de distribucion destensada o con salto de punto", "aceptables": ["Falla en bujias o bobinas de encendido (misfire)"], "dtc": None},
    # 39
    {"esperado": "Falla en termostato o motoventilador de radiador", "aceptables": [], "dtc": None},
    # 40
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 41
    {"esperado": "Bateria descargada o bornes sulfatados", "aceptables": ["Alternador defectuoso o placa de diodos quemada", "Falla en termostato o motoventilador de radiador"], "dtc": None},
    # 42
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Faja o cadena de distribucion destensada o con salto de punto", "Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 43
    {"esperado": "Bomba de gasolina quemada o con baja presion", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 44
    {"esperado": "Falla en compresor de aire acondicionado o fuga de gas R134a", "aceptables": ["Alternador defectuoso o placa de diodos quemada"], "dtc": None},
    # 45
    {"esperado": "Consumo de aceite por desgaste de anillos o retenes", "aceptables": ["Empaque de culata soplado o danado"], "dtc": None},
    # 46
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Falla en bujias o bobinas de encendido (misfire)"], "dtc": None},
    # 47
    {"esperado": "Falla en termostato o motoventilador de radiador", "aceptables": ["Fuga en mangueras de refrigerante o radiador picado"], "dtc": None},
    # 48
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Inyectores sucios o filtro de combustible obstruido"], "dtc": None},
    # 49
    {"esperado": "Falla en sensor de oxigeno o mezcla rica", "aceptables": ["Bomba de gasolina quemada o con baja presion"], "dtc": None},
    # 50
    {"esperado": "Amortiguadores reventados o bujes de suspension gastados", "aceptables": ["Llantas desbalanceadas o desalineadas"], "dtc": None},
]

def evaluar_con_ground_truth():
    json_path = BASE_DIR / "docs" / "graficas" / "reporte_evaluacion_nuevos_100_casos.json"
    if not json_path.exists():
        print(f"ERROR: No se encuentra {json_path}")
        return
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    res_g1 = data["grupo_1"]["resultados"]
    res_g2 = data["grupo_2"]["resultados"]
    
    todos = []
    
    for i, r in enumerate(res_g1):
        gt = GROUND_TRUTH_G1[i]
        todos.append((r, gt, "GRUPO_1"))
        
    for i, r in enumerate(res_g2):
        gt = GROUND_TRUTH_G2[i]
        todos.append((r, gt, "GRUPO_2"))
        
    correctos = 0
    parciales = 0
    incorrectos = 0
    top3_aciertos = 0
    sistema_aciertos = 0
    
    y_true = []
    y_pred = []
    
    errores_detalle = []
    pares_confusion = defaultdict(int)
    
    for r, gt, grp in todos:
        pred_top1 = r["falla_top1"]
        pred_top2 = r["top2_falla"]
        pred_top3 = r["top3_falla"]
        
        esp = gt["esperado"]
        acep = gt["aceptables"]
        
        y_true.append(esp)
        y_pred.append(pred_top1)
        
        # Acierto en macro-sistema
        sist_true = obtener_sistema(esp)
        sist_pred = obtener_sistema(pred_top1)
        if sist_true == sist_pred:
            sistema_aciertos += 1
            
        # Top-3 Accuracy
        candidatos_top3 = [pred_top1, pred_top2, pred_top3]
        if esp in candidatos_top3 or any(a in candidatos_top3 for a in acep):
            top3_aciertos += 1
            
        # Clasificación estricta
        if pred_top1 == esp:
            correctos += 1
            status = "CORRECTO"
        elif pred_top1 in acep:
            parciales += 1
            status = "PARCIAL (Diferencial válido)"
        else:
            incorrectos += 1
            status = "INCORRECTO"
            pares_confusion[(esp, pred_top1)] += 1
            errores_detalle.append({
                "grupo": grp,
                "idx": r["idx"],
                "caso": r["caso"],
                "esperado": esp,
                "predicho": pred_top1,
                "confianza": r["confianza_top1"],
                "top2": pred_top2,
                "sist_esperado": sist_true,
                "sist_predicho": sist_pred
            })

    total = len(todos)
    acc_top1_estricta = correctos / total
    acc_top1_ampliada = (correctos + parciales) / total
    acc_top3 = top3_aciertos / total
    acc_sistema = sistema_aciertos / total
    
    labels_unicos = sorted(list(set(y_true + y_pred)))
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels_unicos, average="macro", zero_division=0
    )
    
    print("\n" + "="*80)
    print("AUDITORÍA DE BENCHMARK V2 CON GROUND TRUTH (100 CASOS)")
    print("="*80)
    print(f"Total casos evaluados:          {total}")
    print(f"Accuracy Top-1 Estricta:        {acc_top1_estricta*100:5.2f}% ({correctos}/{total})")
    print(f"Accuracy Top-1 con Diferencial: {acc_top1_ampliada*100:5.2f}% ({correctos+parciales}/{total})")
    print(f"Top-3 Accuracy:                 {acc_top3*100:5.2f}% ({top3_aciertos}/{total})")
    print(f"Accuracy de Macro-Sistema:      {acc_sistema*100:5.2f}% ({sistema_aciertos}/{total})")
    print(f"Precision Macro Externa:        {prec*100:5.2f}%")
    print(f"Recall Macro Externo:           {rec*100:5.2f}%")
    print(f"F1-Score Macro Externo:         {f1*100:5.2f}%")
    print("-"*80)
    print(f"Distribución de resultados:")
    print(f"  • Correctos (Top-1 exacto):         {correctos} ({correctos/total*100:.1f}%)")
    print(f"  • Parciales (Top-1 aceptable dif.): {parciales} ({parciales/total*100:.1f}%)")
    print(f"  • Incorrectos:                      {incorrectos} ({incorrectos/total*100:.1f}%)")
    print("="*80 + "\n")
    
    print("PARES DE CONFUSIÓN FRECUENTES (Esperado -> Predicho):")
    sorted_conf = sorted(pares_confusion.items(), key=lambda x: x[1], reverse=True)
    for (esp, pred), cnt in sorted_conf[:15]:
        print(f"  [{cnt}x] Esperado: '{esp[:35]}...' -> Predicho: '{pred[:35]}...'")
        
    print("\nERRORES CLAVE AUDITADOS:")
    for err in errores_detalle[:10]:
        print(f"  • [{err['grupo']} #{err['idx']:02d}] Esperado: {err['esperado']} (Sist: {err['sist_esperado']})")
        print(f"    Predicho: {err['predicho']} (Conf: {err['confianza']*100:.1f}%) (Sist: {err['sist_predicho']})")
        print(f"    Caso: {err['caso'][:70]}...")
        
    # Guardar reporte JSON y Markdown
    reporte_path = BASE_DIR / "docs" / "graficas" / "fase5_benchmark_v2_auditoria.json"
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": total,
            "accuracy_top1_estricta": acc_top1_estricta,
            "accuracy_top1_ampliada": acc_top1_ampliada,
            "top3_accuracy": acc_top3,
            "accuracy_sistema": acc_sistema,
            "precision_macro": prec,
            "recall_macro": rec,
            "f1_macro": f1,
            "conteo": {
                "correctos": correctos,
                "parciales": parciales,
                "incorrectos": incorrectos
            },
            "pares_confusion": [{"esperado": k[0], "predicho": k[1], "conteo": v} for k, v in sorted_conf],
            "errores_detalle": errores_detalle
        }, f, ensure_ascii=False, indent=2)
    print(f"\nReporte JSON guardado en: {reporte_path}")

if __name__ == "__main__":
    evaluar_con_ground_truth()
