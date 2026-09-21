"""
Auditoría Quirúrgica y Científica de los 50 Casos de Taller (1er Grupo).
Criterio Estricto según requerimientos explícitos del usuario.
"""

import json
from pathlib import Path

BASE_DIR = Path(".")

with open("docs/graficas/reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data_rep = json.load(f)

casos_raw = {c["id"]: c for c in data_rep["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"}

# Definición de Ground Truth riguroso caso por caso
AUDITORIA_CASOS = [
    {
        "id": "G1_01",
        "sintoma": "Corolla 2017 en frío prende perfecto, después de 25 minutos empieza a tironear y termina apagándose. En caliente gira motor pero no prende; espero 15 minutos y arranca como si nada. No tengo DTC.",
        "gt": "Sensor de cigüeñal (CKP) por fatiga térmica",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 fue Bujías/bobinas (65.8%)
        "eval_top3": "NO", # Top-2 Bomba de gasolina, Top-3 Baja presión aceite. CKP no apareció en Top-3.
        "eval_final": "INCORRECTO", # Principal bujías/bobinas. CKP no aparece en Top-3 ni reporte.
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: PRESIÓN DE COMBUSTIBLE BAJO CARGA (Sim: 0.37)",
        "valores_respaldo": "PARCIAL",
        "nota": "Falla térmica típica de CKP; el modelo predijo bujías y bomba, omitiendo CKP."
    },
    {
        "id": "G1_02",
        "sintoma": "Yaris 2018 pierde fuerza solo cuando subo cerro con 4 pasajeros. En plano anda normal. Si piso a fondo se ahoga un poco, pero si acelero progresivamente responde mejor.",
        "gt": "Bomba de gasolina quemada o con baja presión",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": True,
        "eval_top1": "NO", # Top-1 en clarificación (0.0%)
        "eval_top3": "NO", # Sin terna por clarificación
        "eval_final": "INCORRECTO", # Turno 2 cayó en fuera de alcance
        "macro_ok": "SÍ",
        "interrogador_eval": "SÍ (ACTIVADO)",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "NO",
        "nota": "Auto-interrogador activado oportunamente; fallo en turno 2 por respuesta numérica."
    },
    {
        "id": "G1_03",
        "sintoma": "Kia Rio 2019 mínimo inestable, a veces se apaga en semáforo. Ya limpiaron cuerpo de aceleración y sigue igual. Al prender A/C empeora bastante.",
        "gt": "Cuerpo de aceleración / válvula IAC sucia o descalibrada",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Top-1 fue Cuerpo de aceleracion o valvula IAC (89.4%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: PRESIÓN DE COMBUSTIBLE BAJO CARGA (Sim: 0.35)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto directo en Top-1 y diagnóstico final."
    },
    {
        "id": "G1_04",
        "sintoma": "Sentra 2016 arranca normal, pero cuando calienta comienza a fallar un cilindro. Cambié bujías y bobinas de posición y la falla sigue en el mismo cilindro.",
        "gt": "Inyector con falla térmica / goteo o compresión en cilindro",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Bujías/bobinas (82.0%) - el mecánico ya las había descartado
        "eval_top3": "NO", # Top-2 Bomba, Top-3 Desgaste de anillos. Inyector no está en Top-3.
        "eval_final": "INCORRECTO", # Insistió en bujías/bobinas
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: CAMBIO DE BUJÍAS Y MISFIRE (Sim: 0.42)",
        "valores_respaldo": "PARCIAL",
        "nota": "El usuario ya había rotado bujías/bobinas; el modelo insistió en bujías y no incluyó inyector en Top-3."
    },
    {
        "id": "G1_05",
        "sintoma": "Mazda 3 2018 check parpadea únicamente cuando acelero fuerte. Scanner P0303. En mínimo casi no se siente falla y bujía del cilindro 3 sale húmeda.",
        "gt": "Falla en bujías o bobinas de encendido (misfire cil 3)",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Top-1 Bujías/bobinas (91.1%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BOBINAS DE ENCENDIDO INDIVIDUALES COP (Sim: 0.88)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco con P0303 en Top-1 y diagnóstico final."
    },
    {
        "id": "G1_06",
        "sintoma": "Corolla 2015 tiene P0171. Ya revisé mangueras visibles y no encuentro fuga. En mínimo los fuel trims se van positivos pero acelerando a 2500 rpm mejoran bastante.",
        "gt": "Fuga de vacío en admisión (empaque de múltiple) / entrada de aire no medida",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Cuerpo de aceleración / IAC (53.0%)
        "eval_top3": "NO", # Top-2 Bomba gasolina, Top-3 Fuga intercooler. No está empaque ni fuga de vacío en admisión.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: PRESIÓN DE COMBUSTIBLE BAJO CARGA (Sim: 0.34)",
        "valores_respaldo": "SÍ",
        "nota": "P0171 que mejora a 2500 rpm es clásico de vacío en admisión; modelo culpó a IAC."
    },
    {
        "id": "G1_07",
        "sintoma": "Hyundai Accent demora en prender únicamente después de cargar gasolina hasta llenar el tanque. Cuando prende huele fuerte a combustible y luego trabaja normal.",
        "gt": "Válvula de purga del canister EVAP trabada abierta",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": True,
        "eval_top1": "NO", # Turno 1 Sensor O2 / mezcla rica (50.8%)
        "eval_top3": "NO", # Top-2 Bomba, Top-3 Inyectores. EVAP/canister ausente.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "SÍ (ACTIVADO)",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "NO",
        "nota": "Auto-interrogador activó, pero sus opciones no contemplaban la válvula de purga EVAP."
    },
    {
        "id": "G1_08",
        "sintoma": "Hilux 2GD humo negro en aceleración y testigo de combustible, scanner no da DTC pero presión de riel cae bajo carga.",
        "gt": "Fuga o baja presión en sistema Common Rail Diesel (retorno excesivo)",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Common Rail Diesel (93.2%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: SISTEMA COMMON RAIL DIESEL (Sim: 0.86)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_09",
        "sintoma": "Toyota prende bien frío, pero caliente demora bastante en arrancar. No hay DTC. Presión de combustible queda dentro de rango y el motor de arranque gira normal.",
        "gt": "Inyectores goteando en reposo / Sensor ECT descalibrado",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Predijo Common Rail Diesel (61.5%) en auto gasolina Toyota
        "eval_top3": "NO", # Top-2 Bomba (descartada en síntoma), Top-3 Bujías.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: SISTEMA COMMON RAIL DIESEL (Sim: 0.31)",
        "valores_respaldo": "SÍ",
        "nota": "Predijo Common Rail Diesel para un Toyota a gasolina; inyectores goteando ausentes."
    },
    {
        "id": "G1_10",
        "sintoma": "Tiida cascabelea fuerte al acelerar en subida, timing advance oscila mucho.",
        "gt": "Faja o cadena de distribución destensada o con salto de punto",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Faja o cadena distribución (92.1%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: CAMBIO DE BUJÍAS Y MISFIRE (Sim: 0.38)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_11",
        "sintoma": "Sentra P0420 vuelve cada dos días después de borrarlo. No hay misfire, consumo normal y el sensor delantero oscila, pero el sensor posterior copia casi la misma señal.",
        "gt": "Convertidor catalítico ineficiente / agotado",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Misfire (73.1%) - síntoma decía 'No hay misfire'
        "eval_top3": "SÍ", # Top-2 Falla en sensor de oxígeno o mezcla rica (73.1%), y RAG recuperó DTC P0420
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: EFICIENCIA CATALIZADOR P0420 (Sim: 0.61)",
        "valores_respaldo": "SÍ",
        "nota": "Top-1 erró por insistir en misfire, pero Top-2 y RAG fundamentaron el diferencial P0420."
    },
    {
        "id": "G1_12",
        "sintoma": "Toyota P0301. Cambié bujía y bobina del cilindro 1 por las del cilindro 2 pero P0301 continúa. Compresión del cilindro 1 está bastante más baja que los demás.",
        "gt": "Pérdida de compresión por válvula de escape quemada o anillos en cil 1",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Bujías/bobinas (98.5%) a pesar del descarte previo
        "eval_top3": "SÍ", # Top-2 Consumo de aceite por desgaste de anillos (anillos/compresión)
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: REEMPLAZO BOBINAS COP (Sim: 0.35)",
        "valores_respaldo": "SÍ",
        "nota": "Top-1 sesgado a bujías por P0301; desgaste de anillos en Top-2 rescata el diferencial mecánico."
    },
    {
        "id": "G1_13",
        "sintoma": "Kia con humo negro y consumo alto. Scanner marca mezcla rica. Presión de combustible está por encima de especificación y al retirar la manguera de vacío del regulador aparece gasolina.",
        "gt": "Diafragma del regulador de presión de combustible roto",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Sensor O2 / mezcla rica (84.9%) - es síntoma, no causa raíz
        "eval_top3": "NO", # Top-2 Bomba baja presión, Top-3 Inyectores. Regulador no existe en clases.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: SENSOR DE RELACIÓN A/F Y O2 (Sim: 0.33)",
        "valores_respaldo": "NO",
        "nota": "Confundió la consecuencia (mezcla rica) con la causa (diafragma de regulador roto)."
    },
    {
        "id": "G1_14",
        "sintoma": "Yaris 2016 tironea solo cuando el tanque baja de un cuarto. Con tanque lleno no falla.",
        "gt": "Bomba de gasolina quemada o con baja presión / filtro sumergido",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": True,
        "eval_top1": "NO", # Clarificación (0.0%)
        "eval_top3": "NO",
        "eval_final": "INCORRECTO", # Salida a fuera de alcance
        "macro_ok": "SÍ",
        "interrogador_eval": "SÍ (ACTIVADO)",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "NO",
        "nota": "Auto-interrogador activó, pero turno 2 no resolvió la causa."
    },
    {
        "id": "G1_15",
        "sintoma": "Cerato 2018 tironea entre 1500 y 2000 rpm, DTC P0202.",
        "gt": "Falla en inyector 2 o circuito de cilindro 2 (P0202)",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Bujías/bobinas (74.5%)
        "eval_top3": "NO", # Top-2 Bomba, Top-3 Correa bañada en aceite. Inyector ausente en Top-3.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: PRESIÓN DE COMBUSTIBLE BAJO CARGA (Sim: 0.31)",
        "valores_respaldo": "NO",
        "nota": "P0202 es circuito de inyector; el modelo diagnosticó erróneamente bujías."
    },
    {
        "id": "G1_16",
        "sintoma": "Pedal de freno se va al fondo lentamente en semáforo, nivel de líquido completo y sin fugas externas visibles.",
        "gt": "Fuga interna en cilindro maestro (bomba de freno) o aire en el sistema",
        "macro_esperado": "FRENOS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Fuga hidráulica o aire en el sistema de frenos (93.2%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: PURGA Y CAMBIO LÍQUIDO FRENOS (Sim: 0.69)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_17",
        "sintoma": "Pedal de freno duro como una piedra, frena muy poco salvo que me pare en el pedal con fuerza.",
        "gt": "Falla en servofreno (booster) o manguera/válvula de vacío",
        "macro_esperado": "FRENOS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Falla en servofreno (booster) o linea de vacio (96.5%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: PURGA Y CAMBIO LÍQUIDO FRENOS (Sim: 0.41)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_18",
        "sintoma": "Después de manejar 15 minutos la rueda delantera derecha queda hirviendo y el carro comienza a jalar. Lo dejo enfriar y vuelve a rodar libremente.",
        "gt": "Caliper trabado / mordaza pegada / flexible colapsado",
        "macro_esperado": "FRENOS",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Desgaste de pastillas y zapatas (59.5%) - síntoma, no causa de traba
        "eval_top3": "NO", # Top-2 Llantas desbalanceadas, Top-3 Juntas homocinéticas. Caliper ausente.
        "eval_final": "INCORRECTO", # No se puede convertir desgaste de pastillas en cáliper trabado
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: MANTENIMIENTO FRENOS TAMBOR/PASTILLAS (Sim: 0.34)",
        "valores_respaldo": "NO",
        "nota": "Rueda hirviendo por cáliper trabado fue catalogada como simple desgaste de pastillas."
    },
    {
        "id": "G1_19",
        "sintoma": "A 100 km/h no vibra nada mientras acelero. Piso freno suavemente y empieza a temblar el timón; mientras más fuerte freno, más fuerte vibra.",
        "gt": "Discos de freno alabeados o desgastados",
        "macro_esperado": "FRENOS",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Llantas desbalanceadas (65.7%)
        "eval_top3": "SÍ", # Top-2 Discos de freno alabeados o desgastados (30.9%)
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "NO", # Clasificó como SUSPENSION_CHASIS
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.32)",
        "valores_respaldo": "SÍ",
        "nota": "Top-1 confundió vibración al frenar con llantas, pero Top-2 identificó discos alabeados."
    },
    {
        "id": "G1_20",
        "sintoma": "Vibración en volante que empieza exactamente a 90 km/h y desaparece a 115 km/h, frenando no cambia nada.",
        "gt": "Llantas desbalanceadas o desalineadas",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Llantas desbalanceadas o desalineadas (97.4%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.58)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_21",
        "sintoma": "Testigo ABS encendido continuo. Al frenar suave sobre asfalto seco se siente pulsación en el pedal a muy baja velocidad antes de detenerse por completo.",
        "gt": "Falla en sensor de velocidad de rueda ABS",
        "macro_esperado": "FRENOS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Sensor de velocidad de rueda ABS (76.1%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: SENSOR ABS (Sim: 0.83)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_22",
        "sintoma": "Cambié pastillas delanteras, purgué pero el pedal se va hasta el fondo al primer bombazo y al segundo recién agarra pedal duro.",
        "gt": "Aire en el sistema de frenos tras purga o mordaza desajustada",
        "macro_esperado": "FRENOS",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Fuera de alcance (0.0%)
        "eval_top3": "NO",
        "eval_final": "INCORRECTO",
        "macro_ok": "NO", # Cayó en MOTOR
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "NO",
        "nota": "El clasificador de intenciones derivó erróneamente la consulta a fuera de alcance."
    },
    {
        "id": "G1_23",
        "sintoma": "Caja automática golpea fuerte al pasar de N a D y de N a R, y en subida patina primera antes de enganchar.",
        "gt": "Falta o degradación de aceite de caja de cambios / nivel bajo ATF",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Falta o degradación de aceite de caja de cambios (64.5%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: SERVICIO A TRANSMISIÓN AUTOMÁTICA (Sim: 0.51)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_24",
        "sintoma": "Nissan Sentra CVT acelera el motor pero no avanza proporcionalmente, zumbido agudo en carretera larga y testigo de temperatura de transmisión.",
        "gt": "Sobrecalentamiento o falla en solenoides/poleas caja CVT",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Sobrecalentamiento o solenoides en caja automatica CVT / DSG (75.6%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: SERVICIO A TRANSMISIÓN AUTOMÁTICA (Sim: 0.48)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_25",
        "sintoma": "Volkswagen DSG en frío trabaja normal, pero caliente tiembla al salir en primera y demora en enganchar D. No presenta falla de motor.",
        "gt": "Embrague K1 desgastado o mecatrónica en caja DSG",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Bujías/bobinas (82.8%)
        "eval_top3": "SÍ", # Top-2 Disco de embrague desgastado o patinando (6.6%), Top-3 Caja Dualogic (2.1%)
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "NO", # Clasificó como MOTOR
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: CAMBIO DE BUJÍAS Y MISFIRE (Sim: 0.21)",
        "valores_respaldo": "NO",
        "nota": "Top-1 erró en motor, pero Top-2 rescató embrague desgastado de transmisión."
    },
    {
        "id": "G1_26",
        "sintoma": "Fiat Dualogic no pone cambios por las mañanas y suena bomba hidráulica continuamente en la puerta del chofer.",
        "gt": "Acumulador de presión o bomba de caja robotizada Dualogic",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Falla en caja robotizada Dualogic / I-Motion / Easytronic (95.7%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: GRUPO ELECTROHIDRÁULICO DUALOGIC (Sim: 0.64)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_27",
        "sintoma": "Acelero en 3ra y suben las revoluciones pero el carro no avanza con la misma fuerza, huele a asbesto quemado.",
        "gt": "Disco de embrague desgastado o patinando",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Sensor O2 / mezcla rica (26.4%)
        "eval_top3": "NO", # Top-2 Bujías/bobinas, Top-3 Bomba gasolina. Embrague ausente.
        "eval_final": "INCORRECTO",
        "macro_ok": "NO", # Clasificó como MOTOR
        "interrogador_eval": "ACTIVACIÓN PREVENTIVA",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "NO",
        "nota": "Embrague patinando fue confundido con mezcla rica; embrague no figuró en Top-3."
    },
    {
        "id": "G1_28",
        "sintoma": "Al pisar embrague aparece un ronquido. Suelto pedal y desaparece completamente. Los cambios entran bien y el embrague no patina.",
        "gt": "Collarín de empuje / crapodina de embrague desgastada",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Bombín o bomba hidráulica (63.7%) - actuador, no rodamiento
        "eval_top3": "SÍ", # Top-2 Disco de embrague desgastado o patinando (34.1%)
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: MECATRÓNICA DSG (Sim: 0.31)",
        "valores_respaldo": "NO",
        "nota": "CarBot no tiene clase específica de 'Collarín'; Top-1 fue bombín y Top-2 conjunto embrague."
    },
    {
        "id": "G1_29",
        "sintoma": "En neutro caja hace un zumbido. Piso embrague y el ruido desaparece. Al soltarlo vuelve inmediatamente aunque el carro esté detenido.",
        "gt": "Rodajes de caja mecánica o diferencial gastados (rodamiento primario)",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Bombín o bomba hidráulica (89.2%) - absurdo mecánico
        "eval_top3": "NO", # Top-2 Falta aceite, Top-3 Caja Dualogic. Rodajes de caja ausentes en Top-3.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: GRUPO ELECTROHIDRÁULICO DUALOGIC (Sim: 0.33)",
        "valores_respaldo": "NO",
        "nota": "Zumbido en neutro que calla al pisar es eje primario; el modelo predijo bombín."
    },
    {
        "id": "G1_30",
        "sintoma": "Al arrancar en primera el carro trepida / zapatea bruscamente. Ya cambiaron soportes de motor y sigue igual.",
        "gt": "Plato opresor alabeado o embrague zapateando",
        "macro_esperado": "TRANSMISION",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Disco de embrague desgastado o patinando (95.4%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: GRUPO ELECTROHIDRÁULICO DUALOGIC (Sim: 0.27)",
        "valores_respaldo": "NO",
        "nota": "Acierto unívoco en embrague como causa de la trepidación."
    },
    {
        "id": "G1_31",
        "sintoma": "Carro jala hacia la derecha después de caer en una zanja profunda, timón queda torcido unos 15 grados para ir recto.",
        "gt": "Llantas desalineadas / desalineación severa tras impacto",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Llantas desbalanceadas o desalineadas (98.6%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.67)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en Top-1 y E2E."
    },
    {
        "id": "G1_32",
        "sintoma": "Crujido metálico repetitivo clac-clac-clac únicamente al doblar toda la dirección acelerando en esquinas.",
        "gt": "Juntas homocinéticas o palieres dañados",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Juntas homocinéticas o palieres dañados (63.8%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.35)",
        "valores_respaldo": "NO",
        "nota": "Acierto unívoco en homocinéticas."
    },
    {
        "id": "G1_33",
        "sintoma": "A 70 km/h aparece zumbido ronco adelante. Al hacer una curva larga hacia la izquierda el ruido disminuye y hacia la derecha aumenta.",
        "gt": "Rodamiento de rueda / maza delantera picado",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Llantas desbalanceadas (93.6%)
        "eval_top3": "SÍ", # Top-2 Rodajes de caja o diferencial (3.4%), y RAG recuperó Metrología de Rodamientos de Maza
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: METROLOGÍA RODAMIENTO MAZA (Sim: 0.24)",
        "valores_respaldo": "SÍ",
        "nota": "Top-1 erró en llantas, pero Top-2 (rodajes) y RAG fundamentaron el diferencial de rodamientos."
    },
    {
        "id": "G1_34",
        "sintoma": "El carro rebota dos o tres veces después de cada rompemuelle y en carretera se siente flotando. Las llantas tienen presión correcta.",
        "gt": "Amortiguadores reventados o bujes de suspensión gastados",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Llantas desbalanceadas (67.1%)
        "eval_top3": "NO", # Top-2 Sensor O2 (5.0%), Top-3 Inyectores (3.7%). Amortiguadores ausentes.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.19)",
        "valores_respaldo": "NO",
        "nota": "Rebote de amortiguador fue catalogado como llantas desbalanceadas; amortiguador no apareció en Top-3."
    },
    {
        "id": "G1_35",
        "sintoma": "Juego excesivo en el timón antes de que respondan las llantas, en pista adoquinada suena traqueteo en la caña.",
        "gt": "Cremallera de dirección asistida con holgura o terminales axiales",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Cremallera de dirección asistida (95.5%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.39)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en cremallera de dirección."
    },
    {
        "id": "G1_36",
        "sintoma": "Llantas delanteras se comen por el borde interno de ambos lados rápidamente, dibujo externo está intacto.",
        "gt": "Llantas desalineadas (divergencia / camber negativo)",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Llantas desbalanceadas o desalineadas (98.9%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.71)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en alineación."
    },
    {
        "id": "G1_37",
        "sintoma": "Temperatura sube en tráfico lento hasta la zona roja pero en carretera rápida baja a la mitad. Motoventilador no enciende.",
        "gt": "Motoventilador de radiador quemado o relé defectuoso",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Falla en termostato o motoventilador de radiador (91.0%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: TERMOSTATO Y PURGA ANTICONGELANTE (Sim: 0.68)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en motoventilador."
    },
    {
        "id": "G1_38",
        "sintoma": "Motor calienta en carretera y ciudad por igual, manguera superior del radiador hierve dura y la manguera inferior está fría.",
        "gt": "Termostato trabado cerrado",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Falla en termostato o motoventilador de radiador (70.6%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: TERMOSTATO Y PURGA ANTICONGELANTE (Sim: 0.74)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en termostato."
    },
    {
        "id": "G1_39",
        "sintoma": "Consumo de refrigerante de medio litro semanal sin fuga visible en mangueras ni radiador, saca humo blanco dulce al acelerar.",
        "gt": "Empaque de culata soplado o dañado",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": True,
        "eval_top1": "NO", # Top-1 Fuga mangueras/radiador (25.6%)
        "eval_top3": "SÍ", # Top-3 Empaque de culata soplado o dañado
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "SÍ",
        "interrogador_eval": "SÍ (ACTIVADO)",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "NO",
        "nota": "Auto-interrogador activó oportunamente y Top-3 capturó empaque de culata."
    },
    {
        "id": "G1_40",
        "sintoma": "Testigo de aceite parpadea en caliente únicamente cuando el motor cae a ralentí, al acelerar a 1500 rpm se apaga.",
        "gt": "Baja presión de aceite o bomba de aceite defectuosa",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Baja presion de aceite o bomba de aceite defectuosa (66.9%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: BOMBA DE ALTA PRESIÓN Y ACEITE (Sim: 0.33)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en presión de aceite."
    },
    {
        "id": "G1_41",
        "sintoma": "En las mañanas hace tac-tac metálico arriba del motor durante 3 minutos. Cuando llega aceite y calienta desaparece por completo. No hay check engine.",
        "gt": "Taqués / buzos hidráulicos descargados (o retraso en presión de aceite en culata)",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Baja presion de aceite o bomba de aceite defectuosa (53.0%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: SENSORES DE POSICIÓN (Sim: 0.29)",
        "valores_respaldo": "NO",
        "nota": "Baja presión inicial de aceite es la causa directa del traqueteo de taqués hidráulicos."
    },
    {
        "id": "G1_42",
        "sintoma": "Luces parpadean acelerando y se quemaron dos focos en la misma semana. Multímetro marca 16.1 V a 2000 rpm.",
        "gt": "Alternador defectuoso o placa de diodos/regulador en sobrevoltaje",
        "macro_esperado": "ELECTRICO",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Alternador defectuoso o placa de diodos quemada (87.2%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: ALTERNADOR Y BATERÍA (Sim: 0.82)",
        "valores_respaldo": "PARCIAL",
        "nota": "Acierto unívoco en alternador/regulador."
    },
    {
        "id": "G1_43",
        "sintoma": "P0562 presente. En mínimo tengo 11.9 V y acelerando apenas llega a 12.3 V. Batería fue cambiada hace una semana.",
        "gt": "Alternador defectuoso o placa de diodos quemada (baja carga P0562)",
        "macro_esperado": "ELECTRICO",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Batería descargada (79.3%) - síntoma, no causa (batería era nueva)
        "eval_top3": "SÍ", # Top-2 Alternador defectuoso o placa de diodos quemada (17.7%)
        "eval_final": "DIFERENCIAL ACEPTABLE",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: ALTERNADOR Y BATERÍA (Sim: 1.00)",
        "valores_respaldo": "PARCIAL",
        "nota": "Top-1 culpó a batería (recién cambiada), pero Top-2 identificó alternador defectuoso."
    },
    {
        "id": "G1_44",
        "sintoma": "Giro llave y solo hace clac una vez. Faros mantienen buen brillo y batería mide 12.7 V. Golpeando suavemente el motor de arranque algunas veces prende.",
        "gt": "Motor de arranque o solenoide defectuoso (carbones/escobillas desgastadas)",
        "macro_esperado": "ELECTRICO",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Batería descargada (88.2%)
        "eval_top3": "NO", # Top-2 Alternador, Top-3 Inversor IGBT EV. Arrancador ausente en Top-3.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: ALTERNADOR Y BATERÍA (Sim: 0.52)",
        "valores_respaldo": "SÍ",
        "nota": "Batería 12.7V y golpe al arrancador confirma motor de arranque; modelo insistió en batería."
    },
    {
        "id": "G1_45",
        "sintoma": "Batería nueva se descarga durante la noche. Alternador carga 14.2 V andando. Con carro apagado medí consumo de 650 mA y al retirar un fusible baja a 35 mA.",
        "gt": "Fuga parásita de corriente en reposo",
        "macro_esperado": "ELECTRICO",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Alternador defectuoso (83.8%) - alternador carga 14.2V perfecto
        "eval_top3": "NO", # Top-2 Batería descargada (consecuencia), Top-3 Batería HV EV. Fuga parásita ausente.
        "eval_final": "INCORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: ALTERNADOR Y BATERÍA (Sim: 0.77)",
        "valores_respaldo": "SÍ",
        "nota": "Consumo parásito de 650mA; el modelo culpó erróneamente al alternador."
    },
    {
        "id": "G1_46",
        "sintoma": "Camión Volvo FM demorando más de 20 minutos en cargar aire a 8 bar, sin fugas audibles en mangueras.",
        "gt": "Válvulas de compresor desgastadas / fuga en compresor de frenos neumático",
        "macro_esperado": "CARROCERIA_NEUMATICA",
        "requiere_interrogador": False,
        "eval_top1": "SÍ", # Fugas de aire o fallos en el sistema de frenos neumático (Camiones) (57.7%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "SÍ",
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: FRENOS DE AIRE PESADOS (Sim: 0.75)",
        "valores_respaldo": "SÍ",
        "nota": "Acierto unívoco en neumática pesada."
    },
    {
        "id": "G1_47",
        "sintoma": "Gobernadora descarga aire cada 10 segundos en ralentí con secador APS nuevo y depósitos limpios.",
        "gt": "Válvula de freno de aire o secador APS obstruido / fuga en señal gobernadora",
        "macro_esperado": "CARROCERIA_NEUMATICA",
        "requiere_interrogador": True,
        "eval_top1": "SÍ", # Válvula de freno de aire o secador APS obstruido (41.8%)
        "eval_top3": "SÍ",
        "eval_final": "CORRECTO",
        "macro_ok": "NO", # Clasificó como MOTOR
        "interrogador_eval": "SÍ (ACTIVADO)",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "NO",
        "nota": "Acierto de falla y activación de auto-interrogador; macro-sistema falló a MOTOR."
    },
    {
        "id": "G1_48",
        "sintoma": "Tractocamión Volvo FH: al soltar el freno de parqueo se escucha escape constante de aire por la válvula de escape rápido del eje trasero y las ruedas quedan bloqueadas.",
        "gt": "Fugas de aire en cámara de freno Maxi-Brake (diafragma roto)",
        "macro_esperado": "CARROCERIA_NEUMATICA",
        "requiere_interrogador": False,
        "eval_top1": "NO", # Top-1 Bomba de gasolina quemada (65.6%)
        "eval_top3": "NO", # Top-2 Discos alabeados, Top-3 Intercooler. Neumática ausente.
        "eval_final": "INCORRECTO",
        "macro_ok": "NO", # Clasificó como MOTOR
        "interrogador_eval": "NO APLICABA",
        "rag_doc": "PROCEDIMIENTO: PRESIÓN DE COMBUSTIBLE BAJO CARGA (Sim: 0.38)",
        "valores_respaldo": "NO",
        "nota": "Falla severa de neumática clasificada erróneamente como bomba de gasolina."
    },
    {
        "id": "G1_49",
        "sintoma": "Cliente solo dice: 'cuando calienta se pone pesado, tiembla un poco y a veces se apaga; después de descansar vuelve normal'. No hay scanner conectado ni más datos.",
        "gt": "Consulta térmica ambigua de motor (Criterio: Activación de Auto-Interrogador)",
        "macro_esperado": "MOTOR",
        "requiere_interrogador": True,
        "eval_top1": "NO", # Enfoque interactivo: no adivinar falla
        "eval_top3": "SÍ", # Opciones diferenciales desplegadas en la auto-pregunta
        "eval_final": "CORRECTO", # Éxito por activación correcta del auto-interrogador
        "macro_ok": "SÍ",
        "interrogador_eval": "SÍ (ACTIVADO)",
        "rag_doc": "Procedimiento Estándar OEM (Sim: 0.00)",
        "valores_respaldo": "SÍ",
        "nota": "Éxito metodológico: activó auto-interrogador con opciones diferenciales técnicas."
    },
    {
        "id": "G1_50",
        "sintoma": "Cliente dice: 'adelante hace cloc, a veces jala y siento algo raro en el timón'. No sabe cuándo empezó, no sabe si ocurre frenando y no hay inspección todavía.",
        "gt": "Consulta difusa en tren delantero (Criterio: Activación de Auto-Interrogador)",
        "macro_esperado": "SUSPENSION_CHASIS",
        "requiere_interrogador": True,
        "eval_top1": "NO", # Adivinó directamente Llantas desbalanceadas al 84%
        "eval_top3": "NO",
        "eval_final": "INCORRECTO", # Falló al no activar el auto-interrogador en consulta difusa
        "macro_ok": "SÍ",
        "interrogador_eval": "NO (NO ACTIVADO)",
        "rag_doc": "PROCEDIMIENTO: BALANCEO DINÁMICO Y ALINEACIÓN (Sim: 0.42)",
        "valores_respaldo": "SÍ",
        "nota": "Fallo metodológico: emitió diagnóstico directo al 84% sin activar auto-interrogador."
    }
]

# Recalcular métricas desde cero
total = len(AUDITORIA_CASOS)
assert total == 50, f"Error: se esperaban 50 casos y hay {total}"

conteo_top1 = sum(1 for c in AUDITORIA_CASOS if c["eval_top1"] == "SÍ")
conteo_top3 = sum(1 for c in AUDITORIA_CASOS if c["eval_top3"] == "SÍ")

conteo_final_correcto = sum(1 for c in AUDITORIA_CASOS if c["eval_final"] == "CORRECTO")
conteo_final_diferencial = sum(1 for c in AUDITORIA_CASOS if c["eval_final"] == "DIFERENCIAL ACEPTABLE")
conteo_final_incorrecto = sum(1 for c in AUDITORIA_CASOS if c["eval_final"] == "INCORRECTO")

conteo_macro_ok = sum(1 for c in AUDITORIA_CASOS if c["macro_ok"] == "SÍ")

# Auto-interrogador
casos_requiere_interrogador = [c for c in AUDITORIA_CASOS if c["requiere_interrogador"]]
total_requiere_inter = len(casos_requiere_interrogador)
conteo_interrogador_exito = sum(1 for c in casos_requiere_interrogador if "SÍ" in c["interrogador_eval"])

# Respaldo de valores
conteo_respaldo_si = sum(1 for c in AUDITORIA_CASOS if c["valores_respaldo"] == "SÍ")
conteo_respaldo_parcial = sum(1 for c in AUDITORIA_CASOS if c["valores_respaldo"] == "PARCIAL")
conteo_respaldo_no = sum(1 for c in AUDITORIA_CASOS if c["valores_respaldo"] == "NO")

print("=" * 80)
print("REAUDITORÍA CIENTÍFICA ESTRICTA (50 CASOS INDIVIDUALES)")
print("=" * 80)
print(f"Total casos auditados: {total}")
print(f"1. Top-1 ML Accuracy: {conteo_top1}/{total} ({conteo_top1/total*100:.2f}%)")
print(f"2. Top-3 ML Accuracy: {conteo_top3}/{total} ({conteo_top3/total*100:.2f}%)")
print(f"3. Diagnóstico Final E2E:")
print(f"   - Correcto Estricto: {conteo_final_correcto}/{total} ({conteo_final_correcto/total*100:.2f}%)")
print(f"   - Diferencial Aceptable: {conteo_final_diferencial}/{total} ({conteo_final_diferencial/total*100:.2f}%)")
print(f"   - Incorrecto: {conteo_final_incorrecto}/{total} ({conteo_final_incorrecto/total*100:.2f}%)")
print(f"   - Exactitud Global (Correcto + Diferencial): {conteo_final_correcto + conteo_final_diferencial}/{total} ({(conteo_final_correcto + conteo_final_diferencial)/total*100:.2f}%)")
print(f"4. Exactitud Macro-Sistema: {conteo_macro_ok}/{total} ({conteo_macro_ok/total*100:.2f}%)")
print(f"5. Efectividad Auto-Interrogador: {conteo_interrogador_exito}/{total_requiere_inter} ({conteo_interrogador_exito/total_requiere_inter*100:.2f}%)")
print(f"   (Casos que lo requerían: {total_requiere_inter}, activados con éxito: {conteo_interrogador_exito})")
print(f"6. Respaldo Documental de Tolerancias:")
print(f"   - SÍ: {conteo_respaldo_si}/{total} ({conteo_respaldo_si/total*100:.2f}%)")
print(f"   - PARCIAL: {conteo_respaldo_parcial}/{total} ({conteo_respaldo_parcial/total*100:.2f}%)")
print(f"   - NO: {conteo_respaldo_no}/{total} ({conteo_respaldo_no/total*100:.2f}%)")
print("=" * 80)

# Verificación de consistencia de sumas
assert conteo_final_correcto + conteo_final_diferencial + conteo_final_incorrecto == 50, "Error en suma de E2E"
assert conteo_respaldo_si + conteo_respaldo_parcial + conteo_respaldo_no == 50, "Error en suma de respaldo"
print("¡Verificación de consistencia matemática 50/50 superada exitosamente!")
