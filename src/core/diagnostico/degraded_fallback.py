"""Generación de respuestas locales deterministas en modo degradado (sin LLM o ante fallo de red)."""

from __future__ import annotations

from typing import Tuple


def generar_respuesta_degradada(
    tipo_consulta: str,
    contexto_manual: str,
    titulo_manual: str,
    diagnostico_ml: str,
    confianza_pct: int,
    alerta_revision: str,
) -> Tuple[str, dict]:
    """Genera una respuesta técnica determinista basada exclusivamente en ML y RAG."""
    no_manual = "No se encontró" in (contexto_manual or "") or "Coincidencia baja" in (titulo_manual or "")

    if tipo_consulta == "consulta_tecnica":
        if no_manual:
            respuesta_tecnica = (
                "💡 *Consulta técnica identificada*\n\n"
                "No encontré una fuente documental suficientemente cercana para dar una cifra "
                "exacta con seguridad. Puedes agregar, si los conoces, marca, modelo, año, motor "
                "y el equipo GNV/GLP. Estos datos son opcionales; verifica la especificación "
                "en el manual del fabricante o con un centro autorizado."
            )
        else:
            respuesta_tecnica = (
                f"💡 *Orientación técnica — {titulo_manual}*\n\n{contexto_manual}\n\n"
                "Confirma la especificación exacta en el manual correspondiente al modelo y año."
            )
        return respuesta_tecnica, {
            "usado": False,
            "modelo": None,
            "modo": "consulta_tecnica_degradada",
            "tokens_entrada": 0,
            "tokens_salida": 0,
        }

    seccion_1 = (
        f"🛠️ **1. Posible Falla Vehicular (Modo Degradado ML+RAG):**\n"
        f"• **Diagnóstico Sugerido (ML):** {diagnostico_ml}\n"
        f"• **Certeza del Modelo:** {confianza_pct}%{alerta_revision}"
    )

    if no_manual:
        seccion_2 = (
            "📖 **2. Procedimiento Técnico de Reparación:**\n"
            "⚠️ *Nota:* No se encontró un procedimiento específico en el manual de taller para esta consulta. "
            "Se sugiere revisión visual directa."
        )
        seccion_3 = (
            "⏱️ **3. Tiempo Estimado y Gravedad:**\n"
            "• **Tiempo Estimado:** 30-45 minutos (Evaluación inicial)\n"
            "• **Gravedad:** Por determinar en taller"
        )
    else:
        seccion_2 = (
            f"📖 **2. Procedimiento Técnico de Reparación ({titulo_manual}):**\n"
            f"{contexto_manual}"
        )
        seccion_3 = (
            "⏱️ **3. Tiempo Estimado y Gravedad:**\n"
            "• **Recomendación Técnica:** Siga los pasos del manual de taller adjunto y realice las pruebas de verificación correspondientes."
        )

    return f"{seccion_1}\n\n{seccion_2}\n\n{seccion_3}", {
        "usado": False,
        "modelo": None,
        "modo": "diagnostico_degradado_ml_rag",
        "tokens_entrada": 0,
        "tokens_salida": 0,
    }
