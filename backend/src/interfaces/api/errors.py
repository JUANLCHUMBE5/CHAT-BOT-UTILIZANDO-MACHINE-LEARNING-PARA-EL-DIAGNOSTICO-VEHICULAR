"""Manejadores uniformes de errores HTTP sin filtrar información sensible."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.logger import logger

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


def _mensaje(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        return detail["message"]
    return "La solicitud no pudo procesarse."


def _contenido_error(
    request: Request,
    status_code: int,
    detail: Any,
    *,
    details: Any | None = None,
) -> dict[str, Any]:
    return {
        "detail": detail,
        "code": _STATUS_CODES.get(status_code, f"HTTP_{status_code}"),
        "message": _mensaje(detail),
        "request_id": _request_id(request),
        "details": details,
    }


async def manejar_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_contenido_error(request, exc.status_code, exc.detail),
        headers=exc.headers,
    )


async def manejar_error_validacion(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errores = [
        {
            "location": [str(parte) for parte in error.get("loc", ())],
            "message": error.get("msg", "Valor inválido"),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    detail = "Los datos enviados no cumplen el contrato de la API."
    return JSONResponse(
        status_code=422,
        content=_contenido_error(request, 422, detail, details=errores),
    )


async def manejar_error_no_controlado(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Error no controlado request_id=%s ruta=%s",
        _request_id(request),
        request.url.path,
        exc_info=exc,
    )
    detail = "Ocurrió un error interno. Use request_id para solicitar soporte."
    return JSONResponse(
        status_code=500,
        content=_contenido_error(request, 500, detail),
    )
