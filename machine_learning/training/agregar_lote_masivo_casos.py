from pathlib import Path

import pandas as pd

BASE_DIR = Path(r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data")
PATH_LIMPIO = BASE_DIR / "dataset_sintomas_limpio.csv"
PATH_SINTOMAS = BASE_DIR / "dataset_sintomas.csv"

df_limpio = pd.read_csv(PATH_LIMPIO, encoding="utf-8")
clases_existentes = {c.lower(): c for c in df_limpio["falla"].unique()}

def obtener_nombre_clase(subcadena: str) -> str:
    for k, v in clases_existentes.items():
        if subcadena.lower() in k:
            return v
    raise ValueError(f"No se encontró clase con subcadena: {subcadena}")

# Mapa de nuevos casos para balancear las 20 clases con menor soporte
casos_por_clase = {
    obtener_nombre_clase("mangueras de refrigerante o radiador"): [
        "Maestro, encontré un charco de líquido verde fosforescente debajo del motor en la mañana y el tanque de expansión está seco",
        "Amigo, sale un olor dulce a refrigerante caliente cuando paro en los semáforos y veo que la manguera superior del radiador está hinchada",
        "El radiador tiene una fisura en el tanque de plástico superior y bota vapor blanco con presión al calentar en subidas",
        "Tengo que rellenar agua cada tres días porque baja el nivel del depósito, revisé abajo y hay una gota constante en la abrazadera inferior del radiador",
        "Manguera del radiador cuarteada y con sudado aceitoso cerca al termostato, al acelerar chisguetea refrigerante con fuerza",
        "Se recalentó el carro en la autopista y al abrir el capó vi que el radiador estaba picado botando chorritos finos de vapor por el panal",
        "La abrazadera metálica de la manguera inferior se pudrió y se soltó en marcha, botando todo el refrigerante al suelo de golpe",
        "Pérdida de refrigerante invisible: el líquido gotea sobre el múltiple de escape caliente y se evapora al instante dejando costra blanca",
    ],
    obtener_nombre_clase("fscm / pem"): [
        "El auto se apaga de golpe en carretera como si le cortaran la corriente de combustible, luego de enfriar 15 minutos vuelve a encender normal",
        "Código P069E y U0109 en escáner: el módulo FSCM de control de la bomba de gasolina recalienta bajo el asiento y corta el pulso de presión",
        "Mi Ford se jalonea en alta velocidad y se corta la inyección de repente, el mecánico revisó la bomba y el fallo está en el módulo electrónico PEM",
        "Falla intermitente de encendido: a veces la bomba de gasolina no zumba al abrir contacto porque el módulo FSCM no recibe voltaje de activación",
        "El carro se detiene en marcha después de rodar media hora, no hay presión en el riel pero al puentear directo la bomba sí funciona: módulo PEM defectuoso",
        "Tironeos violentos al acelerar en calor por módulo de bomba de gasolina FSCM recalentado en el chasis",
        "Chevrolet Cruze se apaga en ralentí con código de pérdida de comunicación con el módulo de control de combustible de la bomba",
        "Módulo PEM con soldaduras frías internas: al pasar baches vibra y apaga la bomba de nafta momentáneamente",
    ],
    obtener_nombre_clase("dpf / fap"): [
        "Luz de advertencia del filtro de partículas DPF encendida fija en el tablero con pérdida notoria de fuerza y humo picante",
        "Mensaje en pantalla de arranque no permitido en 800 km por bajo nivel o cristalización de urea líquida en sistema AdBlue DEF",
        "Camioneta diesel entró en modo degradado Limp Mode sin pasar de 2000 RPM por colmatación severa de hollín en el DPF (DTC P2463)",
        "El escáner arroja código DTC P2002 de eficiencia del filtro de partículas por debajo del umbral, intento regeneración y se cancela sola",
        "Inyector de AdBlue tupido con sarro blanco cristalizado, arroja código de falla en el sistema de reducción catalítica SCR",
        "Sensor de presión diferencial de gases DPF marcando valores descalibrados, la ECU cree que el filtro está tapado y limita la potencia",
        "Humo blanco azulado constante y nivel de aceite de motor subiendo por exceso de diesel inyectado durante regeneraciones fallidas del DPF",
        "Consumo excesivo de AdBlue y advertencia de bloqueo de arranque en cuenta regresiva en camioneta Hilux Euro 6",
    ],
    obtener_nombre_clase("sincronizacion variable"): [
        "El motor cascabelea feo al subir cuestas a 2500 RPM y el escáner arroja código DTC P0011 de fase avanzada del árbol de levas",
        "Válvula solenoide OCV del VVT-i atascada con carbón de aceite sucio, provoca que el ralentí se vuelva inestable y tiemble al frenar",
        "Código P0014 en escape: el faser o piñón variador hidráulico no retorna a su posición de reposo por falta de presión de aceite",
        "Al pisar el acelerador el motor no tiene respuesta ágil y se siente amarrado, la válvula VVT no abre los conductos de avance de levas",
        "Filtro de malla del solenoide VVT completamente tupido de lodo negro, bloquea el paso de aceite hacia el actuador del eje de levas",
        "El árbol de levas hace un ruido de matraca durante los primeros 3 segundos de encendido en frío hasta que carga presión el engranaje VVT",
        "Ralentí descontrolado y cabeceo de motor por solenoide de distribución variable trabado en posición abierta con código P0012",
        "Pérdida de sincronización de levas al acelerar fuerte en carretera por actuador hidráulico VVT con desgaste interno en la paleta",
    ],
    obtener_nombre_clase("descarbonizacion e inyeccion directa gdi"): [
        "Motor GDI con tironeos fuertes en frío por las mañanas y ralentí áspero debido a costra de carbón acumulada en las válvulas de admisión",
        "Pérdida progresiva de potencia y consumo alto en motor de inyección directa: las válvulas de admisión tienen lodo seco de aceite y hollín",
        "Falla de combustión aleatoria P0300 en motor EcoBoost / TSI: el aire no entra parejo a los cilindros por carbón pegado en el asiento de válvulas",
        "El carro cabecea al salir en primera y le cuesta emparejar el ralentí, requiere limpieza por chorreado con cáscara de nuez de válvulas GDI",
        "Carbonilla dura en el lomo de las válvulas de admisión obstruye el flujo de aire laminar provocando mezcla desequilibrada en inyección directa",
        "Motor 1.6 GDI pierde pique en alta y se siente pesado al adelantar por taponamiento de carbonilla en los puertos de admisión de la culata",
        "Auto con inyección directa gasolina tironea a 1500 RPM a velocidad crucero, las bujías e inyectores están bien pero las válvulas están tupidas de carbón",
        "Arranque tosco y sacudida del motor en frío que disminuye cuando calienta: acumulación severa de carbonilla en válvulas de admisión GDI",
    ],
    obtener_nombre_clase("actuador de turbocompresor o vgt"): [
        "Código DTC P0299 de baja presión de turbo en motor TSI / TFSI: el actuador electrónico de la compuerta Wastegate tiene holgura y no cierra",
        "El motor entra en modo de emergencia y no pasa de 80 km/h al exigir en pendiente, apago el contacto y vuelve la fuerza momentáneamente",
        "Vástago de la válvula Wastegate del turbo trabado con código P2563 de sensor de posición del actuador de sobrealimentación",
        "Silbido y fuga de presión en aceleración por compuerta de descarga del turbo desgastada que no sella hermética en la caracola de escape",
        "Actuador eléctrico del turbocompresor emite un zumbido eléctrico anormal al poner contacto y registra error de calibración de límites",
        "Pérdida repentina de potencia del turbo en carretera al superar 3000 RPM en motor alemán 1.4 / 2.0 TSI por desgaste en el buje del actuador",
        "El turbo no carga presión en bajas revoluciones y el escáner marca falla de recorrido del vástago de geometría variable VGT",
        "Luz EPC encendida en el tablero y corte de aceleración por holgura excesiva en la articulación del actuador Wastegate del turbocompresor",
    ],
    obtener_nombre_clase("correa dentada banada en aceite"): [
        "Testigo rojo de presión de aceite titila en el tablero al calentar el motor 1.0 Dragon / PureTech / GM Turbo de faja bañada en aceite",
        "La correa bañada en aceite se está desgranando y soltó virutas de jebe negro que taponaron la rejilla de la coladera de la bomba de aceite",
        "Ruido de zumbido y cascabeleo en la parte baja del motor por pérdida de presión de lubricación provocada por residuos de la correa de distribución",
        "Al cambiar el aceite salieron hilachas y trozos de caucho de la faja húmeda, la bomba de aceite no puede chupar lubricante con fluidez",
        "Falla de lubricación crítica por desprendimiento de material de la correa de distribución bañada en aceite en motor 1.2 / 1.0 turbo",
        "Presión de aceite cae a 8 PSI en ralentí caliente por obstrucción severa del chupador de aceite con goma descompuesta de la correa",
        "DTC de sincronización de árbol de levas y alarma de presión de aceite baja simultánea por deterioro prematuro de la faja en baño de aceite",
        "Correa de distribución sumergida en aceite hinchada y agrietada, amenaza con saltar de punto y tapona los conductos de lubricación",
    ],
    obtener_nombre_clase("caja robotizada dualogic"): [
        "Mensaje en el tablero 'Hacer controlar el cambio' y la transmisión se salta a Neutro sola en pleno tráfico de la avenida",
        "La caja robotizada Dualogic / I-Motion no aplica la marcha atrás ni primera con motor encendido, pero con motor apagado sí entran",
        "La electrobomba del grupo hidráulico robotizado suena a cada rato intentando levantar presión y se calienta en menos de 15 minutos",
        "Fuga de líquido hidráulico Tutela CS Speed por el actuador del embrague del sistema robotizado, dejando el auto inmovilizado",
        "Tironeo violento y cabeceo al salir de parado en primera velocidad en caja robotizada por desgaste en la electroválvula de embrague",
        "Auto robotizado se queda bloqueado en Neutro y no pasa a Drive al acelerar, emite pitido de advertencia en el odómetro",
        "Pérdida de presión en el acumulador de nitrógeno del grupo robotizado: la bomba eléctrica trabaja sin descanso y quema el fusible",
        "Retardo excesivo de 3 a 5 segundos para meter los cambios en transmisión Dualogic, pateando fuerte al enganchar la segunda",
    ],
    obtener_nombre_clase("sistema flex"): [
        "El auto flex no quiere arrancar en las mañanas frías, gira el arranque pesado y ahoga las bujías de olor a alcohol",
        "Sensor virtual de mezcla aire-combustible A/F descalibrado: la ECU calcula 85% de etanol cuando el tanque tiene gasolina pura",
        "Dificultad severa para encender en frío en vehículo bi-combustible porque la resistencia térmica o el inyectorcito de arranque en frío no activa",
        "Consumo altísimo de combustible y humo negro en motor Flex por lectura errónea de porcentaje de alcohol en la computadora",
        "El motor cabecea y pierde fuerza al salir de viaje porque la ECU no adaptó el cambio de combustible de gasolina a alcohol/etanol",
        "Arranque prolongado de 10 segundos en las mañanas con temperatura ambiente baja en vehículo brasileño Flex",
        "Mezcla extremadamente rica y ahogamiento de bujías en motor bi-combustible por desprogramación del factor estequiométrico adaptativo",
        "Luz de motor encendida con código de mezcla rica y sonda lambda en tope superior tras cargar combustible en vehículo Flex",
    ],
    obtener_nombre_clase("termostato o motoventilador"): [
        "La aguja de temperatura sube a la zona roja cuando me detengo en el tráfico, pero al empezar a rodar en pista rápida baja a la mitad",
        "El motoventilador no enciende en su primera velocidad y el refrigerante hierve por la tapa del radiador al llegar a 100 grados",
        "La aguja de temperatura se queda pegada abajo en frío todo el día y la calefacción de la cabina no calienta: termostato trabado abierto",
        "Código DTC P0128 de temperatura de motor por debajo del rango de regulación por termostato vencido que no cierra",
        "Resistencia de la primera velocidad del electroventilador quemada: solo prende la velocidad máxima ruidosa cuando el auto ya está recalentando",
        "El motor del ventilador del radiador se siente pesado con la mano, quema el fusible de 30 amperios y deja el motor sin enfriamiento",
        "El termostato se quedó pegado cerrado: la manguera de arriba está hirviendo inflada y la manguera de abajo está totalmente fría",
        "Electroventilador enciende directo todo el tiempo apenas pongo la llave en contacto por sensor de temperatura desconectado o en corto",
    ],
    obtener_nombre_clase("compresor de aire acondicionado"): [
        "Al presionar el botón A/C el compresor no acopla y sale aire tibio a temperatura ambiente por las rejillas de ventilación",
        "Zumbido metálico como de rodamiento seco que empieza justo cuando se activa el compresor del aire acondicionado",
        "La polea del compresor de aire acondicionado patina y bota humo con olor a caucho quemado por bobina magnética en cortocircuito",
        "Fuga masiva de gas refrigerante R134a por el sello del eje delantero del compresor, manómetro de taller marca cero libras de presión",
        "El aire acondicionado enfría bien unos minutos pero luego empieza a tirar aire húmedo caliente porque el compresor corta por recalentamiento",
        "Cuerpo del compresor de aire acondicionado trabado internamente por falta de lubricante PAG, no deja girar la faja de accesorios",
        "Fuga de gas por el condensador picado por piedras del camino, dejando sin presión el circuito del aire acondicionado",
        "Embrague magnético del compresor de aire desgastado: la placa no atrae contra la polea y no bombea gas refrigerante",
    ],
    obtener_nombre_clase("sensor de velocidad de rueda abs"): [
        "Luz de ABS y testigo de control de estabilidad ESP encendidos fijos en el tablero después de pasar un rompemuelles",
        "Al frenar despacio llegando a un semáforo el pedal del freno empieza a patear y vibrar como si patinara en hielo en asfalto seco",
        "Código de falla DTC C0035 en el escáner: circuito abierto o señal errática en el sensor de velocidad de la rueda delantera izquierda",
        "Cable del sensor ABS rozó con el palier de la rueda y se peló haciendo masa con el chasis, apagando el velocímetro",
        "Rueda fónica dentada o imantada del rodamiento llena de grasa con viruta de metal que distorsiona la lectura del sensor de rueda ABS",
        "El odómetro digital y velocímetro no marcan nada de velocidad en marcha porque el sensor ABS principal de rueda trasera está roto",
        "Testigo de freno y luz de ABS prendidos con código de falla de rango de señal en sensor de velocidad de rueda derecha",
        "El control de tracción se activa solo quitando fuerza al motor en curvas por falso contacto en el conector del sensor de rueda ABS",
    ],
    obtener_nombre_clase("rodajes de caja mecanica"): [
        "Zumbido continuo como de engranajes secos en la caja de cambios que desaparece por completo al pisar el pedal de embrague a fondo",
        "Sonido de molienda y cascajo en neutro con motor encendido, suelto el embrague y empieza a zumbar el rodamiento del eje piloto",
        "Zumbido áspero al acelerar en 3ra y 4ta marcha que aumenta con la velocidad del carro, rodamiento secundario de transmisión picado",
        "La palanca de cambios vibra y el diferencial emite un aullido metálico en retención al soltar el acelerador en carretera",
        "Al vaciar el aceite de la caja de cambios salieron partículas y escamas plateadas de rodajes desgastados de la transmisión mecánica",
        "Sonido de rodaje molido en la directa de la caja de cambios: al estar en neutro suena feo y al pisar el embrague se silencia",
        "Cojinetes cónicos del diferencial de la caja con excesivo juego axial, producen zumbido que varía al virar a derecha o izquierda",
        "Ruido de zumbido permanente en la caja manual que no se quita al cambiar de marcha por desgaste en las pistas de los rodamientos",
    ],
    obtener_nombre_clase("sobrecalentamiento o solenoides en caja automatica"): [
        "La caja automática CVT zumba como turbina en autopista y entra en protección limitando la velocidad a no más de 60 km/h por calor",
        "Patinamiento al arrancar en subida y tirón seco al aplicar Reversa o Directa en transmisión automática con código P0746",
        "Aceite de transmisión automática de color marrón oscuro con olor a disco quemado y partículas suspendidas en el cárter",
        "Luz de advertencia de temperatura de transmisión automática encendida en el odómetro tras subir cuestas exigiendo carga",
        "Solenoide de presión de línea trabado mecánicamente en la caja de válvulas, provoca que los cambios pasen a golpes bruscos",
        "La transmisión CVT patina al acelerar a fondo y las revoluciones suben a 4000 RPM sin que el carro avance con fuerza proporcional",
        "Caja DSG de doble embrague da tirones fuertes en 1ra y 2da velocidad por mecatrónica sobrecalentada con código de presión baja",
        "Filtro enfriador de la caja CVT tapado de suciedad que impide la circulación del fluido hacia el radiador, elevando la temperatura",
    ],
    obtener_nombre_clase("baja presion de aceite"): [
        "La luz de la alquitara roja de aceite parpadea en el tablero cuando el motor calienta a temperatura normal y queda en ralentí",
        "Sonido fuerte de taqués hidráulicos y cascabeleo metálico en la culata por falta de presión de lubricación al motor caliente",
        "Manómetro de taller conectado en el puerto del bulbo marca menos de 10 PSI de presión en ralentí, la bomba de aceite tiene desgaste",
        "Al acelerar a 2000 RPM la luz de aceite se apaga, pero al soltar el acelerador en cada parada vuelve a encender parpadeando",
        "Coladera del cárter tupida de lodo negro de carbón por aceite viejo degradado, impidiendo que la bomba aspire suficiente caudal",
        "Válvula de alivio de sobrepresión de la bomba de aceite trabada abierta por virutas de metal, fugando la presión directo al cárter",
        "Bomba de aceite con holgura en los engranajes trocoidales: no genera suficiente presión hidráulica para lubricar los muñones de biela",
        "Testigo de presión de aceite se encendió fijo en carretera acompañado de un golpeteo seco metálico de metales de biela",
    ],
    obtener_nombre_clase("faja o cadena de distribucion"): [
        "Traqueteo metálico fuerte tipo cadena suelta durante los primeros 5 segundos de encendido en frío proveniente del costado del motor",
        "El motor demora en arrancar, perdió fuerza de aceleración y el escáner arroja código DTC P0016 de correlación cigüeñal-levas fuera de punto",
        "Cadena de distribución estirada: el tensor hidráulico llegó al tope máximo de sus estrías y ya no puede compensar la holgura",
        "La faja de distribución saltó un diente al arrancar empujado el carro, el motor cabecea en ralentí y tira explosiones por la admisión",
        "Guías plásticas de la cadena de distribución rotas con pedazos en el cárter, la cadena roza directamente contra la tapa metálica",
        "Pérdida de potencia y código de desfase de sincronización entre el sensor CKP y CMP por holgura severa en la cadena de repartición",
        "Chirrido y ruido de cascajo rítmico en la distribución por rodamiento tensor de la faja de tiempo desengrasado a punto de trancarse",
        "Cadena de tiempo golpea contra el block al desacelerar bruscamente por tensor hidráulico descargado que no retiene presión",
    ],
    obtener_nombre_clase("falla electrica del cierre centralizado"): [
        "El pestillo de la puerta del copiloto no baja ni sube al presionar el botón de la llave, se escucha que intenta pero no tiene fuerza",
        "La chapa centralizada se vuelve loca cerrando y abriendo sola continuamente mientras el auto va rodando por un bache",
        "El actuador eléctrico de la puerta trasera derecha suena como un quejido trabado y no asegura la cerradura con el cierre central",
        "El mando a distancia activa la alarma pero las cuatro puertas se quedan abiertas porque el módulo de cierre no manda el pulso de 12V",
        "Fusible del cierre centralizado se quema de inmediato por cortocircuito en el motorcito actuador de la puerta del conductor",
        "Cableado en el fuelle de goma de la puerta quebrado por fatiga de abrir y cerrar: no llega corriente al actuador del pestillo",
        "La puerta del maletero no abre eléctricamente con el botón exterior, hay que destrabarla desde adentro con la palanca de emergencia",
        "Actuador de puerta trabado en posición cerrada que no permite abrir la puerta ni desde adentro ni desde afuera con la manija",
    ],
    obtener_nombre_clase("secador aps"): [
        "El camión no descarga el aire o la válvula estornuda continuamente cada 30 segundos porque el cartucho secador está saturado de aceite",
        "La presión en los tanques de aire sube lentísimo y no pasa de 6 Bar, las ruedas traseras se quedan frenadas por falta de aire de servicio",
        "Al purgar los tanques de aire primario y secundario sale agua mezclada con aceite negro del compresor, el filtro coalescente no seca",
        "Válvula de cuatro vías o secador APS pierde aire constantemente por el desfogue inferior impidiendo que cargue el circuito de frenos",
        "Gobernador de aire de la válvula secadora trabado con sarro, no corta la carga del compresor y sopla la válvula de seguridad a 12 Bar",
        "Los frenos neumáticos demoran en liberar y se escucha fuga continua de aire en el módulo secador APS bajo el chasis del camión",
        "Luz de advertencia de baja presión de aire en cabina de camión con zumbador sonando permanente por obstrucción en la válvula secadora",
        "Cartucho secador de aire congelado o con carbón acumulado, bloquea el paso de aire comprimido hacia las botellas de almacenamiento",
    ],
    obtener_nombre_clase("frenado regenerativo"): [
        "Luz de advertencia de freno regenerativo encendida en auto híbrido con aviso de revisar sistema de frenos en la pantalla",
        "El pedal de freno se siente extremadamente duro al inicio y luego se va al fondo con una transición brusca entre freno eléctrico e hidráulico",
        "Código DTC C1256 o C1391 en escáner: fuga interna de presión en el acumulador del servofreno hidráulico del sistema híbrido",
        "El vehículo no recupera energía en el indicador de carga al soltar el acelerador o frenar suavemente, solo frena con las pastillas",
        "Bomba eléctrica del actuador de freno del sistema híbrido zumba cada 10 segundos para mantener la presión de nitrógeno acumulada",
        "Pérdida de asistencia en frenada regenerativa en bajadas pronunciadas en auto eléctrico, requiriendo pisar a fondo el pedal mecánico",
        "Sensor de carrera del pedal de freno descalibrado, provoca que el motor generador no active el frenado por regeneración de batería",
        "Falla en el módulo de control del actuador de freno regenerativo ECB en Toyota Prius con código de presión anormal de frenada",
    ],
    obtener_nombre_clase("refrigeracion de bateria/inversor"): [
        "Mensaje en la pantalla de aviso 'Temperatura excesiva en sistema híbrido/inversor' al exigir aceleración continua en autopista",
        "La bomba eléctrica de agua que enfría el módulo inversor IGBT no zumba ni recircula refrigerante en el depósito transparente",
        "Ventilador de refrigeración de la batería de alto voltaje bajo el asiento trasero suena como turbina forzada lleno de pelusa y polvo",
        "Luz de advertencia de batería híbrida con código de recalentamiento de módulos por conducto de aire de enfriamiento bloqueado",
        "Nivel de refrigerante rosado del circuito del inversor eléctrico vacío por fuga en la manguera inferior del enfriador de potencia",
        "El auto híbrido apaga el motor eléctrico y se limita a funcionar solo con el motor a gasolina por sobrecalentamiento en el convertidor DC-DC",
        "Sensor de temperatura interna de la batería de tracción reporta más de 55 grados Celsius activando corte de potencia de seguridad",
        "Bomba de enfriamiento del inversor trabada mecánicamente con código DTC P0A93 de rendimiento del sistema de enfriamiento del inversor",
    ],
}

total_agregados = 0
nuevas_filas = []
for clase, ejemplos in casos_por_clase.items():
    for s in ejemplos:
        nuevas_filas.append({"sintoma": s.strip(), "falla": clase})
        total_agregados += 1

df_nuevos = pd.DataFrame(nuevas_filas)
print(f"Total casos nuevos generados: {total_agregados} repartidos en {len(casos_por_clase)} clases.")

# Guardar en dataset_sintomas_limpio.csv
df_limpio_act = pd.concat([df_limpio, df_nuevos], ignore_index=True).drop_duplicates(subset=["sintoma"])
df_limpio_act.to_csv(PATH_LIMPIO, index=False, encoding="utf-8")
print(f"Guardado {PATH_LIMPIO.name}: {len(df_limpio)} -> {len(df_limpio_act)} filas.")

# Guardar en dataset_sintomas.csv
if PATH_SINTOMAS.exists():
    df_sint = pd.read_csv(PATH_SINTOMAS, encoding="utf-8")
    df_sint_act = pd.concat([df_sint, df_nuevos], ignore_index=True).drop_duplicates(subset=["sintoma"])
    df_sint_act.to_csv(PATH_SINTOMAS, index=False, encoding="utf-8")
    print(f"Guardado {PATH_SINTOMAS.name}: {len(df_sint)} -> {len(df_sint_act)} filas.")
