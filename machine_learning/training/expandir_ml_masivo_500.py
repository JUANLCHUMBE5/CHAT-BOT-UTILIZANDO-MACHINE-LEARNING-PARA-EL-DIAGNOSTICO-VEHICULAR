import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data")
LIMPIO_CSV = BASE_DIR / "dataset_sintomas_limpio.csv"
DATASET_CSV = BASE_DIR / "dataset_sintomas.csv"

# Diccionario de casos tecnicos reales y coloquiales recopilados
casos_adicionales = {
    "falla_turbo_vgt": {
        "patron": "actuador de turbocompresor o VGT",
        "casos": [
            "En plena cuesta de la autopista el motor se queda sin pique, no pasa de 2800 RPM y el escáner arroja P0299 presión baja de sobrealimentación",
            "Siento que la camioneta se frena sola al exigirle en subida y entra en modo de protección Limp Mode con código P0234 sobrepresión de turbo",
            "La varilla del actuador electrónico de la compuerta Wastegate vibra con un sonido metálico al desacelerar a 2200 RPM en motor TSI",
            "Pérdida de potencia intempestiva al adelantar, se prende el testigo EPC y al apagar y encender el motor vuelve a reaccionar",
            "Álabes de la geometría variable del turbocompresor atascados con carbonilla de aceite impidiendo el giro libre",
            "Motor corta inyección a 3000 RPM en carretera por código P2563 sensor de posición del actuador de sobrealimentación fuera de rango"
        ]
    },
    "inversor_hibrido": {
        "patron": "inversor de corriente IGBT o motor electrico",
        "casos": [
            "El auto híbrido no pasa a modo READY, se enciende el triángulo rojo maestro y marca código P0A78 rendimiento de inversor de motor",
            "Fallo en transistor de potencia IGBT del módulo inversor por recalentamiento arrojando DTC P0A94 convertidor DC-DC",
            "El convertidor DC-DC del inversor no suministra los 14V a la batería auxiliar de 12V y el vehículo se apaga rodando",
            "Olor a componente electrónico quemado en la caja del inversor sobre la transmisión y fusible AM2 de alta corriente fundido",
            "Aislamiento a masa del bobinado trifásico del motor MG2 por debajo de 5 MegaOhms con megóhmetro",
            "El motor eléctrico de tracción pega tirones violentos y vibra como lavadora al arrancar en pendiente empinada"
        ]
    },
    "refrigeracion_hibrido": {
        "patron": "refrigeracion de bateria/inversor",
        "casos": [
            "Se enciende alarma de temperatura en el inversor híbrido DTC P0A93 circuito de enfriamiento sin flujo de líquido",
            "La bomba de agua eléctrica dedicada al circuito del inversor híbrido no vibra ni recircula el refrigerante rosado",
            "El ventilador de refrigeración de la batería de alto voltaje bajo el asiento trasero sopla al 100% ruidosamente por filtro tapado con pelusa",
            "Filtro de la toma de aire de refrigeración de la batería híbrida saturado de polvo y pelos provocando sobrecalentamiento de celdas",
            "Líquido refrigerante del inversor hirviendo en el depósito auxiliar transparente por bolsa de aire en el radiador"
        ]
    },
    "bomba_alta_gdi": {
        "patron": "Inyectores sucios o filtro de combustible obstruido",
        "casos": [
            "Al acelerar a fondo a más de 3500 RPM el motor tironea violento y cae la presión de combustible en el riel con DTC P0087",
            "El vaso seguidor de leva Cam Follower de la bomba de alta presión se desgastó y perforó contra el árbol de levas",
            "Presión de riel de combustible no sube de 5 Bar al acelerar en motor de inyección directa GDI manteniéndose en presión de baja",
            "Cascabeleo metálico agudo en la culata y modo seguro en motor TSI por falla en el regulador de presión de gasolina P2293",
            "El carro pierde toda la fuerza al intentar rebasar en subida y en datos en vivo la presión real cae 20 Bar por debajo de la deseada",
            "Bomba de alta presión de gasolina goteando combustible por el retén hacia el cárter y diluyendo el aceite de motor"
        ]
    },
    "caja_automatica_cvt": {
        "patron": "caja automatica CVT / DSG",
        "casos": [
            "La transmisión CVT patina en subidas pronunciadas, el motor ruge a 4500 RPM pero la camioneta no gana velocidad",
            "DTC P0776 solenoide de control de presión de polea secundaria B atascado en caja automática CVT con pérdida de empuje",
            "Zumbido o quejido metálico agudo continuo en la caja CVT que se intensifica al acelerar por desgaste en la faja metálica de eslabones",
            "La caja automática da una patada seca al colocar Drive o Reversa y parpadea la luz de advertencia de temperatura de transmisión",
            "El cárter de la caja de cambios tiene viruta metálica pegada en los imanes colectores indicando fricción entre conos y correa",
            "Pérdida súbita de tracción en carretera, la aguja de RPM salta y la transmisión entra en modo de emergencia en una marcha simulada"
        ]
    },
    "embrague_powershift": {
        "patron": "Disco de embrague desgastado o patinando",
        "casos": [
            "Mensaje de transmisión averiada en tablero con código P2872 embrague A trabado acoplado en caja Powershift de doble embrague",
            "El carro da saltos y tironeos bruscos como zapateo de caballo al arrancar despacio en primera marcha en semáforo",
            "DTC P0882 voltaje bajo de entrada al módulo TCM por bornes flojos provocando que la caja pierda las marchas pares",
            "Horquilla de accionamiento del embrague A trabada mecánicamente por acumulación de ferodo y polvo en la campana",
            "La palanca de cambios se bloquea y la pantalla indica que no se reconoce la posición de aparcamiento o reversa",
            "Olor a embrague quemado penetrante tras circular en tráfico lento de Lima con caja de doble embrague seco"
        ]
    },
    "frenos_dtv_alabeo": {
        "patron": "Discos de freno alabeados",
        "casos": [
            "Al pisar suave el pedal de freno a 60 km/h se siente una pulsación rítmica continua que empuja el pedal hacia arriba",
            "Variación de espesor DTV en el disco de freno superior a 0.015 mm provocando saltos en la presión hidráulica",
            "El volante vibra y tiembla en las manos al presionar el freno bajando cuestas largas por sobrecalentamiento térmico del disco",
            "Los discos rectificados quedaron por debajo del espesor mínimo de seguridad y se alabearon en la primera frenada fuerte",
            "Sensación de cabeceo y frenado irregular en las ruedas delanteras al frenar sin que se active el sistema ABS"
        ]
    },
    "servofreno_vacio": {
        "patron": "servofreno.*booster",
        "casos": [
            "El pedal de freno está rígido como una piedra y para detener el auto tengo que pisar con las dos piernas con toda la fuerza",
            "Al pisar el freno se escucha un soplido continuo de aire sssss bajo el tablero y el motor empieza a temblar en ralentí",
            "Bomba de vacío mecánica en el árbol de levas no genera suficiente depresión de vacío marcando menos de -15 inHg en vacuómetro",
            "Válvula check antirretorno de la manguera de vacío del booster rajada perdiendo la asistencia de frenado al apagar el motor",
            "Manguera de vacío colapsada o estrangulada por calor impidiendo que el servofreno asista la pisada del conductor"
        ]
    },
    "canbus_red": {
        "patron": "Bateria descargada",
        "casos": [
            "El tablero parece árbol de navidad con todos los testigos prendidos y velocímetro muerto con código U0100 pérdida de comunicación",
            "Medí con multímetro entre el pin 6 y 14 del puerto OBD-II y marca 120 Ohms en vez de 60 Ohms, hay resistencia de terminación abierta",
            "Línea de comunicación CAN-Bus caída por cortocircuito entre cables trenzados impidiendo que el motor dé arranque",
            "La pantalla central muestra falla de frenos, falla de dirección y falla de motor simultáneamente por falso contacto en módulo Gateway",
            "Pérdida intermitente de comunicación con el módulo de transmisión TCM DTC U0101 al pasar por baches fuertes"
        ]
    },
    "sensor_ckp": {
        "patron": "bujias o bobinas",
        "casos": [
            "El motor da marcha vigorosa con el arrancador pero no enciende para nada, no hay pulso de inyección ni chispa con DTC P0335",
            "El vehículo se apaga de golpe en caliente al alcanzar los 90 grados y no vuelve a prender hasta que se enfría el sensor de cigüeñal",
            "Sensor de posición de cigüeñal CKP inductivo con bobina interna cortada en caliente por dilatación térmica",
            "Señal errática de sensor de cigüeñal de efecto Hall provocando explosiones falsas y cortes de inyección a 2500 RPM",
            "Cable del sensor CKP tostado y pelado por roce con el múltiple de escape haciendo falso contacto a masa"
        ]
    },
    "vvt_distribucion": {
        "patron": "sincronizacion variable de valvulas",
        "casos": [
            "Ruido de matraca metálica de 3 segundos al arrancar en frío por la mañana en el piñón de distribución variable VVT",
            "DTC P0011 posición sobreavanzada de árbol de levas de admisión por solenoide de aceite OCV trabado con lodo",
            "El motor tiembla en ralentí y se apaga al frenar en las esquinas porque el variador de fase no regresa a su posición cero",
            "Microtamiz del solenoide VVT-i tupido de barniz por usar aceite de motor 20W-50 inadecuado en motor moderno",
            "Desincronización entre árbol de levas y cigüeñal DTC P0016 por cadena de distribución estirada y tensador al límite"
        ]
    },
    "common_rail_presion": {
        "patron": "Common Rail Diesel",
        "casos": [
            "La camioneta diésel se apaga de golpe al acelerar fuerte en carretera con código de baja presión de riel P0087",
            "Arranque prolongado de más de 8 segundos en caliente para encender el motor diésel por fuga de retorno en inyector piezoeléctrico",
            "Inyector diésel con fuga interna que llena la probeta de retorno en menos de 1 minuto botando la presión del riel",
            "Válvula reguladora de presión SCV / IMV en la bomba de alta pegada por diésel con agua provocando ralentí oscilante",
            "Viruta metálica en el filtro de petróleo proveniente de la bomba de alta presión que contaminó todo el circuito Common Rail"
        ]
    },
    "frenos_neumaticos_camion": {
        "patron": "frenos neum.*tico.*Camiones",
        "casos": [
            "El camión no suelta los frenos de parqueo Maxi-Brake porque los tanques no logran subir de 5 Bar de presión de aire",
            "Fuga continua de aire soplado por la válvula de descarga rápida del eje posterior al presionar la pedalina de freno",
            "Pulmón de freno neumático con diafragma roto botando todo el aire comprimido a la atmósfera al frenar",
            "Compresor de aire de dos pistones con aros gastados pasa aceite de motor hacia los tanques de aire humedeciendo las válvulas",
            "Alarma sonora de baja presión de aire encendida permanente en la cabina del camión y freno trabado por seguridad"
        ]
    },
    "secador_aps_camion": {
        "patron": "secador APS obstruido",
        "casos": [
            "La válvula secadora de aire APS del camión estornuda y descarga aire cada 5 segundos sin parar en ralentí",
            "Sale agua condensada y emulsión grasosa negra por los grifos de purga de los tanques de aire comprimido",
            "Cartucho de desecante del secador colmatado de aceite de motor carbonizado impidiendo la retención de humedad",
            "Válvula de cuatro vías distribuidora de aire atascada con lodo aceitoso dejando sin aire el circuito de suspensión",
            "Válvula de purga automática del secador de aire congelada abierta botando toda la presión del camión a la atmósfera"
        ]
    },
    "correa_humeda_aceite": {
        "patron": "correa dentada banada en aceite",
        "casos": [
            "La correa de distribución sumergida en aceite se está deshaciendo y soltando pedazos de jebe dentro del cárter",
            "Testigo de baja presión de aceite se prende al calentar el motor porque los restos de la faja taparon el colador de la bomba",
            "Trozos de goma de la faja bañada en aceite taponaron la bomba de vacío dejando el pedal de freno completamente duro",
            "Faja bañada en aceite desgranada en motor Ford 1.0 Dragon o GM 1.2 Turbo por usar aceite sin especificación correcta",
            "Salto de dientes en la correa húmeda provocando pérdida de sincronización y choque de válvulas contra los pistones"
        ]
    },
    "termostato_electronico": {
        "patron": "termostato o motoventilador",
        "casos": [
            "El electroventilador del radiador se enciende a máxima velocidad en frío con código DTC P0597 resistencia de termostato abierta",
            "El termostato electrónico tiene la resistencia calefactora quemada y la aguja de temperatura sube al rojo vivo en tráfico",
            "Manguera superior del radiador hirviendo a 105 grados y manguera inferior totalmente fría por termostato trabado cerrado",
            "Fuga de refrigerante por la carcasa plástica del termostato pilotado que viaja por capilaridad mojando los pines de la ECU",
            "DTC P0128 temperatura de refrigerante por debajo del umbral de regulación por termostato trabado abierto en autopista"
        ]
    },
    "alternador_lin": {
        "patron": "Alternador defectuoso",
        "casos": [
            "El alternador inteligente con bus LIN no regula el voltaje y la batería amanece descargada con código DTC P065A",
            "Con el motor encendido el voltaje se queda clavado en 12.2V y no sube a 14V porque el puente de diodos está quemado",
            "Testigo de batería parpadea en el tablero y las luces de los faros suben y bajan de intensidad con zumbido en el alternador",
            "El sensor inteligente de batería IBS en el borne negativo tiene el cable de comunicación LIN arrancado tras cambiar batería",
            "Regulador de voltaje en cortocircuito enviando 16.8V que funde las bombillas halógenas y recalienta la batería"
        ]
    },
    "pastillas_al_fierro": {
        "patron": "Desgaste de pastillas y zapatas",
        "casos": [
            "Al frenar despacio en bajada suena un rechinido insoportable de fierro con fierro raspando la cara del disco",
            "Las pastillas de freno llegaron al sensor acústico de lata y chillan agudo cada vez que acaricio el pedal de freno",
            "Polvo negro de ferodo quemado impregnado en los aros delanteros y pedal de freno con tacto duro y frenada larga",
            "Las zapatas de freno del tambor trasero se quedaron sin material de fricción y rozan los remaches contra la pista",
            "Chirriador metálico de aviso de pastilla rozando continuamente contra el disco incluso sin pisar el pedal"
        ]
    },
    "fuga_liquido_frenos": {
        "patron": "Fuga hidraulica o aire en el sistema de frenos",
        "casos": [
            "Piso el pedal de freno y se va lentamente hasta el piso de la cabina, tengo que bombear para que agarre algo de presión",
            "Nivel de líquido de frenos en el depósito baja por debajo del mínimo cada 3 días y veo goteo aceitoso en el neumático trasero",
            "Pedal de freno con tacto esponjoso y blando tras cambiar pastillas debido a burbujas de aire atrapadas en el módulo ABS",
            "Cañería metálica de freno picada por óxido debajo del chasis botando un chorro de líquido DOT al pisar a fondo",
            "Bombín esclavo de rueda de tambor trasero con el guardapolvo reventado perdiendo presión hidráulica en frenadas bruscas"
        ]
    },
    "dpf_adblue_scr": {
        "patron": "filtro de particulas DPF.*AdBlue",
        "casos": [
            "Aparece mensaje en el cuadro indicando arranque no permitido en 500 km por avería en el sistema de urea AdBlue DEF",
            "El inyector de AdBlue en el escape está completamente taponado por una costra sólida de cristales blancos de sales de urea",
            "DTC P2463 acumulación excesiva de hollín en el filtro DPF y motor en modo degradado sin pasar de 80 km/h en carretera",
            "Sensor de presión diferencial del DPF con mangueras de silicona rotas arrojando lecturas falsas de contrapresión de escape",
            "Resistencia calefactora del tanque de AdBlue en circuito abierto impidiendo la dosificación de urea por las mañanas"
        ]
    }
}

