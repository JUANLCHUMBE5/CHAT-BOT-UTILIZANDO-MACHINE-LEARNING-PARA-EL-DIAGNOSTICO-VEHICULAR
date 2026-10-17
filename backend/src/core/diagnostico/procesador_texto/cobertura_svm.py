"""Telemetría raw y abstención por ausencia de vocabulario o síntomas fuera de catálogo (OOD)."""
import time

from src.core.diagnostico.detector_ood import detectar_sintoma_fuera_de_catalogo
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

    # 1. Detección segura de síntomas fuera de catálogo (OOD)
    if not diagnostico_forzado:
        es_ood, regla_ood = detectar_sintoma_fuera_de_catalogo(texto_evaluar)
        if es_ood and regla_ood is not None:
            logger.info("Abstención segura activada por síntoma fuera de catálogo: %s", regla_ood.categoria)
            return predicciones_svm_raw, tiempo_telemetria_svm_ms, ResultadoDiagnostico(
                respuesta_texto=regla_ood.mensaje_abstencion,
                diagnostico_ml=f"Fuera de Catálogo: {regla_ood.sistema_objetivo}",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                modo_diagnostico="abstencion_ood",
                motivo_abstencion=f"OOD_{regla_ood.categoria}",
                sintoma_evaluado=texto_evaluar,
                predicciones_ml=[],
                predicciones_svm_raw=predicciones_svm_raw,
                tiempo_ml_ms=tiempo_telemetria_svm_ms,
                tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
            )

    # 2. Abstención conservadora por ausencia de vocabulario TF-IDF
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
