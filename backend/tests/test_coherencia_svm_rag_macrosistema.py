"""Test de coherencia arquitectónica entre el clasificador SVM y el recuperador RAG.

Garantiza que:
1. No se recuperen ni inyecten procedimientos de macrosistemas incompatibles (e.g., TRANSMISIÓN vs SUSPENSIÓN).
2. Se permita la afinidad técnica legítima (e.g., MOTOR <-> TRANSMISIÓN en tren motriz).
3. Las probabilidades del clasificador SVM se preserven intactas en el contrato de respuesta.
"""

from __future__ import annotations

import pytest

from src.core.diagnostico.rag_hypothesis_compatibility import procedimiento_apoya_hipotesis
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture(scope="module")
def gestor():
    return GestorDiagnostico()


def test_rechazo_procedimiento_macrosistema_incompatible():
    """Valida que una hipótesis de TRANSMISIÓN rechace formalmente un manual de SUSPENSIÓN_CHASIS."""
    meta_incompatible = {
        "sistema": "SUSPENSION_CHASIS",
        "system": "SUSPENSION_CHASIS",
        "falla": "Rodajes de caja mecanica o diferencial gastados",  # Metadato documental erróneo
    }
    # La hipótesis canónica pertenece a TRANSMISION
    apoya = procedimiento_apoya_hipotesis(
        hipotesis="Rodajes de caja mecanica o diferencial gastados",
        titulo="PROCEDIMIENTO: DIAGNÓSTICO METROLÓGICO DE RODAMIENTOS DE RUEDA / MAZA",
        meta=meta_incompatible,
    )
    assert apoya is False, "El procedimiento de suspensión debió ser rechazado para una falla de transmisión."


def test_aprobacion_procedimiento_macrosistema_compatible():
    """Valida que hipótesis de MOTOR y TRANSMISIÓN aprueben manuales de sus respectivos macrosistemas."""
    meta_motor = {
        "sistema": "MOTOR",
        "system": "MOTOR",
        "falla": "Falla de encendido (misfire) en cilindro por bujia o bobina defectuosa",
    }
    apoya_motor = procedimiento_apoya_hipotesis(
        hipotesis="Falla de encendido (misfire) en cilindro por bujia o bobina defectuosa",
        titulo="PROCEDIMIENTO: DIAGNÓSTICO DE MISFIRE",
        meta=meta_motor,
    )
    assert apoya_motor is True

    meta_transmision = {
        "sistema": "TRANSMISION",
        "system": "TRANSMISION",
        "falla": "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
    }
    apoya_trans = procedimiento_apoya_hipotesis(
        hipotesis="Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        titulo="PROCEDIMIENTO: DIAGNÓSTICO DE TRANSMISIÓN ROBOTIZADA",
        meta=meta_transmision,
    )
    assert apoya_trans is True


def test_recuperacion_hibrida_filtra_candidatos_incompatibles(gestor):
    """Caso ablación #29: Consulta con predicción TRANSMISIÓN no debe recuperar ficha de SUSPENSIÓN."""
    consulta = "Zumbido tipo avión u oscilación sorda que aumenta en curvas hacia un lado específico de la rueda"
    macro = gestor.modelo_ml.predecir_sistema(consulta)
    top_fallas = gestor.modelo_ml.predecir_top_fallas(consulta, limite=3)

    _, titulo, sim, meta = gestor.motor_rag.recuperar_procedimiento_hibrido(
        consulta=consulta,
        macro_sistema=macro,
        top_fallas=top_fallas,
    )

    doc_sistema = (meta.get("sistema") or meta.get("system") or "").strip().upper()
    assert doc_sistema != "SUSPENSION_CHASIS", f"RAG retornó procedimiento incompatible de {doc_sistema}"
    if macro == "TRANSMISION":
        assert titulo in ("Coincidencia baja", "Sin procedimiento compatible verificado") or sim < 0.12


def test_preservacion_probabilidades_svm_ante_rag_incompatible(gestor):
    """Verifica que el filtrado de RAG no altere las probabilidades entregadas por el pipeline de ML."""
    consulta = "Zumbido tipo avión u oscilación sorda que aumenta en curvas hacia un lado específico de la rueda"
    resultado = gestor.procesar_consulta_texto(consulta)

    # La confianza devuelta debe coincidir exactamente con la probabilidad de la hipótesis Top-1 devuelta por ML
    assert len(resultado.predicciones_ml) > 0
    assert round(resultado.confianza_ml, 4) == round(resultado.predicciones_ml[0].probabilidad, 4)
    assert resultado.diagnostico_ml == resultado.predicciones_ml[0].falla
    # El título del RAG debe indicar coincidencia baja o procedimiento no compatible
    assert resultado.titulo_manual in ("Coincidencia baja", "Sin procedimiento compatible verificado")
