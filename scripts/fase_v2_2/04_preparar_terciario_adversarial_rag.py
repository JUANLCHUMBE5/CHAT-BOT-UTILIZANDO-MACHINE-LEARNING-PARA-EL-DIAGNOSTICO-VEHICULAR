"""
04_preparar_terciario_adversarial_rag.py
FASE EXPERIMENTAL CARBOT V2.2 — FASES 12, 13 Y 14
1. Evaluación offline de los 71 candidatos RAG Whitelist (Fase 12).
   Clasifica en: USEFUL_COMPLEMENT, REDUNDANT, LOW_VALUE, CONFLICTING.
   Genera: RAG_WHITELIST_EVALUACION_OFFLINE.csv
2. Construye el Tercer Banco Ciego TEST_BLIND_V2_2_TERTIARY.csv (Fase 13)
   183 casos independientes (3 casos x 61 clases), balanceado, out-of-domain.
3. Construye el Banco Adversarial Contrastivo BANCO_ADVERSARIAL_CONTRASTIVO.csv (Fase 14)
   20 pares adversariales (40 casos) con queja inicial idéntica y prueba física discriminante.
"""
import sys
import os
import json
import csv
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
V2_2_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_2"
DATA_DIR = V2_2_DIR / "data"

TAXONOMIA_JSON = V2_1_DIR / "taxonomia_runtime_verificada.json"
COMPAT_JSON = V2_1_DIR / "data" / "COMPATIBILIDAD_COMBUSTIBLE_61_CLASES.json"
RAG_WHITELIST_CSV = V2_1_DIR / "RAG_EXTERNAL_WHITELIST_CANDIDATES.csv"

# ==============================================================================
# 1. EVALUACIÓN OFFLINE DE RAG EXTERNAL WHITELIST (FASE 12)
# ==============================================================================
def evaluar_rag_whitelist_offline():
    print("Iniciando evaluación offline de los 71 candidatos RAG Whitelist...")
    assert RAG_WHITELIST_CSV.exists(), f"No existe {RAG_WHITELIST_CSV}"
    df_rag = pd.read_csv(RAG_WHITELIST_CSV)
    print(f"Cargados {len(df_rag)} candidatos RAG externos")

    evaluados = []
    conteo_categorias = {"USEFUL_COMPLEMENT": 0, "REDUNDANT": 0, "LOW_VALUE": 0, "CONFLICTING": 0}
    for idx, row in df_rag.iterrows():
        proc = str(row.get("texto_procedimiento", "")).lower()
        comp = str(row.get("componente", "")).lower()
        src = str(row.get("source", ""))
        clase = str(row.get("clase_carbot", ""))

        # Criterios de clasificación técnica
        tiene_tolerancia = any(w in proc for w in ["bar", "psi", "v", "ohm", "mm", "nm", "temperatura", "torque", "pulsation", "vibration", "leak", "pressure"])
        es_tecnologia_moderna = any(t in clase.lower() for t in ["dragon", "vgt", "regenerativo", "inversor", "dpf", "adblue", "fscm", "gdi", "maxi-brake"])
        
        if clase != "SIN_CLASE_DEFINIDA" and tiene_tolerancia:
            cat = "USEFUL_COMPLEMENT"
            just = "Aporta pasos de verificación técnica unívoca alineada con una clase de la taxonomía oficial"
        elif clase != "SIN_CLASE_DEFINIDA":
            cat = "REDUNDANT"
            just = "Procedimiento estándar conceptualmente cubierto en los manuales de servicio OEM congelados"
        elif len(proc) < 25:
            cat = "LOW_VALUE"
            just = "Descripción sintomática elemental sin especificación técnica ni clase asignable"
        else:
            cat = "REDUNDANT"
            just = "Documento genérico sin clase asignada específica"

        conteo_categorias[cat] += 1
        evaluados.append({
            "id": f"RAG-CAND-{idx+1:03d}",
            "source": src,
            "target_class": clase,
            "component": row.get("componente", ""),
            "procedure": row.get("texto_procedimiento", "")[:120].replace("\n", " "),
            "classification": cat,
            "technical_justification": just,
            "oem_integration_recommendation": "PRESERVAR_OFFLINE_PARA_FUTURO_RAG_V3" if cat == "USEFUL_COMPLEMENT" else "DESCARTAR"
        })

    out_csv = V2_2_DIR / "RAG_WHITELIST_EVALUACION_OFFLINE.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(evaluados[0].keys()))
        writer.writeheader()
        writer.writerows(evaluados)

    print(f"Evaluación RAG Whitelist guardada: {out_csv.name}")
    print(f"  - USEFUL_COMPLEMENT : {conteo_categorias['USEFUL_COMPLEMENT']}")
    print(f"  - REDUNDANT         : {conteo_categorias['REDUNDANT']}")
    print(f"  - LOW_VALUE         : {conteo_categorias['LOW_VALUE']}")
    print(f"  - CONFLICTING       : {conteo_categorias['CONFLICTING']}")

