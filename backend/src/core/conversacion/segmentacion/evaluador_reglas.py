"""Evaluación de reglas operacionales y de alcance para transiciones de caso."""

from __future__ import annotations

import re
import unicodedata
import uuid
from typing import TYPE_CHECKING, Any, Dict

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import (
    ConversationPhase,
    EstadoOperativo,
    QuestionIntent,
)
from src.core.conversacion.segmentacion.detector_subsistemas import (
    detectar_subsistema_texto,
    es_sintoma_coexistente,
    obtener_subsistema_estado,
)
from src.core.conversacion.segmentacion.tipos import (
    DecisionTransicion,
    SubsistemaVehicular,
    TransicionCasoResultado,
)

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState

PREGUNTA_ACLARACION_CANONICA = (
    "¿Este problema corresponde al mismo vehículo/caso que estábamos revisando o es una falla diferente?"
)


def es_nueva_queja_principal(texto: str) -> bool:
    """Solo marca cambio con una solicitud explícita; la diferencia de síntomas no basta."""
    solicitud = ExtractorHechos.clasificar_solicitud_caso(texto)
    return bool(solicitud and solicitud.get("accion") == "nuevo_caso")


def evaluar_transicion(
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

    solicitud_caso = ExtractorHechos.clasificar_solicitud_caso(texto_usuario)
    if solicitud_caso and solicitud_caso.get("accion") == "nuevo_caso":
        sub_det = detectar_subsistema_texto(texto_usuario)
        sufijo_vehiculo = "_MISMO_VEHICULO" if solicitud_caso.get("preservar_vehiculo") else ""
        return TransicionCasoResultado(
            decision=DecisionTransicion.CAMBIO_DE_CASO,
            motivo=f"SOLICITUD_EXPLICITA_NUEVA_CONSULTA{sufijo_vehiculo}",
            nuevo_case_id=str(uuid.uuid4()),
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
            dominio_detectado_mensaje=sub_det,
        )

    # 0a. Consultas de resumen, presupuesto, cotización, explicación técnica o procedimiento
    es_meta_consulta = bool(
        re.search(
            r"\b(resumen|cotizar|cotizacion|presupuesto|informe|orden\s+de\s+reparacion|cuanto\s+cuesta|"
            r"procedimiento|paso\s+a\s+paso|como\s+pruebo|como\s+compruebo|como\s+inspecciono|como\s+(?:se\s+)?mide|como\s+mido|como\s+(?:se\s+)?calibra|como\s+calibro|como\s+(?:se\s+)?prueba|reloj\s+comparador|alabeo|"
            r"por\s+que|explicacion|tolerancia|especificacion|que\s+significa|que\s+codigo|"
            r"confirma|descarta|indica|significa)\b",
            texto_l,
        )
    )
    if es_meta_consulta:
        return TransicionCasoResultado(
            decision=DecisionTransicion.MANTENER_CASO,
            motivo="CONSULTA_PROCEDIMIENTO_O_RESUMEN_CASO_ACTIVO",
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
            dominio_detectado_mensaje=obtener_subsistema_estado(estado),
        )

    # 0. Si la última pregunta fue de aclaración de alcance, interpretar la respuesta directa
    if estado.preguntas_realizadas:
        ult_preg = estado.preguntas_realizadas[-1]
        if ult_preg.get("intent") in (QuestionIntent.ACLARACION_ALCANCE.value, QuestionIntent.ACLARACION_CONTRADICCION.value):
            if re.match(
                r"^(?:si[,\s]+)?(?:(?:es|se trata de|corresponde a)\s+)?"
                r"(?:diferente|otra\s+falla|otro\s+problema|otro\s+carro|otro\s+vehiculo|distinto)\b",
                texto_l,
            ) and not re.search(r"\b(?:no|negativo)\b", texto_l):
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
    if not estado.hechos and not estado.active_symptoms:
        return TransicionCasoResultado(
            decision=DecisionTransicion.MANTENER_CASO,
            motivo="SIN_HECHOS_PREVIOS",
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
        )

    correccion_sistema = bool(
        re.search(r"\bno\s+es\s+(?:un\s+)?(?:problema\s+de\s+)?(?:motor|mecanico|combustion)\b", texto_l)
        and re.search(r"\b(?:ruido|falla|problema)\b.{0,45}\b(?:suspension|frenos?|transmision|embrague|electric[oa])\b", texto_l)
    ) or bool(
        re.search(
            r"\b(?:ruido|falla)\s+(?:viene|proviene)\s+de\s+(?:la\s+|el\s+)?(?:suspension|frenos?|transmision)\b",
            texto_l,
        )
        and re.search(r"\b(?:no\s+es|me\s+equivoque|corrijo|quise\s+decir)\b", texto_l)
    )
    correccion_sistema = correccion_sistema or bool(
        re.search(r"\b(?:corrige|corrijo|me equivoque|quise decir|en realidad|no es)\b", texto_l)
        and "?" not in texto_l
    )
    if correccion_sistema:
        anterior = obtener_subsistema_estado(estado)
        # El sistema negado no determina el destino de la rectificación.
        afirmado = " ".join(c for c in re.split(r"[.;,]", texto_usuario)
                            if not re.search(r"\bno\s+es\b", c, re.IGNORECASE))
        actual = detectar_subsistema_texto(afirmado or texto_usuario)
        if actual != SubsistemaVehicular.DESCONOCIDO and actual != anterior:
            return TransicionCasoResultado(
                decision=DecisionTransicion.MANTENER_CASO,
                motivo=f"RECTIFICACION_SISTEMA_{anterior.value}_A_{actual.value}",
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
                dominio_detectado_mensaje=actual,
            )

    # 1.5 Corrección explícita del usuario sobre el problema/síntoma activo
    corrs_usuario = ExtractorHechos.detectar_correcciones(texto_usuario)
    if corrs_usuario:
        sub_det = detectar_subsistema_texto(texto_usuario)
        return TransicionCasoResultado(
            decision=DecisionTransicion.MANTENER_CASO,
            motivo="CORRECCION_USUARIO_REEMPLAZA_SISTEMA",
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
            dominio_detectado_mensaje=sub_det,
        )

    # 1.6 Especificación de configuración o perfil técnico del vehículo activo
    es_especificacion_perfil = bool(
        re.search(
            r"\b(?:es\s+)?(?:transmisi[oó]n|caja)\s+(?:mec[aá]nica|manual|autom[aá]tica|cvt)\b|"
            r"\b(?:es\s+)?caja\s+de\s+\d+\s+(?:cambios|velocidades)\b|"
            r"\b(?:transmisi[oó]n|caja)\s+(?:mec[aá]nica\s+)?manual\s+de\s+\d+\s+velocidades\b",
            texto_l,
        )
        and not re.search(r"\b(otro\s+carro|otro\s+auto|otra\s+falla|nuevo\s+caso)\b", texto_l)
    )
    if es_especificacion_perfil:
        return TransicionCasoResultado(
            decision=DecisionTransicion.MANTENER_CASO,
            motivo="ESPECIFICACION_PERFIL_VEHICULAR",
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
            dominio_detectado_mensaje=detectar_subsistema_texto(texto_usuario),
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

    coexistencia_declarada = any(
        re.search(
            r"\b(?:dos|2)\s+(?:problemas|fallas|aver[ií]as)\b.{0,45}"
            r"\b(?:simult[aá]ne|mismo\s+tiempo|mismo\s+veh[ií]culo|no\s+mezcl)",
            mensaje,
            re.IGNORECASE,
        )
        for mensaje in estado.historial_mensajes_usuario
    )

    # Una condición de marcha no borra un problema de arranque ni viceversa.
    # Si el relato introduce otro sistema, aclarar el alcance antes de diagnosticar.
    subsistema_previo = obtener_subsistema_estado(estado)
    subsistema_actual = detectar_subsistema_texto(texto_usuario)
    if (
        subsistema_previo != SubsistemaVehicular.DESCONOCIDO
        and subsistema_actual != SubsistemaVehicular.DESCONOCIDO
        and subsistema_previo != subsistema_actual
        and not coexistencia_declarada
        and not es_sintoma_coexistente(subsistema_previo, subsistema_actual, texto_usuario)
    ):
        return TransicionCasoResultado(
            decision=DecisionTransicion.ACLARACION_REQUERIDA,
            motivo="ALCANCE_NUEVO_SISTEMA_PENDIENTE",
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
            dominio_previo=subsistema_previo,
            dominio_detectado_mensaje=subsistema_actual,
            pregunta_aclaracion=PREGUNTA_ACLARACION_CANONICA,
        )

    # Regla A: Incompatibilidad inequívoca ARRANQUE vs MOVIMIENTO
    if tiene_arranque_heredado and tiene_movimiento_actual and es_nueva_queja_principal(texto_usuario):
        sub_det = detectar_subsistema_texto(texto_usuario)
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
    if tiene_movimiento_heredado and tiene_arranque_actual and es_nueva_queja_principal(texto_usuario):
        sub_det = detectar_subsistema_texto(texto_usuario)
        return TransicionCasoResultado(
            decision=DecisionTransicion.CAMBIO_DE_CASO,
            motivo=f"INCOMPATIBILIDAD_OPERACIONAL: {estado_previo.value}_VS_ARRANQUE",
            nuevo_case_id=str(uuid.uuid4()),
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
            dominio_detectado_mensaje=sub_det if sub_det != SubsistemaVehicular.DESCONOCIDO else SubsistemaVehicular.ARRANQUE,
        )

    # Regla C: Regresiones Cross-System tras caso previamente diagnosticado o maduro
    subsistema_previo = obtener_subsistema_estado(estado)
    subsistema_actual = detectar_subsistema_texto(texto_usuario)


    caso_ya_diagnosticado = bool(estado.fase == ConversationPhase.RESULTADO or estado.top3_actual)
    if caso_ya_diagnosticado and subsistema_actual != SubsistemaVehicular.DESCONOCIDO and subsistema_previo != SubsistemaVehicular.DESCONOCIDO:
        if subsistema_actual != subsistema_previo:
            if coexistencia_declarada:
                return TransicionCasoResultado(
                    decision=DecisionTransicion.MANTENER_CASO,
                    motivo=f"AVERIAS_SIMULTANEAS_DECLARADAS: {subsistema_previo.value}_CON_{subsistema_actual.value}",
                    estado_previo=estado_previo,
                    estado_detectado_mensaje=estado_detectado_mensaje,
                    dominio_detectado_mensaje=subsistema_actual,
                )
            if es_nueva_queja_principal(texto_usuario):
                return TransicionCasoResultado(
                    decision=DecisionTransicion.CAMBIO_DE_CASO,
                    motivo=f"NUEVA_QUEJA_PRINCIPAL: {subsistema_previo.value}_A_{subsistema_actual.value}",
                    nuevo_case_id=str(uuid.uuid4()),
                    estado_previo=estado_previo,
                    estado_detectado_mensaje=estado_detectado_mensaje,
                )
            if es_sintoma_coexistente(subsistema_previo, subsistema_actual, texto_usuario):
                return TransicionCasoResultado(
                    decision=DecisionTransicion.MANTENER_CASO,
                    motivo=f"SINTOMAS_COEXISTENTES: {subsistema_previo.value}_CON_{subsistema_actual.value}",
                    estado_previo=estado_previo,
                    estado_detectado_mensaje=estado_detectado_mensaje,
                )
            return TransicionCasoResultado(
                decision=DecisionTransicion.ACLARACION_REQUERIDA,
                motivo=f"AMBIGUEDAD_TRANSICION_SISTEMA: {subsistema_previo.value}_VS_{subsistema_actual.value}",
                estado_previo=estado_previo,
                estado_detectado_mensaje=estado_detectado_mensaje,
                pregunta_aclaracion=PREGUNTA_ACLARACION_CANONICA,
            )

    # Regla D: Ambigüedad operacional genuina
    if seniales_mensaje.get("es_contradictorio_interno"):
        return TransicionCasoResultado(
            decision=DecisionTransicion.ACLARACION_REQUERIDA,
            motivo="AMBIGUEDAD_OPERACIONAL_MENSAJE",
            estado_previo=estado_previo,
            estado_detectado_mensaje=estado_detectado_mensaje,
            pregunta_aclaracion=PREGUNTA_ACLARACION_CANONICA,
        )

    # Regla E: Caso en progreso con síntoma de sistema totalmente diferente sin conectores
    if not caso_ya_diagnosticado and subsistema_actual != SubsistemaVehicular.DESCONOCIDO:
        if subsistema_previo != SubsistemaVehicular.DESCONOCIDO and subsistema_actual != subsistema_previo:
            if coexistencia_declarada:
                return TransicionCasoResultado(
                    decision=DecisionTransicion.MANTENER_CASO,
                    motivo=f"AVERIAS_SIMULTANEAS_DECLARADAS: {subsistema_previo.value}_CON_{subsistema_actual.value}",
                    estado_previo=estado_previo,
                    estado_detectado_mensaje=estado_detectado_mensaje,
                    dominio_detectado_mensaje=subsistema_actual,
                )
            if not es_sintoma_coexistente(subsistema_previo, subsistema_actual, texto_usuario):
                if es_nueva_queja_principal(texto_usuario):
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
                    pregunta_aclaracion=PREGUNTA_ACLARACION_CANONICA,
                )

    # Regla F: Síntomas compatibles en el mismo caso
    return TransicionCasoResultado(
        decision=DecisionTransicion.MANTENER_CASO,
        motivo="SINTOMAS_COMPATIBLES_MISMO_CASO",
        estado_previo=estado_previo,
        estado_detectado_mensaje=estado_detectado_mensaje,
    )
