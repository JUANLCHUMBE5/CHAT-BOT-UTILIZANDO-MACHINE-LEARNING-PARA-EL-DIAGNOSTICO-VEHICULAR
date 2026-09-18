"""
Generador modular de casos independientes de MOTOR para Fase 8.
Genera datos de entrenamiento independientes basados en sintomatología técnica y de taller.
Blindaje: Totalmente disjunto del benchmark TEST G1_01-G1_50.
"""

from typing import Dict, List


def obtener_casos_motor_fase8() -> List[Dict[str, str]]:
    casos = []

    # 1. CKP / CMP
    f_ckp = "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)"
    s_ckp = [
        "Despues de andar 30 minutos por carretera el motor se apaga de golpe, giro la llave y da marcha con buena fuerza pero no arranca hasta que se enfria media hora",
        "Tengo codigo P0335 en scanner, el motor gira al dar arranque pero no hay senal de encendido ni chispa en las bujias",
        "El carro se detiene en caliente como si le cortaran la corriente de golpe, espero que baje la temperatura y prende normal al primer toque",
        "Falla intermitente en sensor inductivo de cigueñal, con osciloscopio la senal de onda senoidal se corta cuando sube la temperatura del bloque",
        "Codigo P0336 en escaner, sensor de cigueñal no registra pulsos de RPM mientras gira el motor de arranque",
        "Al acelerar a 3000 rpm la aguja del tacometro cae abruptamente a cero y el motor tironea fuerte antes de apagarse, sensor ckp sospechoso",
        "Motor gira con velocidad adecuada pero la computadora no detecta giro de cigueñal y corta inyeccion de combustible",
        "El motor pierde pulso de inyectores y pulso de chispa en caliente, el sensor de posicion de cigueñal marca circuito abierto al calentarse",
        "P0340 falla en circuito del sensor de posicion de arbol de levas banco 1, tarda mucho en encender dando arranque prolongado",
        "Arranca perfecto por la manana en frio, pero despues de calentar a 90 grados si lo apago no vuelve a prender hasta que se enfria por completo",
        "Sensor de cigueñal tipo Hall pierde alimentacion de 5 voltios o senal de salida cuadrada se degrada con la vibracion",
        "DTC P0335 Crankshaft Position Sensor Circuit Malfunction, vehiculo no enciende en caliente gira motor pero no arranca",
        "El motor se muere de repente al parar en un semaforo despues de un viaje largo, arrancador gira rapido pero no hay combustion",
        "Falta de sincronizacion entre ckp y cmp por sensor de posicion con bobinado abierto por fatiga termica",
        "Sensor de cigueñal sucio con virutas metalicas en la punta no genera suficiente voltaje en el entrehierro",
        "En autopista se apago el motor de improvisto, no hay chispa en ninguna bobina y la bomba no activa por falta de pulso ckp",
        "El escaner no muestra revoluciones por minuto durante el arranque, indicando fallo total de senal del sensor ckp",
        "Vehiculo tironea violentamente al calentar y se apaga, en el scanner aparece DTC P0335",
        "Corte repentino de encendido en caliente, sin codigos de encendido pero sin senal de RPM en linea de datos",
        "Sensor ckp magnetico pierde inductancia al llegar a temperatura de operacion impidiendo el arranque",
    ]
    for s in s_ckp:
        casos.append({"sintoma": s, "falla": f_ckp, "sistema": "MOTOR"})

    # 2. EVAP
    f_evap = "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)"
    s_evap = [
        "Apenas termino de llenar el tanque de gasolina en el grifo el carro le cuesta arrancar y sale olor fuerte a nafta en el escape",
        "Valvula de purga del canister se quedo trabada abierta, succiona vapores en exceso y ahoga el motor en ralenti tras cargar combustible",
        "DTC P0440 en scanner falla en el sistema de control de emisiones por evaporacion",
        "DTC P0442 deteccion de fuga pequena en sistema EVAP canister o manguera agrietada",
        "DTC P0455 fuga grande detectada en el sistema EVAP, sello de tapa de combustible danado o linea de purga desconectada",
        "Olor penetrante a gasolina dentro de la cabina y cerca del guardabarros trasero despues de tanquear a full",
        "Al retirar la tapa del tanque de combustible se escucha un fuerte silbido de succion de vacio por solenoide de purga trabado",
        "Ralenti inestable y mezcla excesivamente rica solo inmediatamente despues de poner gasolina en la estacion de servicio",
        "Canister de carbon activado inundado con combustible liquido por sobrellenar el tanque",
        "Solenoide de purga EVAP no cierra hermeticamente cuando se le aplica vacio con bomba manual Mityvac",
        "Luz de check engine encendida con codigo P0441 flujo incorrecto de purga del sistema evaporativo",
        "Motor se ahoga y bajan las revoluciones al detenerse luego de repostar combustible, valvula purga canister permeable",
        "Prueba de humo en sistema EVAP muestra fuga de humo por el respiradero de la valvula de ventilacion del canister",
        "Olor a gases de gasolina en el compartimiento del motor cerca del solenoide de purga del multiple de admision",
        "Codigo P0456 microfuga en sistema EVAP canister, empaque de tapa de tanque agrietado",
    ]
    for s in s_evap:
        casos.append({"sintoma": s, "falla": f_evap, "sistema": "MOTOR"})

    # 3. Catalizador P0420
    f_cat = "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)"
    s_cat = [
        "Check engine prendido con scanner marcando P0420 eficiencia del sistema de catalizador por debajo del umbral banco 1",
        "En la grafica del scanner el sensor de oxigeno downstream oscila identico al sensor upstream indicando que el catalizador no almacena oxigeno",
        "DTC P0430 eficiencia de catalizador banco 2 insuficiente, no supera la prueba de gases contaminantes por hidrocarburos y monoxido",
        "Perdida de fuerza notable en subidas y alta velocidad por catalizador tapado, contrapresion de escape superior a 3 psi en ralenti",
        "Al acelerar a fondo el motor no pasa de 3500 rpm y se escucha un soplido ahogado por convertidor catalitico obstruido",
        "Sustrato ceramico del catalizador fundido o desprendido genera un cascabeleo y sonido metalico dentro del tubo de escape",
        "Temperatura a la salida del catalizador es menor que a la entrada con pirómetro laser, indicando catalizador inactivo que no realiza conversion",
        "Consumo excesivo de combustible y falta de potencia con codigo OBD2 P0420 Catalyst System Efficiency Below Threshold",
        "El carro huele a azufre y huevo podrido por el tubo de escape y no tiene fuerza en pendientes pronunciadas",
        "Monitoreo OBD2 del catalizador no completa ciclo y arroja falla constante P0420",
        "Multiple de escape se pone al rojo vivo por exceso de contrapresion causada por ceramica catalitica tapada",
        "Prueba de manometro en rosca de sensor de oxigeno delantero marca 5 psi de presion de escape, catalizador obstruido",
        "Catalizador ceramico roto por golpe en el chasis produce ruido de piedritas adentro del silenciador de escape",
        "Luz MIL encendida con P0420 tras cambiar sensor de oxigeno, la lectura confirma convertidor catalitico agotado",
        "Emisiones de gases rechazadas en la revision tecnica por falla de conversion catalitica del convertidor de gases",
    ]
    for s in s_cat:
        casos.append({"sintoma": s, "falla": f_cat, "sistema": "MOTOR"})

    # 4. Regulador de presión de combustible
    f_reg = "Falla en regulador de presion de combustible o diafragma roto"
    s_reg = [
        "Diafragma del regulador de presion roto pasa gasolina pura a traves de la manguera de vacio directo al multiple de admision",
        "Al desconectar la manguera de vacio del regulador de presion de combustible gotea nafta liquida",
        "Bujias salen completamente negras y humedas de gasolina cruda, humo negro por escape y olor fuerte a combustible",
        "Presion de combustible en el riel de inyectores se dispara a mas de 65 psi cuando el manual especifica maximo 43 psi con vacio",
        "Dificultad severa para encender el motor en caliente porque se ahoga por exceso de combustible acumulado en la admision",
        "Valvula reguladora de presion no mantiene presion residual al apagar el motor y se descarga la linea a cero bares inmediatamente",
        "Regulador de presion trabado cerrado produce mezcla sumamente rica y pulsos de inyeccion negativos en los fuel trims STFT y LTFT",
        "El carro consume el doble de gasolina, tira humo negro por el escape y la admision esta empapada de nafta por diafragma roto",
        "Regulador mecanico de riel de inyeccion con resorte vencido no eleva presion bajo aceleracion a fondo",
        "Presion de nafta inestable oscila violentamente en el manometro del riel de combustible en ralenti",
        "Al dar arranque huele mucho a nafta por la admision y el motor tose ahogado por nafta filtrada por la manguerita de vacio",
        "Regulador de presion de gasolina danado genera codigo de mezcla rica permanente P0172",
    ]
    for s in s_reg:
        casos.append({"sintoma": s, "falla": f_reg, "sistema": "MOTOR"})

    # 5. Circuito de inyector (P0201 - P0208)
    f_iny = "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
    s_iny = [
        "Scanner arroja DTC P0202 circuito abierto en inyector numero 2, motor cojea en 3 cilindros permanentemente",
        "Codigo P0201 circuito de inyector cilindro 1 defectuoso, la resistencia del inyector marca infinito con el multimetro",
        "DTC P0203 injector circuit open cylinder 3, no hay pulso de disparo negativo desde la computadora al inyector",
        "Conector de inyector del cilindro 4 quebrado o con cables pelados hace falso contacto y genera P0204",
        "Falla de cilindro constante en caliente y en frio, con punta logica no destella el pulso del inyector afectado",
        "Solenoide de inyector quemado con resistencia en cortocircuito inferior a 1 ohm cuando debe marcar 14 ohms",
        "Falla cilindro 2 permanentemente, cambie bujias y bobina pero sigue cojeando y el scanner marca P0202",
        "Arnes electrico de inyectores rozando contra la tapa de punterias tiene cable a tierra del inyector cortado",
        "DTC P0200 falla general en circuito de control de inyectores de combustible",
        "Driver de inyector en la ECM danado no commuta a tierra el solenoide del inyector del cilindro numero 1",
        "Inyector numero 3 no produce clic audible con estetoscopio de mecanico y registra falla electrica P0203",
        "Falla de encendido en cilindro 2 provocada por corte electrico en la linea de senal del inyector P0202",
    ]
    for s in s_iny:
        casos.append({"sintoma": s, "falla": f_iny, "sistema": "MOTOR"})

    # 6. Pérdida de compresión
    f_comp = "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados"
    s_comp = [
        "Falla un cilindro permanentemente, ya intercambie bujia, bobina e inyector y la falla no se mueve del cilindro 1",
        "Medicion de compresion en seco marca 70 psi en cilindro 3 y 160 psi en los otros tres cilindros",
        "Prueba de compresion humeda con aceite eleva la presion de 60 a 140 psi confirmando desgaste severo de anillos de piston",
        "Prueba de fugas de cilindro leak-down test revela 45% de fuga con escape de aire soplado por el multiple de admision valvula pisada",
        "Valvula de escape quemada no sella hermeticamente produciendo falla de fuego constante y piston sin compresion",
        "Motor tiembla en ralenti desparejo, cambie bujias y bobinas nuevas pero el cilindro 4 no tiene nada de compresion",
        "Soplido por la varilla medidora de aceite o tapon de llenado blow-by excesivo por anillos de compresion rotos o pegados",
        "Luz de check parpadea P0301, se descartaron bujias bobina y cables, manometro confirma 50 psi en cilindro 1",
        "Asiento de valvula carbonizado o valvula doblada por salto de punto no retiene compresion de la camara",
        "Al medir compresion con manometro motor gira disparejo al dar arranque por falta de compresion en un cilindro",
        "El cilindro 2 no quema la mezcla a pesar de haber chispa azul potente e inyeccion verificada con probeta, falta compresion mecanica",
        "Valvula de admision sin holgura queda pisada en caliente perdiendo toda la estanqueidad y presion de combustion",
    ]
    for s in s_comp:
        casos.append({"sintoma": s, "falla": f_comp, "sistema": "MOTOR"})

    return casos
