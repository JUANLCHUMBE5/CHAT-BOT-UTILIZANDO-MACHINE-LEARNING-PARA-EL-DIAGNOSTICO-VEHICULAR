"""Carga y ejecucion segura del clasificador de sintomas."""

from __future__ import annotations

import os

import joblib

from src.config import settings
from src.core.logger import logger


class ModeloML:
    def __init__(
        self,
        modelo_path: str = settings.MODELO_ML_PATH,
        vectorizador_path: str = settings.VECTORIZADOR_TFIDF_PATH,
    ):
        self.modelo_path = modelo_path
        self.vectorizador_path = vectorizador_path
        self.modelo = None
        self.vectorizador = None
        self._cargar_modelos()

    def _cargar_modelos(self) -> None:
        if os.path.exists(self.modelo_path) and os.path.exists(self.vectorizador_path):
            self.modelo = joblib.load(self.modelo_path)
            self.vectorizador = joblib.load(self.vectorizador_path)
            logger.info("Modelo ML y vectorizador TF-IDF cargados correctamente.")
        else:
            logger.warning("Archivos del modelo ML no encontrados.")

    def predecir(self, texto: str) -> tuple[str, float]:
        return self.predecir_falla_con_confianza(texto)

    def predecir_falla(self, texto: str) -> str:
        prediccion, _ = self.predecir_falla_con_confianza(texto)
        return prediccion

    def predecir_falla_con_confianza(self, texto: str) -> tuple[str, float]:
        """Retorna la clase y la probabilidad calibrada cuando esta disponible."""
        if self.modelo is None or self.vectorizador is None:
            return "Falla mecanica no clasificada (modelo ML ausente)", 0.0

        try:
            entrada = self.vectorizador.transform([texto])
            if getattr(entrada, "nnz", 0) == 0:
                return "Sintoma fuera del vocabulario del modelo", 0.0

            if not hasattr(self.modelo, "predict_proba"):
                return str(self.modelo.predict(entrada)[0]), 0.0

            probabilidades = self.modelo.predict_proba(entrada)[0]
            indice = int(probabilidades.argmax())
            return str(self.modelo.classes_[indice]), round(float(probabilidades[indice]), 4)
        except Exception as exc:
            logger.error("Error al predecir falla con el modelo ML: %s", exc)
            return "Error de prediccion", 0.0
