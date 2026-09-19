"""Módulo de segmentación automática de casos y aislamiento de contexto (Fase 9.10).

Evalúa la compatibilidad operacional y de subsistemas entre mensajes dentro de la
misma conversación para prevenir la contaminación de hechos entre diagnósticos no relacionados.
"""

from __future__ import annotations

import re
import time
import unicodedata
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    EstadoOperativo,
    FactState,
    QuestionIntent,
    TurnTrace,
)
from src.core.version import ORCHESTRATOR_VERSION


class DecisionTransicion(str, Enum):
    MANTENER_CASO = "MANTENER_CASO"
    CAMBIO_DE_CASO = "CAMBIO_DE_CASO"
    ACLARACION_REQUERIDA = "ACLARACION_REQUERIDA"


class SubsistemaVehicular(str, Enum):
    ARRANQUE = "ARRANQUE"
    FRENOS = "FRENOS"
    MARCHA_MOTOR = "MARCHA_MOTOR"
    ELECTRICO = "ELECTRICO"
    TRANSMISION = "TRANSMISION"
    SUSPENSION = "SUSPENSION"
    CLIMATIZACION = "CLIMATIZACION"
    DESCONOCIDO = "DESCONOCIDO"


@dataclass
class TransicionCasoResultado:
    decision: DecisionTransicion
    motivo: str
    nuevo_case_id: Optional[str] = None
    estado_previo: EstadoOperativo = EstadoOperativo.DESCONOCIDO
    estado_detectado_mensaje: EstadoOperativo = EstadoOperativo.DESCONOCIDO
    pregunta_aclaracion: Optional[str] = None
    dominio_previo: SubsistemaVehicular = SubsistemaVehicular.DESCONOCIDO
    dominio_detectado_mensaje: SubsistemaVehicular = SubsistemaVehicular.DESCONOCIDO


