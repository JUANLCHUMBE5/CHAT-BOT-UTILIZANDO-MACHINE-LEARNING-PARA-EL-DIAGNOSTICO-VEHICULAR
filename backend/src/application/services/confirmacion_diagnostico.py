"""Interpretación segura de confirmaciones técnicas recibidas por WhatsApp e interactividad."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ConfirmacionDiagnosticoWhatsApp:
    """Comando explícito enviado por un mecánico para validar su último diagnóstico."""

    estado: str
    observacion: str | None = None
    requiere_observacion: bool = False


@dataclass
class SeleccionHipotesisTop3:
    """Interpretación conservadora de una respuesta sobre el Top-3 visible."""

    accion: str
    orden: int | None = None
    orden_descartado: int | None = None
    metodo: str | None = None
    texto_referencia: str | None = None


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", sin_tildes.strip().lower())


def _extraer_observacion(texto: str, prefijos: tuple[str, ...]) -> str | None:
    original = texto.strip()
    normalizado = _normalizar(original)
    for prefijo in sorted(prefijos, key=len, reverse=True):
        if normalizado == prefijo:
            return None
        if normalizado.startswith(prefijo):
            resto = original[len(prefijo) :].lstrip(" :–—\t")
            return resto.strip()[:4000] or None
    return None


def interpretar_confirmacion_whatsapp(
    texto: str,
) -> ConfirmacionDiagnosticoWhatsApp | None:
    """Reconoce únicamente órdenes explícitas para no confundir síntomas con validaciones."""

    normalizado = _normalizar(texto)
    confirmar = ("confirmar", "confirmado", "falla confirmada", "diagnostico confirmado")
    descartar = ("descartar", "descartado", "falla diferente", "diagnostico incorrecto")
    revisar = ("revisar", "en revision", "dejar en revision")

    for prefijos, estado, requiere_observacion in (
        (confirmar, "confirmado", False),
        (descartar, "descartado", True),
        (revisar, "en_revision", False),
    ):
        if any(
            normalizado == prefijo
            or normalizado.startswith(f"{prefijo}:")
            or normalizado.startswith(f"{prefijo} -")
            for prefijo in prefijos
        ):
            return ConfirmacionDiagnosticoWhatsApp(
                estado=estado,
                observacion=_extraer_observacion(texto, prefijos),
                requiere_observacion=requiere_observacion,
            )
    return None


def interpretar_respuesta_validacion_whatsapp(texto: str) -> str | None:
    """Interpreta un SÍ/NO únicamente cuando el flujo ya espera esa respuesta.

    Soporta texto libre y payloads de botones interactivos WhatsApp (conf_si, conf_no).
    """

    normalizado = _normalizar(texto).strip(" .,!¡¿?")

    # Soporte para payloads de botones interactivos WhatsApp
    if re.search(r"\bconf[_\-]?si\b|\bbtn[_\-]?si\b", normalizado) or normalizado.startswith("conf_si") or normalizado.startswith("btn_si"):
        return "si"
    if re.search(r"\bconf[_\-]?no\b|\bbtn[_\-]?no\b", normalizado) or normalizado.startswith("conf_no") or normalizado.startswith("btn_no"):
        return "no"

    respuestas_positivas = {
        "si",
        "correcto",
        "correcta",
        "fue correcto",
        "fue correcta",
        "esta bien",
    }
    respuestas_negativas = {
        "no",
        "incorrecto",
        "incorrecta",
        "fue incorrecto",
        "fue incorrecta",
        "esta mal",
    }
    # Descartar frases clínicas funcionales ("si tiene chispa...", "no arranca...", etc.)
    frases_clinicas = (
        "si tiene", "si hay", "si llega", "si pasa", "si marca", "si bota", "si suena", "si prende", "si arranca",
        "no tiene", "no hay", "no llega", "no pasa", "no marca", "no bota", "no suena", "no prende", "no arranca",
    )
    if any(normalizado.startswith(pref) for pref in frases_clinicas):
        return None

    # La puntuación tras «no» no transforma falta de herramientas en rechazo de hipótesis.
    if re.search(
        r"\bno\s+(?:(?:he|pude|puedo|logre)\s+)?"
        r"(?:revise|revisar|medi|medir|probe|probar|comprobe|comprobar|tengo|dispongo|cuento)(?:lo|la|los|las)?\b",
        normalizado,
    ):
        return None

    if normalizado in respuestas_positivas:
        return "si"
    if normalizado in respuestas_negativas:
        return "no"
    if re.match(r"^(?:no\s*[,:;\-]|(?:negativo|descartado|falso|no es|no fue|descartar)\b)", normalizado):
        return "no"
    if re.match(r"^(?:si\s*[,:;\-]|(?:fue correcto|fue correcta|esta bien)\b)", normalizado):
        return "si"
    return None


def instrucciones_confirmacion_whatsapp(cantidad_hipotesis: int = 3) -> str:
    """Pregunta breve que acompaña cada resultado dirigido a personal técnico."""
    if cantidad_hipotesis <= 1:
        return "\n\n¿Fue correcta? *SÍ / NO*"
    if cantidad_hipotesis == 2:
        return (
            "\n\n¿Fue correcta? *SÍ / NO* (1/2)\n"
            "O indica la opción a verificar:\n"
            "1. Primera hipótesis\n"
            "2. Segunda hipótesis"
        )
    return (
        "\n\n¿Fue correcta? *SÍ / NO* (1/2/3)\n"
        "O indica la opción a verificar:\n"
        "1. Primera hipótesis\n"
        "2. Segunda hipótesis\n"
        "3. Tercera hipótesis"
    )

def interpretar_seleccion_top3(
    texto: str,
    hipotesis: list[dict] | None = None,
) -> SeleccionHipotesisTop3 | None:
    """
    Interpreta selecciones naturales sobre un Top-3 YA presentado.

    Soporta botones interactivos (payload id 'hip_1_...' y títulos de botones),
    así como respuestas textuales ('1', '2', '3', 'primera', nombres).
    No ejecuta diagnósticos ni modifica probabilidades.
    Devuelve None cuando el mensaje no constituye una selección segura.
    """
    def norm(valor: str) -> str:
        valor = unicodedata.normalize("NFD", str(valor or "").lower())
        valor = "".join(c for c in valor if unicodedata.category(c) != "Mn")
        valor = re.sub(r"(?<=\d)[.,](?=\d)", "", valor)
        valor = re.sub(r"[^a-z0-9\s]", " ", valor)
        return re.sub(r"\s+", " ", valor).strip()

    t = norm(texto)

    if not t:
        return None

    # 0. Reconocimiento directo de botón interactivo de WhatsApp (payload id: hip_1_..., btn_hip_1_...)
    m_btn = re.search(r"\b(?:btn[_\-]?)?hip[_\-]?([1-9])\b", t)
    if m_btn:
        orden = int(m_btn.group(1))
        return SeleccionHipotesisTop3(
            accion="CONFIRMAR",
            orden=orden,
            metodo="boton_interactivo",
            texto_referencia=texto,
        )

    # "ninguna" descarta provisionalmente las opciones presentadas
    if re.fullmatch(r"(?:ninguna|ninguno|ninguna de las anteriores|ninguna opcion|ninguna alternativa)", t):
        return SeleccionHipotesisTop3(
            accion="NINGUNA",
            metodo="ninguna",
            texto_referencia=texto,
        )

    # "no sé" o incertidumbre técnica jamás equivale a NO/descarte físico.
    if re.search(r"\b(no se|nose|no estoy seguro|no estoy segura|sin verificar|aun no se|todavia no se)\b", t):
        return SeleccionHipotesisTop3(
            accion="NO_SE",
            metodo="incertidumbre",
            texto_referencia=texto,
        )

    referencias = {
        1: (r"\b1\b", r"\bprimera\b", r"\bprimero\b", r"\bopcion 1\b"),
        2: (r"\b2\b", r"\bsegunda\b", r"\bsegundo\b", r"\bopcion 2\b"),
        3: (r"\b3\b", r"\btercera\b", r"\btercero\b", r"\bopcion 3\b"),
    }

    mencionadas = []

    for orden, patrones in referencias.items():
        if any(re.search(p, t) for p in patrones):
            mencionadas.append(orden)

    # ------------------------------------------------------------
    # Caso mixto:
    # "la 1 no, la 2 sí"
    # "no es la primera, es la segunda"
    # ------------------------------------------------------------
    mapa = {
        "1": 1, "primera": 1,
        "2": 2, "segunda": 2,
        "3": 3, "tercera": 3,
    }

    # Forma frecuente: "la 1 no, la 2 si"
    mixto_simple = re.search(
        r"(?:la\s+|opcion\s+)?(1|2|3|primera|segunda|tercera)"
        r"\s+no\b.{0,35}?"
        r"(?:la\s+|opcion\s+)?(1|2|3|primera|segunda|tercera)"
        r"\s+si\b",
        t,
    )

    if mixto_simple:
        descartada = mapa[mixto_simple.group(1)]
        confirmada = mapa[mixto_simple.group(2)]

        if descartada != confirmada:
            return SeleccionHipotesisTop3(
                accion="DESCARTAR_Y_CONFIRMAR",
                orden=confirmada,
                orden_descartado=descartada,
                metodo="mixto",
                texto_referencia=texto,
            )

    # "no es la primera, es la segunda"
    mixto_es = re.search(
        r"no\s+es\s+(?:la\s+)?(1|2|3|primera|segunda|tercera)"
        r".{0,35}?"
        r"es\s+(?:la\s+)?(1|2|3|primera|segunda|tercera)",
        t,
    )

    if mixto_es:
        descartada = mapa[mixto_es.group(1)]
        confirmada = mapa[mixto_es.group(2)]

        if descartada != confirmada:
            return SeleccionHipotesisTop3(
                accion="DESCARTAR_Y_CONFIRMAR",
                orden=confirmada,
                orden_descartado=descartada,
                metodo="mixto",
                texto_referencia=texto,
            )

    # Más de una opción mencionada sin resolución clara.
    if len(set(mencionadas)) > 1:
        return SeleccionHipotesisTop3(
            accion="AMBIGUO",
            metodo="ambiguedad",
            texto_referencia=texto,
        )

    # ------------------------------------------------------------
    # Selección por número / ordinal
    # ------------------------------------------------------------
    if len(mencionadas) == 1:
        orden = mencionadas[0]

        negativo = bool(
            re.search(r"\bno\b", t)
            or "incorrect" in t
            or "descart" in t
        )

        if negativo:
            return SeleccionHipotesisTop3(
                accion="DESCARTAR",
                orden=orden,
                metodo="numero_ordinal",
                texto_referencia=texto,
            )

        # Un número/ordinal aislado dentro del contexto Top-3
        # o que inicia con el número de opción (como los títulos de botón "1. Fuga hidráulica")
        verbos_seleccion = (
            r"(?:es|seria|confirmo|correcta|correcto|acerto|fue|elijo|escojo|opto|"
            r"quiero|voy|vamos|prefiero|empecemos|empezar|iniciar|revisemos|revisar|"
            r"probar|chequear|ver|vamos\s+a\s+revisar|quiero\s+revisar|voy\s+a\s+revisar|"
            r"me\s+inclino\s+por|me\s+quedo\s+con)"
        )
        permitido = bool(
            re.fullmatch(
                r"(?:si\s+)?(?:la\s+)?(?:opcion\s+)?(?:numero\s+)?"
                r"(?:1|2|3|primera|segunda|tercera)"
                r"(?:\s+si)?",
                t,
            )
            or re.search(
                rf"\b{verbos_seleccion}\s+(?:por\s+|con\s+|en\s+)?(?:la\s+)?(?:opcion\s+)?(?:numero\s+)?(?:1|2|3|primera|segunda|tercera)\b",
                t,
            )
            or re.match(
                r"^(?:si\s+)?(?:la\s+)?(?:opcion\s+)?(?:numero\s+)?([1-3]|primera|segunda|tercera)\b",
                t,
            )
        )

        if permitido:
            return SeleccionHipotesisTop3(
                accion="CONFIRMAR",
                orden=orden,
                metodo="numero_ordinal",
                texto_referencia=texto,
            )

    # ------------------------------------------------------------
    # Selección conservadora por nombre de la falla
    # ------------------------------------------------------------
    if hipotesis:
        # Si el texto describe síntomas, limitaciones o explicaciones libres sin verbo de elección, no es selección
        tiene_marcador_eleccion = bool(
            re.search(
                r"\b(elijo|escojo|opto|me\s+inclino|me\s+quedo|confirmo|correcta|es\s+la\s+de|la\s+opcion\s+de|la\s+falla\s+es)\b",
                t,
            )
        )
        tiene_retroalimentacion_sintoma = bool(
            re.search(
                r"\b(no\s+tengo|no\s+puedo|no\s+cuento|no\s+dispongo|siento|escucho|nota|vibra|chirr|golpe|bache|pero\s+si|esponjoso|al\s+fondo|desmontar)\b",
                t,
            )
        )
        if len(t.split()) > 5 and not tiene_marcador_eleccion:
            return None
        if tiene_retroalimentacion_sintoma and not tiene_marcador_eleccion:
            return None

        STOP = {
            "de", "del", "la", "las", "el", "los", "por", "o", "y",
            "en", "con", "sin", "una", "un", "falla", "problema",
            "freno", "frenos", "motor", "rueda", "ruedas", "coche",
            "auto", "vehiculo", "pedal", "sistema", "parte", "delantera",
            "delanteras", "trasera", "traseras", "cuando", "donde",
        }

        tokens_usuario = {
            w for w in t.split()
            if len(w) >= 4 and w not in STOP
        }

        candidatos = []

        for idx, hip in enumerate(hipotesis[:3], start=1):
            if isinstance(hip, dict):
                nombre = (
                    hip.get("falla")
                    or hip.get("nombre")
                    or hip.get("diagnostico")
                    or ""
                )
            else:
                nombre = str(hip)

            n = norm(nombre)

            tokens_falla = {
                w for w in n.split()
                if len(w) >= 4 and w not in STOP
            }

            comunes = tokens_usuario & tokens_falla

            # Conservador:
            # exigir al menos una palabra distintiva suficientemente larga.
            if comunes:
                score = max(len(w) for w in comunes)
                candidatos.append((idx, score, comunes))

        if candidatos:
            candidatos.sort(key=lambda x: x[1], reverse=True)

            # Solo resolver si existe un candidato claramente superior
            mejor = candidatos[0]

            if len(candidatos) == 1 or (
                len(candidatos) > 1
                and mejor[1] > candidatos[1][1]
            ):
                return SeleccionHipotesisTop3(
                    accion="CONFIRMAR",
                    orden=mejor[0],
                    metodo="nombre",
                    texto_referencia=texto,
                )

    return None


def generar_titulo_boton_hipotesis(orden: int, falla: str, max_chars: int = 20) -> str:
    """Genera un título conciso y legible para un botón interactivo WhatsApp (máx 20 caracteres)."""
    prefijo = f"{orden}. "
    disponible = max(1, max_chars - len(prefijo))
    # Limpiar detalles entre paréntesis o notas accesorias
    nombre = falla.split("(")[0].strip()
    # Si contiene ' o ', tomar la causa primaria para no truncar a mitad de palabra
    if len(nombre) > disponible and " o " in nombre:
        nombre = nombre.split(" o ")[0].strip()
    if len(nombre) > disponible:
        palabras = nombre.split()
        acumulado = []
        for p in palabras:
            if len(" ".join(acumulado + [p])) <= disponible:
                acumulado.append(p)
            else:
                break
        nombre = " ".join(acumulado) if acumulado else nombre[:disponible]
    titulo = f"{prefijo}{nombre}".strip()
    return titulo[:max_chars]


def construir_botones_hipotesis(
    hipotesis_lista: list[Any],
    case_id: str | None = None,
) -> dict[str, Any]:
    """Construye la estructura de botones interactivos de WhatsApp para hipótesis.

    - 1 a 3 hipótesis: Botones Quick Reply ('type': 'button', máx 20 caracteres por botón).
    - Más de 3 hipótesis: Lista interactiva ('type': 'list').
    """
    cid_corto = str(case_id or "")[:8]
    total = len(hipotesis_lista)

    if total <= 3:
        botones = []
        action_buttons = []
        for idx, h in enumerate(hipotesis_lista[:3], start=1):
            falla = getattr(h, "falla", None) or getattr(h, "falla_probable", None)
            if not falla and isinstance(h, dict):
                falla = h.get("falla") or h.get("falla_probable") or h.get("nombre") or ""
            falla = str(falla or f"Hipótesis {idx}")
            titulo = generar_titulo_boton_hipotesis(idx, falla, max_chars=20)
            btn_id = f"hip_{idx}_{cid_corto}" if cid_corto else f"hip_{idx}"
            botones.append({"id": btn_id, "title": titulo})
            action_buttons.append({"type": "reply", "reply": {"id": btn_id, "title": titulo}})
        return {
            "tipo": "button",
            "type": "button",
            "botones": botones,
            "action": {"buttons": action_buttons},
        }
    else:
        filas = []
        for idx, h in enumerate(hipotesis_lista[:10], start=1):
            falla = getattr(h, "falla", None) or getattr(h, "falla_probable", None)
            if not falla and isinstance(h, dict):
                falla = h.get("falla") or h.get("falla_probable") or h.get("nombre") or ""
            falla = str(falla or f"Hipótesis {idx}")
            confianza = getattr(h, "probabilidad", None) or getattr(h, "confianza", None)
            if confianza is None and isinstance(h, dict):
                confianza = h.get("probabilidad") or h.get("confianza")
            desc = f"{int(float(confianza)*100)}% prob." if confianza is not None else ""
            titulo = generar_titulo_boton_hipotesis(idx, falla, max_chars=24)
            btn_id = f"hip_{idx}_{cid_corto}" if cid_corto else f"hip_{idx}"
            fila = {"id": btn_id, "title": titulo}
            if desc:
                fila["description"] = desc[:72]
            filas.append(fila)
        return {
            "tipo": "list",
            "type": "list",
            "boton_menu": "Ver hipótesis",
            "titulo_seccion": "Causas posibles",
            "filas": filas,
            "action": {
                "button": "Ver hipótesis",
                "sections": [{"title": "Causas posibles", "rows": filas}],
            },
        }


def construir_botones_confirmacion(case_id: str | None = None) -> dict[str, Any]:
    """Construye botones interactivos SÍ / NO para confirmación física de una hipótesis."""
    cid_corto = str(case_id or "")[:8]
    id_si = f"conf_si_{cid_corto}" if cid_corto else "conf_si"
    id_no = f"conf_no_{cid_corto}" if cid_corto else "conf_no"
    botones = [
        {"id": id_si, "title": "SÍ"},
        {"id": id_no, "title": "NO"},
    ]
    action_buttons = [
        {"type": "reply", "reply": {"id": id_si, "title": "SÍ"}},
        {"type": "reply", "reply": {"id": id_no, "title": "NO"}},
    ]
    return {
        "tipo": "button",
        "type": "button",
        "botones": botones,
        "action": {"buttons": action_buttons},
    }
