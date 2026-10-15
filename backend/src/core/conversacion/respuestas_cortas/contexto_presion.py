"""Distingue la magnitud medida del circuito que originó la pregunta."""
import re
import unicodedata


def presion_de_otro_circuito(texto: str) -> bool:
    normalizado = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                          if unicodedata.category(c) != "Mn")
    return bool(
        re.search(r"\d+(?:[.,]\d+)?\s*(?:psi|bar|kpa|mbar)\b", normalizado)
        and re.search(r"\b(?:compresion|cilindros?|neumaticos?|aceite|sobrealimentacion|"
                      r"diferencial|dpf|admision|map|frenos?)\b", normalizado)
    )
