"""Enumeraciones formales para el estado conversacional y clínico de CarBot."""

from __future__ import annotations

from enum import Enum


class FactState(str, Enum):
    """Estados clínicos de un hecho observado o declarado."""
    CONFIRMADO = "CONFIRMADO"
    REPORTADO_SIN_VERIFICAR = "REPORTADO_SIN_VERIFICAR"
    AUSENTE_NEGADO = "AUSENTE_NEGADO"
    NO_REVISADO = "NO_REVISADO"
    NO_SABE_REALIZAR = "NO_SABE_REALIZAR"
    DESCARTADO = "DESCARTADO"
    DESCONOCIDO = "DESCONOCIDO"
    CORREGIDO = "CORREGIDO"
    CONTRADICTORIO = "CONTRADICTORIO"
    AMBIGUO = "AMBIGUO"
    NO_APLICA = "NO_APLICA"


class ConversationPhase(str, Enum):
    """Fases formales de la máquina de estados conversacional."""
    INICIO = "INICIO"
    RECOLECTANDO = "RECOLECTANDO"
    ACLARANDO = "ACLARANDO"
    DIAGNOSTICANDO = "DIAGNOSTICANDO"
    RESULTADO = "RESULTADO"


class EstadoOperativo(str, Enum):
    """Fase o condición operacional descrita por el usuario (Fase 9.6)."""
    ARRANQUE = "ARRANQUE"
    RALENTI = "RALENTI"
    MARCHA = "MARCHA"
    FRENADO = "FRENADO"
    ESTACIONADO = "ESTACIONADO"
    DESCONOCIDO = "DESCONOCIDO"


class QuestionIntent(str, Enum):
    """Intención semántica para discriminación y escape de bucles."""
    TEMPERATURA_APARICION = "TEMPERATURA_APARICION"
    CONDICION_OPERACION = "CONDICION_OPERACION"
    COMPORTAMIENTO_MOTOR = "COMPORTAMIENTO_MOTOR"
    PRESENCIA_RUIDO = "PRESENCIA_RUIDO"
    CODIGO_DTC = "CODIGO_DTC"
    MEDICION_TECNICA = "MEDICION_TECNICA"
    DISPONIBILIDAD_HERRAMIENTA = "DISPONIBILIDAD_HERRAMIENTA"
    MEDICION_VOLTAJE = "MEDICION_VOLTAJE"
    MEDICION_PRESION = "MEDICION_PRESION"
    COMPONENTE_REVISADO = "COMPONENTE_REVISADO"
    CONFIRMACION_ALTERNATIVA = "CONFIRMACION_ALTERNATIVA"
    DISCRIMINACION_TOP3 = "DISCRIMINACION_TOP3"
    COMPORTAMIENTO_ARRANQUE = "COMPORTAMIENTO_ARRANQUE"
    CAIDA_TENSION_ARRANQUE = "CAIDA_TENSION_ARRANQUE"
    TEMPERATURA_MOTOR_EN_MARCHA = "TEMPERATURA_MOTOR_EN_MARCHA"
    TEMPERATURA_AMBIENTAL_ARRANQUE = "TEMPERATURA_AMBIENTAL_ARRANQUE"
    ACLARACION_CONTRADICCION = "ACLARACION_CONTRADICCION"
    ACLARACION_ALCANCE = "ACLARACION_ALCANCE"
    PLAN_B_SIN_HERRAMIENTAS = "PLAN_B_SIN_HERRAMIENTAS"
    DATOS_VEHICULO = "DATOS_VEHICULO"
    GENERAL = "GENERAL"


class EvidenceLevel(str, Enum):
    """Nivel de evidencia clínica acumulada en la conversación."""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class DtcStatus(str, Enum):
    """Estado de verificación del código de diagnóstico OBD-II (Adenda 9.1)."""
    DTC_OBSERVADO = "DTC_OBSERVADO"      # Aportado explícitamente por el mecánico
    DTC_RELACIONADO = "DTC_RELACIONADO"  # Sugerido hipotéticamente por ML/RAG
    SIN_DTC = "SIN_DTC"                  # Ningún código presente
    DTC_AUSENTE = "SIN_DTC"              # Alias retrocompatible para SIN_DTC
    DTC_DESCONOCIDO = "DTC_DESCONOCIDO"  # No se ha escaneado o sin escáner disponible


class FactType(str, Enum):
    """Clasificación del hecho según Adenda 9.1."""
    SINTOMA = "SINTOMA"
    CAUSA = "CAUSA"
    CONDICION = "CONDICION"
    MODIFICADOR = "MODIFICADOR"
