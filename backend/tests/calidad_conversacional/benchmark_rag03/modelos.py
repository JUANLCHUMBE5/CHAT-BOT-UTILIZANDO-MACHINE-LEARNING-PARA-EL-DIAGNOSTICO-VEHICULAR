"""Tipos compartidos del evaluador de desarrollo."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TurnoEsperado:
    mensaje_usuario: str
    intencion_esperada: str
    comportamiento_esperado: str
    debe_contener: List[str] = field(default_factory=list)
    no_debe_contener: List[str] = field(default_factory=list)
    es_pregunta_esperada: Optional[bool] = None
    es_seguridad_critica: bool = False
    es_plan_b: bool = False
    es_abstencion_o_provisional: bool = False


@dataclass
class EscenarioConversacional:
    id: str
    categoria: str
    titulo: str
    vehiculo_inicial: Dict[str, Optional[str]]
    turnos: List[TurnoEsperado]
    severidad_falla: str = "MEDIA"


@dataclass
class ResultadoTurnoAuditoria:
    numero_turno: int
    mensaje_usuario: str
    intencion_esperada: str
    comportamiento_esperado: str
    respuesta_obtenida: str
    decision_orquestador: str
    status_orquestador: str
    tiempo_ms: float
    es_pregunta_obtenida: bool
    diagnostico_ml: str
    confianza_ml: float
    resultado_pass: bool
    evidencia_fallo: Optional[str] = None
    severidad_fallo: Optional[str] = None


@dataclass
class ResultadoEscenarioAuditoria:
    id: str
    categoria: str
    titulo: str
    vehiculo_inicial: Dict[str, Optional[str]]
    turnos: List[ResultadoTurnoAuditoria]
    resultado_global_pass: bool
    severidad_maxima: str
    retencion_vehiculo_ok: bool
    retencion_sintomas_ok: bool
    pertinencia_preguntas_ok: bool
    preguntas_repetidas: int
    deteccion_intencion_ok: bool
    continuidad_turnos_ok: bool
    coherencia_diferencial_ok: bool
    manejo_incertidumbre_ok: bool
    orientacion_alternativa_ok: bool
    seguridad_cumplida_ok: bool
    utilidad_practica_ok: bool
