from typing import Optional

from src.infrastructure.ml import ModeloML
from src.infrastructure.rag import MotorRAG


class ServiceContainer:
    """
    Contenedor de Inyección de Dependencias y Patrón Singleton para la infraestructura.
    Garantiza que el modelo de ML (TF-IDF + Clasificador) y el índice FAISS del Motor RAG
    se carguen exactamente UNA sola vez en memoria (~540MB compartidos).
    """
    _modelo_ml: Optional[ModeloML] = None
    _motor_rag: Optional[MotorRAG] = None

    @classmethod
    def get_modelo_ml(cls) -> ModeloML:
        """Retorna la instancia Singleton del modelo ML."""
        if cls._modelo_ml is None:
            cls._modelo_ml = ModeloML()
        return cls._modelo_ml

    @classmethod
    def get_motor_rag(cls) -> MotorRAG:
        """Retorna la instancia Singleton del motor RAG FAISS."""
        if cls._motor_rag is None:
            cls._motor_rag = MotorRAG()
        return cls._motor_rag

    @classmethod
    def reset(cls):
        """Reinicia las instancias para pruebas en aislamiento."""
        cls._modelo_ml = None
        cls._motor_rag = None
