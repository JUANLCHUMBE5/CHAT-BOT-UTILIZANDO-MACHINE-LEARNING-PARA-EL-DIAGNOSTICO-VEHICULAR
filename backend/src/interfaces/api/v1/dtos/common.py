"""DTOs compartidos para respuestas y errores HTTP."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MessageResponseDTO(BaseModel):
    mensaje: str


class ErrorResponseDTO(BaseModel):
    """Contrato uniforme que conserva ``detail`` por compatibilidad FastAPI."""

    detail: Any
    code: str
    message: str
    request_id: str
    details: Any | None = None
