"""Carga y ejecución segura del clasificador jerárquico de síntomas (Sistema -> Falla).
Cumple estrictamente con la Regla 1 de Arquitectura de Tesis (Linear SVM + TF-IDF).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import joblib
import numpy as np

from src.config import settings
from src.core.logger import logger
from src.core.diagnostico.taxonomia_sistemas import (
    obtener_macro_sistema,
    obtener_sistema_por_dtc,
)


class ModeloML:
    def __init__(
        self,
        modelo_path: str = str(settings.paths.model_pkl),
        vectorizador_path: str = str(settings.paths.vectorizer_pkl),
        modelo_sistema_path: Optional[str] = None,
        temperatura: float = 0.80,
    ):
        self.modelo_path = modelo_path
        self.vectorizador_path = vectorizador_path
        self.temperatura = float(temperatura)
        if modelo_sistema_path is None:
            self.modelo_sistema_path = str(Path(self.modelo_path).parent / "modelo_sistema.pkl")
        else:
            self.modelo_sistema_path = modelo_sistema_path

        self.modelo = None
        self.modelo_sistema = None
        self.vectorizador = None
        self._cargar_modelos()

    def _cargar_modelos(self) -> None:
        if os.path.exists(self.modelo_path) and os.path.exists(self.vectorizador_path):
            self.modelo = joblib.load(self.modelo_path)
            self.vectorizador = joblib.load(self.vectorizador_path)
            logger.info("Modelo ML Nivel 2 y vectorizador TF-IDF cargados correctamente.")
        else:
            logger.warning("Archivos del modelo ML no encontrados.")

        if os.path.exists(self.modelo_sistema_path):
            try:
                self.modelo_sistema = joblib.load(self.modelo_sistema_path)
                logger.info("Modelo ML Nivel 1 (Macro-Sistemas) cargado correctamente.")
            except Exception as e:
                logger.warning("No se pudo cargar el modelo de macro-sistemas: %s", e)
                self.modelo_sistema = None

    def predecir(self, texto: str) -> tuple[str, float]:
        return self.predecir_falla_con_confianza(texto)

    def predecir_falla(self, texto: str) -> str:
        prediccion, _ = self.predecir_falla_con_confianza(texto)
        return prediccion

    def predecir_sistema(self, texto: str) -> str:
        """Predice el macro-sistema automotriz principal (Nivel 1)."""
        if self.modelo_sistema is None or self.vectorizador is None:
            return "MOTOR"
        texto_limpio = str(texto or "").strip()[:4000]
        if not texto_limpio:
            return "MOTOR"
        entrada = self.vectorizador.transform([texto_limpio])
        if getattr(entrada, "nnz", 0) == 0:
            return "MOTOR"
        return str(self.modelo_sistema.predict(entrada)[0])

    def predecir_falla_con_confianza(self, texto: str) -> tuple[str, float]:
        """Retorna la clase y la probabilidad calibrada cuando está disponible."""
        predicciones = self.predecir_top_fallas(texto, limite=1)
        if not predicciones:
            return "Error de prediccion", 0.0
        principal = predicciones[0]
        return str(principal["falla"]), float(principal["probabilidad"])

    def predecir_top_fallas(
        self, texto: str, limite: int = 3, dtc_codigo: Optional[str] = None
    ) -> list[dict[str, float | str]]:
        """
        Devuelve las clases más probables mediante inferencia jerárquica (Macro-Sistema -> Falla).
        Integra autoridad estructurada para códigos DTC.
        """
        if self.modelo is None or self.vectorizador is None:
            return [{"falla": "Falla mecanica no clasificada (modelo ML ausente)", "probabilidad": 0.0}]

        try:
            texto_limpio = str(texto or "").strip()[:4000]
            if not texto_limpio:
                return [{"falla": "Sintoma fuera del vocabulario del modelo", "probabilidad": 0.0}]
            entrada = self.vectorizador.transform([texto_limpio])
            if getattr(entrada, "nnz", 0) == 0:
                return [{"falla": "Sintoma fuera del vocabulario del modelo", "probabilidad": 0.0}]

            if not hasattr(self.modelo, "predict_proba"):
                return [{"falla": str(self.modelo.predict(entrada)[0]), "probabilidad": 0.0}]

            probabilidades_fallas = self.modelo.predict_proba(entrada)[0].copy()
            clases_fallas = list(self.modelo.classes_)

            # Detección o extracción de DTC
            codigos_dtc = []
            if dtc_codigo:
                codigos_dtc.append(dtc_codigo.strip().upper())
            else:
                matches = re.findall(r"\b[PBCU]\d{4}\b", texto_limpio, re.IGNORECASE)
                codigos_dtc.extend([m.upper() for m in matches])

            # Inferencia de Nivel 1 (Macro-Sistemas) si el modelo está disponible
            if self.modelo_sistema is not None and hasattr(self.modelo_sistema, "predict_proba"):
                probabilidades_sistemas = self.modelo_sistema.predict_proba(entrada)[0].copy()
                clases_sistemas = list(self.modelo_sistema.classes_)
                sist_map = {s: probabilidades_sistemas[i] for i, s in enumerate(clases_sistemas)}

                # Autoridad Estructurada del DTC sobre Macro-Sistemas
                if codigos_dtc:
                    for cod in codigos_dtc:
                        info_dtc = obtener_sistema_por_dtc(cod)
                        if info_dtc:
                            sist_dtc, fallas_dtc = info_dtc
                            if sist_dtc in sist_map:
                                sist_map[sist_dtc] = max(sist_map[sist_dtc], 0.92)
                            # Boost directo a las clases asociadas al DTC
                            for idx_f, f_nom in enumerate(clases_fallas):
                                if f_nom in fallas_dtc:
                                    probabilidades_fallas[idx_f] *= 2.5

                # Combinación jerárquica de probabilidades: P(Falla) * P(Sistema)^0.65
                scores_combinados = np.zeros(len(clases_fallas), dtype=float)
                for idx_f, f_nom in enumerate(clases_fallas):
                    macro_sist = obtener_macro_sistema(f_nom)
                    p_sist = sist_map.get(macro_sist, 0.05)
                    # Exponenciación suave para penalizar sistemas cruzados absurdos
                    scores_combinados[idx_f] = probabilidades_fallas[idx_f] * (p_sist ** 0.65)

                suma_scores = np.sum(scores_combinados)
                if suma_scores > 0:
                    probs_norm = scores_combinados / suma_scores
                    if self.temperatura > 0 and self.temperatura != 1.0:
                        probs_t = probs_norm ** (1.0 / self.temperatura)
                        probabilidades_finales = probs_t / np.sum(probs_t)
                    else:
                        probabilidades_finales = probs_norm
                else:
                    probabilidades_finales = probabilidades_fallas
            else:
                if self.temperatura > 0 and self.temperatura != 1.0:
                    probs_t = probabilidades_fallas ** (1.0 / self.temperatura)
                    probabilidades_finales = probs_t / np.sum(probs_t)
                else:
                    probabilidades_finales = probabilidades_fallas

            limite_seguro = max(1, min(int(limite), len(probabilidades_finales)))
            indices = probabilidades_finales.argsort()[::-1][:limite_seguro]
            return [
                {
                    "falla": str(clases_fallas[int(indice)]),
                    "probabilidad": round(float(probabilidades_finales[int(indice)]), 4),
                }
                for indice in indices
            ]
        except Exception as exc:
            logger.error("Error al predecir falla con el modelo ML jerárquico: %s", exc)
            return [{"falla": "Error de prediccion", "probabilidad": 0.0}]
