"""
Evaluación de los Nuevos 100 Casos (Grupo 1 y Grupo 2)
tras el reentrenamiento con Linear SVM calibrado + TF-IDF y expansión dirigida de clases débiles.
"""

import sys
import json
import time
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.infrastructure.container import ServiceContainer

GRUPO_1 = [
    "Mazda 3 2018 llegó fallando en mínimo, tiembla bastante y al acelerar da tirones. Scanner marca P0302.",
    "Toyota Corolla 2019 prende normal pero después de unos minutos comienza a cabecear y pierde fuerza, check parpadea cuando acelero.",
    "Kia Rio 2018 tiene chispa pero un cilindro no está trabajando parejo, ya cambié bujía y la falla sigue igual.",
    "Hyundai Accent 2017 en frío trabaja parejo pero cuando calienta empieza a fallar y tironear, si lo dejo enfriar mejora.",
    "Nissan Versa 2020 llegó con P0171, mínimo inestable y se escucha como una chupada de aire cerca del múltiple.",
    "Yaris 2018 no da arranque, tablero y faros prenden fuerte pero al girar llave solamente hace un clac y motor no gira.",
    "Corolla 2016 llegó con batería descargada, le puse batería cargada y prendió pero midiendo con motor encendido solo tengo 12.1 voltios.",
    "Kia Picanto 2019 arranca con puente pero después de dejarlo estacionado toda la noche otra vez aparece sin batería.",
    "Hyundai Elantra 2018 testigo de batería aparece cuando prendo luces y aire, al acelerar desaparece algunas veces.",
    "Nissan Sentra 2017 scanner arroja P0562 y el cliente dice que las luces bajan bastante cuando está parado en mínimo.",
    "Toyota Avanza 2018 tiene pedal de freno durísimo, para detenerlo tengo que hacer bastante fuerza y escucho un silbido cuando piso.",
    "Kia Rio 2019 frena pero pedal se va bajando poco a poco mientras lo mantengo pisado, no encuentro fuga por las ruedas.",
    "Corolla 2017 a 100 km/h anda normal, pero apenas piso freno comienza a vibrar timón y también siento pulsación en pedal.",
    "Hyundai Accent 2019 timón vibra entre 90 y 110, pero cuando freno no cambia la vibración.",
    "Nissan Versa 2018 una rueda delantera queda muy caliente después de manejar y el carro se jala hacia ese mismo lado.",
    "Yaris 2015 se está calentando parado en tráfico, revisé refrigerante y está lleno, cuando comienzo a avanzar la temperatura baja.",
    "Corolla 2014 está consumiendo refrigerante pero no veo fuga afuera, hace burbujas en depósito y sale humo blanco cuando calienta.",
    "Kia Sportage 2017 temperatura sube rápido y manguera superior está caliente pero la inferior sigue casi fría.",
    "Hyundai Accent 2016 testigo de aceite prende solamente con motor caliente en mínimo, si acelero un poco se apaga.",
    "Nissan Sentra 2015 está gastando aceite sin dejar manchas en el piso y al acelerar después de estar un rato en mínimo bota humo azul.",
    "Toyota Yaris mecánico, en cuarta acelero fuerte y RPM suben rápido pero velocidad casi no aumenta, en primera todavía sale normal.",
    "Kia Rio 2018 pedal de embrague quedó abajo y encontré líquido por la zona de la caja, ahora no entran bien los cambios.",
    "Hyundai Accent 2017 cuando piso embrague aparece un ronquido, cuando suelto pedal desaparece.",
    "Corolla 2016 al salir en primera tiembla bastante, pero una vez que el carro ya está avanzando trabaja normal.",
    "Fiat con Dualogic, en tráfico empieza a marcar N solo, bomba trabaja seguido y después de enfriar vuelve a funcionar.",
    "Nissan Sentra CVT entra en modo protección después de manejar un rato, no acelera normal y tengo P0841.",
    "Volkswagen con DSG da golpe al salir, a veces demora en enganchar D y después de calentarse empeora.",
    "Toyota automático demora varios segundos en entrar reversa cuando está frío, después entra con golpe.",
    "Yaris 2018 hace cloc cloc adelante al pasar pistas malas, en carretera lisa no suena y no vibra al frenar.",
    "Kia Rio 2019 al girar todo el timón y avanzar despacio hace tac tac tac de un lado, en línea recta no suena.",
    "Hyundai Accent 2018 rebota varias veces después de pasar rompemuelle y en carretera se siente medio flotante.",
    "Corolla 2017 después de pegar fuerte en un hueco quedó jalando a la derecha y el timón ya no queda centrado.",
    "Nissan Versa tiene desgaste fuerte solamente por la parte interna de las dos llantas delanteras.",
    "Toyota Yaris recién cambió llantas, desde ese día empieza vibración en timón llegando a 90 km/h, al frenar sigue prácticamente igual.",
    "Kia Rio hace zumbido en una rueda que aumenta con la velocidad, cuando hago curva hacia la izquierda el ruido cambia.",
    "Corolla 2016 demora en prender y en subida se queda sin fuerza, medí combustible y la presión cae bastante cuando acelero.",
    "Hyundai Accent gira motor normal pero no prende, hay chispa y al dar contacto no escucho trabajar la bomba debajo del asiento.",
    "Nissan Sentra arranca normal en frío pero después de 30 minutos pierde potencia, bomba empieza a zumbar fuerte y si lo dejo enfriar vuelve normal.",
    "Yaris 2017 mínimo inestable y se apaga al llegar al semáforo, si mantengo un poquito acelerado no se apaga.",
    "Corolla 2018 está botando humo negro, huele bastante a gasolina y el consumo aumentó, check engine prendido.",
    "Chevrolet llegó con P0420, no presenta una falla fuerte al manejar pero check vuelve después de borrarlo.",
    "Toyota con P0301 y P0303, motor tiembla y huele a gasolina cruda por escape, check parpadea bajo carga.",
    "Camión pierde aire estando estacionado, se escucha fuga continua cerca de una de las ruedas traseras y presión de tanques empieza a caer.",
    "Camión carga aire normal pero el secador está purgando a cada rato, hace descarga cada pocos segundos aunque no estoy pisando freno.",
    "Camión demora demasiado en levantar presión de aire y el compresor trabaja prácticamente todo el tiempo.",
    "Toyota cierre centralizado no abre puerta trasera con control, se escucha que el actuador intenta trabajar pero el pestillo no se mueve.",
    "Kia al presionar control remoto ninguna puerta cierra, pero desde cada seguro manual sí puedo cerrar las puertas.",
    "Cliente dice que el carro pierde fuerza después de un rato y prende check, no tengo código todavía y después de apagarlo vuelve a caminar normal.",
    "Hace un ruido adelante cuando manejo, a veces vibra y cliente dice que comenzó después de caer en un hueco.",
    "Motor tiembla un poco, consume más gasolina y algunas mañanas demora en prender. Scanner todavía no se ha conectado."
]

