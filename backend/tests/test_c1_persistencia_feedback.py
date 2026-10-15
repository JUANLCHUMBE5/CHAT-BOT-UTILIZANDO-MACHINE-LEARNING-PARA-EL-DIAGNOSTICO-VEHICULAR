"""Regresión: la abstención no solicita confirmación de una falla hipotética."""

from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.services.webhook.diagnostic_persister import DiagnosticPersister


def _dto(**extra):
    return ResultadoDiagnostico(
        respuesta_texto="Falta evidencia objetiva",
        diagnostico_ml="Indeterminado",
        confianza_ml=0.0,
        contexto_manual="",
        titulo_manual="",
        **extra,
    )


def test_abstencion_no_solicita_feedback_si_no_hay_confirmacion_fisica():
    assert not DiagnosticPersister.debe_solicitar_feedback(
        _dto(motivo_abstencion="SIN_VOCABULARIO_TFIDF")
    )
    assert not DiagnosticPersister.debe_solicitar_feedback(
        _dto(motivo_abstencion="EVIDENCIA_INSUFICIENTE")
    )


def test_orientacion_provisional_no_solicita_feedback():
    assert not DiagnosticPersister.debe_solicitar_feedback(
        _dto(es_orientacion_provisional=True)
    )
