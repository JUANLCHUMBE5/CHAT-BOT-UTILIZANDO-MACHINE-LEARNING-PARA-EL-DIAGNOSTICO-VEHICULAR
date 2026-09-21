import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data")
LIMPIO_CSV = BASE_DIR / "dataset_sintomas_limpio.csv"
DATASET_CSV = BASE_DIR / "dataset_sintomas.csv"

df_limpio = pd.read_csv(LIMPIO_CSV)
clases_existentes = list(df_limpio["falla"].unique())

def buscar_clase(patron):
    for c in clases_existentes:
        if re.search(patron, c, re.IGNORE_CASE):
            return c
    raise ValueError(f"No se encontro clase para patron: {patron}")

casos_por_categoria = {
    "pastillas": {
        "patron": "Desgaste de pastillas y zapatas",
        "casos": [
            "Al tocar apenas el pedal de freno en bajada se escucha un chillido agudo insoportable como metal con metal y frena poco",
            "Siento que las ruedas de adelante rechinan fuerte cuando piso freno a baja velocidad llegando al semaforo",
            "Mecánico, las llantas delanteras botan un polvo negro espeso pegado al aro y suena un chirrido de lata al frenar",
            "Al frenar despacio en el tráfico de Lima se oye un roce metálico seco en la llanta delantera derecha",
            "El carro frena largo y cuando piso el pedal raspa feo como si las pastillas estuvieran en el puro fierro",
            "Chirría horrible la rueda delantera al frenar en frío y ya se siente una pestaña pronunciada en el borde del disco",
            "Sonido de fricción aguda al frenar en retroceso y el pedal vibra un poco con olor a ferodo quemado",
            "Las zapatas traseras del tambor están silbando al poner el freno de mano o al frenar en pendiente"
        ]
    },
    "fuga_hidraulica": {
        "patron": "Fuga hidraulica o aire en el sistema de frenos",
        "casos": [
            "Piso el pedal de freno y se va despacito hasta el fondo de la alfombra, tengo que bombear para que agarre presión",
            "El pedal se siente como una esponja blanda y veo un charco de líquido aceitoso transparente junto a la rueda trasera",
            "Nivel de líquido de frenos baja en el depósito cada semana y el pedal pierde resistencia al pisarlo parado",
            "Cuando freno de golpe el pedal baja sin resistencia y se encendió el testigo rojo de frenos con signo de exclamación",
            "Purgaron los frenos pero al día siguiente el pedal volvió a ponerse fofo y esponjoso, hay fuga en bombín de rueda",
            "Al presionar el freno no frena casi nada, el pedal toca la lata del piso y hay que bombear tres veces seguidas",
            "Fuga de líquido de frenos por el flexible o cañería oxidada, el pedal cede y no tiene tacto firme"
        ]
    },
    "misfire": {
        "patron": "bujias o bobinas",
        "casos": [
            "El motor corcovea y tiembla horrible en ralentí como en 3 cilindros, parpadea el Check Engine con código P0301",
            "Al meter 3ra y acelerar en subida el carro empieza a jalonear y dar cabezazos como si faltara chispa",
            "Siento explosiones sordas por el escape al acelerar y el motor tiembla todo el tablero, arrojó DTC P0303 cilindro 3",
            "Bujía empapada en carbonilla negra y bobina con chispa saltando por el capuchón de jebe reseco",
            "El auto pierde fuerza de la nada, tironea en baja y la luz de motor parpadea cuando le exijo potencia",
            "Falla de encendido errática P0300 múltiple cilindro, tiembla al prender el aire acondicionado en ralentí",
            "Al salir en primera cascabelea y tiembla feo el motor, se siente que un cilindro no está quemando bien la mezcla",
            "Bobina de encendido partida rajada por calor, no manda chispa a la bujía número 4 y huele a bencina cruda"
        ]
    },
    "bateria": {
        "patron": "Bateria descargada",
        "casos": [
            "Giro la llave y solo se escucha un clac clac metálico rápido del arrancador y las luces del tablero se apagan solas",
            "Por las mañanas el motor da vueltas pesadas y lentas para arrancar y los bornes tienen una masa azul verdosa sulfatada",
            "Dejé el auto parqueado dos días y ya no prende nada, medí la batería con multímetro y marca apenas 11.4 voltios",
            "El reloj y la radio se desconfiguran cada vez que doy marcha porque el voltaje cae a 8V durante el cranking",
            "Borne negativo flojo y sulfatado, no hace buen contacto a masa y a veces el carro parece muerto sin corriente",
            "Pongo contacto, prenden las luces testigos pero al darle a start se cae todo el tablero a negro sin girar motor",
            "Batería vieja inflada a los costados, no retiene carga después de apagar el motor ni media hora"
        ]
    },
    "alineacion": {
        "patron": "Llantas desbalanceadas",
        "casos": [
            "A partir de 80 km/h en la Panamericana el timón empieza a vibrar y zumbar con un hormigueo molesto en las manos",
            "Suelto el timón en pista recta y el carro se jala de golpe hacia la derecha, las llantas delanteras comen por dentro",
            "Desgaste disparejo en el hombro interno del neumático delantero, parece que tuviera caída negativa o divergencia",
            "El volante vibra entre 90 y 110 km/h pero al frenar no vibra nada, solo vibra rodando a velocidad de carretera",
            "Sentí que el carro vibra como tembladera en el piso de la cabina y las llantas de adelante están gastadas en escalera",
            "Al pasar baches el timón se desalinea y queda torcido unos 15 grados hacia la izquierda para ir en línea recta",
            "Vibración rítmica en el asiento y piso a 100 km/h, se le cayó el plomo de contrapeso a la rueda trasera"
        ]
    },
    "amortiguadores": {
        "patron": "Amortiguadores reventados",
        "casos": [
            "Al pasar un rompemuelle o bache la parte delantera rebota como tres veces y golpea seco un clonk abajo",
            "El amortiguador delantero derecho está chorreado de aceite con tierra pegada en el vástago y el carro cabecea",
            "En curvas la camioneta se inclina demasiado como barco y al agarrar un desnivel golpea metal con metal",
            "Sonido de cama vieja rechinando al amortiguar en los resaltos, bujes de trapecio o meseta totalmente rajados",
            "Golpeteo seco toc toc en el lado del copiloto al circular por trocha afirmada o adoquines, terminal y bieleta con juego",
            "La trompa del auto se hunde demasiado al clavar el freno y la cola se levanta de golpe sin amortiguación",
            "Coperas o bases de amortiguador con el jebe despegado, truena al girar la dirección en parqueo"
        ]
    },
    "palieres": {
        "patron": "Juntas homocineticas o palieres",
        "casos": [
            "Al girar todo el timón a la izquierda y acelerar para doblar en una esquina suena un track track track repetitivo",
            "Cubrepolvo de la junta homocinética roto con toda la grasa negra salpicada en la llanta y masa de rueda",
            "Al acelerar fuerte en carretera vibra toda la trompa del auto pero cuando piso el embrague la vibración desaparece",
            "La copa o triceta del semieje tiene holgura excesiva y produce un tironeo y campaneo metálico al salir en 1ra",
            "Sonido de traqueteo continuo cla cla cla en la rueda delantera derecha al hacer giro cerrado en U",
            "Palier con juego radial y axial que produce zapateo en la transmisión al acelerar entre 40 y 60 km/h",
            "Se salió el fuelle de goma del palier y entró arena, la cruceta trituró las canastillas y se traba al girar"
        ]
    },
    "inyectores": {
        "patron": "Inyectores sucios o filtro",
        "casos": [
            "El auto pierde pique y se 'chupa' cuando piso a fondo el acelerador, se siente atrancado como si le faltara combustible",
            "Ralentí irregular e inestable, el motor tose al arrancar en frío y huele a gasolina cruda por mala atomización",
            "Filtro de combustible obstruido con suciedad de grifo, no pasa suficiente caudal a altas revoluciones",
            "Código de falla P0171 mezcla pobre por inyector trabado sucio con barniz en la tobera de inyección",
            "Tironea feo a 2500 RPM al intentar adelantar a otro vehículo en carretera, le falta comida al motor",
            "Microfiltros de inyectores colmatados de sedimentos rojizos de óxido provenientes del tanque de combustible",
            "Inyector goteando en reposo que inunda el cilindro y dificulta el arranque en caliente ahogando el motor"
        ]
    },
    "oxigeno": {
        "patron": "sensor de oxigeno",
        "casos": [
            "Consumo excesivo de gasolina, el carro me está rindiendo menos de 25 km por galón y bota olor picante por el escape",
            "Luz Check Engine encendida fija en tablero con código DTC P0134 señal de sensor de oxígeno sin actividad banco 1",
            "El sensor lambda se quedó clavado en 0.1V y la computadora enriquece la mezcla a lo loco subiendo el Short Term Fuel Trim al 25%",
            "Humo negro con hollín en la cola del escape y la bujía sale carbonizada de negro mate por mezcla hiper rica",
            "DTC P0135 resistencia calefactora de la sonda de oxígeno abierta, tarda mucho en entrar en lazo cerrado Closed Loop",
            "El auto tiembla ligeramente en ralentí caliente y no pasa la revisión técnica por exceso de monóxido de carbono CO y HC",
            "Sensor de relación aire/combustible A/F de banda ancha marcando 4.8V fijo sin oscilar al acelerar"
        ]
    },
    "consumo_aceite": {
        "patron": "Consumo de aceite por desgaste",
        "casos": [
            "Al acelerar fuerte en carretera bota una nube de humo azulado espeso con olor a aceite quemado por el tubo de escape",
            "Cada mil kilómetros tengo que agregarle casi un litro de aceite porque la varilla de nivel queda en la punta inferior",
            "Por las mañanas al encender tira una bocanada de humo azul grisáceo que dura 30 segundos y luego se disipa, retenes de válvula secos",
            "Saco las bujías y las roscas están bañadas en aceite quemado aceitoso pastoso, los aros rascadores de aceite están pegados",
            "Pérdida severa de compresión con soplado de vapores aceitosos por la varilla de medición al acelerar en ralentí",
            "El motor tiene 280 mil km y consume 20W-50 sintético como si fuera combustible, bujías empastadas de carbonilla",
            "Guías de válvula con desgaste excesivo permitiendo que el aceite de culata se filtre a la cámara de combustión"
        ]
    },
    "empaque_culata": {
        "patron": "Empaque de culata soplado",
        "casos": [
            "El depósito de agua burbujea constantemente como olla hirviendo y las mangueras del radiador se ponen duras como piedra",
            "Saco la tapa del aceite y tiene una pasta cremosa blanca tipo mayonesa o café con leche, se pasó el agua al aceite",
            "Bota humo blanco denso y dulce por el escape que no se quita ni calentando el motor, se consumió todo el refrigerante",
            "Recalentó el motor por manguera rota y ahora no arranca bien, mete compresión al circuito de refrigeración y bota el agua",
            "Prueba química con líquido azul detector de CO2 en el vaso de expansión cambió a verde amarillento confirmando fuga de gases",
            "Presión excesiva en el radiador que revienta las tapas plásticas, junta de culata quemada entre cilindro 2 y 3",
            "Pasa agua al cilindro 1 cuando el carro duerme y en la mañana el motor se traba por bloqueo hidráulico momentáneo"
        ]
    },
    "alternador": {
        "patron": "Alternador defectuoso",
        "casos": [
            "Se encendió el testigo de la batería en rojo mientras manejaba y las luces delanteras alumbran con muy poca fuerza",
            "Con el motor encendido medí los bornes de la batería con el voltímetro y marca apenas 12.1 voltios, no sube a 14V",
            "El alternador emite un chillido o silbido magnético caliente y huele a barniz quemado, puente de diodos en cortocircuito",
            "Se apagó la radio, el timón asistido se puso durísimo y luego el motor se detuvo por falta total de voltaje",
            "Voltaje sube a 16.5 voltios al acelerar quemando bombillos de faros y fundiendo fusibles, regulador de voltaje en corto",
            "Al acelerar el alternador zumba fuerte como avión turbohélice por rodamiento delantero con pistas picadas",
            "Escobillas o carbones del alternador totalmente gastados que no hacen contacto con las pistas de cobre del rotor"
        ]
    },
    "cuerpo_aceleracion": {
        "patron": "Cuerpo de aceleracion o valvula IAC",
        "casos": [
            "Al frenar y poner neutro el motor cae de revoluciones bruscamente hasta 400 RPM y se apaga de golpe",
            "El ralentí oscila loco subiendo y bajando entre 1000 y 1800 RPM sin pisar el pedal de acelerador",
            "La mariposa de aceleración electrónica tiene una costra gruesa de carbonilla negra pegada en el contorno del plato",
            "Código DTC P0505 o P2135 con el carro en modo degradado sin responder al acelerador tras lavar el motor",
            "Válvula IAC atascada de hollín no compensa cuando se enciende el aire acondicionado y el motor se ahoga",
            "Al encender en frío por la mañana no mantiene la marcha mínima acelerada y hay que mantener el pie en el acelerador",
            "Garganta de admisión sucia provocando tironeo en baja velocidad y trabamiento del pedal al pisarlo suave"
        ]
    },
    "bomba_gasolina": {
        "patron": "Bomba de gasolina quemada",
        "casos": [
            "Pongo la llave en contacto y no se escucha el zumbido eléctrico característico bzzz en el tanque de combustible",
            "El auto arranca pero a los 10 minutos de marcha empieza a perder fuerza hasta que se apaga y no vuelve a prender hasta que enfría",
            "Medí la presión en el riel de inyectores con manómetro y solo marca 20 PSI cuando debería estar en 45 a 50 PSI",
            "En pendientes largas el motor tironea y se ahoga por falta de caudal de combustible en la bomba de gasolina",
            "Relé de la bomba calienta demasiado y la pila de combustible se corta sola cuando el tanque está con menos de un cuarto",
            "El motor da marcha vigorosa pero no prende por falta total de presión de gasolina en la rampa de inyección",
            "Filtro colador de la bomba de gasolina en el tanque tapado de lodo y arenilla impidiendo la succión normal"
        ]
    },
    "mangueras_refrigerante": {
        "patron": "Fuga en mangueras de refrigerante",
        "casos": [
            "Veo un goteo constante de líquido verde fosforescente debajo del motor y el depósito de reserva se vacía solo",
            "La manguera superior del radiador está hinchada como balón y tiene una microfisura que bota un chorrito fino de vapor",
            "El radiador tiene una fisura en el tanque plástico lateral superior y bota anticongelante caliente al tomar presión",
            "Abrazadera floja en el codo de la bomba de agua dejando escapar refrigerante con olor dulce en el motor",
            "Depósito plástico de expansión cuarteado con fuga por la costura inferior al presurizarse el circuito térmico",
            "Manguera de calefacción picada por roce con la carrocería, dejó el auto sin agua en plena avenida",
            "Radiador tapado externamente con tierra e insectos provocando que suba la temperatura en tráfico"
        ]
    },
    "termostato": {
        "patron": "termostato o motoventilador",
        "casos": [
            "La aguja de temperatura sube al rojo vivo en menos de 10 minutos y el ventilador del radiador no gira para nada",
            "El motoventilador nunca enciende en alta velocidad porque el relé de control está fundido o la resistencia quemada",
            "La manguera superior está hirviendo y la manguera inferior del radiador está totalmente fría, el termostato se trabó cerrado",
            "DTC P0128 temperatura de motor por debajo del umbral de regulación, el termostato se quedó trabado abierto y no calienta",
            "Motor del electroventilador trancado con juego en el buje, vibra el frontal del auto cuando intenta arrancar",
            "Sensor de temperatura de radiador defectuoso no comanda la señal de encendido del ventilador a los 95 grados",
            "Termostato con el sello de jebe roto se descalibró y recalienta el motor al subir pendientes en carretera"
        ]
    },
    "embrague_patina": {
        "patron": "Disco de embrague desgastado",
        "casos": [
            "Acelero a fondo en 3ra marcha, las RPM suben de golpe como bólido a 4000 RPM pero el carro no aumenta de velocidad",
            "Huele a ferodo quemado insoportable en subidas pronunciadas y el embrague patina al soltar el pedal",
            "El pedal de embrague corta muy arriba, casi en el tope superior del recorrido y ya no tiene margen de ajuste",
            "El disco de embrague llegó a los remaches metálicos y resbala contra la prensa y el volante bimasa",
            "Al intentar salir cargado en pendiente el auto tiembla violento y resbala el disco perdiendo tracción",
            "Prensa de embrague destemplada con los diafragmas vencidos, patina en cuanto entra el torque máximo del motor",
            "Embrague patinando por contaminación con aceite de motor debido a fuga del retén de bancada trasero"
        ]
    },
    "frenos_alabeados": {
        "patron": "Discos de freno alabeados",
        "casos": [
            "Al frenar a 90 o 100 km/h en autopista el pedal de freno pulsa fuerte y el volante tiembla violentamente",
            "Discos de freno con alabeo superior a 0.05 mm verificado con reloj comparador de carátula en el buje",
            "Variación de espesor DTV en el disco de freno genera una sacudida rítmica en el pedal al frenar suave",
            "Se rectificaron los discos por debajo del espesor mínimo de seguridad y ahora se calientan y tuercen de inmediato",
            "El volante de dirección baila en las manos al presionar el freno bajando cuestas largas, discos sobrecalentados",
            "Superficie del disco de freno con marcas de temple azuladas y surcos profundos provocando frenado a saltos",
            "Al presionar el freno a alta velocidad parece que las ruedas delanteras rebotaran contra la calzada"
        ]
    }
}

print(f"Cargadas {len(casos_por_categoria)} categorias prioritarias con patrones exactos.")
