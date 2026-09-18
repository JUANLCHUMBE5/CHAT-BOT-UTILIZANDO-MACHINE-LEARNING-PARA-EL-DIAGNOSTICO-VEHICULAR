"""Generador de preguntas discriminantes Top-3, comprobación already_known y regla anti-loop (Adenda 9.1)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)
from src.core.diagnostico.auto_interrogador import MAPA_DESCRIPCION_OPCION
from src.core.logger import logger


class GeneradorPreguntas:
    """Gestiona la formulación de preguntas discriminantes y garantiza el escape de bucles."""

    @staticmethod
    def already_known(intent: QuestionIntent, estado: ConversationState) -> bool:
        """Determina si la información requerida ya está confirmada o abordada en el estado conversacional."""
        if intent in (
            QuestionIntent.TEMPERATURA_APARICION,
            QuestionIntent.TEMPERATURA_MOTOR_EN_MARCHA,
            QuestionIntent.TEMPERATURA_AMBIENTAL_ARRANQUE,
        ):
            return estado.obtener_hecho("temperatura") is not None or estado.obtener_hecho("temperatura_arranque") is not None

        if intent == QuestionIntent.CONDICION_OPERACION:
            if estado.estado_operativo in (
                EstadoOperativo.ARRANQUE,
                EstadoOperativo.RALENTI,
                EstadoOperativo.MARCHA,
                EstadoOperativo.FRENADO,
            ):
                return True
            return estado.obtener_hecho("condicion_operacion") is not None

        if intent in (QuestionIntent.COMPORTAMIENTO_ARRANQUE, QuestionIntent.CAIDA_TENSION_ARRANQUE):
            return bool(
                estado.obtener_hecho("giro_motor") is not None
                and estado.obtener_hecho("luces_se_atenuan") is not None
            )

        if intent == QuestionIntent.ACLARACION_CONTRADICCION:
            return estado.obtener_hecho("conflicto_operativo") is None or estado.ya_preguntado(QuestionIntent.ACLARACION_CONTRADICCION)

        if intent == QuestionIntent.CODIGO_DTC:
            return (
                estado.dtc_status == DtcStatus.DTC_OBSERVADO
                or any(h.categoria == "dtc" for h in estado.hechos.values())
            )

        if intent == QuestionIntent.COMPONENTE_REVISADO:
            return any(
                h.categoria in ("componente_descartado", "antecedente", "inspeccion")
                and h.estado == FactState.CONFIRMADO
                for h in estado.hechos.values()
            ) or bool(estado.completed_tests) or estado.ya_comprobado_o_respondido("acople_compresor")

        if intent == QuestionIntent.PLAN_B_SIN_HERRAMIENTAS:
            return estado.ya_preguntado(QuestionIntent.PLAN_B_SIN_HERRAMIENTAS)

        if intent == QuestionIntent.DATOS_VEHICULO:
            return bool(estado.marca and estado.modelo)

        return False

    @classmethod
    def puede_preguntar(cls, intent: QuestionIntent, estado: ConversationState) -> bool:
        """Verifica si es válido formular una pregunta sin caer en repetición ni violar el límite."""
        # 1. Límite máximo de repreguntas consecutivas (MAX_FOLLOW_UP_QUESTIONS = 3)
        if estado.turnos_repregunta >= estado.max_repreguntas:
            return False

        # 2. Dato ya conocido o respondido previamente
        if cls.already_known(intent, estado):
            return False

        # 3. Detección semántica de preguntas repetidas: máximo 1 vez si hubo respuesta
        veces = estado.veces_preguntado(intent)
        if veces >= 2:
            return False
        if veces == 1 and len(estado.respuestas_obtenidas) >= 1:
            return False

        return True

    @classmethod
    def es_pregunta_compatible(
        cls,
        intent: QuestionIntent,
        texto_pregunta: str,
        estado: ConversationState,
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida que la pregunta candidata sea compatible con el estado operativo y hechos conocidos.
        Retorna (True, None) si es compatible, o (False, motivo) si debe descartarse.
        Motivos:
          - INCOMPATIBLE_ESTADO_OPERATIVO
          - HECHO_YA_CONOCIDO
          - INTENT_YA_RESUELTO
          - PREGUNTA_REPETIDA
        """
        texto_l = texto_pregunta.lower()

        # 0. Aclaración de contradicción tiene reglas propias de resolución
        if intent == QuestionIntent.ACLARACION_CONTRADICCION:
            if estado.veces_preguntado(intent) >= 1 and len(estado.respuestas_obtenidas) >= 1:
                return False, "PREGUNTA_REPETIDA"
            return True, None

        # 1. PREGUNTA_REPETIDA
        if any(p.get("texto", "").strip().lower() == texto_pregunta.strip().lower() for p in estado.preguntas_realizadas):
            return False, "PREGUNTA_REPETIDA"
        if intent != QuestionIntent.COMPONENTE_REVISADO:
            veces = estado.veces_preguntado(intent)
            if veces >= 2:
                return False, "PREGUNTA_REPETIDA"
            if veces == 1 and len(estado.respuestas_obtenidas) >= 1:
                return False, "PREGUNTA_REPETIDA"
        else:
            veces = estado.veces_preguntado(intent)
            if veces >= 3:
                return False, "PREGUNTA_REPETIDA"

        # 2. INTENT_YA_RESUELTO
        if intent == QuestionIntent.CONDICION_OPERACION and estado.estado_operativo != EstadoOperativo.DESCONOCIDO:
            return False, "INTENT_YA_RESUELTO"
        if intent == QuestionIntent.TEMPERATURA_APARICION and estado.obtener_hecho("temperatura") is not None:
            return False, "INTENT_YA_RESUELTO"
        if intent == QuestionIntent.CODIGO_DTC and (
            estado.dtc_status == DtcStatus.DTC_OBSERVADO or any(h.categoria == "dtc" for h in estado.hechos.values())
        ):
            return False, "INTENT_YA_RESUELTO"

        # 3. Aplicabilidad semántica por dominio. La ganancia de información
        # solo se evalúa después de superar esta compuerta.
        compatible_dominio, motivo_dominio = CompatibilidadPreguntas.validar(
            intent, texto_pregunta, estado
        )
        if not compatible_dominio:
            return False, motivo_dominio

        # 4. HECHO_YA_CONOCIDO
        if ("clic" in texto_l or "metralleta" in texto_l or "chasquido" in texto_l) and estado.obtener_hecho("ruido_arranque") is not None:
            return False, "HECHO_YA_CONOCIDO"
        if "luces" in texto_l and estado.obtener_hecho("luces_se_atenuan") is not None:
            return False, "HECHO_YA_CONOCIDO"
        if "intento de girar" in texto_l and estado.obtener_hecho("giro_motor") is not None:
            return False, "HECHO_YA_CONOCIDO"
        if ("compresor" in texto_l or "clic" in texto_l or "acopla" in texto_l) and (
            estado.ya_comprobado_o_respondido("acople_compresor")
            or estado.completed_tests.get("acople_compresor") is not None
            or estado.obtener_hecho("compresor_acopla") is not None
        ):
            return False, "HECHO_YA_CONOCIDO"
        if "electroventilador" in texto_l and (
            estado.ya_comprobado_o_respondido("electroventilador_condensador")
            or estado.completed_tests.get("electroventilador_condensador") is not None
        ):
            return False, "HECHO_YA_CONOCIDO"

        # 5. INCOMPATIBLE_ESTADO_OPERATIVO
        if estado.estado_operativo == EstadoOperativo.ARRANQUE:
            if re.search(
                r"\b(ralent[ií]|carretera|freno|frenar|acelerar\s+con\s+fuerza|"
                r"a\s+alta\s+velocidad|en\s+marcha|al\s+acelerar\s+bajo\s+carga)\b",
                texto_l,
            ):
                return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

        elif estado.estado_operativo == EstadoOperativo.FRENADO:
            palabras_arranque = ("al arrancar", "primer arranque", "no arranca", "al girar la llave", "dar arranque")
            if any(w in texto_l for w in palabras_arranque):
                return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

        elif estado.estado_operativo == EstadoOperativo.MARCHA:
            palabras_arranque = ("al arrancar", "primer arranque", "no arranca", "al girar la llave", "dar arranque")
            if any(w in texto_l for w in palabras_arranque):
                return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

        elif estado.estado_operativo == EstadoOperativo.RALENTI:
            if "freno" in texto_l or "frenar" in texto_l:
                return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

        # 6. PRECONDICIONES LOGICAS DE PREGUNTA (Principio General de Presuposiciones)
        # Una pregunta que presupone alcanzar temperatura de régimen tras funcionar
        # requiere evidencia compatible con que el motor arrancó o funcionó previamente.
        if (
            "temperatura de trabajo normal" in texto_l
            or "después de que el motor alcanza" in texto_l
            or "en caliente tras andar" in texto_l
        ):
            if (
                estado.obtener_hecho("motor_arranca")
                and estado.obtener_hecho("motor_arranca").valor == "NO"
                and not estado.tiene_antecedente_motor_en_marcha()
            ):
                return False, "PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA"

        if intent == QuestionIntent.CONDICION_OPERACION:
            if (
                estado.obtener_hecho("motor_arranca")
                and estado.obtener_hecho("motor_arranca").valor == "NO"
                and not estado.tiene_antecedente_motor_en_marcha()
            ):
                return False, "PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA"

        # Regla de Tesis: Averías mecánicas puras sin control electrónico nunca sugieren escaneo DTC
        if intent == QuestionIntent.CODIGO_DTC:
            hechos_mecanicos_puros = (
                "desbalanceo", "desalineacion", "desalineación", "alabeo", "pastillas",
                "rotula", "rótula", "bieleta", "embrague patinando", "anomalía en frenos",
                "buje", "bujes", "trapecio", "amortiguador",
            )
            historial_completo = " ".join(estado.historial_mensajes_usuario).lower()
            hechos_str = " ".join(f"{h.campo} {h.valor}" for h in estado.hechos.values()).lower()
            if any(m in historial_completo or m in hechos_str for m in hechos_mecanicos_puros):
                if not any(e in historial_completo or e in hechos_str for e in ("check", "testigo", "abs", "esc", "esp", "sensor", "dtc")):
                    return False, "INCOMPATIBLE_AVERIA_MECANICA_PURA"

        return True, None

    @classmethod
    def generar_pregunta_discriminante_top3(
        cls,
        top_candidatos: List[str],
        estado: ConversationState,
    ) -> Optional[Tuple[str, List[str], List[str], QuestionIntent]]:
        """
        Genera una pregunta dirigida a diferenciar el Top-3 de hipótesis diagnósticas.
        Retorna:
          (texto_pregunta, lista_opciones_formateadas, lista_hipotesis_canonica, QuestionIntent)
        """
        if not cls.puede_preguntar(QuestionIntent.DISCRIMINACION_TOP3, estado):
            return None

        candidatos = [c for c in top_candidatos[:3] if c]
        if len(candidatos) < 2:
            return None

        opciones_texto = []
        hipotesis_validas = []
        for c in candidatos:
            desc = MAPA_DESCRIPCION_OPCION.get(c)
            if not desc:
                desc = f"La falla coincide con: {c}"
            opciones_texto.append(desc)
            hipotesis_validas.append(c)

        iconos = ["1️⃣", "2️⃣", "3️⃣"]
        lineas_opciones = [
            f"{iconos[i]} {opciones_texto[i]}" for i in range(len(opciones_texto))
        ]

        texto = (
            "Para confirmar la causa exacta entre las posibilidades principales, "
            "¿cuál de las siguientes situaciones describe mejor el comportamiento de tu vehículo?\n\n"
            + "\n".join(lineas_opciones)
            + "\n\nResponde indicando el número (1, 2"
            + (", o 3" if len(opciones_texto) == 3 else "")
            + ")."
        )

        return texto, opciones_texto, hipotesis_validas, QuestionIntent.DISCRIMINACION_TOP3

    @classmethod
    def seleccionar_pregunta_con_filtro(
        cls,
        estado: ConversationState,
    ) -> Optional[Tuple[str, List[str], QuestionIntent, List[Dict[str, Any]], List[Dict[str, Any]]]]:
        """
        Evalúa, valida precondiciones y prioriza preguntas candidatas por ganancia de información.
        Retorna:
          (texto_pregunta, opciones, intent, lista_candidatas, lista_descartadas)
        """
        if estado.turnos_repregunta >= estado.max_repreguntas:
            return None

        # Candidatas: tupla de (texto, opciones, intent, prioridad_base)
        candidatas: List[Tuple[str, List[str], QuestionIntent, int]] = []

        # 0. Aclaración de contradicción operativa (Prioridad 100)
        if estado.obtener_hecho("conflicto_operativo") and cls.puede_preguntar(QuestionIntent.ACLARACION_CONTRADICCION, estado):
            txt = (
                "Para orientar bien el diagnóstico: mencionas que el vehículo no arranca, pero también una condición en marcha. "
                "¿La falla en marcha ocurrió antes como antecedente, o describes dos situaciones distintas?"
            )
            opc = ["Ocurrió antes como antecedente", "Es otra consulta / otro vehículo", "Me equivoqué al escribir"]
            candidatas.append((txt, opc, QuestionIntent.ACLARACION_CONTRADICCION, 100))

        # 1. Preguntas operacionales de ARRANQUE
        if estado.estado_operativo == EstadoOperativo.ARRANQUE:
            if estado.obtener_hecho("sintoma_demora_arranque") and estado.obtener_hecho("giro_motor") is None and cls.puede_preguntar(QuestionIntent.COMPORTAMIENTO_ARRANQUE, estado):
                txt_dem = (
                    "Al intentar arrancar por las mañanas: ¿el motor gira con buena velocidad pero tarda muchos segundos en encender, "
                    "o gira pesado y lento como si la batería estuviera agotada?"
                )
                opc_dem = ["Gira rápido pero demora en encender", "Gira pesado / lento", "A veces no gira"]
                candidatas.append((txt_dem, opc_dem, QuestionIntent.COMPORTAMIENTO_ARRANQUE, 90))

            if estado.obtener_hecho("luces_se_atenuan") is None and cls.puede_preguntar(QuestionIntent.COMPORTAMIENTO_ARRANQUE, estado):
                txt = (
                    "Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, "
                    "o se mantienen encendidas con brillo normal?"
                )
                opc = ["Se apagan o bajan mucho", "Se mantienen con brillo normal"]
                candidatas.append((txt, opc, QuestionIntent.COMPORTAMIENTO_ARRANQUE, 85))

            if estado.obtener_hecho("giro_motor") is None and cls.puede_preguntar(QuestionIntent.COMPORTAMIENTO_ARRANQUE, estado):
                txt = (
                    "Al intentar arrancar: ¿el motor hace algún intento de girar (gira pesado o lento) "
                    "o no gira absolutamente nada (solo se oye el clic)?"
                )
                opc = ["No gira nada (solo el clic)", "Gira pesado / muy lento", "A veces gira y a veces no"]
                candidatas.append((txt, opc, QuestionIntent.COMPORTAMIENTO_ARRANQUE, 80))

        # 2. Condición de operación general (solo si estado_operativo es DESCONOCIDO y NO hay queja de arranque)
        tiene_queja_arranque = bool(
            estado.obtener_hecho("sintoma_demora_arranque")
            or estado.obtener_hecho("sintoma_motor_no_arranca")
            or any("demora en arrancar" in m.lower() or "cuesta prender" in m.lower() or "demora en encender" in m.lower() for m in estado.historial_mensajes_usuario)
        )
        if estado.estado_operativo == EstadoOperativo.DESCONOCIDO and not tiene_queja_arranque and cls.puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado):
            txt = (
                "Para orientar el diagnóstico: ¿la falla se presenta cuando el vehículo está detenido en ralentí, "
                "al acelerar con fuerza en carretera o únicamente al pisar el pedal de freno?"
            )
            opc = ["Detenido en ralentí", "Al acelerar bajo carga", "Al frenar"]
            candidatas.append((txt, opc, QuestionIntent.CONDICION_OPERACION, 75))

        # 2b. Preguntas propias del dominio detectado.
        dominio = CompatibilidadPreguntas.dominio_actual(estado)
        if dominio == "TRANSMISION":
            if cls.puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
                candidatas.append((
                    "¿Has revisado el nivel y estado del aceite ATF de la transmisión, o si existen fugas visibles debajo de la caja?",
                    ["Nivel/ATF bajo o deteriorado", "Hay una fuga visible", "Todavía no se revisó"],
                    QuestionIntent.COMPONENTE_REVISADO,
                    85,
                ))
            if (
                cls.puede_preguntar(QuestionIntent.TEMPERATURA_APARICION, estado)
                and CompatibilidadPreguntas.diferencial_justifica_temperatura(estado, dominio)
            ):
                candidatas.append((
                    "¿La demora o el golpe al acoplar cambia cuando la transmisión está fría frente a cuando ya alcanzó temperatura de trabajo?",
                    ["Falla más en frío", "Falla más en caliente", "No cambia"],
                    QuestionIntent.TEMPERATURA_APARICION,
                    80,
                ))
        elif dominio == "FRENOS":
            if cls.puede_preguntar(QuestionIntent.PRESENCIA_RUIDO, estado):
                candidatas.append((
                    "Al frenar, ¿la vibración se siente principalmente en el volante, en el pedal o en todo el vehículo?",
                    ["En el volante", "En el pedal", "En todo el vehículo"],
                    QuestionIntent.PRESENCIA_RUIDO,
                    85,
                ))
            if cls.puede_preguntar(QuestionIntent.PLAN_B_SIN_HERRAMIENTAS, estado):
                candidatas.append((
                    "Sin desmontar la rueda: al alumbra con una linterna a través del rin hacia el disco, ¿se observan surcos profundos al tacto o marcas azuladas de sobrecalentamiento?",
                    ["Surcos profundos / desgaste visible", "Disco liso y uniforme", "No logro ver bien"],
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                    80,
                ))
        elif dominio == "SUSPENSION":
            condicion_activa = estado.obtener_valor_confirmado("condicion_operacion") or ""
            if ("bache" in condicion_activa or "irregular" in condicion_activa) and cls.puede_preguntar(QuestionIntent.PRESENCIA_RUIDO, estado):
                candidatas.append((
                    "Al pasar por el bache, ¿el sonido es un golpe seco y sordo con rebote continuo, o un cascabeleo metálico al trabajar la suspensión?",
                    ["Golpe seco con rebote", "Cascabeleo metálico seco", "Crujido al comprimir"],
                    QuestionIntent.PRESENCIA_RUIDO,
                    85,
                ))
            elif cls.puede_preguntar(QuestionIntent.PRESENCIA_RUIDO, estado):
                candidatas.append((
                    "¿El ruido o golpe aparece al pasar baches, al girar o también en una vía lisa?",
                    ["Al pasar baches", "Al girar", "También en vía lisa"],
                    QuestionIntent.PRESENCIA_RUIDO,
                    85,
                ))
            if cls.puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
                candidatas.append((
                    "¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?",
                    ["Tienen holgura", "Se ven en buen estado", "Todavía no se revisó"],
                    QuestionIntent.COMPONENTE_REVISADO,
                    80,
                ))
            if cls.puede_preguntar(QuestionIntent.PLAN_B_SIN_HERRAMIENTAS, estado):
                prio_plan_b = 85 if estado.es_prueba_no_sabe_realizar() else 78
                candidatas.append((
                    "Para comprobarlo de forma segura sin levantar el vehículo ni correr riesgos: con el auto estacionado en plano y motor apagado, gira el volante bruscamente con movimientos cortos de vaivén de lado a lado, o empuja la carrocería hacia abajo. ¿Se percibe un 'clac-clac' metálico seco o juego muerto?",
                    ["Se percibe 'clac-clac' / holgura", "Firme / sin sonido", "Prefiero revisión en taller"],
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                    prio_plan_b,
                ))
            if cls.puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado):
                candidatas.append((
                    "Al circular en línea recta por una vía lisa, ¿el auto se desvía hacia algún lado si sueltas levemente el volante o notas vibración?",
                    ["Se desvía hacia un lado", "Se mantiene alineado", "Vibra al superar 60 km/h"],
                    QuestionIntent.CONDICION_OPERACION,
                    75,
                ))
        elif dominio == "CLIMATIZACION":
            acople_ya_hecho = (
                estado.ya_comprobado_o_respondido("acople_compresor")
                or estado.completed_tests.get("acople_compresor") is not None
                or estado.obtener_hecho("compresor_acopla") is not None
            )
            if acople_ya_hecho:
                if not estado.ya_comprobado_o_respondido("electroventilador_condensador") and cls.puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
                    candidatas.append((
                        "Con el A/C encendido y compresor acoplado: ¿gira el electroventilador del condensador (adelante) y al tocar las tuberías en el vano motor se siente una bien fría y la otra caliente?",
                        ["Electroventilador gira y tubería fría", "Electroventilador no gira", "Ambas tuberías a temperatura ambiente (posible fuga de gas)"],
                        QuestionIntent.COMPONENTE_REVISADO,
                        85,
                    ))
            elif cls.puede_preguntar(QuestionIntent.COMPONENTE_REVISADO, estado):
                candidatas.append((
                    "Al encender el botón A/C (aire acondicionado) con motor encendido: ¿se escucha un 'clic' metálico claro en el compresor y bajan un instante las revoluciones?",
                    ["Sí, acopla", "No acopla", "No se escucha clic"],
                    QuestionIntent.COMPONENTE_REVISADO,
                    85,
                ))

        # 3. Temperatura térmica diferenciada (Principio de Presuposiciones)
        # 3a. Temperatura de motor en marcha (requiere evidencia de funcionamiento previo / régimen)
        if cls.puede_preguntar(QuestionIntent.TEMPERATURA_APARICION, estado):
            prio_marcha = 80 if estado.estado_operativo in (EstadoOperativo.MARCHA, EstadoOperativo.RALENTI) else 50
            txt_m = (
                "¿El problema aparece con el motor en frío (primeros minutos tras arrancar) "
                "o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?"
            )
            opc_m = ["En frío", "En caliente tras andar"]
            candidatas.append((txt_m, opc_m, QuestionIntent.TEMPERATURA_APARICION, prio_marcha))

        # 3b. Temperatura ambiental / reposo (pertinente para arranque sin asumir marcha)
        if cls.puede_preguntar(QuestionIntent.TEMPERATURA_APARICION, estado):
            prio_arr = 65 if estado.estado_operativo == EstadoOperativo.ARRANQUE else 45
            txt_a = (
                "¿La dificultad para arrancar ocurrió con el motor totalmente frío (primer intento tras horas o días estacionado) "
                "o intentaste encenderlo poco después de haber apagado el motor?"
            )
            opc_a = ["Primer intento en frío", "Poco después de apagar"]
            candidatas.append((txt_a, opc_a, QuestionIntent.TEMPERATURA_APARICION, prio_arr))

        # 4. Escáner / Testigo Check Engine (Prioridad complementaria 40)
        if cls.puede_preguntar(QuestionIntent.CODIGO_DTC, estado):
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
            es_compatible, motivo = cls.es_pregunta_compatible(intent, txt, estado)
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
        active_system = CompatibilidadPreguntas.dominio_actual(estado)
        top3_fallas = [h.get("falla") for h in estado.top3_actual] if estado.top3_actual else []
        txt_elegido = None
        opc_elegida = None
        intent_elegido = None

        if compatibles:
            # Priorización por Ganancia de Información (mayor score a menor)
            compatibles.sort(key=lambda x: x[3], reverse=True)
            txt_elegido, opc_elegida, intent_elegido, _ = compatibles[0]

        for item in candidatas_traza:
            p_txt = item["pregunta"]
            is_sel = (p_txt == txt_elegido)
            p_comp = item["aplicable"]
            p_dom = item["dominio_pregunta"]
            p_mot = next((d["motivo"] for d in descartadas if d["pregunta"] == p_txt), "OK")
            logger.info(
                "[QUESTION_DECISION] case_id=%s active_problem=%s active_system=%s c1_top3=%s "
                "candidate_question='%s' candidate_system=%s compatible=%s reason=%s selected=%s",
                estado.case_id,
                active_problem,
                active_system,
                top3_fallas,
                p_txt,
                p_dom,
                p_comp,
                p_mot,
                is_sel,
            )

        if compatibles:
            return txt_elegido, opc_elegida, intent_elegido, candidatas_traza, descartadas

        return None

    @classmethod
    def generar_pregunta_aclaratoria_inicial(
        cls,
        estado: ConversationState,
    ) -> Optional[Tuple[str, List[str], QuestionIntent]]:
        """Formula una pregunta concreta inicial si falta información básica indispensable."""
        resultado = cls.seleccionar_pregunta_con_filtro(estado)
        if resultado:
            txt, opc, intent, _, _ = resultado
            return txt, opc, intent
        return None

    @staticmethod
    def construir_salida_limite_repreguntas(
        top_candidatos: List[str],
        confianzas: List[float],
        estado: ConversationState,
    ) -> str:
        """Genera respuesta compacta cuando se alcanza el límite de 3 repreguntas (Fase 9.3)."""
        from src.core.conversacion.formateador_compacto import FormateadorCompacto

        hipotesis = []
        for i, c in enumerate(top_candidatos[:3]):
            conf = confianzas[i] if i < len(confianzas) else 0.10
            hipotesis.append({"falla": c, "probabilidad": conf})

        return FormateadorCompacto.formatear_respuesta_diagnostico(
            top_hipotesis=hipotesis,
            sintoma_original="",
        )