class SegmentadorCasos:
    """Evalúa transiciones automáticas de caso diagnóstico basadas en compatibilidad operacional."""

    PREGUNTA_ACLARACION_CANONICA = (
        "¿Este problema corresponde al mismo vehículo/caso que estábamos revisando o es una falla diferente?"
    )

    @classmethod
    def detectar_subsistema_texto(cls, texto: str) -> SubsistemaVehicular:
        """Clasifica el subsistema automotriz primario al que alude el texto."""
        txt = (texto or "").lower()
        modificador_clima = bool(
            re.search(r"\bcon\s+(?:el\s+)?(?:a/c|aire\s+acondicionado|clima)\s+encendido\b", txt)
            and not re.search(r"\b(no\s+enfr[ií]a|sale\s+aire\s+caliente|compresor|falla|problema)\b", txt)
        )
        if re.search(
            r"\b(no\s+(?:quiso\s+|llega\s+a\s+)?(?:arranca|arrancar|prende|prender|enciende|encender)|"
            r"(?:demora|tarda|cuesta)\s+(?:(?:bastante|mucho|demasiado|varios\s+segundos|un\s+poco)\s+)?(?:en\s+)?(?:arrancar|prender|encender)|"
            r"le\s+cuesta\s+(?:arrancar|prender|encender)|"
            r"da\s+marcha\s+(?:bastante|un\s+rato|varios\s+segundos)|"
            r"dificultad\s+(?:de|para|al)\s+arranc(?:ar|e)|arranque\s+(?:largo|en\s+fr[ií]o|pesado)|"
            r"(?:por|en)\s+las\s+mañanas\s+(?:demora|tarda|le\s+cuesta)|"
            r"demora\s+por\s+las\s+mañanas|tarda\s+en\s+la\s+mañana|"
            r"clic\s+seco|chasquido|solenoide|motor\s+de\s+arranque|dar\s+arranque|llave)\b",
            txt,
        ):
            return SubsistemaVehicular.ARRANQUE
        freno_negado = bool(
            re.search(r"\b(al\s+frenar|frenando|cuando\s+freno)\s*,?\s*no\b", txt)
            or re.search(r"\bno\s+(?:frena|vibra|se\s+va|hace\s+ruido)\s+(?:al\s+frenar|cuando\s+freno)\b", txt)
            or re.search(r"\bal\s+frenar\s+no\s+vibra\b", txt)
        )
        tiene_freno_positivo = bool(
            re.search(r"\b(pedal\s+(?:se\s+hunde|esponjoso|duro)|frena\s+(?:disparejo|mal|largo)|chillido\s+al\s+frenar|pastillas?|disco(?:s)?|alabeo)\b", txt)
            and not freno_negado
        )
        if (re.search(r"\b(freno|frenar|frenando|frenos|pedal\s+de\s+freno)\b", txt) and not freno_negado) or tiene_freno_positivo:
            return SubsistemaVehicular.FRENOS
        if not modificador_clima and re.search(
            r"\b(aire\s+acondicionado|climatizaci[oó]n|compresor|no\s+enfr[ií]a|"
            r"sale\s+aire\s+(?:caliente|tibio|ambiente)|gas\s+r134a|refrigerante\s+r134a|r134a)\b",
            txt,
        ):
            return SubsistemaVehicular.CLIMATIZACION
        if re.search(
            r"\b(caja(?:\s+de\s+cambios|\s+autom[aá]tica)?|transmisi[oó]n|embrague|clutch|"
            r"palanca(?:\s+de\s+cambios)?|selector(?:\s+de\s+marchas)?|cambio(?:s)?|marcha(?:s)?|"
            r"junta(?:s)?\s+homocin[eé]tica(?:s)?|palier(?:es)?|semieje(?:s)?|"
            r"patina\s+el\s+embrague|patea\s+la\s+caja|"
            r"no\s+entra\s+(?:segunda|cambio)|reversa|retroceso)\b",
            txt,
        ) or (
            re.search(r"\b(acopla(?:r|miento)?|engancha(?:r)?)\b", txt)
            and not re.search(r"\b(compresor|clima|a/c|aire)\b", txt)
        ):
            return SubsistemaVehicular.TRANSMISION
        if re.search(r"\b(suspensi[oó]n|amortiguador(?:es)?|r[oó]tulas?|terminal(?:es)?|baches|pistas?\s+irregulares|rompemuelles|golpe\s+en\s+la\s+rueda)\b", txt):
            return SubsistemaVehicular.SUSPENSION
        if re.search(r"\b(alternador|bater[ií]a\s+descargada|voltaje|mult[ií]metro|luces\s+parpadean|fusible)\b", txt):
            return SubsistemaVehicular.ELECTRICO
        if re.search(
            r"\b(pierde\s+fuerza|perdia\s+fuerza|se\s+ahoga|no\s+jala|misfire|ratea|cabecea|tironea|acelerar|"
            r"en\s+carretera|a\s+\d+\s*km/h|se\s+calienta|sobrecalienta|hierve|refrigerante|humo\s+blanco|"
            r"buj[ií]as?|bobinas?|inyector(?:es)?|fuga\s+de\s+(?:l[ií]quido|agua|refrigerante)|"
            r"temperatura\s+(?:del\s+motor\s+)?(?:est[aá]\s+)?subiendo|sube\s+la\s+temperatura|"
            r"calentamiento|radiador)\b",
            txt,
        ):
            return SubsistemaVehicular.MARCHA_MOTOR
        return SubsistemaVehicular.DESCONOCIDO

    @classmethod
    def obtener_subsistema_estado(cls, estado: ConversationState) -> SubsistemaVehicular:
        """Determina el subsistema dominante del caso clínico activo en memoria."""
        # 1. Por hechos confirmados (excluye AUSENTE_NEGADO y NO_REVISADO)
        for campo, hecho in estado.hechos.items():
            if hecho.estado != FactState.CONFIRMADO:
                continue
            c_low = campo.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
            v_low = str(hecho.valor).lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
            if any(k in c_low or k in v_low for k in ("freno", "pastilla", "disco")):
                return SubsistemaVehicular.FRENOS
            if any(k in c_low or k in v_low for k in ("motor_arranca", "ruido_arranque", "evento", "arranque", "demora_arranque", "solenoide")):
                return SubsistemaVehicular.ARRANQUE
            if any(k in c_low or k in v_low for k in ("caja", "embrague", "transmision")):
                return SubsistemaVehicular.TRANSMISION
            if any(k in c_low or k in v_low for k in ("suspension", "amortiguador", "bache", "rotula")):
                return SubsistemaVehicular.SUSPENSION
            if any(k in c_low or k in v_low for k in ("alternador", "voltaje", "bateria")):
                return SubsistemaVehicular.ELECTRICO
            if any(k in c_low or k in v_low for k in ("climatizacion", "aire acondicionado", "r134a")):
                return SubsistemaVehicular.CLIMATIZACION
            if any(k in c_low or k in v_low for k in ("potencia", "misfire", "sobrecalentamiento", "humo", "refrigerante")):
                return SubsistemaVehicular.MARCHA_MOTOR

        # 2. Por hipótesis principal previa si existe
        falla_p = (getattr(estado, "falla_principal", None) or (estado.top3_actual[0]["falla"] if estado.top3_actual else "")).lower()
        falla_p = falla_p.replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
        if "freno" in falla_p or "disco" in falla_p:
            return SubsistemaVehicular.FRENOS
        if "arranque" in falla_p or "solenoide" in falla_p:
            return SubsistemaVehicular.ARRANQUE
        if "bateria" in falla_p or "alternador" in falla_p:
            return SubsistemaVehicular.ELECTRICO
        if "caja" in falla_p or "embrague" in falla_p or "transmision" in falla_p:
            return SubsistemaVehicular.TRANSMISION
        if "suspension" in falla_p or "amortiguador" in falla_p or "rotula" in falla_p:
            return SubsistemaVehicular.SUSPENSION
        if "aire acondicionado" in falla_p or "climatizacion" in falla_p or "r134a" in falla_p:
            return SubsistemaVehicular.CLIMATIZACION
        if any(k in falla_p for k in ("bujia", "bobina", "refrigerante", "culata", "inyeccion", "termostato")):
            return SubsistemaVehicular.MARCHA_MOTOR

        # 3. Por EstadoOperativo
        if estado.estado_operativo == EstadoOperativo.ARRANQUE:
            return SubsistemaVehicular.ARRANQUE
        if estado.estado_operativo == EstadoOperativo.FRENADO:
            return SubsistemaVehicular.FRENOS
        if estado.estado_operativo in (EstadoOperativo.MARCHA, EstadoOperativo.RALENTI):
            return SubsistemaVehicular.MARCHA_MOTOR

        # 4. Por dominio_probable si está registrado
        if getattr(estado, "dominio_probable", None):
            dom = str(estado.dominio_probable).strip().upper()
            for sub in SubsistemaVehicular:
                if sub.value == dom or sub.name == dom:
                    return sub

        return SubsistemaVehicular.DESCONOCIDO

    @classmethod
    def es_sintoma_coexistente(cls, sub1: SubsistemaVehicular, sub2: SubsistemaVehicular, texto: str) -> bool:
        """Determina si dos síntomas corresponden al mismo vehículo/diagnóstico integral."""
        if sub1 == sub2:
            return True
        # Par frenos / suspensión (vibración en volante a velocidad o al frenar)
        if {sub1, sub2} == {SubsistemaVehicular.FRENOS, SubsistemaVehicular.SUSPENSION}:
            return True
        # Par motor marcha / eléctrico (rateo de encendido y alternador/check engine)
        if {sub1, sub2} == {SubsistemaVehicular.MARCHA_MOTOR, SubsistemaVehicular.ELECTRICO}:
            return True
        # Arranque y alimentación eléctrica forman un mismo árbol diagnóstico.
        if {sub1, sub2} == {SubsistemaVehicular.ARRANQUE, SubsistemaVehicular.ELECTRICO}:
            return True
        # Arranque y desempeño del motor pueden ser eslabones de una misma
        # cadena causal (p. ej. arranque difícil, humo y pérdida bajo carga).
        if {sub1, sub2} == {SubsistemaVehicular.ARRANQUE, SubsistemaVehicular.MARCHA_MOTOR}:
            return True
        # Solo conectores aditivos inequívocos. "Y cuando" / "y al" dentro de
        # una queja nueva describen su propia secuencia y no enlazan casos.
        txt = texto.lower()
        if re.search(r"\b(tambi[eé]n|adem[aá]s|junto\s+con|aparte\s+de\s+eso)\b", txt):
            return True
        return False

    @staticmethod
    def es_nueva_queja_principal(texto: str) -> bool:
        """Detecta marcadores de una queja nueva sin depender del sistema."""
        txt = "".join(
            c for c in unicodedata.normalize("NFD", (texto or "").lower().strip())
            if unicodedata.category(c) != "Mn"
        )
        if re.search(r"\bayer\b.*\bhoy\b", txt):
            return True
        if re.search(
            r"\b(el\s+cliente\s+(?:dejo|trajo|dice\s+que|indica|comenta|comenta\s+que|menciona|menciona\s+que|reporta|reporta\s+que|refiere|refiere\s+que)|"
            r"otro\s+vehiculo|otro\s+veh.culo|otro\s+carro|otro\s+auto|este\s+es\s+otro|nuevo\s+caso|ahora\s+el\s+problema|"
            r"tengo\s+(?:un\s+|otro\s+)?(?:vehiculo|veh.culo|auto|carro|caso)\s+(?:en\s+el\s+taller|en\s+taller)|"
            r"ahora\s+revisemos|ya\s+revisare\s+eso|tengo\s+otro\s+problema|olvida\s+lo\s+anterior)\b",
            txt,
        ):
            return True
        return bool(
            re.search(
                r"^(?:(?:hola|buenas(?:\s+d[ií]as|\s+tardes|\s+noches)?)[,.:;!]?\s*)?"
                r"(?:tengo|presenta|traigo|vengo\s+por|me\s+llego|nos\s+llego)\s+(?:otro\s+|un\s+)?(?:problema|falla|consulta|vehiculo|veh.culo|auto|carro|caso)\b",
                txt,
            )
        )

    @classmethod
    def evaluar_transicion(
        cls,
        estado: ConversationState,
        texto_usuario: str,
        estado_detectado_mensaje: EstadoOperativo,
        seniales_mensaje: Dict[str, Any],
        seniales_heredadas: Dict[str, Any],
    ) -> TransicionCasoResultado:
        """
        Determina si el mensaje entrante debe procesarse en el caso activo,
        iniciar un nuevo caso clínico o solicitar aclaración de alcance.
        """
        estado_previo = estado.estado_operativo
        texto_l = "".join(
            c for c in unicodedata.normalize("NFD", (texto_usuario or "").lower().strip())
            if unicodedata.category(c) != "Mn"
        )

        # 0. Si la última pregunta fue de aclaración de alcance, interpretar la respuesta directa
        if estado.preguntas_realizadas:
            ult_preg = estado.preguntas_realizadas[-1]
            if ult_preg.get("intent") in (QuestionIntent.ACLARACION_ALCANCE.value, QuestionIntent.ACLARACION_CONTRADICCION.value):
                if re.search(r"\b(diferente|otra\s+falla|otro\s+problema|otro\s+carro|distinto|nuevo\s+caso)\b", texto_l):
                    return TransicionCasoResultado(
                        decision=DecisionTransicion.CAMBIO_DE_CASO,
                        motivo="USUARIO_CONFIRMA_FALLA_DIFERENTE",
                        nuevo_case_id=str(uuid.uuid4()),
                        estado_previo=estado_previo,
                        estado_detectado_mensaje=estado_detectado_mensaje,
                    )
                if re.search(r"\b(mismo|misma\s+falla|el\s+mismo\s+carro|mismo\s+auto|del\s+mismo)\b", texto_l):
                    return TransicionCasoResultado(
                        decision=DecisionTransicion.MANTENER_CASO,
                        motivo="USUARIO_CONFIRMA_MISMO_CASO",
                        estado_previo=estado_previo,
                        estado_detectado_mensaje=estado_detectado_mensaje,
                    )

        # 1. Si no hay hechos activos previos, siempre se mantiene el caso actual
        if not estado.hechos:
            return TransicionCasoResultado(
                decision=DecisionTransicion.MANTENER_CASO,
                motivo="SIN_HECHOS_PREVIOS",
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
            )

        # 1.5 Corrección explícita del usuario sobre el problema/síntoma activo (Fase 11.3 - Caso F / T08)
        corrs_usuario = ExtractorHechos.detectar_correcciones(texto_usuario)
        if corrs_usuario:
            sub_det = cls.detectar_subsistema_texto(texto_usuario)
            return TransicionCasoResultado(
                decision=DecisionTransicion.MANTENER_CASO,
                motivo="CORRECCION_USUARIO_REEMPLAZA_SISTEMA",
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
                dominio_detectado_mensaje=sub_det,
            )

        # 2. Solicitud explícita de nuevo diagnóstico / vehículo / caso de taller
        if re.search(
            r"\b(otro\s+problema|falla\s+diferente|tengo\s+otra\s+consulta|otro\s+auto|otro\s+carro|"
            r"el\s+cliente\s+dejo|nuevo\s+caso|este\s+es\s+otro\s+carro|otro\s+vehiculo|otro\s+veh.culo|"
            r"ahora\s+el\s+problema\s+es|ya\s+revisare\s+eso\s+despues)\b",
            texto_l,
        ):
            sub_det = cls.detectar_subsistema_texto(texto_usuario)
            return TransicionCasoResultado(
                decision=DecisionTransicion.CAMBIO_DE_CASO,
                motivo="SOLICITUD_EXPLICITA_NUEVA_CONSULTA",
                nuevo_case_id=str(uuid.uuid4()),
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
                dominio_detectado_mensaje=sub_det,
            )

        tiene_arranque_heredado = bool(
            seniales_heredadas.get("senial_arranque")
            or estado_previo == EstadoOperativo.ARRANQUE
            or any(
                h.valor in ("NO", "clic_unico", "clics_repetidos")
                for k, h in estado.hechos.items()
                if k in ("motor_arranca", "ruido_arranque")
            )
        )

        tiene_movimiento_actual = bool(
            seniales_mensaje.get("senial_frenado")
            or seniales_mensaje.get("senial_marcha")
            or estado_detectado_mensaje in (EstadoOperativo.FRENADO, EstadoOperativo.MARCHA)
            or re.search(r"\b(cuando\s+freno|al\s+frenar|frenando|en\s+carretera|a\s+\d+\s*km/h|manejando|circulando)\b", texto_l)
        )

        # Regla A: Incompatibilidad inequívoca ARRANQUE (inmovilizado) vs MOVIMIENTO (circulando/frenando)
        if (
            tiene_arranque_heredado
            and tiene_movimiento_actual
            and cls.es_nueva_queja_principal(texto_usuario)
        ):
            sub_det = cls.detectar_subsistema_texto(texto_usuario)
            return TransicionCasoResultado(
                decision=DecisionTransicion.CAMBIO_DE_CASO,
                motivo=f"INCOMPATIBILIDAD_OPERACIONAL: ARRANQUE_VS_{estado_detectado_mensaje.value}",
                nuevo_case_id=str(uuid.uuid4()),
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
                dominio_detectado_mensaje=sub_det,
            )

        # Regla B: Incompatibilidad inversa: Caso activo en MOVIMIENTO vs Mensaje reporta arranque inmovilizado
        tiene_movimiento_heredado = bool(
            estado_previo in (EstadoOperativo.FRENADO, EstadoOperativo.MARCHA)
            or seniales_heredadas.get("senial_frenado")
            or seniales_heredadas.get("senial_marcha")
        )
        tiene_arranque_actual = bool(
            seniales_mensaje.get("senial_arranque")
            or estado_detectado_mensaje == EstadoOperativo.ARRANQUE
            or re.search(r"\b(no\s+quiso\s+arrancar|no\s+arranca|no\s+prende|clic\s+seco|se\s+quedo\s+parado\s+y\s+no\s+arranca)\b", texto_l)
        )
        if (
            tiene_movimiento_heredado
            and tiene_arranque_actual
            and cls.es_nueva_queja_principal(texto_usuario)
        ):
            sub_det = cls.detectar_subsistema_texto(texto_usuario)
            return TransicionCasoResultado(
                decision=DecisionTransicion.CAMBIO_DE_CASO,
                motivo=f"INCOMPATIBILIDAD_OPERACIONAL: {estado_previo.value}_VS_ARRANQUE",
                nuevo_case_id=str(uuid.uuid4()),
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
                dominio_detectado_mensaje=sub_det if sub_det != SubsistemaVehicular.DESCONOCIDO else SubsistemaVehicular.ARRANQUE,
            )

        # Regla C: Regresiones Cross-System tras caso previamente diagnosticado o maduro
        subsistema_previo = cls.obtener_subsistema_estado(estado)
        subsistema_actual = cls.detectar_subsistema_texto(texto_usuario)

        caso_ya_diagnosticado = bool(estado.fase == ConversationPhase.RESULTADO or estado.top3_actual)
        if (
            caso_ya_diagnosticado
            and subsistema_actual != SubsistemaVehicular.DESCONOCIDO
            and subsistema_previo != SubsistemaVehicular.DESCONOCIDO
        ):
            if subsistema_actual != subsistema_previo:
                if cls.es_nueva_queja_principal(texto_usuario):
                    return TransicionCasoResultado(
                        decision=DecisionTransicion.CAMBIO_DE_CASO,
                        motivo=(
                            f"NUEVA_QUEJA_PRINCIPAL: {subsistema_previo.value}_A_"
                            f"{subsistema_actual.value}"
                        ),
                        nuevo_case_id=str(uuid.uuid4()),
                        estado_previo=estado_previo,
                        estado_detectado_mensaje=estado_detectado_mensaje,
                    )
                if cls.es_sintoma_coexistente(subsistema_previo, subsistema_actual, texto_usuario):
                    return TransicionCasoResultado(
                        decision=DecisionTransicion.MANTENER_CASO,
                        motivo=f"SINTOMAS_COEXISTENTES: {subsistema_previo.value}_CON_{subsistema_actual.value}",
                        estado_previo=estado_previo,
                        estado_detectado_mensaje=estado_detectado_mensaje,
                    )
                # Transición de sistema nítida (ej. FRENADO->MARCHA, ELECTRICO->TRANSMISION, MOTOR->SUSPENSION)
                return TransicionCasoResultado(
                    decision=DecisionTransicion.CAMBIO_DE_CASO,
                    motivo=f"TRANSICION_SISTEMA: {subsistema_previo.value}_A_{subsistema_actual.value}",
                    nuevo_case_id=str(uuid.uuid4()),
                    estado_previo=estado_previo,
                    estado_detectado_mensaje=estado_detectado_mensaje,
                )

        # Regla D: Ambigüedad operacional genuina (condiciones contrapuestas en el mismo mensaje)
        if seniales_mensaje.get("es_contradictorio_interno"):
            return TransicionCasoResultado(
                decision=DecisionTransicion.ACLARACION_REQUERIDA,
                motivo="AMBIGUEDAD_OPERACIONAL_MENSAJE",
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
                pregunta_aclaracion=cls.PREGUNTA_ACLARACION_CANONICA,
            )

        # Regla E: Caso en progreso con síntoma de sistema totalmente diferente sin conectores
        if not caso_ya_diagnosticado and subsistema_actual != SubsistemaVehicular.DESCONOCIDO:
            if subsistema_previo != SubsistemaVehicular.DESCONOCIDO and subsistema_actual != subsistema_previo:
                if not cls.es_sintoma_coexistente(subsistema_previo, subsistema_actual, texto_usuario):
                    if cls.es_nueva_queja_principal(texto_usuario):
                        return TransicionCasoResultado(
                            decision=DecisionTransicion.CAMBIO_DE_CASO,
                            motivo=f"NUEVA_QUEJA_PRINCIPAL: {subsistema_previo.value}_A_{subsistema_actual.value}",
                            nuevo_case_id=str(uuid.uuid4()),
                            estado_previo=estado_previo,
                            estado_detectado_mensaje=estado_detectado_mensaje,
                            dominio_detectado_mensaje=subsistema_actual,
                        )
                    return TransicionCasoResultado(
                        decision=DecisionTransicion.ACLARACION_REQUERIDA,
                        motivo=f"AMBIGUEDAD_DISCREPANCIA_SISTEMA: {subsistema_previo.value}_VS_{subsistema_actual.value}",
                        estado_previo=estado_previo,
                        estado_detectado_mensaje=estado_detectado_mensaje,
                        pregunta_aclaracion=cls.PREGUNTA_ACLARACION_CANONICA,
                    )

        # Regla F: Síntomas compatibles en el mismo caso
        return TransicionCasoResultado(
            decision=DecisionTransicion.MANTENER_CASO,
            motivo="SINTOMAS_COMPATIBLES_MISMO_CASO",
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
        )

    @classmethod
    def archivar_y_limpiar_caso(
        cls,
        estado: ConversationState,
        nuevo_case_id: Optional[str] = None,
    ) -> str:
        """
        Archiva los hechos del caso activo en hechos_historicos y resetea
        la memoria activa para el nuevo caso clínico.
        """
        nuevo_id = nuevo_case_id or str(uuid.uuid4())
        estado.archivar_caso_actual(nuevo_id)
        return nuevo_id

    @classmethod
    def resolver_transicion_turno(
        cls,
        estado: ConversationState,
        texto_limpio: str,
        gestor_diagnostico: Any,
        session_id: str,
        t0: float,
        contexto_previo: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], TransicionCasoResultado]:
        """
        Evalúa y aplica la transición de caso en el estado conversacional.
        Retorna (respuesta_temprana_dict, transicion) o (None, transicion).
        """
        res_op = ExtractorHechos.inferir_estado_operativo(estado, texto_limpio)
        estado_op_det, _, meta_op = res_op[0], res_op[1], res_op[2]

        transicion = cls.evaluar_transicion(
            estado=estado,
            texto_usuario=texto_limpio,
            estado_detectado_mensaje=estado_op_det,
            seniales_mensaje=meta_op.get("seniales_mensaje", {}),
            seniales_heredadas=meta_op.get("seniales_heredadas", {}),
        )
        transicion.dominio_previo = cls.obtener_subsistema_estado(estado)
        transicion.dominio_detectado_mensaje = cls.detectar_subsistema_texto(texto_limpio)

        if transicion.decision == DecisionTransicion.CAMBIO_DE_CASO:
            cls.archivar_y_limpiar_caso(estado, transicion.nuevo_case_id)
            if transicion.dominio_detectado_mensaje and transicion.dominio_detectado_mensaje != SubsistemaVehicular.DESCONOCIDO:
                estado.dominio_probable = transicion.dominio_detectado_mensaje.value
            if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
                gestor_diagnostico.session_manager.reiniciar_sesion(session_id)
            return None, transicion

        if transicion.decision == DecisionTransicion.ACLARACION_REQUERIDA:
            pregunta_aclarar = transicion.pregunta_aclaracion or cls.PREGUNTA_ACLARACION_CANONICA
            estado.registrar_pregunta(
                intent=QuestionIntent.ACLARACION_ALCANCE,
                texto=pregunta_aclarar,
                incrementar_repregunta=False,
            )
            traza = TurnTrace(
                turno=estado.turno_actual,
                mensaje_original=texto_limpio,
                contexto_previo=contexto_previo,
                decision="ACLARACION_CASO",
                motivo_decision=transicion.motivo,
                respuesta_enviada=pregunta_aclarar,
                hechos_nuevos_extraidos=[],
                hechos_actualizados=[],
                consulta_consolidada="",
                top3=[],
                confianza=1.0,
                estado_operativo=estado.estado_operativo.value,
                question_intent=QuestionIntent.ACLARACION_ALCANCE.value,
                pregunta_final=pregunta_aclarar,
                estado_previo=transicion.estado_previo.value,
                estado_detectado_mensaje_actual=transicion.estado_detectado_mensaje.value,
                decision_transicion=transicion.decision.value,
                motivo_transicion=transicion.motivo,
                dominio_previo=transicion.dominio_previo.value,
                dominio_detectado_actual=transicion.dominio_detectado_mensaje.value,
                dominio_actual=estado.dominio_probable,
                version_orquestador=ORCHESTRATOR_VERSION,
            )
            estado.trazabilidad.append(traza.to_dict())
            ret = {
                "status": "aclaracion_caso",
                "respuesta_texto": pregunta_aclarar,
                "diagnostico_ml": "Aclaración de alcance",
                "confianza_ml": estado.confianza_actual,
                "fase": estado.fase.value,
                "es_pregunta": True,
                "decision": "ACLARACION_CASO",
                "motivo_decision": transicion.motivo,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
                "estado_operativo": estado.estado_operativo.value,
                "question_intent": QuestionIntent.ACLARACION_ALCANCE.value,
                "pregunta_final": pregunta_aclarar,
                "decision_transicion": transicion.decision.value,
                "motivo_transicion": transicion.motivo,
                "estado_previo": transicion.estado_previo.value,
                "estado_detectado_mensaje_actual": transicion.estado_detectado_mensaje.value,
                "dominio_previo": transicion.dominio_previo.value,
                "dominio_detectado_actual": transicion.dominio_detectado_mensaje.value,
                "dominio_actual": estado.dominio_probable,
                "version_orquestador": ORCHESTRATOR_VERSION,
            }
            return ret, transicion

        return None, transicion
