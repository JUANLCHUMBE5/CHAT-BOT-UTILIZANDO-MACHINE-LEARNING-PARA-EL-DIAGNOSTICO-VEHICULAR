"""Contratos tipados para la comprensión semántica con LLM y orquestación inteligente."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class IntencionConversacional(str, Enum):
    """Intenciones reconocibles en los mensajes del mecánico."""
    REPORTAR_SINTOMA = "reportar_sintoma"
    ACLARAR_COMPROBACION = "aclarar_comprobacion"
    SOLICITAR_ALTERNATIVAS = "solicitar_alternativas"
    CONSULTAR_CAUSA_O_EXPLICACION = "consultar_causa_o_explicacion"
    CONSULTAR_PROCEDIMIENTO = "consultar_procedimiento"
    CONSULTAR_TOLERANCIA_OEM = "consultar_tolerancia_oem"
    CONTINUAR_CASO = "continuar_caso"
    NUEVO_CASO = "nuevo_caso"
    REANUDAR_CASO = "reanudar_caso"
    CORREGIR_DATO = "corregir_dato"
    SALUDO = "saludo"
    AGRADECIMIENTO_O_CIERRE = "agradecimiento_o_cierre"
    CONFIRMAR_HIPOTESIS = "confirmar_hipotesis"
    DESCARTAR_HIPOTESIS = "descartar_hipotesis"
    CONSULTAR_MEMORIA = "consultar_memoria"
    OTRO = "otro"


class EstadoHechoSemantico(str, Enum):
    """Estados admisibles para un hecho técnico."""
    CONFIRMADO = "CONFIRMADO"
    NO_REVISADO = "NO_REVISADO"        # Declarado explícitamente como no probado/no realizado aún
    DESCARTADO = "DESCARTADO"          # Descartado o comprobado con prueba física / medición
    REEMPLAZADO = "REEMPLAZADO"        # Componente reemplazado/nuevo como antecedente técnico
    AUSENTE_NEGADO = "AUSENTE_NEGADO"  # Síntoma o herramienta negada (ej: "sin vibración", "no tengo manómetro")
    DESCONOCIDO = "DESCONOCIDO"


class TipoHechoSemantico(str, Enum):
    """Categoría ontológica del hecho."""
    SINTOMA = "sintoma"
    CONDICION = "condicion"
    COMPROBACION = "comprobacion"
    VEHICULO = "vehiculo"
    HERRAMIENTA = "herramienta"


class HechoSemantico(BaseModel):
    """Representación normalizada de un hecho extraído semánticamente."""
    tipo: TipoHechoSemantico = Field(
        default=TipoHechoSemantico.SINTOMA,
        description="Categoría ontológica: sintoma, condicion, comprobacion, vehiculo, herramienta"
    )
    campo: str = Field(
        ...,
        description="Identificador normalizado (ej: 'bomba_combustible', 'pastillas_freno', 'aceleracion_subida')"
    )
    valor: str = Field(
        ...,
        description="Descripción textual clara del hecho o hallazgo"
    )
    estado: EstadoHechoSemantico = Field(
        default=EstadoHechoSemantico.CONFIRMADO,
        description="CONFIRMADO, NO_REVISADO, DESCARTADO, REEMPLAZADO, AUSENTE_NEGADO, DESCONOCIDO"
    )
    evidencia_texto: str = Field(
        default="",
        description="Fragmento textual exacto del mensaje que sustenta este hecho"
    )

    @field_validator("tipo", mode="before")
    @classmethod
    def _normalizar_tipo(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_norm = v.strip().lower()
            return v_norm
        return v

    @field_validator("estado", mode="before")
    @classmethod
    def _normalizar_estado(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_norm = v.strip().upper()
            return v_norm
        return v


class InterpretacionSemantica(BaseModel):
    """Interpretación estructurada validada devuelta por el LLM o el fallback."""
    intenciones: List[str] = Field(
        default_factory=list,
        description="Lista de intenciones conversacionales detectadas en el mensaje"
    )
    hechos_nuevos: List[HechoSemantico] = Field(
        default_factory=list,
        description="Nuevos hechos técnicos identificados en el mensaje"
    )
    pregunta_tecnica_usuario: Optional[str] = Field(
        default=None,
        description="Pregunta explícita realizada por el mecánico (si existe)"
    )
    solicita_causas_alternativas: bool = Field(
        default=False,
        description="True si el mecánico pide qué otras causas podrían explicar la falla"
    )
    solicita_nuevo_caso: bool = Field(
        default=False,
        description="True si solicita iniciar un caso nuevo o cambiar de vehículo"
    )
    solicita_continuar: bool = Field(
        default=False,
        description="True si pide continuar el mismo caso sin reiniciar"
    )
    datos_vehiculo: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Datos de vehículo mencionados en este mensaje (marca, modelo, anio, placa)"
    )
    requiere_aclaracion: bool = Field(
        default=False,
        description="True si el mensaje es completamente ambiguo o ininteligible"
    )
    explicacion_resumida: str = Field(
        default="",
        description="Breve resumen de lo que el mecánico está comunicando o preguntando"
    )
    confianza_interpretacion: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nivel de certeza en la comprensión (0.0 a 1.0)"
    )
    origen: str = Field(
        default="llm_groq",
        description="Origen de la interpretación: 'llm_groq', 'llm_gemini', 'heuristica_fallback'"
    )
    latencia_ms: float = Field(
        default=0.0,
        description="Latencia de inferencia en milisegundos"
    )
