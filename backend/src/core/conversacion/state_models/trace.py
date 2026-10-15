"""Registro de trazabilidad y auditoría de turnos conversacionales."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TurnTrace:
    """Registro de auditoría detallado por cada turno de WhatsApp."""
    turno: int
    mensaje_original: str
    contexto_previo: Dict[str, Any]
    decision: str  # PREGUNTAR | DIAGNOSTICAR | DIFERENCIAL
    motivo_decision: str
    respuesta_enviada: str
    hechos_nuevos_extraidos: List[Dict[str, Any]] = field(default_factory=list)
    hechos_actualizados: List[Dict[str, Any]] = field(default_factory=list)
    consulta_consolidada: str = ""
    top3: List[Dict[str, Any]] = field(default_factory=list)
    confianza: float = 0.0
    origen_confianza: str = "NO_REGISTRADO"
    evidence_level: str = "BAJA"
    dtc_status: str = "SIN_DTC"
    estado_operativo: str = "DESCONOCIDO"
    question_intent: Optional[str] = None
    preguntas_candidatas: List[Dict[str, Any]] = field(default_factory=list)
    preguntas_descartadas: List[Dict[str, Any]] = field(default_factory=list)
    pregunta_final: Optional[str] = None
    top3_ml_raw: Optional[List[Dict[str, Any]]] = None
    hipotesis_rechazadas_usuario: List[str] = field(default_factory=list)
    nueva_evidencia: Optional[str] = None
    hipotesis_final_presentada: Optional[List[Dict[str, Any]]] = None
    exclusiones_compatibilidad: List[Dict[str, Any]] = field(default_factory=list)
    scores_presentacion: Optional[List[Dict[str, Any]]] = None
    estado_previo: Optional[str] = None
    estado_detectado_mensaje_actual: Optional[str] = None
    decision_transicion: Optional[str] = None
    motivo_transicion: Optional[str] = None
    dominio_previo: Optional[str] = None
    dominio_detectado_actual: Optional[str] = None
    dominio_actual: Optional[str] = None
    plan_b_activado: Optional[str] = None
    herramientas_bloqueadas: List[str] = field(default_factory=list)
    version_orquestador: str = "9.13.0"
    tipo_mensaje: str = "sintoma_nuevo"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turno": self.turno,
            "mensaje_original": self.mensaje_original,
            "tipo_mensaje": self.tipo_mensaje,
            "contexto_previo": self.contexto_previo,
            "hechos_nuevos_extraidos": self.hechos_nuevos_extraidos,
            "hechos_actualizados": self.hechos_actualizados,
            "consulta_consolidada": self.consulta_consolidada,
            "top3": self.top3,
            "confianza": round(self.confianza, 4),
            "origen_confianza": self.origen_confianza,
            "decision": self.decision,
            "motivo_decision": self.motivo_decision,
            "respuesta_enviada": self.respuesta_enviada,
            "evidence_level": self.evidence_level,
            "dtc_status": self.dtc_status,
            "estado_operativo": self.estado_operativo,
            "question_intent": self.question_intent,
            "preguntas_candidatas": list(self.preguntas_candidatas),
            "preguntas_descartadas": list(self.preguntas_descartadas),
            "pregunta_final": self.pregunta_final,
            "top3_ml_raw": self.top3_ml_raw,
            "scores_presentacion": self.scores_presentacion,
            "hipotesis_rechazadas_usuario": list(self.hipotesis_rechazadas_usuario),
            "nueva_evidencia": self.nueva_evidencia,
            "hipotesis_final_presentada": self.hipotesis_final_presentada,
            "exclusiones_compatibilidad": list(self.exclusiones_compatibilidad),
            "estado_previo": self.estado_previo,
            "estado_detectado_mensaje_actual": self.estado_detectado_mensaje_actual,
            "decision_transicion": self.decision_transicion,
            "motivo_transicion": self.motivo_transicion,
            "dominio_previo": self.dominio_previo,
            "dominio_detectado_actual": self.dominio_detectado_actual,
            "dominio_actual": self.dominio_actual,
            "plan_b_activado": self.plan_b_activado,
            "herramientas_bloqueadas": list(self.herramientas_bloqueadas),
            "version_orquestador": self.version_orquestador,
            "timestamp": self.timestamp,
        }