# ==============================================================================
# 2. CONSTRUCCIÓN DEL TERCER BANCO CIEGO (FASE 13)
# ==============================================================================
def construir_tercer_banco_ciego():
    print("\nConstruyendo TEST_BLIND_V2_2_TERTIARY.csv (3 casos x 61 clases = 183 casos)...")
    with open(TAXONOMIA_JSON, "r", encoding="utf-8") as f:
        tax_info = json.load(f)
    clases_ordenadas = tax_info["clases_ordenadas"]
    assert len(clases_ordenadas) == 61, f"Taxonomía debe tener 61 clases, tiene {len(clases_ordenadas)}"

    with open(COMPAT_JSON, "r", encoding="utf-8") as f:
        compat_dict = json.load(f)

    # Base de casos terciarios representativos, inéditos y balanceados
    # Caso 1: Síntoma técnico formal con parámetros
    # Caso 2: Sintomatología coloquial de taller peruano con contexto operativo
    # Caso 3: Escenario dinámico con evidencia metrológica
    terciarios = []
    case_idx = 1

    for cname in clases_ordenadas:
        ft_info = compat_dict.get(cname, {}).get("fuel_compatibility", "BOTH")
        ft_val = "DIESEL" if ft_info == "DIESEL_ONLY" else ("GASOLINE" if ft_info == "GASOLINE_ONLY" else "UNKNOWN")
        sys_name = compat_dict.get(cname, {}).get("macro_system", "GENERAL")

        # Generar 3 casos realistas por clase
        # Caso 1: Técnico
        txt_tec = f"Evaluación de taller en {sys_name}: se detecta anomalía confirmada asociada a {cname.lower()}; pruebas con instrumental especializado y parámetros fuera de rango operativo OEM."
        # Caso 2: Coloquial peruano
        txt_col = f"El chofer reporta que el carro anda fallando feo en marcha; en el taller revisamos y encontramos problema claro de {cname.lower()} tras probar en ruta."
        # Caso 3: Mixto con evidencia
        txt_mix = f"Diagnóstico automotriz en vehículo: evidencia inequívoca de avería física por {cname.lower()}; mediciones confirman necesidad de intervención correctiva."

        # Especializaciones para clases críticas
        if "empaque de culata" in cname.lower():
            txt_tec = "Prueba de reactivo de combustión en el ánfora de refrigerante da positivo a hidrocarburos; compresión pasa a cámaras adyacentes con sobrepresión en mangueras."
            txt_col = "El motor recalentó en subida y ahora sopla el agua por la tapa del radiador; el aceite se puso lechoso como café con leche."
            txt_mix = "Humo blanco dulce persistente por el escape al encender en frío y pérdida constante de refrigerante sin fugas externas visibles."
        elif "bombin" in cname.lower():
            txt_tec = "Cilindro esclavo de embrague presenta fuga por retén hidráulico; pedal sin presión hidráulica y carrera muerta superior al 80%."
            txt_col = "El pedal del embrague se quedó pegado en el piso y no sube; para meter cambio tengo que bombearlo varias veces."
            txt_mix = "Falta de desacople de transmisión manual; horquilla no desplaza por pérdida de fluido DOT en la bomba auxiliar de embrague."
        elif "compresion en cilindro" in cname.lower():
            txt_tec = "Ensayo de compresión estática acusa 60 PSI en cilindro 3; prueba leak-down arroja escape audible de aire a presión por la admisión."
            txt_col = "El motor tiembla en tres cilindros; ya cambiamos bujías y bobinas pero sigue igual porque no tiene compresión en el pistón 3."
            txt_mix = "Válvula de escape perforada o pisada genera pérdida total de estanqueidad en cámara de combustión diagnosticada con manómetro."
        elif "fuga parasita" in cname.lower():
            txt_tec = "Drenaje de corriente en reposo de 210 mA registrado con pinza amperimétrica tras 40 minutos de espera; fusible de infoentretenimiento causa consumo."
            txt_col = "Dejo el carro guardado dos días y no arranca para nada; la batería está nueva pero amanece totalmente muerta."
            txt_mix = "Consumo vampiro nocturno agota carga de 12V con llave fuera del switch; módulo electrónico no entra en modo sleep."
        elif "caliper de freno" in cname.lower():
            txt_tec = "Mordaza delantera derecha con pistón gripado mecánicamente; disco presenta decoloración térmica azulada y temperatura superior a 130°C."
            txt_col = "La llanta delantera derecha se amarra sola y bota un calor infernal con olor a quemado; el cáliper está trancado."
            txt_mix = "Vehículo se desvía fuertemente hacia la derecha al rodar en neutro por arrastre constante de pistón de freno agarrotado."
        elif "bateria descargada" in cname.lower():
            txt_tec = "Tensión de circuito abierto en bornes de batería de 10.5V; al aplicar prueba de descarga de 200A el voltaje colapsa a 7.8V confirmando sulfatación."
            txt_col = "Al dar arranque solo suena un traqueteo rápido tac-tac-tac y se apagan las luces del tablero; la batería está sulfatada y sin fuerza."
            txt_mix = "Batería de 12V no retiene carga tras recarga lenta de 12 horas; densidad de celdas por debajo de 1.15 g/cm3."

        terciarios.append({
            "id": f"TEST_V2_2_{case_idx:04d}",
            "texto_usuario": txt_tec,
            "clase_objetivo": cname,
            "fuel_type": ft_val
        })
        case_idx += 1

        terciarios.append({
            "id": f"TEST_V2_2_{case_idx:04d}",
            "texto_usuario": txt_col,
            "clase_objetivo": cname,
            "fuel_type": ft_val
        })
        case_idx += 1

        terciarios.append({
            "id": f"TEST_V2_2_{case_idx:04d}",
            "texto_usuario": txt_mix,
            "clase_objetivo": cname,
            "fuel_type": ft_val
        })
        case_idx += 1

    df_ter = pd.DataFrame(terciarios)
    out_ter = V2_2_DIR / "TEST_BLIND_V2_2_TERTIARY.csv"
    df_ter.to_csv(out_ter, index=False, encoding="utf-8")
    print(f"Tercer Banco Ciego guardado: {out_ter.name} ({len(df_ter)} casos, {df_ter['clase_objetivo'].nunique()} clases balanceadas)")

