"""Carga y ejecucion segura del clasificador de sintomas."""

from __future__ import annotations

import os

import joblib

from src.config import settings
from src.core.logger import logger


class ModeloML:
    def __init__(
        self,
        modelo_path: str = str(settings.paths.model_pkl),
        vectorizador_path: str = str(settings.paths.vectorizer_pkl),
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
        predicciones = self.predecir_top_fallas(texto, limite=1)
        if not predicciones:
            return "Error de prediccion", 0.0
        principal = predicciones[0]
        return str(principal["falla"]), float(principal["probabilidad"])

    def predecir_top_fallas(self, texto: str, limite: int = 3) -> list[dict[str, float | str]]:
        """Devuelve las clases más probables para explicar cada inferencia en el panel."""
        if self.modelo is None or self.vectorizador is None:
            return [{"falla": "Falla mecanica no clasificada (modelo ML ausente)", "probabilidad": 0.0}]

        try:
            entrada = self.vectorizador.transform([texto])
            if getattr(entrada, "nnz", 0) == 0:
                return [{"falla": "Sintoma fuera del vocabulario del modelo", "probabilidad": 0.0}]

            if not hasattr(self.modelo, "predict_proba"):
                return [{"falla": str(self.modelo.predict(entrada)[0]), "probabilidad": 0.0}]

            probabilidades = self.modelo.predict_proba(entrada)[0]
            limite_seguro = max(1, min(int(limite), len(probabilidades)))
            indices = probabilidades.argsort()[::-1][:limite_seguro]
            return [
                {
                    "falla": str(self.modelo.classes_[int(indice)]),
                    "probabilidad": round(float(probabilidades[int(indice)]), 4),
                }
                for indice in indices
            ]
        except Exception as exc:
            logger.error("Error al predecir falla con el modelo ML: %s", exc)
            return [{"falla": "Error de prediccion", "probabilidad": 0.0}]
