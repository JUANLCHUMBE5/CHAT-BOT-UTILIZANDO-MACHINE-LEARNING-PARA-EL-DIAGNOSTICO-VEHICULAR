"""Regresión del contrato de abstención C1, sin alterar artefactos ML."""

from src.core.diagnostico.models import ResultadoDiagnostico


def test_abstencion_no_confirma_averia_ni_inventa_probabilidad():
    for motivo in (
        "SIN_VOCABULARIO_TFIDF",
        "FUERA_DE_ALCANCE",
        "EVIDENCIA_INSUFICIENTE",
        "SISTEMA_AMBIGUO",
    ):
        resultado = ResultadoDiagnostico(
            respuesta_texto="Solicitar aclaración",
            diagnostico_ml="Indeterminado",
            confianza_ml=0.0,
            contexto_manual="",
            titulo_manual="",
            requiere_revision_humana=True,
            motivo_abstencion=motivo,
        )
        assert resultado.predicciones_ml == []
        assert resultado.predicciones_svm_raw == []
        assert resultado.confianza_ml == 0.0
        assert resultado.motivo_abstencion == motivo


def test_raw_no_se_interpreta_como_confirmacion_fisica():
    resultado = ResultadoDiagnostico(
        respuesta_texto="Requiere inspección presencial",
        diagnostico_ml="Hipótesis provisional",
        confianza_ml=0.4,
        contexto_manual="",
        titulo_manual="",
        requiere_revision_humana=True,
        predicciones_svm_raw=[{"falla": "Bobina", "probabilidad": 0.9}],
        es_orientacion_provisional=True,
    )
    assert resultado.predicciones_svm_raw[0].probabilidad == 0.9
    assert resultado.requiere_revision_humana is True
    assert resultado.es_orientacion_provisional is True