GRUPO_2 = [
    "Maestro, al salir en subida o cuando acelero fuerte en tercera, el carro empieza a temblar, jalonea feo y parpadea la luz del motor en el tablero. Si voy en bajada o despacio casi ni se siente.",
    "En plano rueda tranquilo, pero piso a fondo en carretera para adelantar y el carro se ahoga, tironea y no pasa de 80 km/h. Además, debajo del asiento de atrás se escucha un zumbido agudo y constante.",
    "Cuando paso los 60 o 70 km/h empieza a sonar un zumbido sordo adelante, como turbina de avión. Si doblo hacia la izquierda se calla, pero si doblo suave a la derecha suena el doble de fuerte. El timón no vibra para nada.",
    "En pista recta a 90 km/h rueda sedita, pero apenas piso el freno para detenerme, el timón empieza a sacudirse de izquierda a derecha y el pedal me tiembla en el pie. Apenas suelto el freno desaparece.",
    "En ciudad anda perfecto, pero apenas salgo a pista rápida y llego a 80 o 90 km/h, el timón empieza a vibrar solo. Si acelero más y paso los 110 km/h se quita. No toco el pedal de freno para nada.",
    "Frenando en velocidad responde bien, pero si me quedo parado en un semáforo con el pie puesto en el freno, siento que el pedal se va cayendo despacito hasta el fondo y el auto se empieza a mover. No veo charcos de líquido en el piso.",
    "Giro la llave y no hace nada de marcha, solo se escucha un 'clac' seco abajo en el motor. La batería tiene fuerza porque las luces del tablero ni bajan de brillo. Si le doy tres o cuatro llavazos seguidos, de repente agarra y prende normal.",
    "Prende al llavazo en frío, pero cuando ando media hora en tráfico pesado se apaga de golpe en plena marcha. Doy arranque, el motor gira con fuerza pero no enciende; tengo que esperar 20 minutos que enfríe y vuelve a prender como si nada.",
    "Llego a una esquina, piso el embrague o pongo neutro y el carro empieza a temblar, las revoluciones suben y bajan solas y se apaga. Si prendo el aire acondicionado se muere más rápido, pero mientras vaya acelerando no falla.",
    "En asfalto liso el carro no suena nada y el timón va derechito, pero paso por adoquines, baches o bajo un rompemuelle despacio y suena un 'cloc-cloc-cloc' seco y metálico abajo en las ruedas.",
    "En línea recta anda suave sin ruidos, pero cuando doblo cerrado en una esquina en primera acelerando, suena un traqueteo seco continuo adelante: 'tra-tra-tra-tra'.",
    "Acelero a fondo en subida, las revoluciones del motor se disparan a 4000 RPM pero el carro casi no avanza, se queda sin fuerza. Encima sale un olor a quemado amargo por debajo.",
    "Anoche manejando noté que las luces y el tablero bajaban de brillo y titilaban, la radio se apagaba sola y hoy por la mañana fui a prender el carro y no hizo absolutamente nada, ni el tablero prendió.",
    "Salgo a manejar y a los 10 minutos la aguja de temperatura se va directo a la zona roja. La manguera de arriba del radiador hierve, pero toco la manguera de abajo y está completamente fría.",
    "En frío prende al toque. Lo ruedo una hora, lo apago 15 minutos para comprar algo y al volver gira y gira el arranque y no prende. Cuando por fin arranca tose disparejo, bota humo negro y huele a pura gasolina cruda.",
    "El motor en neutro se queda acelerado a casi 1500 revoluciones y no baja para nada. Si abro el capó se escucha un siseo o silbido constante de aire cerca del motor.",
    "Solo cuando piso el acelerador en tercera o cuarta para ganar velocidad en pista, toda la trompa del carro se sacude de lado a lado. Si suelto el pedal y voy rodando libre, la sacudida se corta al instante.",
    "Paso un bache y el carro sigue rebotando varias veces seguidas como si fuera una lancha. Al clavar los frenos siento que la trompa se va demasiado contra el suelo.",
    "Con el carro parado en neutro y sin pisar pedales suena un chillido como de rodaje en la caja. Apenas piso el embrague al fondo, el ruido se apaga por completo; lo suelto y vuelve a sonar.",
    "Cada vez que pongo primera y saco el embrague para avanzar, o cuando meto retroceso, se siente un golpe seco adelante, como si el motor saltara y golpeara el chasis.",
    "Le doy a la llave para arrancar y el motor no gira, solo hace un sonido rápido como de metralleta ('tr-tr-tr-tr') y las agujas del tablero parpadean y se vuelven locas.",
    "En tramos cortos anda bien, pero en carretera por más que pise a fondo no pasa de 3000 revoluciones, se siente ahogado y por la palanca de cambios calienta tanto que quema la cabina.",
    "Piso el acelerador de golpe para salir rápido y el motor se queda pensando un segundo, no responde de inmediato y se siente pesado, como amarrado.",
    "En carretera la temperatura va perfecta a la mitad, pero apenas me agarra el tráfico o me quedo parado esperando a alguien, el agua empieza a hervir y sube la aguja.",
    "Cada vez que piso el freno suave se escucha un chillido agudo insoportable, y si piso con más fuerza se siente como un raspón áspero de fierro contra fierro adelante.",
    "El carro anda suave y no vibra, pero si suelto el timón un segundo en pista recta se va de golpe hacia la derecha. Me fijé y la llanta delantera de ese lado está comida por el borde de adentro.",
    "Al girar el timón despacio para estacionar en la cochera, suena un crujido metálico seco arriba ('clac-ñic'), como si un resorte grueso se trabara y se soltara de golpe.",
    "El carro calienta al exigirlo en subida, el depósito de agua empieza a burbujear y las mangueras se ponen duras como piedra. Por el escape sale un humo blanco que huele medio dulce.",
    "Cada vez que voy al grifo y lleno el tanque de gasolina a tope, el carro no quiere prender; tengo que quedarme dándole arranque con el acelerador a fondo para que prenda tosiendo.",
    "En autopista el carro se siente flotante, el timón tiene un juego muerto al centro que no responde y tengo que ir corrigiendo la trayectoria todo el tiempo para que no se salga del carril.",
    "En las mañanas demora bastante en prender, le cuesta salir de parado en primera y noto que se está tragando la gasolina mucho más rápido que antes.",
    "Al doblar toda la dirección despacio o al entrar a una rampa suena un 'clac' seco y fuerte abajo en la rueda. El timón por ratos se siente un poco duro.",
    "Las luces alumbran demasiado brillante por momentos y se me quemaron dos focos en una semana. Hay un olor fuerte como a huevo podrido en el motor y la batería está tibia.",
    "El carro se frena solo hacia un lado al rodar. Cuando me estaciono después de manejar 20 minutos, el aro delantero derecho quema si lo toco y sale un olor a balata quemada.",
    "El pedal del freno se va muy abajo y frena despacio, se siente como pisar una esponja. Si bombeo el pedal dos o tres veces seguidas, agarra cuerpo y frena arriba.",
    "En las mañanas al prender suena un taqueteo metálico rápido arriba en el motor ('tac-tac-tac'). Después de cinco minutos que calienta el carro, el ruido se apaga por completo.",
    "A velocidad bien baja, como a 20 km/h, siento que el carro cabecea de lado a lado como si fuera cojeando, pero el timón no jala para ningún lado.",
    "Le hicieron el cambio de faja hace dos días y el carro quedó sin fuerza, tiembla disparejo en mínimo y por el escape se escuchan unos pedos sordos al acelerar.",
    "En carretera la aguja de temperatura se cae al suelo como si el carro estuviera apagado, y la calefacción adentro solo bota aire tibio, casi frío.",
    "Huele fuertísimo a gasolina cruda por el motor, bota humo negro por el escape y al desconectar una manguerita delgadita de aire que va a la flauta de inyección salió un chorro de gasolina.",
    "Cuando prendo las luces altas o la calefacción, la aguja de la temperatura se sube sola de golpe al máximo, pero el motor no está hirviendo. A veces al dar arranque gira lento como pesado.",
    "Demora como cinco segundos de giro continuo para prender. Tiene la luz de check engine prendida fija y siento que en alta velocidad no tiene el mismo pique de antes.",
    "Si acelero suave responde parejo, pero si piso el pedal a fondo de golpe empieza a toser, pierde fuerza y no acelera nada hasta que suelto un poco el pie.",
    "Prendo el aire acondicionado y se escucha un chillido fuertísimo de faja adelante, el motor tiembla como si se fuera a apagar y por las rejillas solo sale aire caliente.",
    "Cuando dejo el carro parado en una bajada aguantado con el motor y vuelvo a acelerar, o al prenderlo en la mañana, bota una nube de humo azul por el tubo de escape y luego se limpia.",
    "El carro cascabelea al acelerar a medio pedal como si tuviera gasolina de mala calidad, gasta bastante y por ratos tose humo negro al salir de los semáforos.",
    "El motor calienta únicamente cuando voy en subida con pasajeros o con carga, pero en pista plana o bajada la aguja baja a su nivel normal al toque.",
    "Se me prendió la luz del motor en el tablero fija. El auto anda normal, no falla ni jalonea, pero la cola del escape está llena de hollín negro y me rinde mucho menos kilometraje por galón.",
    "Al acelerar suena un zumbido ronco y fuerte debajo de los asientos como si fuera carro de carrera, y cuando me quedo parado en ralentí se mete olor a humo de escape a la cabina.",
    "Paso por cualquier hueco y suena un golpe seco de fierro abajo, y al mirar el carro de frente estacionado en plano se nota claramente que un lado está más caído que el otro."
]