def main():
    df_limpio = pd.read_csv(LIMPIO_CSV)
    clases_existentes = list(df_limpio["falla"].unique())
    print(f"Dataset limpio actual: {len(df_limpio)} filas, {len(clases_existentes)} clases.")

    nuevas_filas = []
    textos_existentes = set(df_limpio["sintoma"].dropna().str.strip().str.lower())

    for cat_key, cat_data in casos_adicionales.items():
        patron = cat_data["patron"]
        casos = cat_data["casos"]
        
        clase_target = None
        for c in clases_existentes:
            if re.search(patron, c, re.IGNORECASE):
                clase_target = c
                break
        
        if not clase_target:
            print(f"[ALERTA] No se encontro clase para patron: '{patron}' (clave: {cat_key})")
            continue

        for texto in casos:
            t_clean = texto.strip()
            if t_clean.lower() in textos_existentes:
                continue
            
            nuevas_filas.append({
                "sintoma": t_clean,
                "falla": clase_target,
                "codigo_falla": "N/A",
                "sistema": "General",
                "severidad": "alta"
            })
            textos_existentes.add(t_clean.lower())

    print(f"Nuevas filas unicas a incorporar en este lote: {len(nuevas_filas)}")

    if not nuevas_filas:
        print("No hay nuevas filas para agregar.")
        return

    df_nuevas = pd.DataFrame(nuevas_filas)
    df_limpio_actualizado = pd.concat([df_limpio, df_nuevas], ignore_index=True)
    df_limpio_actualizado.to_csv(LIMPIO_CSV, index=False)
    print(f"[EXITO] Guardado {LIMPIO_CSV}. Total filas ahora: {len(df_limpio_actualizado)}")

    if DATASET_CSV.exists():
        df_raw = pd.read_csv(DATASET_CSV)
        raw_textos = set(df_raw["sintoma"].dropna().str.strip().str.lower())
        filas_para_raw = []
        for nf in nuevas_filas:
            if nf["sintoma"].lower() not in raw_textos:
                filas_para_raw.append({"sintoma": nf["sintoma"], "falla": nf["falla"]})
                raw_textos.add(nf["sintoma"].lower())
        
        if filas_para_raw:
            df_nuevas_raw = pd.DataFrame(filas_para_raw)
            df_raw_actualizado = pd.concat([df_raw, df_nuevas_raw], ignore_index=True)
            df_raw_actualizado.to_csv(DATASET_CSV, index=False)
            print(f"[EXITO] Guardado {DATASET_CSV}. Total filas ahora: {len(df_raw_actualizado)}")

if __name__ == "__main__":
    main()
