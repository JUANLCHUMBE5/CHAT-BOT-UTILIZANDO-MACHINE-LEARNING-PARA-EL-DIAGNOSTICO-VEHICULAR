"""Clasificación determinista de intención antes del diagnóstico vehicular."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

TipoConsulta = Literal["diagnostico", "consulta_tecnica", "fuera_de_alcance"]


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    return " ".join(
        "".join(caracter for caracter in sin_tildes if not unicodedata.combining(caracter)).split()
    )


PATRONES_SINTOMA = (
    r"\bno (?:arranca|enciende|frena|acelera|enfria|funciona|abre|cierra|sube|baja|responde|carga)\b",
    r"\b(?:pierde|perdio) (?:fuerza|potencia|aceite|refrigerante)\b",
    r"\b(?:vibra|tiembla|jalonea|cascabelea|recalienta|hierve|patina|gotea|humea|chilla|rechina|golpea|raspa)\b",
    r"\b(?:ruido|chillido|rechinido|golpeteo|vibracion|fuga|humo|olor a quemado|luz de falla|check engine)\b",
    r"\b(?:se apaga|esta duro|esta esponjoso|se traba|esta trabado|se quedo trabado|trabado|inclinada|inclinado|no encaja|se descarga|consume demasiado)\b",
    r"\b(?:falla|fallando|averia|defectuoso|roto|quemado|sulfatado|baja presion|alta temperatura)\b",
    r"\b(?:p|b|c|u)\d{4}\b",
)

PATRONES_PREGUNTA = (
    r"^(?:que|cual|cuanto|cuanta|cuantos|cuantas|como|cuando|donde|por que)\b",
    r"(?:^|[:;,]\s*)(?:que|cual|cuanto|cuanta|cuantos|cuantas|como|cuando|donde|por que)\b",
    r"^(?:se puede|puedo|debo|conviene|es recomendable|es normal|cada cuanto|necesito saber)\b",
    r"\b(?:que porcentaje|que potencia|que tipo|cuantos kilometros|cuanto kilometraje)\b",
)

TERMINOS_AUTOMOTRICES = {
    "auto", "carro", "vehiculo", "motor", "aceite", "refrigerante", "radiador",
    "gnv", "glp", "gas", "gasolina", "diesel", "freno", "frenos", "bateria",
    "embrague", "caja", "transmision", "llanta", "llantas", "faro", "faros",
    "foco", "focos", "led", "h4", "bujia", "bujias", "inyector", "inyectores",
    "kilometraje", "scanner", "escaner", "dtc", "suzuki", "toyota", "hyundai",
    "puerta", "chapa", "cerradura", "pestillo", "seguro", "ventana", "vidrio",
    "kia", "nissan", "chevrolet", "volkswagen", "ford", "mazda", "honda",
}


def clasificar_intencion_consulta(texto: str) -> TipoConsulta:
    """Separa síntomas diagnosticables de preguntas informativas y texto ajeno.

    Las señales explícitas de avería tienen prioridad incluso cuando el mensaje
    está redactado como pregunta (por ejemplo: "¿por qué vibra al frenar?").
    """

    normalizado = _normalizar(texto)
    if any(re.search(patron, normalizado) for patron in PATRONES_SINTOMA):
        return "diagnostico"

    es_pregunta = "?" in texto or any(
        re.search(patron, normalizado) for patron in PATRONES_PREGUNTA
    )
    contiene_contexto_auto = any(
        re.search(rf"\b{re.escape(termino)}\b", normalizado)
        for termino in TERMINOS_AUTOMOTRICES
    )
    if es_pregunta and contiene_contexto_auto:
        return "consulta_tecnica"

    if contiene_contexto_auto:
        return "diagnostico"
    return "fuera_de_alcance"
