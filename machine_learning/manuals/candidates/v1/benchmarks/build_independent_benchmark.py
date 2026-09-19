"""
Generador del Benchmark Independiente de Evaluación RAG (122 consultas).
Cubre las 61 clases vehiculares canónicas y los 7 macro-sistemas.
Incluye variaciones técnicas, coloquiales (WhatsApp de taller), con DTC y sin DTC,
grupos de confusión (A/C, arranque/batería, combustible, vibración, frenos, transmisión, EV/HEV, camiones)
y consultas críticas de seguridad.
Estrictamente independiente: CERO uso de TEST10 y CERO uso de los 60 registros de campo de tesis.
CERO fuga de texto: no copia textualmente ningún párrafo del manual.
"""
import json
import csv
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")

def build_benchmark():
    reconciled_file = PROJECT_ROOT / "RAG_RECONCILIACION_61_CLASES.csv"
    with open(reconciled_file, "r", encoding="utf-8-sig") as f:
        clases_data = list(csv.DictReader(f))

    benchmark_items = []
    q_counter = 1

    # Definición de grupos de confusión y seguridad por clase
    CONFUSION_MAP = {
        0: "STARTUP", 3: "STARTUP", 31: "STARTUP", 49: "STARTUP",  # Alternador, Batería, Arranque, Fuga parásita
        4: "COMBUSTIBLE", 30: "COMBUSTIBLE", 32: "COMBUSTIBLE", 48: "COMBUSTIBLE", 51: "COMBUSTIBLE",  # Bomba, FSCM, Regulador, Common Rail, Inyectores
        12: "BRAKES", 15: "BRAKES", 35: "BRAKES", 36: "BRAKES", 47: "BRAKES", 50: "BRAKES", 60: "BRAKES",  # Pastillas, Discos, ABS, Booster, Fuga hidráulica, Neumático, Válvula aire
        13: "TRANSMISSION", 14: "TRANSMISSION", 24: "TRANSMISSION", 26: "TRANSMISSION", 43: "TRANSMISSION", 56: "TRANSMISSION", 57: "TRANSMISSION", 59: "TRANSMISSION",  # Embrague, Collarín, Bombín, DSG/CVT
        1: "VIBRATION", 9: "VIBRATION", 52: "VIBRATION", 54: "VIBRATION", 58: "VIBRATION",  # Amortiguador, Cremallera, Homocinética, Llantas, Maza
        28: "AC",  # Aire Acondicionado
        11: "EV_HV", 39: "EV_HV", 42: "EV_HV", 44: "EV_HV",  # Batería HV, Regenerativo, Inversor, Refrigeración EV
        22: "TRUCK", 50: "TRUCK", 60: "TRUCK"  # Maxi-Brake, Frenos de aire camión, Secador
    }

    SAFETY_CLASSES = {11, 22, 39, 42, 44, 47, 48, 50, 60}

    # Plantillas de síntomas técnicos y coloquiales para las 61 clases
    # Diseñadas independientemente del corpus
    TEMPLATES = {
        0: [
            ("Luz de batería roja encendida en cuadro, voltaje de carga en 11.8V con motor en marcha", "TECHNICAL", True, ["P0622"]),
            ("maestro el carro se apago en marcha y la bateria es nueva parece que no carga el alternador", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        1: [
            ("Golpeteo seco cloc-cloc en tren delantero al pasar baches, rebote excesivo de carrocería", "WORKSHOP", False, []),
            ("siento que la camioneta rebota mucho como barco en badenes y golpea la suspension", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        2: [
            ("Testigo de presión de aceite titila en ralentí en caliente, presión hidrostática cae a 4 PSI", "TECHNICAL", False, ["P0524"]),
            ("se prende la aceitera cuando calienta el motor en semaforos y suena un taqueteo feo", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        3: [
            ("Voltaje en reposo 10.5V, sulfatación en borne positivo, no retiene carga tras reposo nocturno", "TECHNICAL", False, []),
            ("no arranca en las mananas solo hace click rapido y las luces del tablero se bajan todas", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        4: [
            ("Presión en riel de combustible en cero, no se escucha zumbido de bomba al colocar contacto", "TECHNICAL", True, ["P0087"]),
            ("el carro gira y gira pero no enciende para nada parece que no le llega gasolina", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        5: [
            ("Rueda delantera derecha humea con olor a pastilla quemada, vehículo se carga hacia un lado al rodar", "WORKSHOP", False, []),
            ("un aro delantero se calienta que quema y frena frenado el carro se jala a la derecha", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        6: [
            ("Pestillo de puerta de piloto trabado mecánicamente, no abre ni por dentro ni por fuera con manija", "WORKSHOP", False, []),
            ("la puerta del chofer se quedo atorada y la llave gira en falso no suelta el seguro", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        7: [
            ("Consumo de 1 litro de aceite cada 800 km, humo azulado constante por el escape al acelerar", "TECHNICAL", False, []),
            ("bota humo azul por el escape cuando acelero fuerte y se come el aceite rapidisimo", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        8: [
            ("Código P0420 activo, baja eficiencia en sensor de oxígeno post-catalizador Banco 1", "TECHNICAL", True, ["P0420"]),
            ("tengo check engine prendido me escanearon y salio catalizador tapado pierde fuerza en subida", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        9: [
            ("Juego muerto excesivo en el volante, fuga de líquido hidráulico rojo por fuelles de dirección", "WORKSHOP", False, []),
            ("la direccion timon tiene juego y gotea aceite de direccion por la cremallera", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        10: [
            ("Ralentí inestable oscila entre 500 y 1200 RPM, motor se cala al frenar en detenciones", "TECHNICAL", True, ["P0505"]),
            ("en minimo el motor tiembla y se apaga solito cuando freno en las esquinas", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        11: [
            ("Triángulo rojo maestro activo en Prius, código P0A80 reemplazo de paquete de batería híbrida", "TECHNICAL", True, ["P0A80"]),
            ("en el tablero sale aviso de revisar sistema hibrido y el ventilador de atras sopla a full", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        12: [
            ("Chirrido metálico agudo de fricción al aplicar pedal de freno, espesor de material menor a 2mm", "WORKSHOP", False, []),
            ("suena un chillido fuerte cada vez que toco el freno parece que roza metal con metal", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        13: [
            ("Zumbido tipo rozamiento que desaparece totalmente al pisar el pedal de embrague a fondo", "WORKSHOP", False, []),
            ("suena como un grillo en la caja cuando suelto el embrague y cuando lo piso se quita", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        14: [
            ("El motor revoluciona en 3ra marcha pero la velocidad no incrementa proporcionalmente", "TECHNICAL", False, []),
            ("acelero a fondo ruge el motor pero el carro avanza lentito el embrague patina", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        15: [
            ("Vibración intensa en el pedal de freno y volante al frenar a velocidades superiores a 80 km/h", "WORKSHOP", False, []),
            ("cuando voy rapido en autopista y freno el timon y el pedal tiemblan un monton", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        16: [
            ("Ventana eléctrica del copiloto no sube, se escucha motor girar pero el vidrio está caído", "WORKSHOP", False, []),
            ("se cayo el vidrio de la puerta sono un crujido y ya no levanta con el boton", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        17: [
            ("Burbujas continuas en vaso de expansión de refrigerante, aceite color café con leche en bayoneta", "TECHNICAL", False, []),
            ("el refrigerante hierve y se paso el agua al aceite salio como chocolate la varilla", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        18: [
            ("Ruido de matraca metálica al arrancar en frío, desfase de sincronización árbol de levas DTC P0016", "TECHNICAL", True, ["P0016"]),
            ("suena como cadena suelta al encender en las mananas y tiene check engine prendido", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        19: [
            ("Obstrucción de chupador de aceite por desprendimiento de hilos de correa bañada en aceite", "TECHNICAL", True, ["P0011"]),
            ("motor ford dragon perdio presion de aceite dicen que se deshizo la faja humeda en el carter", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        20: [
            ("Pérdida de potencia y tironeo bajo carga por carbonilla acumulada en válvulas de admisión GDI", "TECHNICAL", True, ["P0300"]),
            ("el carro gdi pierde pique en alta y me dicen que necesita descarbonizado de valvulas", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        21: [
            ("Actuador de cierre centralizado no responde al telemando en puerta trasera izquierda", "WORKSHOP", False, []),
            ("con la alarma bajan 3 seguros pero una puerta de atras no traba se queda abierta", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        22: [
            ("Cámara de freno Maxi-Brake bloqueada por resorte vencido, camión arrastrando eje trasero", "TECHNICAL", False, []),
            ("el camion pesado se quedo amarrado de atras no suelta el freno de resorte de aire", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        23: [
            ("Falta de sobrealimentación, actuador electrónico de wastegate VGT trabado en posición abierta", "TECHNICAL", True, ["P0299"]),
            ("motor tsi entra en modo emergencia y no tiene nada de fuerza codigo p0299 baja presion turbo", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        24: [
            ("Pedal de embrague se queda pegado en el piso, nivel de líquido de frenos bajo en depósito compartido", "WORKSHOP", False, []),
            ("el pedal del embrague se fue hasta el fondo y no regresa no puedo meter ningun cambio", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        25: [
            ("Tironeo fuerte bajo aceleración, código DTC P0301 fallo de encendido cilindro 1 registrado", "TECHNICAL", True, ["P0301"]),
            ("el motor tiembla horrible al acelerar como si anduviera en 3 cilindros bujias o bobina", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        26: [
            ("Falla en actuador electrohidráulico Dualogic / I-Motion, código de presión baja en acumulador", "TECHNICAL", True, ["P1773"]),
            ("la caja automatizada salta a neutro sola en marcha y sale averia de transmision", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        27: [
            ("Circuito abierto en inyector número 3 DTC P0203, pulso de inyección ausente con punta lógica", "TECHNICAL", True, ["P0203"]),
            ("falla cilindro 3 y el mecanico comprobo que no le llega corriente al enchufe del inyector", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        28: [
            ("Presiones de baja y alta anómalas en A/C, clutch electromagnético no acopla al pulsar botón", "TECHNICAL", True, ["B1010"]),
            ("el aire acondicionado sale aire por las rejillas pero no enfria nada compresor no acopla gas r134a", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        29: [
            ("Luz DPF encendida, saturación de hollín sobre 85%, regeneración forzada bloqueada", "TECHNICAL", True, ["P2463"]),
            ("en el tablero sale aviso de filtro de particulas diesel dpf tapado y no deja acelerar", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        30: [
            ("Módulo FSCM recalentado no envía modulación PWM a la bomba de tanque en vehículo Ford", "TECHNICAL", True, ["U0109"]),
            ("se apaga de la nada el auto y el modulo de control de la bomba de gasolina esta hirviendo", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        31: [
            ("Al girar la llave se escucha un clac único metálico pero el motor de combustión no gira", "WORKSHOP", False, []),
            ("le doy arranque hace clac en seco y no gira nada la bateria esta cargada carbones de marcha", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        32: [
            ("Presión en riel excede especificación, combustible presente en manguera de vacío del regulador", "TECHNICAL", False, ["P0172"]),
            ("el escape huele a gasolina cruda y saca bujias negras el regulador de presion esta roto", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        33: [
            ("Sensor de oxígeno Banco 1 Sensor 1 congelado en 0.9V mezcla excesivamente rica DTC P0131", "TECHNICAL", True, ["P0131"]),
            ("humo negro por el tubo de escape gasta mucho combustible sensor de oxigeno marcando mal", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        34: [
            ("Corte repentino de motor en caliente, señal de sensor CKP inductivo intermitente en osciloscopio", "TECHNICAL", True, ["P0335"]),
            ("cuando calienta el motor se apaga de golpe y hasta que no enfria 20 minutos no vuelve a encender ckp", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        35: [
            ("Luz ABS encendida fija en cuadro, código DTC C0035 sensor de velocidad rueda delantera izquierda", "TECHNICAL", True, ["C0035"]),
            ("se prendio el foco amarillo de abs en el tablero y el scanner marca sensor de rueda roto", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        36: [
            ("Pedal de freno extremadamente duro como una piedra, pérdida de asistencia por vacío roto", "TECHNICAL", False, []),
            ("el pedal de freno se puso durisimo como una tabla cuesta un mundo frenar el carro", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        37: [
            ("Dificultad de arranque y relación estequiométrica errónea en sistema Bi-combustible etanol/gasolina", "TECHNICAL", True, ["P0178"]),
            ("carro bi combustible no reconoce mezcla de combustible y tose mucho al prender", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        38: [
            ("Código DTC P0442 fuga menor en sistema EVAP, válvula de purga de canister atascada abierta", "TECHNICAL", True, ["P0442"]),
            ("olor fuerte a vapores de gasolina cerca del tanque y check engine prendido con valvula de purga", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        39: [
            ("Transición brusca entre frenado regenerativo y fricción hidráulica en híbrido Toyota DTC C1203", "TECHNICAL", True, ["C1203"]),
            ("en el hibrido al frenar despacio da un jaloneo raro como si frenara en dos golpes regenerativo", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        40: [
            ("Desfase en árbol de levas de admisión VVT DTC P0011, solenoide OCV trabado con barniz de aceite", "TECHNICAL", True, ["P0011"]),
            ("el motor cascabelea en bajas revoluciones y pierde fuerza falla en sistema vvt-i solenoide sucio", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        41: [
            ("Temperatura de motor sube a zona roja en tráfico detenido, motoventilador no enciende en velocidad alta", "TECHNICAL", False, ["P0217"]),
            ("el carro calienta y bota vapor cuando me paro en el trafico pero corriendo en pista baja temperatura", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        42: [
            ("Vehículo eléctrico no pasa a READY, código DTC P0A1B rendimiento de inversor de tracción IGBT", "TECHNICAL", True, ["P0A1B"]),
            ("el carro hibrido o electrico no prende en ready y marca falla en el inversor de corriente", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        43: [
            ("Zumbido agudo en caja automática, aceite ATF negro con olor a quemado y partículas metálicas", "TECHNICAL", False, []),
            ("la caja patea al meter d o r y el aceite salio negro requemado con olor a quemado", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        44: [
            ("Bomba eléctrica de refrigeración de electrónica de potencia inverter inoperativa DTC P0A93", "TECHNICAL", True, ["P0A93"]),
            ("el deposito chico de enfriamiento del inversor hibrido no tiene turbulencia y recalienta", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        45: [
            ("Silbido agudo tipo fuga de aire a presión bajo carga en turbo diésel, pérdida notable de empuje", "WORKSHOP", False, []),
            ("cuando acelero se oye un soplido fuerte como aire que se escapa por una manguera del turbo", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        46: [
            ("Charco de refrigerante verde bajo el parachoques delantero, fisura en tanque plástico de radiador", "WORKSHOP", False, []),
            ("bota agua verde por adelante y baja el nivel del deposito todas las semanas radiador picado", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        47: [
            ("Pedal de freno se va al fondo lentamente al mantenerlo pisado en detención en pendiente", "TECHNICAL", False, []),
            ("piso el freno en una bajada y se va hundiendo despacito hasta el piso como esponjoso", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        48: [
            ("Presión en riel diésel no alcanza 250 bar durante arranque en Hilux DTC P0087 riel Common Rail", "TECHNICAL", True, ["P0087"]),
            ("camioneta petrolera toyota hilux demora un monton en arrancar common rail presion baja en riel", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        49: [
            ("Consumo parásito de 350 mA en reposo con vehículo bloqueado, descarga de batería en 24 horas", "TECHNICAL", False, []),
            ("si dejo el carro parado dos dias amanece totalmente muerto sin nada de bateria fuga de corriente", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        50: [
            ("Pérdida de presión en manómetro de aire circuito primario de camión, silbido en racores de freno", "TECHNICAL", False, []),
            ("el camion pierde aire por las canerias de frenos en la noche descarga los tanques", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        51: [
            ("Inyectores de gasolina con caudal disparejo en banco de pruebas, filtro de línea colmatado", "WORKSHOP", False, []),
            ("jalonea en alta y cuando acelero parece que se ahoga inyectores sucios o filtro tapado", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        52: [
            ("Chasquido clac-clac-clac continuo en rueda delantera al doblar el volante cerrado acelerando", "WORKSHOP", False, []),
            ("suena un trac trac trac clarito en la llanta delantera cuando giro toda la curva acelerando palier", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        53: [
            ("Brazos limpiaparabrisas no se mueven en ninguna velocidad, motor pluma no recibe alimentación", "WORKSHOP", False, []),
            ("prendo las plumas del parabrisas y no se mueven nada lloviendo y se quedaron paradas", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        54: [
            ("Vibración rítmica en la carrocería entre 90 y 110 km/h que desaparece al reducir velocidad", "TECHNICAL", False, []),
            ("a 100 por hora tiembla todo el piso y el asiento pero el timon esta quieto balanceo de llantas", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        55: [
            ("Compresión de cilindro 2 en 60 PSI, prueba de fugas indica escape de aire por la admisión", "TECHNICAL", False, []),
            ("mecanico midio compresion de motor y un cilindro no tiene nada de presion valvula doblada", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        56: [
            ("Zumbido continuo en caja de cambios mecánica que cambia de tono al acelerar y desacelerar", "WORKSHOP", False, []),
            ("la caja manual tiene un zumbido como turbina en marcha rodamiento de caja o corona zumba", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        57: [
            ("Ruido de arrastre en eje primario de transmisión manual en neutro que desaparece al pisar embrague", "TECHNICAL", False, []),
            ("en neutro la caja hace un ruido ronco suelto y cuando piso el embrague se silencia eje de entrada", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        58: [
            ("Zumbido tipo avión u oscilación sorda que aumenta en curvas hacia un lado específico de la rueda", "WORKSHOP", False, []),
            ("suena un zumbido feo en la rueda izquierda que aumenta mientras mas rapido voy como rodaje roto", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        59: [
            ("Aviso de sobrecalentamiento de transmisión CVT / DSG, patinamiento de variador DTC P0841", "TECHNICAL", True, ["P0841"]),
            ("caja cvt se calienta en subidas de carretera pierde traccion solenoides o aceite degradado", "COLLOQUIAL_WHATSAPP", False, [])
        ],
        60: [
            ("Válvula de freno o cartucho secador de aire APS saturado de aceite en sistema neumático de camión", "TECHNICAL", False, []),
            ("la valvula de descarga del camion escupe aceite con agua y los tanques de aire estan llenos de humedad", "COLLOQUIAL_WHATSAPP", False, [])
        ]
    }

    for idx, c_info in enumerate(clases_data):
        c1_id = int(c_info["ID_C1"])
        c1_name = c_info["CLASE_EXACTA"].strip()
        c1_macro = c_info["MACRO"].strip()

        pair = TEMPLATES.get(c1_id, [
            (f"Falla vehicular en sistema {c1_macro} correspondiente a {c1_name}", "TECHNICAL", False, []),
            (f"consulta de cliente en taller mecanico sobre problema de {c1_name}", "COLLOQUIAL_WHATSAPP", False, [])
        ])

        for q_text, lang_type, has_dtc, dtc_list in pair:
            item = {
                "query_id": f"BENCH_{q_counter:03d}",
                "query": q_text,
                "language_type": lang_type,
                "has_dtc": has_dtc,
                "dtc_codes": dtc_list,
                "confusion_group": CONFUSION_MAP.get(c1_id, "NONE"),
                "is_safety": c1_id in SAFETY_CLASSES,
                "expected_class_id": c1_id,
                "expected_class_name": c1_name,
                "expected_macro": c1_macro
            }
            benchmark_items.append(item)
            q_counter += 1

    out_bench = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/benchmarks/benchmark_dataset.json"
    with open(out_bench, "w", encoding="utf-8") as f:
        json.dump({
            "benchmark_name": "RAG_INDEPENDENT_EVAL_122",
            "total_queries": len(benchmark_items),
            "classes_covered": 61,
            "queries": benchmark_items
        }, f, indent=2, ensure_ascii=False)

    print(f"BENCHMARK INDEPENDIENTE CREADO EXITOSAMENTE:")
    print(f"  Ruta: {out_bench}")
    print(f"  Total consultas: {len(benchmark_items)} (2 por clase x 61 clases)")
    print(f"  Con DTC: {sum(1 for x in benchmark_items if x['has_dtc'])}")
    print(f"  Sin DTC: {sum(1 for x in benchmark_items if not x['has_dtc'])}")
    print(f"  Coloquiales WhatsApp: {sum(1 for x in benchmark_items if x['language_type'] == 'COLLOQUIAL_WHATSAPP')}")
    print(f"  Seguridad crítica: {sum(1 for x in benchmark_items if x['is_safety'])}")

if __name__ == "__main__":
    build_benchmark()
