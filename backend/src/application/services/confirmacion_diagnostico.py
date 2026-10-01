"""Interpretación segura de confirmaciones técnicas recibidas por WhatsApp."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfirmacionDiagnosticoWhatsApp:
    """Comando explícito enviado por un mecánico para validar su último diagnóstico."""

    estado: str
    observacion: str | None = None
    requiere_observacion: bool = False


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
            resto = original[len(prefijo) :].lstrip(" :-–—\t")
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
    """Interpreta un SÍ/NO únicamente cuando el flujo ya espera esa respuesta."""

    normalizado = _normalizar(texto).strip(" .,!¡¿?")
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

    if normalizado in respuestas_positivas:
        return "si"
    if normalizado in respuestas_negativas:
        return "no"
    if re.match(r"^(?:no\s*[,:;\-]|(?:negativo|descartado|falso|no es|no fue|descartar)\b)", normalizado):
        return "no"
    if re.match(r"^(?:si\s*[,:;\-]|(?:fue correcto|fue correcta|esta bien)\b)", normalizado):
        return "si"
    return None


def instrucciones_confirmacion_whatsapp() -> str:
    """Pregunta breve que acompaña cada resultado dirigido a personal técnico."""

    return (
        "\n\n🔎 ¿Fue correcta? *SÍ / NO*"
    )


@dataclass
class SeleccionHipotesisTop3:
    """Interpretación conservadora de una respuesta sobre el Top-3 visible."""
    accion: str
    orden: int | None = None
    orden_descartado: int | None = None
    metodo: str | None = None
    texto_referencia: str | None = None


def interpretar_seleccion_top3(
    texto: str,
    hipotesis: list[dict] | None = None,
) -> SeleccionHipotesisTop3 | None:
    """
    Interpreta selecciones naturales sobre un Top-3 YA presentado.

    No ejecuta diagnósticos ni modifica probabilidades.
    Devuelve None cuando el mensaje no constituye una selección segura.
    """
    import re
    import unicodedata

    def norm(valor: str) -> str:
        valor = unicodedata.normalize("NFD", str(valor or "").lower())
        valor = "".join(c for c in valor if unicodedata.category(c) != "Mn")
        valor = re.sub(r"[^a-z0-9\s]", " ", valor)
        return re.sub(r"\s+", " ", valor).strip()

    t = norm(texto)

    if not t:
        return None

    # "no sé" jamás equivale a NO/descarte.
    if re.search(r"\b(no se|nose|no estoy seguro|no estoy segura)\b", t):
        nums = {
            int(n)
            for n in re.findall(r"\b([123])\b", t)
        }
        return SeleccionHipotesisTop3(
            accion="AMBIGUO",
            metodo="ambiguedad",
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
    negativo_positivo = re.search(
        r"(?:no\s+es\s+)?(?:la\s+|opcion\s+)?"
        r"(1|2|3|primera|segunda|tercera)"
        r"\s*(?:no|incorrecta|incorrecto)?"
        r".{0,35}?"
        r"(?:si|es)\s+(?:la\s+|opcion\s+)?"
        r"(1|2|3|primera|segunda|tercera)",
        t,
    )

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
        # se considera selección afirmativa.
        permitido = bool(
            re.fullmatch(
                r"(?:si\s+)?(?:la\s+|opcion\s+)?"
                r"(?:1|2|3|primera|segunda|tercera)"
                r"(?:\s+si)?",
                t,
            )
            or re.search(
                r"\b(es|seria|confirmo|correcta|correcto)\s+"
                r"(?:la\s+|opcion\s+)?(?:1|2|3|primera|segunda|tercera)\b",
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
        STOP = {
            "de", "del", "la", "las", "el", "los", "por", "o", "y",
            "en", "con", "sin", "una", "un", "falla", "problema"
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

