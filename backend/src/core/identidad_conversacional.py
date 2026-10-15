"""Identidad técnica por ámbito; las placas nunca identifican sesiones globales."""
from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5


def es_identificador_provisional(valor: str | None) -> bool:
    token = "".join(c for c in (valor or "").upper() if c.isalnum())
    return not token or token in {"RESTAPI", "WAPP01", "SINPLACA"} or token.startswith("PROV")


def clave_sesion_rest(taller_id: str, usuario_id: str, sesion: str | None, placa: str | None) -> str:
    """Aisla incluso un session_id elegido por dos usuarios o talleres distintos."""
    referencia = sesion or placa
    if not referencia:
        raise ValueError("Se requiere una sesión explícita para un vehículo sin placa.")
    return str(uuid5(NAMESPACE_URL, f"carbot/rest/{taller_id}/{usuario_id}/{referencia}"))


def identificador_provisional(taller_id: str, conversacion_id: str, case_id: str) -> str:
    """Derivado estable del caso; no representa matrícula ni se persiste como vehículo."""
    if not all((taller_id, conversacion_id, case_id)):
        raise ValueError("Un provisional necesita taller, conversación y caso.")
    return "PROV_" + uuid5(NAMESPACE_URL, f"{taller_id}/{conversacion_id}/{case_id}").hex
