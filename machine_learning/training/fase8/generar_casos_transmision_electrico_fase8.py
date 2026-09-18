"""
Generador modular de casos independientes de TRANSMISION y ELECTRICO para Fase 8.
Blindaje: Totalmente disjunto del benchmark TEST G1_01-G1_50.
"""

from typing import List, Dict

def obtener_casos_transmision_electrico_fase8() -> List[Dict[str, str]]:
    casos = []

    # 1. Collarín de empuje
    f_col = "Desgaste en collarin de empuje o crapodina de embrague"
    s_col = [
        "Al pisar el pedal de embrague se escucha un chillido metalico agudo o zumbido fuerte que desaparece completamente cuando suelto el pedal",
        "Ruido de friccion en la caja de cambios que suena exclusivamente mientras mantengo presionado el pedal del clutch",
        "Collarin de empuje seco y sin grasa suena a rodamiento oxidado al apoyar contra el diafragma de la prensa de embrague",
        "Vibracion y aspereza notable en la planta del pie al momento de pisar el embrague para meter primera marcha",
        "Crapodina o ruleman de empuje de embrague hidraulico chilla al desembragar y disminuye al soltar el pedal",
        "Sonido de rodaje seco que aparece inmediatamente al hundir el pedal de embrague con motor en marcha",
        "Rodamiento del collarin atascado roza contra los dedos del plato opresor provocando chillido chirriante",
        "El carro en neutro no hace ningun ruido pero al apretar el clutch para cambiar de marcha hace un quejido agudo",
        "Collarin con pistas picadas genera traqueteo de friccion que cesa cuando el embrague esta completamente acoplado",
        "Chillido estridente en la campana de transmision al accionar el pedal del embrague en semaforos",
        "Al pisar embrague en frio suena un chirrido que va aumentando conforme pasan los minutos, collarin gastado",
        "Ruido de rozamiento en transmision que se activa solamente bajo presion del bombin sobre el collarin de empuje",
    ]
    for s in s_col:
        casos.append({"sintoma": s, "falla": f_col, "sistema": "TRANSMISION"})

    # 2. Rodajes de transmisión manual / eje primario
    f_eje = "Rodajes de transmision manual o eje primario gastados"
    s_eje = [
        "En neutro con motor encendido se escucha un zumbido o ronroneo continuo en la caja, pero al pisar el embrague a fondo el ruido desaparece",
        "Zumbido constante en la transmision manual que se apaga inmediatamente cuando hundo el pedal de clutch y se detiene el eje de entrada",
        "Rodamiento del eje primario de caja mecanica con desgaste severo hace ruido en punto muerto y en todas las marchas",
        "Ronroneo de engranajes y rodajes en la caja que se siente en la palanca de cambios en ralenti y cesa al pisar embrague",
        "Al soltar el pedal de embrague en neutro empieza a sonar como licuadora con rodajes secos dentro de la caja de cambios",
        "Caja manual suena a ruleman picado cuando el vehiculo esta regulando sin pisar embrague, al desembragar queda silencioso",
        "Rodaje de apoyo del arbol primario desgastado genera zumbido que aumenta al acelerar en primera segunda y tercera velocidad",
        "Ruido sordo de rodamientos en la caja de velocidades que desaparece al aislar la transmision presionando el embrague",
        "Zumbido de caja mecanica que suena fuerte al rodar y desaparece al colocar neutro y presionar el pedal del clutch",
        "Falta de aceite de transmision daño los rodamientos conicos del eje primario produciendo rumor continuo en neutro",
    ]
    for s in s_eje:
        casos.append({"sintoma": s, "falla": f_eje, "sistema": "TRANSMISION"})

    # 3. Motor de arranque / solenoide (clac seco)
    f_arr = "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)"
    s_arr = [
        "Giro la llave de contacto y solo se escucha un clac seco en el arrancador pero el motor de arranque no gira nada",
        "Bateria marca 12.6 voltios y faros prenden con buena potencia pero al dar arranque se escucha un solo clic y se queda mudo",
        "Tengo que darle unos golpecitos con una llave a la carcasa del arrancador para que enganchen los carbones y recien enciende",
        "Carbones o escobillas del motor de arranque totalmente desgastados no hacen contacto con el colector del inducido",
        "Terminal 50 del solenoide recibe 12V con la llave en posicion START pero el arrancador no acciona el bendix ni gira",
        "Contactos de potencia de cobre del solenoide fogueados o carbonizados impiden el paso de corriente al inducido",
        "Al dar arranque se apagan tenuemente los testigos del tablero pero el arrancador no mueve el volante motor clac clac",
        "El arrancador a veces gira normal y otras veces hace un clic metalico seco y no hace absolutamente nada",
        "Bobina del automatico o rele del solenoide de arranque con falso contacto interno no retiene el embolo",
        "Motor de arranque se queda pegado o zumba en vacio sin engranar el bendix a la cercha del volante",
        "Luces del tablero quedan encendidas firmes pero el motor no da marcha solo se oye un chasquido debajo del motor",
        "El carro no da arranque de manera aleatoria, arrancador mudo a pesar de bateria nueva recien instalada",
    ]
    for s in s_arr:
        casos.append({"sintoma": s, "falla": f_arr, "sistema": "ELECTRICO"})

    # 4. Fuga parásita de corriente en reposo
    f_fuga = "Fuga parasita de corriente en reposo (consumo nocturno de bateria)"
    s_fuga = [
        "La bateria amanece completamente muerta y descargada si dejo el vehiculo parado toda la noche o durante el fin de semana",
        "Bateria nueva se descarga sola en dos dias de estacionamiento, alternador carga perfecto a 14.3V con motor encendido",
        "Medicion con multimetro en serie en borne negativo marca consumo parasito de 350 miliamperios en reposo con llave retirada",
        "Modulo de confort de carroceria BCM no entra en modo sleep y sigue consumiendo 0.4 amperios con el auto apagado y cerrado",
        "Luz interior de la guantera o del maletero se queda encendida permanentemente descargando la bateria en la noche",
        "Alarma no original o radio pantalla aftermarket tiene consumo parásito continuo que drena la bateria en reposo",
        "Corriente parasita de 280 mA en reposo excede la tolerancia de 50 mA segun manual de taller y descarga el acumulador",
        "Si desconecto el borne de la bateria por la noche arranca perfecto al dia siguiente confirmando fuga de corriente",
        "Al retirar fusibles uno por uno en la fusilera el consumo parasito de 0.5A cae a 0.02A al sacar el fusible de la radio",
        "Descarga lenta de acumulador en reposo con alternador y bateria en excelente estado comprobados en banco",
        "El carro se queda sin energia despues de 48 horas sin uso, requiriendo auxilio de arranque con cables",
    ]
    for s in s_fuga:
        casos.append({"sintoma": s, "falla": f_fuga, "sistema": "ELECTRICO"})

    return casos
