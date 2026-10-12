"""Tipos y enumeraciones para la segmentación de casos diagnósticos."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.core.conversacion.models import EstadoOperativo


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
