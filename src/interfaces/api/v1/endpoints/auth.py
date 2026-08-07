import hmac

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from src.core.security import crear_jwt_token
from src.config import settings
from src.limiter import limiter

router = APIRouter()

class LoginRequestDTO(BaseModel):
    username: str
    password: str

class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 7200  # 2 horas
    mensaje: str = "Token válido por 2 horas. Incluir en header: Authorization: Bearer <token>"

@router.post("/login", response_model=TokenResponseDTO, summary="Generar Token JWT con validez de 2 horas")
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequestDTO):
    """
    Endpoint de Autenticación para obtener un Token JWT de 2 horas.
    Las credenciales se configuran vía variables de entorno AUTH_USERNAME y AUTH_PASSWORD.
    """
    expected_user = getattr(settings, "auth_username", "admin")
    expected_pass = getattr(settings, "auth_password", "carbot2026")
    
    usuario_valido = hmac.compare_digest(payload.username.encode(), expected_user.encode())
    password_valido = hmac.compare_digest(payload.password.encode(), expected_pass.encode())
    if usuario_valido and password_valido:
        token = crear_jwt_token(sub=payload.username)
        return TokenResponseDTO(access_token=token)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas."
    )
