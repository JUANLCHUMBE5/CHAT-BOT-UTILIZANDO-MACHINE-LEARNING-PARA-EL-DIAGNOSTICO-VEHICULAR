"""Contratos de datos Pydantic V2 para el procesamiento de mensajes y memoria conversacional de CarBot."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IntentType(str, Enum):
    """Intención primaria del turno del usuario."""
    SALUDO = "SALUDO"
    CONSULTA_TECNICA = "CONSULTA_TECNICA"
    DIAGNOSTICO_SINTOMA = "DIAGNOSTICO_SINTOMA"
    VALIDACION_TECNICA = "VALIDACION_TECNICA"
    CORRECCION_DATOS = "CORRECCION_DATOS"
    CAMBIO_CASO = "CAMBIO_CASO"
    SOLICITUD_DETALLE = "SOLICITUD_DETALLE"
    REINICIO = "REINICIO"
    FUERA_DE_ALCANCE = "FUERA_DE_ALCANCE"
    INDETERMINADO = "INDETERMINADO"


class VehiculoIdentificado(BaseModel):
    """Datos explícitos identificados del vehículo en el mensaje o turno."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    placa: Optional[str] = Field(
        default=None,
        description="Placa vehicular normalizada formal (ej: 'ABC-1234', 'A1B-234'). Nunca 'SIN-PLACA'.",
    )
    es_provisional: bool = Field(
        default=False,
        description="Indica si el vehículo carece de placa formal y opera con identificador provisional interno.",
    )
    id_provisional: Optional[str] = Field(
        default=None,
        description="Identificador interno temporal único cuando no hay placa formal (ej: 'PROV_a1b2c3d4').",
    )
    marca: Optional[str] = Field(default=None, description="Marca automotriz normalizada (ej: 'Toyota').")
    modelo: Optional[str] = Field(default=None, description="Modelo automotriz normalizado (ej: 'Yaris').")
    anio: Optional[int] = Field(default=None, ge=1900, le=2100, description="Año de fabricación.")
    motor: Optional[str] = Field(default=None, description="Cilindrada o código de motor (ej: '1.5', '1NZ-FE').")
    combustible: Optional[str] = Field(default=None, description="Combustible (ej: 'GLP', 'GNV', 'Gasolina', 'Diésel').")
    transmision: Optional[str] = Field(default=None, description="Transmisión (ej: 'manual', 'automatica', 'CVT').")
    kilometraje: Optional[int] = Field(default=None, ge=0, description="Kilometraje reportado.")

    @property
    def placa_efectiva(self) -> Optional[str]:
        """Retorna la placa formal si existe; de lo contrario None (no expone id_provisional como placa real)."""
        return self.placa if not self.es_provisional else None

    @property
    def identificador_taller(self) -> str:
        """Identificador para seguimiento en taller (placa real o id provisional)."""
        return self.placa or self.id_provisional or "NO_IDENTIFICADO"


class HechoClinico(BaseModel):
    """Hecho diagnóstico individual extraído con polaridad y trazabilidad."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    campo: str = Field(..., description="Identificador canónico del hecho (ej: 'sintoma_cascabeleo', 'arranque_lento').")
    valor: str = Field(..., description="Valor semántico (ej: 'cascabeleo al acelerar', 'frío', '12.4 V').")
    polaridad: bool = Field(default=True, description="True si es síntoma confirmado/afirmado; False si es negado/ausente.")
    categoria: str = Field(default="sintoma", description="Categoría: 'sintoma', 'condicion', 'antecedente', 'prueba', 'dtc'.")
    texto_origen: str = Field(default="", description="Fragmento literal del mensaje que originó la extracción.")
    confianza: float = Field(default=1.0, ge=0.0, le=1.0, description="Nivel de certidumbre en la extracción.")


class MedicionTecnica(BaseModel):
    """Lectura física o metrológica aportada en el mensaje."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    tipo: str = Field(..., description="Magnitud medida: 'presion_combustible', 'voltaje_bateria', 'compresion_cilindro'.")
    valor: float = Field(..., description="Valor numérico de la medición.")
    unidad: str = Field(..., description="Unidad de medida: 'PSI', 'bar', 'V', 'mV', 'ohm', 'mm', 'kPa'.")
    contexto: Optional[str] = Field(default=None, description="Condición operacional: 'en_contacto', 'al_dar_arranque', 'en_ralenti'.")


class UserTurnInputDTO(BaseModel):
    """Contrato atómico inmutable que captura TODA la información recibida en un turno."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    mensaje_original: str = Field(..., description="Texto textual recibido desde WhatsApp / API sin alteraciones.")
    mensaje_normalizado: str = Field(..., description="Texto con jerga y espacios normalizados.")
    timestamp: float = Field(default_factory=time.time, description="Marca temporal del turno.")

    # Clasificación de intención
    intencion: IntentType = Field(default=IntentType.INDETERMINADO)
    motivo_intencion: str = Field(default="", description="Justificación técnica de la intención detectada.")

    # Entidades estructuradas del vehículo
    vehiculo: VehiculoIdentificado = Field(default_factory=VehiculoIdentificado)

    # Entidades clínicas separadas por polaridad
    hechos_afirmados: List[HechoClinico] = Field(default_factory=list, description="Síntomas y condiciones presentes.")
    hechos_negados: List[HechoClinico] = Field(default_factory=list, description="Síntomas y fallas descartadas/ausentes.")
    dtcs: List[str] = Field(default_factory=list, description="Códigos de diagnóstico OBD-II válidos (ej: ['P0301']).")
    mediciones: List[MedicionTecnica] = Field(default_factory=list, description="Mediciones físicas extraídas.")

    # Control de diálogo y respuestas cortas
    es_respuesta_corta: bool = Field(default=False)
    valor_respuesta_corta: Optional[str] = Field(default=None)

    # Marcadores de ciclo de vida del caso
    es_correccion_vehiculo: bool = Field(default=False, description="Corrección sobre el mismo auto/caso.")
    es_cambio_caso: bool = Field(default=False, description="Cambio hacia otro vehículo o consulta no relacionada.")

    # Suficiencia de información
    datos_faltantes: List[str] = Field(default_factory=list, description="Entidades obligatorias ausentes para diagnóstico completo.")


class DiagnosticOutputDTO(BaseModel):
    """Contrato de salida para la respuesta diagnóstica hacia WhatsApp / Outbox."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: str = Field(..., description="Decisión: 'PREGUNTAR', 'DIAGNOSTICAR', 'PLAN_B', 'VALIDAR', 'SALUDO'.")
    respuesta_texto: str = Field(..., description="Mensaje formateado y validado para envío por WhatsApp.")
    falla_principal: Optional[str] = Field(default=None, description="Hipótesis diagnóstica primaria (Top 1).")
    confianza_ml: float = Field(default=0.0, ge=0.0, le=1.0, description="Probabilidad de la hipótesis principal.")
    top3_diferencial: List[Dict[str, Any]] = Field(default_factory=list, description="Top 3 de probabilidades ML para comparación técnica.")
    contexto_rag: Optional[str] = Field(default=None, description="Procedimiento y tolerancias del manual de servicio.")
    es_pregunta: bool = Field(default=False)
    pregunta_intent: Optional[str] = Field(default=None)
    caso_id: Optional[str] = Field(default=None)
    ficha_diagnostica_actualizada: bool = Field(default=False)
