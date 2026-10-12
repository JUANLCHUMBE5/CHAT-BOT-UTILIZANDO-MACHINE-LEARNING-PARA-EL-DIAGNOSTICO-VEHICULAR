"""Estado acumulativo estructurado de una sesión conversacional de CarBot."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core.conversacion.state_models.enums import (
    ConversationPhase,
    DtcStatus,
    EstadoOperativo,
    EvidenceLevel,
    FactState,
    FactType,
    QuestionIntent,
)
from src.core.conversacion.state_models.facts import DiagnosticFact


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
    turno_ultima_correccion: Optional[int] = None
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
            self.hechos_historicos.append(anterior.to_dict())
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

    @property
    def historial_respuestas(self) -> List[Dict[str, Any]]:
        """Alias retrocompatible de respuestas_obtenidas para trazabilidad y auditorías."""
        return self.respuestas_obtenidas

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
        tiene_estado = bool(
            self.hechos
            or self.active_symptoms
            or self.top3_actual
            or self.preguntas_realizadas
            or self.pending_question
        )
        if not self.case_id or not tiene_estado:
            return

        snapshot = self.exportar_dict()
        snapshot.pop("hechos_historicos", None)
        snapshot["turno_cierre"] = self.turno_actual
        snapshot["timestamp"] = time.time()
        for indice, archivado in enumerate(self.hechos_historicos):
            if archivado.get("case_id") == self.case_id:
                self.hechos_historicos[indice] = snapshot
                break
        else:
            self.hechos_historicos.append(snapshot)

    def archivar_caso_actual(
        self,
        nuevo_case_id: Optional[str] = None,
        preservar_vehiculo: bool = False,
    ) -> str:
        """Archiva los hechos del caso activo en el historial y genera un nuevo case_id limpio."""
        self._archivar_estado_activo()
        nuevo_id = nuevo_case_id or str(uuid.uuid4())
        self.iniciar_nuevo_caso(nuevo_id, preservar_vehiculo=preservar_vehiculo)
        return nuevo_id

    def iniciar_nuevo_caso(
        self,
        case_id: Optional[str] = None,
        preservar_vehiculo: bool = False,
    ) -> None:
        """Archiva el caso activo y crea otro sin transferir evidencia diagnóstica."""
        self._archivar_estado_activo()
        vehiculo = {
            campo: getattr(self, campo)
            for campo in ("placa", "marca", "modelo", "anio", "motor", "combustible", "transmision")
        } if preservar_vehiculo else {}
        self.case_id = case_id or str(uuid.uuid4())
        self.active_problem_id = str(uuid.uuid4())
        self.active_system = None
        self.active_symptoms.clear()
        self.pending_question = None
        self.pending_test = None
        self.completed_tests.clear()
        self.measurements.clear()
        self.last_user_correction = None
        self.turno_ultima_correccion = None
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
        self.tools_available.clear()
        self.tools_unavailable.clear()
        self.preguntas_realizadas.clear()
        self.respuestas_obtenidas.clear()
        self.historial_mensajes_usuario.clear()
        self.trazabilidad.clear()
        self.placa = None
        self.marca = None
        self.modelo = None
        self.anio = None
        self.motor = None
        self.combustible = None
        self.transmision = None
        if preservar_vehiculo:
            for campo, valor in vehiculo.items():
                setattr(self, campo, valor)
        self.updated_at = time.time()

    def restaurar_caso_archivado(self, case_id: str) -> bool:
        """Reabre solo una instantánea histórica identificada explícitamente."""
        if not case_id:
            return False
        snapshot = next(
            (caso for caso in reversed(self.hechos_historicos) if caso.get("case_id") == case_id),
            None,
        )
        if not snapshot:
            return False
        if self.case_id == case_id:
            return True

        self._archivar_estado_activo()
        historial = list(self.hechos_historicos)
        estado_restaurado = type(self).from_dict(snapshot)
        estado_restaurado.session_id = self.session_id
        estado_restaurado.hechos_historicos = historial
        estado_restaurado.updated_at = time.time()
        self.__dict__.update(estado_restaurado.__dict__)
        return True

    def reiniciar(self) -> None:
        """Limpia el caso activo y conserva los diagnósticos previos en el historial."""
        self._archivar_estado_activo()
        historial = list(self.hechos_historicos)
        estado_vacio = type(self)(session_id=self.session_id)
        estado_vacio.hechos_historicos = historial
        self.__dict__.update(estado_vacio.__dict__)

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
            "turno_ultima_correccion": self.turno_ultima_correccion,
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
            "falla_principal": self.falla_principal,
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
        state.falla_principal = data.get("falla_principal")
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
        state.turno_ultima_correccion = data.get("turno_ultima_correccion")
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
