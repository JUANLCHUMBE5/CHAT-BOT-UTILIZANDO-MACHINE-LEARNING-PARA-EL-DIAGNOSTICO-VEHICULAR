"""Telemetría raw y abstención por ausencia de vocabulario, sin recalibración."""
import time

from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.logger import logger


def evaluar_cobertura_svm(gestor, texto_evaluar, diagnostico_forzado, inicio_total):
    # Telemetría independiente: probabilidad original antes de cualquier fusión.
    inicio_telemetria_svm = time.perf_counter()
    # Nunca se usa para cambiar el ranking o confianza operativos.
    predicciones_svm_raw = []
    modelo = getattr(gestor, "modelo_ml", None)
    if modelo is not None and hasattr(modelo, "predecir_top_fallas_svm_raw"):
        try:
            texto_svm = gestor._purificar_sintoma_para_vectorizador_ml(texto_evaluar)
            predicciones_svm_raw = [
                {"falla": item["falla"], "probabilidad": item["probabilidad"]}
                for item in modelo.predecir_top_fallas_svm_raw(texto_svm, limite=3)
            ]
        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning("No se pudo obtener telemetría SVM raw: %s", exc)

    tiempo_telemetria_svm_ms = max(0, int((time.perf_counter() - inicio_telemetria_svm) * 1000))

    # Abstención conservadora únicamente cuando no existe vocabulario TF-IDF
    # utilizable. No se asignan umbrales de confianza sin evaluación OOD.
    motivo_abstencion = None
    if modelo is not None and getattr(modelo, "vectorizador", None) is not None:
        try:
            texto_c1 = gestor._purificar_sintoma_para_vectorizador_ml(texto_evaluar)
            entrada_c1 = modelo.vectorizador.transform([texto_c1])
            if getattr(entrada_c1, "nnz", 0) == 0:
                motivo_abstencion = "SIN_VOCABULARIO_TFIDF"
        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning("No se pudo evaluar cobertura TF-IDF: %s", exc)
    if motivo_abstencion and not diagnostico_forzado:
        return predicciones_svm_raw, tiempo_telemetria_svm_ms, ResultadoDiagnostico(
            respuesta_texto=(
                "No tengo evidencia textual reconocible para proponer una avería. "
                "Describe un síntoma concreto y la condición en que aparece."
            ),
            diagnostico_ml="Baja Confianza / Indeterminado",
            confianza_ml=0.0,
            contexto_manual="",
            titulo_manual="",
            requiere_revision_humana=True,
            modo_diagnostico="abstencion_c1",
            motivo_abstencion=motivo_abstencion,
            predicciones_ml=[],
            predicciones_svm_raw=[],
            tiempo_ml_ms=tiempo_telemetria_svm_ms,
            tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
        )

    return predicciones_svm_raw, tiempo_telemetria_svm_ms, None
