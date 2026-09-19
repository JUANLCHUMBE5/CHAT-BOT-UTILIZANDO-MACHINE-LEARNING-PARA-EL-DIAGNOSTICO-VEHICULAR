"""Verificación de ambigüedad, saludos y respuestas cordiales en consultas mecánicas."""

from __future__ import annotations

import re
from typing import Tuple

from src.core.diagnostico.constants import VERBOS_FALLA, VOCABULARIO_COMPONENTES


def es_respuesta_opcion_o_combustible(texto: str) -> bool:
    """Detecta si el mensaje es una selección de opción (1, 2, 3), respuesta de combustible/estado o descarte."""
    limpio = texto.strip().lower().strip(" .,!¡¿?")
    opciones_directas = {
        "1", "2", "3", "4", "5", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣",
        "opcion 1", "opción 1", "opcion 2", "opción 2", "opcion 3", "opción 3",
        "la 1", "la 2", "la 3", "la primera", "la segunda", "la tercera",
        "primera", "segunda", "tercera", "uno", "dos", "tres",
        "gnv", "glp", "gasolina", "diesel", "diésel", "gas", "ambos", "dos",
        "frio", "frío", "caliente", "en frio", "en frío", "en caliente",
        "ninguna", "ninguno", "ninguna de las tres", "ninguna de esas", "no es ninguna",
        "ninguna opcion", "ninguna opción", "ninguna de las anteriores", "nada de eso",
        "otra", "otro", "ninguno de esos", "no pasa eso", "tampoco", "no es eso",
    }
    if limpio in opciones_directas:
        return True
    if re.match(r"^(?:opci[oó]n\s*|la\s*)?[1-5][\.\)]?$", limpio):
        return True
    if re.search(r"\b(?:ningun[ao]s?|no\s+es\s+ningun[ao]|nada\s+de\s+eso)\b", limpio):
        return True
    return False


def es_saludo_o_contacto_inicial(texto: str) -> Tuple[bool, str]:
    """Detecta si el mensaje es un saludo o contacto inicial sin detalles mecánicos."""
    texto_limpio = texto.strip().lower()

    saludos = [
        "hola", "holaa", "holaaa", "buenas", "buenos dias", "buenas tardes", "buenas noches",
        "hola buenas", "saludos", "hola que tal"
    ]

    tiene_componente = any(pm in texto_limpio for pm in VOCABULARIO_COMPONENTES)
    tiene_verbo = any(vf in texto_limpio for vf in VERBOS_FALLA)

    if texto_limpio in saludos or (
        any(s in texto_limpio for s in ["hola", "buenas"]) and not tiene_componente and not tiene_verbo
    ):
        return True, "👋 Hola. ¿Qué falla presenta el vehículo?"
    return False, ""


def es_respuesta_cordial(texto: str) -> bool:
    """Reconoce respuestas breves que no representan un síntoma nuevo."""
    limpio = texto.strip().lower().strip(" .,!¡¿?")
    return limpio in {
        "ok",
        "okay",
        "bien",
        "está bien",
        "esta bien",
        "entendido",
        "gracias",
        "perfecto",
        "listo",
        "de acuerdo",
    }


def es_continuacion_contextual(texto: str) -> bool:
    """Reconoce datos adicionales que deben unirse al síntoma anterior."""
    if es_respuesta_opcion_o_combustible(texto):
        return True
    limpio = texto.strip().lower()
    conectores = (
        "pero ", "ademas ", "además ", "tambien ", "también ",
        "y tambien ", "y además ", "el auto es ", "el carro es ",
        "funciona con ", "usa ", "es a gnv", "es gnv", "es a glp",
        "cuando usa ", "solo pasa ", "me olvide ", "me olvidé ",
        "en subida", "en bajada", "en pendiente", "en carretera",
        "en frío", "en frio", "en caliente", "en neutro", "en mínimo",
        "en minimo", "en ralentí", "en ralenti", "al acelerar", "al frenar",
        "en semáforo", "en semaforo", "con el aire", "con aire",
        "con el a/c", "con a/c", "con clima", "con las luces", "con luces",
        "con carga", "y cuando", "y al", "solo en", "con el motor",
    )
    return any(limpio.startswith(valor) or valor in limpio for valor in conectores)



def es_consulta_ambigua(texto: str) -> Tuple[bool, str]:
    """Determina si la consulta del usuario es incompleta o ambigua utilizando contexto técnico dinámico."""
    if es_respuesta_opcion_o_combustible(texto):
        return False, ""
    texto_limpio = texto.strip().lower()
    words = texto_limpio.split()

    if any(v in texto_limpio for v in ("vibracion", "vibración", "vibraciones", "vibra")) and not any(
        detalle in texto_limpio
        for detalle in (
            "freno",
            "frenar",
            "pisar el freno",
            "al frenar",
            "al acelerar",
            "acelerar",
            "velocidad",
            "km/h",
            "en minimo",
            "en ralenti",
            "volante",
            "asiento",
            "pedal",
            "zapatea",
            "zapateo",
        )
    ):
        return True, "🔎 ¿Vibra al frenar, a cierta velocidad o en mínimo?"

    frases_ambiguas = [
        "el carro falla", "mi auto falla", "mi carro falla", "tengo un problema", "tengo problemas",
        "tengo una falla", "ayuda", "falla el carro", "mi vehiculo falla", "mi coche falla",
        "falla mi carro", "mi auto tiene una falla", "ayuda con mi carro"
    ]

    # Consulta explícitamente genérica o vacía
    if texto_limpio in frases_ambiguas:
        return True, "⚠️ Especifique: ¿ocurre al arrancar, acelerar o frenar?"

    # Si el mensaje es descriptivo (>= 6 palabras) no declararlo ambiguo ciegamente
    if len(words) >= 6:
        return False, ""

    tiene_componente = any(comp in texto_limpio for comp in VOCABULARIO_COMPONENTES)
    tiene_verbo_falla = any(vf in texto_limpio for vf in VERBOS_FALLA)

    if tiene_componente and tiene_verbo_falla:
        return False, ""

    if len(words) < 3 or (not tiene_componente and not tiene_verbo_falla):
        # Preguntas de aclaración contextualizadas según el sistema mencionado
        if any(k in texto_limpio for k in ["puerta", "chapa", "cerradura", "pestillo", "seguro"]):
            return True, (
                "⚠️ Por favor, especifique el síntoma con más detalle. Por ejemplo: "
                "¿El control remoto acciona las demás puertas? ¿Se escucha accionar el actuador eléctrico? "
                "¿La puerta abre manualmente con la llave o la manija exterior?"
            )
        if any(k in texto_limpio for k in ["vidrio", "luna", "elevalunas", "ventana", "alzacristales"]):
            return True, (
                "⚠️ Por favor, especifique el síntoma con más detalle. Por ejemplo: "
                "¿El motor del elevalunas emite sonido al presionar el botón? "
                "¿El vidrio se cayó dentro de la puerta o está atascado en las guías?"
            )
        return True, "⚠️ Especifique: ¿ocurre al arrancar, acelerar o frenar?"

    return False, ""
