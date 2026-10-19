"""Generador y validador de los 1,050 escenarios multiturno de calidad conversacional flexible.

Cubre las 7 familias operativas mandatarias para el mecánico:
1. Consultas técnicas y de comprobación sin pérdida de caso (150 escenarios)
2. Descripciones sucesivas de síntomas y condiciones operativas (150 escenarios)
3. Tolerancias metrológicas, especificaciones y pares de apriete (150 escenarios)
4. Declaraciones de reemplazo de componentes e intercambio de piezas (150 escenarios)
5. Informes de comprobaciones físicas: conformidad y descarte (150 escenarios)
6. Corrección de datos de vehículo y descarte de falsos reinicios por analogías (150 escenarios)
7. Solicitud de causas alternativas, hipótesis secundarias y diagnósticos diferenciales (150 escenarios)

Total: 7 * 150 = 1,050 escenarios multiturno completos.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

os.environ.setdefault("DATABASE_ENABLED", "false")
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["GROQ_CHAT_ENABLED"] = "false"



MARCAS_MODELOS = [
    ("Toyota", "Yaris", "2018", "Gasolina"),
    ("Nissan", "Tiida", "2015", "Gasolina"),
    ("Hyundai", "Tucson", "2019", "Gasolina"),
    ("Kia", "Rio", "2017", "Gasolina"),
    ("Volkswagen", "Gol", "2016", "Gasolina"),
    ("Chevrolet", "Sail", "2018", "Gasolina"),
    ("Ford", "Ranger", "2020", "Diésel"),
    ("Toyota", "Hilux", "2019", "Diésel"),
    ("Nissan", "Frontier", "2018", "Diésel"),
    ("Suzuki", "Grand Vitara", "2014", "Gasolina"),
]

def construir_1050_escenarios() -> List[Dict[str, Any]]:
    escenarios: List[Dict[str, Any]] = []

    # 1. Consultas técnicas y de comprobación sin perder contexto (150)
    procedimientos = [
        ("¿Cómo se mide el alabeo de disco con reloj comparador?", ["reloj comparador", "alabeo", "disco"]),
        ("¿Cómo se calibra el cuerpo de aceleración electrónico?", ["cuerpo", "aceleración", "mariposa", "calibración"]),
        ("¿Cómo se prueba el retorno de inyectores con probetas?", ["retorno", "probetas", "inyectores"]),
        ("¿Cómo medir contrapresión en el escape?", ["contrapresión", "manómetro", "escape", "catalizador"]),
        ("¿Cómo comprobar el consumo parásito con multímetro?", ["consumo", "parásito", "fuga", "multímetro"]),
    ]
    for i in range(150):
        marca, mod, anio, comb = MARCAS_MODELOS[i % len(MARCAS_MODELOS)]
        proc_q, keywords = procedimientos[i % len(procedimientos)]
        escenarios.append({
            "id": f"ESC_PROC_{i+1:04d}",
            "familia": "1_CONSULTAS_TECNICAS",
            "turnos": [
                f"{marca} {mod} {anio} {comb} presenta vibración y pérdida de potencia.",
                proc_q,
                "La medición dio dentro de rango especificado, ¿qué más comprobamos?",
            ],
            "vehiculo_esperado": {"marca": marca, "modelo": mod},
            "sintoma_preservado": True,
            "espera_status_turno_2": ["detalle", "solicitud_detalle", "consulta_tecnica"],
        })

    # 2. Síntomas concurrentes y condiciones operativas sucesivas (150)
    condiciones = [
        ("falla en subida pronunciada a 2500 RPM", "subida"),
        ("humo negro al acelerar a fondo", "humo"),
        ("temperatura sube solo en tráfico pesado", "temperatura"),
        ("cascabeleo con el aire acondicionado prendido", "cascabeleo"),
        ("jaloneo intermitente al soltar el embrague", "jaloneo"),
    ]
    for i in range(150):
        marca, mod, anio, comb = MARCAS_MODELOS[i % len(MARCAS_MODELOS)]
        cond_text, cond_kw = condiciones[i % len(condiciones)]
        escenarios.append({
            "id": f"ESC_SINTOMA_{i+1:04d}",
            "familia": "2_SINTOMAS_CONCURRENTES",
            "turnos": [
                f"Tengo un {marca} {mod} {anio} con check engine prendido.",
                f"Además de eso, {cond_text}.",
                "El escáner no arroja códigos grabados en la memoria.",
            ],
            "vehiculo_esperado": {"marca": marca, "modelo": mod},
            "sintoma_preservado": True,
            "espera_status_turno_2": ["diagnosticar", "preguntar", "evidencia_registrada", "conclusion_tecnica"],
        })

    # 3. Tolerancias metrológicas y especificaciones técnicas (150)
    tolerancias = [
        ("¿Cuál es la tolerancia máxima de alabeo de disco de freno?", ["0.05", "0.07", "alabeo", "disco"]),
        ("¿Cuál es el juego axial admisible en el volante de inercia?", ["0.10", "volante", "alabeo"]),
        ("¿Cuál es la contrapresión admisible en el escape?", ["0.8", "1.5", "2.0", "psi", "escape"]),
        ("¿Cuál es el valor máximo de corriente parásita en reposo?", ["0.05", "50 ma", "parásito", "fuga"]),
        ("¿Cuánto es la presión normal en riel de combustible en ralentí?", ["presión", "riel", "bar", "psi"]),
    ]
    for i in range(150):
        marca, mod, anio, comb = MARCAS_MODELOS[i % len(MARCAS_MODELOS)]
        tol_q, tol_kw = tolerancias[i % len(tolerancias)]
        escenarios.append({
            "id": f"ESC_TOLERANCIA_{i+1:04d}",
            "familia": "3_TOLERANCIAS_METROLOGICAS",
            "turnos": [
                f"Estamos revisando un {marca} {mod} {anio}.",
                tol_q,
                "Perfecto, con esa referencia voy a medir con el instrumento.",
            ],
            "vehiculo_esperado": {"marca": marca, "modelo": mod},
            "sintoma_preservado": False,
            "espera_status_turno_2": ["tolerancia_oem", "detalle", "consulta_tecnica", "solicitud_detalle"],
        })

    # 4. Declaración de reemplazo de piezas e intercambio de componentes (150)
    piezas = [
        ("bujías", "Cambié bujías nuevas originales y el problema continúa."),
        ("bobina", "Intercambié bobina 1 con la 2 y la falla no se trasladó."),
        ("filtro de gasolina", "El filtro de combustible es nuevo, recién colocado."),
        ("sensor de oxígeno", "Reemplacé la sonda lambda pero sigue marcando mezcla."),
        ("bomba de agua", "La bomba de agua fue cambiada la semana pasada."),
    ]
    for i in range(150):
        marca, mod, anio, comb = MARCAS_MODELOS[i % len(MARCAS_MODELOS)]
        nombre_pieza, reemplazo_txt = piezas[i % len(piezas)]
        escenarios.append({
            "id": f"ESC_REEMPLAZO_{i+1:04d}",
            "familia": "4_PIEZAS_REEMPLAZADAS",
            "turnos": [
                f"{marca} {mod} {anio} {comb} falla en ralentí inestable.",
                reemplazo_txt,
                "¿Hacia qué otro componente orientamos la revisión?",
            ],
            "vehiculo_esperado": {"marca": marca, "modelo": mod},
            "pieza_reemplazada": nombre_pieza,
            "sintoma_preservado": True,
            "espera_status_turno_2": ["diagnosticar", "evidencia_registrada", "detalle", "conclusion_tecnica"],
        })

    # 5. Comprobaciones físicas: conformidad y descarte (150)
    comprobaciones = [
        ("Medí compresión: 175 psi parejo en los 4 cilindros, mecánica OK.", "compresión"),
        ("Presión de riel marca 3.5 bar estables con manómetro.", "presión"),
        ("Revisé masa y alimentación en el arnés: 12.6V y 0.02V de caída.", "alimentación"),
        ("Hice prueba de fugas con máquina de humo y no hay entradas de aire.", "humo"),
        ("El catalizador no está tapado, la contrapresión marcó 0.3 psi.", "catalizador"),
    ]
    for i in range(150):
        marca, mod, anio, comb = MARCAS_MODELOS[i % len(MARCAS_MODELOS)]
        comp_txt, comp_kw = comprobaciones[i % len(comprobaciones)]
        escenarios.append({
            "id": f"ESC_COMPROB_{i+1:04d}",
            "familia": "5_COMPROBACIONES_FISICAS",
            "turnos": [
                f"{marca} {mod} {anio} pierde fuerza en caliente.",
                comp_txt,
                "Con esta prueba descartada, dime qué inspeccionamos a continuación.",
            ],
            "vehiculo_esperado": {"marca": marca, "modelo": mod},
            "sintoma_preservado": True,
            "espera_status_turno_2": ["diagnosticar", "conclusion_tecnica", "evidencia_registrada"],
        })

    # 6. Corrección de datos de vehículo y descarte de falsos reinicios por analogías (150)
    analogias_o_correcciones = [
        ("En un Nissan Tiida vi algo similar, pero en este auto cascabelea en subida.", "analogia"),
        ("El cliente mencionó que su otro auto es un Ford, pero estamos revisando este.", "analogia"),
        ("No es año 2015, me equivoqué: es 2018.", "correccion_anio"),
        ("Corrijo el modelo, quise decir versión automática con motor 1.6.", "correccion_detalle"),
        ("Como en un Chevrolet Sail que tuve, pero aquí ratea en frío.", "analogia"),
    ]
    for i in range(150):
        marca, mod, anio, comb = MARCAS_MODELOS[i % len(MARCAS_MODELOS)]
        texto_cambio, tipo_acc = analogias_o_correcciones[i % len(analogias_o_correcciones)]
        escenarios.append({
            "id": f"ESC_CORREC_{i+1:04d}",
            "familia": "6_CORRECCION_Y_ANALOGIAS",
            "turnos": [
                f"{marca} {mod} {anio} {comb} no acelera parejo.",
                texto_cambio,
                "¿Qué mediciones recomiendas para este auto?",
            ],
            "vehiculo_esperado": {"marca": marca, "modelo": mod},
            "tipo_accion": tipo_acc,
            "sintoma_preservado": True,
            "espera_status_turno_2": ["diagnosticar", "preguntar", "evidencia_registrada"],
        })

    # 7. Solicitud de causas alternativas e hipótesis secundarias (150)
    preguntas_hipotesis = [
        "Dame causas alternativas si la bobina y bujías ya están descartadas.",
        "¿Qué otra hipótesis técnica podría generar este síntoma?",
        "No creo que sea combustible, qué otros sistemas podrían causar esto.",
        "Plantéame un diagnóstico diferencial con los datos actuales.",
        "Si descartamos inyectores, ¿qué componentes secundarios quedan?",
    ]
    for i in range(150):
        marca, mod, anio, comb = MARCAS_MODELOS[i % len(MARCAS_MODELOS)]
        preg_hip = preguntas_hipotesis[i % len(preguntas_hipotesis)]
        escenarios.append({
            "id": f"ESC_HIPOTESIS_{i+1:04d}",
            "familia": "7_HIPOTESIS_ALTERNATIVAS",
            "turnos": [
                f"{marca} {mod} {anio} tironea en baja velocidad.",
                "Revisé bujías y presión de riel, todo dentro de norma.",
                preg_hip,
            ],
            "vehiculo_esperado": {"marca": marca, "modelo": mod},
            "sintoma_preservado": True,
            "espera_status_turno_3": ["diagnosticar", "diferencial", "detalle"],
        })

    return escenarios
