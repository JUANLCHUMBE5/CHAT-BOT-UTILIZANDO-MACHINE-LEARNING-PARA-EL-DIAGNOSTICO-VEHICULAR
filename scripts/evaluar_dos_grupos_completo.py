"""
Evaluación exhaustiva de dos grupos de 50 casos cada uno (Total: 100 pruebas)
para medir la confianza del modelo ML (Linear SVM calibrado), recuperación RAG
y detección DTC tras la incorporación de los 300 casos de taller y bases OBD.
"""

import os
import sys
import json
import time
from pathlib import Path

# Ajustar PYTHONPATH para backend
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.infrastructure.container import ServiceContainer

GRUPO_1 = [
    "Tengo un Yaris 2018, el motor tiembla bastante en mínimo y cuando acelero pierde fuerza. Me sale P0301.",
    "Corolla 2017, está fallando en ralentí y se siente como si trabajara en 3 cilindros. Check prendido.",
    "Kia Rio 2019, da tirones cuando acelero y el motor cabecea en mínimo.",
    "Hyundai Accent 2016, cambié bujías pero sigue temblando y perdiendo potencia cuando acelero.",
    "Nissan Versa 2018, en frío prende bien pero después empieza a fallar y tironear el motor.",
    "Toyota Etios 2019 no arranca, tablero prende débil y cuando doy contacto solo suena clic clic.",
    "Kia Picanto 2018, batería aparentemente está buena pero en las mañanas le cuesta bastante arrancar.",
    "Hyundai Accent 2017, se prende batería en tablero y las luces bajan de intensidad cuando está en mínimo.",
    "Corolla 2015, tengo P0562 y el voltaje cae cuando prendo luces y aire acondicionado.",
    "Nissan Sentra 2016, batería nueva pero después de manejar un rato se descarga y ya no vuelve a arrancar.",
    "Yaris 2017, cuando freno a 80 o 90 el timón comienza a vibrar fuerte.",
    "Kia Rio 2020, pedal de freno está esponjoso y tengo que pisarlo casi hasta el fondo para que frene.",
    "Hyundai Elantra 2018, escucho chillido adelante cada vez que freno.",
    "Corolla 2016, al frenar se va un poco hacia la derecha y siento que una rueda queda frenada.",
    "Nissan Versa 2019, después de cambiar pastillas el pedal sigue largo, ya revisé que no haya fuga visible.",
    "Toyota Corolla 2014 se está calentando, depósito hace burbujas y está botando refrigerante.",
    "Kia Rio 2016, temperatura sube cuando estoy en tráfico pero cuando avanzo vuelve a bajar.",
    "Hyundai Accent 2015, está consumiendo aceite y sale humo azul cuando acelero.",
    "Yaris 2013, prende testigo de aceite cuando está caliente y en mínimo, al acelerar se apaga.",
    "Nissan Sentra 2015, escucho golpeteo arriba del motor cuando calienta, parece taqué.",
    "Toyota Yaris mecánico, acelero pero el carro no avanza como debería y las revoluciones se disparan.",
    "Kia Rio 2017 mecánico, cuesta meter primera y retroceso con el motor prendido, apagado entran normal.",
    "Hyundai Accent 2016, pedal de embrague se fue al fondo y ya no regresa solo.",
    "Corolla mecánico 2015, cuando suelto embrague tiembla todo el carro al salir.",
    "Nissan Versa 2018, escucho ruido cuando piso el embrague y desaparece cuando lo suelto.",
    "Yaris 2018, golpea adelante cuando paso rompemuelles y pistas con huecos.",
    "Kia Rio 2019, el carro rebota demasiado después de pasar un bache y siento inestable la parte trasera.",
    "Hyundai Accent 2017, cuando doblo completamente suena tac tac tac en la rueda delantera.",
    "Corolla 2016, tengo ruido seco adelante al pasar huecos, ya revisé las llantas y están bien.",
    "Nissan Sentra 2017, a velocidad alta siento que el carro flota y se mueve demasiado.",
    "Toyota Yaris 2019, timón vibra entre 90 y 110 km/h pero cuando bajo velocidad desaparece.",
    "Kia Rio 2018, el carro se va hacia la izquierda aunque mantenga el timón derecho.",
    "Hyundai Accent 2020, desgaste de llanta delantera por la parte interna, las demás están normales.",
    "Corolla 2017, después de caer en un hueco quedó el timón medio chueco para andar recto.",
    "Nissan Versa 2018, cambié llantas y ahora tengo vibración fuerte en carretera, en ciudad casi no se siente.",
    "Yaris 2016, demora en arrancar y cuando acelero fuerte se queda sin fuerza como si faltara gasolina.",
    "Kia Rio 2017, motor gira pero no prende, revisé chispa y sí tiene.",
    "Hyundai Accent 2018, cuando piso a fondo pierde potencia pero manejando suave funciona normal.",
    "Corolla 2015, en subida se queda sin fuerza y a veces se apaga, tanque tiene gasolina.",
    "Nissan Sentra 2016, la bomba hace bastante ruido y el carro demora en prender por las mañanas.",
    "Toyota Yaris 2017, check engine prendido, ralentí inestable y consumo de gasolina aumentó bastante.",
    "Kia Rio 2019, cuando acelero demora en responder y a veces se apaga llegando al semáforo.",
    "Hyundai Accent 2016, motor inestable en mínimo pero cuando acelero trabaja mejor.",
    "Corolla 2018, check prendido y el carro está gastando más combustible de lo normal, no siento otra falla fuerte.",
    "Nissan Versa 2017, al encender en frío las RPM suben y bajan solas durante unos minutos.",
    "Corolla 2016, no tiene fuerza, tiembla y a veces demora en arrancar. No tengo scanner ahorita.",
    "Yaris 2018 llegó con check prendido, cliente dice que se apaga de vez en cuando y consume más gasolina.",
    "Kia Rio 2017, tengo vibración fuerte cuando acelero pero parado el motor trabaja normal.",
    "Hyundai Accent 2015, cliente dice que escucha golpe adelante cuando frena y también cuando pasa huecos.",
    "Nissan Sentra 2018, pierde fuerza después de manejar unos 20 minutos, lo apago un rato y vuelve a trabajar normal."
]

