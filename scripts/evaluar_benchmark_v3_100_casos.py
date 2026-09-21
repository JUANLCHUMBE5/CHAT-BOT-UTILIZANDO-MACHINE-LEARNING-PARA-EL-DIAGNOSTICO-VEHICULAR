"""
Benchmark Externo V3 (100 Casos Completamente Nuevos e Inéditos)
Evaluación de validación ciega post-entrenamiento para contrastar con Benchmark V2.
Calcula métricas externas estrictas, Top-3, RAG Hit@K/MRR y comparativa lado a lado V2 vs V3.
"""

import sys
import json
import time
import re
from pathlib import Path
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.infrastructure.container import ServiceContainer
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema, obtener_sistema_por_dtc
from evaluar_rag_relevancia import es_procedimiento_relevante


# 50 CASOS INÉDITOS - GRUPO 1 (Taller / Modelo vehicular / DTC)
BENCHMARK_V3_G1 = [
    # 01
    ("Toyota Rav4 2019 parpadea check en subida, motor tironea y vibra fuerte al acelerar a fondo, scanner marca P0304.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Inyectores sucios o filtro de combustible obstruido"], "P0304"),
    # 02
    ("Kia Cerato 2018 arranca bien pero en baja revoluciones cabecea bastante y al pisar gas pierde fuerza.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Bomba de gasolina quemada o con baja presion"], None),
    # 03
    ("Hyundai Grand i10 2017 un cilindro no quema parejo, cambie bobinas pero persiste la falla en minimo.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 04
    ("Nissan Qashqai 2018 tironea cuando calienta despues de 20 minutos de manejo, en frio anda perfecto.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Bomba de gasolina quemada o con baja presion"], None),
    # 05
    ("Suzuki Swift 2020 registra P0171, motor acelerado y se percibe soplido de vacio en la admision.",
     "Falla en servofreno (booster) o linea de vacio", ["Cuerpo de aceleracion o valvula IAC sucia"], "P0171"),
    # 06
    ("Toyota Hilux 2017 tablero ilumina normal pero al dar contacto solo se escucha clac y arrancador no mueve motor.",
     "Bateria descargada o bornes sulfatados", ["Alternador defectuoso o placa de diodos quemada"], None),
    # 07
    ("Kia Sorento 2016 se apago rodando, voltaje medido en bornes con motor prendido marca 11.9 voltios.",
     "Alternador defectuoso o placa de diodos quemada", ["Bateria descargada o bornes sulfatados"], None),
    # 08
    ("Hyundai Creta 2019 bateria amanece muerta si el carro duerme sin desconectar el borne negativo.",
     "Bateria descargada o bornes sulfatados", ["Alternador defectuoso o placa de diodos quemada"], None),
    # 09
    ("Nissan Tiida 2015 luz de bateria en tablero destella cuando enciendo el aire y faros principales.",
     "Alternador defectuoso o placa de diodos quemada", ["Bateria descargada o bornes sulfatados"], None),
    # 10
    ("Chevrolet Sail 2018 testigo de bateria activo y escaner lee P0562 tension del sistema por debajo de 12V.",
     "Alternador defectuoso o placa de diodos quemada", ["Bateria descargada o bornes sulfatados"], "P0562"),
    # 11
    ("Toyota Rush 2019 pedal de freno durisimo cuesta detener el auto y sisea aire al presionarlo.",
     "Falla en servofreno (booster) o linea de vacio", [], None),
    # 12
    ("Kia Soluto 2020 pedal de freno se hunde lentamente en semaforos mientras lo piso sin fuga exterior.",
     "Fuga hidraulica o aire en el sistema de frenos", ["Desgaste de pastillas y zapatas de freno"], None),
    # 13
    ("Mazda 2 2018 volante vibra fuerte unicamente cuando presiono el freno a 90 km/h en bajada.",
     "Discos de freno alabeados o desgastados", ["Llantas desbalanceadas o desalineadas"], None),
    # 14
    ("Hyundai i20 2019 volante sacude entre 95 y 115 km/h pero al frenar suave no cambia la vibracion.",
     "Llantas desbalanceadas o desalineadas", ["Amortiguadores reventados o bujes de suspension gastados"], None),
    # 15
    ("Nissan Kicks 2019 rueda delantera izquierda quema al tacto despues de 10 km y desvia el volante a la izquierda.",
     "Desgaste de pastillas y zapatas de freno", ["Llantas desbalanceadas o desalineadas"], None),
    # 16
    ("Toyota Yaris 2016 recalienta en embotellamientos pero al salir a carretera libre la aguja baja al centro.",
     "Falla en termostato o motoventilador de radiador", ["Fuga en mangueras de refrigerante o radiador picado"], None),
    # 17
    ("Corolla 2015 burbujeo constante en reservorio de refrigerante y expulsa humo blanco denso por escape.",
     "Empaque de culata soplado o danado", ["Fuga en mangueras de refrigerante o radiador picado"], None),
    # 18
    ("Kia Sportage 2018 aguja de temperatura sube a rojo manguera de radiador superior hirviendo e inferior fria.",
     "Falla en termostato o motoventilador de radiador", ["Fuga en mangueras de refrigerante o radiador picado"], None),
    # 19
    ("Hyundai Accent 2017 testigo rojo de aceite parpadea cuando el motor calienta y queda en ralenti.",
     "Baja presion de aceite o bomba de aceite defectuosa", [], None),
    # 20
    ("Nissan Sentra 2016 quema aceite de motor bota humo azulado al acelerar saliendo de semaforo.",
     "Consumo de aceite por desgaste de anillos o retenes", [], None),
    # 21
    ("Toyota Etios 2018 mecanico acelero en tercera suben revoluciones a 3800 pero velocidad casi no aumenta.",
     "Disco de embrague desgastado o patinando", [], None),
    # 22
    ("Kia Rio 2019 pedal de embrague sin presion cayo al piso y gotea fluido por la campana de transmision.",
     "Falla en bombin o bomba hidraulica de embrague", ["Disco de embrague desgastado o patinando"], None),
    # 23
    ("Hyundai Elantra 2016 zumbido o crujido que aparece al pisar el pedal de embrague y se quita al soltarlo.",
     "Falla en bombin o bomba hidraulica de embrague", ["Rodajes de caja mecanica o diferencial gastados"], None),
    # 24
    ("Corolla mecanico 2017 tiembla y zapatea fuerte la carroceria unicamente al soltar embrague en primera.",
     "Disco de embrague desgastado o patinando", ["Falla en bujias o bobinas de encendido (misfire)"], None),
    # 25
    ("Fiat Palio Dualogic salta a neutro solo en trafico y bomba hidraulica del robot suena continuo.",
     "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)", [], None),
    # 26
    ("Nissan Versa CVT caja entra en limp mode no pasa de 60 km/h y scanner arroja codigo P0841.",
     "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", [], "P0841"),
    # 27
    ("Volkswagen Gol I-Motion demora en acoplar marcha hacia adelante y golpea al calentar en parada.",
     "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG"], None),
    # 28
    ("Toyota Corolla automatico tarda 5 segundos en acoplar reversa en frio y entra con sacudida fuerte.",
     "Falta o degradacion de aceite de caja de cambios", ["Sobrecalentamiento o solenoides en caja automatica CVT / DSG"], None),
    # 29
    ("Yaris 2019 golpeteo seco cloc cloc en la rueda delantera al transitar por adoquines o baches.",
     "Amortiguadores reventados o bujes de suspension gastados", ["Llantas desbalanceadas o desalineadas"], None),
    # 30
    ("Kia Rio 2018 traqueteo seco continuo trac trac en rueda delantera al dar vuelta en U acelerando.",
     "Juntas homocineticas o palieres danados", ["Cremallera de direccion asistida con holgura o fuga"], None),
    # 31
    ("Hyundai Accent 2019 auto rebota tres veces al pasar lomos de burro y flota la cola en curva.",
     "Amortiguadores reventados o bujes de suspension gastados", [], None),
    # 32
    ("Corolla 2018 direccion tira hacia el lado derecho en pista plana despues de pasar un bache profundo.",
     "Llantas desbalanceadas o desalineadas", ["Cremallera de direccion asistida con holgura o fuga"], None),
    # 33
    ("Nissan Tiida 2016 desgaste irregular por la banda interior en ambos neumaticos delanteros.",
     "Llantas desbalanceadas o desalineadas", ["Amortiguadores reventados o bujes de suspension gastados"], None),
    # 34
    ("Toyota Prius 2017 vibracion en volante a 100 km/h despues de montar dos llantas nuevas adelante.",
     "Llantas desbalanceadas o desalineadas", ["Discos de freno alabeados o desgastados"], None),
    # 35
    ("Kia Picanto 2018 zumbido agudo en rueda que se intensifica con la velocidad y varia al girar volante.",
     "Rodajes de caja mecanica o diferencial gastados", ["Llantas desbalanceadas o desalineadas"], None),
    # 36
    ("Corolla 2017 perdida de fuerza en pendientes y presion de combustible cae al exigir aceleracion.",
     "Bomba de gasolina quemada o con baja presion", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 37
    ("Hyundai i10 motor gira con motor de arranque pero no enciende hay chispa y bomba de combustible no zumba.",
     "Bomba de gasolina quemada o con baja presion", [], None),
    # 38
    ("Nissan Sentra 2018 despues de media hora de uso bomba de tanque empieza a aullar y auto pierde potencia.",
     "Bomba de gasolina quemada o con baja presion", ["Falla en bujias o bobinas de encendido (misfire)"], None),
    # 39
    ("Toyota Yaris 2018 ralenti inestable oscila y se apaga al frenar en esquinas, acelerando no falla.",
     "Cuerpo de aceleracion o valvula IAC sucia", ["Bomba de gasolina quemada o con baja presion"], None),
    # 40
    ("Corolla 2019 olor muy penetrante a gasolina cruda por escape humo negro y check prendido.",
     "Falla en sensor de oxigeno o mezcla rica", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 41
    ("Chevrolet Cruze 2017 escaner arroja P0420 eficiencia baja de catalizador check vuelve a prender.",
     "Falla en sensor de oxigeno o mezcla rica", ["Falla en bujias o bobinas de encendido (misfire)"], "P0420"),
    # 42
    ("Toyota Corolla 2018 scanner marca P0301 y P0302 motor tiembla y check destella al acelerar.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Falla en sensor de oxigeno o mezcla rica"], "P0301"),
    # 43
    ("Camion Volvo pierde presion de aire en tanques estacionado por fuga audible en pulmon de rueda trasera.",
     "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)", ["Válvula de freno de aire o secador APS obstruido (Camiones)"], None),
    # 44
    ("Camion Mercedes secador de aire APS descarga y purga cada 10 segundos continuamente sin pisar freno.",
     "Válvula de freno de aire o secador APS obstruido (Camiones)", ["Fugas de aire o fallos en el sistema de frenos neumático (Camiones)"], None),
    # 45
    ("Camion Hino compresor mecanico de aire trabaja todo el tiempo y tarda 40 minutos en cargar 7 bares.",
     "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)", ["Válvula de freno de aire o secador APS obstruido (Camiones)"], None),
    # 46
    ("Toyota Hilux actuador de seguro de puerta trasera suena pero no levanta el pestillo con el control.",
     "Falla electrica del cierre centralizado o actuador de puerta", ["Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado"], None),
    # 47
    ("Kia Cerato seguros electricos no responden a control remoto pero manualmente con llave cierran todos.",
     "Falla electrica del cierre centralizado o actuador de puerta", ["Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado"], None),
    # 48
    ("Cliente reporta que el vehiculo pierde pique despues de rodar y prende check engine sin codigo claro.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Bomba de gasolina quemada o con baja presion", "Falla en sensor de oxigeno o mezcla rica"], None),
    # 49
    ("Vibracion y ruido metalico delantero que aparecio tras golpear llanta en cuneta profunda.",
     "Amortiguadores reventados o bujes de suspension gastados", ["Llantas desbalanceadas o desalineadas", "Juntas homocineticas o palieres danados"], None),
    # 50
    ("Motor vibra en las mañanas consumo de nafta elevado y arranque demorado sin escanear aun.",
     "Falla en sensor de oxigeno o mezcla rica", ["Inyectores sucios o filtro de combustible obstruido", "Bomba de gasolina quemada o con baja presion"], None)
]

