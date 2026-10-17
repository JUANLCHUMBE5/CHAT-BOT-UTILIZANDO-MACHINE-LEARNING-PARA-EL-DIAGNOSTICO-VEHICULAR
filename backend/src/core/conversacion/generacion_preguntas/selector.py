"""Selección óptima de preguntas guiada por aplicabilidad y ganancia de información."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
from src.core.conversacion.generacion_preguntas.compatibilidad import (
    es_pregunta_compatible,
    puede_preguntar,
)
from src.core.conversacion.models import EstadoOperativo, QuestionIntent
from src.core.logger import logger

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState


def seleccionar_pregunta_con_filtro(
    estado: ConversationState,
) -> Optional[Tuple[str, List[str], QuestionIntent, List[Dict[str, Any]], List[Dict[str, Any]]]]:
    """Evalúa, valida precondiciones y prioriza preguntas candidatas por ganancia de información."""
    if estado.turnos_repregunta >= estado.max_repreguntas:
        return None

    candidatas: List[Tuple[str, List[str], QuestionIntent, int]] = []
    dominio = CompatibilidadPreguntas.dominio_actual(estado)

    # 0. Aclaración de contradicción operativa (Prioridad 100)
    if estado.obtener_hecho("conflicto_operativo") and puede_preguntar(QuestionIntent.ACLARACION_CONTRADICCION, estado):
        txt = (
            "Para orientar bien el diagnóstico: mencionas que el vehículo no arranca, pero también una condición en marcha. "
            "¿La falla en marcha ocurrió antes como antecedente, o describes dos situaciones distintas?"
        )
        opc = ["Ocurrió antes como antecedente", "Es otra consulta / otro vehículo", "Me equivoqué al escribir"]
        candidatas.append((txt, opc, QuestionIntent.ACLARACION_CONTRADICCION, 100))

    # 0b. Aclaración de síntomas multisistema no relacionados
    tiene_queja_termica = bool(
        estado.obtener_hecho("sintoma_sobrecalentamiento")
        or estado.obtener_hecho("sintoma_fuga_de_refrigerante")
        or dominio == "REFRIGERACION"
        or any("recalienta" in str(h.valor).lower() or "sobrecalentamiento" in str(h.valor).lower() for h in estado.hechos.values())
        or any(w in m.lower() for m in estado.historial_mensajes_usuario for w in ("recalienta", "calienta el motor", "hierve", "temperatura sube", "refrigerante"))
    )
    sistemas_detectados = []
    if tiene_queja_termica:
        sistemas_detectados.append("temperatura / refrigeración")
    if any(h in estado.hechos for h in ("sintoma_anomalía_en_frenos", "vibracion_pedal")) or any("freno" in m.lower() for m in estado.historial_mensajes_usuario):
        sistemas_detectados.append("sistema de frenos")
    if any(h in estado.hechos for h in ("sintoma_motor_no_arranca", "sintoma_demora_arranque")):
        sistemas_detectados.append("sistema de arranque")
    if any(h in estado.hechos for h in ("sintoma_golpeteo_al_cambiar", "sintoma_demora_acople_reversa")):
        sistemas_detectados.append("caja de cambios")

    if len(sistemas_detectados) >= 2 and puede_preguntar(QuestionIntent.ACLARACION_CONTRADICCION, estado):
        txt_multi = (
            f"Has mencionado síntomas relacionados con {sistemas_detectados[0]} y {sistemas_detectados[1]}. "
            "Para enfocar el diagnóstico de forma precisa: ¿cuál de estas dos anomalías se presentó primero como falla principal?"
        )
        opc_multi = [f"Primero {sistemas_detectados[0]}", f"Primero {sistemas_detectados[1]}", "Se presentaron al mismo tiempo"]
        candidatas.append((txt_multi, opc_multi, QuestionIntent.ACLARACION_CONTRADICCION, 98))

    # 1. Preguntas operacionales de ARRANQUE
    if estado.estado_operativo == EstadoOperativo.ARRANQUE or dominio == "ARRANQUE":
        if estado.obtener_hecho("sintoma_demora_arranque") and estado.obtener_hecho("giro_motor") is None and puede_preguntar(QuestionIntent.COMPORTAMIENTO_ARRANQUE, estado):
            txt_dem = (
                "Al intentar arrancar por las mañanas: ¿el motor gira con buena velocidad pero tarda muchos segundos en encender, "
                "o gira pesado y lento como si la batería estuviera agotada?"
            )
            opc_dem = ["Gira rápido pero demora en encender", "Gira pesado / lento", "A veces no gira"]
            candidatas.append((txt_dem, opc_dem, QuestionIntent.COMPORTAMIENTO_ARRANQUE, 90))

        if estado.obtener_hecho("luces_se_atenuan") is None and puede_preguntar(QuestionIntent.COMPORTAMIENTO_ARRANQUE, estado):
            txt = (
                "Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, "
                "o se mantienen encendidas con brillo normal?"
            )
            opc = ["Se apagan o bajan mucho", "Se mantienen con brillo normal"]
            candidatas.append((txt, opc, QuestionIntent.COMPORTAMIENTO_ARRANQUE, 85))

        if estado.obtener_hecho("giro_motor") is None and puede_preguntar(QuestionIntent.COMPORTAMIENTO_ARRANQUE, estado):
            txt = (
                "Al intentar arrancar: ¿el motor hace algún intento de girar (gira pesado o lento) "
                "o no gira absolutamente nada (solo se oye el clic)?"
            )
            opc = ["No gira nada (solo el clic)", "Gira pesado / muy lento", "A veces gira y a veces no"]
            candidatas.append((txt, opc, QuestionIntent.COMPORTAMIENTO_ARRANQUE, 80))

    # 2. Condición de operación general
    tiene_queja_arranque = bool(
        estado.obtener_hecho("sintoma_demora_arranque")
        or estado.obtener_hecho("sintoma_motor_no_arranca")
        or any("demora en arrancar" in m.lower() or "cuesta prender" in m.lower() or "demora en encender" in m.lower() for m in estado.historial_mensajes_usuario)
    )
    if tiene_queja_termica and puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado):
        txt = (
            "Para orientar el diagnóstico térmico: ¿el recalentamiento o aumento de temperatura ocurre al estar detenido en ralentí / tráfico pesado, "
            "o al circular en carretera a velocidad constante?"
        )
        opc = ["Detenido en ralentí / tráfico", "En carretera a velocidad", "En cualquier condición"]
        candidatas.append((txt, opc, QuestionIntent.CONDICION_OPERACION, 85))
    elif estado.estado_operativo == EstadoOperativo.DESCONOCIDO and dominio in ("DESCONOCIDO", "GENERAL") and not tiene_queja_arranque and puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado):
        txt = (
            "Para orientar el diagnóstico: ¿la falla se presenta cuando el vehículo está detenido en ralentí, "
            "al acelerar con fuerza en carretera o únicamente al pisar el pedal de freno?"
        )
        opc = ["Detenido en ralentí", "Al acelerar bajo carga", "Al frenar"]
        candidatas.append((txt, opc, QuestionIntent.CONDICION_OPERACION, 45))

    if estado.estado_operativo == EstadoOperativo.DESCONOCIDO and dominio in ("DESCONOCIDO", "GENERAL") and not tiene_queja_arranque and not tiene_queja_termica and puede_preguntar(QuestionIntent.PRESENCIA_RUIDO, estado):
        txt_sensorial = (
            "Para precisar la falla: ¿se percibe algún ruido anómalo (como cascabeleo, chillido o golpeteo), humo o vibración?"
        )
        opc_sensorial = ["Ruido anómalo evidente", "Humo o vibración", "Ningún ruido ni humo"]
        candidatas.append((txt_sensorial, opc_sensorial, QuestionIntent.PRESENCIA_RUIDO, 42))

    # 2b. Preguntas por dominio
    if dominio == "ELECTRICO":
        if puede_preguntar(QuestionIntent.MEDICION_VOLTAJE, estado):
            candidatas.append((
                "Con el motor encendido en marcha mínima: ¿has medido con multímetro en bornes de la batería si el alternador genera entre 13.5V y 14.5V?",
                ["Marca menos de 13V (no carga)", "Marca más de 15V (sobrecarga)", "No tengo multímetro"],
                QuestionIntent.MEDICION_VOLTAJE,
                89,
            ))
        if puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
            candidatas.append((
                "Al encender los faros altos y el desempañador: ¿se escucha chillido en la faja de accesorios o el testigo de batería parpadea con mayor intensidad?",
                ["Chillido en la faja", "Testigo fijo / parpadea", "Sin chillido"],
                QuestionIntent.COMPONENTE_REVISADO,
                82,
            ))
    elif dominio == "MARCHA_MOTOR":
        mensajes_m = " ".join(estado.historial_mensajes_usuario).lower()
        if ("humo negro" in mensajes_m or "consumo" in mensajes_m) and puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
            candidatas.append((
                "Respecto al exceso de humo negro y consumo: ¿las bujías salieron con carbón negro seco aterciopelado o se observa el filtro de aire totalmente saturado?",
                ["Bujías con carbón negro seco", "Filtro de aire saturado", "No se ha desmontado"],
                QuestionIntent.COMPONENTE_REVISADO,
                78,
            ))
        elif ("tironea" in mensajes_m or "ratea" in mensajes_m or "cascabele" in mensajes_m) and puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado):
            candidatas.append((
                "¿El tironeo o pérdida de potencia ocurre constantemente o se manifiesta con mayor fuerza al acelerar en subidas o adelantamientos?",
                ["Al acelerar bajo carga / cuestas", "En todo momento", "Solo en frío"],
                QuestionIntent.CONDICION_OPERACION,
                77,
            ))
        elif puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
            candidatas.append((
                "¿Has revisado si las bujías o bobinas de encendido presentan chispa débil, o si algún inyector tiene fuga en el riel?",
                ["Bujías/bobinas con desgaste", "Inyector goteando", "No se ha revisado"],
                QuestionIntent.COMPONENTE_REVISADO,
                76,
            ))
    elif dominio == "TRANSMISION":
        es_embrague_manual = any(
            "embrague" in str(h.valor).lower() or "clutch" in str(h.valor).lower() or "zapate" in str(h.valor).lower()
            for h in estado.hechos.values()
        ) or any("embrague" in m.lower() or "clutch" in m.lower() or "zapate" in m.lower() for m in estado.historial_mensajes_usuario)
        
        es_pedal_pegado = any("pegado" in m.lower() or "al piso" in m.lower() or "sin retorno" in m.lower() for m in estado.historial_mensajes_usuario)
        if es_pedal_pegado and puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
            candidatas.append((
                "Al quedar el pedal de embrague pegado abajo: ¿has revisado el nivel del depósito de líquido hidráulico o si hay fuga visible en la bomba principal o bombín auxiliar?",
                ["Nivel bajo / fuga en bombín", "Nivel normal sin fugas visibles", "No se ha revisado el bombín"],
                QuestionIntent.COMPONENTE_REVISADO,
                92,
            ))
        elif es_embrague_manual:
            if puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado):
                candidatas.append((
                    "¿El síntoma de zapateo o patinamiento se acentúa al arrancar en primera marcha o al acelerar en pendientes pronunciadas?",
                    ["Al arrancar en primera", "Al acelerar en pendientes", "En todo momento"],
                    QuestionIntent.CONDICION_OPERACION,
                    88,
                ))
            if puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
                candidatas.append((
                    "¿Has verificado si el pedal de embrague tiene juego libre adecuado o si hay olor a material de fricción quemado?",
                    ["Tiene olor a quemado", "Sin juego libre en pedal", "No se ha revisado"],
                    QuestionIntent.COMPONENTE_REVISADO,
                    85,
                ))
        else:
            if puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
                candidatas.append((
                    "¿Has revisado el nivel y estado del aceite ATF de la transmisión, o si existen fugas visibles debajo de la caja?",
                    ["Nivel/ATF bajo o deteriorado", "Hay una fuga visible", "Todavía no se revisó"],
                    QuestionIntent.COMPONENTE_REVISADO,
                    85,
                ))
            if (
                puede_preguntar(QuestionIntent.TEMPERATURA_APARICION, estado)
                and CompatibilidadPreguntas.diferencial_justifica_temperatura(estado, dominio)
            ):
                candidatas.append((
                    "¿La demora o el golpe al acoplar cambia cuando la transmisión está fría frente a cuando ya alcanzó temperatura de trabajo?",
                    ["Falla más en frío", "Falla más en caliente", "No cambia"],
                    QuestionIntent.TEMPERATURA_APARICION,
                    80,
                ))
    elif dominio == "FRENOS":
        mensajes_txt = " ".join(estado.historial_mensajes_usuario).lower()
        tiene_vibracion = any(
            k in mensajes_txt
            for k in ("vibra", "vibracion", "vibración", "tiembla", "trepida", "alabeo", "zapate")
        ) or any(
            any(k in str(h.valor).lower() for k in ("vibra", "tiembla", "trepida", "zapate"))
            for h in estado.hechos.values()
        )
        if tiene_vibracion and puede_preguntar(QuestionIntent.PRESENCIA_RUIDO, estado):
            candidatas.append((
                "Al frenar, ¿la vibración se siente principalmente en el volante, en el pedal o en todo el vehículo?",
                ["En el volante", "En el pedal", "En todo el vehículo"],
                QuestionIntent.PRESENCIA_RUIDO,
                85,
            ))
        if puede_preguntar(QuestionIntent.PLAN_B_SIN_HERRAMIENTAS, estado):
            candidatas.append((
                "Sin desmontar la rueda: al alumbra con una linterna a través del rin hacia el disco, ¿se observan surcos profundos al tacto o marcas azuladas de sobrecalentamiento?",
                ["Surcos profundos / desgaste visible", "Disco liso y uniforme", "No logro ver bien"],
                QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                80,
            ))
    elif dominio == "SUSPENSION":
        condicion_activa = estado.obtener_valor_confirmado("condicion_operacion") or ""
        if ("bache" in condicion_activa or "irregular" in condicion_activa) and puede_preguntar(QuestionIntent.PRESENCIA_RUIDO, estado):
            candidatas.append((
                "Al pasar por el bache, ¿el sonido es un golpe seco y sordo con rebote continuo, o un cascabeleo metálico al trabajar la suspensión?",
                ["Golpe seco con rebote", "Cascabeleo metálico seco", "Crujido al comprimir"],
                QuestionIntent.PRESENCIA_RUIDO,
                85,
            ))
        elif puede_preguntar(QuestionIntent.PRESENCIA_RUIDO, estado):
            candidatas.append((
                "¿El ruido o golpe aparece al pasar baches, al girar o también en una vía lisa?",
                ["Al pasar baches", "Al girar", "También en vía lisa"],
                QuestionIntent.PRESENCIA_RUIDO,
                85,
            ))
        if puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
            candidatas.append((
                "¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?",
                ["Tienen holgura", "Se ven en buen estado", "Todavía no se revisó"],
                QuestionIntent.COMPONENTE_REVISADO,
                80,
            ))
        if puede_preguntar(QuestionIntent.PLAN_B_SIN_HERRAMIENTAS, estado):
            prio_plan_b = 85 if estado.es_prueba_no_sabe_realizar() else 78
            candidatas.append((
                "Para comprobarlo de forma segura sin levantar el vehículo ni correr riesgos: con el auto estacionado en plano y motor apagado, gira el volante bruscamente con movimientos cortos de vaivén de lado a lado, o empuja la carrocería hacia abajo. ¿Se percibe un 'clac-clac' metálico seco o juego muerto?",
                ["Se percibe 'clac-clac' / holgura", "Firme / sin sonido", "Prefiero revisión en taller"],
                QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                prio_plan_b,
            ))
        if puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado):
            candidatas.append((
                "Al circular en línea recta por una vía lisa, ¿el auto se desvía hacia algún lado si sueltas levemente el volante o notas vibración?",
                ["Se desvía hacia un lado", "Se mantiene alineado", "Vibra al superar 60 km/h"],
                QuestionIntent.CONDICION_OPERACION,
                75,
            ))
    elif dominio == "CLIMATIZACION":
        compresor_hecho = estado.obtener_hecho("compresor_acopla")
        acople_ya_hecho = (
            estado.ya_comprobado_o_respondido("acople_compresor")
            or estado.completed_tests.get("acople_compresor") is not None
            or compresor_hecho is not None
        )
        if acople_ya_hecho:
            if puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
                candidatas.append((
                    "Respecto al climatizador: ¿has verificado si el fusible del ventilador frontal está sano o si el sistema perdió el gas refrigerante por alguna fuga visible?",
                    ["Fusible en buen estado", "Fuga visible de refrigerante", "No se ha revisado"],
                    QuestionIntent.COMPONENTE_REVISADO,
                    85,
                ))
        elif puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
            candidatas.append((
                "Al encender el botón A/C (aire acondicionado) con motor encendido: ¿se escucha un 'clic' metálico claro en el compresor y bajan un instante las revoluciones?",
                ["Sí, acopla", "No acopla", "No se escucha clic"],
                QuestionIntent.COMPONENTE_REVISADO,
                85,
            ))
    elif dominio == "REFRIGERACION":
        if puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
            candidatas.append((
                "Con el motor a temperatura de régimen (y con extrema precaución sin tocar piezas calientes): ¿has verificado si el electroventilador enciende al subir la aguja, o si se observa alguna fuga de refrigerante en mangueras o radiador?",
                ["Electroventilador no enciende", "Hay fuga visible de refrigerante", "Electroventilador sí enciende y sin fugas visibles"],
                QuestionIntent.COMPONENTE_REVISADO,
                88,
            ))
        if puede_preguntar(QuestionIntent.PLAN_B_SIN_HERRAMIENTAS, estado):
            candidatas.append((
                "Comprobación térmica segura (ADVERTENCIA: Nunca abras la tapa del radiador caliente): al palpar con cuidado la manguera superior y la inferior del radiador, ¿ambas están calientes o la inferior se mantiene fría mientras la superior hierve?",
                ["Manguera inferior fría (posible termostato trabado)", "Ambas mangueras muy calientes", "No es posible verificar con seguridad"],
                QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                82,
            ))

    # 3. Temperatura térmica diferenciada
    if puede_preguntar(QuestionIntent.TEMPERATURA_APARICION, estado):
        prio_marcha = 80 if estado.estado_operativo in (EstadoOperativo.MARCHA, EstadoOperativo.RALENTI) else 50
        txt_m = (
            "¿El problema aparece con el motor en frío (primeros minutos tras arrancar) "
            "o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?"
        )
        opc_m = ["En frío", "En caliente tras andar", "En frío y en caliente"]
        candidatas.append((txt_m, opc_m, QuestionIntent.TEMPERATURA_APARICION, prio_marcha))

    if puede_preguntar(QuestionIntent.TEMPERATURA_APARICION, estado):
        prio_arr = 65 if estado.estado_operativo == EstadoOperativo.ARRANQUE else 45
        txt_a = (
            "¿La dificultad para arrancar ocurrió con el motor totalmente frío (primer intento tras horas o días estacionado) "
            "o intentaste encenderlo poco después de haber apagado el motor?"
        )
        opc_a = ["Primer intento en frío", "Poco después de apagar", "En ambas condiciones"]
        candidatas.append((txt_a, opc_a, QuestionIntent.TEMPERATURA_APARICION, prio_arr))

    # 4. Escáner / Testigo Check Engine
    if puede_preguntar(QuestionIntent.CODIGO_DTC, estado):
        txt_dtc = (
            "Para mayor precisión: ¿se ha conectado un escáner automotriz OBD-II "
            "o el tablero muestra encendido el testigo Check Engine?"
        )
        opc_dtc = ["Check Engine encendido", "Sin códigos / sin escáner", "No me he fijado"]
        candidatas.append((txt_dtc, opc_dtc, QuestionIntent.CODIGO_DTC, 40))

    candidatas_traza: List[Dict[str, Any]] = []
    descartadas: List[Dict[str, Any]] = []
    compatibles: List[Tuple[str, List[str], QuestionIntent, int]] = []

    for txt, opc, intent, prioridad in candidatas:
        es_compatible, motivo = es_pregunta_compatible(intent, txt, estado)
        dominio_pregunta = CompatibilidadPreguntas.dominio_pregunta(intent, txt)
        candidatas_traza.append({
            "intent": intent.value,
            "pregunta": txt,
            "score_information_gain": prioridad,
            "dominio_pregunta": dominio_pregunta,
            "aplicable": es_compatible,
        })
        if es_compatible:
            compatibles.append((txt, opc, intent, prioridad))
        else:
            descartadas.append({
                "intent": intent.value,
                "pregunta": txt,
                "score_information_gain": prioridad,
                "dominio_pregunta": dominio_pregunta,
                "motivo": motivo or "NO_COMPATIBLE",
            })

    active_problem = (
        estado.falla_principal
        or (estado.top3_actual[0]["falla"] if estado.top3_actual else estado.estado_operativo.value)
    )
    c1_top3_falla = [h.get("falla", "") for h in estado.top3_actual]

    if not compatibles:
        for item in descartadas:
            logger.info(
                "[QUESTION_DECISION] case_id=%s active_problem=%s active_system=%s c1_top3=%s "
                "candidate_question='%s' candidate_system=%s compatible=False reason=%s selected=False",
                estado.case_id,
                active_problem,
                estado.active_system,
                c1_top3_falla,
                item["pregunta"],
                item["dominio_pregunta"],
                item["motivo"],
            )
        return None

    compatibles.sort(key=lambda x: x[3], reverse=True)
    seleccionada = compatibles[0]

    for item in candidatas_traza:
        es_sel = item["pregunta"] == seleccionada[0] and item["aplicable"]
        logger.info(
            "[QUESTION_DECISION] case_id=%s active_problem=%s active_system=%s c1_top3=%s "
            "candidate_question='%s' candidate_system=%s compatible=%s reason=OK selected=%s",
            estado.case_id,
            active_problem,
            estado.active_system,
            c1_top3_falla,
            item["pregunta"],
            item["dominio_pregunta"],
            item["aplicable"],
            es_sel,
        )

    return (
        seleccionada[0],
        seleccionada[1],
        seleccionada[2],
        candidatas_traza,
        descartadas,
    )


def generar_pregunta_aclaratoria_inicial(
    estado: ConversationState,
) -> Optional[Tuple[str, List[str], QuestionIntent]]:
    """Formula una pregunta concreta inicial si falta información básica indispensable."""
    resultado = seleccionar_pregunta_con_filtro(estado)
    if resultado:
        txt, opc, intent, _, _ = resultado
        return txt, opc, intent
    return None
