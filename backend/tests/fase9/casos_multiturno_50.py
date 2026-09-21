"""Definición de 50 escenarios conversacionales multi-turno independientes para la Fase 9.1."""

from __future__ import annotations

from typing import Any, Dict, List

ESCENARIOS_50_MULTITURNO: List[Dict[str, Any]] = [
    # 1. Caso base acumulativo estándar (4 turnos)
    {
        "id": "caso_01_acumulativo_ralenti",
        "turnos": [
            "mi Toyota tiembla",
            "cuando estoy parado",
            "en el semáforo casi se apaga",
            "si acelero mejora",
        ],
        "hechos_esperados": {
            "marca": "Toyota",
            "sintoma_vibración": "vibración",
            "condicion_operacion": "detenido en ralentí",
            "evolucion_accion": "mejora al acelerar",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Toyota presenta vibración cuando estoy parado en el semáforo casi se apaga si acelero mejora.",
    },
    # 2. Pérdida de potencia y tironeo bajo carga con bujías cambiadas (3 turnos)
    {
        "id": "caso_02_carga_bujias_cambiadas",
        "turnos": [
            "tengo un Nissan Sentra que se chupa",
            "jalonea feo en subida cuando acelero",
            "ya cambié las bujías y sigue igual",
        ],
        "hechos_esperados": {
            "marca": "Nissan",
            "sintoma_pérdida_de_potencia": "pérdida de potencia",
            "condicion_operacion": "al acelerar bajo carga",
            "reemplazado_bujías": "bujías reemplazado(a)",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Nissan Sentra se chupa jalonea en subida al acelerar y ya cambié las bujías.",
    },
    # 3. Sobrecalentamiento con ebullición y humo blanco (evidencia fuerte temprana) (2 turnos)
    {
        "id": "caso_03_sobrecalentamiento_humo_blanco",
        "turnos": [
            "el motor calienta demasiado y hierve el depósito",
            "bota humo blanco por el escape",
        ],
        "hechos_esperados": {
            "sintoma_sobrecalentamiento": "sobrecalentamiento",
            "sintoma_humo_blanco___ebullición_refrigerante": "humo blanco / ebullición refrigerante",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "El motor calienta demasiado hierve el depósito y bota humo blanco por el escape.",
    },
    # 4. Arranque con chasquido seco solenoide (2 turnos)
    {
        "id": "caso_04_arranque_clac_seco",
        "turnos": [
            "mi Hyundai no prende",
            "al dar llave solo suena un clac seco pero las luces quedan prendidas",
        ],
        "hechos_esperados": {
            "marca": "Hyundai",
            "sintoma_motor_no_arranca": "motor no arranca",
            "sintoma_chasquido_de_arranque_clac": "chasquido de arranque clac",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Hyundai no prende al girar llave suena clac seco solenoide con luces encendidas.",
    },
    # 5. Respuesta a temperatura: usuario responde "caliente" (2 turnos)
    {
        "id": "caso_05_temperatura_caliente_corta",
        "turnos": [
            "falla el motor",
            "caliente",
        ],
        "respuesta_corta_turno": 1,
        "hechos_esperados": {
            "temperatura": "caliente",
        },
    },
    # 6. Respuesta a temperatura: usuario responde "en frío" (2 turnos)
    {
        "id": "caso_06_temperatura_frio_corta",
        "turnos": [
            "cuesta arrancar en la mañana",
            "frío",
        ],
        "hechos_esperados": {
            "temperatura": "frío",
        },
    },
    # 7. Corrección explícita de temperatura ("me equivoqué, es caliente") (3 turnos)
    {
        "id": "caso_07_correccion_temperatura",
        "turnos": [
            "el carro tiembla en frío",
            "me equivoqué, en realidad solo falla caliente",
            "en el semáforo parado",
        ],
        "hechos_esperados": {
            "temperatura": "caliente",
            "condicion_operacion": "detenido en ralentí",
        },
        "debe_corregir": "temperatura",
    },
    # 8. Contradicción explícita de condición ("no es en marcha, es parado") (2 turnos)
    {
        "id": "caso_08_correccion_condicion",
        "turnos": [
            "vibra en carretera",
            "me equivoqué, no es frío, es caliente y solo cuando estoy parado",
        ],
        "hechos_esperados": {
            "temperatura": "caliente",
            "condicion_operacion": "detenido en ralentí",
        },
    },
    # 9. Inserción de código DTC en turno posterior (3 turnos)
    {
        "id": "caso_09_dtc_posterior",
        "turnos": [
            "el motor ratea y perdió fuerza",
            "lo escaneamos en el taller",
            "arrojó código P0301",
        ],
        "hechos_esperados": {
            "sintoma_funcionamiento_irregular___misfire": "funcionamiento irregular / misfire",
            "dtc_P0301": "P0301",
        },
        "dtc_esperado": "P0301",
    },
    # 10. Código DTC P0420 directo (evidencia fuerte temprana) (1 turno)
    {
        "id": "caso_10_dtc_p0420_directo",
        "turnos": [
            "tengo check engine encendido con código P0420 y olor a azufre",
        ],
        "hechos_esperados": {
            "dtc_P0420": "P0420",
        },
        "dtc_esperado": "P0420",
    },
    # 11. Medición de presión de riel / combustible (2 turnos)
    {
        "id": "caso_11_medicion_presion_bomba",
        "turnos": [
            "el carro se chupa en alta y tose",
            "medí con manómetro y tiene 20 psi en el riel de gasolina",
        ],
        "hechos_esperados": {
            "medicion": "20 psi",
        },
    },
    # 12. Componente intercambiado / descartado (2 turnos)
    {
        "id": "caso_12_componente_intercambiado",
        "turnos": [
            "misfire persistente en cilindro 3 con P0303",
            "ya intercambié la bobina del cilindro 3 con la del 2 y sigue fallando el 3",
        ],
        "hechos_esperados": {
            "dtc_P0303": "P0303",
            "probado_bobinas": "bobinas probado/descartado",
        },
    },
    # 13. Jerga peruana: cáliper / mordaza y pedal esponjoso (3 turnos)
    {
        "id": "caso_13_jerga_frenos",
        "turnos": [
            "mi Kia frena raro",
            "la mordaza calienta mucho",
            "el pedal se siente esponjoso al pisar el freno",
        ],
        "hechos_esperados": {
            "marca": "Kia",
            "condicion_operacion": "al frenar",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Kia frena raro cáliper calienta y pedal de freno esponjoso al frenar.",
    },
    # 14. Jerga peruana: collarín / crapodina de embrague (2 turnos)
    {
        "id": "caso_14_jerga_embrague",
        "turnos": [
            "suena un chillido agudo en la transmisión",
            "suena la crapodina únicamente al pisar el embrague",
        ],
        "hechos_esperados": {
            "sintoma_ruido_anómalo": "ruido anómalo",
        },
    },
    # 15. Jerga peruana: rodaje / rodamiento picado (2 turnos)
    {
        "id": "caso_15_jerga_rodamiento",
        "turnos": [
            "zumba fuerte en carretera a 90 km/h",
            "es un rodaje de rueda delantera que aúlla al doblar la dirección",
        ],
        "hechos_esperados": {
            "condicion_operacion": "al doblar la dirección",
        },
    },
    # 16. Jerga: 'está chancho' (pérdida de potencia) y subida (2 turnos)
    {
        "id": "caso_16_chancho_subida",
        "turnos": [
            "el auto está chancho no jala nada",
            "se queda sin fuerza en subida cuando acelero",
        ],
        "hechos_esperados": {
            "sintoma_pérdida_de_potencia": "pérdida de potencia",
            "condicion_operacion": "al acelerar bajo carga",
        },
    },
    # 17. Jerga: 'zapatea' al salir en primera (embrague) (2 turnos)
    {
        "id": "caso_17_zapatea_embrague",
        "turnos": [
            "el carro zapatea feo",
            "al soltar el embrague para salir en primera marcha",
        ],
        "hechos_esperados": {
            "sintoma_vibración": "vibración",
        },
    },
    # 18. Modificador A/C encendido (Adenda 9.1 punto 6) (2 turnos)
    {
        "id": "caso_18_modificador_ac",
        "turnos": [
            "mi Toyota Corolla tiembla en ralentí",
            "cuando enciendo el A/C vibra más fuerte",
        ],
        "hechos_esperados": {
            "marca": "Toyota",
            "modificador_ac": "A/C encendido",
            "sintoma_vibración": "vibración",
        },
    },
    # 19. Modificador luces altas (Adenda 9.1 punto 6) (2 turnos)
    {
        "id": "caso_19_modificador_luces",
        "turnos": [
            "las luces parpadean y la aguja de RPM oscila",
            "empeora con las luces altas prendidas en la noche",
        ],
        "hechos_esperados": {
            "modificador_luces": "luces encendidas",
        },
    },
    # 20. Reinicio de caso: 'otro carro' (3 turnos con reset intermedio)
    {
        "id": "caso_20_reinicio_otro_carro",
        "turnos": [
            "Toyota Corolla vibra en ralentí",
            "otro carro",
            "Nissan Sentra no arranca suena clac",
        ],
        "debe_reiniciar_en_turno": 1,
        "marca_final_esperada": "Nissan",
        "marca_no_debe_existir": "Toyota",
    },
    # 21. Reinicio de caso: 'nuevo diagnóstico' (3 turnos)
    {
        "id": "caso_21_reinicio_nuevo_diagnostico",
        "turnos": [
            "consume refrigerante y hierve",
            "nuevo diagnóstico",
            "Hyundai Accent pedal de freno duro",
        ],
        "debe_reiniciar_en_turno": 1,
        "marca_final_esperada": "Hyundai",
    },
    # 22. Selección de opción: 'la 2' (2 turnos)
    {
        "id": "caso_22_opcion_la_2",
        "turnos": [
            "el motor recalienta",
            "la 2",
        ],
        "respuesta_corta_turno": 1,
    },
    # 23. Selección de opción numérica: '1' (2 turnos)
    {
        "id": "caso_23_opcion_1_directa",
        "turnos": [
            "falla de encendido",
            "1",
        ],
        "respuesta_corta_turno": 1,
    },
    # 24. Selección de opción: 'la 3' (2 turnos)
    {
        "id": "caso_24_opcion_la_3",
        "turnos": [
            "ruido en tren delantero",
            "la 3",
        ],
        "respuesta_corta_turno": 1,
    },
    # 25. Respuesta SÍ a confirmación (2 turnos)
    {
        "id": "caso_25_respuesta_si",
        "turnos": [
            "el ventilador enciende tarde",
            "sí",
        ],
        "respuesta_corta_turno": 1,
    },
    # 26. Respuesta NO a confirmación (2 turnos)
    {
        "id": "caso_26_respuesta_no",
        "turnos": [
            "humo por escape",
            "no",
        ],
        "respuesta_corta_turno": 1,
    },
    # 27. Respuesta 'ya lo cambié' (2 turnos)
    {
        "id": "caso_27_ya_lo_cambie",
        "turnos": [
            "el termostato se queda pegado",
            "ya lo cambié",
        ],
        "respuesta_corta_turno": 1,
    },
    # 28. Respuesta 'eso ya lo revisé' (2 turnos)
    {
        "id": "caso_28_eso_ya_lo_revise",
        "turnos": [
            "comprobar los fusibles",
            "eso ya lo revisé",
        ],
        "respuesta_corta_turno": 1,
    },
    # 29. Acumulación en 5 turnos progresivos (Toyota Hilux)
    {
        "id": "caso_29_cinco_turnos_hilux",
        "turnos": [
            "Toyota Hilux",
            "diésel",
            "tarda en encender en frío",
            "bota humo negro",
            "pierde fuerza en subida",
        ],
        "hechos_esperados": {
            "marca": "Toyota",
            "combustible": "Diésel",
            "temperatura": "frío",
            "sintoma_pérdida_de_potencia": "pérdida de potencia",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Toyota Hilux diésel tarda en encender en frío bota humo negro y pierde fuerza en subida.",
    },
    # 30. Acumulación en 6 turnos progresivos (Chevrolet Sail)
    {
        "id": "caso_30_seis_turnos_sail",
        "turnos": [
            "Chevrolet Sail",
            "año 2014",
            "a gas GLP",
            "vibra en ralentí",
            "en el semáforo",
            "mejora al acelerar",
        ],
        "hechos_esperados": {
            "marca": "Chevrolet",
            "anio": "2014",
            "combustible": "GLP",
            "sintoma_vibración": "vibración",
            "condicion_operacion": "detenido en ralentí",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Chevrolet Sail año 2014 a gas GLP vibra en ralentí en el semáforo y mejora al acelerar.",
    },
    # 31. Intento de loop semántico con preguntas repetidas (3 turnos)
    {
        "id": "caso_31_loop_temperatura_repetida",
        "turnos": [
            "falla el motor",
            "caliente",
            "ya dije que caliente",
        ],
        "hechos_esperados": {
            "temperatura": "caliente",
        },
        "debe_evitar_loop": True,
    },
    # 32. Límite de 3 repreguntas forzando salida diferencial
    {
        "id": "caso_32_escape_limite_3_repreguntas",
        "turnos": [
            "el carro falla",
            "no sé",
            "a veces",
            "puede ser",
        ],
        "debe_alcanzar_limite_escape": True,
    },
    # 33. Información suficiente directa (3 categorías en 1 turno)
    {
        "id": "caso_33_suficiencia_directa",
        "turnos": [
            "Toyota Corolla tiembla cuando estoy detenido en el semáforo y casi se apaga",
        ],
        "espera_suficiente_inmediato": True,
    },
    # 34. Información insuficiente inicial que pasa a suficiente en turno 2
    {
        "id": "caso_34_insuficiente_luego_suficiente",
        "turnos": [
            "tiembla el motor",
            "parado en el semáforo en caliente",
        ],
        "espera_pregunta_turno_0": True,
        "espera_diagnostico_turno_1": True,
    },
    # 35. Transmisión automática DSG golpetea en caliente (2 turnos)
    {
        "id": "caso_35_dsg_golpeteo",
        "turnos": [
            "Volkswagen con caja automática DSG",
            "golpea al pasar los cambios cuando calienta",
        ],
        "hechos_esperados": {
            "marca": "Volkswagen",
            "temperatura": "caliente",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Volkswagen caja automática DSG golpea al pasar cambios en caliente.",
    },
    # 36. Embrague patinando en subida (2 turnos)
    {
        "id": "caso_36_embrague_patina_subida",
        "turnos": [
            "el motor sube revoluciones pero el carro no avanza con fuerza",
            "el embrague patina al acelerar en subida",
        ],
        "hechos_esperados": {
            "condicion_operacion": "al acelerar bajo carga",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Motor sube revoluciones carro no avanza con fuerza embrague patinando en subida al acelerar.",
    },
    # 37. Freno vibra únicamente al pisar pedal (discos alabeados) (2 turnos)
    {
        "id": "caso_37_discos_alabeados_freno",
        "turnos": [
            "el timón y el pedal tiemblan",
            "ocurre únicamente al frenar a alta velocidad",
        ],
        "hechos_esperados": {
            "condicion_operacion": "al frenar",
            "sintoma_vibración": "vibración",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Timón y pedal tiemblan vibración únicamente al frenar a alta velocidad.",
    },
    # 38. Llantas desbalanceadas en carretera (2 turnos)
    {
        "id": "caso_38_llantas_desbalanceadas",
        "turnos": [
            "vibra el volante a partir de 90 km/h",
            "en carretera a velocidad constante sin tocar el freno",
        ],
        "hechos_esperados": {
            "condicion_operacion": "en carretera a velocidad",
            "sintoma_vibración": "vibración",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Volante vibra en carretera a 90 km/h sin tocar el pedal de freno llantas desbalanceadas.",
    },
    # 39. Batería descargada con bornes sulfatados (2 turnos)
    {
        "id": "caso_39_bateria_bornes",
        "turnos": [
            "el carro no prende",
            "las luces del tablero parpadean y el borne de batería está sulfatado",
        ],
        "hechos_esperados": {
            "sintoma_motor_no_arranca": "motor no arranca",
        },
    },
    # 40. Alternador testigo de batería encendido (2 turnos)
    {
        "id": "caso_40_alternador_testigo",
        "turnos": [
            "testigo de batería encendido en rojo",
            "medí con multímetro y bota 11.8V con el motor en marcha",
        ],
        "hechos_esperados": {
            "medicion": "11.8v",
        },
    },
    # 41. Bomba de gasolina quemada sin zumbido (2 turnos)
    {
        "id": "caso_41_bomba_gasolina_sin_zumbido",
        "turnos": [
            "da arranque pero no enciende",
            "no se escucha el zumbido de la bomba en el tanque y no hay presión",
        ],
        "hechos_esperados": {
            "sintoma_motor_no_arranca": "motor no arranca",
        },
    },
    # 42. Inyectores sucios con tironeo constante (2 turnos)
    {
        "id": "caso_42_inyectores_sucios",
        "turnos": [
            "el motor tironea a cualquier velocidad",
            "le cuesta responder al acelerador y gasta nafta",
        ],
        "hechos_esperados": {
            "sintoma_funcionamiento_irregular___misfire": "funcionamiento irregular / misfire",
        },
    },
    # 43. Sensor de oxígeno y humo negro (2 turnos)
    {
        "id": "caso_43_sensor_oxigeno_humo_negro",
        "turnos": [
            "bota humo negro por el escape",
            "olor a gasolina cruda y consumo excesivo",
        ],
        "hechos_esperados": {
            "sintoma_alto_consumo_de_combustible": "alto consumo de combustible",
        },
    },
    # 44. Termostato trabado en caliente (2 turnos)
    {
        "id": "caso_44_termostato_cerrado",
        "turnos": [
            "la temperatura sube al máximo en tráfico",
            "manguera superior de radiador hirviendo e inferior fría",
        ],
        "hechos_esperados": {
            "sintoma_sobrecalentamiento": "sobrecalentamiento",
        },
    },
    # 45. Amortiguadores reventados en baches (2 turnos)
    {
        "id": "caso_45_amortiguadores_baches",
        "turnos": [
            "el carro rebota demasiado",
            "golpea seco en pistas con baches y huecos",
        ],
        "hechos_esperados": {
            "sintoma_ruido_anómalo": "ruido anómalo",
        },
    },
    # 46. Punta de palier homocinética al girar (2 turnos)
    {
        "id": "caso_46_palier_homocinetica",
        "turnos": [
            "suena un clac clac continuo",
            "solo cuando doblo la dirección acelerando",
        ],
        "hechos_esperados": {
            "condicion_operacion": "al doblar la dirección",
        },
    },
    # 47. Cremallera de dirección asistida con juego (2 turnos)
    {
        "id": "caso_47_cremallera_juego",
        "turnos": [
            "el timón tiene mucho juego libre",
            "golpetea al doblar y fuga líquido hidráulico",
        ],
        "hechos_esperados": {
            "sintoma_ruido_anómalo": "ruido anómalo",
        },
    },
    # 48. Falla cuerpo aceleración IAC con RPM inestables (2 turnos)
    {
        "id": "caso_48_cuerpo_aceleracion_iac",
        "turnos": [
            "las RPM suben y bajan solas",
            "se apaga al llegar al semáforo en neutro",
        ],
        "hechos_esperados": {
            "condicion_operacion": "detenido en ralentí",
            "evolucion_accion": "oscilación de RPM",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "RPM suben y bajan solas aguja oscila se apaga al desacelerar o llegar al semáforo cuerpo de aceleración IAC.",
    },
    # 49. Reinicio por expresión 'empezar de nuevo'
    {
        "id": "caso_49_empezar_de_nuevo",
        "turnos": [
            "Ford Ranger bota humo azul",
            "empezar de nuevo",
            "Toyota Yaris no frena bien",
        ],
        "debe_reiniciar_en_turno": 1,
        "marca_final_esperada": "Toyota",
    },
    # 50. Conversación completa con datos técnicos y DTC (4 turnos)
    {
        "id": "caso_50_completo_toyota_corolla",
        "turnos": [
            "tengo un Toyota Corolla 2018 a gasolina",
            "vibra en el semáforo y casi se apaga",
            "al acelerar empareja",
            "le pusimos escáner y tiene código P0300",
        ],
        "hechos_esperados": {
            "marca": "Toyota",
            "modelo": "Corolla",
            "anio": "2018",
            "combustible": "Gasolina",
            "sintoma_vibración": "vibración",
            "condicion_operacion": "detenido en ralentí",
            "dtc_P0300": "P0300",
        },
        "es_consistencia_par": True,
        "texto_single_turn": "Toyota Corolla 2018 a gasolina vibra en el semáforo casi se apaga al acelerar empareja escáner código P0300.",
    },
]
