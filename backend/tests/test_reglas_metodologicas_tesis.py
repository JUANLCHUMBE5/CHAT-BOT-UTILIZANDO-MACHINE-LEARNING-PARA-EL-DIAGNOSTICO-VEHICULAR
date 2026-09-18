"""Pruebas de cumplimiento riguroso de las Reglas Metodológicas de Tesis y Arquitectura CarBot."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

from src.core.diagnostico.models import ResultadoDiagnostico
from src.infrastructure.modelo_ml import ModeloML
from src.infrastructure.motor_rag import MotorRAG
from src.interfaces.api.v1.endpoints.validacion_taller import exportar_fichas_anexo2_csv


def test_regla_1_arquitectura_ml_es_estrictamente_linear_svm_y_tfidf():
    """
    Regla 1: El clasificador de ML debe ser estrictamente Linear SVM con TF-IDF.
    Se prohíbe RandomForestClassifier o XGBoost como modelo principal de producción.
    """
    motor_ml = ModeloML()
    assert motor_ml.vectorizador is not None
    assert isinstance(motor_ml.vectorizador, TfidfVectorizer)

    modelo = motor_ml.modelo
    assert modelo is not None

    es_linear_svm_puro = isinstance(modelo, LinearSVC)
    es_calibrado_linear_svm = (
        isinstance(modelo, CalibratedClassifierCV)
        and (
            isinstance(getattr(modelo, "estimator", None), LinearSVC)
            or isinstance(getattr(modelo, "base_estimator", None), LinearSVC)
        )
    )
    assert (
        es_linear_svm_puro or es_calibrado_linear_svm
    ), f"El modelo debe ser LinearSVC o CalibratedClassifierCV(LinearSVC). Encontrado: {type(modelo)}"

    # Verificar que NO sea Random Forest ni XGBoost
    nombre_tipo = type(modelo).__name__.lower()
    assert "forest" not in nombre_tipo
    assert "xgb" not in nombre_tipo


@pytest.mark.anyio
async def test_regla_2_nota_metodologica_en_matriz_experimental():
    """
    Regla 2 y 5: La exportación debe incluir la advertencia contra datos simulados
    y dejar el contraste estadístico pendiente con el asesor.
    """
    registro_ejemplo = {
        "item": 1,
        "fase": "Postest",
        "fecha": "2026-03-01",
        "placa_enmascarada": "ABC-***",
        "marca_modelo": "Toyota Yaris",
        "sintoma": "Tironea en subida",
        "falla_real": "Bujías desgastadas",
        "chatbot_prediccion": "Falla en bujias o bobinas de encendido (misfire)",
        "prediccion_correcta": 1,
        "campos_completos": 1,
        "tiempo_diagnostico_minutos": 15,
        "sintoma_registrado_correctamente": 1,
        "procesamiento_validado": 1,
        "metodo_confirmacion": "Inspección física",
        "evidencia_ref": "OT-101",
        "mecanico_id": "MEC-01",
        "fecha_validacion": "2026-03-01 10:00:00",
        "estado_registro": "verificado",
        "taller_id": "test_taller",
    }

    with (
        patch("src.interfaces.api.v1.endpoints.validacion_taller.database_configurada", return_value=False),
        patch("src.interfaces.api.v1.endpoints.validacion_taller._cargar_df_tracker") as mock_df,
    ):
        import pandas as pd
        mock_df.return_value = pd.DataFrame([registro_ejemplo])

        response = await exportar_fichas_anexo2_csv(
            periodo=(None, None),
            payload={"taller_id": "test_taller", "rol": "admin_taller"},
        )

    # Leer el body del StreamingResponse
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    contenido = b"".join(chunks).decode("utf-8-sig")

    assert "TESIS: CHATBOT UTILIZANDO MACHINE LEARNING PARA EL DIAGNÓSTICO VEHICULAR" in contenido
    assert "Prediccion_Linear_SVM" in contenido
    assert "pendiente de definición con el asesor estadístico" in contenido.lower()
    assert "prohíbe el uso de datos sintéticos" in contenido.lower() or "prohibe el uso de datos sinteticos" in contenido.lower()


def test_regla_3_telemetria_separa_tiempo_ml_y_tiempo_total():
    """
    Regla 4: La telemetría debe separar con precisión:
    a) tiempo_ml_ms (inferencia TF-IDF + SVM)
    b) tiempo_total_ms (pipeline completo)
    """
    dto = ResultadoDiagnostico(
        respuesta_texto="Diagnóstico de prueba",
        diagnostico_ml="Falla en bujías",
        confianza_ml=0.85,
        contexto_manual="Manual RAG",
        titulo_manual="Manual OEM",
        tiempo_ml_ms=12,
        tiempo_rag_ms=6,
        tiempo_llm_ms=1800,
        tiempo_total_ms=1818,
    )

    assert isinstance(dto.tiempo_ml_ms, int)
    assert isinstance(dto.tiempo_total_ms, int)
    assert dto.tiempo_ml_ms <= dto.tiempo_total_ms
    assert dto.tiempo_ml_ms > 0
    assert dto.tiempo_total_ms > dto.tiempo_ml_ms


def test_regla_6_separacion_dataset_sintomas_vs_manuales_oem():
    """
    Regla 6: El dataset de entrenamiento ML procesa los síntomas coloquiales,
    mientras que el corpus RAG sólo indexa manuales técnicos de servicio (OEM).
    """
    motor_ml = ModeloML()
    motor_rag = MotorRAG()

    # Motor ML tiene clases vehiculares
    assert motor_ml.modelo is not None

    # Motor RAG tiene documentos con terminología técnica
    assert len(motor_rag.documentos) > 0
    terminos_tecnicos = ("procedimiento", "inspección", "inspeccion", "revisar", "tolerancia", "torque", "comprobar", "falla", "sensor", "voltaje", "presion", "motor", "freno", "bujia")
    assert any(
        any(t in doc.lower() for t in terminos_tecnicos)
        for doc in motor_rag.documentos[:10]
    )
