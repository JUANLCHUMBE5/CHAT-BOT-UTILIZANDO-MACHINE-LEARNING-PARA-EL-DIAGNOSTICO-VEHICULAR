"""Generador sintético de aumento lingüístico automotriz peruano.

Compila variaciones controladas de síntomas con lenguaje coloquial. Estos
registros no son observaciones reales de taller y nunca se admiten directamente
como muestra oficial ni como correcciones confirmadas por mecánicos.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

# Base exhaustiva de sistemas de taller con asignación directa a la taxonomía canónica
SISTEMAS_TALLER = [
    # 1. MOTOR MECÁNICO Y DISTRIBUCIÓN
    {
        "sistema": "Motor",
        "subcomponente": "Bujías y bobinas",
        "categoria_oficial": "Falla en bujias o bobinas de encendido (misfire)",
        "codigo_falla": "MOTOR_001",
        "requiere_escaner": "SI",
        "prueba": "Lectura de conteo de misfire en escáner, prueba de chispómetro e inspección de electrodos",
        "dtc": "P0301",
        "inicios": ["Al subir una cuesta con pasajeros", "Acelerando en tercera a bajas vueltas", "Al exigir torque en carretera", "Al pisar el acelerador saliendo"],
        "sintomas": ["el carro empieza a temblar feo y pierde pique", "parece que anduviera en 3 pistones", "jalonea bruscamente al acelerar", "el motor cabecea y pierde fuerza"],
        "condiciones": ["y parpadea el check engine en el tablero", "con olor a gasolina sin quemar en el tubo de escape", "y el motor vibra mucho en ralentí", "pero en neutro se siente parejo"]
    },
    {
        "sistema": "Motor",
        "subcomponente": "Retenes y anillos",
        "categoria_oficial": "Consumo de aceite por desgaste de anillos o retenes",
        "codigo_falla": "MOTOR_002",
        "requiere_escaner": "NO",
        "prueba": "Inspección de depósitos húmedos en bujías, prueba de compresión húmeda y prueba de fugas de cilindro",
        "dtc": "N/A",
        "inicios": ["Al encender el carro tras horas apagado", "Al acelerar después de frenar con motor en bajada", "Saliendo de un semáforo largo", "En las mañanas al dar marcha"],
        "sintomas": ["escupe una bocanada visible de humo azulado", "despide humo azul por el escape por unos 20 segundos", "quema aceite visiblemente al primer arranque", "bota humo gris azulado por el escape"],
        "condiciones": ["pero luego de avanzar un par de cuadras el humo desaparece", "y la varilla marca consumo de medio cuarto de aceite por mes", "sin que se sienta pérdida de fuerza en carretera", "dejando residuo aceitoso en la cola del escape"]
    },
    {
        "sistema": "Motor",
        "subcomponente": "Empaque de culata",
        "categoria_oficial": "Empaque de culata soplado o danado",
        "codigo_falla": "MOTOR_003",
        "requiere_escaner": "NO",
        "prueba": "Prueba química de CO2 en refrigerante y medición de compresión entre cilindros adyacentes",
        "dtc": "N/A",
        "inicios": ["Al revisar el depósito de agua", "En las mañanas al arrancar", "Manejando en subidas pronunciadas", "Al sacar la tapa del aceite"],
        "sintomas": ["el refrigerante tiene burbujas y parece café con leche", "bota humo blanco espeso con olor dulce por el escape", "consume agua sin dejar charco y recalienta rápido", "la compresión pasa al sistema de enfriamiento"],
        "condiciones": ["y el motor falla en ralentí como si perdiera compresión", "y las mangueras del radiador se ponen infladas y duras", "encontrando grasa lechosa pegada en la tapa", "con sobrecalentamiento constante"]
    },
    {
        "sistema": "Motor",
        "subcomponente": "Bomba de aceite / Coladera",
        "categoria_oficial": "Baja presion de aceite o bomba de aceite defectuosa",
        "codigo_falla": "MOTOR_004",
        "requiere_escaner": "NO",
        "prueba": "Instalación de manómetro hidráulico en el puerto del bulbo de aceite y desmontaje del cárter",
        "dtc": "N/A",
        "inicios": ["Al calentar bien el motor en tráfico", "Estando en ralentí detenido en semáforo", "Al caer las RPM a menos de 900", "Con motor caliente en mínimo"],
        "sintomas": ["parpadea la aceitera roja en el tablero", "se prende el testigo de presión de aceite en mínimo", "suena un zumbido seco en la parte baja del motor", "golpetea la bancada en ralentí"],
        "condiciones": ["pero apenas piso un poquito el acelerador la luz se apaga", "y el nivel de aceite en la varilla está completamente lleno", "aumentando el ruido metálico si se mantiene en ralentí", "con aceite perdiendo viscosidad"]
    },
    {
        "sistema": "Motor",
        "subcomponente": "Faja o cadena de tiempo",
        "categoria_oficial": "Faja o cadena de distribucion destensada o con salto de punto",
        "codigo_falla": "MOTOR_005",
        "requiere_escaner": "SI",
        "prueba": "Comprobación de marcas de distribución y osciloscopio correlacionando señales CKP y CMP",
        "dtc": "P0016",
        "inicios": ["Luego de cambiar de marcha bruscamente", "De un momento a otro al acelerar", "Al encender después de un tirón", "Tras sonar un latigazo en el motor"],
        "sintomas": ["el motor perdió casi toda la fuerza y tiembla disparejo", "cuesta mucho arrancar y petardea por la admisión o escape", "el motor cabecea fuerte y suena fuera de punto", "arranca desfasado y tose"],
        "condiciones": ["y prendió el testigo de check engine fijo", "con el escape sonando como ahogado y desfasado", "sin aceleración en pendientes", "con desfase de levas respecto a cigüeñal"]
    },
    {
        "sistema": "Motor",
        "subcomponente": "Inyección Directa GDI",
        "categoria_oficial": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
        "codigo_falla": "MOTOR_006",
        "requiere_escaner": "SI",
        "prueba": "Inspección con boroscopio de toberas de admisión y monitoreo de ajustes de combustible STFT/LTFT",
        "dtc": "P0300",
        "inicios": ["En motores GDI con más de 60,000 km", "Al acelerar a fondo en bajas revoluciones", "En frío al encender el auto"],
        "sintomas": ["sufre de tirones intermitentes en aceleración", "las válvulas de admisión están saturadas de carbón negro", "pierde aceleración progresiva y ralentí áspero", "tiembla en mínimo por estrangulamiento de aire"],
        "condiciones": ["sin código de falla específico en bujías", "pero con carbonilla dura en las cabezas de válvula", "mejorando temporalmente a altas RPM"]
    },
    {
        "sistema": "Motor",
        "subcomponente": "VVT / VVT-i",
        "categoria_oficial": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
        "codigo_falla": "MOTOR_007",
        "requiere_escaner": "SI",
        "prueba": "Prueba de activación de solenoide OCV con escáner, limpieza de microfiltro VVT y revisión de presión",
        "dtc": "P0011",
        "inicios": ["Al pasar de 3000 RPM en carretera", "Con motor caliente en autopista", "Al exigir respuesta rápida"],
        "sintomas": ["no entra la distribución variable y se siente achanchado", "suena una matraca metálica en la tapa de balancines al acelerar", "se queda pegado el variador de fase VVT", "pierde potencia a altas revoluciones"],
        "condiciones": ["arrojando código de posición de árbol de levas retardado", "y el solenoide OCV presenta barniz de aceite pegado", "con código P0011 o P0012 en el escáner"]
    },
    {
        "sistema": "Motor",
        "subcomponente": "Correa bañada en aceite",
        "categoria_oficial": "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)",
        "codigo_falla": "MOTOR_008",
        "requiere_escaner": "NO",
        "prueba": "Inspección visual del ancho de correa por la boca de llenado de aceite y desmontaje de chupona de cárter",
        "dtc": "P0524",
        "inicios": ["En motores Ford Dragon 1.0 o Chevrolet Onix Turbo", "Al llegar a los 70,000 km", "Al encenderse la luz de aceite"],
        "sintomas": ["la correa húmeda se está deshilachando y botando caucho", "la coladera de la bomba de aceite se tapó con viruta de correa", "perdió presión de lubricación por restos de faja"],
        "condiciones": ["con el aceite lleno de polvillo negro de caucho", "y advertencia de baja presión de aceite en curvas", "requiriendo reemplazo inmediato del kit"]
    },

    # 2. INYECCIÓN Y COMBUSTIBLE
    {
        "sistema": "Combustible",
        "subcomponente": "Inyectores y filtros",
        "categoria_oficial": "Inyectores sucios o filtro de combustible obstruido",
        "codigo_falla": "COMBUSTIBLE_001",
        "requiere_escaner": "SI",
        "prueba": "Prueba de goteo, balance de flujo y atomización en banco de inyectores con ultrasonido",
        "dtc": "P0300",
        "inicios": ["Al intentar encender el auto en caliente", "En marcha mínima", "Al acelerar a fondo saliendo", "Al rodar despacio"],
        "sintomas": ["arranca ahogado con fuerte olor a gasolina cruda", "el motor cabecea y arroja humo negro por el escape", "las bujías salen completamente empapadas de combustible negro", "el carro tironea en bajas revoluciones"],
        "condiciones": ["registrando consumo de combustible excesivo", "y el auto tironea en bajas revoluciones", "con desbalance en el pulso de inyección", "y bujías carbonizadas"]
    },
    {
        "sistema": "Combustible",
        "subcomponente": "Bomba de gasolina",
        "categoria_oficial": "Bomba de gasolina quemada o con baja presion",
        "codigo_falla": "COMBUSTIBLE_002",
        "requiere_escaner": "NO",
        "prueba": "Conexión de manómetro en riel de inyectores midiendo presión sostenida (45-60 psi) y caudal",
        "dtc": "P0087",
        "inicios": ["En el primer arranque de la mañana", "Al querer prender el carro tras dejarlo parqueado", "Al girar la llave", "Con tanque bajo de gasolina"],
        "sintomas": ["da vueltas el motor de arranque pero no agarra", "tengo que dar 3 o 4 intentos prolongados para que arranque", "el motor tose antes de prender", "se apaga en marcha al calentar la pila de bomba"],
        "condiciones": ["pero una vez que enciende el resto del día trabaja parejo", "y la bomba en el tanque no emite el zumbido típico de presurización al poner contacto", "con batería en perfecto estado", "cayendo la presión en riel a cero"]
    },
    {
        "sistema": "Combustible",
        "subcomponente": "Cuerpo de aceleración / IAC",
        "categoria_oficial": "Cuerpo de aceleracion o valvula IAC sucia",
        "codigo_falla": "COMBUSTIBLE_003",
        "requiere_escaner": "SI",
        "prueba": "Limpieza profunda del cuerpo de aceleración, prueba de actuador IAC y reaprendizaje electrónico de mariposa",
        "dtc": "P0505",
        "inicios": ["Al llegar a un semáforo y poner neutro", "Al soltar el pedal del acelerador", "Al prender el aire acondicionado estando parado", "Al frenar en una esquina"],
        "sintomas": ["el motor se apaga de golpe si no lo mantengo acelerado", "las revoluciones oscilan subiendo y bajando entre 500 y 1200 RPM", "el mínimo está totalmente descalibrado", "tiembla el motor y se cae el ralentí"],
        "condiciones": ["pero acelerando en carretera no falla absolutamente nada", "y tiembla toda la carrocería en las paradas", "con el conducto de bypass cubierto de carbonilla", "estabilizándose solo al acelerar"]
    },
    {
        "sistema": "Combustible",
        "subcomponente": "Sensor de oxígeno",
        "categoria_oficial": "Falla en sensor de oxigeno o mezcla rica",
        "codigo_falla": "COMBUSTIBLE_004",
        "requiere_escaner": "SI",
        "prueba": "Graficación de curva de voltaje oscilante (0.1V a 0.9V) en escáner y prueba de resistencia calefactora",
        "dtc": "P0130",
        "inicios": ["En el uso diario en ciudad", "Al rodar en velocidad crucero", "En tráfico moderado", "Al revisar el consumo semanal"],
        "sintomas": ["el auto consume el doble de gasolina que de costumbre", "despide un olor muy fuerte a combustión ácida por el escape", "el motor se nota achanchado y pesado", "hollín negro en el silenciador"],
        "condiciones": ["con el check engine encendido fijo en el panel", "y la punta del tubo de escape manchada de hollín negro", "sin presentar tirones violentos", "con sensor ciclando lento"]
    },
    {
        "sistema": "Combustible Diésel",
        "subcomponente": "Common Rail Diésel",
        "categoria_oficial": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
        "codigo_falla": "COMBUSTIBLE_005",
        "requiere_escaner": "SI",
        "prueba": "Monitoreo de presión en riel diésel con escáner (mínimo 250 bar en arranque) y prueba de retorno de inyectores",
        "dtc": "P0087",
        "inicios": ["En camionetas Hilux o camiones diésel", "Al pisar fondo en subida con carga", "En arranques en frío matutinos"],
        "sintomas": ["cuesta un montón que encienda y tira humo blanco o negro", "se limita la potencia y entra en modo de emergencia limp-mode", "no levanta más de 2000 RPM en carretera"],
        "condiciones": ["marcando baja presión de combustible diésel en rampa", "y retorno excesivo en 2 inyectores piezoeléctricos", "con testigo de filtro o inyección prendido"]
    },
    {
        "sistema": "Combustible",
        "subcomponente": "Módulo FSCM / PEM",
        "categoria_oficial": "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)",
        "codigo_falla": "COMBUSTIBLE_006",
        "requiere_escaner": "SI",
        "prueba": "Verificación con osciloscopio de señal PWM de control hacia la bomba y escaneo de módulo de control de combustible",
        "dtc": "U0109",
        "inicios": ["En autos Ford o Chevrolet americanos", "Luego de pasar por baches o lluvia", "El carro se apaga de golpe andando"],
        "sintomas": ["no llega corriente a la bomba a pesar de que el fusible está bien", "el motor se detiene como si se cortara la corriente general", "la bomba no activa por falta de comando del FSCM"],
        "condiciones": ["con código U0109 de pérdida de comunicación con módulo de bomba", "y el módulo ubicado bajo el chasis presenta sulfato o corrosión", "sin presión en el riel"]
    },
    {
        "sistema": "Combustible",
        "subcomponente": "Sistema Flex Bi-combustible",
        "categoria_oficial": "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)",
        "codigo_falla": "COMBUSTIBLE_007",
        "requiere_escaner": "SI",
        "prueba": "Reinicio de parámetro de combustible adaptativo con escáner y verificación de sensor de relación de mezcla",
        "dtc": "P0171",
        "inicios": ["Luego de recargar combustible en grifo dudoso", "Al pasar de gasolina regular a especial", "En las mañanas frías"],
        "sintomas": ["el carro arranca con enorme dificultad y cabecea", "la computadora cree que tiene alcohol y descalibra los inyectores", "el motor tose y no mantiene el ralentí"],
        "condiciones": ["con cálculo erróneo del porcentaje de etanol en la ECU", "y mezcla pobre en banco 1", "requiriendo reseteo de mapa de combustible con escáner"]
    },

    # 3. TRANSMISIÓN Y EMBRAGUE
    {
        "sistema": "Transmisión y Embrague",
        "subcomponente": "Disco de embrague",
        "categoria_oficial": "Disco de embrague desgastado o patinando",
        "codigo_falla": "EMBRAGUE_001",
        "requiere_escaner": "NO",
        "prueba": "Prueba de calado en 3ra marcha con freno de mano aplicado y control de altura de pedal",
        "dtc": "N/A",
        "inicios": ["Al pisar el acelerador a fondo en tercera o cuarta", "Intentando subir una cuesta empinada", "Al adelantar un camión", "Al soltar el pedal de embrague"],
        "sintomas": ["el motor ruge y suben las RPM pero el auto no gana velocidad", "el embrague resbala y patina al soltar el pedal", "acelera en vacío sin traccionar con fuerza", "el carro se siente pesado y patina"],
        "condiciones": ["y sale un olor penetrante a material de fricción quemado", "con el pedal desembragando casi al final del recorrido superior", "perdiendo fuerza progresiva con carga", "sin que exista código electrónico de falla"]
    },
    {
        "sistema": "Transmisión y Embrague",
        "subcomponente": "Bombín de embrague hidráulico",
        "categoria_oficial": "Falla en bombin o bomba hidraulica de embrague",
        "codigo_falla": "EMBRAGUE_002",
        "requiere_escaner": "NO",
        "prueba": "Inspección visual de fugas en bombín maestro/esclavo y purgado del circuito hidráulico con dot 4",
        "dtc": "N/A",
        "inicios": ["Al pisar el pedal de embrague en las mañanas", "En tráfico pesado al meter primera", "Al soltar el embrague"],
        "sintomas": ["el pedal de embrague se queda pegado en el piso", "raspan todos los cambios y cuesta meter primera y retroceso", "el pedal no tiene presión y se siente flojo", "no desembraga completamente"],
        "condiciones": ["con fuga visible de líquido en la campana o detrás del pedal", "y el depósito de líquido de frenos/embrague ha bajado su nivel", "requiriendo bombear el pedal para que entre la marcha"]
    },
    {
        "sistema": "Transmisión y Embrague",
        "subcomponente": "Caja automática CVT / DSG",
        "categoria_oficial": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "codigo_falla": "TRANSMISION_001",
        "requiere_escaner": "SI",
        "prueba": "Escaneo de presiones de solenoide, monitoreo de temperatura de fluido ATF/CVT y prueba de calado",
        "dtc": "P0750",
        "inicios": ["Al pasar de primera a segunda marcha", "Al meter Drive o Reversa desde Parking", "Al exigir aceleración en subida", "Con la caja caliente"],
        "sintomas": ["la caja mete un golpe seco y patea la carrocería", "pega un tirón brusco cada vez que entra un cambio", "la transmisión patina y demora en acoplar", "se queda trabada en una sola marcha"],
        "condiciones": ["prendiendo el testigo de advertencia AT en el tablero", "con el fluido ATF de color marrón quemado", "siendo más notorio con la caja caliente", "con solenoide pegado"]
    },
    {
        "sistema": "Transmisión y Embrague",
        "subcomponente": "Rodajes de caja y diferencial",
        "categoria_oficial": "Rodajes de caja mecanica o diferencial gastados",
        "codigo_falla": "TRANSMISION_002",
        "requiere_escaner": "NO",
        "prueba": "Escucha con estetoscopio mecánico en bancada de transmisión con ruedas al aire y revisión de limaduras en tapón",
        "dtc": "N/A",
        "inicios": ["Al acelerar en 3ra o 4ta velocidad", "Rodando en pista rápida a más de 60 km/h", "Al desacelerar con marcha puesta"],
        "sintomas": ["se escucha un zumbido agudo o bramido continuo 'uooom'", "suena como turbina de avión en la caja de cambios", "el diferencial aúlla constantemente bajo carga"],
        "condiciones": ["pero al pisar el pedal de embrague el ruido cesa por completo", "o aumenta progresivamente con la velocidad del vehículo", "con presencia de partículas de bronce o acero en la valvulina"]
    },
    {
        "sistema": "Transmisión y Embrague",
        "subcomponente": "Aceite de caja",
        "categoria_oficial": "Falta o degradacion de aceite de caja de cambios",
        "codigo_falla": "TRANSMISION_003",
        "requiere_escaner": "NO",
        "prueba": "Inspección del nivel por el tapón de llenado, estado térmico y viscosidad de la valvulina",
        "dtc": "N/A",
        "inicios": ["Al meter los cambios en frío por la mañana", "Tras recorrer largas distancias", "Al circular en días calurosos"],
        "sintomas": ["la palanca de cambios se siente dura y entran ásperos los cambios", "raspan las marchas al meter segunda o tercera", "la caja genera sobrecalentamiento y chirridos suaves"],
        "condiciones": ["con el nivel de aceite varios centímetros por debajo del tapón", "o lubricante quemado y negro sin viscosidad", "sin pérdida de líquido visible"]
    },
    {
        "sistema": "Transmisión y Embrague",
        "subcomponente": "Caja Robotizada",
        "categoria_oficial": "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        "codigo_falla": "TRANSMISION_004",
        "requiere_escaner": "SI",
        "prueba": "Medición de presión de acumulador hidráulico (mínimo 45 bar) con escáner y purga guiada de electroválvulas",
        "dtc": "P1773",
        "inicios": ["Al detenerse en un semáforo y querer salir", "Al poner marcha atrás", "En tráfico denso"],
        "sintomas": ["la caja se salta a punto muerto Neutro sola", "aparece mensaje 'caja no disponible' en el tablero", "la bomba del robotizador no presuriza"],
        "condiciones": ["con pérdida de fluido hidráulico Tutela CS Speed", "y acumulador de presión desinflado", "con escáner marcando baja presión hidráulica de robot"]
    },

    # 4. REFRIGERACIÓN
    {
        "sistema": "Refrigeración",
        "subcomponente": "Termostato y motoventilador",
        "categoria_oficial": "Falla en termostato o motoventilador de radiador",
        "codigo_falla": "REFRIGERACION_001",
        "requiere_escaner": "NO",
        "prueba": "Toma de temperatura comparativa con pirómetro en mangueras superior e inferior del radiador y activación de relé",
        "dtc": "P0128",
        "inicios": ["A los 10 minutos de circular", "En tráfico o en subida", "Manejando a medio día", "Al subir pendientes"],
        "sintomas": ["la aguja de temperatura se va hasta el tope rojo", "el refrigerante hierve y se desborda por el depósito auxiliar", "bota vapor hirviendo por la tapa", "el electroventilador no activa"],
        "condiciones": ["y la manguera inferior del radiador sigue completamente fría", "a pesar de que el electroventilador prende a máxima velocidad", "sin que baje el calor ni acelerando", "con termostato trabado cerrado"]
    },
    {
        "sistema": "Refrigeración",
        "subcomponente": "Mangueras y radiador",
        "categoria_oficial": "Fuga en mangueras de refrigerante o radiador picado",
        "codigo_falla": "REFRIGERACION_002",
        "requiere_escaner": "NO",
        "prueba": "Presurización del circuito de enfriamiento con bomba manual a 15 psi e inspección de abrazaderas y paneles",
        "dtc": "N/A",
        "inicios": ["Al dejar estacionado el auto", "Con el motor encendido en mínimo", "Al revisar la zona frontal", "Al guardar el auto en la cochera"],
        "sintomas": ["deja un charco de líquido verde o rosado bajo el motor", "se escucha un siseo de vapor por el radiador", "gotea refrigerante constantemente por las abrazaderas", "baja el nivel en el vaso de expansión"],
        "condiciones": ["y el nivel en el vaso de expansión baja cada dos días", "con olor dulzón penetrante en el vano motor", "sin que el motor falle en frío", "con panel de radiador sulfatado"]
    },

    # 5. SISTEMA ELÉCTRICO Y CARGA
    {
        "sistema": "Sistema Eléctrico",
        "subcomponente": "Alternador y carga",
        "categoria_oficial": "Alternador defectuoso o placa de diodos quemada",
        "codigo_falla": "ELECTRICO_001",
        "requiere_escaner": "NO",
        "prueba": "Medición con multímetro de voltaje de carga en bornes (13.8V a 14.4V) bajo carga de luces y aire acondicionado",
        "dtc": "P0562",
        "inicios": ["Manejando de noche con faros encendidos", "Al acelerar en pista rápida", "De repente en plena marcha", "Al encender los accesorios"],
        "sintomas": ["se encendió el testigo rojo de la batería en el panel", "las luces del tablero y faros bajan su intensidad o parpadean", "la radio se reinicia sola y las agujas se caen", "el carro se apaga en marcha"],
        "condiciones": ["y al apagar el carro ya no volvió a prender por falta de carga", "registrando voltaje menor a 12V con el motor en marcha", "con olor a barniz quemado en el alternador", "con placa de diodos abierta"]
    },
    {
        "sistema": "Sistema Eléctrico",
        "subcomponente": "Batería y bornes",
        "categoria_oficial": "Bateria descargada o bornes sulfatados",
        "codigo_falla": "ELECTRICO_002",
        "requiere_escaner": "NO",
        "prueba": "Prueba de estado de salud (SOH) y CCA con analizador digital de baterías e inspección de bornes",
        "dtc": "N/A",
        "inicios": ["En las mañanas frías al dar arranque", "Tras dejar el carro parado 2 días", "Al girar la llave para dar marcha", "Al intentar salir temprano"],
        "sintomas": ["el motor gira sumamente pesado y lento como cansado", "se bajan por completo las luces del tablero al dar contacto", "solo se escucha un 'clac' seco pero el arrancador no gira", "no tiene fuerza para mover el motor"],
        "condiciones": ["con los bornes llenos de sarro blanquecino y sulfato", "y el voltaje cae por debajo de 9.6V durante el arranque", "con la batería cumpliendo su ciclo de vida útil", "sin carga eléctrica suficiente"]
    },

    # 6. SUSPENSIÓN Y DIRECCIÓN
    {
        "sistema": "Suspensión",
        "subcomponente": "Amortiguadores y bujes",
        "categoria_oficial": "Amortiguadores reventados o bujes de suspension gastados",
        "codigo_falla": "SUSPENSION_001",
        "requiere_escaner": "NO",
        "prueba": "Inspección de fuga en vástago de amortiguador y palanqueo en elevador de rótulas, bieletas y bujes",
        "dtc": "N/A",
        "inicios": ["Al cruzar calles afirmadas o trochas", "Al pasar baches o rompemuelles a baja velocidad", "En pistas con ondulaciones", "Al cruzar huecos"],
        "sintomas": ["suena un golpe seco y constante 'cloc cloc' adelante", "el carro se queda rebotando como una lancha sin parar", "se siente un traqueteo sordo en el piso del auto", "golpetea el tren delantero"],
        "condiciones": ["pero en carretera totalmente lisa y asfaltada no suena nada", "con el amortiguador bañado en aceite o rótula con juego", "especialmente al descolgar la rueda en un hueco", "con bujes de trapecio rajados"]
    },
    {
        "sistema": "Suspensión y Ejes",
        "subcomponente": "Junta homocinética",
        "categoria_oficial": "Juntas homocineticas o palieres danados",
        "codigo_falla": "SUSPENSION_002",
        "requiere_escaner": "NO",
        "prueba": "Inspección de guardapolvo roto y prueba de giro con volante a tope acelerando",
        "dtc": "N/A",
        "inicios": ["Al dar la vuelta en U en una esquina", "Girando todo el timón para estacionar", "Al doblar en curvas cerradas acelerando", "Al salir doblando a la izquierda o derecha"],
        "sintomas": ["se escucha un 'taca taca taca' metálico y repetitivo en la rueda", "cruje y traquetea fuertemente el semieje al girar", "truena la punta de eje delantera", "suena matraca metálica al virar"],
        "condiciones": ["pero cuando pongo la dirección en línea recta el ruido desaparece por completo", "y se ve grasa negra salpicada por dentro del aro y amortiguador", "aumentando el chasquido si acelero en plena curva", "con fuelle roto"]
    },
    {
        "sistema": "Dirección",
        "subcomponente": "Cremallera de dirección",
        "categoria_oficial": "Cremallera de direccion asistida con holgura o fuga",
        "codigo_falla": "SUSPENSION_003",
        "requiere_escaner": "NO",
        "prueba": "Inspección de retenes de cremallera, nivel de fluido hidráulico y calibración de sensor de ángulo SAS",
        "dtc": "C1511",
        "inicios": ["En las mañanas al maniobrar para salir", "Al girar la dirección a los topes", "Al mover el volante despacio", "Al parquear"],
        "sintomas": ["la dirección asistida se pone durísima como piedra", "la bomba emite un zumbido chillón al girar", "tiembla el timón al estacionar con juego muerto", "se traba la dirección hacia un lado"],
        "condiciones": ["y encontré gotas de aceite rojizo en el piso de la cochera", "pero acelerando un poco el motor la dirección se afloja", "con holgura perceptible en el volante al girar", "con fuga en retenes laterales"]
    },
    {
        "sistema": "Dirección y Ruedas",
        "subcomponente": "Balanceo y alineación",
        "categoria_oficial": "Llantas desbalanceadas o desalineadas",
        "codigo_falla": "SUSPENSION_004",
        "requiere_escaner": "NO",
        "prueba": "Calibración de presión en frío, balanceo dinámico computarizado en máquina y alineación de cotas 3D",
        "dtc": "N/A",
        "inicios": ["En autopista al alcanzar 70 u 80 km/h", "Al correr a más de 80 km/h en recta", "Soltando el timón en pista plana", "Al ir en línea recta en carretera", "Manejando en la Panamericana"],
        "sintomas": ["el timón empieza a vibrar y cabecear en las manos", "se sacude el volante continuamente de lado a lado", "el vehículo se jala con fuerza hacia la derecha", "el timón queda torcido para ir recto", "vibra feo el volante a velocidad"],
        "condiciones": ["pero al frenar no tiembla el pedal ni aumenta la vibración", "y las llantas delanteras presentan desgaste irregular en bordes", "desapareciendo la vibración si bajo la velocidad", "sin que se sienta en el pedal de freno", "pero freno y la vibración sigue exactamente igual"]
    },

    # 7. FRENOS
    {
        "sistema": "Frenos",
        "subcomponente": "Pastillas y zapatas",
        "categoria_oficial": "Desgaste de pastillas y zapatas de freno",
        "codigo_falla": "FRENO_001",
        "requiere_escaner": "NO",
        "prueba": "Inspección de espesor en milímetros de pastillas con vernier, estado de pistas del disco y guías de cáliper",
        "dtc": "N/A",
        "inicios": ["Al pisar suavemente el pedal de freno", "Al llegar frenando a las esquinas", "En paradas a baja velocidad", "Al aplicar freno en bajada"],
        "sintomas": ["suena un chillido agudo de lata con lata muy estridente", "raspa fierro con fierro en las ruedas al frenar", "se siente un rechinido metálico insoportable", "chilla el freno cada vez que toco el pedal"],
        "condiciones": ["y bota bastante hollín negro en los aros delanteros", "pero si piso el freno a fondo frena sin perder la línea", "con los avisadores metálicos tocando el disco", "con menos de 2 mm de material de fricción"]
    },
    {
        "sistema": "Frenos",
        "subcomponente": "Circuito hidráulico",
        "categoria_oficial": "Fuga hidraulica o aire en el sistema de frenos",
        "codigo_falla": "FRENO_002",
        "requiere_escaner": "NO",
        "prueba": "Prueba de retención estática del pedal, inspección de bombines y purgado de circuito hidráulico",
        "dtc": "N/A",
        "inicios": ["Al mantener el pie pisando el freno en una parada", "Estando detenido en un semáforo en bajada", "Al aplicar frenada de emergencia", "Al pisar el freno"],
        "sintomas": ["el pedal de freno se hunde lentamente hasta el fondo", "el pedal se siente completamente esponjoso y frena muy abajo", "tengo que bombear dos veces para que agarre el freno", "se va de largo el pedal"],
        "condiciones": ["sin que frene con la fuerza requerida", "con presencia de burbujas de aire en tuberías o fuga en cilindro maestro", "perdiendo presión hidráulica sostenida", "con el depósito de líquido bajando"]
    },
    {
        "sistema": "Frenos",
        "subcomponente": "Discos de freno",
        "categoria_oficial": "Discos de freno alabeados o desgastados",
        "codigo_falla": "FRENO_003",
        "requiere_escaner": "NO",
        "prueba": "Medición de alabeo axial y variación de espesor con reloj comparador montado en base magnética",
        "dtc": "N/A",
        "inicios": ["Al pisar el freno a más de 60 km/h", "Al frenar bajando una pendiente", "Cada vez que aplico freno en autopista", "Al reducir velocidad con freno"],
        "sintomas": ["el pedal de freno zapatea y pulsa contra el pie", "el timón se sacude bruscamente solo al frenar", "vibra toda la pedalera y el tablero al detenerse", "tiembla fuertemente el volante al aplicar freno"],
        "condiciones": ["pero cuando suelto el freno el carro rueda perfectamente suave", "especialmente si los discos ya están calientes por uso constante", "con discos de freno deformados térmicamente", "y al soltar el freno la vibración desaparece de inmediato"]
    },
    {
        "sistema": "Frenos",
        "subcomponente": "Booster / Servofreno",
        "categoria_oficial": "Falla en servofreno (booster) o linea de vacio",
        "codigo_falla": "FRENO_004",
        "requiere_escaner": "NO",
        "prueba": "Prueba de vacío con vacuómetro en manguera de admisión e inspección de válvula check del servofreno",
        "dtc": "N/A",
        "inicios": ["Al pisar el pedal de freno para detener el auto", "Con el motor encendido al frenar", "En frenadas cortas en ciudad"],
        "sintomas": ["el pedal de freno se puso durísimo como un ladrillo", "cuesta un esfuerzo enorme detener el carro pisando a fondo", "se escucha un siseo de aire bajo el pedal al frenar", "el carro no frena y el pedal está duro"],
        "condiciones": ["y al pisar el freno el motor cabecea y quiere apagarse por fuga de vacío", "sin que exista pérdida de líquido en los depósitos", "con diafragma de servofreno roto o manguera perforada"]
    },
    {
        "sistema": "Frenos",
        "subcomponente": "Sensor ABS",
        "categoria_oficial": "Falla en sensor de velocidad de rueda ABS",
        "codigo_falla": "FRENO_005",
        "requiere_escaner": "SI",
        "prueba": "Lectura de velocidad de rueda en datos en vivo con escáner e inspección de entrehierro del sensor",
        "dtc": "C0035",
        "inicios": ["Al frenar a baja velocidad en pista seca", "Al arrancar y pasar los 20 km/h", "De la nada en pavimento plano", "Al encender"],
        "sintomas": ["el pedal patea y activa el ABS sin motivo", "se encendió el testigo del ABS y control de tracción fijo", "el sistema antibloqueo se dispara solo", "se activa la vibración del ABS sin derrapar"],
        "condiciones": ["con el sensor de rueda lleno de viruta metálica o cable cortado", "y los frenos mecánicos convencionales siguen funcionando", "registrando circuito abierto en sensor de velocidad", "marcando cero km/h en rueda delantera"]
    },
    {
        "sistema": "Frenos Neumáticos",
        "subcomponente": "Líneas neumáticas de camión",
        "categoria_oficial": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
        "codigo_falla": "FRENO_006",
        "requiere_escaner": "NO",
        "prueba": "Inspección de fugas con agua jabonosa en racores y verificación de caída de presión en calderines",
        "dtc": "N/A",
        "inicios": ["Al dejar estacionado el camión", "Con el motor apagado y aire cargado", "Al pisar la válvula de pedal"],
        "sintomas": ["se escucha un silbido continuo de aire en los tanques", "la aguja de los manómetros de aire cae rápidamente a cero", "las ruedas se quedan bloqueadas por falta de aire en pulmones"],
        "condiciones": ["con manguera de tecalán partida o racor desajustado", "tardando más de 15 minutos en cargar los calderines a 8 bar", "sin fugas en los pulmones de servicio"]
    },
    {
        "sistema": "Frenos Neumáticos",
        "subcomponente": "Secador de aire APS",
        "categoria_oficial": "Válvula de freno de aire o secador APS obstruido (Camiones)",
        "codigo_falla": "FRENO_007",
        "requiere_escaner": "NO",
        "prueba": "Purga de calderines verificando presencia de agua/aceite y sustitución del cartucho desecante",
        "dtc": "N/A",
        "inicios": ["Al purgar las válvulas inferiores de los calderines", "En mañanas de invierno o frío", "Al sonar la descarga del compresor"],
        "sintomas": ["sale un chorro de agua y aceite mezclado por la purga", "la válvula de descarga no libera el exceso de presión y suena trabada", "se congelan o engarrotan las válvulas de frenado"],
        "condiciones": ["con el filtro secador saturado de humedad y hollín", "y el compresor pasando aceite por desgaste de aros", "sin deshumidificar el circuito neumático"]
    },

    # 8. CLIMATIZACIÓN, TURBO Y ESCAPE
    {
        "sistema": "Climatización",
        "subcomponente": "Compresor de A/C",
        "categoria_oficial": "Falla en compresor de aire acondicionado o fuga de gas R134a",
        "codigo_falla": "CLIMA_001",
        "requiere_escaner": "NO",
        "prueba": "Medición de presiones en alta y baja con manómetros de A/C y prueba de fuga con nitrógeno o lámpara UV",
        "dtc": "N/A",
        "inicios": ["Al encender el botón A/C al mediodía", "En días calurosos al activar el enfriamiento", "Al conectar el aire acondicionado", "Al prender el clima"],
        "sintomas": ["solo sale aire tibio por las rejillas de ventilación", "no enfría nada la cabina a pesar de ponerlo al mínimo", "el embrague magnético del compresor no acopla ni gira", "sopla aire caliente"],
        "condiciones": ["y se escucha un siseo de escape de gas detrás de la guantera", "sin ruidos extraños en el ventilador interior", "marcando cero presión estática de gas refrigerante R134a", "con sello del compresor picado"]
    },
    {
        "sistema": "Turbo",
        "subcomponente": "Intercooler y mangueras turbo",
        "categoria_oficial": "Fuga en mangueras de intercooler o turbocompresor danado",
        "codigo_falla": "TURBO_001",
        "requiere_escaner": "SI",
        "prueba": "Comprobación de presión de sobrealimentación con escáner e inspección visual de fisuras en manguerones",
        "dtc": "P0299",
        "inicios": ["Al pisar a fondo para adelantar en carretera", "Al pasar de 2500 RPM en subida", "Al entrar la sobrealimentación"],
        "sintomas": ["se escucha un soplido de aire fuertísimo tipo vendaval", "el carro no tiene fuerza y bota humo negro espeso por el tubo", "el turbo silba agudo como ambulancia y pierde empuje"],
        "condiciones": ["con manguera de silicona rajada o abrazadera suelta", "y el escáner registrando baja presión de turbo P0299", "con juego radial excesivo en turbina"]
    },
    {
        "sistema": "Turbo",
        "subcomponente": "Actuador de turbo TSI",
        "categoria_oficial": "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
        "codigo_falla": "TURBO_002",
        "requiere_escaner": "SI",
        "prueba": "Calibración de recorrido milimétrico de la varilla de la wastegate electrónica y prueba de actuador con escáner",
        "dtc": "P2563",
        "inicios": ["En motores Volkswagen o Audi TSI", "Al acelerar fuerte en carretera", "Al arrancar en frío"],
        "sintomas": ["se prende el testigo EPC y el carro se achancha por completo", "no acelera nada y se limita la velocidad a 60 km/h", "la varilla electrónica del turbo se queda trabada"],
        "condiciones": ["con código P2563 de sensor de posición de actuador de sobrealimentación", "y holgura mecánica en el buje de la válvula de descarga", "recuperando fuerza momentánea al apagar y encender"]
    },
    {
        "sistema": "Escape y Emisiones",
        "subcomponente": "Filtro DPF y AdBlue",
        "categoria_oficial": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
        "codigo_falla": "ESCAPE_001",
        "requiere_escaner": "SI",
        "prueba": "Medición de presión diferencial en filtro DPF y regeneración forzada estática con escáner",
        "dtc": "P2463",
        "inicios": ["Luego de mucho uso en tráfico lento de ciudad", "En autos diésel modernos Euro 5 o 6", "Al encender el panel"],
        "sintomas": ["se encendió el testigo del DPF o advertencia de AdBlue", "el motor pierde potencia y entra en estrategia de protección", "el tubo de escape despide olor químico penetrante y calor excesivo"],
        "condiciones": ["con el filtro de partículas saturado de hollín a más del 80%", "e imposibilidad de completar la regeneración automática por trayectos cortos", "registrando sobrepresión en sensor diferencial"]
    },

    # 9. CARROCERÍA Y CONFORT
    {
        "sistema": "Carrocería",
        "subcomponente": "Cierre centralizado eléctrico",
        "categoria_oficial": "Falla electrica del cierre centralizado o actuador de puerta",
        "codigo_falla": "CARROCERIA_001",
        "requiere_escaner": "SI",
        "prueba": "Comprobación de señal de pulso de 12V con lámpara lógica y escaneo del módulo de confort BCM",
        "dtc": "B1300",
        "inicios": ["Al presionar el botón de la llave de control", "Al intentar cerrar el auto desde la puerta", "Al parquear"],
        "sintomas": ["tres puertas aseguran pero la del piloto queda abierta", "rebotan los seguros y no trancan al presionar el mando", "no responde el cierre eléctrico de ninguna puerta"],
        "condiciones": ["con el motor actuador de la chapa quemado o cable cortado en el fuelle de puerta", "y la chapa manual con llave mecánica sigue abriendo", "sin accionar los pestillos eléctricos"]
    },
    {
        "sistema": "Carrocería",
        "subcomponente": "Chapa y pestillo mecánico",
        "categoria_oficial": "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado",
        "codigo_falla": "CARROCERIA_002",
        "requiere_escaner": "NO",
        "prueba": "Alineación del cerradero en el pilar, lubricación de varillaje y regulación de holguras mecánicas",
        "dtc": "N/A",
        "inicios": ["Al intentar abrir o cerrar la puerta del chofer", "Al tirar de la manija exterior", "Al empujar la puerta para cerrar"],
        "sintomas": ["la puerta no encaja y hay que tirarla durísimo con fuerza", "la manija se siente suelta y no destraba el pestillo mecánico", "se queda atascada la cerradura y no abre por dentro"],
        "condiciones": ["con el cerradero flojo o bisagra descolgada por desgaste", "sin que intervenga ningún componente eléctrico", "con el pestillo trabado por falta de lubricación"]
    },
    {
        "sistema": "Carrocería",
        "subcomponente": "Elevalunas eléctrico",
        "categoria_oficial": "Elevalunas electrico o guaya de alzacristales rota o trabada",
        "codigo_falla": "CARROCERIA_003",
        "requiere_escaner": "NO",
        "prueba": "Desmontaje del tapiz de puerta, prueba directa de motor a 12V e inspección de guías y cables de acero",
        "dtc": "N/A",
        "inicios": ["Al pulsar el botón para bajar la ventana", "Al intentar subir el vidrio del copiloto", "Al pagar en un peaje"],
        "sintomas": ["el vidrio se cayó de golpe al fondo de la puerta", "el motorcito zumba pero la luna no sube ni baja", "se escucha un crujido de cables trenzados enredándose adentro"],
        "condiciones": ["con la guaya de acero del mecanismo completamente reventada", "o los patines plásticos de la corredera rotos", "estando el mando eléctrico en buen estado"]
    },
    {
        "sistema": "Carrocería",
        "subcomponente": "Limpiaparabrisas",
        "categoria_oficial": "Limpiaparabrisas o motor pluma quemado",
        "codigo_falla": "CARROCERIA_004",
        "requiere_escaner": "NO",
        "prueba": "Prueba de alimentación y masa en el conector del motor pluma e inspección de rótulas de varillaje",
        "dtc": "N/A",
        "inicios": ["Al llover y activar la palanca de plumas", "Al querer limpiar el parabrisas empolvado", "En marcha bajo garúa"],
        "sintomas": ["las plumillas no se mueven absolutamente nada", "se quedan trabadas a la mitad del vidrio", "el motor de plumas huele a quemado y no gira"],
        "condiciones": ["a pesar de tener fusible en buen estado", "o varillaje articulado engarrotado por óxido", "sin responder a ninguna de las velocidades"]
    },

    # 10. VEHÍCULOS ELÉCTRICOS E HÍBRIDOS (EV / HEV)
    {
        "sistema": "Vehículos Eléctricos e Híbridos",
        "subcomponente": "Batería de alto voltaje",
        "categoria_oficial": "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
        "codigo_falla": "ELECTRICO_HV_001",
        "requiere_escaner": "SI",
        "prueba": "Medición con escáner del delta de voltaje entre bloques de celdas (máximo 0.2V de diferencia) y SOH",
        "dtc": "P0A80",
        "inicios": ["En un Toyota Prius o auto híbrido/EV", "Al subir pendientes en modo eléctrico", "Al encender el carro"],
        "sintomas": ["aparece el triángulo rojo maestro o aviso de revisar sistema híbrido", "el motor a gasolina no se apaga nunca y carga forzado", "la batería pasa de llena a vacía en menos de 2 cuadras"],
        "condiciones": ["con código P0A80 de reemplazo de paquete de baterías", "y bloque de celdas con resistencia interna disparada", "con ventilador de enfriamiento de batería al máximo"]
    },
    {
        "sistema": "Vehículos Eléctricos e Híbridos",
        "subcomponente": "Inversor IGBT",
        "categoria_oficial": "Fallo en inversor de corriente IGBT o motor electrico (EV)",
        "codigo_falla": "ELECTRICO_HV_002",
        "requiere_escaner": "SI",
        "prueba": "Escaneo de códigos de aislamiento de alta tensión y verificación de circulación de refrigerante de inversor",
        "dtc": "P0A94",
        "inicios": ["Al exigir aceleración a fondo en modo EV", "En días calurosos al circular", "De repente el auto se queda en neutro"],
        "sintomas": ["el vehículo no avanza y se apaga el indicador READY", "huele a plástico recalentado en el vano motor de alta tensión", "la bomba de agua auxiliar del inversor no circula refrigerante"],
        "condiciones": ["con transistor IGBT quemado por sobretemperatura", "y disparo de fusible de alta tensión pirotécnico", "con código P0A94 en escáner"]
    },
    {
        "sistema": "Vehículos Eléctricos e Híbridos",
        "subcomponente": "Frenado Regenerativo",
        "categoria_oficial": "Falla en sistema de frenado regenerativo (EV / Hibridos)",
        "codigo_falla": "ELECTRICO_HV_003",
        "requiere_escaner": "SI",
        "prueba": "Calibración con escáner de la carrera de pedal stroke sensor y purga con equipo de alta presión",
        "dtc": "C1391",
        "inicios": ["Al tocar suavemente el pedal de freno en un híbrido", "Al aproximarse a una detención", "Al frenar en bajada"],
        "sintomas": ["el freno se siente brusco o sin transición hidráulica", "el generador no recupera energía al soltar el acelerador", "se enciende la luz de frenos y ABS en conjunto"],
        "condiciones": ["con fuga interna en el actuador de freno regenerativo", "y pérdida de presión en acumulador de freno hidráulico", "sin frenada suave asistida"]
    },
    {
        "sistema": "Vehículos Eléctricos e Híbridos",
        "subcomponente": "Refrigeración de batería/inversor EV",
        "categoria_oficial": "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)",
        "codigo_falla": "ELECTRICO_HV_004",
        "requiere_escaner": "SI",
        "prueba": "Prueba de activación de bomba eléctrica de agua con escáner y limpieza de tobera de soplador de batería",
        "dtc": "P0A93",
        "inicios": ["Al usar carga rápida DC en estación de carga", "En días soleados de intenso calor", "Tras 30 minutos de manejo continuo"],
        "sintomas": ["se limita drásticamente la potencia del motor eléctrico", "se enciende advertencia de temperatura de alta tensión", "la velocidad de carga se reduce al mínimo"],
        "condiciones": ["con el conducto de ventilación de la batería tapado con pelusas o suciedad", "o bomba eléctrica de refrigerante trabada", "con código de falla P0A93 de sobrecalentamiento"]
    }
]


def generar_dataset_aumento(nombre_archivo: str = "dataset_sintomas_aumento_taller.csv", total_filas: int = 3360):
    """Genera el dataset complementario con distribución balanceada y variaciones coloquiales peruanas."""
    cabeceras = [
        "id",
        "sintoma",
        "falla",
        "codigo_falla",
        "sistema",
        "subcomponente",
        "requiere_escaner",
        "prueba_sugerida",
        "codigo_dtc",
        "origen_dato",
        "grupo_origen",
        "estado_revision",
        "validado_mecanico",
    ]

    random.seed(42)
    ruta_salida = Path(__file__).resolve().parents[1] / "data" / nombre_archivo

    with open(ruta_salida, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cabeceras)

        num_clases = len(SISTEMAS_TALLER)
        por_clase = total_filas // num_clases
        resto = total_filas % num_clases

        row_id = 1
        for idx, item in enumerate(SISTEMAS_TALLER):
            repeticiones = por_clase + (1 if idx < resto else 0)

            inicios = item["inicios"]
            sintomas = item["sintomas"]
            condiciones = item["condiciones"]

            for _ in range(repeticiones):
                indice_inicio = random.randrange(len(inicios))
                indice_sintoma = random.randrange(len(sintomas))
                indice_condicion = random.randrange(len(condiciones))
                ini = inicios[indice_inicio]
                sin = sintomas[indice_sintoma]
                con = condiciones[indice_condicion]
                grupo_origen = (
                    f"AUG-{idx + 1:03d}-{indice_inicio:02d}-"
                    f"{indice_sintoma:02d}-{indice_condicion:02d}"
                )

                patron = random.randint(1, 5)
                if patron == 1:
                    texto = f"{ini}, {sin}, {con}."
                elif patron == 2:
                    texto = f"Maestro, {sin} {ini.lower()}. Pasa que {con}."
                elif patron == 3:
                    texto = f"Mire: {sin.capitalize()} {ini.lower()}, sobre todo {con}."
                elif patron == 4:
                    texto = f"Revisión técnica: {ini.lower()} se nota que {sin} y además {con}."
                else:
                    texto = f"Al probar el auto: {ini.lower()}, {sin}; el cliente indica que {con}."

                texto = texto.replace("  ", " ").strip()

                writer.writerow([
                    row_id,
                    texto,
                    item["categoria_oficial"],
                    item["codigo_falla"],
                    item["sistema"],
                    item["subcomponente"],
                    item["requiere_escaner"],
                    item["prueba"],
                    item["dtc"],
                    "sintetico_aumentado",
                    grupo_origen,
                    "solo_experimento",
                    "NO",
                ])
                row_id += 1

    print(f"[OK] Dataset de aumento guardado con {row_id - 1} filas en: {ruta_salida}")


if __name__ == "__main__":
    generar_dataset_aumento()
