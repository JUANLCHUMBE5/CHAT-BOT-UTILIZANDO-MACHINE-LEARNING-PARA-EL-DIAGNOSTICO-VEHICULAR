"""Hallazgo declarado de fuga: orientación general, nunca confirmación OEM."""

import re
import unicodedata


def estado_fuga(texto: str, refrigeracion: bool = False) -> bool | None:
    """Devuelve la última afirmación explícita; None no equivale a ausencia de fuga."""
    txt = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                  if not unicodedata.combining(c))
    contexto = refrigeracion or bool(re.search(r"recalient|refriger|radiador|anticongelante", txt))
    resultado = None
    for frase in re.split(r"[.;\n]|\bpero\b", txt):
        fluido = bool(re.search(r"refrigerante|anticongelante|\bagua\b|coolant", frase))
        perdida = bool(re.search(r"\bfugas?\b|\bpierde\b|perdiendo|perdida|gote[ao]", frase))
        mancha = bool(re.search(r"(?:mancha|charco|goteo).{0,35}(?:piso|suelo)", frase))
        if not ((perdida and (fluido or contexto)) or (mancha and contexto)):
            continue
        if re.search(r"\bno\b.{0,25}(?:fuga|pierde|perdiendo|gote|mancha|charco)|"
                     r"\bsin\b.{0,20}(?:fuga|perdida|mancha|charco)", frase):
            resultado = False
        elif not re.search(r"\b(?:quizas|posible|podria|sospecho)\b|\?", frase):
            resultado = True
    return resultado


ORIENTACION_FUGA = (
    "Tomo la fuga como hallazgo reportado, no como pieza confirmada. "
    "Prioriza localizar la pérdida en radiador, mangueras y conexiones; "
    "la prueba de presión del sistema requiere motor frío, equipo adecuado "
    "y la especificación del fabricante. No abras el circuito caliente. "
)


def instruccion_hallazgo(pregunta: str, titulo: str, contexto: str) -> str:
    if estado_fuga(pregunta) is not True:
        return ""
    fuente = ""
    if not contexto:
        fuente = (
            "Declara: corpus preliminar no inyectado, pendiente de validación OEM/taller. "
            if "preliminar" in titulo.lower()
            else "Declara que no dispones de procedimiento RAG validado aplicable. "
        )
    return (
        "PRIORIDAD DE HALLAZGO REPORTADO (no confirmación física): fuga de refrigerante. "
        "El siguiente paso/pregunta debe tratar localización en radiador/mangueras o "
        "resultado de prueba de presión del sistema, NO temperatura genérica del escáner. "
        "Esto es orientación general por el hallazgo, no un procedimiento OEM recuperado. "
        "No des presiones numéricas ni declares reparaciones confirmadas. Motor frío, "
        "equipo adecuado y especificación del fabricante; nunca abrir caliente. " + fuente
    )
