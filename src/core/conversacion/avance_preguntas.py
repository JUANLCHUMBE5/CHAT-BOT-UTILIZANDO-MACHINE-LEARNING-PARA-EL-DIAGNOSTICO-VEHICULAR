"""Control de la pregunta realmente mostrada, sin reiniciar ni repetir bloques."""

import re
import unicodedata

from src.core.conversacion.models import ConversationState, QuestionIntent
from src.core.diagnostico.hallazgo_refrigerante import ORIENTACION_FUGA, estado_fuga


def _clave(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.casefold())
    texto = " ".join("".join(c for c in texto if not unicodedata.combining(c)).split())
    if re.search(r"\b(?:frio|caliente|temperatura)\b", texto) and re.search(
        r"\b(?:ocurre|aparece|falla|manifiesta|motor)\b", texto,
    ):
        return "pregunta:condicion_temperatura"
    if re.search(r"\b(?:dtc|codigo(?:s)?(?:\s+de\s+falla)?|obd)\b", texto) and re.search(
        r"\b(?:mezcla|stft|ltft|trim|combustible)\b", texto,
    ):
        return "pregunta:dtc_mezcla"
    if re.search(r"\b(?:stft|ltft|fuel\s+trim|ajuste\s+de\s+combustible)\b", texto):
        return "pregunta:dtc_mezcla"
    if re.search(r"\bmaf\b", texto) and re.search(
        r"\b(?:g/s|rpm|valor|cuanto|numerico|dato exacto)\b", texto,
    ):
        return "pregunta:lectura_maf_valor"
    if re.search(r"\bmaf\b", texto) and re.search(
        r"\b(?:cambia|variable|fija|irregular|estable|acelerar)\b", texto,
    ):
        return "pregunta:comportamiento_maf"
    if re.search(r"\b(?:maf|flujo\s+de\s+aire)\b", texto) and re.search(
        r"\b(?:lectura|valor|flujo|g/s|senal|mide)\b", texto,
    ):
        return "pregunta:lectura_maf"
    if re.search(r"\b(?:map|carga\s+absoluta|presion\s+del\s+multiple)\b", texto) and re.search(
        r"\b(?:lectura|valor|presion|kpa|marca|mide)\b", texto,
    ):
        return "pregunta:lectura_map"
    if re.search(r"\b(?:inyector|inyectores)\b", texto) and re.search(
        r"\b(?:balance|caudal|pulverizacion|entrega)\b", texto,
    ):
        return "pregunta:balance_inyectores"
    if re.search(r"\b(?:presion|psi|riel)\b", texto) and re.search(
        r"\b(?:combustible|gasolina|bomba)\b", texto,
    ):
        return "pregunta:presion_combustible"
    if re.search(r"\b(?:bobina|bobinas|bujia|bujias|chispa)\b", texto):
        return "pregunta:prueba_chispa"
    if re.search(r"\b(?:fuga|pierde|gotea)\b", texto) and re.search(
        r"\b(?:refrigerante|radiador|manguera|presion)\b", texto,
    ):
        return "pregunta:prueba_fuga_refrigerante"
    if re.search(r"\b(?:electroventilador|motoventilador|ventilador)\b", texto) and re.search(
        r"\b(?:activa|funciona|enciende|entra)\b", texto,
    ):
        return "refrigeracion:activacion_ventilador"
    return texto


def preguntas(texto: str) -> list[str]:
    return re.findall(r"¿[^?]*\?", texto or "", flags=re.DOTALL)


def _priorizar_fuga(
    estado: ConversationState,
    respuesta: str,
    anteriores: set[str],
) -> str:
    if estado.active_system != "refrigeracion":
        return respuesta

    hallazgo = None
    for mensaje in getattr(estado, "historial_mensajes_usuario", []):
        hallazgo_actual = estado_fuga(mensaje, refrigeracion=True)
        if hallazgo_actual is not None:
            hallazgo = hallazgo_actual
    if hallazgo is not True:
        return respuesta

    opciones = [
        "¿En qué punto del radiador, mangueras o conexiones se localizó la fuga?",
        "¿Qué resultado dio la prueba de presión del sistema realizada en frío?",
    ]
    siguiente = next((pregunta for pregunta in opciones if _clave(pregunta) not in anteriores), None)
    cierre = (
        siguiente
        or "Queda pendiente la comprobación física; aporta su resultado o solicita revisión presencial. "
        "No repetiré las preguntas anteriores."
    )
    return (
        ORIENTACION_FUGA
        + "Esta orientación general no acredita un procedimiento OEM/taller validado. "
        + cierre
    )


def asegurar_pregunta_util(
    estado: ConversationState, respuesta: str, previas: list[dict],
    permitir_preguntas: bool = True,
) -> tuple[str, str | None]:
    """Comprueba la salida final (incluido formateador/LLM) contra el historial real."""
    if not permitir_preguntas:
        respuesta = re.sub(r"¿[^?]*\?", "", respuesta, flags=re.DOTALL).strip()
        return (
            respuesta + "\nEl caso permanece sin confirmar. Se requiere revisión presencial antes de concluir la falla.",
            None,
        )
    from src.core.conversacion.orientacion_provisional import (
        es_imposibilidad_completa,
        generar_orientacion_provisional,
    )
    ultimo_mensaje = getattr(estado, "historial_mensajes_usuario", [])[-1:]
    if (
        (ultimo_mensaje and es_imposibilidad_completa(ultimo_mensaje[0]))
        or getattr(estado, "obtener_hecho", lambda _: None)("comprobacion_fisica_imposible")
    ):
        return generar_orientacion_provisional(estado), None

    anteriores = {
        _clave(p)
        for registro in previas
        for p in preguntas(registro.get("texto", ""))
    }
    respuesta = _priorizar_fuga(estado, respuesta, anteriores)
    actuales = preguntas(respuesta)
    if not actuales:
        return respuesta, None
    repetida = any(_clave(p) in anteriores for p in actuales)
    if repetida:
        opciones = {
            "refrigeracion": [
                "¿El electroventilador del radiador se activa cuando aumenta la temperatura del refrigerante?",
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
        if estado.active_system == "combustible_admision" and estado.obtener_hecho("caudal_inyectores_reportado"):
            opciones = [
                "¿Con el manómetro conectado al riel, qué presión mediste, en qué unidad y bajo qué condición?",
                "¿Qué diferencia de caudal o caída de presión mostró la prueba de balance entre los inyectores?",
            ]
            if any("presion" in str(nombre).lower() for nombre in estado.measurements):
                opciones = opciones[1:]
        siguiente = next((p for p in opciones if _clave(p) not in anteriores), None)
        if siguiente is None:
            from src.core.conversacion.orientacion_provisional import generar_orientacion_provisional
            return generar_orientacion_provisional(estado), None
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
