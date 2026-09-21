"""Modelos y tipos de datos para la memoria conversacional estructurada de CarBot (Fase 9.1)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FactState(str, Enum):
    """Estados clínicos de un hecho observado o declarado."""
    CONFIRMADO = "CONFIRMADO"
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
    DTC_DESCONOCIDO = "DTC_DESCONOCIDO"  # No se ha escaneado o sin escáner disponible


class FactType(str, Enum):
    """Clasificación del hecho según Adenda 9.1."""
    SINTOMA = "SINTOMA"
    CAUSA = "CAUSA"
    CONDICION = "CONDICION"
    MODIFICADOR = "MODIFICADOR"


@dataclass
class DiagnosticFact:
    """Hecho diagnóstico estructurado con trazabilidad y estado clínico."""
    campo: str
    valor: str
    estado: FactState = FactState.CONFIRMADO
    turno_origen: int = 1
    confianza: float = 1.0
    texto_crudo: Optional[str] = None
    categoria: str = "sintoma"
    tipo: FactType = FactType.SINTOMA
    procedencia: str = "inferred"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campo": self.campo,
            "valor": self.valor,
            "estado": self.estado.value,
            "turno_origen": self.turno_origen,
            "confianza": round(self.confianza, 2),
            "texto_crudo": self.texto_crudo,
            "categoria": self.categoria,
            "tipo": self.tipo.value,
            "procedencia": self.procedencia,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DiagnosticFact:
        raw_tipo = d.get("tipo", "SINTOMA")
        if isinstance(raw_tipo, FactType):
            tipo_val = raw_tipo
        else:
            try:
                tipo_val = FactType(str(raw_tipo))
            except (ValueError, TypeError):
                tipo_val = FactType.SINTOMA
        raw_estado = d.get("estado", "CONFIRMADO")
        if isinstance(raw_estado, FactState):
            estado_val = raw_estado
        else:
            try:
                estado_val = FactState(str(raw_estado))
            except (ValueError, TypeError):
                estado_val = FactState.CONFIRMADO
        return cls(
            campo=d["campo"],
            valor=d["valor"],
            estado=estado_val,
            turno_origen=d.get("turno_origen", 1),
            confianza=float(d.get("confianza", 1.0)),
            texto_crudo=d.get("texto_crudo"),
            categoria=d.get("categoria", "sintoma"),
            tipo=tipo_val,
            procedencia=d.get("procedencia", "inferred"),
        )


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
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turno": self.turno,
            "mensaje_original": self.mensaje_original,
            "contexto_previo": self.contexto_previo,
            "hechos_nuevos_extraidos": self.hechos_nuevos_extraidos,
            "hechos_actualizados": self.hechos_actualizados,
            "consulta_consolidada": self.consulta_consolidada,
            "top3": self.top3,
            "confianza": round(self.confianza, 4),
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


@dataclass
class ConversationState:
    """Estado acumulativo estructurado de una sesión conversacional."""
    session_id: str
    case_id: Optional[str] = None
    placa: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[str] = None
    motor: Optional[str] = None
    combustible: Optional[str] = None
    transmision: Optional[str] = None
    fase: ConversationPhase = ConversationPhase.INICIO
    estado_operativo: EstadoOperativo = EstadoOperativo.DESCONOCIDO
    dominio_probable: str = "DESCONOCIDO"
    turno_actual: int = 0
    turnos_repregunta: int = 0
    max_repreguntas: int = 3
    confianza_actual: float = 0.0
    conversation_evidence_level: EvidenceLevel = EvidenceLevel.BAJA
    dtc_status: DtcStatus = DtcStatus.SIN_DTC
    top3_actual: List[Dict[str, Any]] = field(default_factory=list)
    falla_principal: Optional[str] = None
    hipotesis_descartadas: List[str] = field(default_factory=list)
    hechos: Dict[str, DiagnosticFact] = field(default_factory=dict)
    hechos_historicos: List[Dict[str, Any]] = field(default_factory=list)
    herramientas_no_disponibles: List[str] = field(default_factory=list)
    pruebas_no_disponibles: List[Dict[str, Any]] = field(default_factory=list)
    tools_available: List[str] = field(default_factory=list)
    tools_unavailable: List[str] = field(default_factory=list)
    pending_question: Optional[Dict[str, Any]] = None
    pending_test: Optional[Dict[str, Any]] = None
    completed_tests: Dict[str, Any] = field(default_factory=dict)
    measurements: Dict[str, Any] = field(default_factory=dict)
    active_problem_id: Optional[str] = None
    active_system: Optional[str] = None
    active_symptoms: List[str] = field(default_factory=list)
    last_user_correction: Optional[str] = None
    last_diagnostic_action: Optional[str] = None
    preguntas_realizadas: List[Dict[str, Any]] = field(default_factory=list)
    respuestas_obtenidas: List[Dict[str, Any]] = field(default_factory=list)
    historial_mensajes_usuario: List[str] = field(default_factory=list)
    trazabilidad: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def hechos_caso_activo(self) -> Dict[str, DiagnosticFact]:
        """Retorna exclusivamente los hechos pertenecientes al caso activo."""
        return self.hechos

    def obtener_hecho(self, campo: str) -> Optional[DiagnosticFact]:
        return self.hechos.get(campo)

    def obtener_valor_confirmado(self, campo: str) -> Optional[str]:
        hecho = self.hechos.get(campo)
        return hecho.valor if hecho and hecho.estado == FactState.CONFIRMADO else None

    def es_hecho_negado(self, campo: str) -> bool:
        hecho = self.hechos.get(campo)
        return hecho is not None and hecho.estado == FactState.AUSENTE_NEGADO

    def es_hecho_confirmado(self, campo: str) -> bool:
        hecho = self.hechos.get(campo)
        return hecho is not None and hecho.estado == FactState.CONFIRMADO

    def es_hecho_no_revisado(self, campo: str) -> bool:
        hecho = self.hechos.get(campo)
        return hecho is not None and hecho.estado == FactState.NO_REVISADO

    def es_prueba_no_sabe_realizar(self, campo: str = "") -> bool:
        if campo:
            hecho = self.hechos.get(campo)
            return hecho is not None and hecho.estado == FactState.NO_SABE_REALIZAR
        return any(h.estado == FactState.NO_SABE_REALIZAR for h in self.hechos.values())

    def tiene_inspeccion_pendiente(self, patron: str = "") -> bool:
        p = patron.lower()
        return any(
            (h.estado in (FactState.NO_REVISADO, FactState.NO_SABE_REALIZAR) or h.categoria == "inspeccion_pendiente")
            and (not p or p in k.lower() or p in h.valor.lower())
            for k, h in self.hechos.items()
        )

    def obtener_hecho_no_sabe_realizar(self, patron_o_campo: str = "") -> Optional[DiagnosticFact]:
        p = patron_o_campo.lower()
        for k, h in self.hechos.items():
            if h.estado == FactState.NO_SABE_REALIZAR and (not p or p in k.lower() or p in h.valor.lower()):
                return h
        return None

    def obtener_hecho_negado(self, patron_o_campo: str) -> Optional[DiagnosticFact]:
        p = patron_o_campo.lower()
        for k, h in self.hechos.items():
            if h.estado == FactState.AUSENTE_NEGADO and (p in k.lower() or p in h.valor.lower()):
                return h
        return None

    def obtener_hecho_no_revisado(self, patron_o_campo: str) -> Optional[DiagnosticFact]:
        p = patron_o_campo.lower()
        for k, h in self.hechos.items():
            if h.estado == FactState.NO_REVISADO and (p in k.lower() or p in h.valor.lower()):
                return h
        return None

    def bloquear_herramienta(self, her: str) -> None:
        if her not in self.herramientas_no_disponibles:
            self.herramientas_no_disponibles.append(her)
            self.updated_at = time.time()

    def desbloquear_herramienta(self, her: str) -> None:
        if her in self.herramientas_no_disponibles:
            self.herramientas_no_disponibles.remove(her)
            self.pruebas_no_disponibles = [p for p in self.pruebas_no_disponibles if p.get("herramienta") != her]
            self.updated_at = time.time()

    def bloquear_prueba(self, prueba: str, herramienta: str, motivo: str = "sin_herramienta") -> None:
        if not self.es_prueba_bloqueada(prueba):
            self.pruebas_no_disponibles.append({"prueba": prueba, "herramienta": herramienta, "motivo": motivo})
            self.updated_at = time.time()

    def es_prueba_bloqueada(self, prueba: str) -> bool:
        return any(p.get("prueba") == prueba for p in self.pruebas_no_disponibles)

    def ya_preguntado_texto(self, fragmento: str) -> bool:
        frag = fragmento.lower()
        return any(frag in str(p.get("texto", "")).lower() for p in self.preguntas_realizadas)

    def registrar_hecho(
        self,
        campo: str,
        valor: str,
        categoria: str = "sintoma",
        estado: FactState = FactState.CONFIRMADO,
        confianza: float = 1.0,
        texto_crudo: Optional[str] = None,
        tipo: FactType = FactType.SINTOMA,
        procedencia: str = "inferred",
    ) -> DiagnosticFact:
        if isinstance(tipo, FactState):
            estado = tipo
            tipo = FactType.SINTOMA
        if isinstance(estado, FactType):
            tipo = estado
            estado = FactState.CONFIRMADO
        anterior = self.hechos.get(campo)
        if anterior and anterior.estado == FactState.CONFIRMADO and anterior.valor != valor:
            anterior.estado = FactState.CORREGIDO
        hecho = DiagnosticFact(
            campo=campo, valor=valor, estado=estado, turno_origen=self.turno_actual,
            confianza=confianza, texto_crudo=texto_crudo, categoria=categoria, tipo=tipo,
            procedencia=procedencia,
        )
        self.hechos[campo] = hecho
        self.updated_at = time.time()
        return hecho

    def eliminar_hecho(self, campo: str) -> None:
        if campo in self.hechos:
            self.hechos.pop(campo, None)
            self.updated_at = time.time()

    def ya_preguntado(self, intent: QuestionIntent) -> bool:
        return any(p.get("intent") == intent.value for p in self.preguntas_realizadas)

    def veces_preguntado(self, intent: QuestionIntent) -> int:
        return sum(1 for p in self.preguntas_realizadas if p.get("intent") == intent.value)

    def tiene_antecedente_motor_en_marcha(self) -> bool:
        """Indica si existe evidencia de que el motor estuvo en funcionamiento en el episodio reportado."""
        if self.obtener_hecho("antecedente_motor_en_marcha"):
            return True
        if self.estado_operativo in (EstadoOperativo.MARCHA, EstadoOperativo.RALENTI, EstadoOperativo.FRENADO):
            return True
        hechos_marcha = (
            "sintoma_pérdida_de_potencia",
            "sintoma_funcionamiento_irregular___misfire",
            "sintoma_sobrecalentamiento",
            "sintoma_humo_blanco___ebullición_refrigerante",
            "sintoma_alto_consumo_de_combustible",
            "sintoma_anomalía_en_frenos",
        )
        return any(self.obtener_hecho(k) is not None for k in hechos_marcha)

    def registrar_pregunta(
        self,
        intent: QuestionIntent,
        texto: str,
        opciones: Optional[List[str]] = None,
        hipotesis: Optional[List[str]] = None,
        incrementar_repregunta: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        datos_pregunta: Dict[str, Any] = {
            "intent": intent.value if isinstance(intent, QuestionIntent) else str(intent),
            "texto": texto,
            "turno": self.turno_actual,
            "opciones": list(opciones or []),
            "hipotesis": list(hipotesis or []),
            "timestamp": time.time(),
        }
        if metadata:
            datos_pregunta["metadata"] = dict(metadata)
        self.preguntas_realizadas.append(datos_pregunta)
        if incrementar_repregunta:
            self.turnos_repregunta += 1
            self.fase = ConversationPhase.ACLARANDO
        self.updated_at = time.time()

    def registrar_respuesta(self, texto: str, interpretacion: Optional[str] = None) -> None:
        self.respuestas_obtenidas.append({
            "texto": texto,
            "turno": self.turno_actual,
            "interpretacion": interpretacion,
            "timestamp": time.time(),
        })
        self.updated_at = time.time()

    def ultima_pregunta(self) -> Optional[Dict[str, Any]]:
        return self.preguntas_realizadas[-1] if self.preguntas_realizadas else None

    def establecer_pregunta_pendiente(
        self,
        intent: str,
        texto: str = "",
        expected_quantity: Optional[str] = None,
        expected_units: Optional[List[str]] = None,
        related_system: Optional[str] = None,
        related_hypothesis: Optional[str] = None,
    ) -> None:
        self.pending_question = {
            "intent": intent,
            "texto": texto,
            "expected_quantity": expected_quantity,
            "expected_units": list(expected_units or []),
            "related_system": related_system,
            "related_hypothesis": related_hypothesis,
            "asked_turn": self.turno_actual,
            "timestamp": time.time(),
        }
        self.updated_at = time.time()

    def limpiar_pregunta_pendiente(self) -> None:
        self.pending_question = None
        self.pending_test = None
        self.updated_at = time.time()

    def registrar_prueba_completada(
        self,
        prueba: str,
        resultado: str,
        detalles: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.completed_tests[prueba] = resultado
        self.limpiar_pregunta_pendiente()

    def registrar_medicion(
        self,
        tipo: str,
        valor: float,
        unidad: str,
        contexto: Optional[str] = None,
        prueba: Optional[str] = None,
        procedencia: str = "measured",
        estado: str = "observado",
    ) -> Dict[str, Any]:
        med = {
            "tipo": tipo,
            "valor": float(valor),
            "unidad": unidad,
            "contexto": contexto,
            "prueba": prueba or (self.pending_question.get("intent") if self.pending_question else None),
            "estado": estado,
            "turno": self.turno_actual,
            "procedencia": procedencia,
            "timestamp": time.time(),
        }
        self.measurements[tipo] = med
        self.limpiar_pregunta_pendiente()
        return med

    def marcar_herramienta_disponible(self, her: str) -> None:
        h_norm = her.lower().strip()
        if h_norm not in self.tools_available:
            self.tools_available.append(h_norm)
        if h_norm in self.tools_unavailable:
            self.tools_unavailable.remove(h_norm)
        self.desbloquear_herramienta(h_norm)

    def marcar_herramienta_indisponible(self, her: str) -> None:
        h_norm = her.lower().strip()
        if h_norm not in self.tools_unavailable:
            self.tools_unavailable.append(h_norm)
        if h_norm in self.tools_available:
            self.tools_available.remove(h_norm)
        self.bloquear_herramienta(h_norm)

    def es_herramienta_disponible(self, her: str) -> bool:
        return her.lower().strip() in self.tools_available

    def ya_comprobado_o_respondido(self, clave_prueba: str) -> bool:
        c_low = clave_prueba.lower()
        if any(c_low in k.lower() for k in self.completed_tests):
            return True
        if any(c_low in k.lower() for k in self.measurements):
            return True
        if c_low in self.hechos and self.hechos[c_low].estado in (FactState.CONFIRMADO, FactState.DESCONOCIDO):
            return True
        return False

    def _archivar_estado_activo(self) -> None:
        """Conserva el estado específico del caso solo dentro del histórico."""
        if self.hechos and self.case_id:
            ya_archivado = any(h.get("case_id") == self.case_id for h in self.hechos_historicos)
            if not ya_archivado:
                self.hechos_historicos.append({
                    "case_id": self.case_id,
                    "active_problem_id": self.active_problem_id,
                    "estado_operativo": self.estado_operativo.value,
                    "turno_cierre": self.turno_actual,
                    "hechos": [h.to_dict() for h in self.hechos.values()],
                    "completed_tests": dict(self.completed_tests),
                    "measurements": dict(self.measurements),
                    "top3": list(self.top3_actual),
                    "dominio_probable": self.dominio_probable,
                    "preguntas_realizadas": list(self.preguntas_realizadas),
                    "respuestas_obtenidas": list(self.respuestas_obtenidas),
                    "herramientas_no_disponibles": list(self.herramientas_no_disponibles),
                    "pruebas_no_disponibles": list(self.pruebas_no_disponibles),
                    "historial_mensajes_usuario": list(self.historial_mensajes_usuario),
                    "timestamp": time.time(),
                })

    def archivar_caso_actual(self, nuevo_case_id: Optional[str] = None) -> str:
        """Archiva los hechos del caso activo en el historial y genera un nuevo case_id limpio."""
        self._archivar_estado_activo()
        nuevo_id = nuevo_case_id or str(uuid.uuid4())
        self.iniciar_nuevo_caso(nuevo_id)
        return nuevo_id

    def iniciar_nuevo_caso(self, case_id: Optional[str] = None) -> None:
        """Inicia un nuevo caso diagnóstico limpiando hechos y manteniendo trazabilidad."""
        self._archivar_estado_activo()
        self.case_id = case_id or str(uuid.uuid4())
        self.active_problem_id = str(uuid.uuid4())
        self.active_system = None
        self.active_symptoms.clear()
        self.pending_question = None
        self.pending_test = None
        self.completed_tests.clear()
        self.measurements.clear()
        self.last_user_correction = None
        self.last_diagnostic_action = None
        self.fase = ConversationPhase.INICIO
        self.estado_operativo = EstadoOperativo.DESCONOCIDO
        self.dominio_probable = "DESCONOCIDO"
        self.turno_actual = 0
        self.turnos_repregunta = 0
        self.confianza_actual = 0.0
        self.conversation_evidence_level = EvidenceLevel.BAJA
        self.dtc_status = DtcStatus.SIN_DTC
        self.top3_actual = []
        self.falla_principal = None
        self.hipotesis_descartadas = []
        self.hechos.clear()
        self.herramientas_no_disponibles.clear()
        self.pruebas_no_disponibles.clear()
        self.preguntas_realizadas.clear()
        self.respuestas_obtenidas.clear()
        self.historial_mensajes_usuario.clear()
        self.updated_at = time.time()

    def reiniciar(self) -> None:
        """Limpia el estado conversacional para iniciar un nuevo vehículo."""
        self.case_id, self.placa, self.marca, self.modelo = None, None, None, None
        self.anio, self.motor, self.combustible, self.transmision = None, None, None, None
        self.active_problem_id = None
        self.active_system = None
        self.active_symptoms.clear()
        self.pending_question = None
        self.pending_test = None
        self.completed_tests.clear()
        self.measurements.clear()
        self.tools_available.clear()
        self.tools_unavailable.clear()
        self.last_user_correction = None
        self.last_diagnostic_action = None
        self.fase, self.estado_operativo = ConversationPhase.INICIO, EstadoOperativo.DESCONOCIDO
        self.dominio_probable = "DESCONOCIDO"
        self.turno_actual, self.turnos_repregunta = 0, 0
        self.confianza_actual, self.conversation_evidence_level = 0.0, EvidenceLevel.BAJA
        self.dtc_status = DtcStatus.SIN_DTC
        self.top3_actual.clear()
        self.hipotesis_descartadas.clear()
        self.hechos.clear()
        self.hechos_historicos.clear()
        self.herramientas_no_disponibles.clear()
        self.pruebas_no_disponibles.clear()
        self.preguntas_realizadas.clear()
        self.respuestas_obtenidas.clear()
        self.historial_mensajes_usuario.clear()
        self.trazabilidad.clear()
        self.updated_at = time.time()

    def exportar_dict(self, incluir_trazabilidad: bool = True) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "case_id": self.case_id,
            "active_problem_id": self.active_problem_id,
            "active_system": self.active_system,
            "active_symptoms": list(self.active_symptoms),
            "pending_question": dict(self.pending_question) if self.pending_question else None,
            "pending_test": dict(self.pending_test) if self.pending_test else None,
            "completed_tests": dict(self.completed_tests),
            "measurements": dict(self.measurements),
            "tools_available": list(self.tools_available),
            "tools_unavailable": list(self.tools_unavailable),
            "last_user_correction": self.last_user_correction,
            "last_diagnostic_action": self.last_diagnostic_action,
            "hipotesis_descartadas": list(self.hipotesis_descartadas),
            "placa": self.placa,
            "marca": self.marca,
            "modelo": self.modelo,
            "anio": self.anio,
            "motor": self.motor,
            "combustible": self.combustible,
            "transmision": self.transmision,
            "fase": self.fase.value,
            "estado_operativo": self.estado_operativo.value,
            "dominio_probable": self.dominio_probable,
            "turno_actual": self.turno_actual,
            "turnos_repregunta": self.turnos_repregunta,
            "max_repreguntas": self.max_repreguntas,
            "confianza_actual": self.confianza_actual,
            "conversation_evidence_level": self.conversation_evidence_level.value,
            "dtc_status": self.dtc_status.value,
            "top3_actual": list(self.top3_actual),
            "hechos": {k: v.to_dict() for k, v in self.hechos.items()},
            "hechos_historicos": list(self.hechos_historicos),
            "herramientas_no_disponibles": list(self.herramientas_no_disponibles),
            "pruebas_no_disponibles": list(self.pruebas_no_disponibles),
            "preguntas_realizadas": list(self.preguntas_realizadas),
            "respuestas_obtenidas": list(self.respuestas_obtenidas),
            "historial_mensajes_usuario": list(self.historial_mensajes_usuario),
            "trazabilidad": list(self.trazabilidad[-15:]) if incluir_trazabilidad else [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationState:
        state = cls(
            session_id=data.get("session_id", "default"),
            case_id=data.get("case_id"),
            placa=data.get("placa"),
            marca=data.get("marca"),
            modelo=data.get("modelo"),
            anio=data.get("anio"),
            motor=data.get("motor"),
            combustible=data.get("combustible"),
            transmision=data.get("transmision"),
            fase=ConversationPhase(data.get("fase", "INICIO")),
            estado_operativo=EstadoOperativo(data.get("estado_operativo", "DESCONOCIDO")),
            dominio_probable=str(data.get("dominio_probable", "DESCONOCIDO")),
            turno_actual=int(data.get("turno_actual", 0)),
            turnos_repregunta=int(data.get("turnos_repregunta", 0)),
            max_repreguntas=int(data.get("max_repreguntas", 3)),
            confianza_actual=float(data.get("confianza_actual", 0.0)),
            conversation_evidence_level=EvidenceLevel(data.get("conversation_evidence_level", "BAJA")),
            dtc_status=DtcStatus(data.get("dtc_status", "SIN_DTC")),
            top3_actual=list(data.get("top3_actual") or []),
            hipotesis_descartadas=list(data.get("hipotesis_descartadas") or []),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
        )
        state.active_problem_id = data.get("active_problem_id")
        state.active_system = data.get("active_system")
        state.active_symptoms = list(data.get("active_symptoms") or [])
        state.pending_question = data.get("pending_question")
        state.pending_test = data.get("pending_test")
        state.completed_tests = dict(data.get("completed_tests") or {})
        state.measurements = dict(data.get("measurements") or {})
        state.tools_available = list(data.get("tools_available") or [])
        state.tools_unavailable = list(data.get("tools_unavailable") or [])
        state.last_user_correction = data.get("last_user_correction")
        state.last_diagnostic_action = data.get("last_diagnostic_action")
        for k, v in (data.get("hechos") or {}).items():
            state.hechos[k] = DiagnosticFact.from_dict(v)
        state.hechos_historicos = list(data.get("hechos_historicos") or [])
        state.herramientas_no_disponibles = list(data.get("herramientas_no_disponibles") or [])
        state.pruebas_no_disponibles = list(data.get("pruebas_no_disponibles") or [])
        state.preguntas_realizadas = list(data.get("preguntas_realizadas") or [])
        state.respuestas_obtenidas = list(data.get("respuestas_obtenidas") or [])
        state.historial_mensajes_usuario = list(data.get("historial_mensajes_usuario") or [])
        state.trazabilidad = list((data.get("trazabilidad") or [])[-15:])
        return state
