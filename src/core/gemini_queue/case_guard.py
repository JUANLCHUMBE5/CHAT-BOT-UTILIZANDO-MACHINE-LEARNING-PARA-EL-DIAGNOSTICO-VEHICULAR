"""Guards for preventing asynchronous diagnostic work from crossing case boundaries."""

from __future__ import annotations

from typing import Any


def case_id_from_context(context: dict[str, Any] | None) -> str | None:
    """Return a single unambiguous active case ID from persisted conversation context."""
    if not isinstance(context, dict):
        return None
    nested = context.get("conversation_state")
    nested_id = nested.get("case_id") if isinstance(nested, dict) else None
    outer_id = context.get("case_id")
    if outer_id and nested_id and str(outer_id) != str(nested_id):
        return None
    active_id = nested_id or outer_id
    return str(active_id) if active_id else None


def solicitud_corresponde_a_caso(
    solicitud_case_id: str | None,
    conversation_context: dict[str, Any] | None,
    *,
    diagnostico_id: str | None = None,
    tipo_consulta: str = "diagnostico",
) -> bool:
    """Fail closed for diagnostic replies without an exact active-case match."""
    if tipo_consulta == "consulta_tecnica" and not diagnostico_id and not solicitud_case_id:
        return True
    active_case_id = case_id_from_context(conversation_context)
    return bool(solicitud_case_id and active_case_id and str(solicitud_case_id) == active_case_id)
