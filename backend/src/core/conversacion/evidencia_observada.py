"""Observaciones de taller: conservar evidencia sin convertirla en una falla confirmada."""

import re
import unicodedata

from src.core.diagnostico.evidencia_proposicional import evidencia_afirmada


def normalizar(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.lower())
                   if not unicodedata.combining(c))


def observacion_tecnica(texto: str) -> bool:
    """Identifica reportes, fallos y lecturas; excluye instrucciones y respuestas de menú."""
    texto = normalizar(texto)
    return subsistema_observado(texto) is not None and bool(re.search(
        r'\b(?:senal\s+(?:baja|alta|ausente|intermitente)|circuito\s+(?:abierto|en corto)|'
        r'(?:mide|marca|registra|reporta|aparece|arroja|encontre)|'
        r'(?:no|sin)\s+(?:levanta|funciona|responde|enciende|gira)|'
        r'(?:timon|direccion|volante)\s+(?:esta\s+)?dur[oa])\b', texto))


def subsistema_observado(texto: str) -> str | None:
    """Prioriza el componente explícito, con negaciones fuera de la evidencia afirmada."""
    texto = normalizar(evidencia_afirmada(texto))
    if re.search(r'\b(?:pedal\s+(?:del?\s+)?acelerador|sensor\s+(?:app|tps)|'
                 r'potenciometro|senal\s+(?:baja|alta|ausente|intermitente)|'
                 r'circuito\s+(?:abierto|en corto))\b', texto):
        return 'senal_electrica'
    if re.search(r'\b(?:velocimetro|odometro|tacometro|tablero\s+de\s+instrumentos)\b', texto):
        return 'instrumentacion'
    if re.search(r'\b(?:timon|direccion|volante)\b.{0,25}\b(?:dur[oa]|pesad[oa]|'
                 r'sin asistencia)|\b(?:dur[oa]|pesad[oa])\b.{0,20}\b(?:timon|direccion|volante)\b', texto):
        return 'direccion'
    return None


def pregunta_observacion(estado):
    """Formula una siguiente comprobación específica sin afirmar causa ni umbrales OEM."""
    historial = getattr(estado, 'historial_mensajes_usuario', []) or []
    # Una respuesta corta mantiene el último componente; no se mezcla con otro caso.
    sistema = next((s for t in reversed(historial) if (s := subsistema_observado(t))), None)
    preguntas = {
        'senal_electrica': (
            'Registré la anomalía de señal del componente reportado; no confirma que deba reemplazarse. '
            '¿Cuál es el DTC exacto y qué lectura muestra el escáner para ese componente, '
            'con su unidad y condición de medición? La alimentación, masa y señal se comprueban '
            'según el diagrama aplicable, sin puentear circuitos.'),
        'instrumentacion': (
            'Para aislar la falla del instrumento, ¿el escáner registra el dato correspondiente '
            'aunque el tablero no lo muestre? Si no puedes comprobarlo, conserva el caso pendiente; '
            'no realices una prueba de conducción para obtenerlo.'),
        'direccion': (
            'Para orientar la dirección dura sin asumir el tipo de asistencia: '
            '¿ocurre detenido, en marcha o en ambas condiciones, y hay testigo de dirección? '
            'Si dificulta controlar el vehículo, no circules y solicita inspección en taller.'),
    }
    if sistema:
        return preguntas.get(sistema)
    texto = normalizar(" ".join(historial))
    if re.search(r"\b(?:cabece\w*|tiembla|sacude|vibra)\b", texto) and not re.search(
        r"\b(?:ralenti|motor|rpm|volante|rueda|fren\w*|bache\w*|embrague|clutch|cambio|"
        r"carretera|velocidad|piso|aceler\w*|subida|carga|primera|salir|soltar|p[0-3]\d{3})\b", texto
    ):
        return (
            "Para distinguir motor de ruedas o suspensión: ¿la sacudida aparece también "
            "con el vehículo detenido y el motor en ralentí, o solo al desplazarse? "
            "Indica dónde se siente; no hace falta conducir para reproducirla."
        )
    return None
