from typing import Protocol, Tuple, runtime_checkable


@runtime_checkable
class IModeloML(Protocol):
    """Protocolo de dominio para la clasificación con Machine Learning."""
    def predecir_falla_con_confianza(self, sintoma: str) -> Tuple[str, float]:
        ...

@runtime_checkable
class IMotorRAG(Protocol):
    """Protocolo de dominio para la búsqueda semántica en manuales de taller RAG."""
    def recuperar_contexto(self, query: str) -> Tuple[str, str]:
        ...

    def recuperar_contexto_con_similitud(self, query: str) -> Tuple[str, str, float]:
        ...