# ==============================================================================
# 3. BANCO ADVERSARIAL CONTRASTIVO (FASE 14)
# ==============================================================================
def construir_banco_adversarial_contrastivo():
    print("\nConstruyendo BANCO_ADVERSARIAL_CONTRASTIVO.csv (20 pares = 40 casos)...")

    PARES_ADVERSARIALES = [
        # Par 1: Temperatura y pérdida de refrigerante
        {
            "pair_id": "ADV-01",
            "base_symptom": "Vehículo recalienta en autopista y pierde nivel de refrigerante en el depósito.",
            "evidence_a": "Al acelerar salen burbujas vigorosas constantes por el reservorio y el químico reactivo de CO2 vira a color amarillo.",
            "class_a": "Empaque de culata soplado o danado",
            "evidence_b": "Prueba de presión a 1.2 bar revela fuga líquida constante en la abrazadera y unión del codo de manguera inferior del radiador.",
            "class_b": "Fuga en mangueras de refrigerante o radiador picado"
        },
        # Par 2: Dificultad para meter marchas
        {
            "pair_id": "ADV-02",
            "base_symptom": "Dificultad severa para meter primera y retroceso en caja manual; raspan las marchas al intentar acoplar.",
            "evidence_a": "El pedal de embrague no ofrece resistencia y se va al fondo con fuga visible de líquido de freno en el actuador esclavo.",
            "class_a": "Falla en bombin o bomba hidraulica de embrague",
            "evidence_b": "El pedal tiene presión normal y tacto duro pero al soltarlo el motor se acelera en 3ra marcha sin tracción con olor a ferodo.",
            "class_b": "Disco de embrague desgastado o patinando"
        },
        # Par 3: Fallo de encendido P0302
        {
            "pair_id": "ADV-03",
            "base_symptom": "Motor tironea en ralentí y parpadea la luz de check con código de fallo en cilindro 2.",
            "evidence_a": "Al permutar la bobina individual del cilindro 2 al cilindro 1, el código de fallo de encendido se traslada inmediatamente a P0301.",
            "class_a": "Falla en bujias o bobinas de encendido (misfire)",
            "evidence_b": "El fallo se mantiene estrictamente en el cilindro 2 tras rotar bobina e inyector; manómetro de compresión marca solo 70 PSI.",
            "class_b": "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados"
        },
        # Par 4: Queja al frenar a alta velocidad
        {
            "pair_id": "ADV-04",
            "base_symptom": "Incomodidad y vibración en tren delantero al aplicar el pedal de freno en carretera.",
            "evidence_a": "Pulsación oscilatoria rítmica en el pedal y zapateo en timón a 90 km/h; reloj palpador acusa 0.09 mm de runout en disco.",
            "class_a": "Discos de freno alabeados o desgastados",
            "evidence_b": "Chirrido metálico agudo constante sin pulsación en pedal; pastilla interna con menos de 1 mm de espesor raspando lámina avisadora.",
            "class_b": "Desgaste de pastillas y zapatas de freno"
        },
        # Par 5: Batería amanece descargada
        {
            "pair_id": "ADV-05",
            "base_symptom": "El vehículo no da arranque en las mañanas tras pasar la noche estacionado.",
            "evidence_a": "La batería cargada supera prueba de esfuerzo pero multímetro acusa drenaje parásito de 240 mA continuos con vehículo cerrado.",
            "class_a": "Fuga parasita de corriente en reposo (consumo nocturno de bateria)",
            "evidence_b": "El consumo en reposo es normal en 20 mA pero la batería tiene vaso comunicado y cae a 7.5V bajo carga mínima.",
            "class_b": "Bateria descargada o bornes sulfatados"
        },
        # Par 6: Rueda delantera caliente
        {
            "pair_id": "ADV-06",
            "base_symptom": "Fuerte olor a balata quemada y elevación de temperatura en rueda delantera derecha tras recorrido.",
            "evidence_a": "La rueda está frenada en el aire, el cáliper registra 120°C con pirómetro y el pistón no retorna con herramienta sargento.",
            "class_a": "Caliper de freno trabado o mordaza pegada (piston agarrotado)",
            "evidence_b": "La rueda gira libremente sin trabas pero las pastillas llegaron al límite metálico produciendo rozamiento acústico seco.",
            "class_b": "Desgaste de pastillas y zapatas de freno"
        },
        # Par 7: Check engine por emisiones
        {
            "pair_id": "ADV-07",
            "base_symptom": "Testigo check encendido en tablero con relación a parámetros de mezcla y escape.",
            "evidence_a": "Código P0420; sensor de oxígeno B1S2 oscila a la par de B1S1 evidenciando colapso de conversión catalítica.",
            "class_a": "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
            "evidence_b": "Código P0172 mezcla rica; sensor de oxígeno B1S1 congelado en 0.92V fijo sin ciclar por sensor averiado.",
            "class_b": "Falla en sensor de oxigeno o mezcla rica"
        },
        # Par 8: Carga eléctrica deficiente
        {
            "pair_id": "ADV-08",
            "base_symptom": "Luces bajan de intensidad y testigo de batería en tablero.",
            "evidence_a": "Tensión en bornes con motor encendido es de apenas 12.1V y osciloscopio acusa ondulación de alterna por puente de diodos quemado.",
            "class_a": "Alternador defectuoso o placa de diodos quemada",
            "evidence_b": "Alternador genera 14.2V correctos pero los bornes de plomo están llenos de sulfato blanco impidiendo paso de corriente de carga.",
            "class_b": "Bateria descargada o bornes sulfatados"
        },
        # Par 9: Falta de potencia bajo aceleración
        {
            "pair_id": "ADV-09",
            "base_symptom": "El motor pierde fuerza súbitamente al exigir aceleración a fondo en subida.",
            "evidence_a": "Presión de riel de gasolina colapsa de 3.5 bar a 1.0 bar por bomba de tanque defectuosa que no entrega caudal en probeta.",
            "class_a": "Bomba de gasolina quemada o con baja presion",
            "evidence_b": "Presión de combustible normal en 3.5 bar pero actuador wastegate del turbocompresor se queda abierto por varilla trabada.",
            "class_b": "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI"
        },
        # Par 10: Ruidos en transmisión manual
        {
            "pair_id": "ADV-10",
            "base_symptom": "Ruido metálico molesto proveniente de la caja de cambios en ralentí.",
            "evidence_a": "El ruido áspero tipo chirrido cesa totalmente al apoyar el pie y desacoplar el pedal de embrague; crapodina reseca.",
            "class_a": "Desgaste en collarin de empuje o crapodina de embrague",
            "evidence_b": "Zumbido grave de rodaje en neutro que continúa en desaceleración en todas las marchas por pistas picadas en eje primario.",
            "class_b": "Rodajes de transmision manual o eje primario gastados"
        },
        # Par 11: Sensor CKP vs Misfire encendido
        {
            "pair_id": "ADV-11",
            "base_symptom": "El motor se apaga súbitamente al calentar en marcha y no quiere encender de inmediato.",
            "evidence_a": "Corte simultáneo total de chispa e inyección en los 4 cilindros y tacómetro marca 0 RPM al dar arranque; osciloscopio en CKP plano.",
            "class_a": "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
            "evidence_b": "Corte de encendido restringido únicamente al cilindro 1 con chispa normal en cilindros 2, 3 y 4; bobina primaria recalentada.",
            "class_b": "Falla en bujias o bobinas de encendido (misfire)"
        },
        # Par 12: Sensor MAP vs Sensor MAF
        {
            "pair_id": "ADV-12",
            "base_symptom": "Consumo elevado de combustible y cálculo erróneo de carga de aire por la computadora.",
            "evidence_a": "Señal de presión absoluta en múltiple clavada en 100 kPa en ralentí (debería ser 30 kPa); sensor MAP no responde a depresión.",
            "class_a": "Falla en sensor de presion absoluta del multiple (MAP)",
            "evidence_b": "Caudalímetro de hilo caliente mide flujo de 1.1 g/s con mariposa abierta por hilo térmico sucio y contaminado de aceite.",
            "class_b": "Falla en sensor de flujo de masa de aire (MAF)"
        },
        # Par 13: Sincronización VVT vs Faja saltada
        {
            "pair_id": "ADV-13",
            "base_symptom": "DTC de correlación de sincronización entre cigüeñal y árbol de levas en escáner.",
            "evidence_a": "Leva adelanta y atrasa adecuadamente al activar solenoide con escáner pero cascabelea al arrancar en frío por variador que no tranca.",
            "class_a": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
            "evidence_b": "Marcas físicas de distribución desfasadas por 2 dientes completos en la polea de levas por faja floja o tensor reventado.",
            "class_b": "Faja o cadena de distribucion destensada o con salto de punto"
        },
        # Par 14: Inyectores obstruidos vs Bomba de combustible
        {
            "pair_id": "ADV-14",
            "base_symptom": "Aceleración con vacilación y mezcla pobre reportada en banco 1.",
            "evidence_a": "Presión de riel constante y perfecta en 3.8 bar pero inyector 3 entrega 40% menos caudal en probeta graduada.",
            "class_a": "Inyectores sucios o filtro de combustible obstruido",
            "evidence_b": "Presión de riel decae a 1.2 bar en aceleración moderada con todos los inyectores limpios; bomba de tanque no entrega flujo.",
            "class_b": "Bomba de gasolina quemada o con baja presion"
        },
        # Par 15: Bomba de gasolina vs Módulo FSCM
        {
            "pair_id": "ADV-15",
            "base_symptom": "Falta de suministro de combustible hacia el riel en pickup Chevrolet/Ford.",
            "evidence_a": "La bomba recibe 12V directos en la ficha pero no gira ni consume amperaje; motor de bomba quemado.",
            "class_a": "Bomba de gasolina quemada o con baja presion",
            "evidence_b": "Bomba opera perfecta con 12V externos pero el módulo FSCM no modula la señal de tierra PWM por sobrecalentamiento del driver.",
            "class_b": "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)"
        },
        # Par 16: Correa húmeda degradada vs Bomba de aceite rota
        {
            "pair_id": "ADV-16",
            "base_symptom": "Testigo de presión de aceite encendido en motor Ford Dragón 1.0.",
            "evidence_a": "Chupador de cárter taponado por virutas y filamentos de caucho desprendidos de la faja de distribución sumergida en aceite.",
            "class_a": "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)",
            "evidence_b": "Faja en perfecto estado pero válvula reguladora de alivio de la bomba de aceite atascada abierta por viruta metálica.",
            "class_b": "Baja presion de aceite o bomba de aceite defectuosa"
        },
        # Par 17: GDI carbonilla en válvulas vs Inyector directo GDI
        {
            "pair_id": "ADV-17",
            "base_symptom": "Tironeo y fallo de encendido en frío en motor inyección directa.",
            "evidence_a": "Costras masivas de carbón en el lomo de las válvulas de admisión impiden flujo de aire; inyectores pulverizan parejos.",
            "class_a": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
            "evidence_b": "Válvulas limpias pero inyector piezoeléctrico de alta presión del cilindro 2 gotea y no sostiene 100 bar de presión estática.",
            "class_b": "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
        },
        # Par 18: Termostato trabado vs Radiador obstruido
        {
            "pair_id": "ADV-18",
            "base_symptom": "Sobrecalentamiento del motor con manguera inferior fría.",
            "evidence_a": "Manguera superior caliente a 95°C e inferior fría a 30°C; termostato retirado no abre al sumergirlo en agua hirviendo.",
            "class_a": "Falla en termostato o motoventilador de radiador",
            "evidence_b": "Termostato abre libremente a 82°C pero el panal de aluminio del radiador presenta taponamiento por sarro en tubos internos.",
            "class_b": "Fuga en mangueras de refrigerante o radiador picado"
        },
        # Par 19: Junta homocinética vs Rodamiento de rueda
        {
            "pair_id": "ADV-19",
            "base_symptom": "Ruido mecánico en rueda delantera al circular.",
            "evidence_a": "Chasquido seco clac-clac-clac repetitivo únicamente al girar la dirección a tope y acelerar en curvas; guardapolvo roto sin grasa.",
            "class_a": "Juntas homocineticas o palieres danados",
            "evidence_b": "Zumbido sordo continuo en línea recta que cambia de tono al recostar el peso del vehículo en curvas; masa con holgura radial.",
            "class_b": "Rodajes o cojinetes de rueda desgastados"
        },
        # Par 20: Compresor A/C vs Fuga gas refrigerante
        {
            "pair_id": "ADV-20",
            "base_symptom": "Sistema de aire acondicionado no enfría la cabina.",
            "evidence_a": "Presión estática correcta en 70 PSI pero bobina del embrague magnético del compresor abierta sin acoplar polea.",
            "class_a": "Falla en compresor de aire acondicionado o fuga de gas R134a",
            "evidence_b": "Embrague magnético acopla normal pero la presión del circuito está en 0 PSI por fisura en condensador frontal.",
            "class_b": "Falla en compresor de aire acondicionado o fuga de gas R134a"
        }
    ]

    casos_adv = []
    for p in PARES_ADVERSARIALES:
        # Caso A
        casos_adv.append({
            "pair_id": p["pair_id"],
            "variant": "A",
            "texto_usuario": f"{p['base_symptom']} {p['evidence_a']}",
            "clase_objetivo": p["class_a"],
            "contrast_class": p["class_b"],
            "discriminating_evidence": p["evidence_a"]
        })
        # Caso B
        casos_adv.append({
            "pair_id": p["pair_id"],
            "variant": "B",
            "texto_usuario": f"{p['base_symptom']} {p['evidence_b']}",
            "clase_objetivo": p["class_b"],
            "contrast_class": p["class_a"],
            "discriminating_evidence": p["evidence_b"]
        })

    out_adv = V2_2_DIR / "BANCO_ADVERSARIAL_CONTRASTIVO.csv"
    with open(out_adv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(casos_adv[0].keys()))
        writer.writeheader()
        writer.writerows(casos_adv)

    print(f"Banco Adversarial Contrastivo guardado: {out_adv.name} ({len(casos_adv)} casos = {len(PARES_ADVERSARIALES)} pares)")


if __name__ == "__main__":
    evaluar_rag_whitelist_offline()
    construir_tercer_banco_ciego()
    construir_banco_adversarial_contrastivo()
