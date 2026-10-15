"""
Incorporación de ~240 casos clínicos y de taller dirigidos a subsanar
las 7 clases débiles y los principales pares de confusión detectados en la auditoría Fase 1.
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

# Definición de casos dirigidos por clase canónica
CASOS_DIRIGIDOS = {
    # 1. Servofreno (Booster) / Línea de vacío (40 casos)
    # Foco: "pedal duro como piedra", "silbido de aire bajo el tablero", "freno durísimo con motor encendido", "manguera de vacío rajada"
    "Falla en servofreno (booster) o linea de vacio": [
        "pedal de freno duro como palo y no frena casi nada aunque lo pise con las dos piernas",
        "Corolla 2016 pedal de freno durísimo como piedra, ya cambié pastillas pero no tiene asistencia",
        "al pisar el pedal de freno se escucha un soplido o escape de aire por debajo del tablero",
        "Yaris 2018 cuando piso el freno se siente duro y el motor cabecea como si chupara aire",
        "pedal de freno durisimo con motor prendido, parece que no tuviera servofreno",
        "Nissan Sentra 2015 pedal de freno como tabla, hay que pararse encima para que detenga el carro",
        "se escucha un silbido continuo debajo del timon cada vez que piso el pedal de freno",
        "Kia Rio 2017 pedal de freno duro y no baja, el booster no retiene vacio",
        "Hyundai Accent 2018 manguera de vacio que va del multiple al booster de freno esta rajada y el pedal se puso duro",
        "freno duro sin asistencia de vacio, motor tiembla al presionar el freno a fondo",
        "valvula check del booster pegada, pedal de freno sumamente duro",
        "Sentra 2016 se escapa el vacio del booster al frenar y el pedal queda rigido",
        "pedal de freno duro como roca al encender el auto, no hay vacio en el servofreno",
        "Corolla 2017 piso el freno y suena un chiflido de aire por los pedales, el carro no frena bien",
        "diafragma del booster de frenos roto o picado, pedal duro como piedra",
        "Yaris 2019 pedal durisimo, manguera de vacio del servofreno cuarteada y con fuga",
        "freno sin servofreno, pedal extremadamente pesado y distancia de frenado larguisima",
        "Accent 2016 al frenar el pedal se pone como palo y el motor se quiere apagar por entrada de aire falso",
        "Kia Picanto 2018 pedal de freno muy duro, no frena de golpe, booster sin vacio",
        "pedal duro no tiene vacio el booster, al pisar se escucha succión de aire en la pedalera",
        "Toyota Etios 2019 freno sumamente duro como si el motor estuviera apagado",
        "bomba de vacio o manguera de booster rota, pedal duro en camioneta diesel",
        "Versa 2018 fuga de vacio en el servofreno, pedal como roca y silba al frenar",
        "pedal duro rigido, no son pastillas, es el booster de freno que perdio el diafragma",
        "Corolla 2015 el freno no baja, se quedo arriba y durisimo como madera",
        "al pisar el freno chifla aire bajo el tablero y las rpm del motor suben solas",
        "freno durisimo, el servofreno no multiplica la fuerza de frenado",
        "Accent 2017 pedal duro como piedra desde que prendo el motor, valvula antirretorno dañada",
        "pedal de freno no tiene recorrido suave, durisimo y se siente aire soplando en el pie",
        "Yaris mecanico pedal de freno pesado como piedra, pastillas y zapatas son nuevas",
        "silbido en la pedalera al aplicar el freno y pedal excesivamente duro",
        "Kia Rio 2019 falta vacio en el booster, freno muy duro para detener el vehiculo",
        "Sentra 2017 servofreno soplado, pedal duro como una piedra al frenar",
        "freno duro por perdida de vacio del multiple de admision hacia el servofreno",
        "pedal duro como palo, al frenar se acelera un poquito el motor por la fuga de vacio",
        "Versa 2019 no tiene freno suave, durisimo al fondo y silba en la cabina",
        "diafragma interno del servofreno roto, pedal de freno duro y suena pssss al pisar",
        "Toyota Corolla 2014 pedal de freno extremadamente duro, no es bomba ni pastillas, es el booster",
        "Accent 2019 manguera de vacio del booster estrangulada o partida, freno duro",
        "pedal durisimo como bloque de cemento, fuga de vacio en el pulmon del servofreno"
    ],

    # 2. Cierre centralizado eléctrico / actuador de puerta (35 casos)
    # Foco: "con el control remoto no activa", "actuador suena como matraca traca-traca", "pestillos eléctricos no responden", "mando a distancia"
    "Falla electrica del cierre centralizado o actuador de puerta": [
        "con el control remoto no sube ni baja ningun seguro de las puertas",
        "Yaris 2018 el actuador de la puerta del piloto suena como matraca traca traca y no traba el pestillo",
        "presiono el boton del cierre centralizado y no se mueven los pestillos electricos",
        "Kia Rio 2019 el seguro de la puerta trasera derecha no baja con la alarma ni con el mando",
        "motorcito actuador del cierre centralizado se quedo pegado y suena clac clac rapido sin cerrar",
        "Corolla 2017 seguro electrico no responde al control, hay que cerrarlo manualmente con la llave",
        "Hyundai Accent 2016 pestillo electrico del copiloto no tiene fuerza para subir o bajar",
        "fusible del cierre centralizado se quema cada vez que acciono los seguros desde la puerta",
        "Nissan Versa 2018 con la llave manual si cierra pero el actuador electrico no acciona las demas puertas",
        "mando a distancia abre la maletera pero no desactiva el cierre centralizado de las 4 puertas",
        "actuador de pestillo de puerta delantera zumba pero no traba el seguro electrico",
        "Corolla 2016 seguros electricos no bajan al pasar los 20 km por hora, modulo de cierre no envia señal",
        "Accent 2017 puerta del piloto no traba con el boton maestro de los seguros",
        "Sentra 2015 suena un traqueteo electrico dentro del tapiz de la puerta al poner seguro con la alarma",
        "seguros electricos se abren y cierran solos de forma intermitente mientras voy manejando",
        "relevador o rele del cierre centralizado no pega y los pestillos electricos no funcionan",
        "Kia Rio 2018 actuador electrico de la puerta del chofer quemado, no responde al control remoto",
        "Yaris 2017 pestillos electricos muertos, no responden al boton de la consola ni a la llave con chip",
        "actuador de cierre centralizado gira en falso y suena un zumbido sin mover el seguro",
        "Hyundai Elantra 2018 puerta trasera izquierda no desbloquea con el cierre centralizado",
        "modulo del cierre centralizado no recibe señal del control remoto, seguros no accionan",
        "cableado del actuador de puerta cortado en el pasacables del pilar, pestillo electrico inoperativo",
        "Versa 2019 al presionar candado cerrado en el mando solo parpadean las luces pero los seguros no bajan",
        "motor electrico de la cerradura de puerta no tiene fuerza para levantar el pestillo",
        "Corolla 2018 seguro electrico del copiloto se queda trabado a medio camino y la alarma no arma",
        "chapa manual si gira pero el actuador electrico de cierre centralizado no emite ningun sonido",
        "Accent 2018 falla electrica en los pestillos centralizados, no traba ninguna puerta con el switch",
        "actuador de seguro de puerta suena clac clac como si los engranajes estuvieran barridos",
        "Kia Picanto 2018 no abre seguros con control remoto, modulo confort del cierre centralizado sin energia",
        "Sentra 2016 pestillos electricos bajan pero inmediatamente rebotan y se vuelven a abrir",
        "puerta del conductor no manda señal electrica para trabar las otras tres puertas",
        "Yaris 2019 motor del actuador de cierre centralizado quemado, huele a circuito quemado dentro de la puerta",
        "los 4 seguros electricos dejaron de funcionar de un momento a otro, fusible o modulo de cierre",
        "Corolla 2015 el mando a distancia no acciona los seguros, bateria del control nueva",
        "actuador electrico trabado por engranaje interno roto, no abre seguro de puerta con llave ni mando"
    ],

    # 3. Sobrecalentamiento o solenoides en caja automática CVT / DSG (30 casos)
    # Foco: "caja CVT entra en limp mode", "patina banda metálica", "caja DSG traba en cambios pares", "código P0700/P0841", "golpe al pasar a D"
    "Sobrecalentamiento o solenoides en caja automatica CVT / DSG": [
        "caja automatica CVT entra en modo de emergencia limp mode en carretera y no pasa de 40 km por hora",
        "Nissan Sentra 2016 caja CVT recalienta en subida, sale testigo AT y patina al acelerar",
        "caja DSG de doble embrague no mete cambios pares, solo funciona en primera tercera y quinta",
        "Yaris CVT patina la banda metalica sobre las poleas cuando calienta despues de media hora de viaje",
        "Corolla 2017 con caja CVT tiene codigo P0841 de sensor de presion de fluido y zumba al acelerar",
        "golpe fuerte o patada al pasar de neutro o parking a Drive en caja automatica caliente",
        "Kia Rio 2019 caja automatica patina entre segunda y tercera y las revoluciones suben en vacio",
        "temperatura de aceite de transmision automatica CVT sube al maximo y el carro pierde traccion",
        "caja DSG salta a neutro sola en carretera y parpadea la llave inglesa en el tablero",
        "solenoide de presion de linea de caja CVT trancado, el carro arranca con un jalon violento",
        "Sentra CVT testigo de sobrecalentamiento de transmision prendido, carro no avanza hasta que enfria",
        "caja DSG 7 velocidades mecatronica con fuga de presion interna, no engancha reversa ni segunda",
        "Corolla CVT suben las revoluciones a 4000 rpm pero la polea patina y el carro no gana velocidad",
        "Versa 2017 caja automatica da patada fuerte al reducir de tercera a segunda marcha",
        "fluido de caja CVT degradado y quemado, genera vibracion y patinamiento de poleas conicas",
        "codigo P0700 y P0776 en transmision automatica CVT, electrovalvula de control pegada",
        "caja automatica golpea duro al entrar la marcha hacia atras, solenoides de caja con falla",
        "Accent 2018 automatico calienta en trafico y demora en acoplar la marcha directa",
        "caja DSG mecatronica no cambia de marcha, se queda pegada en tercera velocidad",
        "zumbido continuo en caja CVT como turbina de avion y testigo de transmision en tablero",
        "solenoide TCC de bloqueo de convertidor de par pegado, motor se cala al frenar",
        "Sentra 2018 caja CVT patinando en carretera, acelerador a fondo y la velocidad no aumenta",
        "caja de cambios automatica no hace los cambios a tiempo, se pasa de revoluciones y patea",
        "DSG doble embrague con codigo de presion de bomba mecatronica baja, no entra reversa",
        "transmision CVT pierde presion hidraulica al calentar el aceite de caja y se neutraliza",
        "Yaris automatico caja CVT vibra feo al arrancar desde cero por desgaste de conos y correa",
        "caja automatica se desliza como si estuviera en neutro al acelerar en pendientes pronunciadas",
        "testigo de temperatura de caja de cambios automatica prendido, fluido CVT negro y con olor a quemado",
        "solenoide de cambio B atascado en cuerpo de valvulas de caja automatica",
        "Corolla 2016 caja CVT zumba fuerte al rodar a 80 y da tirones intermitentes al acelerar suave"
    ],

    # 4. Caja robotizada Dualogic / I-Motion / Easytronic (25 casos)
    # Foco: "bomba electrohidráulica robotizada no para de sonar", "pasa a neutro sola en el semáforo", "acumulador de presión descargado", "aviso en tablero revisar transmisión"
    "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)": [
        "Fiat con caja Dualogic se pasa a neutro sola cuando me detengo en el semaforo y pita el tablero",
        "bomba electrohidraulica de caja robotizada I-Motion suena cada 10 segundos y no mantiene presion",
        "Volkswagen Gol I-Motion mensaje en pantalla revisar transmision y no entran los cambios",
        "caja Dualogic no quiere meter reversa ni primera en frio, suena la alarma de averia de transmision",
        "acumulador de presion de aceite de caja robotizada pinchado o sin gas, la bomba trabaja continuo",
        "caja Easytronic de Opel/Chevrolet se queda en F en el tablero y el motor no arranca",
        "Dualogic pierde aceite hidraulico por el actuador robotizado y las marchas se traban",
        "caja robotizada pega un tiron muy brusco al pasar de primera a segunda marcha",
        "Fiat Palio Dualogic parpadea la marcha en el cuadro de instrumentos y no acopla velocidad",
        "electrobomba del sistema robotizado Dualogic quemada, no presuriza el circuito hidraulico",
        "caja I-Motion salta a neutro al frenar y hasta que no apago y prendo el carro no entra cambio",
        "rele de la bomba hidraulica de caja robotizada fogueado, bomba no enciende",
        "sensor de posicion de marchas del actuador robotizado dañado, no encuentra el punto muerto",
        "caja Dualogic da error transmision averiada y no sube a tercera marcha",
        "Fox I-Motion dañado el pulmon acumulador de nitrogeno de la caja robotizada",
        "actuador de embrague robotizado descalibrado, tiembla fuertemente al salir en primera",
        "bomba de presion de caja robotizada zumba todo el tiempo con la puerta del chofer abierta",
        "Fiat Cronos Dualogic no acopla la directa ni el modo manual secuencial",
        "caja Easytronic no desacopla el embrague electronico y el motor se cala de golpe al parar",
        "perdida de fluido Tutela CS Speed en robot de transmision Dualogic",
        "caja robotizada no reconoce la palanca selectora de cambios, se queda bloqueada en N",
        "acumulador de presion descargado en caja automatizada, bomba hidraulica se recalienta",
        "I-Motion golpetea en cada cambio de marcha y demora 3 segundos entre cambio y cambio",
        "Dualogic salta neutro en subida y pita la campana del tablero con aviso caja no disponible",
        "falla en electrovalvulas de seleccion de marchas del bloque robotizado"
    ],

    # 5. Bomba de gasolina quemada o con baja presión (30 casos)
    # Foco: "zumbido agudo en el tanque bajo asiento", "presión en riel cae bajo carga", "en subida se ahoga con medio tanque", "no arranca en caliente"
    "Bomba de gasolina quemada o con baja presion": [
        "se escucha un zumbido agudo muy fuerte en el tanque de gasolina debajo del asiento trasero",
        "Yaris 2016 en subida empinada pierde fuerza y se ahoga como si faltara gasolina, tanque a la mitad",
        "medí presion de combustible en la rampa y cae de 45 a 15 psi cada vez que acelero a fondo",
        "Corolla 2015 en frio arranca bien pero cuando calienta y lo apago ya no prende, bomba de gasolina pegada",
        "Kia Rio 2017 motor gira con fuerza pero no enciende, no le llega presion de combustible al riel",
        "Accent 2018 al acelerar a fondo se chupa y pega un jalon feo, presion de bomba insuficiente",
        "bomba de gasolina zumba como avispa debajo de los asientos traseros y el carro tironea en carretera",
        "Nissan Sentra 2016 demora mucho en prender por las mañanas porque la valvula check de la bomba no retiene presion",
        "con medio tanque de gasolina el carro tose y se apaga en curvas o pendientes",
        "presion de gasolina en el manometro se cae a cero al poner carga al motor",
        "Corolla 2014 la bomba de nafta no zumba al dar contacto y el auto no arranca",
        "Yaris 2018 acelero en carretera y el carro se agacha y no pasa de 80 por baja presion de combustible",
        "rele de bomba de gasolina caliente y la bomba deja de enviar combustible despues de una hora de viaje",
        "Accent 2016 motor se queda sin gasolina al exigirle potencia pero regulando funciona parejo",
        "bomba de combustible quemada no activa al girar la llave, fusible y relay estan buenos",
        "filtro de succion de la bomba de gasolina tupido de lodo en el fondo del tanque",
        "Sentra 2017 zumbido insoportable en el tanque de combustible y tironeo bajo aceleracion constante",
        "presion de combustible baja a 20 psi en rampa de inyeccion, bomba defectuosa",
        "Kia Rio 2018 arranca luego de darle arranque 4 o 5 veces, descarga la linea de nafta",
        "bomba de gasolina se calienta y se apaga sola, despues de 20 minutos fria vuelve a prender normal",
        "Versa 2018 pierde pique y aceleracion en subidas porque la bomba no entrega el caudal necesario",
        "Corolla 2016 no hay chispa descartado si tiene chispa pero la rampa de inyectores esta seca sin presion",
        "aforador y modulo de bomba de gasolina con cable recalentado en la tapa del tanque",
        "Yaris 2017 al pasar de 3000 revoluciones el motor se queda sin nafta y empieza a tironear",
        "Accent 2015 la bomba de combustible se queda pegada, le doy golpecitos al tanque y vuelve a prender",
        "presion residual de combustible cae a cero apenas apago el motor, regulador o bomba defectuosa",
        "Kia Picanto 2018 carro tose y pierde potencia en autopista como si se le acabara la gasolina",
        "bomba de gasolina ruidosa y con bajo caudal de litros por hora",
        "Sentra 2015 al pisar el acelerador fuerte se ahoga y en el reloj de presion la aguja cae de golpe",
        "modulo de bomba de gasolina en el tanque no levanta presion de trabajo especificada por el fabricante"
    ],

    # 6. Llantas desbalanceadas o desalineadas (25 casos)
    # Foco: "tiembla timón a 90-110 km/h sin tocar el freno", "se va a la izquierda en recta sin pisar el pedal", "desgaste irregular de banda"
    "Llantas desbalanceadas o desalineadas": [
        "timon vibra fuertemente entre 90 y 110 km por hora en autopista recta sin tocar para nada el pedal de freno",
        "Yaris 2019 vibracion en el volante a 100 km por hora en pista lisa sin pisar los frenos",
        "el carro se va hacia la izquierda solo en linea recta aunque mantenga el timon centrado y derecho",
        "Corolla 2017 cambié llantas nuevas y ahora el volante tiembla en carretera a 95 km por hora",
        "desgaste prematuro de la llanta delantera por el borde interno, comba o convergencia abierta",
        "Kia Rio 2018 a velocidad de 100 km por hora tiembla el timon, al acelerar o bajar a 70 desaparece la vibracion",
        "Accent 2020 despues de caer en un bache el timon quedo ladeado para que el auto ande recto",
        "Nissan Versa 2018 volante vibra a alta velocidad en autopista, sin frenar no es problema de discos",
        "llanta delantera derecha tiene un chichon o deformacion y bambolea el timon a baja velocidad",
        "plomo de balanceo de la rueda delantera se cayo y empezo a vibrar el volante a 90 por hora",
        "Corolla 2016 el auto tira hacia la derecha en carretera plana al soltar el volante unos segundos",
        "Sentra 2017 timon tirita entre 90 y 115 km por hora rodando en carretera sin pisar el freno",
        "desgaste en dientes de sierra en las llantas traseras por mala alineacion del eje posterior",
        "Yaris 2018 vibracion constante en el asiento y en el piso del auto a 100 km por hora sin tocar el freno",
        "alineacion abierta, el vehiculo tiene tendencia a derivar a la izquierda de forma continua",
        "Kia Rio 2019 rueda delantera desbalanceada genera cascabeleo o temblor en el volante en velocidad crucero",
        "Accent 2017 timon chueco para poder mantener el carro en su carril recto",
        "Versa 2019 perdi el contrapeso de la llanta y ahora zumba y tiembla el timon a mas de 80",
        "geometria de suspension delantera desalineada, llantas chillan al doblar a poca velocidad",
        "timon vibra solo entre 90 y 110 en velocidad constante, al frenar no cambia la vibracion",
        "Corolla 2018 camber negativo excesivo gasta la llanta por adentro de manera dispareja",
        "Sentra 2016 alineacion y balanceo necesario, el volante tironea a un costado en pista recta",
        "vibracion en timon que empieza exactamente a los 90 km por hora y se calma pasando los 120",
        "Yaris 2019 balanceo dinamico de las 4 ruedas descalibrado, volante vibra en carretera",
        "llanta delantera ovalada o deformada por golpe produce balanceo de la direccion"
    ],

    # 7. Discos de freno alabeados o desgastados (20 casos)
    # Foco: "vibración en el volante y pedal ÚNICAMENTE al frenar a alta velocidad"
    "Discos de freno alabeados o desgastados": [
        "cuando freno a 80 o 90 km por hora el timon y el pedal de freno vibran y tiemblan fuertemente",
        "Corolla 2017 al pisar el freno bajando una pendiente el volante cabecea y el pedal pulsa",
        "Yaris 2018 sin frenar el carro va suave pero apenas toco el pedal de freno tiembla todo el timon",
        "pedal de freno pulsa o rebota contra el pie unicamente durante la frenada a velocidad de carretera",
        "Kia Rio 2020 discos de freno delanteros alabeados u ondulados por cambio termico al lavar con agua fria",
        "Accent 2018 timon zapatea o vibra feo cada vez que aplico el freno a mas de 70 por hora",
        "Nissan Versa 2019 al frenar suave no pasa nada pero al frenar fuerte a 90 tiembla el volante de lado a lado",
        "discos de freno rectificados en exceso por debajo del espesor minimo de seguridad estan doblados",
        "Sentra 2016 volante vibra de izquierda a derecha unicamente en el momento exacto de frenar",
        "surcos profundos y rebaba pronunciada en los discos de freno delanteros, pedal vibra al frenar",
        "Corolla 2015 alabeo en disco de freno medido con reloj comparador supera 0.08 milimetros",
        "Yaris 2017 freno a fondo y siento pulsaciones en el pedal de freno y vibracion en la columna de direccion",
        "discos de freno recalentados y cristalizados provocan zapateo violento en la frenada",
        "Accent 2017 pisando el freno en bajada el timon sacude de lado a lado por disco deformado",
        "Kia Rio 2019 timon tirita unicamente al tocar el freno, rodando sin frenar va completamente parejo",
        "Versa 2018 discos de freno torcidos provocan golpeteo ritmico en el pedal al frenar a 80",
        "al aplicar los frenos en autopista el volante vibra con fuerza, al soltar el freno deja de vibrar",
        "Corolla 2018 freno de disco delantero alabeado genera trepidacion en el volante",
        "Sentra 2017 pedal de freno tiembla de arriba a abajo al detener el carro desde 90 km por hora",
        "discos de freno con variacion de espesor DTV causan pulsaciones en el pedal de freno"
    ],

    # 8. Fugas de aire o fallos en el sistema de frenos neumático (Camiones) (20 casos)
    # Foco: fuga continua en pulmones/mangueras espirales, aguja de manómetro no sube a 100 psi, fuga audible
    "Fugas de aire o fallos en el sistema de frenos neumtico (Camiones)": [
        "camion diesel pierde presion de aire en los tanques por fuga continua en la manguera espiral del semirremolque",
        "fuga audible de aire constante en el pulmon de freno de estacionamiento trasero del camion",
        "los manometros de presion de aire del camion no suben de 60 psi por fuga continua en cañeria",
        "camion se queda bloqueado o frenado de atras porque no acumula suficiente aire comprimido",
        "manguera de aire de frenos neumático rota debajo del chasis sisea aire todo el tiempo",
        "pulmon de freno roto con diafragma de aire reventado en el eje tractor del camion",
        "fuga de aire en la valvula de pedal de freno de camion, al pisar se escapa toda la presion",
        "tanque de aire primario de frenos de camion se descarga por completo durante la noche",
        "fuga continua de aire por acople rapido de la linea de servicio entre tractor y carreta",
        "compresor de aire de camion trabaja continuo pero la presion de aire en los manometros no llega a 100 psi",
        "manguera roja de emergencia de frenos de camion botando aire a chorros por empaque gastado",
        "camion no desfrena porque los pulmones maxi-brake no reciben presion de aire para soltar resortes",
        "fuga masiva de aire comprimido en tuberia flexible del eje delantero de camion de carga",
        "valvula relé de freno trasero de camion escapa aire constante por el escape inferior",
        "silbido fuerte y continuo de escape de aire en el sistema de frenos neumático de bus interprovincial",
        "perdida de presion neumática en circuito secundario de frenos de camion pesado",
        "cañeria de cobre de aire de frenos picada por rozamiento con el chasis del camion",
        "manometro de aire baja de golpe a 40 psi al aplicar el freno de pedal en camion",
        "empaque de campana de pulmon de freno neumatico roto con fuga de aire evidente",
        "camion pierde aire comprimido y se prende la alarma sonora y chicharra de baja presion en tablero"
    ],

    # 9. Válvula de freno de aire o secador APS obstruido (Camiones) (15 casos)
    # Foco: purga y descarga cíclica del secador, cartucho desecante saturado con aceite, válvula de cuatro vías
    "Vlvula de freno de aire o secador APS obstruido (Camiones)": [
        "valvula del secador de aire APS de camion descarga o purga aire cada 10 segundos sin parar",
        "filtro o cartucho desecante del secador de aire de camion saturado de carbon y aceite de compresor",
        "valvula de descarga o gobernador de presion de aire de camion no corta a los 120 psi y se dispara la de alivio",
        "valvula secadora de aire de camion botando agua y lodo de aceite por la tobera de escape de purga",
        "valvula de proteccion de cuatro circuitos APS de camion trabada, no reparte aire al circuito de suspension",
        "secador de aire neumático congelado o con elemento calefactor quemado en clima frio",
        "gobernador de aire de camion no manda señal de descarga y el secador no realiza la purga automatica",
        "valvula de seguridad del secador de aire de camion disparada por sobrepresion de mas de 13 bar",
        "cartucho de secador de aire lleno de humedad pasa agua a los tanques de frenos de camion",
        "valvula de purga del modulo APS de camion se quedo abierta y no permite que carguen los tanques",
        "sensor de presion del secador electronico APS da falla de procesamiento de aire en camion",
        "valvula reguladora de presion del secador neumático de camion trabada con sarro y suciedad",
        "modulo secador de aire APS de camion no regenera el cartucho desecante y acumula condensacion",
        "descarga constante de aire con emulsion blanca de agua y aceite por el secador de camion",
        "valvula de retencion del secador de aire de camion dañada, no retiene la presion de secado"
    ]
}

def main():
    print(f"Cargando dataset actual desde: {DATA_PATH}")
    df_actual = pd.read_csv(DATA_PATH, encoding="utf-8")
    total_inicial = len(df_actual)
    print(f"Total registros actuales: {total_inicial}")

    clases_existentes = list(df_actual["falla"].unique())
    def resolver_clase(nombre_clave: str) -> str:
        if nombre_clave in clases_existentes:
            return nombre_clave
        for c in clases_existentes:
            if "APS" in nombre_clave and "APS" in c:
                return c
            if "neum" in nombre_clave and "neum" in c:
                return c
        raise ValueError(f"No se pudo resolver clase: {nombre_clave}")

    nuevos_registros = []
    sintomas_existentes = set(df_actual["sintoma"].str.lower().str.strip())

    for falla_clave, lista_sintomas in CASOS_DIRIGIDOS.items():
        falla_canonica = resolver_clase(falla_clave)
        agregados_clase = 0
        for s in lista_sintomas:
            s_limpio = s.strip()
            if s_limpio.lower() not in sintomas_existentes:
                nuevos_registros.append({
                    "sintoma": s_limpio,
                    "falla": falla_canonica
                })
                sintomas_existentes.add(s_limpio.lower())
                agregados_clase += 1
        print(f"  + {agregados_clase:>2} casos agregados para: '{falla_canonica}'")

    print(f"\nTotal nuevos casos generados: {len(nuevos_registros)}")
    df_nuevos = pd.DataFrame(nuevos_registros)
    
    # Concatenar y guardar
    df_actualizado = pd.concat([df_actual, df_nuevos], ignore_index=True)
    # Deduplicar
    df_actualizado = df_actualizado.drop_duplicates(subset=["sintoma"]).reset_index(drop=True)
    total_final = len(df_actualizado)
    
    print(f"Total registros luego de incorporar y deduplicar: {total_final} (incremento neto: +{total_final - total_inicial})")
    df_actualizado.to_csv(DATA_PATH, index=False, encoding="utf-8")
    print(f"Dataset guardado exitosamente en: {DATA_PATH}")

if __name__ == "__main__":
    main()
