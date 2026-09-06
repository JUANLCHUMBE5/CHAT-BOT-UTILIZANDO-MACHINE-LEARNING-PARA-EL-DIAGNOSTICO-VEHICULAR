"""Contratos de autenticación y ciclo de sesión."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.core.security import JWT_EXPIRATION_SECONDS, JWT_REFRESH_EXPIRATION_SECONDS


class LoginRequestDTO(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class UserInfoDTO(BaseModel):
    id: Optional[str] = None
    username: str
    nombre: str
    rol: str
    taller_id: str
    taller_nombre: str
    requiere_cambio_password: bool = False


class CambiarPasswordDTO(BaseModel):
    password_actual: str
    password_nuevo: str = Field(min_length=12, max_length=128)


class RefreshTokenDTO(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in_seconds: int = JWT_EXPIRATION_SECONDS
    refresh_expires_in_seconds: int = JWT_REFRESH_EXPIRATION_SECONDS
    mensaje: str = "Token de acceso temporal. Incluir en Authorization: Bearer <token>"
    user: Optional[UserInfoDTO] = None
