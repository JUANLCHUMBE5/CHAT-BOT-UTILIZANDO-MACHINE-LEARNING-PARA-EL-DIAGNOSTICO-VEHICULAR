import os
import joblib
from src.core.logger import logger
from src.config import settings

class ModeloML:
    """Clase encargada de encapsular el modelo de clasificación de texto de Machine Learning."""
    
    def __init__(
        self, 
        modelo_path: str = settings.MODELO_ML_PATH, 
        vectorizador_path: str = settings.VECTORIZADOR_TFIDF_PATH
    ):
        self.modelo_path = modelo_path
        self.vectorizador_path = vectorizador_path
        self.modelo = None
        self.vectorizador = None
        self._cargar_modelos()

    def _cargar_modelos(self):
        if os.path.exists(self.modelo_path) and os.path.exists(self.vectorizador_path):
            self.modelo = joblib.load(self.modelo_path)
            self.vectorizador = joblib.load(self.vectorizador_path)
            logger.info("Modelo ML y Vectorizador TF-IDF cargados correctamente.")
        else:
            logger.warning("Archivos de modelo ML no encontrados.")

    def predecir(self, texto: str) -> tuple:
        """Alias para predecir_falla_con_confianza."""
        return self.predecir_falla_con_confianza(texto)

    def predecir_falla(self, texto: str) -> str:
        """Predice la categoría de la falla basándose en el síntoma de texto."""
        prediccion, _ = self.predecir_falla_con_confianza(texto)
        return prediccion

    def predecir_falla_con_confianza(self, texto: str) -> tuple:
        """Predice la categoría de la falla y calcula el porcentaje de certeza/confianza."""
        if not self.modelo or not self.vectorizador:
            return "Falla mecánica no clasificada (Modelo ML ausente)", 0.0
            
        try:
            entrada_vec = self.vectorizador.transform([texto])
            if getattr(entrada_vec, "nnz", 0) == 0:
                return "Síntoma fuera del vocabulario del modelo", 0.0
            if hasattr(self.modelo, "predict_proba"):
                probabilidades = self.modelo.predict_proba(entrada_vec)[0]
                idx_max = probabilidades.argmax()
                ordenadas = sorted((float(p) for p in probabilidades), reverse=True)
                maxima = ordenadas[0]
                margen = maxima - ordenadas[1] if len(ordenadas) > 1 else maxima
                # Random Forest no produce probabilidades calibradas. Este score
                # conservador penaliza predicciones sin separación entre clases.
                confianza = maxima * min(1.0, margen / 0.25)
                prediccion = self.modelo.classes_[idx_max]
            else:
                prediccion = self.modelo.predict(entrada_vec)[0]
                confianza = 0.85
                
            return prediccion, confianza
        except Exception as e:
            logger.error(f"Error al predecir falla con el modelo ML: {e}")
            return "Error de predicción", 0.0
