"""Comprobaciones del espacio vectorial independientes del motor RAG."""


class FrozenRAGMismatch(ValueError):
    """El corpus disponible no permite consultar el índice sin reconstruirlo."""


def validar_espacio_congelado(index, vectorizer, document_count: int) -> None:
    dimension = len(vectorizer.get_feature_names_out())
    if index.d != dimension or index.ntotal != document_count:
        raise FrozenRAGMismatch(
            f"Índice congelado incompatible: índice=({index.d}, {index.ntotal}), "
            f"corpus=({dimension}, {document_count}). No se reconstruirá el índice."
        )
