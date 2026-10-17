"""Conjunto de 65 escenarios conversacionales independientes para la validación E2E de Fase 10.

Cubre rigurosamente:
- Conversaciones largas (10 a 20 turnos).
- Peruanismos y modismos automotrices (cascabeleo, cabecea, tironea, se chupa, zapatea, está chancho).
- Interrupciones, pausas temporales y retomas conversacionales.
- Correcciones explícitas de vehículo, síntomas o condiciones de falla.
- Manejo de falta de herramientas y comprobaciones imposibles.
- Registro metrológico de mediciones físicas (voltaje, presión, compresión).
- Detección OOD y abstención segura de 6 familias.
- Cierre formal del caso e inicio de caso nuevo sin contaminación cruzada.
REGLA METODOLÓGICA: 100% independiente, NO utiliza los 60 casos reservados de tesis.
"""

from __future__ import annotations

from typing import Any, Dict, List

CASOS_CONVERSACIONALES_65: List[Dict[str, Any]] = [
    # =========================================================================
    # GRUPO 1: CONVERSACIONES LARGAS Y EXHAUSTIVAS (10 A 15 TURNOS) - 10 CASOS
    # =========================================================================
    {
        "id": "F10_LARGO_01_COROLLA_MISFIRE",
        "grupo": "LARGO",
        "descripcion": "Corolla con misfire intermitente en aceleración y diagnóstico guiado completo de 12 turnos",
        "turnos": [
            "Buenas tardes maestro, tengo un Toyota Corolla 2015 placa ABC-123",
            "El motor cabecea feo cuando intento acelerar en subida",
            "En ralentí se siente un temblor leve, pero al pisar a fondo se chupa",
            "Le metí el escáner y me arrojó código P0302",
            "Espérame un rato maestro, voy a desmontar la bobina del cilindro 2 para revisarla",
            "Ya regresé, continuemos",
            "Intercambié la bobina 2 con la del cilindro 1 a ver si se traslada la falla",
            "Volví a acelerar y ahora el escáner me marca P0301",
            "Saqué la bujía 1 y la veo con desgaste normal y color café claro",
            "Medí la compresión del cilindro 2 y me da 175 psi parejo",
            "Entonces definitivamente es la bobina que se cruzó internamente, ¿cierto?",
            "Muchas gracias maestro, voy a pedir el repuesto original y cerramos la revisión",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "no_repite_pregunta": True,
            "conserva_placa": "ABC-123",
            "conserva_dtc": "P0302",
            "detecta_pausa": True,
            "cierre_adecuado": True,
        },
    },
    {
        "id": "F10_LARGO_02_YARIS_REFRIGERACION",
        "grupo": "LARGO",
        "descripcion": "Toyota Yaris con temperatura oscilante en tráfico pesado (11 turnos)",
        "turnos": [
            "Hola, mi carro es un Toyota Yaris placa BCD-234",
            "En el tráfico de Lima la aguja de temperatura empieza a subir casi hasta la H",
            "Cuando agarro la Panamericana y el carro corre, la aguja baja a su nivel normal",
            "No hierve el depósito pero veo que el ventilador no arranca en primera velocidad",
            "Dame 10 minutos, voy a puentear el relé del electroventilador a ver si gira",
            "Listo amigo, ya regresé al taller",
            "Puentee el relé y el electroventilador prende con fuerza y gira sin problemas",
            "Revisé los fusibles principales y todos tienen continuidad",
            "Medí voltaje en el conector del sensor de temperatura y le llegan los 5V de referencia",
            "Con el termostato tengo dudas porque la manguera inferior del radiador se siente tibia mientras la superior quema",
            "Excelente orientación técnica, procederé con el reemplazo del termostato",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "BCD-234",
            "detecta_pausa": True,
            "sin_preguntas_redundantes": True,
        },
    },
    {
        "id": "F10_LARGO_03_NISSAN_TIIDA_ARRANQUE",
        "grupo": "LARGO",
        "descripcion": "Nissan Tiida con demora prolongada de arranque en caliente (10 turnos)",
        "turnos": [
            "Doc, tengo un Nissan Tiida placa CDE-345 en mi taller",
            "Por las mañanas arranca al toque, a la primera vuelta de llave",
            "El problema es cuando el cliente lo apaga tras manejar una hora; para volver a prender demora hasta 6 segundos dando estárter",
            "Las bujías son nuevas de iridio originales",
            "Le conecté el manómetro de presión de combustible en el riel",
            "En contacto marca 45 psi y el motor prende bien",
            "Lo apagué y a los 10 minutos la presión en el riel cayó a cero completamente",
            "Un toque, voy a estrangular la manguera de retorno para ver por dónde fuga la presión",
            "Seguimos, al estrangular no retiene, lo que indica que gotea un inyector o la válvula check de la bomba en el tanque no retiene",
            "Desmonté el riel y comprobé que el inyector 3 gotea una gota cada 15 segundos",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "CDE-345",
            "conserva_medicion_presion": True,
        },
    },
    {
        "id": "F10_LARGO_04_HILUX_1KD_HUMO_NEGRO",
        "grupo": "LARGO",
        "descripcion": "Toyota Hilux 1KD con humo negro y pérdida de fuerza en subidas (11 turnos)",
        "turnos": [
            "Maestro, Hilux 2018 placa DEF-456",
            "Bota humo negro denso por el escape cada vez que piso a fondo en segunda y tercera",
            "Siento que el turbo no sopla como antes, está chancho",
            "No tengo código de avería activo en el tablero, el check engine está apagado",
            "Revisé visualmente las mangueras del intercooler",
            "Encontré una abrazadera floja y un poco de aceite rezumando",
            "Espérame un ratito que voy a desmontar el intercooler para lavarlo y probar fugas con humo",
            "Ya volví, le metí 1.5 bar de presión al intercooler sumergido y no tiene fisuras",
            "Limpié el caudalímetro MAF con spray dieléctrico especial",
            "Salí a probar en pista y la presión de boost sube a 1.2 bar normal, el humo negro desapareció",
            "El diagnóstico quedó resuelto, era la fuga en la abrazadera del intercooler",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "DEF-456",
            "detecta_pausa": True,
        },
    },
    {
        "id": "F10_LARGO_05_SPORTAGE_FRENOS_PULSACION",
        "grupo": "LARGO",
        "descripcion": "Kia Sportage con fuerte vibración en el pedal al frenar en bajada (10 turnos)",
        "turnos": [
            "Tengo una Kia Sportage 2016 placa EFG-567",
            "Al bajar por cerro y pisar el pedal de freno, el timón y el pedal zapatean bastante",
            "En plano a baja velocidad casi no se nota",
            "Las pastillas de freno las cambiaron hace 1 mes y tienen 80% de vida",
            "Desmonté la llanta delantera derecha para revisar el disco",
            "Al tacto no tiene ceja pero se ven manchas tornasoladas azuladas",
            "Le coloqué el reloj comparador con base magnética en la pista de frenado",
            "Al girar la masa marca 0.12 mm de alabeo lateral, superando el límite de 0.05 mm",
            "El disco está alabado por exceso de temperatura",
            "Procederé a rectificar los dos discos delanteros y cambiar líquido de frenos DOT 4",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "EFG-567",
            "sin_repetir_preguntas": True,
        },
    },
    {
        "id": "F10_LARGO_06_SUZUKI_SWIFT_RALENTI_INESTABLE",
        "grupo": "LARGO",
        "descripcion": "Suzuki Swift que oscila de rpm al encender el aire acondicionado (10 turnos)",
        "turnos": [
            "Buenas, auto Suzuki Swift placa FGH-678",
            "El motor oscila en ralentí, sube y baja entre 600 y 1100 rpm",
            "Empeora drásticamente cuando enciendo el aire acondicionado, se apaga si no lo acelero",
            "Bujías y filtro de aire limpios y en buen estado",
            "Dame unos minutos que voy a revisar si la mariposa electrónica tiene carbón",
            "Ya estoy de vuelta amigo",
            "El cuerpo de aceleración tenía una costra gruesa de carbonilla negra alrededor de la mariposa",
            "Lo limpié con carbuclean y trapo de microfibra con el switch cerrado",
            "Realicé el procedimiento de reaprendizaje de ralentí dejando calentar a 90 grados",
            "Quedó parejito en 750 rpm con y sin aire acondicionado, falla corregida",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "detecta_pausa": True,
            "conserva_placa": "FGH-678",
        },
    },
    {
        "id": "F10_LARGO_07_CHEVROLET_SAIL_CONSUMO_ACEITE",
        "grupo": "LARGO",
        "descripcion": "Chevrolet Sail con humo azul en desaceleración y consumo excesivo (10 turnos)",
        "turnos": [
            "Tengo en taller un Chevrolet Sail placa GHI-789",
            "Consume casi 1 cuarto de aceite de motor cada 1,500 kilómetros",
            "Al acelerar a fondo no bota casi nada, pero cuando suelto el acelerador y vuelvo a acelerar bota una bocanada de humo azul",
            "La válvula PCV es nueva original",
            "Medí compresión en seco y da 170 psi parejo en los 4 cilindros",
            "Hice la prueba de compresión húmeda con unas gotas de aceite y no varió la presión",
            "Eso descarta anillos pegados o desgaste de cilindros",
            "Lo más probable son los retenes de válvulas resecos o juego en las guías",
            "Voy a cambiar los retenes de válvula sin desmontar la culata usando aire a presión",
            "Quedó asentado el plan de trabajo con el cliente, cerramos consulta",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "GHI-789",
        },
    },
    {
        "id": "F10_LARGO_08_HONDA_CIVIC_RUIDO_SUSPENSION",
        "grupo": "LARGO",
        "descripcion": "Honda Civic con chasquido metálico al girar el timón a tope (10 turnos)",
        "turnos": [
            "Honda Civic 2014 placa HIJ-890",
            "Al salir de una curva cerrada o al doblar en una esquina con aceleración suena un traqueteo clac clac clac constante",
            "Si voy en línea recta en pista rota no suena nada",
            "El ruido proviene de la rueda delantera izquierda",
            "Levanté el carro con la gata hidráulica para inspeccionar el palier",
            "El guardapolvo exterior de la junta homocinética está completamente roto y botó toda la grasa grafitada",
            "Al mover el palier con la mano tiene juego axial y radial excesivo",
            "La junta homocinética exterior se desgastó por falta de lubricación y entrada de tierra",
            "Reemplazaremos la punta de palier completa y colocaremos grasa nueva con guardapolvo de neoprene",
            "Listo amigo, caso cerrado",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "HIJ-890",
        },
    },
    {
        "id": "F10_LARGO_09_HYUNDAI_TUCSON_ALTERNADOR",
        "grupo": "LARGO",
        "descripcion": "Hyundai Tucson con testigo de batería que parpadea sobre 3000 rpm (10 turnos)",
        "turnos": [
            "Hyundai Tucson placa IJK-901",
            "En ralentí la luz de batería en el tablero está apagada",
            "Pero cuando acelero en carretera a más de 3000 rpm el testigo de batería empieza a parpadear",
            "La faja de accesorios está bien tensada y no patina ni chilla",
            "Puse el multímetro en bornes de batería con el motor en ralentí",
            "En ralentí marca 14.1 voltios constante",
            "Le pedí a mi ayudante que acelere a 3500 rpm y el voltaje sube bruscamente a 15.8 voltios",
            "Eso es sobrecarga peligrosa para la ECU y la batería",
            "El regulador de voltaje del alternador está averiado",
            "Desmontaremos el alternador para cambiar la placa reguladora y carbones",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "IJK-901",
            "conserva_mediciones_voltaje": True,
        },
    },
    {
        "id": "F10_LARGO_10_MAZDA_3_BOMBA_GASOLINA",
        "grupo": "LARGO",
        "descripcion": "Mazda 3 que se apaga intempestivamente al rodar 20 minutos (10 turnos)",
        "turnos": [
            "Vehículo Mazda 3 placa JKL-012",
            "El carro rueda perfecto unos 15 o 20 minutos y de pronto pierde aceleración y se apaga",
            "Si espero 15 minutos vuelve a arrancar como si nada hubiera pasado",
            "Cuando se apaga tiene chispa en las 4 bujías",
            "Instalé manómetro de combustible en serie para monitorear en ruta",
            "Al principio la presión marca 50 psi estable",
            "A los 18 minutos de prueba la presión empezó a caer progresivamente: 40 psi, 30 psi, 15 psi hasta que se apagó el motor",
            "Toqué el tanque de gasolina por abajo y la bomba eléctrica se siente excesivamente caliente",
            "El motor de la bomba de gasolina se dilata por temperatura y pierde caudal térmico",
            "Reemplazaremos la bomba de combustible completa con su filtro canastilla",
        ],
        "verificaciones": {
            "min_turnos": 10,
            "conserva_placa": "JKL-012",
        },
    },

    # =========================================================================
    # GRUPO 2: PERUANISMOS Y MODISMOS AUTOMOTRICES (10 CASOS)
    # =========================================================================
    {
        "id": "F10_JERGA_01_SE_CHUPA",
        "grupo": "JERGA",
        "turnos": [
            "Mi carro se chupa feo en subida cuando acelero",
            "Sí, es un Toyota Yaris 2012",
        ],
        "termino_clave": "se chupa",
        "sistema_esperado": "combustible_admision",
    },
    {
        "id": "F10_JERGA_02_CABECEA",
        "grupo": "JERGA",
        "turnos": [
            "Maestro, el motor cabecea en ralentí como si fuera a apagarse",
            "Bujías y cables revisados",
        ],
        "termino_clave": "cabecea",
        "sistema_esperado": "encendido",
    },
    {
        "id": "F10_JERGA_03_CASCABELEA",
        "grupo": "JERGA",
        "turnos": [
            "Cascabelea fuerte cuando piso fondo en tercera con gasolina de 90",
            "En frío no suena",
        ],
        "termino_clave": "cascabelea",
        "sistema_esperado": "combustion_detonacion",
    },
    {
        "id": "F10_JERGA_04_ZAPATEA",
        "grupo": "JERGA",
        "turnos": [
            "El embrague zapatea al arrancar en primera marcha",
            "Solo pasa al soltar el pedal",
        ],
        "termino_clave": "zapatea",
        "sistema_esperado": "embrague",
    },
    {
        "id": "F10_JERGA_05_CHANCHO",
        "grupo": "JERGA",
        "turnos": [
            "El carro está chancho para picar, no reacciona al pedal",
            "Filtro de aire nuevo",
        ],
        "termino_clave": "chancho",
        "sistema_esperado": "potencia_aceleracion",
    },
    {
        "id": "F10_JERGA_06_ZUMBA",
        "grupo": "JERGA",
        "turnos": [
            "La rueda delantera zumba como avión cuando paso de 60 km/h",
            "Al doblar a la izquierda el zumbido aumenta",
        ],
        "termino_clave": "zumba",
        "sistema_esperado": "rodamiento_rueda",
    },
    {
        "id": "F10_JERGA_07_CHILLIDO_CLAVAR",
        "grupo": "JERGA",
        "turnos": [
            "Chillido agudo al clavar los frenos en semáforo",
            "Frena parejo pero suena metálico",
        ],
        "termino_clave": "chillido",
        "sistema_esperado": "frenos",
    },
    {
        "id": "F10_JERGA_08_TIRONEA",
        "grupo": "JERGA",
        "turnos": [
            "El carro tironea en carretera cuando mantengo 80 km/h fijo",
            "Acelero a fondo y se le quita",
        ],
        "termino_clave": "tironea",
        "sistema_esperado": "inyeccion_mezcla",
    },
    {
        "id": "F10_JERGA_09_MOTOR_FLOJO",
        "grupo": "JERGA",
        "turnos": [
            "Siento el motor flojo, no tiene pique al adelantar camiones",
            "Consume un poco más de combustible de lo normal",
        ],
        "termino_clave": "motor flojo",
        "sistema_esperado": "potencia",
    },
    {
        "id": "F10_JERGA_10_NO_EMPAREJA",
        "grupo": "JERGA",
        "turnos": [
            "El motor tiembla y no empareja ni en caliente",
            "Huele bastante a gasolina cruda por el tubo de escape",
        ],
        "termino_clave": "no empareja",
        "sistema_esperado": "combustion_inyeccion",
    },

    # =========================================================================
    # GRUPO 3: INTERRUPCIONES, PAUSAS Y RETOMAS (8 CASOS)
    # =========================================================================
    {
        "id": "F10_PAUSA_01_ESPERAME",
        "grupo": "PAUSA",
        "turnos": [
            "Toyota Corolla tiembla al frenar placa KLM-123",
            "Espérame un rato maestro, voy a levantar la rueda",
            "Ya regresé, continuemos",
            "El disco tiene ceja pronunciada al pasarle la uña",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True, "mantiene_placa": "KLM-123"},
    },
    {
        "id": "F10_PAUSA_02_ESTOY_REVISANDO",
        "grupo": "PAUSA",
        "turnos": [
            "Nissan Sentra no enciende placa LMN-234",
            "Estoy revisando los fusibles en la caja del motor",
            "Seguimos, el fusible de ignición de 15A estaba quemado",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True},
    },
    {
        "id": "F10_PAUSA_03_AHORITA_TE_DIGO",
        "grupo": "PAUSA",
        "turnos": [
            "Hyundai i10 bota humo negro placa MNO-345",
            "Ahorita te digo, estoy sacando el filtro de aire",
            "Ya volví, el filtro está taponado de tierra negra",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True},
    },
    {
        "id": "F10_PAUSA_04_DAME_10_MINUTOS",
        "grupo": "PAUSA",
        "turnos": [
            "Kia Picanto pedal de embrague duro placa NOP-456",
            "Dame 10 minutos que voy a purgar el bombín",
            "Continuemos donde quedamos, al purgar salió líquido oscuro con burbujas",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True},
    },
    {
        "id": "F10_PAUSA_05_UN_TOQUE",
        "grupo": "PAUSA",
        "turnos": [
            "Chevrolet Aveo recalienta placa OPQ-567",
            "Un toque, voy a chequear si el radiador tiene fugas",
            "Listo amigo ya regresé, el tanque plástico superior tiene una fisura",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True},
    },
    {
        "id": "F10_PAUSA_06_AGUANTA_AHI",
        "grupo": "PAUSA",
        "turnos": [
            "Suzuki Grand Vitara golpeteo al pasar baches placa PQR-678",
            "Aguanta ahí un ratito que voy a subir el carro al elevador",
            "Ya regresé, los bujes de la trapecio están rajados",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True},
    },
    {
        "id": "F10_PAUSA_07_DAME_UN_MOMENTO",
        "grupo": "PAUSA",
        "turnos": [
            "Mazda 2 luces parpadean placa QRS-789",
            "Dame un momento, voy a medir con el tester",
            "Seguimos donde estábamos, el alternador está botando 14.2V parejo",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True},
    },
    {
        "id": "F10_PAUSA_08_YA_ESTOY_DE_VUELTA",
        "grupo": "PAUSA",
        "turnos": [
            "Honda CR-V no entra retroceso placa RST-890",
            "Espérate que estoy verificando el nivel de aceite de caja",
            "Ya estoy de vuelta, el nivel está en el mínimo y el aceite huele a quemado",
        ],
        "verificaciones": {"detecta_espera": True, "detecta_retoma": True},
    },

    # =========================================================================
    # GRUPO 4: CORRECCIONES DE INFORMACIÓN Y ACLARACIONES (8 CASOS)
    # =========================================================================
    {
        "id": "F10_CORR_01_OTRO_VEHICULO",
        "grupo": "CORRECCION",
        "turnos": [
            "Buenas tardes, tengo un Yaris que no arranca",
            "Me equivoqué, disculpa, no era un Yaris, era una camioneta Toyota Hilux",
            "Da vuelta el motor con fuerza pero no inyecta diesel",
        ],
        "verificaciones": {"corrige_modelo": "Hilux"},
    },
    {
        "id": "F10_CORR_02_CONDICION_TERMICA",
        "grupo": "CORRECCION",
        "turnos": [
            "Mi auto falla al arrancar en frío por las mañanas",
            "No, lo que quise decir es que falla en caliente cuando lo vuelvo a prender",
            "En frío arranca a la primera",
        ],
        "verificaciones": {"corrige_condicion": "caliente"},
    },
    {
        "id": "F10_CORR_03_PLACA_ERRONEA",
        "grupo": "CORRECCION",
        "turnos": [
            "Auto Corolla placa AAA-111 con cascabeleo",
            "Corrijo la placa amigo, me equivoqué de tarjeta, es ABC-999",
            "Cascabelea en tercera subiendo cerro",
        ],
        "verificaciones": {"corrige_placa": "ABC-999"},
    },
    {
        "id": "F10_CORR_04_RUIDO_UBICACION",
        "grupo": "CORRECCION",
        "turnos": [
            "Siento un ruido en la rueda delantera izquierda",
            "Revisando bien con mi mecánico, el ruido viene de la rueda trasera derecha",
            "Es un chillido al frenar suave",
        ],
        "verificaciones": {"ajusta_contexto": True},
    },
    {
        "id": "F10_CORR_05_NO_ERA_BUJIA",
        "grupo": "CORRECCION",
        "turnos": [
            "Creo que son las bujías que están fallando",
            "Retiro lo dicho, las bujías son nuevas las revisé hace 10 minutos y están limpias",
            "La falla es que se corta la corriente del inyector 1",
        ],
        "verificaciones": {"ajusta_hipotesis": True},
    },
    {
        "id": "F10_CORR_06_COMBUSTIBLE_TIPO",
        "grupo": "CORRECCION",
        "turnos": [
            "Tengo un Hyundai que jalonea en gasolina",
            "Aclaro, el carro es a gasolina y GLP, pero jalonea únicamente cuando conmuta a GLP",
            "En gasolina acelera parejito sin falla",
        ],
        "verificaciones": {"detecta_glp_ood": True},
    },
    {
        "id": "F10_CORR_07_AÑO_VEHICULO",
        "grupo": "CORRECCION",
        "turnos": [
            "Nissan Sentra 1998 a carburador no regula",
            "Perdón, me equivoqué de año, es un Nissan Sentra 2012 B16 inyectado",
            "La válvula IAC no compensa al prender luces",
        ],
        "verificaciones": {"corrige_año": "2012"},
    },
    {
        "id": "F10_CORR_08_TESTIGO_SIMBOLO",
        "grupo": "CORRECCION",
        "turnos": [
            "Se prendió el foco de la aceitera en el tablero",
            "Mirando con atención el tablero no es la aceitera, es el foco de la batería roja",
            "El carro se fue apagando lentamente de noche",
        ],
        "verificaciones": {"corrige_sistema": "electrico_carga"},
    },

    # =========================================================================
    # GRUPO 5: COMPROBACIONES IMPOSIBLES / SIN HERRAMIENTAS (8 CASOS)
    # =========================================================================
    {
        "id": "F10_SIN_HERR_01_NO_ESCANER",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Toyota Yaris tiembla y prende check engine",
            "No tengo escáner en este momento, estoy de viaje en provincia",
            "¿Qué prueba básica puedo hacer sin escáner?",
        ],
        "verificaciones": {"bloquea_escaner": True, "ofrece_plan_b": True},
    },
    {
        "id": "F10_SIN_HERR_02_NO_MANOMETRO",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Nissan Tiida pierde fuerza en alta",
            "No tengo manómetro de presión de combustible a la mano",
            "Solo tengo herramientas de mano básicas y multímetro",
        ],
        "verificaciones": {"bloquea_manometro": True},
    },
    {
        "id": "F10_SIN_HERR_03_NO_COMPRESIMETRO",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Kia Rio humo azul al acelerar",
            "No cuento con medidor de compresión en mi taller",
            "Puedo revisar bujías y sacar la tapa de balancines",
        ],
        "verificaciones": {"bloquea_compresimetro": True},
    },
    {
        "id": "F10_SIN_HERR_04_NO_MULTIMETRO",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Hyundai Accent no da arranque",
            "No tengo tester ni multímetro aquí",
            "Las luces del techo prenden pero al dar llave se apagan por completo",
        ],
        "verificaciones": {"bloquea_multimetro": True},
    },
    {
        "id": "F10_SIN_HERR_05_NO_ELEVADOR",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Suzuki Swift golpe seco abajo al acelerar",
            "No tengo fosa ni elevador para ver por debajo",
            "Puedo agacharme con una linterna o usar la gata de emergencia",
        ],
        "verificaciones": {"bloquea_elevador": True},
    },
    {
        "id": "F10_SIN_HERR_06_EN_CARRETERA",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Estoy varado en la carretera con una Hilux que calienta",
            "No tengo herramientas ni repuestos aquí, solo agua embotellada",
            "¿Puedo abrir la tapa del radiador caliente?",
        ],
        "verificaciones": {"alerta_seguridad_termica": True},
    },
    {
        "id": "F10_SIN_HERR_07_NO_OSCILOSCOPIO",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Mazda 3 corte de inyección intermitente",
            "No tengo osciloscopio automotriz para ver la señal del CKP",
            "¿Puedo medir la resistencia de la bobina del sensor con multímetro?",
        ],
        "verificaciones": {"bloquea_osciloscopio": True},
    },
    {
        "id": "F10_SIN_HERR_08_PROPIETARIO_SIN_CONOCIMIENTO",
        "grupo": "SIN_HERRAMIENTAS",
        "turnos": [
            "Soy el dueño del carro y no sé nada de mecánica",
            "No sé cómo sacar una bujía ni dónde queda la bobina",
            "Solo quiero saber si es peligroso manejar así hasta el taller",
        ],
        "verificaciones": {"adapta_lenguaje_dueño": True},
    },

    # =========================================================================
    # GRUPO 6: MEDICIONES TÉCNICAS EXACTAS / METROLOGÍA (8 CASOS)
    # =========================================================================
    {
        "id": "F10_METRO_01_VOLTAJE_BATERIA",
        "grupo": "METROLOGIA",
        "turnos": [
            "Tengo un Toyota Corolla que demora en dar marcha",
            "Medí voltaje con multímetro digital: marca 12.2V en reposo",
            "Al darle arranque el voltaje cae hasta 9.1V",
        ],
        "verificaciones": {"registra_voltajes": True},
    },
    {
        "id": "F10_METRO_02_PRESION_RIEL",
        "grupo": "METROLOGIA",
        "turnos": [
            "Nissan Sentra pierde potencia",
            "Medí la presión en el riel con manómetro y marca 42 psi en ralentí",
            "Al acelerar a fondo la presión se cae a 25 psi",
        ],
        "verificaciones": {"registra_presion_psi": True},
    },
    {
        "id": "F10_METRO_03_COMPRESION_CILINDROS",
        "grupo": "METROLOGIA",
        "turnos": [
            "Hyundai Elantra motor tiembla en baja",
            "Tomé compresión en caliente: cilindro 1 170 psi, cilindro 2 95 psi, cilindro 3 170 psi, cilindro 4 165 psi",
        ],
        "verificaciones": {"detecta_desbalance_cilindro_2": True},
    },
    {
        "id": "F10_METRO_04_RESISTENCIA_BOBINA",
        "grupo": "METROLOGIA",
        "turnos": [
            "Kia Rio misfire en cilindro 3",
            "Medí resistencia en el primario de la bobina y marca 0.9 ohmios",
            "En el secundario me marca circuito abierto infinito en la escala de 20k",
        ],
        "verificaciones": {"registra_ohmios": True},
    },
    {
        "id": "F10_METRO_05_TEMPERATURA_LASER",
        "grupo": "METROLOGIA",
        "turnos": [
            "Chevrolet Sail calienta en subidas",
            "Con pirómetro láser medí la manguera superior en 98 grados centígrados",
            "La manguera inferior apenas marca 45 grados centígrados",
        ],
        "verificaciones": {"registra_temperatura": True},
    },
    {
        "id": "F10_METRO_06_PRESION_ACEITE",
        "grupo": "METROLOGIA",
        "turnos": [
            "Toyota Yaris prende luz de presión de aceite al frenar",
            "Instalé manómetro mecánico en el bulbo: marca 18 psi en ralentí frío",
            "Al calentar a 90 grados la presión cae a 4 psi en ralentí",
        ],
        "verificaciones": {"registra_presion_aceite": True},
    },
    {
        "id": "F10_METRO_07_VACIO_ADMISION",
        "grupo": "METROLOGIA",
        "turnos": [
            "Suzuki Grand Vitara ralentí oscilante",
            "Conecté vacuómetro al múltiple: marca 14 pulgadas de mercurio con aguja vibrando rápido",
        ],
        "verificaciones": {"registra_vacio": True},
    },
    {
        "id": "F10_METRO_08_CORRIENTE_ARRANQUE",
        "grupo": "METROLOGIA",
        "turnos": [
            "Hilux motor de arranque pesado",
            "Con pinza amperimétrica DC medí el consumo de arranque: jala 280 amperios",
        ],
        "verificaciones": {"registra_amperaje": True},
    },

    # =========================================================================
    # GRUPO 7: ABSTENCIÓN SEGURA OOD DE 6 FAMILIAS (7 CASOS)
    # =========================================================================
    {
        "id": "F10_OOD_01_AIRBAG_SRS",
        "grupo": "OOD",
        "turnos": [
            "Se prendió la luz roja de Airbag SRS en mi Nissan Versa tras un bache",
        ],
        "esperado_ood": "AIRBAG_SRS",
    },
    {
        "id": "F10_OOD_02_GNV_GLP",
        "grupo": "OOD",
        "turnos": [
            "El reductor de gas GNV de quinta generación congela y no pasa a gas",
        ],
        "esperado_ood": "GLP_GNV",
    },
    {
        "id": "F10_OOD_03_DIRECCION_EPS",
        "grupo": "OOD",
        "turnos": [
            "El timón eléctrico EPS se puso durísimo y prendió el testigo del volante con signo de exclamación",
        ],
        "esperado_ood": "DIRECCION_EPS",
    },
    {
        "id": "F10_OOD_04_RED_CAN_BCM",
        "grupo": "OOD",
        "turnos": [
            "La linea CAN bus sin comunicacion con ECM y se caen los modulos",
        ],
        "esperado_ood": "RED_CAN_INMOVILIZADOR_CENTRAL",
    },
    {
        "id": "F10_OOD_05_HVAC_COMPUERTAS",
        "grupo": "OOD",
        "turnos": [
            "La compuerta de mezcla del climatizador bizona tiene tac-tac en tablero y no sale calefaccion",
        ],
        "esperado_ood": "HVAC_COMPUERTA_MEZCLA_CALEFACCION",
    },
    {
        "id": "F10_OOD_06_TRANSMISION_DSG",
        "grupo": "OOD",
        "turnos": [
            "Caja automática DSG de doble embrague da tirones bruscos y salta el aviso de sobrecalentamiento de embragues",
        ],
        "esperado_ood": "TRANSMISION_NO_CUBIERTA_CONVERTIDOR",
    },
    {
        "id": "F10_OOD_07_INMOVILIZADOR_CHIP",
        "grupo": "OOD",
        "turnos": [
            "El candadito parpadea en el tablero y el chip de la llave no reconoce",
        ],
        "esperado_ood": "RED_CAN_INMOVILIZADOR_CENTRAL",
    },

    # =========================================================================
    # GRUPO 8: CICLO DE VIDA, CIERRE Y TRANSICIÓN A NUEVO CASO (6 CASOS)
    # =========================================================================
    {
        "id": "F10_CICLO_01_CIERRE_Y_NUEVO_CARRO",
        "grupo": "CICLO_VIDA",
        "turnos": [
            "Toyota Yaris placa XYZ-100 tiembla al frenar",
            "Eran los discos alabados, muchas gracias maestro, cerramos el diagnóstico",
            "Ahora por favor atiende este otro vehículo: tengo un Nissan Sentra placa NNN-200 que no prende",
        ],
        "verificaciones": {
            "cierra_primer_caso": True,
            "inicia_segundo_caso": True,
            "aislamiento_placas": ("XYZ-100", "NNN-200"),
        },
    },
    {
        "id": "F10_CICLO_02_NUEVO_DIAGNOSTICO_MISMO_CARRO",
        "grupo": "CICLO_VIDA",
        "turnos": [
            "Corolla placa COR-001 ya le cambié la batería y prende al toque, caso cerrado",
            "Maestro, en este mismo Corolla ahora quiero revisar los frenos porque chillan al parar",
        ],
        "verificaciones": {
            "resetea_sistema_activo": True,
            "nuevo_sistema": "frenos",
        },
    },
    {
        "id": "F10_CICLO_03_GRACIAS_Y_DESPEDIDA",
        "grupo": "CICLO_VIDA",
        "turnos": [
            "Hilux placa TOY-777 recalienta en ralentí",
            "Cambié el termostato y quedó perfecto a 88 grados",
            "Muchas gracias por la ayuda maestro, que tenga buen día",
        ],
        "verificaciones": {"detecta_despedida": True},
    },
    {
        "id": "F10_CICLO_04_DOS_SINTOMAS_SEPARADOS",
        "grupo": "CICLO_VIDA",
        "turnos": [
            "Kia Rio placa KIA-555 chillido en faja de alternador",
            "Tensé la faja y se le quitó el chillido, asunto resuelto",
            "Ahora tengo otra consulta: el pedal de freno baja hasta el fondo",
        ],
        "verificaciones": {"transicion_limpia": True},
    },
    {
        "id": "F10_CICLO_05_CANCELAR_Y_REINICIAR",
        "grupo": "CICLO_VIDA",
        "turnos": [
            "Buenas, estaba consultando por un Hyundai",
            "Cancela esa consulta anterior por favor, quiero empezar de cero",
            "Tengo un Suzuki Swift placa SUZ-123 que vibra en carretera",
        ],
        "verificaciones": {"reinicio_explicito": True, "nueva_placa": "SUZ-123"},
    },
    {
        "id": "F10_CICLO_06_CONSULTA_MEMORIA_HISTORIAL",
        "grupo": "CICLO_VIDA",
        "turnos": [
            "Toyota Yaris placa YAR-999 misfire en cilindro 4 por bobina abierta",
            "¿Qué habíamos diagnosticado para este carro hace un momento?",
        ],
        "verificaciones": {"lectura_memoria": True},
    },
]
