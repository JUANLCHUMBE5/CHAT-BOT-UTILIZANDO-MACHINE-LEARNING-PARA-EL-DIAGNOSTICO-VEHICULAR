"""
Generador robusto de expansiones sintomáticas independientes para la Fase 8.
Genera ~50 ejemplos realistas por clase para las 13 clases nuevas y clases reforzadas.
Cumple con la regla de NO contaminación con el benchmark TEST G1_01-G1_50.
"""

from typing import List, Dict

def generar_dataset_expansiones_fase8() -> List[Dict[str, str]]:
    casos = []

    # Plantillas y combinaciones contextuales para generar variedad lingüística
    # 1. CKP / CMP
    f_ckp = "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)"
    ckp_patrones = [
        "El motor se apaga repentinamente luego de {tiempo} minutos de marcha continua y no arranca hasta que {enfriamiento}",
        "Tengo codigo {dtc} en el escaner, al dar arranque el arrancador gira con fuerza pero no hay {falla_combustion}",
        "Falla termica en sensor de cigueñal: en frio enciende de inmediato pero a {temp} grados se corta la senal y el motor se detiene",
        "Con osciloscopio automotriz se observa que la senal del sensor {sensor} pierde amplitud y se deforma al subir la temperatura del motor",
        "El carro tironea bruscamente a {velocidad} km/h, la aguja de las RPM se cae a cero al instante y el motor se apaga",
        "Corte intempestivo de encendido en caliente, la bomba no zumba y las bobinas no reciben pulso de disparo de la ECM por falta de senal de RPM",
        "Sensor de arbol de levas {dtc_cmp} con arnes agrietado produce arranque sumamente largo de mas de 8 segundos antes de encender",
        "Al detenerse en ralenti despues de un viaje el motor se muere en seco; gira rapido el motor de arranque pero no hay chispa ni pulso de inyector",
        "Sensor CKP de efecto Hall con alimentacion de 5V inestable se apaga y deja al vehiculo botado en subida",
        "Resistencia de la bobina captadora del sensor de cigueñal se va a infinito al calentarse el bloque motor"
    ]
    tiempos = ["20", "25", "35", "40", "45", "50"]
    enfriamientos = ["se enfria 15 minutos", "baja la aguja de temperatura", "lo dejo descansar 20 minutos", "el motor reposa media hora", "se enfria completamente el bloque"]
    dtcs = ["P0335", "P0336", "P0339"]
    fallas_c = ["chispa en las bujias ni pulso de inyectores", "combustion a pesar de tener buena presion de gasolina", "pulso de activacion en las bobinas COP", "senal de revoluciones en la linea de datos"]
    temps = ["85", "90", "95", "100"]
    sensores = ["CKP inductivo", "CKP efecto Hall", "de posicion de cigueñal", "de posicion del arbol de levas CMP"]
    velocidades = ["60", "80", "90", "100", "110"]
    dtcs_cmp = ["P0340", "P0341", "P0342"]

    for i in range(50):
        t = tiempos[i % len(tiempos)]
        e = enfriamientos[i % len(enfriamientos)]
        d = dtcs[i % len(dtcs)]
        fc = fallas_c[i % len(fallas_c)]
        te = temps[i % len(temps)]
        s = sensores[i % len(sensores)]
        v = velocidades[i % len(velocidades)]
        dc = dtcs_cmp[i % len(dtcs_cmp)]
        pat = ckp_patrones[i % len(ckp_patrones)]
        texto = pat.format(tiempo=t, enfriamiento=e, dtc=d, falla_combustion=fc, temp=te, sensor=s, velocidad=v, dtc_cmp=dc)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_ckp, "sistema": "MOTOR"})

    # 2. EVAP
    f_evap = "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"
    evap_patrones = [
        "Inmediatamente despues de tanquear combustible en el grifo el motor tose, se ahoga y le cuesta mucho volver a prender",
        "Fuerte olor a gasolina pura dentro del habitaculo y cerca del tanque despues de llenar {nivel}",
        "Valvula solenoide de purga del canister {estado_valvula} deja pasar vapores de nafta sin control hacia la admision",
        "Codigo de falla {dtc} en scanner automotriz relacionado con el sistema de emisiones evaporativas EVAP",
        "Al destapar la tapa de gasolina en la estacion se escucha un gran {sonido} por acumulacion indebida de vacio en el tanque",
        "El ralenti sube y baja erratico y la mezcla se va a extremadamente rica apenas cargo combustible en la estacion",
        "Canister de carbon activado saturado de nafta liquida por sobrellenado continuo de la pistola del surtidor",
        "Prueba con maquina generadora de humo detecta fuga de vapor en {componente_evap}",
        "La valvula de purga del multiple succiona constantemente en ralenti impidiendo la regulacion estequiometrica",
        "Testigo de falla de motor encendido con DTC {dtc_fuga} microfuga detectada en circuito de recuperacion de vapores"
    ]
    niveles = ["el tanque a full", "el deposito completo de combustible", "gasolina hasta el tope de la boca"]
    estados_v = ["trabada abierta de forma permanente", "con asiento de goma danado que no cierra", "con fuga interna al aplicarle vacio manual"]
    dtcs_evap = ["P0440", "P0441", "P0442", "P0455", "P0456"]
    sonidos = ["silbido de succion de aire", "vacio que deforma el tanque metalico", "chasquido de aire que entra con fuerza"]
    comps_evap = ["la manguera de venteo del canister", "la valvula vent solenoide trasera", "el empaque del tapon de llenado de nafta"]

    for i in range(50):
        n = niveles[i % len(niveles)]
        ev = estados_v[i % len(estados_v)]
        de = dtcs_evap[i % len(dtcs_evap)]
        so = sonidos[i % len(sonidos)]
        ce = comps_evap[i % len(comps_evap)]
        pat = evap_patrones[i % len(evap_patrones)]
        texto = pat.format(nivel=n, estado_valvula=ev, dtc=de, sonido=so, componente_evap=ce, dtc_fuga=de)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_evap, "sistema": "MOTOR"})

    # 3. Catalizador P0420 / P0430
    f_cat = "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)"
    cat_patrones = [
        "Luz de check engine fija con codigo {dtc}, monitor de eficiencia de conversion catalitica reprobado",
        "En la grafica del escaner el sensor de oxigeno downstream 2 copia la forma de onda del sensor 1 sin amortiguar la senal",
        "Perdida progresiva de potencia en pendientes y carreteras, motor no desarrolla mas de {rpm} rpm por contrapresion de escape tapada",
        "Manometro en rosca del sensor de oxigeno delantero indica {presion} psi de presion en el multiple de escape en ralenti",
        "Sustrato ceramico del catalizador quebrado genera ruido de cascabel metalico dentro del canister de escape bajo el piso",
        "Olor desagradable a azufre y gases picantes saliendo por el tubo de escape con rendimiento de combustible reducido",
        "Prueba de pirómetro infrarrojo muestra que la entrada del catalizador esta a {temp_in} C y la salida a {temp_out} C sin generar calor exotermico",
        "Catalizador obstruido calienta excesivamente el piso del habitaculo y multiple de escape se torna incandescente",
        "Vehiculo rechazado en inspeccion tecnica vehicular por hidrocarburos y monoxido de carbono altos con codigo P0420",
        "Falla de desahogo del motor en alta velocidad provocada por panal de ceramica fundido en el primer convertidor"
    ]
    dtcs_cat = ["P0420 banco 1", "P0430 banco 2", "P0420 Catalyst Efficiency Below Threshold", "P0430 Catalyst System Efficiency"]
    rpms = ["3000", "3500", "4000", "2800"]
    presiones = ["3.5", "4.0", "5.0", "6.5"]
    temp_in = ["320", "350", "380"]
    temp_out = ["290", "310", "330"]

    for i in range(50):
        dc = dtcs_cat[i % len(dtcs_cat)]
        rp = rpms[i % len(rpms)]
        pr = presiones[i % len(presiones)]
        tin = temp_in[i % len(temp_in)]
        tout = temp_out[i % len(temp_out)]
        pat = cat_patrones[i % len(cat_patrones)]
        texto = pat.format(dtc=dc, rpm=rp, presion=pr, temp_in=tin, temp_out=tout)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_cat, "sistema": "MOTOR"})

    # 4. Regulador de presión de combustible
    f_reg = "Falla en regulador de presion de combustible o diafragma roto"
    reg_patrones = [
        "Diafragma del regulador de presion de gasolina roto {fuga} hacia la manguera de vacio que conecta al multiple",
        "Presion de riel medida con manometro se eleva a {presion_psi} psi excediendo el limite especificado de 40 psi",
        "Al desconectar la toma de vacio del regulador de presion de nafta sale combustible liquido en abundancia",
        "Dificultad de encendido en caliente por ahogo excesivo y bujias empapadas de combustible no quemado",
        "Humo negro denso por el tubo de escape con fuerte olor a gasolina cruda y fuel trims en menos 25 por ciento",
        "Regulador mecanico de presion no retiene presion residual al apagar el motor y cae a cero en {segundos} segundos",
        "Resorte interno del regulador vencido no permite aumentar el caudal y la presion cae fuertemente al acelerar",
        "Mezcla sumamente rica en ralenti provocada por nafta que se filtra directamente por la linea de vacio del regulador",
        "Bujias carbonizadas en los 4 cilindros por exceso de presion en la rampa de inyeccion de combustible",
        "Tirones por sobrepresion de gasolina en el riel de inyectores con codigos de mezcla rica permanente"
    ]
    fugas = ["fuga nafta pura", "pasa gasolina liquida", "chorrea combustible crudo"]
    presiones_reg = ["60", "65", "70", "75"]
    segs = ["3", "5", "8", "10"]

    for i in range(50):
        fu = fugas[i % len(fugas)]
        pr = presiones_reg[i % len(presiones_reg)]
        sg = segs[i % len(segs)]
        pat = reg_patrones[i % len(reg_patrones)]
        texto = pat.format(fuga=fu, presion_psi=pr, segundos=sg)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_reg, "sistema": "MOTOR"})

    # 5. Circuito de inyector
    f_iny = "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
    iny_patrones = [
        "Codigo de falla {dtc} en scanner, cilindro {cil} completamente inactivo tanto en ralenti como al acelerar",
        "Medicion con multimetro en el inyector del cilindro {cil} marca resistencia {resistencia} confirmando solenoide cortado",
        "Punta logica conectada al conector del inyector {cil} no parpadea al dar marcha por falta de senal de conmutacion a masa",
        "Cable de control del inyector {cil} cortado en el arnes principal cerca de la tapa de balancines",
        "Conector electrico del inyector numero {cil} quebrado con pines sulfatados que hacen falso contacto intermitente",
        "DTC {dtc} injector circuit open, el motor tiembla fuertemente en tres cilindros de forma continua",
        "Driver de potencia del inyector {cil} dentro de la computadora de motor quemado no entrega pulso de inyeccion",
        "El cilindro {cil} no trabaja a pesar de intercambiar bujia y bobina, la prueba confirma solenoide de inyector abierto",
        "Falla de encendido estatica en cilindro {cil} originada por corte electrico en la linea positiva de 12V del inyector",
        "Inyector {cil} no acciona su aguja interna ni emite clic acustico verificado con estetoscopio de mecanico"
    ]
    dtcs_iny = ["P0201", "P0202", "P0203", "P0204"]
    cils = ["1", "2", "3", "4"]
    resists = ["infinita (circuito abierto)", "de 0.2 ohms (cortocircuito total)", "mayor a 100 kilo-ohms", "abierta en circuito"]

    for i in range(50):
        di = dtcs_iny[i % len(dtcs_iny)]
        cl = cils[i % len(cils)]
        rs = resists[i % len(resists)]
        pat = iny_patrones[i % len(iny_patrones)]
        texto = pat.format(dtc=di, cil=cl, resistencia=rs)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_iny, "sistema": "MOTOR"})

    # 6. Pérdida de compresión de cilindro
    f_comp = "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados"
    comp_patrones = [
        "Cilindro {cil} sin compresion: manometro marca {psi} psi mientras los otros cilindros registran 160 psi parejos",
        "Falla de cilindro constante en caliente, se cambiaron bujias bobina e inyector pero la prueba de compresion confirma falla mecanica",
        "Prueba de fugas de cilindro leakdown test en cilindro {cil} muestra {fuga_pct} por ciento de fuga de aire hacia {escape_aire}",
        "Valvula de escape del cilindro {cil} quemada o con asiento carbonizado no sella la presion de combustion",
        "Anillos de compresion pegados o rotos en piston {cil} permiten paso de compresion hacia el carter generando humo por la varilla",
        "Motor cojea en ralenti con soplido rítmico audible en el multiple de admision por valvula de admision pisada",
        "Prueba humeda con chorro de aceite eleva la compresion de {psi_baja} a {psi_alta} psi verificando desgaste en anillos",
        "Asiento de valvula descalibrado deja la valvula sin juego de taques impidiendo su cierre hermetico en temperatura de operacion",
        "Piston con fisura o anillos alineados pierden la compresion provocando codigo persistente de misfire en cilindro {cil}",
        "Vibracion fuerte en ralenti por desbalance de compresion de mas del 40 por ciento entre cilindros del motor"
    ]
    cils_comp = ["1", "2", "3", "4"]
    psis = ["50", "60", "70", "80"]
    fugas_pct = ["40", "50", "60", "75"]
    escapes = ["el multiple de admision (valvula pisada)", "el tubo de escape (valvula de escape quemada)", "el tapon de aceite (anillos gastados)"]
    psis_b = ["55", "65", "75"]
    psis_a = ["135", "145", "155"]

    for i in range(50):
        cl = cils_comp[i % len(cils_comp)]
        ps = psis[i % len(psis)]
        fp = fugas_pct[i % len(fugas_pct)]
        es = escapes[i % len(escapes)]
        pb = psis_b[i % len(psis_b)]
        pa = psis_a[i % len(psis_a)]
        pat = comp_patrones[i % len(comp_patrones)]
        texto = pat.format(cil=cl, psi=ps, fuga_pct=fp, escape_aire=es, psi_baja=pb, psi_alta=pa)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_comp, "sistema": "MOTOR"})

    # 7. Cáliper trabado
    f_cal = "Caliper de freno trabado o mordaza pegada (piston agarrotado)"
    cal_patrones = [
        "Rueda delantera {lado} recalienta exageradamente tras rodar {minutos} minutos con olor a pastilla chamuscada",
        "El carro tira y se jala fuertemente hacia el lado {lado} en linea recta sin necesidad de accionar el pedal de frenos",
        "Piston del caliper de freno trabado con corrosion interna y guardapolvo roto no libera la presion sobre el disco",
        "Pernos pasadores guia de la mordaza totalmente secos sin lubricante impiden el desplazamiento flotante de la pinza",
        "Pastilla de freno interna de la rueda {lado} gastada hasta el metal mientras la pastilla exterior tiene 60 por ciento de espesor",
        "Al suspender el vehiculo la rueda {lado} se encuentra completamente bloqueada y no gira con fuerza manual",
        "Humo y calor radiante saliendo del aro {lado} tras conducir en autopista a velocidad constante",
        "Disco de freno de la rueda {lado} presenta coloracion azul violacea y alabeo por friccion continua involuntaria",
        "Flexible de freno delantero colapsado internamente no permite el retorno del fluido manteniendo el caliper accionado",
        "Aumento en el consumo de gasolina y sensacion de carro amarrado o frenado provocado por pinza de freno pegada"
    ]
    lados = ["izquierdo", "derecho", "delantero derecho", "delantero izquierdo", "trasero derecho", "trasero izquierdo"]
    mins = ["10", "15", "20", "25"]

    for i in range(50):
        ld = lados[i % len(lados)]
        m = mins[i % len(mins)]
        pat = cal_patrones[i % len(cal_patrones)]
        texto = pat.format(lado=ld, minutos=m)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_cal, "sistema": "FRENOS"})

    # 8. Collarín de empuje de embrague
    f_col = "Desgaste en collarin de empuje o crapodina de embrague"
    col_patrones = [
        "Ruido de chillido metalico agudo o rozamiento chirriante que suena exclusivamente cuando piso el pedal de embrague",
        "Al presionar el embrague a fondo para realizar el cambio de marcha aparece un zumbido fuerte que desaparece al soltar el pedal",
        "Crapodina o ruleman de empuje sin lubricacion genera vibracion y quejido chirriante al apoyar contra el diafragma de la prensa",
        "Pulsacion y temblor perceptible en la planta del pie al momento de desembragar con motor en marcha",
        "En punto muerto con el pedal suelto el vehiculo no produce ningun ruido, pero al pisar el pedal chilla de inmediato",
        "Rodamiento del collarin agarrotado roza metal con metal contra las puntas del resorte de diafragma del plato",
        "Chirrido estridente al mantener el embrague presionado esperando la luz verde del semaforo",
        "Collarin hidraulico con pistas con pitting y bolas picadas produce rumor seco solo bajo carga del pedal",
        "Zumbido chirriante en la campana de transmision que se corta en el instante en que retiro el pie del pedal de clutch",
        "Ruido de rodamiento desgastado que se activa al accionar el bombin de embrague contra el diafragma"
    ]
    for i in range(50):
        pat = col_patrones[i % len(col_patrones)]
        casos.append({"sintoma": f"Vehiculo {i+1}: {pat}", "falla": f_col, "sistema": "TRANSMISION"})

    # 9. Rodajes de caja manual / eje primario
    f_eje = "Rodajes de transmision manual o eje primario gastados"
    eje_patrones = [
        "Con el motor encendido en neutro suena un ronroneo continuo en la caja, pero al pisar el embrague el ruido desaparece por completo",
        "Zumbido permanente de rodajes dentro de la caja de cambios mecanica que se apaga al desembragar y detener el eje de entrada",
        "Rodamiento del arbol primario de transmision con pistas picadas zumba constantemente en marcha neutra y acelerando",
        "Al pisar el pedal de clutch se corta el sonido de engranajes y rulemanes girando en la caja manual",
        "Ruido como de licuadora o cascabel en la transmision con vehiculo detenido que cesa al pisar el pedal a fondo",
        "Rodajes conicos de apoyo del eje principal de caja desgastados producen zumbido que sube con las revoluciones del motor",
        "Falta de lubricacion en la transmision provoco desgaste en los rodamientos del tren de engranajes con zumbido en neutro",
        "Sonido de rodadura interna en caja de velocidades que solo se manifiesta cuando el eje primario esta girando embragado",
        "Aspereza y rumor mecanico en la palanca de cambios en ralenti que se elimina al presionar el embrague",
        "Zumbido continuo en transmision manual presente en punto muerto y en marchas intermedias que cesa al desembragar"
    ]
    for i in range(50):
        pat = eje_patrones[i % len(eje_patrones)]
        casos.append({"sintoma": f"Vehiculo {i+1}: {pat}", "falla": f_eje, "sistema": "TRANSMISION"})

    # 10. Rodamiento de maza / rueda
    f_rod = "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)"
    rod_patrones = [
        "Zumbido sordo y grave de rodadura a partir de {vel} km/h que se intensifica claramente al tomar curva hacia {curva}",
        "Ruido continuo como de avion a helice en las ruedas que incrementa su frecuencia y volumen a mayor velocidad",
        "Al doblar hacia la {curva} el zumbido de rueda {comportamiento} al cargarse el peso sobre la rueda exterior",
        "Prueba con estetoscopio y giro manual de la rueda en el elevador revela aspereza y holgura en el rodamiento de maza",
        "Rodaje sellado de buje de rueda delantera con fatiga superficial en las pistas genera zumbido de rozamiento constante",
        "Vibracion de alta frecuencia perceptible en el piso y timon provocada por rodamiento de rueda picado",
        "El zumbido de rodadura no cambia si piso el freno o si pongo la caja en neutro rodando en bajada",
        "Maza de rueda toma temperatura excesiva por rodamiento sin grasa sintetica con pistas con picaduras de oxido",
        "Sonido de rodaje wub wub en la rueda trasera que se vuelve insoportable en autopista sobre asfalto parejo",
        "Juego de cojinete de rueda perceptible al bambolear la llanta con las manos a las 12 y 6 horas"
    ]
    vels = ["50", "60", "70", "80", "90"]
    curvas = ["la derecha cargando la rueda izquierda", "la izquierda cargando la rueda derecha", "curva abierta en carretera"]
    comps_r = ["aumenta fuertemente de volumen", "se agudiza de forma evidente", "se intensifica de manera notoria"]

    for i in range(50):
        v = vels[i % len(vels)]
        c = curvas[i % len(curvas)]
        cr = comps_r[i % len(comps_r)]
        pat = rod_patrones[i % len(rod_patrones)]
        texto = pat.format(vel=v, curva=c, comportamiento=cr)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_rod, "sistema": "SUSPENSION_CHASIS"})

    # 11. Motor de arranque / solenoide
    f_arr = "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)"
    arr_patrones = [
        "Giro la llave a la posicion START y solo se escucha un clac seco pero el motor de arranque no gira nada",
        "Bateria completamente cargada a {volts} voltios pero al dar contacto se oye un solo clic metalico y no da marcha",
        "Tengo que darle unos golpes suaves a la carcasa del motor de arranque para que los carbones hagan contacto y encienda",
        "Escobillas y carbones del arrancador totalmente consumidos no transmiten la corriente al colector del inducido",
        "Terminal 50 del solenoide recibe 12V con la llave en arranque pero los contactos internos fogueados impiden girar",
        "El motor de arranque se queda mudo de manera aleatoria, a veces prende normal y otras veces no hace ningun sonido",
        "Solenoide de arranque con bobina de retencion cortada produce golpeteo clac clac sin engranar el bendix",
        "Faros del vehiculo alumbran con maxima potencia y testigos firmes, pero el arrancador no reacciona al dar arranque",
        "Bendix o motor de arranque gira en vacio zumbando a alta velocidad sin acoplar a la corona del volante motor",
        "Falso contacto en la linea de alimentacion del arrancador deja el vehiculo sin poder dar marcha sin aviso previo"
    ]
    volts_arr = ["12.5", "12.6", "12.7", "12.8"]
    for i in range(50):
        va = volts_arr[i % len(volts_arr)]
        pat = arr_patrones[i % len(arr_patrones)]
        texto = pat.format(volts=va)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_arr, "sistema": "ELECTRICO"})

    # 12. Fuga parásita de corriente en reposo
    f_fuga = "Fuga parasita de corriente en reposo (consumo nocturno de bateria)"
    fuga_patrones = [
        "Bateria amanece totalmente descargada a {volts_baja}V si dejo el auto estacionado de un dia para otro",
        "Bateria nueva instalada hace una semana se drena sola despues de 48 horas sin encender el vehiculo",
        "Medicion con multimetro en serie en borne negativo marca {ma} miliamperios de consumo parasito en reposo con llave fuera",
        "Modulo electronico de confort BCM o radio no entra en modo reposo y sigue consumiendo {amperios} amperios apagado",
        "Luz interior de la maletera o guantera permanece encendida con la tapa cerrada descargando la bateria por la noche",
        "Alternador carga perfecto a 14.2 voltios pero el carro amanece sin bateria por fuga parásita continua",
        "Al retirar los fusibles uno por uno el consumo cae a 25 mA al desconectar el circuito del fusible de accesorios",
        "Alarma o sistema de rastreo satelital GPS defectuoso tiene consumo excesivo de corriente que agota la bateria",
        "Consumo en reposo de mas de {ma} mA excede por mucho la norma tecnica de maximo 50 mA segun manual OEM",
        "Si desconecto el borne de la bateria al parquearlo arranca al primer toque al dia siguiente confirmando fuga"
    ]
    volts_b = ["11.2", "11.5", "10.8", "9.5"]
    mas = ["250", "350", "450", "600"]
    amps = ["0.35", "0.45", "0.60", "0.80"]

    for i in range(50):
        vb = volts_b[i % len(volts_b)]
        m = mas[i % len(mas)]
        a = amps[i % len(amps)]
        pat = fuga_patrones[i % len(fuga_patrones)]
        texto = pat.format(volts_baja=vb, ma=m, amperios=a)
        casos.append({"sintoma": f"Vehiculo {i+1}: {texto}", "falla": f_fuga, "sistema": "ELECTRICO"})

    # 13. Maxi-Brake (Freno de aire)
    f_maxi = "Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)"
    maxi_patrones = [
        "Camion de carga con sistema de frenos de aire tiene la rueda trasera {lado} totalmente bloqueada y arrastrando neumático",
        "Al liberar la valvula amarilla de parqueo del tablero la camara de resorte Maxi-Brake {lado} no comprime el resorte",
        "Presion de aire en manometros marca 8.5 bares pero el diafragma de la camara de estacionamiento pierde aire por el orificio de alivio",
        "Fuga continua de aire a presion en el actuador elastico Maxi-Brake impide que las balatas de freno se separen del tambor",
        "Camara combinada de servicio y emergencia tipo 30/30 trabada mecanicamente por resorte de alta potencia roto",
        "Ruedas motrices posteriores bloqueadas sin poder mover el camion por falta de liberacion neumatica en el actuador",
        "Olor a balata quemada y humo en el eje trasero provocado por camara Maxi-Brake que no retrae la varilla de empuje",
        "Falla de desenganche del freno de resorte de seguridad por rotura del sello diafragma en la seccion de parqueo",
        "Perdida de aire acelerada al accionar el pedal de freno por cilindro de freno neumatico Maxi-Brake fisurado",
        "Tornillo de descompresion manual de la camara Maxi-Brake tuvo que ser ajustado para poder destrabar la rueda del camion"
    ]
    lados_m = ["derecha", "izquierda", "trasera motriz derecha", "trasera motriz izquierda"]
    for i in range(50):
        lm = lados_m[i % len(lados_m)]
        pat = maxi_patrones[i % len(maxi_patrones)]
        texto = pat.format(lado=lm)
        casos.append({"sintoma": f"Camion {i+1}: {texto}", "falla": f_maxi, "sistema": "CARROCERIA_NEUMATICA"})

    return casos
