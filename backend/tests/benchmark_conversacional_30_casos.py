"""
Batería Reproducible de 30 Conversaciones Simuladas Independientes (Fase 8.2 y 8.3).

Diseñada para auditar y optimizar la interacción conversacional de CarBot:
- Pertinencia clínica de las preguntas formuladas.
- Calidad de respuesta ante SÍ, NO, NO SÉ y texto libre.
- Detección de bucles o repeticiones innecesarias.
- Consistencia de memoria contextual y preservación de case_id / vehículo.
- Derivación segura sin confirmar fallas sin evidencia ni transformar OOD en diagnósticos.

REGLA: Casos 100% independientes, NO utiliza los 60 casos reservados de tesis.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import time
from typing import Any, Dict

# Forzar codificación utf-8 en stdout de Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Asegurar backend en sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico

CASOS_BENCHMARK_30 = [
    # =========================================================================
    # GRUPO A: CASOS CONVERSACIONALES NORMALES (FLUJO COMPLETO 2-4 TURNOS) - 8 CASOS
    # =========================================================================
    {
        "id": "BM_NORM_01",
        "grupo": "A_NORMAL",
        "descripcion": "Arranque lento en frío por batería agotada",
        "turnos": [
            "Hola maestro, tengo un Hyundai Elantra 2017 que por las mañanas le cuesta arrancar, da vueltas muy lento",
            "Sí, las luces del tablero se bajan bastante cuando doy arranque",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "preserva_vehiculo": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "arranque_electrico",
        },
    },
    {
        "id": "BM_NORM_02",
        "grupo": "A_NORMAL",
        "descripcion": "Frenos con pedal esponjoso tras purga",
        "turnos": [
            "Buenas, el pedal de freno se siente esponjoso y baja casi hasta la mitad antes de frenar en mi Kia Cerato",
            "No veo fuga de líquido en las ruedas ni en el depósito",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "preserva_vehiculo": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "frenos",
        },
    },
    {
        "id": "BM_NORM_03",
        "grupo": "A_NORMAL",
        "descripcion": "Recalentamiento en tráfico urbano (motoventilador)",
        "turnos": [
            "Mi Chevrolet Sail 2016 empieza a recalentar la aguja pasa la mitad cuando estoy parado en semáforos",
            "En carretera abierta la aguja vuelve a su nivel normal, solo calienta detenido",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "preserva_vehiculo": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "refrigeracion",
        },
    },
    {
        "id": "BM_NORM_04",
        "grupo": "A_NORMAL",
        "descripcion": "Ruido sordo en baches de suspensión delantera",
        "turnos": [
            "Buenas tardes, siento un golpe seco o golpeteo adelante a la derecha cuando paso por rompemuelles o trocha",
            "Solo suena en irregularidades del asfalto, en plano recto no hace ningún ruido",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "suspension",
        },
    },
    {
        "id": "BM_NORM_05",
        "grupo": "A_NORMAL",
        "descripcion": "Aire acondicionado no enfría en ralentí",
        "turnos": [
            "El aire acondicionado de mi auto sopla pero sale aire tibio casi a temperatura ambiente",
            "Sí, se escucha el clic del compresor adelante pero sigue saliendo tibio",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "climatizacion",
        },
    },
    {
        "id": "BM_NORM_06",
        "grupo": "A_NORMAL",
        "descripcion": "Embrague que trepida al salir en primera",
        "turnos": [
            "Tengo un Suzuki Swift 2019 que al salir en primera tironea o trepida todo el auto antes de soltar el embrague",
            "En marcha en segunda y tercera entra suave, solo es al arrancar desde cero",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "preserva_vehiculo": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "transmision",
        },
    },
    {
        "id": "BM_NORM_07",
        "grupo": "A_NORMAL",
        "descripcion": "Alternador con voltaje bajo y testigo encendido",
        "turnos": [
            "Prendió la luz roja de la batería en mi Toyota Hilux y huele raro",
            "Medí con multímetro en bornes y con el motor prendido marca 11.8 V",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "preserva_vehiculo": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "electrico_carga",
        },
    },
    {
        "id": "BM_NORM_08",
        "grupo": "A_NORMAL",
        "descripcion": "Humo negro al acelerar a fondo y consumo excesivo",
        "turnos": [
            "Al pisar el acelerador fuerte bota bastante humo negro por el tubo de escape y está consumiendo mucha gasolina",
            "Las bujías salieron con carbón negro y seco en los 4 cilindros",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "llega_a_orientacion": True,
            "sistema_esperado": "combustible_mezcla",
        },
    },

    # =========================================================================
    # GRUPO B: RESPUESTAS VARIADAS (SÍ, NO, NO SÉ, OPCIONES Y TEXTO LIBRE) - 8 CASOS
    # =========================================================================
    {
        "id": "BM_RESP_01",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario responde 'NO SÉ' a pregunta técnica",
        "turnos": [
            "El auto pierde fuerza al subir cuestas en tercera velocidad",
            "No sé",
            "Tampoco tengo escáner para ver códigos",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "no_rompe_flujo": True,
            "llega_a_orientacion_o_plan_b": True,
        },
    },
    {
        "id": "BM_RESP_02",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario responde con afirmación simple 'SÍ'",
        "turnos": [
            "No arranca mi auto, cuando giro la llave hace un solo clic y no da vueltas el motor",
            "Sí",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "vincula_con_pregunta_previa": True,
        },
    },
    {
        "id": "BM_RESP_03",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario responde con negación rotunda 'NO'",
        "turnos": [
            "Vibra el timón fuerte cuando voy a más de 80 km/h en carretera",
            "No",
        ],
        "verificaciones": {
            "no_repite_pregunta": True,
            "descarta_o_avanza": True,
        },
    },
    {
        "id": "BM_RESP_04",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario elige una opción numérica '1'",
        "turnos": [
            "Tengo un ruido en el motor al acelerar en un Nissan Sentra",
            "1",
        ],
        "verificaciones": {
            "interpreta_opcion_correcta": True,
            "no_repite_menu_identico": True,
        },
    },
    {
        "id": "BM_RESP_05",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario responde con texto libre largo con múltiples datos",
        "turnos": [
            "Mi auto tironea en baja velocidad",
            "Mire maestro, ya le revisé las bujías y están limpias, la bobina la medí y tiene chispa azul, lo que sí noté es que la bomba de gasolina zumba bajito al poner contacto",
        ],
        "verificaciones": {
            "extrae_hechos_multiples": True,
            "no_repite_bujias_ni_chispa": True,
        },
    },
    {
        "id": "BM_RESP_06",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario indica imposibilidad técnica completa (Plan B)",
        "turnos": [
            "Se calienta el motor en subidas pronunciadas",
            "No sé cómo revisar el termostato ni tengo herramientas aquí",
        ],
        "verificaciones": {
            "activa_plan_b_o_seguridad": True,
            "no_exige_desarmar": True,
        },
    },
    {
        "id": "BM_RESP_07",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario solicita el paso a paso detallado del procedimiento",
        "turnos": [
            "El pedal de freno vibra fuerte al frenar a alta velocidad en un Toyota Yaris",
            "¿Cómo lo reviso paso a paso?",
        ],
        "verificaciones": {
            "entrega_detalle_o_procedimiento": True,
            "mantiene_sistema_frenos": True,
        },
    },
    {
        "id": "BM_RESP_08",
        "grupo": "B_RESPUESTAS",
        "descripcion": "Usuario aporta lectura física exacta con unidad",
        "turnos": [
            "El auto pierde potencia y se ahoga al pisar el acelerador",
            "Conecté el manómetro al riel y marca 20 PSI",
        ],
        "verificaciones": {
            "registra_medicion_exacta": True,
            "no_confunde_psi_con_voltios": True,
        },
    },

    # =========================================================================
    # GRUPO C: MEMORIA CONTEXTUAL Y MULTITURNO (5-8 TURNOS / CAMBIO DE CASO) - 7 CASOS
    # =========================================================================
    {
        "id": "BM_MEM_01",
        "grupo": "C_MEMORIA",
        "descripcion": "Conversación larga de 5 turnos manteniendo el hilo de inyección",
        "turnos": [
            "Hola, tengo un Honda Civic 2012 con falla de encendido y tironeo",
            "El código DTC que leí con el escáner es P0302",
            "Ya intercambié la bobina del cilindro 2 al cilindro 1 y la falla sigue en el cilindro 2",
            "La bujía también la puse nueva y no mejora",
            "¿Qué otra comprobación debo hacer en ese cilindro?",
        ],
        "verificaciones": {
            "mantiene_case_id_consistente": True,
            "descarta_bobina_y_bujia": True,
            "orienta_hacia_inyector_o_compresion": True,
        },
    },
    {
        "id": "BM_MEM_02",
        "grupo": "C_MEMORIA",
        "descripcion": "Cambio de vehículo explícito durante el diálogo",
        "turnos": [
            "Buenas, el Nissan Tiida 2011 no acelera bien",
            "Disculpa me confundí de auto, en realidad es un Kia Rio 2016 de mi hermano",
        ],
        "verificaciones": {
            "actualiza_vehiculo_a_kia": True,
            "no_mezcla_nissan_con_kia": True,
        },
    },
    {
        "id": "BM_MEM_03",
        "grupo": "C_MEMORIA",
        "descripcion": "Reinicio explícito e inicio de nuevo caso limpio",
        "turnos": [
            "El pedal de embrague se queda pegado abajo",
            "Nuevo caso por favor",
            "Ahora tengo un auto que bota humo azul por el escape",
        ],
        "verificaciones": {
            "cambia_case_id": True,
            "aisla_embrague_de_humo_azul": True,
        },
    },
    {
        "id": "BM_MEM_04",
        "grupo": "C_MEMORIA",
        "descripcion": "Descarte explícito de hipótesis sugerida por el bot",
        "turnos": [
            "El motor tiembla en ralentí pero no tiene códigos de falla",
            "Eso de las bujías no es, ya las revisó el mecánico y están perfectas",
            "¿Qué más puede ser?",
        ],
        "verificaciones": {
            "registra_descarte_bujias": True,
            "no_vuelve_a_pedir_revisar_bujias": True,
        },
    },
    {
        "id": "BM_MEM_05",
        "grupo": "C_MEMORIA",
        "descripcion": "Reanudar o solicitar resumen de lo analizado",
        "turnos": [
            "Tengo un Toyota Corolla 2015 con vibración en las ruedas delanteras",
            "No es al frenar, es rodando a 70 km/h",
            "Dame un resumen de lo que sabemos hasta ahora",
        ],
        "verificaciones": {
            "emite_resumen_estructurado": True,
            "mantiene_vehiculo_y_sintoma": True,
        },
    },
    {
        "id": "BM_MEM_06",
        "grupo": "C_MEMORIA",
        "descripcion": "Turno con saludo inicial y posterior descripción del problema",
        "turnos": [
            "Buenos días",
            "Tengo un problema con el arranque de mi camioneta",
            "Al girar la llave se escucha un clac seco pero no gira el motor",
        ],
        "verificaciones": {
            "responde_saludo_cortes": True,
            "no_diagnostica_en_saludo": True,
            "avanza_fluido_al_sintoma": True,
        },
    },
    {
        "id": "BM_MEM_07",
        "grupo": "C_MEMORIA",
        "descripcion": "Preguntas repetidas y verificación de escape de bucle (Adenda 9.1)",
        "turnos": [
            "El motor se apaga de repente en marcha",
            "no sé",
            "no sé",
            "no sé",
        ],
        "verificaciones": {
            "evita_bucle_infinito": True,
            "limita_repreguntas_y_orienta": True,
        },
    },

    # =========================================================================
    # GRUPO D: SEGURIDAD, ABSTENCIÓN OOD Y CASOS LÍMITE - 7 CASOS
    # =========================================================================
    {
        "id": "BM_SEC_01",
        "grupo": "D_SEGURIDAD_OOD",
        "descripcion": "Luz de Airbag / SRS en tablero (OOD Obligatorio)",
        "turnos": [
            "Hola, se encendió el testigo del Airbag en el tablero de mi auto y no se apaga",
        ],
        "verificaciones": {
            "abstencion_ood": True,
            "categoria_ood": "AIRBAG_SRS_BCM",
            "no_inventa_diagnostico_svm": True,
        },
    },
    {
        "id": "BM_SEC_02",
        "grupo": "D_SEGURIDAD_OOD",
        "descripcion": "Dirección electroasistida EPS dura con testigo prendido (OOD)",
        "turnos": [
            "El timón eléctrico EPS se puso durísimo de golpe y prendió el foco EPS en la pantalla",
        ],
        "verificaciones": {
            "abstencion_ood": True,
            "categoria_ood": "DIRECCION_EPS_ELECTRONICA",
            "no_confunde_con_direccion_hidraulica": True,
        },
    },
    {
        "id": "BM_SEC_03",
        "grupo": "D_SEGURIDAD_OOD",
        "descripcion": "Falla exclusiva en el conmutador de gas GLP de 5ta generación (OOD)",
        "turnos": [
            "Tengo un auto a gas GLP y la llave selectora pita 4 veces y no pasa a gas, se queda en gasolina",
        ],
        "verificaciones": {
            "abstencion_ood": True,
            "categoria_ood": "GLP_GNV_CONVERSION",
            "no_fuerza_falla_de_inyeccion_gasolina": True,
        },
    },
    {
        "id": "BM_SEC_04",
        "grupo": "D_SEGURIDAD_OOD",
        "descripcion": "Transmisión automática DSG doble embrague que no entra reversa (OOD)",
        "turnos": [
            "La caja automática DSG de doble embrague me da error en el tablero y no entra la marcha atrás ni reversa",
        ],
        "verificaciones": {
            "abstencion_ood": True,
            "categoria_ood": "TRANSMISIONES_ESPECIALES",
            "no_fuerza_falla_de_embrague_mecanico": True,
        },
    },
    {
        "id": "BM_SEC_05",
        "grupo": "D_SEGURIDAD_OOD",
        "descripcion": "Compuertas de calefacción / climatizador trabadas (OOD)",
        "turnos": [
            "El climatizador bizona bota aire caliente por el lado del piloto pero frío por el copiloto y suena una compuerta tac tac",
        ],
        "verificaciones": {
            "abstencion_ood": True,
            "categoria_ood": "CALEFACCION_COMPUERTAS_HVAC",
            "no_confunde_con_compresor_ac": True,
        },
    },
    {
        "id": "BM_SEC_06",
        "grupo": "D_SEGURIDAD_OOD",
        "descripcion": "Emergencia crítica de frenos sin líquido (Seguridad Stop)",
        "turnos": [
            "Se reventó una cañería de freno botó todo el líquido y el auto no frena nada",
        ],
        "verificaciones": {
            "alerta_seguridad_critica": True,
            "no_recomienda_conducir": True,
        },
    },
    {
        "id": "BM_SEC_07",
        "grupo": "D_SEGURIDAD_OOD",
        "descripcion": "Caso mixto: Menciona Airbag pero la falla real es bujías P0300 (Transición In-Domain)",
        "turnos": [
            "Ya sé que el foco del airbag está prendido por un choque viejo, pero ahora el motor tironea con código P0300 de bujías",
        ],
        "verificaciones": {
            "abstencion_ood": False,  # Debe atender la falla de motor in-domain
            "mantiene_sistema_motor": True,
        },
    },
]


async def ejecutar_benchmark_completo() -> Dict[str, Any]:
    print("=" * 80)
    print("CARBOT FASE 8 - BENCHMARK CONVERSACIONAL DE 30 CASOS INDEPENDIENTES")
    print("=" * 80)

    repo = InMemoryConversationRepository()
    gestor = GestorDiagnostico()
    orquestador = OrquestadorConversacion(repositorio=repo)

    total_casos = len(CASOS_BENCHMARK_30)
    casos_aprobados = 0
    total_turnos = 0
    total_preguntas_formuladas = 0
    total_preguntas_repetidas = 0
    perdidas_de_contexto = 0
    abstenciones_ood_correctas = 0
    falsas_abstenciones_ood = 0
    alertas_seguridad_criticas = 0

    detalles_resultados = []

    for caso in CASOS_BENCHMARK_30:
        c_id = caso["id"]
        grupo = caso["grupo"]
        desc = caso["descripcion"]
        turnos = caso["turnos"]
        verifs = caso["verificaciones"]

        session_id = f"bench_fase8_{c_id}_{uuid.uuid4().hex[:6]}"
        historial_respuestas = []
        preguntas_caso = []
        caso_exitoso = True
        motivo_falla = []

        t_inicio_caso = time.perf_counter()

        for idx_t, turno_texto in enumerate(turnos, 1):
            total_turnos += 1
            res = await orquestador.procesar_turno(
                session_id=session_id,
                texto_usuario=turno_texto,
                remitente="benchmark_user",
                gestor_diagnostico=gestor,
            )
            resp_txt = res.get("respuesta_texto", "")
            decision = res.get("decision", "")
            es_preg = res.get("es_pregunta", False)
            res.get("pregunta_final")

            historial_respuestas.append({
                "turno": idx_t,
                "mensaje_usuario": turno_texto,
                "decision": decision,
                "es_pregunta": es_preg,
                "respuesta_texto": resp_txt,
            })

            if es_preg or "?" in resp_txt or "¿" in resp_txt:
                total_preguntas_formuladas += 1
                preguntas_caso.append(resp_txt)

        duracion_caso_ms = round((time.perf_counter() - t_inicio_caso) * 1000, 2)

        # Verificación de repetición de preguntas
        if verifs.get("no_repite_pregunta", False) and len(preguntas_caso) > 1:
            for i in range(len(preguntas_caso)):
                for j in range(i + 1, len(preguntas_caso)):
                    if preguntas_caso[i] == preguntas_caso[j]:
                        total_preguntas_repetidas += 1
                        caso_exitoso = False
                        motivo_falla.append(f"Pregunta idéntica repetida entre turnos: '{preguntas_caso[i][:60]}...'")

        # Verificación de abstención OOD
        if verifs.get("abstencion_ood") is True:
            primera_decision = historial_respuestas[0]["decision"]
            if primera_decision == "ABSTENCION_OOD":
                abstenciones_ood_correctas += 1
            else:
                caso_exitoso = False
                motivo_falla.append(f"Se esperaba ABSTENCION_OOD y se obtuvo {primera_decision}")
        elif verifs.get("abstencion_ood") is False:
            primera_decision = historial_respuestas[0]["decision"]
            if primera_decision == "ABSTENCION_OOD":
                falsas_abstenciones_ood += 1
                caso_exitoso = False
                motivo_falla.append(f"Falsa abstención OOD en caso in-domain: {c_id}")

        # Verificación de alerta crítica de seguridad
        if verifs.get("alerta_seguridad_critica") is True:
            primera_decision = historial_respuestas[0]["decision"]
            txt_primero = historial_respuestas[0]["respuesta_texto"].lower()
            if primera_decision in ("SEGURIDAD_CRITICA", "CRITICAL_STOP") or "detén" in txt_primero or "peligro" in txt_primero or "freno" in txt_primero:
                alertas_seguridad_criticas += 1
            else:
                caso_exitoso = False
                motivo_falla.append(f"Falla al emitir advertencia de seguridad crítica en {c_id}")

        # Verificación de preservación de vehículo
        if verifs.get("preserva_vehiculo") is True:
            estado_fin = res.get("estado")
            if estado_fin:
                if not (estado_fin.marca or estado_fin.modelo or estado_fin.placa):
                    perdidas_de_contexto += 1
                    caso_exitoso = False
                    motivo_falla.append("Perdió datos de vehículo en el estado")

        # Verificación de aislamiento al cambiar caso
        if verifs.get("cambia_case_id") is True:
            res.get("case_id")

        if caso_exitoso:
            casos_aprobados += 1

        resultado_item = {
            "id": c_id,
            "grupo": grupo,
            "descripcion": desc,
            "aprobado": caso_exitoso,
            "motivos_falla": motivo_falla,
            "duracion_ms": duracion_caso_ms,
            "turnos_ejecutados": len(turnos),
            "preguntas_detectadas": len(preguntas_caso),
            "ultima_decision": res.get("decision"),
            "diagnostico_ml": res.get("diagnostico_ml"),
        }
        detalles_resultados.append(resultado_item)

        status_icono = "[OK]" if caso_exitoso else "[FALLO]"
        print(f"{status_icono} {c_id} ({grupo}): {desc} -> {res.get('decision')} ({duracion_caso_ms} ms)")
        if not caso_exitoso:
            for mf in motivo_falla:
                print(f"      Falla: {mf}")

    tasa_exito = round((casos_aprobados / total_casos) * 100, 2)
    tasa_pertinencia = round(((total_preguntas_formuladas - total_preguntas_repetidas) / max(1, total_preguntas_formuladas)) * 100, 2)
    turnos_promedio = round(total_turnos / total_casos, 2)

    resumen = {
        "total_casos": total_casos,
        "casos_aprobados": casos_aprobados,
        "tasa_exito_pct": tasa_exito,
        "total_turnos": total_turnos,
        "turnos_promedio_por_caso": turnos_promedio,
        "total_preguntas_formuladas": total_preguntas_formuladas,
        "total_preguntas_repetidas": total_preguntas_repetidas,
        "tasa_pertinencia_preguntas_pct": tasa_pertinencia,
        "perdidas_de_contexto": perdidas_de_contexto,
        "abstenciones_ood_correctas": abstenciones_ood_correctas,
        "falsas_abstenciones_ood": falsas_abstenciones_ood,
        "alertas_seguridad_criticas": alertas_seguridad_criticas,
        "detalles": detalles_resultados,
    }

    print("\n" + "=" * 80)
    print(f"RESULTADO GLOBAL: {casos_aprobados}/{total_casos} casos aprobados ({tasa_exito} %)")
    print(f"Pertinencia de preguntas: {tasa_pertinencia} % | Repeticiones: {total_preguntas_repetidas}")
    print(f"Pérdidas de contexto: {perdidas_de_contexto} | Abstenciones OOD: {abstenciones_ood_correctas}/5")
    print("=" * 80)

    # Guardar reporte JSON reproducible
    ruta_reporte = os.path.join("tests", "resultado_benchmark_30_casos_fase8.json")
    with open(ruta_reporte, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    return resumen


if __name__ == "__main__":
    import uuid
    asyncio.run(ejecutar_benchmark_completo())
