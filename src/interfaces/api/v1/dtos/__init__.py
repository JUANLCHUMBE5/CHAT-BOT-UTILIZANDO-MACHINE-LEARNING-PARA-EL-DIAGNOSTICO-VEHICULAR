"""Contratos HTTP centralizados de la API v1."""

from src.interfaces.api.v1.dtos.auth import (
    CambiarPasswordDTO,
    LoginRequestDTO,
    RefreshTokenDTO,
    TokenResponseDTO,
    UserInfoDTO,
)
from src.interfaces.api.v1.dtos.common import ErrorResponseDTO, MessageResponseDTO

__all__ = [
    "CambiarPasswordDTO",
    "ErrorResponseDTO",
    "LoginRequestDTO",
    "MessageResponseDTO",
    "RefreshTokenDTO",
    "TokenResponseDTO",
    "UserInfoDTO",
]
