casos_bloque3 = {
    "secador_aps": {
        "patron": "secador APS obstruido",
        "casos": [
            "La válvula secadora de aire APS del camión descarga aire cada 10 segundos de forma continua y descontrolada",
            "Sale agua condensada y emulsión aceitosa por los grifos de purga de los tanques de aire húmedo del camión",
            "Cartucho de desecante del secador colmatado de aceite de motor pasado por los aros del compresor de aire",
            "La válvula cuatro vías distribuidora de aire no alimenta el circuito de accesorios por atascamiento de lodo",
            "Válvula de purga automática del secador de aire congelada o trabada abierta botando toda la presión del sistema",
            "Módulo secador electrónico de aire APS arroja código de falla de regeneración del cartucho desecante en el tablero",
            "Manómetro de aire de camión no sube porque la válvula gobernadora del secador descarga a la atmósfera a 4 Bar"
        ]
    },
    "intercooler_turbo": {
        "patron": "mangueras de intercooler o turbocompresor",
        "casos": [
            "Al acelerar a fondo se escucha un silbido fuerte como de aire presurizado escapando ssshhh en el frente",
            "Manguera de silicona del intercooler con una rajadura de 5 centímetros botando vapor de aceite en el radiador",
            "Pérdida severa de potencia en el motor diésel con humareda negra por el escape al acelerar en cuestas",
            "El turbocompresor tiene juego axial excesivo y la propela roza contra la caracola de admisión con sonido metálico",
            "Intercooler fisurado en el tanque plástico inferior por golpe de piedra perdiendo toda la presión de turbo",
            "Abrazadera de la manguera del turbo reventada soltando el ducto de aire y dejando el carro sin potencia de golpe",
            "Turbocompresor chorreando aceite por los sellos laberínticos hacia la admisión y empapando los sensores"
        ]
    },
    "common_rail": {
        "patron": "Common Rail Diesel",
        "casos": [
            "La camioneta diésel se apaga de golpe al acelerar fuerte en carretera con código de baja presión de riel P0087",
            "Arranque prolongadísimo en caliente para encender el motor diésel por fuga excesiva de retorno en inyectores",
            "Bomba de alta presión Common Rail con viruta metálica plateada contaminando todo el riel y las cañerías",
            "Válvula reguladora de caudal SCV / IMV pegada por combustible diésel sucio provocando ralentí inestable",
            "Al realizar la prueba de probetas de retorno de inyectores diésel el inyector número 3 llena la probeta al doble",
            "Pérdida de potencia en camioneta 4x4 diésel, se enciende la luz de filtro de combustible y entra en modo seguro",
            "Presión de riel no pasa de 150 Bar al dar arranque impidiendo que la ECU autorice la apertura de inyectores"
        ]
    },
    "bateria_hv": {
        "patron": "paquete de bateria de alto voltaje",
        "casos": [
            "El auto híbrido arroja código DTC P0A80 reemplazar paquete de batería híbrida en la pantalla central",
            "La batería de tracción de alto voltaje se descarga del 80% al 10% en menos de dos minutos de subida",
            "El ventilador de refrigeración de la batería híbrida debajo del asiento trasero sopla a máxima velocidad sin parar",
            "Diferencia de voltaje superior a 0.3V entre bloques de celdas de la batería de níquel o litio en el escáner",
            "El motor de gasolina del híbrido no se apaga nunca en ralentí porque la batería HV no logra retener la carga",
            "Testigo del triángulo rojo de advertencia maestro encendido en Toyota Prius con degradación de celdas",
            "Resistencia interna de las celdas de la batería de alto voltaje disparada por envejecimiento químico y calor"
        ]
    },
    "inversor_igbt": {
        "patron": "inversor de corriente IGBT o motor electrico",
        "casos": [
            "El vehículo eléctrico o híbrido no pasa a modo READY y arroja DTC P0A94 rendimiento de módulo inversor DC-DC",
            "Fallo en transistor de potencia IGBT del inversor por sobrecalentamiento, olor a componente electrónico quemado",
            "El motor eléctrico de tracción emite un zumbido eléctrico áspero y tironea al iniciar la marcha en pendiente",
            "Aislamiento eléctrico del devanado del estator del motor eléctrico por debajo de 500 MegaOhms con megóhmetro",
            "Bomba de agua eléctrica dedicada al enfriamiento del módulo inversor no funciona y recalienta la electrónica",
            "El convertidor DC-DC del inversor no carga la batería de 12V auxiliar y el vehículo se apaga en marcha",
            "Luz de advertencia del sistema híbrido EV con bloqueo total de la línea de alta tensión por fusible pirotécnico"
        ]
    },
    "frenado_regenerativo": {
        "patron": "frenado regenerativo",
        "casos": [
            "Al soltar el acelerador en el auto híbrido no retiene ni frena con el motor eléctrico, se va libre sin recargar",
            "Transición brusca y golpe seco entre la frenada regenerativa eléctrica y la frenada hidráulica de pastillas",
            "Testigo de freno regenerativo averiado encendido en el cuadro con código C1391 fuga de presión acumulador",
            "Bomba de precarga del cilindro maestro electrohidráulico del sistema híbrido zumba cada 10 segundos continuamente",
            "Pérdida de asistencia en frenado regenerativo con pedal duro y código de falla en el simulador de carrera de pedal",
            "El sistema regenerativo corta repentinamente la recuperación de energía en curvas o sobre asfalto irregular",
            "Sensor de presión del servofreno electrohidráulico del sistema regenerativo con señal fuera de rango"
        ]
    },
    "refrigeracion_ev": {
        "patron": "refrigeracion de bateria/inversor",
        "casos": [
            "Aparece advertencia en pantalla de sobrecalentamiento del circuito de refrigeración del sistema de batería de tracción",
            "Bomba de agua eléctrica sin escobillas del circuito del inversor híbrido trabada por burbujas de aire en el ducto",
            "Filtro de rejilla de la toma de aire de la batería híbrida tapado completamente de pelos, polvo y pelusa",
            "Fuga de líquido refrigerante dieléctrico rosado de baja conductividad en las mangueras del enfriador del inversor",
            "El ventilador soplador de refrigeración de la batería híbrida tiene los álabes trabados y huele a motor eléctrico quemado",
            "Válvula de tres vías del circuito térmico del paquete de baterías trabada impidiendo el enfriamiento activo",
            "Temperatura del paquete de batería de alto voltaje supera los 55 grados Celsius activando reducción de potencia"
        ]
    },
    "sistema_flex": {
        "patron": "sistema Flex / Bi-combustible",
        "casos": [
            "El motor tiembla y tarda muchísimo en arrancar en frío tras cambiar de combustible de gasolina a alcohol o viceversa",
            "La computadora no reconoce el porcentaje de etanol en el tanque y mantiene una mezcla totalmente descalibrada",
            "El inyector del depósito de arranque en frío (tanquinho) no inyecta gasolina al arrancar en las mañanas frías",
            "Código de falla por sensor de contenido de etanol o cálculo virtual de combustible flexible erróneo en la ECU",
            "Consumo disparado y tirones al acelerar porque los parámetros de combustible flex quedaron congelados en 100% etanol",
            "Bomba de combustible del sistema de partida en frío quemada con fusible fundido en vehículos Flex",
            "Válvula solenoide de purga del sistema bi-combustible trabada abierta ahogando los cilindros con nafta"
        ]
    },
    "caja_robotizada": {
        "patron": "caja robotizada Dualogic",
        "casos": [
            "La caja Dualogic o I-Motion salta a Neutral de golpe en medio del tráfico y se niega a meter primera marcha",
            "Bomba electrohidráulica del robot de cambios no levanta presión suficiente de 45 Bar en el acumulador de nitrógeno",
            "El acumulador de presión del robot de marchas perdió la precarga de gas y la bomba prende cada 5 segundos",
            "Sensor de posición de embrague del robot descalibrado, el auto da tirones y cabeceos bruscos al salir en primera",
            "Fuga de aceite hidráulico tutela por las electroválvulas de selección del grupo hidráulico robotizado",
            "Mensaje de avería de transmisión en la pantalla con pitido continuo y la palanca no responde en modo automático",
            "Degradación del disco de embrague seco en caja robotizada provocando olor a quemado y bloqueo de reversa"
        ]
    },
    "correa_aceite": {
        "patron": "correa dentada banada en aceite",
        "casos": [
            "La correa de distribución húmeda bañada en aceite se está deshilachando y desgranando dentro del motor",
            "Pérdida de presión de aceite de motor por chupador y colador del cárter taponado con restos de goma de la faja",
            "Luz de baja presión de aceite se enciende en ralentí en motor Ford 1.0 Dragon o GM 1.2 Turbo por suciedad de correa",
            "Trozos de jebe y fibras de la correa húmeda taparon la bomba de vacío de frenos dejando el pedal de freno durísimo",
            "Degradación química prematura de la faja bañada en aceite por usar lubricante que no cumple la norma WSS Ford o Dexos",
            "La correa bañada en aceite perdió dientes provocando salto de punto de la distribución y doblado de válvulas",
            "Presencia de partículas negras gomosas en el filtro de aceite de motor durante el mantenimiento preventivo"
        ]
    },
    "actuador_vgt": {
        "patron": "actuador de turbocompresor o VGT",
        "casos": [
            "El auto entra en modo Limp Mode y no pasa de 2500 RPM con código DTC P0299 baja presión de turbo en motor TSI",
            "La varilla del actuador electrónico del turbo Wastegate vibra y suena como cascabeleo metálico al desacelerar a 2000 RPM",
            "Actuador electrónico del turbo con engranajes de plástico internos partidos no logra mover los álabes del turbo",
            "DTC P2563 circuito del sensor de posición del actuador de sobrealimentación fuera de rango en motor turbo",
            "Fallo de sobrepresión de turbo DTC P0234 por actuador VGT atascado cerrado por acumulación severa de carbonilla",
            "Motor TSI corta potencia de golpe en autopista al exigirle aceleración a fondo, recupera al apagar y prender el auto",
            "Juego mecánico excesivo en el buje del eje de la compuerta de alivio del turbocompresor provocando pérdida de presión"
        ]
    },
    "descarbonizacion_gdi": {
        "patron": "descarbonizacion e inyeccion directa GDI",
        "casos": [
            "El motor de inyección directa GDI falla y tiembla en frío por acumulación masiva de carbón en las válvulas de admisión",
            "Pérdida progresiva de potencia y cascabeleo en baja por costra de carbonilla dura en las cabezas de las válvulas",
            "Al inspeccionar con boroscopio por los colectores de admisión las válvulas están tupidas de coque aceitoso",
            "Código de falla de encendido múltiple P0300 en frío que desaparece cuando el motor alcanza los 90 grados",
            "Ralentí desparejo e inestable en motores GDI / TSI requiriendo limpieza por proyección de cáscara de nuez (Walnut Blasting)",
            "Deterioro en la mezcla de aire por reducción del diámetro del puerto de admisión debido al carbón pegado",
            "Inyectores de inyección directa empapados de carbonilla en la punta deformando el cono de atomización de gasolina"
        ]
    },
    "sincronizacion_vvt": {
        "patron": "sincronizacion variable de valvulas",
        "casos": [
            "Al arrancar el motor por las mañanas suena un ruido de matraca metálica fuerte durante 2 segundos en el piñón VVT",
            "Código de falla DTC P0011 posición del árbol de levas de admisión sobreavanzada respecto al mapa de la ECU",
            "Solenoide de control de aceite OCV trabado con lodo por aceite degradado no activa el desfasador de levas",
            "El motor tiembla en ralentí y se apaga al llegar a una esquina por variador de avance VVT-i que no retorna a neutro",
            "Microtamiz o malla filtrante del solenoide de distribución variable tapado de barniz impidiendo la presión hidráulica",
            "Desgaste en el engranaje del piñón desfasador Valvetronic o VVT con holgura interna de bloqueo",
            "Presión insuficiente de aceite en la culata impide el correcto avance de levas en aceleración a más de 3000 RPM"
        ]
    },
    "dpf_adblue": {
        "patron": "filtro de particulas DPF.*AdBlue",
        "casos": [
            "Luz de filtro de partículas DPF encendida fija en el tablero con mensaje de regeneración requerida urgente",
            "El vehículo no arranca o indica cuenta regresiva de kilómetros por falla en el sistema dosificador de AdBlue DEF",
            "El filtro DPF colmatado de hollín y cenizas provoca que el motor no pase de 2000 RPM en modo de protección",
            "Sensor de presión diferencial del DPF arroja lecturas irreales de contrapresión por mangueras de silicona rotas",
            "Inyector de urea AdBlue en el escape completamente taponado por cristales blancos de sales de urea solidificadas",
            "Fallo en la resistencia calefactora del depósito de AdBlue impidiendo el descongelamiento del agente reductor",
            "DTC P2463 restricción de hollín en el filtro de partículas diésel sobre el límite máximo admisible"
        ]
    },
    "fscm_bomba": {
        "patron": "modulo de bomba de gasolina FSCM",
        "casos": [
            "El vehículo se apaga de golpe en marcha y no vuelve a prender hasta que se enfría el módulo FSCM bajo el chasis",
            "Módulo de control de bomba de combustible FSCM recalienta y corta el pulso PWM hacia la bomba de gasolina",
            "Carcasa de aluminio del módulo PEM / FSCM corroída o sulfatada por agua y salitre bajo la rueda de repuesto",
            "Código de falla DTC P069E módulo de control de bomba de combustible solicitó iluminación de Check Engine",
            "La bomba de gasolina no recibe voltaje de modulación variable y la presión en el riel cae a cero de forma intempestiva",
            "Conector del arnés eléctrico del módulo de bomba quemado y derretido por alto amperaje continuo",
            "Arranque prolongado intermitente por falla en la señal de retroalimentación de presión del módulo de bomba"
        ]
    }
}
