# -*- coding: utf-8 -*-
"""Conjunto de evaluación para el experimento RAG-03C (25 consultas técnicas)."""

BENCHMARK_QUERIES = [
    # 1. FRENOS Y METROLOGÍA DE DISCOS (5 consultas)
    {
        "id": "Q_FRENOS_01",
        "categoria": "FRENOS",
        "consulta": "¿Cuál es la tolerancia máxima admisible de alabeo lateral en un disco de freno montado?",
        "tokens_clave": ["alabeo", "disco", "0.10", "freno", "tolerancia"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_FRENOS_02",
        "categoria": "FRENOS",
        "consulta": "¿Qué es la variación de espesor de disco DTV y cuánto es el límite máximo permitido?",
        "tokens_clave": ["dtv", "variacion", "espesor", "0.015", "micras", "judder"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_FRENOS_03",
        "categoria": "FRENOS",
        "consulta": "¿Cuál es el alabeo máximo permitido en el buje de rueda limpio sin disco?",
        "tokens_clave": ["buje", "0.02", "alabeo", "rueda"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_FRENOS_04",
        "categoria": "FRENOS",
        "consulta": "¿Por qué no se debe apretar la rueda con pistola de impacto neumática en discos nuevos?",
        "tokens_clave": ["pistola", "impacto", "par", "apriete", "deformacion", "campana"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_FRENOS_05",
        "categoria": "FRENOS",
        "consulta": "¿Cuáles son los criterios para sustituir un disco por fisuras térmicas y espesor mínimo?",
        "tokens_clave": ["min th", "fisuras", "grietas", "termico", "espesor minimo"],
        "espera_cobertura": True,
    },

    # 2. DIRECCIÓN ASISTIDA C-MDPS HYUNDAI / KIA (5 consultas)
    {
        "id": "Q_DIR_01",
        "categoria": "DIRECCIÓN",
        "consulta": "¿Cómo diagnosticar el ruido de golpeteo clack clack al girar el volante en Hyundai Accent o Elantra?",
        "tokens_clave": ["acoplador", "mdps", "golpeteo", "traqueteo", "columna", "56315-2k000-fff"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_DIR_02",
        "categoria": "DIRECCIÓN",
        "consulta": "¿Cuáles son los pares de apriete de los pernos del motor eléctrico MDPS a la columna de dirección?",
        "tokens_clave": ["apriete", "9.8", "13.7", "pernos", "motor", "mdps"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_DIR_03",
        "categoria": "DIRECCIÓN",
        "consulta": "¿Cómo calibrar y reiniciar a cero el sensor de ángulo de dirección ASP o SAS tras desmontar la columna?",
        "tokens_clave": ["calibracion", "sensor", "angulo", "asp", "sas", "cero", "0.0"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_DIR_04",
        "categoria": "DIRECCIÓN",
        "consulta": "¿Qué significa el código DTC C1102 o C1603 en la dirección asistida de un Kia Rio?",
        "tokens_clave": ["c1102", "c1603", "bateria", "termica", "proteccion", "kia"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_DIR_05",
        "categoria": "DIRECCIÓN",
        "consulta": "¿Cómo diagnosticar el sensor de par torque sensor con códigos DTC C1290 y C1112 en Kia?",
        "tokens_clave": ["c1290", "c1112", "sensor", "par", "torque", "2.5", "5.0"],
        "espera_cobertura": True,
    },

    # 3. REFRIGERACIÓN Y DETECCIÓN QUÍMICA DE CO2 (5 consultas)
    {
        "id": "Q_REFRIG_01",
        "categoria": "REFRIGERACIÓN",
        "consulta": "¿Cómo comprobar si hay fuga de gases de combustión CO2 en el refrigerante usando el probador Laser 5524?",
        "tokens_clave": ["co2", "combustion", "laser", "5524", "radiador", "bromotimol"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_REFRIG_02",
        "categoria": "REFRIGERACIÓN",
        "consulta": "¿Qué cambio de color indica presencia de CO2 en el líquido reactivo en un motor a gasolina?",
        "tokens_clave": ["azul", "amarillo", "viraje", "color", "bromotimol", "gasolina"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_REFRIG_03",
        "categoria": "REFRIGERACIÓN",
        "consulta": "¿A qué color vira el reactivo de CO2 cuando se prueba en un motor diésel?",
        "tokens_clave": ["verde", "azul", "diesel", "reactivo"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_REFRIG_04",
        "categoria": "REFRIGERACIÓN",
        "consulta": "¿Por qué se produce un falso negativo si entra líquido refrigerante al probador de fugas de culata?",
        "tokens_clave": ["falso negativo", "alcalinidad", "contaminacion", "anticongelante", "reactivo"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_REFRIG_05",
        "categoria": "REFRIGERACIÓN",
        "consulta": "¿A qué temperatura debe estar el motor para realizar la prueba química de fugas de combustión?",
        "tokens_clave": ["temperatura", "trabajo", "85", "95", "servicio", "caliente"],
        "espera_cobertura": True,
    },

    # 4. PRESIÓN DINÁMICA E INSTRUMENTAL (5 consultas)
    {
        "id": "Q_INST_01",
        "categoria": "INSTRUMENTAL",
        "consulta": "¿Cuáles son los tres rangos de medición del transductor de presión automotriz Pico WPS500X?",
        "tokens_clave": ["rango", "wps500x", "500 psi", "50 psi", "5 psi", "bar"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_INST_02",
        "categoria": "INSTRUMENTAL",
        "consulta": "¿Qué escala de voltaje y rango se utiliza para medir compresión relativa en cilindro con el WPS500X?",
        "tokens_clave": ["rango 1", "500 psi", "1 v", "100 psi", "compresion", "cilindro"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_INST_03",
        "categoria": "INSTRUMENTAL",
        "consulta": "¿Cuál es la presión máxima que puede soportar el transductor WPS500X y por qué no usar en Common Rail?",
        "tokens_clave": ["500 psi", "maxima", "common rail", "gdi", "alta presion"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_INST_04",
        "categoria": "INSTRUMENTAL",
        "consulta": "¿Cómo analizar la onda de compresión en cilindro de 720 grados para detectar escape obstruido?",
        "tokens_clave": ["720", "torre", "escape", "2 psi", "contrapresion", "catalitico"],
        "espera_cobertura": True,
    },
    {
        "id": "Q_INST_05",
        "categoria": "INSTRUMENTAL",
        "consulta": "¿Cómo detectar un cilindro con válvula de escape quemada mediante pulsos en el tubo de escape?",
        "tokens_clave": ["pulsos", "escape", "rango 3", "valvula", "asiento", "amplitud"],
        "espera_cobertura": True,
    },

    # 5. CASOS SIN COBERTURA / OUT OF DOMAIN (5 consultas para verificar ABSTENCIÓN CORRECTA)
    {
        "id": "Q_OOD_01",
        "categoria": "SIN_COBERTURA",
        "consulta": "¿Cuál es el procedimiento para desactivar el inversor de alto voltaje de 650V en un Tesla Model S?",
        "tokens_clave": ["tesla", "inversor", "650v"],
        "espera_cobertura": False,
    },
    {
        "id": "Q_OOD_02",
        "categoria": "SIN_COBERTURA",
        "consulta": "¿Cómo calibrar los sensores de radar de onda milimétrica de 77 GHz de control crucero adaptativo en un camión Scania?",
        "tokens_clave": ["scania", "radar", "77 ghz"],
        "espera_cobertura": False,
    },
    {
        "id": "Q_OOD_03",
        "categoria": "SIN_COBERTURA",
        "consulta": "¿Cuál es el par de apriete de las bielas forjadas en un motor marino fuera de borda Yamaha V8 350hp?",
        "tokens_clave": ["marino", "yamaha", "bielas"],
        "espera_cobertura": False,
    },
    {
        "id": "Q_OOD_04",
        "categoria": "SIN_COBERTURA",
        "consulta": "¿Cómo purgar el circuito neumático de frenos de aire Wabco EBS en un remolque de tractor articulado?",
        "tokens_clave": ["wabco", "frenos de aire", "remolque"],
        "espera_cobertura": False,
    },
    {
        "id": "Q_OOD_05",
        "categoria": "SIN_COBERTURA",
        "consulta": "¿Cuál es el código de desbloqueo de la radio satelital del sistema SiriusXM en un Ford Mustang Mach-E?",
        "tokens_clave": ["siriusxm", "mach-e", "radio"],
        "espera_cobertura": False,
    },
]
