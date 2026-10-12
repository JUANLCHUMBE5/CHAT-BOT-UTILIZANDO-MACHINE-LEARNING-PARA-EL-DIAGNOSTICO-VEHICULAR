"""Formulación de preguntas dirigidas al Top-3, post-descarte y salida de límite."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from src.core.conversacion.generacion_preguntas.compatibilidad import puede_preguntar
from src.core.conversacion.models import QuestionIntent
from src.core.diagnostico.auto_interrogador import MAPA_DESCRIPCION_OPCION

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState


def generar_pregunta_discriminante_top3(
    top_candidatos: List[str],
    estado: ConversationState,
) -> Optional[Tuple[str, List[str], List[str], QuestionIntent]]:
    """Genera una pregunta dirigida a diferenciar el Top-3 de hipótesis diagnósticas."""
    if not puede_preguntar(QuestionIntent.DISCRIMINACION_TOP3, estado):
        return None

    candidatos = [c for c in top_candidatos[:3] if c]
    if len(candidatos) < 2:
        return None

    opciones_texto = []
    hipotesis_validas = []
    for c in candidatos:
        desc = MAPA_DESCRIPCION_OPCION.get(c)
        if not desc:
            desc = f"La falla coincide con: {c}"
        opciones_texto.append(desc)
        hipotesis_validas.append(c)

    iconos = ["1️⃣", "2️⃣", "3️⃣"]
    lineas_opciones = [
        f"{iconos[i]} {opciones_texto[i]}" for i in range(len(opciones_texto))
    ]

    texto = (
        "Para confirmar la causa exacta entre las posibilidades principales, "
        "¿cuál de las siguientes situaciones describe mejor el comportamiento de tu vehículo?\n\n"
        + "\n".join(lineas_opciones)
        + "\n\nResponde indicando el número (1, 2"
        + (", o 3" if len(opciones_texto) == 3 else "")
        + ")."
    )

    return texto, opciones_texto, hipotesis_validas, QuestionIntent.DISCRIMINACION_TOP3


def formular_pregunta_discriminante_post_descarte(
    estado: ConversationState,
    falla_descartada: str,
) -> Tuple[str, QuestionIntent]:
    """Formula pregunta técnica discriminante adaptativa excluyendo hechos ya conocidos."""
    from src.core.conversacion.filtro_preguntas_discriminantes import FiltroPreguntasDiscriminantes

    return FiltroPreguntasDiscriminantes.formular(estado, falla_descartada)


def construir_salida_limite_repreguntas(
    top_candidatos: List[str],
    confianzas: List[float],
    estado: ConversationState,
) -> str:
    """Genera respuesta compacta cuando se alcanza el límite de repreguntas."""
    from src.core.conversacion.formateador_compacto import FormateadorCompacto

    hipotesis = []
    for i, c in enumerate(top_candidatos[:3]):
        conf = confianzas[i] if i < len(confianzas) else 0.10
        hipotesis.append({"falla": c, "probabilidad": conf})

    return FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=hipotesis,
        sintoma_original="",
    )
