"""Servicios de aplicación públicos, cargados de forma diferida para evitar ciclos."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ConfirmacionDiagnosticoWhatsApp",
    "GestorDiagnostico",
    "PrediccionML",
    "ResultadoDiagnostico",
    "instrucciones_confirmacion_whatsapp",
    "interpretar_confirmacion_whatsapp",
    "interpretar_respuesta_validacion_whatsapp",
]


def __getattr__(nombre: str) -> Any:
    if nombre in {"GestorDiagnostico", "PrediccionML", "ResultadoDiagnostico"}:
        from src.application.services import diagnostics

        return getattr(diagnostics, nombre)
    if nombre in {
        "ConfirmacionDiagnosticoWhatsApp",
        "instrucciones_confirmacion_whatsapp",
        "interpretar_confirmacion_whatsapp",
        "interpretar_respuesta_validacion_whatsapp",
    }:
        from src.application.services import confirmacion_diagnostico

        return getattr(confirmacion_diagnostico, nombre)
    raise AttributeError(f"El módulo {__name__!r} no exporta {nombre!r}")