GRUPO_2 = [
    "El motor tiembla bien feo cuando estoy detenido en el semáforo y al acelerar pierde fuerza. Se nota más cuando ya está caliente. Tiene el código P0300.",
    "Arranca bien en frío, pero cuando lo uso, lo apago y al rato quiero prenderlo otra vez, le cuesta muchísimo o no quiere agarrar. Y sale un olor fuerte a gasolina.",
    "Mientras voy manejando las luces del tablero se ponen súper tenues y a veces el radio se reinicia solo.",
    "Cuando freno desde más de 90 km/h el volante y el pedal vibran fuerte, se siente como si temblara todo.",
    "En el tráfico la temperatura se sube bastante y el ventilador del radiador nunca prende.",
    "El embrague está patinando. Cuando acelero fuerte en tercera o cuarta, suben las revoluciones pero el carro no avanza igual.",
    "Cada vez que giro el volante hasta el fondo para estacionar, se escucha un clic o chasquido en la rueda delantera.",
    "El volante vibra solo cuando voy entre 95 y 115 km/h. En otras velocidades no se siente.",
    "Sale humo blanco constante por el escape, tiene olor dulce y el refrigerante baja aunque no veo fugas.",
    "Se me apaga el carro en los semáforos. Luego arranca normal sin problema.",
    "Tiene el Check Engine con código P0301 y se siente que un cilindro está fallando, vibra feo.",
    "Cuando acelero fuerte se ahoga un segundo y después pega un jalón. Se nota más cuando el tanque está por la mitad o menos.",
    "Al girar la llave solo hace un click y no arranca. Las luces del tablero sí prenden normal.",
    "El pedal de freno se siente blando y si lo mantengo apretado se va hundiendo solito.",
    "En las mañanas al arrancar se escucha un ruido fuerte de cadena por unos segundos y después se quita.",
    "El aire acondicionado enfría bien al principio, pero después de unos 10 minutos ya no enfría casi nada.",
    "La dirección está muy pesada cuando voy despacio, sobre todo al estacionar. En carretera mejora un poco.",
    "Se escucha un aullido que va aumentando con la velocidad y se pone más fuerte cuando doblo.",
    "Sale un olor fuerte a huevo podrido cuando acelero y se prendió el Check Engine.",
    "Cada vez que freno el carro se va solo hacia un lado.",
    "El ralentí está muy inestable, sube y baja solo, y a veces casi se apaga cuando estoy detenido.",
    "Al girar la llave no pasa absolutamente nada. Ni luces, ni click, ni nada.",
    "Sale humo azul cuando acelero y el motor está consumiendo aceite.",
    "En carretera a velocidad constante el motor tironea y a veces se apaga solo el aire acondicionado.",
    "Cada vez que freno se escucha un chillido agudo, aunque frene suavecito.",
    "Cuando suelto el acelerador el motor se queda acelerado varios segundos y después baja.",
    "Se escucha un zumbido bien fuerte que viene del tanque de la gasolina, sobre todo al acelerar.",
    "El carro falla solo cuando llueve o hay mucha humedad. En seco funciona normal.",
    "Al pasar topes o baches se siente un golpeteo fuerte en la parte delantera.",
    "Las luces delanteras y las del tablero parpadean de forma rara mientras manejo.",
    "Tiene el código P0171 de mezcla pobre y el carro se siente sin fuerza.",
    "Se escucha un tic-tic metálico en el motor, más fuerte cuando está frío.",
    "Se prendió la luz de la batería en el tablero mientras iba manejando.",
    "El pedal de freno está muy duro y el carro casi no quiere frenar.",
    "Después de prenderlo se calienta muy rápido, la aguja sube de golpe.",
    "Sale humo negro por el escape y está gastando mucha gasolina.",
    "Al pasar topes se siente un golpe seco en la parte de adelante.",
    "El motor falla de forma intermitente, pero solo cuando ya está bien caliente.",
    "Tiene código de sensor de detonación y a veces se siente como cascabeleo.",
    "Huele fuerte a azufre cuando acelero.",
    "El motor se queda en altas revoluciones varios segundos después de soltar el acelerador.",
    "Al arrancar en frío se escucha el ruido de la cadena más tiempo de lo normal.",
    "La dirección se siente floja y el carro no mantiene bien la línea recta.",
    "La vibración se siente más en el asiento que en el volante a cierta velocidad.",
    "Cuando acelero de golpe se ahoga un momento y después responde con un jalón.",
    "Tiene falla de un solo cilindro con código P030X y se siente la vibración.",
    "Sale humo blanco con olor dulce y el refrigerante baja aunque no hay fugas afuera.",
    "Al girar la llave no responde nada, ni siquiera las luces del tablero.",
    "Al frenar desde alta velocidad vibra mucho el volante y el pedal.",
    "La temperatura del motor casi no sube y el calefactor no calienta casi nada."
]

