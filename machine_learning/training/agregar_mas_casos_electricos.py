from pathlib import Path

import pandas as pd

BASE_DIR = Path(r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data")
PATH_LIMPIO = BASE_DIR / "dataset_sintomas_limpio.csv"
PATH_SINTOMAS = BASE_DIR / "dataset_sintomas.csv"

# Colección de casos realistas, coloquiales de taller, con variaciones de choferes, taxistas y mecánicos
casos_alternador = [
    # Síntomas de faros titilando, radio reseteándose y caída de tensión en marcha
    "Maestro, anoche venía por la Panamericana con los faros prendidos y comenzaron a parpadear como árbol de navidad, la radio se reiniciaba a cada rato y al llegar a mi cochera lo apagué y ya no dio nada de arranque",
    "Amigo una consulta, cuando voy manejando de noche noto que al acelerar los faros bajan y suben de intensidad solos, la pantalla del tablero parpadea y hoy en la mañana el carro amaneció completamente muerto sin batería",
    "Buenas tardes mecánico, mi auto presenta un zumbido agudo en el motor que sube con las revoluciones, los faros alumbran bien bajito en ralentí y la aguja del tacómetro se cae a cero por segundos",
    "Iba en carretera y de repente el radio se apagó y volvió a prender solo, los testigos del tablero titilaron y a los diez minutos el carro empezó a perder fuerza eléctrica hasta que se apagó rodando",
    "Resulta que anoche los faros bajaban de fuerza al frenar en cada semáforo, el tablero parpadeaba y la radio se bloqueó, hoy quise encenderlo y no da ni contacto",
    "Tengo un problema con mi vehículo, venía rodando y sentí un olor como a cable caliente o barniz quemado, las luces bajaron un montón y el velocímetro marcaba cero en plena marcha",
    "Amigo mi carro empezó a fallar de noche, las luces del tablero titilaban suavemente y la radio se reseteaba sola, al día siguiente amaneció sin nada de corriente y tuve que pedir auxilio",
    "Sabes que cuando prendo el aire acondicionado y las luces altas en marcha, el carro se chupa eléctricamente, la radio se apaga y el testigo de la batería empieza a parpadear en el tablero",
    "El alternador empezó a chillar y en la pista los faros alumbraban amarillento y titilaban, al estacionarlo quise volver a prender y ya no dio ni un sonido el motor de arranque",
    "Manejando en tráfico pesado noté que la aguja de temperatura y velocímetro bajaban de golpe a cero y regresaban, la radio se reseteaba y los faros alumbraban con poca fuerza",
    "Placa de diodos en cortocircuito: genera ruido de corriente alterna en los parlantes de la radio, parpadeo constante de faros al acelerar y descarga total de batería al dejarlo parqueado",
    "Amigo el testigo rojo de la batería se prendió tenue en el tablero mientras manejaba, las luces perdieron brillo y a los pocos kilómetros el auto se apagó y no volvió a dar marcha",
    "Venía manejando y noté que los limpiaparabrisas andaban lentísimos, las luces del tablero parpadeaban y la radio se apagó, ahora ni las luces de emergencia prenden",
    "El carro me dejó botado en la avenida: venía funcionando bien pero las luces del tablero empezaron a parpadear, la radio se reinició dos veces y de pronto el motor se detuvo por falta de corriente",
    "Falla de alternador que no manda carga: en el multímetro marca 11.8V con el motor encendido a 2000 RPM y al acelerar cae más el voltaje, descargando la batería en marcha",
    "Buenas, anoche los faros parpadeaban y la luz del techo titilaba al andar, hoy temprano metí la llave y no prende ni la luz del testigo de la puerta",
    "Se me apagó el auto rodando a 60 km/h: primero la radio se reinició, luego los faros alumbraron muy tenue y al pisar embrague el motor se murió sin corriente",
    "Cuando voy en carretera de noche noto fluctuación de voltaje en los faros principales y el tablero, titilan bastante y al apagar el carro ya no tiene fuerza para mover el arranque",
    "Mi vehículo presenta parpadeo de faros al desacelerar y la pantalla táctil se reinicia sola en marcha, después de dejarlo parqueado toda la noche amanece sin nada de carga",
    "Zumbido eléctrico en la zona de fajas y las luces titilan al acelerar en vacío, la batería es nueva de hace un mes pero amanece muerta porque el alternador no la carga en ruta",
    "Anoche venía por la pista y el velocímetro caía a cero un segundo y volvía a subir, la radio se reseteó y los faros titilaban, hoy en la mañana no da contacto ni para abrir los pestillos",
    "Tengo un problema, cuando voy en marcha con faros prendidos se siente que la corriente baja y sube, la radio se apaga unos segundos y al estacionar el carro murió eléctricamente",
    "Diodos quemados en el alternador: meten interferencia electromagnética que vuelve loca la radio, resetea el reloj del tablero y hace titilar las luces bajas y altas en movimiento",
    "Amigo una consulta, el carro rodando empezó a perder intensidad de luces en el tablero, la radio se apagó de la nada y al parar en la gasolinera ya no arrancó más",
    "Venía manejando anoche y sentí que los faros bajaron casi a la mitad de su brillo de golpe y titilaban, la música se cortó y hoy el carro está completamente sin energía",
    "Testigo de batería parpadea al acelerar fuerte en autopista, los faros parpadean y la radio se apaga y prende sola, el alternador está calentando demasiado al tacto",
    "El carro se chupa de corriente en movimiento: faros titilan, agujas del tablero tiemblan y la radio se resetea sola hasta que la batería se vacía por completo",
    "Manejando de noche los faros titilaban como si hubiera un falso contacto en marcha, la radio se apagó y al llegar a casa lo apagué y no encendió ni la luz de cabina",
    "Placa rectificadora con diodo abierto: voltaje de carga no pasa de 12.4V acelerando con consumidores y provoca que la radio se reinicie y los faros bajen su intensidad",
    "Iba rodando en mi taxi y noté que los faros alumbraban amarillos y titilaban, la radio se apagaba y prendía sola y a las dos cuadras el motor se apagó y no dio arranque",
    "Mi auto pierde corriente en plena marcha: luces del odómetro titilan, las agujas caen por un segundo y luego de apagarlo la batería amanece en cero voltios",
    "Amigo anoche venía con la lluvia y los limpiaparabrisas iban super lentos, las luces del tablero titilaban y la radio se reiniciaba, hoy el auto no hace nada al girar la llave",
    "Falla de alternador que descarga la batería rodando: el mecánico midió 12.1V con motor prendido y faros altos, el alternador tiene los carbones gastados y la placa sulfatada",
    "El carro venía cabeceando eléctricamente: radio se apagaba sola, los faros titilaban y las agujas del tacómetro caían, al apagarlo se quedó sin batería por completo",
    "Noté que al andar a 80 km/h la luz de batería titilaba tenue, los faros bajaban de intensidad y la radio se cortaba, al día siguiente amaneció sin batería",
]

casos_bateria_estatica = [
    # Síntomas de batería descargada en reposo (sin fallas de faros ni radio en marcha)
    "Maestro, dejé el auto estacionado 5 días porque estuve de viaje y hoy que quise encenderlo no hace nada de nada, ni las luces del tablero prenden",
    "Amigo una consulta, ayer mi hijo dejó la luz de lectura del techo prendida toda la noche y hoy la batería amaneció totalmente descargada sin dar arranque",
    "Buenas tardes, mi carro arranca perfecto cuando está caliente, pero cuando duerme toda la noche en la mañana amanece pesadísimo y solo hace clac clac",
    "El carro estuvo guardado en la cochera desde el fin de semana y hoy al meter la llave apenas prendió la luz del aceite y se apagó todo al intentar dar arranque",
    "Tengo los bornes de la batería llenos de sarro verde y polvo blanco, al mover el cable hace falso contacto y a veces no enciende el tablero en las mañanas",
    "La batería ya tiene más de 3 años de uso y ya no retiene carga, cada mañana tengo que pedirle a un vecino que me pase corriente con cables para arrancar",
    "Dejé el carro parqueado con la radio prendida una hora con el motor apagado y cuando quise prender ya se había consumido toda la batería",
    "Amigo mi auto amanece descargado los lunes si no lo uso el domingo, pero el alternador carga perfecto a 14.3V cuando el motor está en marcha",
    "Al girar la llave para dar arranque solo suena un clac en el motor y todas las luces del tablero se bajan a cero, la batería no tiene fuerza de arranque en frío",
    "El vaso de la batería está comunicado o seco de líquido, mido con el multímetro en reposo con motor apagado y apenas marca 10.4V",
    "Bornes flojos y sulfatados en la batería: al mover el borne negativo con la mano vuelve la corriente al tablero, pero al dar arranque se corta todo",
    "Dejé la llave en contacto en posición de accesorios durante dos horas sin encender el motor y la batería se descargó por completo",
    "Batería agotada por tiempo de vida: no mantiene los 12.6V en reposo, a las pocas horas de apagado cae a 11.5V y ya no mueve el motor de arranque",
    "El auto estuvo parado en el taller una semana sin prender y la alarma descargó la batería lentamente hasta dejarla en cero",
    "En las mañanas frías el arranque gira sumamente pesado y lento, como que le falta fuerza a la batería, pero una vez que calienta arranca bien el resto del día",
    "Compré una batería de poco amperaje para mi camioneta y no tiene suficiente CCA de arranque en frío, sufre para prender en las mañanas",
    "La luz de la guantera se quedó encendida porque el interruptor de plástico se rompió y me vació la batería durante la noche",
    "Batería hinchada en los costados y con sulfato en el poste positivo, no retiene carga y al poner el cargador hierve el ácido de inmediato",
    "El carro amanece sin corriente si duerme a la intemperie por el frío, le pasamos corriente con otra batería y arranca al toque sin fallar en ruta",
    "Bornes sulfatados con una costra gruesa de ácido: no deja pasar la corriente hacia el arrancador aunque la batería esté cargada",
]

casos_misfire_ignicion = [
    # Misfires y bobinas relacionadas con tironeos y fallas de encendido
    "Maestro, el auto tiembla feo en ralentí como en tres cilindros y al acelerar en segunda tironea bastante, la luz del Check Engine parpadea",
    "Amigo, una de las bobinas de encendido está fallando, cuando el motor calienta empieza a cabecear y pierde fuerza en las subidas",
    "Siento olor a gasolina cruda por el tubo de escape y el motor vibra mucho en las paradas, el escáner arrojó código de falla de encendido en cilindro 3",
    "Al exigir el acelerador en carretera el carro da tirones secos y cabecea, ya le cambié bujías pero sigue la falla en la bobina del cilindro 1",
    "Bobina de encendido con fuga de chispa: el capuchón de jebe está rajado y salta la chispa hacia la culata produciendo cascabeleo y tironeo",
]

casos_cierre_elevalunas = [
    # Fallas eléctricas de confort
    "El pestillo eléctrico de la puerta del conductor no sube ni baja con el mando a distancia, se escucha que intenta pero se queda trabado",
    "El alzacristales del lado derecho suena como que la guaya se enredó y la ventana no sube, se quedó a medio camino",
    "La chapa centralizada de la puerta trasera no responde, hay que abrirla manualmente desde adentro con la palanca",
]

nuevos_registros = []
for s in casos_alternador:
    nuevos_registros.append({"sintoma": s, "falla": "Alternador defectuoso o placa de diodos quemada"})
for s in casos_bateria_estatica:
    nuevos_registros.append({"sintoma": s, "falla": "Bateria descargada o bornes sulfatados"})
for s in casos_misfire_ignicion:
    nuevos_registros.append({"sintoma": s, "falla": "Falla en bujias o bobinas de encendido (misfire)"})
for s in casos_cierre_elevalunas:
    nuevos_registros.append({"sintoma": s, "falla": "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado"})

df_nuevos = pd.DataFrame(nuevos_registros)
print(f"Nuevos casos generados: {len(df_nuevos)}")

# Actualizar dataset_sintomas_limpio.csv
df_limpio = pd.read_csv(PATH_LIMPIO, encoding="utf-8")
total_limpio = pd.concat([df_limpio, df_nuevos], ignore_index=True).drop_duplicates(subset=["sintoma"])
total_limpio.to_csv(PATH_LIMPIO, index=False, encoding="utf-8")
print(f"dataset_sintomas_limpio.csv actualizado: {len(df_limpio)} -> {len(total_limpio)} filas.")

# Actualizar dataset_sintomas.csv
if PATH_SINTOMAS.exists():
    df_sintomas = pd.read_csv(PATH_SINTOMAS, encoding="utf-8")
    total_sintomas = pd.concat([df_sintomas, df_nuevos], ignore_index=True).drop_duplicates(subset=["sintoma"])
    total_sintomas.to_csv(PATH_SINTOMAS, index=False, encoding="utf-8")
    print(f"dataset_sintomas.csv actualizado: {len(df_sintomas)} -> {len(total_sintomas)} filas.")
