"""Rectifica hipótesis y síntomas conservando identidad, evidencia y auditoría."""
import re

from src.core.conversacion.models import ConversationPhase, FactState, FactType


def rectificar_sistema(estado, texto, dominio, estado_operativo):
    for campo, hecho in list(estado.hechos.items()):
        if hecho.tipo == FactType.SINTOMA or campo == "condicion_operacion":
            historico = hecho.to_dict()
            historico.update(estado=FactState.CORREGIDO.value, case_id_origen=estado.case_id,
                             motivo_rectificacion=texto)
            estado.hechos_historicos.append(historico)
            estado.hechos.pop(campo)
    if estado.top3_actual:
        estado.hechos_historicos.append({
            "tipo_evento": "hipotesis_rectificadas", "case_id_origen": estado.case_id,
            "top3": [dict(p) for p in estado.top3_actual], "motivo_rectificacion": texto,
        })
    afirmado = " ".join(c.strip() for c in re.split(r"[.;,]", texto)
                        if c.strip() and not re.search(r"\bno\s+es\b|\bcorrige\b", c, re.IGNORECASE))
    estado.active_symptoms = [afirmado] if afirmado else []
    if afirmado:
        estado.registrar_hecho("sintoma_rectificado", afirmado, categoria="sintoma",
                               texto_crudo=texto, tipo=FactType.SINTOMA)
    estado.active_system = dominio.value
    estado.active_problem_id = None
    estado.top3_actual = []
    estado.falla_principal = None
    estado.confianza_actual = 0.0
    estado.pending_question = None
    estado.pending_test = None
    estado.turnos_repregunta = 0
    estado.fase = ConversationPhase.RECOLECTANDO
    estado.dominio_probable = dominio.value
    estado.estado_operativo = estado_operativo
    estado.last_user_correction = texto
    estado.turno_ultima_correccion = estado.turno_actual + 1
