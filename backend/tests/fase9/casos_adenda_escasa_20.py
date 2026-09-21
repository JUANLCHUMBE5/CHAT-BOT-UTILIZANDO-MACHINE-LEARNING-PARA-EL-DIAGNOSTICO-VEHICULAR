"""Definición de 20 escenarios conversacionales de información escasa, ambigua y 'no sé' (Adenda 9.1)."""

from __future__ import annotations

from typing import Any, Dict, List

ESCENARIOS_20_ADENDA_ESCASOS: List[Dict[str, Any]] = [
    # 1. Mensaje ultra-escaso: 'tiembla' -> debe pedir aclaración, NO emitir conclusión definitiva
    {
        "id": "adenda_01_tiembla_escaso",
        "turnos": ["tiembla"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "vibración",
    },
    # 2. Mensaje escaso: 'consume mucha gasolina'
    {
        "id": "adenda_02_consume_gasolina_escaso",
        "turnos": ["consume mucha gasolina"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "alto consumo de combustible",
    },
    # 3. Mensaje escaso: 'no prende'
    {
        "id": "adenda_03_no_prende_escaso",
        "turnos": ["no prende"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "motor no arranca",
    },
    # 4. Mensaje escaso: 'se apaga'
    {
        "id": "adenda_04_se_apaga_escaso",
        "turnos": ["se apaga"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "apagado de motor",
    },
    # 5. Mensaje escaso: 'suena feo'
    {
        "id": "adenda_05_suena_feo_escaso",
        "turnos": ["suena feo"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "ruido anómalo",
    },
    # 6. Mensaje escaso: 'no jala'
    {
        "id": "adenda_06_no_jala_escaso",
        "turnos": ["no jala"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "pérdida de potencia",
    },
    # 7. Mensaje escaso: 'se calienta'
    {
        "id": "adenda_07_se_calienta_escaso",
        "turnos": ["se calienta"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "sobrecalentamiento",
    },
    # 8. Mensaje escaso: 'frena raro'
    {
        "id": "adenda_08_frena_raro_escaso",
        "turnos": ["frena raro"],
        "espera_pregunta": True,
        "evidence_level_esperado": "BAJA",
        "sintoma_esperado": "anomalía en frenos",
    },
    # 9. Respuesta 'no sé' a pregunta de temperatura -> NO debe repetir la pregunta
    {
        "id": "adenda_09_no_se_temperatura",
        "turnos": [
            "el motor ratea en ralentí y pierde fuerza",
            "no sé",
        ],
        "debe_registrar_desconocido": "temperatura",
        "no_debe_repetir_intent": "TEMPERATURA_APARICION",
    },
    # 10. Respuesta 'ni idea' a pregunta de condición de operación
    {
        "id": "adenda_10_ni_idea_condicion",
        "turnos": [
            "suena un chillido en el motor",
            "ni idea",
        ],
        "debe_registrar_desconocido": "condicion_operacion",
        "no_debe_repetir_intent": "CONDICION_OPERACION",
    },
    # 11. Respuesta 'no me fijé'
    {
        "id": "adenda_11_no_me_fije",
        "turnos": [
            "la aguja de temperatura sube",
            "no me fijé",
        ],
        "no_debe_repetir": True,
    },
    # 12. Respuesta ambigua: 'a veces'
    {
        "id": "adenda_12_ambigua_a_veces",
        "turnos": [
            "vibra el timón",
            "a veces",
        ],
        "debe_tener_estado_ambiguo": True,
    },
    # 13. Respuesta ambigua: 'creo que sí'
    {
        "id": "adenda_13_ambigua_creo_que_si",
        "turnos": [
            "se apaga al frenar",
            "creo que sí",
        ],
        "debe_tener_estado_ambiguo": True,
    },
    # 14. Respuesta ambigua: 'más o menos'
    {
        "id": "adenda_14_ambigua_mas_o_menos",
        "turnos": [
            "cuesta arrancar en la mañana",
            "más o menos",
        ],
        "debe_tener_estado_ambiguo": True,
    },
    # 15. Respuesta ambigua: 'puede ser'
    {
        "id": "adenda_15_ambigua_puede_ser",
        "turnos": [
            "el pedal de freno se va al fondo",
            "puede ser",
        ],
        "debe_tener_estado_ambiguo": True,
    },
    # 16. Secuencia con 'no sé' seguido de 'a veces' (múltiple ambigüedad sin loop)
    {
        "id": "adenda_16_no_se_y_a_veces_sin_loop",
        "turnos": [
            "el carro falla",
            "no sé",
            "a veces",
        ],
        "debe_evitar_loop": True,
        "max_repreguntas_alcanzadas": False,
    },
    # 17. Secuencia de 'no sé' reiterado alcanzando límite de 3 repreguntas
    {
        "id": "adenda_17_no_se_reiterado_escape_obligatorio",
        "turnos": [
            "falla",
            "no sé",
            "ni idea",
            "no me fijé",
        ],
        "debe_alcanzar_limite_escape": True,
        "evidence_level_final": "BAJA",
    },
    # 18. DTC observado real vs DTC hipotético (Adenda 9.1 punto 1)
    {
        "id": "adenda_18_dtc_observado_real",
        "turnos": [
            "tengo código P0171 leído en escáner y mezcla pobre",
        ],
        "dtc_status_esperado": "DTC_OBSERVADO",
        "evidence_level_esperado": "ALTA",
    },
    # 19. Sin DTC observado (el bot no debe afirmar que el carro tiene código sin escaneo)
    {
        "id": "adenda_19_sin_dtc_observado",
        "turnos": [
            "falla el sensor de oxígeno o gasta gasolina",
        ],
        "dtc_status_esperado": "SIN_DTC",
        "no_debe_afirmar_dtc_fijo": True,
    },
    # 20. Modificador A/C con información escasa
    {
        "id": "adenda_20_modificador_ac_escaso",
        "turnos": [
            "vibra",
            "cuando prendo el aire acondicionado vibra más",
        ],
        "modificador_esperado": "A/C encendido",
        "sintoma_esperado": "vibración",
    },
]
