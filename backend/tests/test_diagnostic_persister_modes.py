"""Regresiones para los modos persistidos por el webhook."""

from types import SimpleNamespace

from src.core.services.webhook.diagnostic_persister import DiagnosticPersister


def test_estado_conversacional_completo_se_persiste_como_fallback_ml_rag() -> None:
    dto = SimpleNamespace(modo_diagnostico="completo", llm_usado=False)

    assert DiagnosticPersister._modo_diagnostico_persistible(dto) == "diagnostico_degradado_ml_rag"


def test_sintesis_llm_se_persiste_como_modo_completo_valido() -> None:
    dto = SimpleNamespace(modo_diagnostico="completo", llm_usado=True)

    assert DiagnosticPersister._modo_diagnostico_persistible(dto) == "completo_ml_rag_llm"


def test_modo_esperando_clarificacion_se_conserva() -> None:
    dto = SimpleNamespace(modo_diagnostico="esperando_clarificacion", llm_usado=False)

    assert DiagnosticPersister._modo_diagnostico_persistible(dto) == "esperando_clarificacion"