def evaluar_grupo(nombre, casos, modelo_ml, rag_service, dtc_service):
    print(f"\n================================================================================")
    print(f"EVALUANDO: {nombre} ({len(casos)} Casos)")
    print(f"================================================================================\n")
    
    resultados = []
    tiempos_ml = []
    tiempos_rag = []
    
    for idx, caso in enumerate(casos, 1):
        # 1. Pipeline lingüístico y purificación semántica
        t0_ml = time.perf_counter()
        texto_norm = normalizar_jerga_peruana(caso)
        texto_ml = purificar_sintoma_para_vectorizador_ml(texto_norm)
        
        # 2. Inferencia ML (Linear SVM calibrado)
        top_fallas = modelo_ml.predecir_top_fallas(texto_ml, limite=3)
        t_ml = (time.perf_counter() - t0_ml) * 1000
        tiempos_ml.append(t_ml)
        
        falla_top1 = top_fallas[0]["falla"] if top_fallas else "Desconocida"
        confianza_top1 = top_fallas[0]["probabilidad"] if top_fallas else 0.0
        
        top2_falla = top_fallas[1]["falla"] if len(top_fallas) > 1 else "-"
        top2_conf = top_fallas[1]["probabilidad"] if len(top_fallas) > 1 else 0.0
        
        top3_falla = top_fallas[2]["falla"] if len(top_fallas) > 2 else "-"
        top3_conf = top_fallas[2]["probabilidad"] if len(top_fallas) > 2 else 0.0
        
        # 3. RAG Retrieval
        t0_rag = time.perf_counter()
        contexto_rag, titulo_rag, sim_rag = rag_service.recuperar_contexto_con_similitud(texto_ml)
        t_rag = (time.perf_counter() - t0_rag) * 1000
        tiempos_rag.append(t_rag)
        
        # 4. Extracción de códigos DTC
        codigos_dtc = re.findall(r"\b[PBCU]\d{4}\b", caso, re.IGNORECASE)
        dtc_info = []
        for c in codigos_dtc:
            info = dtc_service.consultar_codigo(c.upper())
            if info:
                dtc_info.append(f"{info['codigo']} ({info.get('descripcion_es') or info.get('descripcion', '')})")
            else:
                dtc_info.append(f"{c.upper()} (Genérico)")
        
        item = {
            "idx": idx,
            "caso": caso,
            "falla_top1": falla_top1,
            "confianza_top1": round(confianza_top1, 4),
            "top2_falla": top2_falla,
            "top2_conf": round(top2_conf, 4),
            "top3_falla": top3_falla,
            "top3_conf": round(top3_conf, 4),
            "similitud_rag": round(sim_rag, 4),
            "titulo_rag": titulo_rag,
            "dtc_detectados": dtc_info,
            "t_ml_ms": round(t_ml, 2),
            "t_rag_ms": round(t_rag, 2)
        }
        resultados.append(item)
        
        dtc_txt = f" | DTC: {','.join(codigos_dtc)}" if codigos_dtc else ""
        print(f"[{idx:02d}] {confianza_top1*100:5.1f}% | Top1: {falla_top1:<30} | Top2: {top2_falla:<25} ({top2_conf*100:4.1f}%) | RAG: {sim_rag*100:4.1f}% ({titulo_rag[:22]}...){dtc_txt}")

    # Estadísticas
    confianzas = [r["confianza_top1"] for r in resultados]
    promedio_conf = sum(confianzas) / len(confianzas)
    min_conf = min(confianzas)
    max_conf = max(confianzas)
    casos_ge_90 = sum(1 for c in confianzas if c >= 0.90)
    casos_ge_80 = sum(1 for c in confianzas if c >= 0.80)
    casos_ge_70 = sum(1 for c in confianzas if c >= 0.70)
    casos_ge_60 = sum(1 for c in confianzas if c >= 0.60)
    casos_lt_60 = sum(1 for c in confianzas if c < 0.60)
    
    prom_t_ml = sum(tiempos_ml) / len(tiempos_ml)
    prom_t_rag = sum(tiempos_rag) / len(tiempos_rag)
    
    print("\n--------------------------------------------------------------------------------")
    print(f"RESUMEN ESTADÍSTICO - {nombre}")
    print(f"--------------------------------------------------------------------------------")
    print(f"Total casos analizados:          {len(casos)}")
    print(f"Confianza promedio:              {promedio_conf*100:.2f}%")
    print(f"Confianza mínima / máxima:       {min_conf*100:.1f}% / {max_conf*100:.1f}%")
    print(f"Casos con confianza >= 90%:      {casos_ge_90}/{len(casos)} ({casos_ge_90/len(casos)*100:.1f}%)")
    print(f"Casos con confianza >= 80%:      {casos_ge_80}/{len(casos)} ({casos_ge_80/len(casos)*100:.1f}%)")
    print(f"Casos con confianza >= 70%:      {casos_ge_70}/{len(casos)} ({casos_ge_70/len(casos)*100:.1f}%)")
    print(f"Casos con confianza >= 60%:      {casos_ge_60}/{len(casos)} ({casos_ge_60/len(casos)*100:.1f}%)")
    print(f"Casos con confianza < 60%:       {casos_lt_60}/{len(casos)} ({casos_lt_60/len(casos)*100:.1f}%)")
    print(f"Tiempo promedio inferencia ML:   {prom_t_ml:.2f} ms")
    print(f"Tiempo promedio búsqueda RAG:    {prom_t_rag:.2f} ms")
    print(f"--------------------------------------------------------------------------------\n")
    
    return {
        "nombre": nombre,
        "total": len(casos),
        "promedio_confianza": promedio_conf,
        "min_confianza": min_conf,
        "max_confianza": max_conf,
        "casos_ge_90": casos_ge_90,
        "casos_ge_80": casos_ge_80,
        "casos_ge_70": casos_ge_70,
        "casos_ge_60": casos_ge_60,
        "casos_lt_60": casos_lt_60,
        "prom_t_ml": prom_t_ml,
        "prom_t_rag": prom_t_rag,
        "resultados": resultados
    }

def main():
    modelo_ml = ServiceContainer.get_modelo_ml()
    rag_service = ServiceContainer.get_motor_rag()
    dtc_service = ServiceContainer.get_dtc_service()
    
    res1 = evaluar_grupo("1MER GRUPO (50 Casos de Taller con Prefijo Vehicular y DTCs)", GRUPO_1, modelo_ml, rag_service, dtc_service)
    res2 = evaluar_grupo("2DO GRUPO (50 Casos Sintomatología Mecánica Profunda y Coloquial)", GRUPO_2, modelo_ml, rag_service, dtc_service)
    
    out_file = BASE_DIR / "docs" / "graficas" / "reporte_evaluacion_nuevos_100_casos.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"grupo_1": res1, "grupo_2": res2}, f, ensure_ascii=False, indent=2)
    print(f"Reporte completo guardado en: {out_file}")

if __name__ == "__main__":
    main()
