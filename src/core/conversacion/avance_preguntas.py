"""Control de la pregunta realmente mostrada, sin reiniciar ni repetir bloques."""

import re
import unicodedata

from src.core.conversacion.models import ConversationState, QuestionIntent


def _clave(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.casefold())
    texto = " ".join("".join(c for c in texto if not unicodedata.combining(c)).split())
    if re.search(r"\b(?:electroventilador|motoventilador|ventilador)\b", texto) and re.search(
        r"\b(?:activa|funciona|enciende|entra)\b", texto,
    ):
        return "refrigeracion:activacion_ventilador"
    return texto


def preguntas(texto: str) -> list[str]:
    return re.findall(r"¿[^?]*\?", texto or "", flags=re.DOTALL)


def asegurar_pregunta_util(
    estado: ConversationState, respuesta: str, previas: list[dict],
) -> tuple[str, str | None]:
    """Comprueba la salida final (incluido formateador/LLM) contra el historial real."""
    anteriores = {
        _clave(p)
        for registro in previas
        for p in preguntas(registro.get("texto", ""))
    }
    actuales = preguntas(respuesta)
    if not actuales:
        return respuesta, None
    repetida = any(_clave(p) in anteriores for p in actuales)
    if repetida:
        opciones = {
            "refrigeracion": [
                "¿El electroventilador se activa cuando aumenta la temperatura?",
                "¿Hay una fuga visible de refrigerante y en qué punto?",
                "¿Qué temperatura muestra el escáner cuando ocurre la falla?",
            ],
            "encendido": [
                "¿Qué resultado dio la revisión de chispa en bujías y bobinas?",
                "¿Se identificó un cilindro específico con la falla?",
            ],
            "frenos": [
                "¿El pedal baja hasta el fondo o mantiene su altura al sostenerlo?",
                "¿Hay pérdida de líquido o aire detectado en el circuito hidráulico?",
                "¿Qué alabeo se midió en los discos y cuál es la especificación del vehículo?",
            ],
            "electrico_ecu": [
                "¿Cuál es el código o texto exacto del error de codificación?",
                "¿El número de parte de la ECU coincide con el especificado para ese vehículo?",
            ],
            "combustible_admision": [
                "¿Qué resultado concreto dio la última comprobación del componente en evaluación?",
            ],
        }.get(estado.active_system, [])
        siguiente = next((p for p in opciones if _clave(p) not in anteriores), None)
        if siguiente is None:
            area = {
                "refrigeracion": "refrigeración: termostato, ventilador y circuito de refrigerante",
                "encendido": "encendido: chispa, bujías y bobinas",
                "frenos": "frenos: circuito hidráulico y comprobación física",
                "combustible_admision": "admisión/combustible: comprobación del hallazgo reportado",
                "electrico_ecu": "ECU/codificación: compatibilidad y mensaje exacto",
            }.get(estado.active_system, "el sistema en evaluación")
            return (
                f"Mantengo los datos y descartes de este caso en {area}. No repetiré las preguntas anteriores. "
                "El diagnóstico sigue sin confirmar; continúa con la comprobación pendiente "
                "y aporta su resultado, o solicita revisión presencial si no puedes realizarla.",
                None,
            )
        respuesta = "Conservo la información que ya aportaste. " + siguiente
        actuales = [siguiente]
    final = actuales[-1]
    if not any(
        registro.get("turno") == estado.turno_actual and final in registro.get("texto", "")
        for registro in estado.preguntas_realizadas
    ):
        estado.registrar_pregunta(
            QuestionIntent.MEDICION_TECNICA, final, incrementar_repregunta=False,
            metadata={"origen": "salida_final", "sistema": estado.active_system},
        )
    return respuesta, final