def evaluar_grupo(nombre, casos, modelo_ml, rag_service, dtc_service):
    print(f"\n=======================================================")
    print(f"EVALUANDO {nombre} ({len(casos)} CASOS)")
    print(f"=======================================================\n")
    
    resultados = []
    tiempos_ml = []
    tiempos_rag = []
    
    for idx, caso in enumerate(casos, 1):
        # 1. Pipeline de normalización de texto y purificación semántica
        t0_ml = time.perf_counter()
        texto_norm = normalizar_jerga_peruana(caso)
        texto_ml = purificar_sintoma_para_vectorizador_ml(texto_norm)
        
        # 2. Inferencia ML
        top_fallas = modelo_ml.predecir_top_fallas(texto_ml, limite=3)
        t_ml = (time.perf_counter() - t0_ml) * 1000
        tiempos_ml.append(t_ml)
        
        falla_top1 = top_fallas[0]["falla"] if top_fallas else "Desconocida"
        confianza_top1 = top_fallas[0]["probabilidad"] if top_fallas else 0.0
        
        # 3. RAG Retrieval
        t0_rag = time.perf_counter()
        contexto_rag, titulo_rag, sim_rag = rag_service.recuperar_contexto_con_similitud(texto_ml)
        t_rag = (time.perf_counter() - t0_rag) * 1000
        tiempos_rag.append(t_rag)
        
        # 4. DTC Lookup (si hay código)
        import re
        codigos_dtc = re.findall(r"\b[PBCU]\d{4}\b", caso, re.IGNORECASE)
        dtc_info = []
        for c in codigos_dtc:
            info = dtc_service.consultar_codigo(c)
            if info:
                dtc_info.append(f"{info['codigo']}: {info['descripcion']}")
        
        resultados.append({
            "idx": idx,
            "caso": caso,
            "falla_top1": falla_top1,
            "confianza_top1": confianza_top1,
            "top_fallas": top_fallas,
            "similitud_rag": round(sim_rag, 4),
            "titulo_rag": titulo_rag,
            "dtc_detectados": dtc_info,
            "t_ml_ms": round(t_ml, 2),
            "t_rag_ms": round(t_rag, 2)
        })
        
        # Log conciso
        dtc_str = f" | DTC: {codigos_dtc}" if codigos_dtc else ""
        print(f"[{idx:02d}] Conf: {confianza_top1*100:5.1f}% | Pred: {falla_top1} | RAG: {sim_rag*100:4.1f}% ({titulo_rag[:25]}...){dtc_str}")

    # Estadísticas agregadas
    confianzas = [r["confianza_top1"] for r in resultados]
    promedio_conf = sum(confianzas) / len(confianzas)
    min_conf = min(confianzas)
    max_conf = max(confianzas)
    casos_ge_80 = sum(1 for c in confianzas if c >= 0.80)
    casos_ge_70 = sum(1 for c in confianzas if c >= 0.70)
    casos_ge_60 = sum(1 for c in confianzas if c >= 0.60)
    
    prom_t_ml = sum(tiempos_ml) / len(tiempos_ml)
    prom_t_rag = sum(tiempos_rag) / len(tiempos_rag)
    
    print("\n-------------------------------------------------------")
    print(f"RESUMEN ESTADÍSTICO - {nombre}:")
    print(f"  Total Casos Evaluados:        {len(casos)}")
    print(f"  Confianza Promedio:           {promedio_conf*100:.2f}%")
    print(f"  Confianza Mínima:             {min_conf*100:.1f}%")
    print(f"  Confianza Máxima:             {max_conf*100:.1f}%")
    print(f"  Casos con Confianza >= 80%:   {casos_ge_80}/{len(casos)} ({casos_ge_80/len(casos)*100:.1f}%)")
    print(f"  Casos con Confianza >= 70%:   {casos_ge_70}/{len(casos)} ({casos_ge_70/len(casos)*100:.1f}%)")
    print(f"  Casos con Confianza >= 60%:   {casos_ge_60}/{len(casos)} ({casos_ge_60/len(casos)*100:.1f}%)")
    print(f"  Latencia Promedio ML:         {prom_t_ml:.2f} ms")
    print(f"  Latencia Promedio RAG:        {prom_t_rag:.2f} ms")
    print("-------------------------------------------------------\n")
    
    return {
        "nombre": nombre,
        "total": len(casos),
        "promedio_confianza": promedio_conf,
        "min_confianza": min_conf,
        "max_confianza": max_conf,
        "casos_ge_80": casos_ge_80,
        "casos_ge_70": casos_ge_70,
        "casos_ge_60": casos_ge_60,
        "prom_t_ml": prom_t_ml,
        "prom_t_rag": prom_t_rag,
        "resultados": resultados
    }

def main():
    modelo_ml = ServiceContainer.get_modelo_ml()
    rag_service = ServiceContainer.get_motor_rag()
    dtc_service = ServiceContainer.get_dtc_service()
    
    res_g1 = evaluar_grupo("1MER GRUPO (Flota Real Taller)", GRUPO_1, modelo_ml, rag_service, dtc_service)
    res_g2 = evaluar_grupo("2DO GRUPO (Sintomatología Clínica Diversa)", GRUPO_2, modelo_ml, rag_service, dtc_service)
    
    salida_json = BASE_DIR / "docs" / "graficas" / "reporte_evaluacion_100_casos.json"
    with open(salida_json, "w", encoding="utf-8") as f:
        json.dump({"grupo_1": res_g1, "grupo_2": res_g2}, f, ensure_ascii=False, indent=2)
    print(f"Resultados exportados a: {salida_json}")

if __name__ == "__main__":
    main()
