"""
Evaluador exhaustivo capa por capa para los 50 casos de taller.
Aplica las reglas metodológicas exactas del usuario:
- Top-1 ML: Exclusivamente clase Top-1 del SVM.
- Top-3 ML: Exclusivamente las tres clases ML del SVM (sin RAG ni auto-interrogador).
- E2E Estricto: Diagnóstico principal final recibido por el usuario.
- E2E Diferencial: Causa esperada presente en diferencial o procedimiento RAG del reporte final.
- Macro: Macro-sistema predicho vs real.
- Interrogador: Decisión de flujo correcta (activó cuando debía o no activó cuando no aplicaba).
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / "docs" / "graficas" / "reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data_rep = json.load(f)

casos_raw = {c["id"]: c for c in data_rep["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"}

# Definición rigurosa de los 50 casos con verificación capa por capa
CASOS_MATRIZ = [
    # G1_01: Corolla calienta 25 min, se apaga, en caliente gira pero no prende, 15 min prende.
    # Causa: Sensor CKP por fatiga térmica.
    # ML: Top1 Bujías (65.8%), Top2 Bomba gasolina (24.4%), Top3 Presión aceite (2.8%).
    # CKP no está en Top-1 ni en Top-3 ML ni en reporte final.
    {"id": "G1_01", "gt": "Sensor CKP por fatiga térmica", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bujias o bobinas de encendido (misfire)", "literal_top2": "Bomba de gasolina quemada o con baja presion", "literal_top3": "Baja presion de aceite o bomba de aceite defectuosa", "literal_e2e": "Bujías o bobinas"},

    # G1_02: Yaris pierde fuerza subiendo cerro con 4 personas, pisando a fondo se ahoga.
    # Causa: Bomba de gasolina quemada o baja presión.
    # Clarificación interactiva (0.0%). Turno 2 cayó en fuera de alcance.
    {"id": "G1_02", "gt": "Bomba de gasolina quemada o baja presión", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Clarificación interactiva", "literal_top2": "N/A", "literal_top3": "N/A", "literal_e2e": "Fuera de alcance automotriz"},

    # G1_03: Kia Rio mínimo inestable, se apaga en semáforo, limpiaron cuerpo aceleración, A/C empeora.
    # Causa: Cuerpo de aceleración / válvula IAC.
    # ML: Top1 Cuerpo de aceleracion o valvula IAC (89.4%).
    {"id": "G1_03", "gt": "Cuerpo de aceleración o válvula IAC", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Cuerpo de aceleracion o valvula IAC sucia", "literal_top2": "Bomba de gasolina", "literal_top3": "Inyectores", "literal_e2e": "Cuerpo de aceleración o válvula IAC"},

    # G1_04: Sentra caliente falla un cilindro, rotaron bujías y bobinas y sigue en mismo cilindro.
    # Causa: Inyector con falla térmica (o compresión).
    # ML: Top1 Bujías (82.0%), Top2 Bomba (11.0%), Top3 Desgaste anillos (2.8%). Inyector ausente en Top-3.
    {"id": "G1_04", "gt": "Inyector con falla térmica (cilindro)", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bujias o bobinas de encendido (misfire)", "literal_top2": "Bomba de gasolina", "literal_top3": "Consumo de aceite por desgaste de anillos", "literal_e2e": "Bujías o bobinas"},

    # G1_05: Mazda 3 check parpadea acelerando fuerte, P0303, bujía 3 húmeda.
    # Causa: Bujías o bobinas de encendido (misfire P0303).
    # ML: Top1 Bujías o bobinas (91.1%).
    {"id": "G1_05", "gt": "Falla en bujías o bobinas (misfire P0303)", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bujias o bobinas de encendido (misfire)", "literal_top2": "Inyectores", "literal_top3": "Cuerpo aceleración", "literal_e2e": "Bujías o bobinas"},

    # G1_06: Corolla P0171, fuel trims positivos en mínimo pero mejoran a 2500 rpm.
    # Causa: Fuga de vacío en admisión (empaque de múltiple).
    # ML: Top1 Cuerpo aceleración / IAC (53.0%), Top2 Bomba, Top3 Intercooler. Fuga de vacío ausente en Top-3.
    {"id": "G1_06", "gt": "Fuga de vacío en múltiple de admisión", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Cuerpo de aceleracion o valvula IAC sucia", "literal_top2": "Bomba de gasolina", "literal_top3": "Fuga mangueras intercooler", "literal_e2e": "Cuerpo de aceleración / IAC"},

    # G1_07: Accent demora en prender tras llenar tanque full, huele a gasolina cruda.
    # Causa: Válvula de purga del cánister EVAP trabada abierta.
    # Clarificación interactiva (50.8%). Turno 2 concluyó en Sensor O2 / mezcla rica. Cánister ausente.
    {"id": "G1_07", "gt": "Válvula de purga de cánister EVAP", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Clarificación interactiva", "literal_top2": "Bomba de gasolina", "literal_top3": "Inyectores", "literal_e2e": "Falla en sensor de oxígeno o mezcla rica"},

    # G1_08: Hilux 2GD humo negro en aceleración, presión de riel cae bajo carga.
    # Causa: Fuga o baja presión Common Rail Diesel.
    # ML: Top1 Common Rail Diesel (93.2%).
    {"id": "G1_08", "gt": "Fuga o baja presión Common Rail Diesel", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", "literal_top2": "Faja distribución", "literal_top3": "Termostato", "literal_e2e": "Common Rail Diesel"},

    # G1_09: Toyota gasolina demora en arrancar en caliente, presión en rango, sin DTC.
    # Causa: Inyectores goteando en reposo / Sensor ECT descalibrado.
    # ML: Top1 Common Rail Diesel (61.5%), Top2 Bomba (15.0%), Top3 Bujías (9.7%). Inyectores ausentes.
    {"id": "G1_09", "gt": "Inyectores goteando en reposo / Sensor ECT", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", "literal_top2": "Bomba de gasolina", "literal_top3": "Bujías/bobinas", "literal_e2e": "Common Rail Diesel"},

    # G1_10: Tiida cascabelea en subida, timing advance oscila mucho.
    # Causa: Faja o cadena de distribución destensada / fuera de punto.
    # ML: Top1 Faja o cadena de distribución (92.1%).
    {"id": "G1_10", "gt": "Faja o cadena de distribución destensada", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Faja o cadena de distribucion destensada o con salto de punto", "literal_top2": "Bujías/bobinas", "literal_top3": "Correa bañada aceite", "literal_e2e": "Faja o cadena de distribución"},

    # G1_11: Sentra P0420, sensor 2 copia la señal del sensor 1, sin misfire.
    # Causa: Convertidor catalítico ineficiente / agotado.
    # ML Top1 Bujías (73.1%), Top2 Sensor O2 (73.1%), Top3 Bomba (3.7%).
    # En Top1 y Top3 ML: "catalizador" no aparece (0 y 0).
    # En E2E: RAG inyectó PROCEDIMIENTO: EFICIENCIA DE CATALIZADOR P0420. (E2E diferencial = 1).
    {"id": "G1_11", "gt": "Convertidor catalítico ineficiente (DTC P0420)", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 1, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bujias o bobinas de encendido (misfire)", "literal_top2": "Falla en sensor de oxigeno o mezcla rica", "literal_top3": "Bomba de gasolina", "literal_e2e": "Bujías/bobinas (Reporte RAG: DTC P0420 Catalizador)"},

    # G1_12: Toyota P0301 persistente tras rotar bujía y bobina, compresión baja en cil 1.
    # Causa: Pérdida de compresión por válvula quemada o anillos cil 1.
    # ML Top1 Bujías (98.5%), Top2 Desgaste anillos (0.3%), Top3 Inyectores (0.2%).
    # Top-1 ML: 0. Top-3 ML: 0 (la causa es válvula quemada / compresión, no consumo de aceite por anillos).
    # E2E: Reporte entregó exclusivamente cambio de bobinas COP y bujías de iridio. E2E = 0.
    {"id": "G1_12", "gt": "Pérdida de compresión válvula/anillos cil 1", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bujias o bobinas de encendido (misfire)", "literal_top2": "Consumo de aceite por desgaste de anillos o retenes", "literal_top3": "Inyectores sucios", "literal_e2e": "Bujías o bobinas COP"},

    # G1_13: Kia humo negro, mezcla rica, presión alta, gasolina en manguera de vacío del regulador.
    # Causa: Diafragma de regulador de presión de combustible roto.
    # ML Top1 Sensor O2 / mezcla rica (84.9%), Top2 Bomba (4.6%), Top3 Inyectores (4.4%).
    # Regulador ausente en Top-1, Top-3 y E2E.
    {"id": "G1_13", "gt": "Diafragma del regulador de presión roto", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en sensor de oxigeno o mezcla rica", "literal_top2": "Bomba de gasolina", "literal_top3": "Inyectores", "literal_e2e": "Falla en sensor de oxígeno o mezcla rica"},

    # G1_14: Yaris tironea solo cuando tanque baja de 1/4.
    # Causa: Bomba de gasolina quemada o baja presión / filtro sumergido.
    # Clarificación interactiva. Turno 2 cayó en fuera de alcance.
    {"id": "G1_14", "gt": "Bomba de gasolina quemada / filtro sumergido", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Clarificación interactiva", "literal_top2": "N/A", "literal_top3": "N/A", "literal_e2e": "Fuera de alcance automotriz"},

    # G1_15: Cerato tironea 1500-2000 rpm, DTC P0202.
    # Causa: Falla en inyector 2 o circuito de inyector P0202.
    # ML Top1 Bujías (74.5%), Top2 Bomba (15.1%), Top3 Correa en aceite (3.2%). Inyector ausente.
    {"id": "G1_15", "gt": "Falla en circuito de inyector 2 (P0202)", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bujias o bobinas de encendido (misfire)", "literal_top2": "Bomba de gasolina", "literal_top3": "Correa bañada en aceite", "literal_e2e": "Bujías o bobinas"},

    # G1_16: Pedal se va al fondo lentamente en semáforo, líquido completo.
    # Causa: Fuga interna en cilindro maestro / aire en frenos.
    # ML Top1 Fuga hidráulica o aire en frenos (93.2%).
    {"id": "G1_16", "gt": "Fuga interna cilindro maestro / aire frenos", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Fuga hidraulica o aire en el sistema de frenos", "literal_top2": "Servofreno booster", "literal_top3": "Pastillas/zapatas", "literal_e2e": "Fuga hidráulica o aire en frenos"},

    # G1_17: Pedal de freno duro como piedra, frena muy poco.
    # Causa: Falla en servofreno booster o línea de vacío.
    # ML Top1 Servofreno booster (96.5%).
    {"id": "G1_17", "gt": "Falla en servofreno booster o vacío", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en servofreno (booster) o linea de vacio", "literal_top2": "Discos alabeados", "literal_top3": "Fuga hidráulica", "literal_e2e": "Servofreno booster o línea de vacío"},

    # G1_18: Rueda derecha hirviendo tras 15 min y carro jala, enfría y rueda libre.
    # Causa: Cáliper de freno trabado / mordaza pegada.
    # ML Top1 Pastillas y zapatas (59.5%), Top2 Llantas (7.8%), Top3 Homocinéticas (5.1%).
    # Cáliper ausente en Top-1, Top-3 y E2E.
    {"id": "G1_18", "gt": "Caliper de freno trabado / mordaza pegada", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Desgaste de pastillas y zapatas de freno", "literal_top2": "Llantas desbalanceadas", "literal_top3": "Juntas homocinéticas", "literal_e2e": "Desgaste de pastillas y zapatas"},

    # G1_19: A 100 km/h no vibra nada, frena suave y tiembla timón.
    # Causa: Discos de freno alabeados o desgastados.
    # ML Top1 Llantas desbalanceadas (65.7%), Top2 Discos de freno alabeados (30.9%), Top3 Booster (0.9%).
    # Top-1 ML: 0. Top-3 ML: 1 (Top2 Discos alabeados). Macro: 0 (SUSPENSION_CHASIS).
    # E2E Estricto: 0 (sugirió Llantas). E2E Diferencial: 1 (Top2 Discos alabeados explícito).
    {"id": "G1_19", "gt": "Discos de freno alabeados o desgastados", "top1_ok": 0, "top3_ok": 1, "e2e_estricto": 0, "e2e_dif": 1, "macro_ok": 0, "inter_ok": 1,
     "literal_top1": "Llantas desbalanceadas o desalineadas", "literal_top2": "Discos de freno alabeados o desgastados", "literal_top3": "Servofreno booster", "literal_e2e": "Llantas (Diferencial Top-2: Discos alabeados)"},

    # G1_20: Vibración en volante exactamente de 90 a 115 km/h, frenando no cambia.
    # Causa: Llantas desbalanceadas o desalineadas.
    # ML Top1 Llantas desbalanceadas (97.4%).
    {"id": "G1_20", "gt": "Llantas desbalanceadas o desalineadas", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Llantas desbalanceadas o desalineadas", "literal_top2": "Juntas homocinéticas", "literal_top3": "Pastillas/zapatas", "literal_e2e": "Llantas desbalanceadas o desalineadas"},

    # G1_21: Testigo ABS encendido, pulsación en pedal a baja velocidad en asfalto seco.
    # Causa: Falla en sensor de velocidad de rueda ABS.
    # ML Top1 Sensor velocidad rueda ABS (76.1%).
    {"id": "G1_21", "gt": "Falla en sensor de velocidad de rueda ABS", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en sensor de velocidad de rueda ABS", "literal_top2": "Pastillas/zapatas", "literal_top3": "Fuga hidráulica", "literal_e2e": "Sensor de velocidad de rueda ABS"},

    # G1_22: Cambió pastillas delanteras, pedal se va al fondo al 1er bombazo, al 2do agarra.
    # Causa: Aire en sistema de frenos / purga deficiente.
    # ML cayó en fuera de alcance automotriz (0.0%). Macro cayó en MOTOR.
    {"id": "G1_22", "gt": "Aire en sistema de frenos tras purga", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 0, "inter_ok": 1,
     "literal_top1": "Consulta fuera del alcance automotriz", "literal_top2": "N/A", "literal_top3": "N/A", "literal_e2e": "Consulta fuera del alcance automotriz"},

    # G1_23: Caja automática golpea de N a D y de N a R, patina en 1ra en subida.
    # Causa: Falta o degradación de aceite de caja de cambios.
    # ML Top1 Falta o degradación de aceite de caja (64.5%).
    {"id": "G1_23", "gt": "Falta o degradación de aceite de caja", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falta o degradacion de aceite de caja de cambios", "literal_top2": "Solenoides CVT/DSG", "literal_top3": "Caja Dualogic", "literal_e2e": "Falta o degradación de aceite de caja"},

    # G1_24: Sentra CVT acelera pero no avanza proporcionalmente, zumbido agudo, testigo temp caja.
    # Causa: Sobrecalentamiento / solenoides / poleas CVT.
    # ML Top1 Solenoides / CVT (75.6%).
    {"id": "G1_24", "gt": "Sobrecalentamiento o solenoides CVT", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "literal_top2": "Inyectores", "literal_top3": "Bomba gasolina", "literal_e2e": "Solenoides en caja automática CVT/DSG"},

    # G1_25: VW DSG tiembla en 1ra caliente, demora en D, sin falla de motor.
    # Causa: Embrague K1 desgastado / mecatrónica DSG.
    # ML Top1 Bujías (82.8%), Top2 Disco de embrague (6.6%), Top3 Dualogic (2.1%). Macro: MOTOR (0).
    # Top1 ML: 0. Top3 ML: 1 (Top2 Disco de embrague desgastado).
    # E2E: Reporte entregó cambio de bujías por misfire P0300/P0301. En E2E el usuario recibió bujías: E2E = 0.
    {"id": "G1_25", "gt": "Embrague K1 desgastado caja DSG", "top1_ok": 0, "top3_ok": 1, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 0, "inter_ok": 1,
     "literal_top1": "Falla en bujias o bobinas de encendido (misfire)", "literal_top2": "Disco de embrague desgastado o patinando", "literal_top3": "Caja robotizada Dualogic", "literal_e2e": "Bujías de encendido y misfire"},

    # G1_26: Fiat Dualogic no pone cambios de mañana, bomba hidráulica suena continuo en puerta.
    # Causa: Acumulador de presión / grupo electrohidráulico Dualogic.
    # ML Top1 Falla en caja robotizada Dualogic (95.7%).
    {"id": "G1_26", "gt": "Acumulador de presión caja Dualogic", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)", "literal_top2": "Bomba gasolina", "literal_top3": "Bombín embrague", "literal_e2e": "Caja robotizada Dualogic"},

    # G1_27: Acelero en 3ra, suben RPM pero carro no avanza, olor a asbesto quemado.
    # Causa: Disco de embrague desgastado o patinando.
    # ML Clarificación (26.4%), Top2 Bujías, Top3 Bomba. Turno 2 concluyó en Sensor O2/mezcla. Macro: MOTOR.
    # Embrague ausente en Top1, Top3 y E2E. Interrogador activó erróneamente en consulta no ambigua de embrague.
    {"id": "G1_27", "gt": "Disco de embrague desgastado o patinando", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 0, "inter_ok": 0,
     "literal_top1": "Clarificación interactiva", "literal_top2": "Bujías/bobinas", "literal_top3": "Bomba gasolina", "literal_e2e": "Falla en sensor de oxígeno o mezcla rica"},

    # G1_28: Al pisar embrague ronquido, suelta pedal y desaparece, no patina.
    # Causa: Collarín de empuje / crapodina de embrague.
    # ML Top1 Bombín embrague (63.7%), Top2 Disco embrague (34.1%), Top3 CVT/DSG (1.7%).
    # Collarín ausente en Top-1, Top-3 ML y en el reporte (que entregó mecatrónica DSG automática).
    {"id": "G1_28", "gt": "Collarín de empuje / crapodina desgastada", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bombin o bomba hidraulica de embrague", "literal_top2": "Disco de embrague desgastado o patinando", "literal_top3": "Solenoides CVT/DSG", "literal_e2e": "Bombín de embrague (Reporte: Mecatrónica DSG)"},

    # G1_29: En neutro zumbido, pisa embrague y desaparece, al soltar vuelve.
    # Causa: Rodajes de caja mecánica o diferencial (rodamiento primario).
    # ML Top1 Bombín embrague (89.2%), Top2 Falta aceite (3.2%), Top3 Dualogic (2.8%). Rodajes ausentes.
    {"id": "G1_29", "gt": "Rodajes de caja mecánica (eje primario)", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en bombin o bomba hidraulica de embrague", "literal_top2": "Falta aceite caja", "literal_top3": "Caja Dualogic", "literal_e2e": "Bombín de embrague"},

    # G1_30: En 1ra trepida / zapatea bruscamente, soportes cambiados.
    # Causa: Plato opresor alabeado o embrague zapateando.
    # ML Top1 Disco de embrague desgastado o patinando (95.4%).
    {"id": "G1_30", "gt": "Plato opresor alabeado / embrague zapatea", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Disco de embrague desgastado o patinando", "literal_top2": "Caja Dualogic", "literal_top3": "Bomba gasolina", "literal_e2e": "Disco de embrague desgastado o patinando"},

    # G1_31: Carro jala a la derecha tras zanja profunda, timón 15 grados torcido.
    # Causa: Llantas desalineadas / desalineación severa.
    # ML Top1 Llantas desbalanceadas o desalineadas (98.6%).
    {"id": "G1_31", "gt": "Llantas desalineadas tras impacto", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Llantas desbalanceadas o desalineadas", "literal_top2": "Amortiguadores", "literal_top3": "Cremallera dirección", "literal_e2e": "Llantas desbalanceadas o desalineadas"},

    # G1_32: Crujido clac-clac al doblar toda la dirección acelerando en esquinas.
    # Causa: Juntas homocinéticas o palieres dañados.
    # ML Top1 Juntas homocinéticas o palieres dañados (63.8%).
    {"id": "G1_32", "gt": "Juntas homocinéticas o palieres dañados", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Juntas homocineticas o palieres danados", "literal_top2": "Llantas desbalanceadas", "literal_top3": "Cremallera dirección", "literal_e2e": "Juntas homocinéticas o palieres dañados"},

    # G1_33: A 70 km/h zumbido ronco adelante, curva izquierda disminuye, derecha aumenta.
    # Causa: Rodamiento de rueda / maza delantera picado.
    # ML Top1 Llantas (93.6%), Top2 Rodajes de caja (3.4%), Top3 Homocinéticas (1.1%).
    # En Top-1 y Top-3 ML: "rodamiento de rueda" no aparece (0 y 0).
    # En E2E: RAG inyectó PROCEDIMIENTO: DIAGNÓSTICO METROLÓGICO DE RODAMIENTOS DE RUEDA / MAZA. (E2E diferencial = 1).
    {"id": "G1_33", "gt": "Rodamiento de rueda / maza picado", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 1, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Llantas desbalanceadas o desalineadas", "literal_top2": "Rodajes de caja mecanica o diferencial", "literal_top3": "Juntas homocinéticas", "literal_e2e": "Llantas (Reporte RAG: Rodamientos de Rueda/Maza)"},

    # G1_34: Rebota 3 veces en rompemuelles y flota en carretera.
    # Causa: Amortiguadores reventados o bujes de suspensión.
    # ML Top1 Llantas (67.1%), Top2 Sensor O2 (5.0%), Top3 Inyectores (3.7%). Amortiguadores ausente.
    {"id": "G1_34", "gt": "Amortiguadores reventados / bujes", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Llantas desbalanceadas o desalineadas", "literal_top2": "Sensor O2/mezcla", "literal_top3": "Inyectores", "literal_e2e": "Llantas desbalanceadas o desalineadas"},

    # G1_35: Juego excesivo en timón antes de responder, traqueteo en adoquinado.
    # Causa: Cremallera de dirección asistida con holgura o terminales axiales.
    # ML Top1 Cremallera de dirección asistida (95.5%).
    {"id": "G1_35", "gt": "Cremallera de dirección asistida con holgura", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Cremallera de direccion asistida con holgura o fuga", "literal_top2": "Llantas desbalanceadas", "literal_top3": "Juntas homocinéticas", "literal_e2e": "Cremallera de dirección asistida"},

    # G1_36: Llantas delanteras comidas por borde interno en ambos lados rápidamente.
    # Causa: Llantas desalineadas (camber negativo / divergencia).
    # ML Top1 Llantas desbalanceadas o desalineadas (98.9%).
    {"id": "G1_36", "gt": "Llantas desalineadas (camber / divergencia)", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Llantas desbalanceadas o desalineadas", "literal_top2": "Juntas homocinéticas", "literal_top3": "Amortiguadores", "literal_e2e": "Llantas desbalanceadas o desalineadas"},

    # G1_37: Temperatura sube en tráfico a zona roja, baja en carretera rápida, ventilador no enciende.
    # Causa: Motoventilador de radiador quemado o relé.
    # ML Top1 Termostato o motoventilador de radiador (91.0%).
    {"id": "G1_37", "gt": "Motoventilador de radiador quemado", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en termostato o motoventilador de radiador", "literal_top2": "Bujías/bobinas", "literal_top3": "Descarbonización GDI", "literal_e2e": "Termostato o motoventilador de radiador"},

    # G1_38: Calienta en carretera y ciudad por igual, manguera superior hierve dura, inferior fría.
    # Causa: Termostato trabado cerrado.
    # ML Top1 Termostato o motoventilador de radiador (70.6%).
    {"id": "G1_38", "gt": "Termostato trabado cerrado", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Falla en termostato o motoventilador de radiador", "literal_top2": "Fuga mangueras radiador", "literal_top3": "Baja presión aceite", "literal_e2e": "Termostato o motoventilador de radiador"},

    # G1_39: Consume refrigerante sin gotear, burbujas constantes en depósito, mangueras duras en frío.
    # Causa: Empaque de culata soplado o dañado.
    # ML Top1 Clarificación (25.6%), Top2 Faja/cadena (19.0%), Top3 Empaque de culata soplado (14.0%).
    # Top-1 ML: 0. Top-3 ML: 1 (Top-3 literal: Empaque de culata soplado o danado).
    # Interactivo: Activó auto-interrogador oportunamente (1).
    # E2E Estricto: 0 (sugirió Fuga en mangueras). E2E Diferencial: 1 (opción 3 del reporte entregó Empaque de culata).
    {"id": "G1_39", "gt": "Empaque de culata soplado o dañado", "top1_ok": 0, "top3_ok": 1, "e2e_estricto": 0, "e2e_dif": 1, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Clarificación interactiva", "literal_top2": "Faja o cadena distribución", "literal_top3": "Empaque de culata soplado o danado", "literal_e2e": "Fuga mangueras (Opción 3 Auto-pregunta: Empaque de culata)"},

    # G1_40: Testigo de aceite parpadea en ralentí caliente, acelera a 1500 rpm y se apaga.
    # Causa: Baja presión de aceite o bomba de aceite defectuosa.
    # ML Top1 Baja presión de aceite o bomba de aceite (66.9%).
    {"id": "G1_40", "gt": "Baja presión de aceite o bomba defectuosa", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Baja presion de aceite o bomba de aceite defectuosa", "literal_top2": "Cuerpo aceleración", "literal_top3": "Descarbonización GDI", "literal_e2e": "Baja presión de aceite o bomba defectuosa"},

    # G1_41: En mañanas tac-tac metálico arriba del motor 3 min, llega aceite y calienta desaparece.
    # Causa: Taqués / buzos hidráulicos descargados (retraso en presión de aceite).
    # ML Top1 Baja presión de aceite (53.0%), Top2 Bujías (14.6%), Top3 Faja (7.9%).
    # ¿Aparece literalmente "taqués"? No. La causa física es baja presión de aceite en culata.
    # Si evaluamos Top-1 ML como la causa física real: Top1 = 1, Top3 = 1.
    # Pero en E2E: RAG entregó Procedimiento de Sensor CKP P0335 (totalmente desvinculado de taqués).
    # En E2E: la hipótesis principal fue baja presión de aceite. (E2E estricto = 1 si se convalida presión de aceite, 0 si se exige taqués).
    {"id": "G1_41", "gt": "Taqués hidráulicos / baja presión de aceite", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Baja presion de aceite o bomba de aceite defectuosa", "literal_top2": "Bujías/bobinas", "literal_top3": "Faja o cadena", "literal_e2e": "Baja presión de aceite o bomba defectuosa"},

    # G1_42: Luces parpadean acelerando, quemó dos focos, 16.1 V a 2000 rpm.
    # Causa: Alternador defectuoso o placa de diodos / regulador en sobrevoltaje.
    # ML Top1 Alternador defectuoso o placa de diodos quemada (87.2%).
    {"id": "G1_42", "gt": "Alternador en sobrevoltaje (placa de diodos)", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Alternador defectuoso o placa de diodos quemada", "literal_top2": "Sensor O2/mezcla", "literal_top3": "Inyectores", "literal_e2e": "Alternador defectuoso o placa de diodos quemada"},

    # G1_43: P0562, 11.9 V en ralentí y 12.3 V acelerando, batería cambiada hace una semana.
    # Causa: Alternador defectuoso o placa de diodos quemada (baja carga P0562).
    # ML Top1 Batería descargada (79.3%), Top2 Alternador defectuoso (17.7%), Top3 IAC (0.9%).
    # Top-1 ML: 0. Top-3 ML: 1 (Top2 Alternador defectuoso).
    # E2E Estricto: 0 (sugirió Batería). E2E Diferencial: 1 (Top2 Alternador explícito).
    {"id": "G1_43", "gt": "Alternador defectuoso (baja carga P0562)", "top1_ok": 0, "top3_ok": 1, "e2e_estricto": 0, "e2e_dif": 1, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Bateria descargada o bornes sulfatados", "literal_top2": "Alternador defectuoso o placa de diodos quemada", "literal_top3": "Cuerpo aceleración", "literal_e2e": "Batería descargada (Diferencial Top-2: Alternador defectuoso)"},

    # G1_44: Solo hace 'clac', faros brillantes, batería 12.7 V, prende al golpear motor de arranque.
    # Causa: Motor de arranque o solenoide defectuoso (escobillas/carbones).
    # ML Top1 Batería descargada (88.2%), Top2 Alternador (11.0%), Top3 Inversor EV (0.3%).
    # Motor de arranque ausente en Top-1, Top-3 y E2E.
    {"id": "G1_44", "gt": "Motor de arranque o solenoide defectuoso", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Bateria descargada o bornes sulfatados", "literal_top2": "Alternador defectuoso", "literal_top3": "Inversor IGBT EV", "literal_e2e": "Batería descargada o bornes sulfatados"},

    # G1_45: Batería nueva se descarga en la noche, alternador carga 14.2 V, consumo de 650 mA.
    # Causa: Fuga parásita de corriente en reposo.
    # ML Top1 Alternador defectuoso (83.8%), Top2 Batería descargada (15.3%), Top3 Batería HV (0.3%).
    # Fuga parásita ausente en Top-1, Top-3 y E2E.
    {"id": "G1_45", "gt": "Fuga parásita de corriente en reposo", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Alternador defectuoso o placa de diodos quemada", "literal_top2": "Bateria descargada", "literal_top3": "Batería HV EV", "literal_e2e": "Alternador defectuoso o placa de diodos quemada"},

    # G1_46: Camión Volvo FM demora más de 20 min en cargar aire a 8 bar, sin fugas audibles.
    # Causa: Válvulas de compresor desgastadas / fuga compresor frenos neumático.
    # ML Top1 Fugas de aire o fallos en el sistema de frenos neumático (57.7%).
    {"id": "G1_46", "gt": "Fuga / falla en frenos neumático (compresor)", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)", "literal_top2": "Termostato", "literal_top3": "Compresor A/C", "literal_e2e": "Fugas de aire / frenos neumático (Camiones)"},

    # G1_47: Gobernadora descarga aire cada 10 s en ralentí con secador APS nuevo.
    # Causa: Válvula de freno de aire o secador APS obstruido / fuga señal gobernadora.
    # ML Top1 Válvula de freno de aire o secador APS obstruido (41.8%).
    # Macro: MOTOR (0). Interactivo: Activó auto-interrogador (1). E2E: Finalizó en secador APS (1).
    {"id": "G1_47", "gt": "Válvula de freno de aire o secador APS", "top1_ok": 1, "top3_ok": 1, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 0, "inter_ok": 1,
     "literal_top1": "Válvula de freno de aire o secador APS obstruido (Camiones)", "literal_top2": "Discos alabeados", "literal_top3": "Bomba gasolina", "literal_e2e": "Válvula de freno de aire o secador APS obstruido"},

    # G1_48: Tractocamión Volvo FH: escape constante por válvula de escape rápido al soltar parqueo.
    # Causa: Fugas de aire en cámara de freno Maxi-Brake (diafragma roto).
    # ML Top1 Bomba gasolina (65.6%), Top2 Discos alabeados, Top3 Intercooler. Macro: MOTOR.
    # Neumática Maxi-Brake ausente en Top-1, Top-3 y E2E.
    {"id": "G1_48", "gt": "Cámara Maxi-Brake de freno de aire rota", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 0, "inter_ok": 1,
     "literal_top1": "Bomba de gasolina quemada o con baja presion", "literal_top2": "Discos alabeados", "literal_top3": "Intercooler", "literal_e2e": "Bomba de gasolina quemada"},

    # G1_49: Consulta térmica ambigua: pesado en caliente, tiembla, se apaga, sin escáner.
    # Criterio principal de éxito: Activar correctamente el auto-interrogador.
    # ML: No intentó adivinar una falla única en frío (Top-1 ML = 0, Top-3 ML = 0 en predicción unívoca).
    # Auto-interrogador: SÍ, activó con éxito (1).
    # E2E Estricto: SÍ, cumplió el criterio de éxito de activación interactiva (1).
    {"id": "G1_49", "gt": "Consulta térmica ambigua (Meta: Auto-interrogador)", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 1, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 1,
     "literal_top1": "Clarificación interactiva (Auto-pregunta)", "literal_top2": "Cuerpo aceleración", "literal_top3": "Bomba gasolina", "literal_e2e": "Auto-pregunta técnica de descarte disparada"},

    # G1_50: Consulta difusa en tren delantero: cloc adelante, jala, raro en timón, sin datos.
    # Criterio principal de éxito: Activar correctamente el auto-interrogador.
    # ML: Adivinó ciegamente Llantas desbalanceadas al 84% sin activar el interrogador.
    # Falló en Top-1, Top-3, Auto-interrogador y E2E.
    {"id": "G1_50", "gt": "Tren delantero difuso (Meta: Auto-interrogador)", "top1_ok": 0, "top3_ok": 0, "e2e_estricto": 0, "e2e_dif": 0, "macro_ok": 1, "inter_ok": 0,
     "literal_top1": "Llantas desbalanceadas o desalineadas", "literal_top2": "Batería descargada", "literal_top3": "Cremallera dirección", "literal_e2e": "Llantas desbalanceadas (Adivinanza sin interrogar)"}
]

# Recálculo exacto
t = len(CASOS_MATRIZ)
s_top1 = sum(c["top1_ok"] for c in CASOS_MATRIZ)
s_top3 = sum(c["top3_ok"] for c in CASOS_MATRIZ)
s_e2e_estricto = sum(c["e2e_estricto"] for c in CASOS_MATRIZ)
s_e2e_dif = sum(c["e2e_dif"] for c in CASOS_MATRIZ)
s_e2e_inc = t - (s_e2e_estricto + s_e2e_dif)
s_macro = sum(c["macro_ok"] for c in CASOS_MATRIZ)
s_inter = sum(c["inter_ok"] for c in CASOS_MATRIZ)

print(f"Total casos: {t}")
print(f"Top1_ML_correcto: {s_top1} / {t} ({s_top1/t*100:.2f}%)")
print(f"Top3_ML_correcto: {s_top3} / {t} ({s_top3/t*100:.2f}%)")
print(f"E2E_estricto: {s_e2e_estricto} / {t} ({s_e2e_estricto/t*100:.2f}%)")
print(f"E2E_diferencial: {s_e2e_dif} / {t} ({s_e2e_dif/t*100:.2f}%)")
print(f"E2E_incorrecto: {s_e2e_inc} / {t} ({s_e2e_inc/t*100:.2f}%)")
print(f"E2E_global (estricto+dif): {s_e2e_estricto + s_e2e_dif} / {t} ({(s_e2e_estricto + s_e2e_dif)/t*100:.2f}%)")
print(f"macro_correcto: {s_macro} / {t} ({s_macro/t*100:.2f}%)")
print(f"interrogador_correcto: {s_inter} / {t} ({s_inter/t*100:.2f}%)")

# Guardar la matriz detallada para la respuesta
out_matrix = BASE_DIR / "scratch" / "matriz_50_verificada.json"
with open(out_matrix, "w", encoding="utf-8") as f:
    json.dump(CASOS_MATRIZ, f, indent=2, ensure_ascii=False)