# 50 CASOS INÉDITOS - GRUPO 2 (Lenguaje Clínico y Coloquial de Taller)
BENCHMARK_V3_G2 = [
    # 01
    ("Maestro piso el pedal a fondo para rebasar y el carro tironea feo, se chupa y la luz del motor parpadea.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Bomba de gasolina quemada o con baja presion"], None),
    # 02
    ("En recta va tranquilo pero al subir cerro o adelantar se ahoga y debajo del asiento suena un zumbido agudo.",
     "Bomba de gasolina quemada o con baja presion", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 03
    ("A 80 km/h empieza un zumbido como avion en la rueda delantera, al doblar a la izquierda se calla y a la derecha redobla.",
     "Rodajes de caja mecanica o diferencial gastados", ["Llantas desbalanceadas o desalineadas"], None),
    # 04
    ("En carretera rueda sedita pero apenas toco el freno el timon empieza a sacudirse y el pedal me zapatea el pie.",
     "Discos de freno alabeados o desgastados", ["Llantas desbalanceadas o desalineadas"], None),
    # 05
    ("A 90 o 100 el timon empieza a temblar solo en pista lisa, si paso los 115 se quita, sin tocar freno para nada.",
     "Llantas desbalanceadas o desalineadas", ["Discos de freno alabeados o desgastados"], None),
    # 06
    ("Detenido en el semaforo con el pie en el freno siento que el pedal se va escurriendo despacito hacia el fondo.",
     "Fuga hidraulica o aire en el sistema de frenos", ["Desgaste de pastillas y zapatas de freno"], None),
    # 07
    ("Giro la llave y no mueve el motor, solo hace un chasquido clac abajo pero las luces del tablero no bajan.",
     "Bateria descargada o bornes sulfatados", ["Alternador defectuoso o placa de diodos quemada"], None),
    # 08
    ("Arranca al toque en frio, pero tras media hora en trafico se apaga en seco, tengo que esperar que enfrie 20 minutos para prender.",
     "Falla en bujias o bobinas de encendido (misfire)", ["Bomba de gasolina quemada o con baja presion"], None),
    # 09
    ("Llego a una esquina piso neutro y las revoluciones oscilan solas suben y bajan y el motor se muere si prendo el aire.",
     "Cuerpo de aceleracion o valvula IAC sucia", ["Falla en compresor de aire acondicionado o fuga de gas R134a"], None),
    # 10
    ("Paso por pistas adoquinadas o baches pequenos y suena un cloc cloc cloc metalico seco abajo en las ruedas.",
     "Amortiguadores reventados o bujes de suspension gastados", ["Juntas homocineticas o palieres danados"], None),
    # 11
    ("Al doblar cerrado en una esquina en primera acelerando se escucha un traqueteo constante tra tra tra tra en la rueda.",
     "Juntas homocineticas o palieres danados", ["Amortiguadores reventados o bujes de suspension gastados"], None),
    # 12
    ("Acelero en subida el motor se va a 4500 vueltas pero el carro no camina casi nada y sale olor a quemado amargo.",
     "Disco de embrague desgastado o patinando", [], None),
    # 13
    ("Anoche las luces del tablero parpadeaban y la radio se reiniciaba, hoy en la manana fui a arrancar y no dio senal de vida.",
     "Alternador defectuoso o placa de diodos quemada", ["Bateria descargada o bornes sulfatados"], None),
    # 14
    ("A los diez minutos de rodar la aguja de temperatura se va al rojo, manguera superior de radiador hierve y la de abajo fria.",
     "Falla en termostato o motoventilador de radiador", ["Fuga en mangueras de refrigerante o radiador picado"], None),
    # 15
    ("En caliente no quiere arrancar gira y gira el motor, cuando por fin prende tose bota humo negro y huele a gasolina pura.",
     "Inyectores sucios o filtro de combustible obstruido", ["Falla en sensor de oxigeno o mezcla rica"], None),
    # 16
    ("El motor en neutro se queda pegado en 1400 revoluciones y no baja y se escucha un silbido o siseo cerca del multiple.",
     "Cuerpo de aceleracion o valvula IAC sucia", ["Falla en servofreno (booster) o linea de vacio"], None),
    # 17
    ("Solo cuando acelero en tercera o cuarta en carretera la trompa del auto se sacude de lado a lado, al soltar pedal se corta.",
     "Juntas homocineticas o palieres danados", ["Discos de freno alabeados o desgastados"], None),
    # 18
    ("Paso cualquier hueco y el auto sigue rebotando varias veces como lancha y al clavar frenos la trompa se clava al suelo.",
     "Amortiguadores reventados o bujes de suspension gastados", [], None),
    # 19
    ("En neutro sin pisar pedales suena un chillido en la caja, apenas piso el embrague al fondo el ruido desaparece por completo.",
     "Rodajes de caja mecanica o diferencial gastados", ["Falla en bombin o bomba hidraulica de embrague"], None),
    # 20
    ("Al poner primera y soltar embrague se siente un golpe seco adelante como si el motor saltara y pegara en el chasis.",
     "Amortiguadores reventados o bujes de suspension gastados", ["Disco de embrague desgastado o patinando"], None),
    # 21
    ("Doy arranque y el motor no gira, solo hace metralleta rapida tr tr tr y las luces del cuadro parpadean como locas.",
     "Bateria descargada o bornes sulfatados", ["Alternador defectuoso o placa de diodos quemada"], None),
    # 22
    ("En carretera piso a fondo y no pasa de 3000 revoluciones se siente trancado y por la palanca de cambios hierve el calor.",
     "Falla en sensor de oxigeno o mezcla rica", ["Bomba de gasolina quemada o con baja presion"], None),
    # 23
    ("Piso el acelerador de golpe y el motor se queda pensando un segundo no responde de inmediato se siente amarrado.",
     "Cuerpo de aceleracion o valvula IAC sucia", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 24
    ("En autopista la temperatura va normal a la mitad pero apenas entro a embotellamiento el agua empieza a hervir.",
     "Falla en termostato o motoventilador de radiador", [], None),
    # 25
    ("Al pisar el freno suave suena un chillido finito agudo y si piso mas fuerte raspa fierro contra fierro.",
     "Desgaste de pastillas y zapatas de freno", ["Discos de freno alabeados o desgastados"], None),
    # 26
    ("Suelto el volante en recta y el carro jala de golpe a la derecha, me fije y la llanta delantera derecha esta lisa por dentro.",
     "Llantas desbalanceadas o desalineadas", ["Amortiguadores reventados o bujes de suspension gastados"], None),
    # 27
    ("Al girar el volante despacio para parquear suena un crujido seco clac-nic arriba como un resorte grueso que se suelta.",
     "Juntas homocineticas o palieres danados", ["Amortiguadores reventados o bujes de suspension gastados"], None),
    # 28
    ("El auto calienta en subida fuerte, deposito burbujea con fuerza, mangueras duras como piedra y humo blanco dulce en escape.",
     "Empaque de culata soplado o danado", ["Fuga en mangueras de refrigerante o radiador picado"], None),
    # 29
    ("Cada vez que lleno el tanque de nafta a full no quiere prender, tengo que darle arranque con el pedal a fondo tosiendo.",
     "Bomba de gasolina quemada o con baja presion", ["Cuerpo de aceleracion o valvula IAC sucia"], None),
    # 30
    ("En autopista el carro se siente flotante el volante tiene un juego muerto al medio que no responde de inmediato.",
     "Cremallera de direccion asistida con holgura o fuga", ["Llantas desbalanceadas o desalineadas"], None),
    # 31
    ("En las mananas le cuesta mucho prender, arranca pesado y noto que esta tragando el doble de combustible.",
     "Inyectores sucios o filtro de combustible obstruido", ["Falla en sensor de oxigeno o mezcla rica"], None),
    # 32
    ("Al cruzar toda la direccion o subir rampa suena un golpe seco clac fuerte en la rueda y el timon se siente duro por ratos.",
     "Cremallera de direccion asistida con holgura o fuga", ["Juntas homocineticas o palieres danados"], None),
    # 33
    ("Las luces alumbran demasiado brillante por momentos y se quemaron focos, sale olor a huevo podrido y bateria esta caliente.",
     "Alternador defectuoso o placa de diodos quemada", ["Bateria descargada o bornes sulfatados"], None),
    # 34
    ("La rueda delantera derecha se queda frenada sola despues de andar 20 minutos el aro quema y sale olor a balata.",
     "Desgaste de pastillas y zapatas de freno", ["Fuga hidraulica o aire en el sistema de frenos"], None),
    # 35
    ("El pedal de freno se siente esponjoso se va abajo pero si bombeo dos o tres veces seguidas agarra presion arriba.",
     "Fuga hidraulica o aire en el sistema de frenos", ["Falla en servofreno (booster) o linea de vacio"], None),
    # 36
    ("En frio por la manana suena un taqueteo metalico rapido tac tac tac arriba en la tapa del motor luego de calentar se silencia.",
     "Baja presion de aceite o bomba de aceite defectuosa", ["Faja o cadena de distribucion destensada o con salto de punto"], None),
    # 37
    ("A velocidad lenta como a 20 o 30 siento que el carro cabecea de lado a lado como cojo pero el timon no tironea.",
     "Llantas desbalanceadas o desalineadas", ["Juntas homocineticas o palieres danados"], None),
    # 38
    ("Cambiaron la faja de distribucion ayer y el carro quedo desganado tiembla disparejo y suena explosiones sordas por escape.",
     "Faja o cadena de distribucion destensada o con salto de punto", ["Falla en bujias o bobinas de encendido (misfire)"], None),
    # 39
    ("En carretera la aguja de temperatura se cae hasta abajo como si estuviera apagado y adentro la calefaccion tira aire frio.",
     "Falla en termostato o motoventilador de radiador", [], None),
    # 40
    ("Huele fuertisimo a gasolina por el motor bota humo negro y al soltar la manguerita de vacio de la flauta salio chorro de nafta.",
     "Falla en sensor de oxigeno o mezcla rica", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 41
    ("Cuando prendo luces altas la aguja de temperatura salta de golpe a tope aunque el motor este frio y arranque gira pesado.",
     "Bateria descargada o bornes sulfatados", ["Alternador defectuoso o placa de diodos quemada"], None),
    # 42
    ("Tarda cinco segundos continuos de giro para prender check prendido fijo y le falta pique al adelantar.",
     "Falla en sensor de oxigeno o mezcla rica", ["Bomba de gasolina quemada o con baja presion"], None),
    # 43
    ("Acelero suavecito y responde bien pero si hundo el pedal de golpe empieza a toser y pierde toda la fuerza.",
     "Bomba de gasolina quemada o con baja presion", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 44
    ("Prendo el aire acondicionado y suena un chillido fuertisimo de correa el motor tiembla y solo tira aire caliente.",
     "Falla en compresor de aire acondicionado o fuga de gas R134a", ["Alternador defectuoso o placa de diodos quemada"], None),
    # 45
    ("Cuando bajo una cuesta aguantado con el motor y vuelvo a acelerar bota una humareda azul espesa por el escape y luego limpia.",
     "Consumo de aceite por desgaste de anillos o retenes", ["Empaque de culata soplado o danado"], None),
    # 46
    ("Cascabelea el motor al acelerar a medio pedal como si tuviera gasolina barata y por ratos bota humo negro.",
     "Falla en sensor de oxigeno o mezcla rica", ["Falla en bujias o bobinas de encendido (misfire)"], None),
    # 47
    ("El motor calienta solo cuando subo pendientes con carga pesada pero en pista plana la aguja vuelve al medio rapido.",
     "Falla en termostato o motoventilador de radiador", ["Fuga en mangueras de refrigerante o radiador picado"], None),
    # 48
    ("Luz de check engine prendida fija el carro anda bien pero la punta del cano de escape esta negra de hollin y gasta mas nafta.",
     "Falla en sensor de oxigeno o mezcla rica", ["Inyectores sucios o filtro de combustible obstruido"], None),
    # 49
    ("Al acelerar suena un zumbido bronco debajo de los asientos como carro de carrera y parado se mete olor a escape a la cabina.",
     "Falla en sensor de oxigeno o mezcla rica", ["Bomba de gasolina quemada o con baja presion"], None),
    # 50
    ("Pase por un bache y sono un golpe seco de fierro abajo, al mirar el auto parado de frente se nota un lado mas bajo que otro.",
     "Amortiguadores reventados o bujes de suspension gastados", ["Llantas desbalanceadas o desalineadas"], None)
]

def evaluar_benchmark_v3():
    print("\n" + "="*80)
    print("EJECUTANDO BENCHMARK V3 (100 CASOS INÉDITOS)")
    print("================================================================================\n")
    
    modelo_ml = ServiceContainer.get_modelo_ml()
    rag_service = ServiceContainer.get_motor_rag()
    dtc_service = ServiceContainer.get_dtc_service()
    
    casos_todos = BENCHMARK_V3_G1 + BENCHMARK_V3_G2
    total = len(casos_todos)
    
    resultados = []
    tiempos_ml = []
    tiempos_rag = []
    
    correctos = 0
    parciales = 0
    incorrectos = 0
    top3_aciertos = 0
    sistema_aciertos = 0
    
    hits_rag_1 = 0
    hits_rag_3 = 0
    hits_rag_5 = 0
    mrr_total = 0.0
    
    y_true = []
    y_pred = []
    confianzas = []
    
    for i, (caso, esp, acep, dtc_esperado) in enumerate(casos_todos, 1):
        # 1. Normalización y purificación
        t0_ml = time.perf_counter()
        texto_norm = normalizar_jerga_peruana(caso)
        texto_ml = purificar_sintoma_para_vectorizador_ml(texto_norm)
        
        # 2. Inferencia Jerárquica ML con autoridad DTC
        codigos_dtc = re.findall(r"\b[PBCU]\d{4}\b", caso, re.IGNORECASE)
        dtc_usado = codigos_dtc[0] if codigos_dtc else None
        
        top_fallas = modelo_ml.predecir_top_fallas(texto_ml, limite=3, dtc_codigo=dtc_usado)
        t_ml = (time.perf_counter() - t0_ml) * 1000
        tiempos_ml.append(t_ml)
        
        falla_top1 = top_fallas[0]["falla"] if top_fallas else "Desconocida"
        conf_top1 = top_fallas[0]["probabilidad"] if top_fallas else 0.0
        confianzas.append(conf_top1)
        
        falla_top2 = top_fallas[1]["falla"] if len(top_fallas) > 1 else "-"
        conf_top2 = top_fallas[1]["probabilidad"] if len(top_fallas) > 1 else 0.0
        
        falla_top3 = top_fallas[2]["falla"] if len(top_fallas) > 2 else "-"
        conf_top3 = top_fallas[2]["probabilidad"] if len(top_fallas) > 2 else 0.0
        
        # 3. RAG Retrieval Híbrido Multiseñal
        t0_rag = time.perf_counter()
        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        sist_pred_ml = obtener_macro_sistema(falla_top1)
        c_hib = construir_consulta_hibrida(
            consulta_usuario=caso,
            macro_sistema=sist_pred_ml,
            top_fallas=top_fallas,
            codigos_dtc=[dtc_usado] if dtc_usado else None,
        )
        consulta_exp = rag_service._expandir_consulta(c_hib)
        consulta_vec = rag_service.vectorizador.transform([consulta_exp]).toarray().astype(np.float32)
        import faiss
        faiss.normalize_L2(consulta_vec)
        sims, indices = rag_service.faiss_index.search(consulta_vec, k=15)

        cands_rag = []
        for k_idx in range(min(15, len(rag_service.documentos))):
            d_idx = int(indices[0][k_idx])
            if 0 <= d_idx < len(rag_service.documentos):
                cands_rag.append({
                    "indice": d_idx,
                    "titulo": rag_service.titulos[d_idx],
                    "documento": rag_service.documentos[d_idx],
                    "similitud": float(sims[0][k_idx]),
                    "metadatos": rag_service.metadatos_procedimientos[d_idx] if d_idx < len(rag_service.metadatos_procedimientos) else {}
                })

        cands_reord = reordenar_candidatos_rag(
            cands_rag,
            macro_sistema=sist_pred_ml,
            top_fallas=top_fallas,
            codigos_dtc=[dtc_usado] if dtc_usado else None,
        )
        t_rag = (time.perf_counter() - t0_rag) * 1000
        tiempos_rag.append(t_rag)
        
        # Evaluar relevancia RAG sobre los reordenados
        rank_rel = 0
        for k_idx in range(min(5, len(cands_reord))):
            t_proc = cands_reord[k_idx]["titulo"]
            c_proc = cands_reord[k_idx]["documento"]
            if es_procedimiento_relevante(t_proc, c_proc, esp, dtc_esperado) and rank_rel == 0:
                rank_rel = k_idx + 1
                    
        if rank_rel == 1:
            hits_rag_1 += 1
            hits_rag_3 += 1
            hits_rag_5 += 1
            mrr_total += 1.0
        elif 1 < rank_rel <= 3:
            hits_rag_3 += 1
            hits_rag_5 += 1
            mrr_total += (1.0 / rank_rel)
        elif 3 < rank_rel <= 5:
            hits_rag_5 += 1
            mrr_total += (1.0 / rank_rel)
            
        # 4. Evaluación de Aciertos ML
        y_true.append(esp)
        y_pred.append(falla_top1)
        
        sist_true = obtener_macro_sistema(esp)
        sist_pred = obtener_macro_sistema(falla_top1)
        if sist_true == sist_pred:
            sistema_aciertos += 1
            
        cands_top3 = [falla_top1, falla_top2, falla_top3]
        if esp in cands_top3 or any(a in cands_top3 for a in acep):
            top3_aciertos += 1
            
        if falla_top1 == esp:
            correctos += 1
            st = "CORRECTO"
        elif falla_top1 in acep:
            parciales += 1
            st = "PARCIAL"
        else:
            incorrectos += 1
            st = "INCORRECTO"
            
        resultados.append({
            "idx": i,
            "caso": caso,
            "esperado": esp,
            "falla_top1": falla_top1,
            "confianza_top1": round(conf_top1, 4),
            "top2_falla": falla_top2,
            "top2_conf": round(conf_top2, 4),
            "top3_falla": falla_top3,
            "top3_conf": round(conf_top3, 4),
            "status": st,
            "sist_esperado": sist_true,
            "sist_predicho": sist_pred,
            "rank_rag": rank_rel,
            "titulo_rag": rag_service.titulos[int(indices[0][0])],
            "t_ml_ms": round(t_ml, 2),
            "t_rag_ms": round(t_rag, 2)
        })

    # Métricas Globales V3
    acc_top1_estricta = (correctos / total) * 100
    acc_top1_ampliada = ((correctos + parciales) / total) * 100
    acc_top3 = (top3_aciertos / total) * 100
    acc_sistema = (sistema_aciertos / total) * 100
    prom_conf = (sum(confianzas) / total) * 100
    
    labels_unicos = sorted(list(set(y_true + y_pred)))
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels_unicos, average="macro", zero_division=0
    )
    
    hit1_rag = (hits_rag_1 / total) * 100
    hit3_rag = (hits_rag_3 / total) * 100
    hit5_rag = (hits_rag_5 / total) * 100
    mrr_rag = mrr_total / total
    
    lat_ml = sum(tiempos_ml) / total
    lat_rag = sum(tiempos_rag) / total
    
    print("="*80)
    print("RESULTADOS GLOBALES DEL BENCHMARK V3 (100 CASOS INÉDITOS)")
    print("="*80)
    print(f"Accuracy Top-1 Estricta:         {acc_top1_estricta:5.2f}% ({correctos}/{total})")
    print(f"Accuracy Top-1 Ampliada (Dif.):  {acc_top1_ampliada:5.2f}% ({correctos+parciales}/{total})")
    print(f"Top-3 Accuracy:                  {acc_top3:5.2f}% ({top3_aciertos}/{total})")
    print(f"Accuracy de Macro-Sistema:       {acc_sistema:5.2f}% ({sistema_aciertos}/{total})")
    print(f"Confianza Promedio Calibrada:    {prom_conf:5.2f}%")
    print(f"Precision Macro:                 {prec*100:5.2f}%")
    print(f"Recall Macro:                    {rec*100:5.2f}%")
    print(f"F1-Score Macro:                  {f1*100:5.2f}%")
    print("-"*80)
    print(f"Métricas de Recuperación RAG:")
    print(f"  • Hit@1:                       {hit1_rag:5.2f}%")
    print(f"  • Hit@3:                       {hit3_rag:5.2f}%")
    print(f"  • Hit@5:                       {hit5_rag:5.2f}%")
    print(f"  • Mean Reciprocal Rank (MRR):  {mrr_rag:.4f}")
    print("-"*80)
    print(f"Latencias Promedio:              ML: {lat_ml:.2f} ms | RAG: {lat_rag:.2f} ms")
    print("="*80 + "\n")
    
    # Cargar métricas V2 para comparación
    v2_path = BASE_DIR / "docs" / "graficas" / "fase5_benchmark_v2_auditoria.json"
    metricas_v2 = {}
    if v2_path.exists():
        with open(v2_path, "r", encoding="utf-8") as f:
            metricas_v2 = json.load(f)
            
    # Guardar reporte comparativo
    reporte_v3_path = BASE_DIR / "docs" / "graficas" / "reporte_comparativo_v2_vs_v3.json"
    with open(reporte_v3_path, "w", encoding="utf-8") as f:
        json.dump({
            "v2": metricas_v2,
            "v3": {
                "total": total,
                "accuracy_top1_estricta": acc_top1_estricta,
                "accuracy_top1_ampliada": acc_top1_ampliada,
                "top3_accuracy": acc_top3,
                "accuracy_sistema": acc_sistema,
                "confianza_promedio": prom_conf,
                "precision_macro": prec * 100,
                "recall_macro": rec * 100,
                "f1_macro": f1 * 100,
                "rag": {
                    "hit_at_1": hit1_rag,
                    "hit_at_3": hit3_rag,
                    "hit_at_5": hit5_rag,
                    "mrr": mrr_rag
                },
                "latencia": {
                    "ml_ms": lat_ml,
                    "rag_ms": lat_rag
                },
                "conteo": {
                    "correctos": correctos,
                    "parciales": parciales,
                    "incorrectos": incorrectos
                }
            },
            "detalles_v3": resultados
        }, f, indent=2, ensure_ascii=False)
        
    print(f"Reporte comparativo guardado en: {reporte_v3_path}")

if __name__ == "__main__":
    evaluar_benchmark_v3()
