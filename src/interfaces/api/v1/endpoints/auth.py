import hmac
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.security import (
    crear_jwt_token,
    generar_password_hash,
    verificar_jwt_token_sin_restriccion,
    verificar_password,
)
from src.config import settings
from src.limiter import limiter
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Usuario
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository

router = APIRouter()


class LoginRequestDTO(BaseModel):
    username: str
    password: str


class UserInfoDTO(BaseModel):
    username: str
    nombre: str
    rol: str
    taller_id: str
    taller_nombre: str
    requiere_cambio_password: bool = False


class CambiarPasswordDTO(BaseModel):
    password_actual: str
    password_nuevo: str = Field(min_length=12, max_length=128)


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 7200  # 2 horas
    mensaje: str = "Token válido por 2 horas. Incluir en header: Authorization: Bearer <token>"
    user: Optional[UserInfoDTO] = None


@router.post("/login", response_model=TokenResponseDTO, summary="Generar Token JWT con validez de 2 horas")
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequestDTO):
    """
    Endpoint de Autenticación seguro que valida la contraseña almacenada en PostgreSQL.
    Rechaza usuarios no registrados, bloqueados o contraseñas inválidas.
    """
    expected_user = getattr(settings, "auth_username", "admin")
    expected_pass = getattr(settings, "auth_password", "carbot2026")

    # Fallback para entorno de pruebas unitarias sin PostgreSQL
    if not database_configurada():
        u_valid = hmac.compare_digest(payload.username.encode(), expected_user.encode())
        p_valid = hmac.compare_digest(payload.password.encode(), expected_pass.encode())
        if u_valid and p_valid:
            token = crear_jwt_token(sub=payload.username, rol="administrador")
            return TokenResponseDTO(
                access_token=token,
                user=UserInfoDTO(
                    username=payload.username,
                    nombre="Juan Carlos Chumbe",
                    rol="administrador",
                    taller_id="00000000-0000-0000-0000-000000000001",
                    taller_nombre="Taller Autorizado Carabayllo",
                    requiere_cambio_password=False,
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación inválidas.",
        )

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)

        # 1. Buscar usuario en PostgreSQL por nombres o por teléfono/WhatsApp
        usuario = None
        if sum(c.isdigit() for c in payload.username) >= 6:
            usuario = await user_repo.buscar_por_telefono(payload.username)

        if not usuario:
            stmt = (
                select(Usuario)
                .options(selectinload(Usuario.taller), selectinload(Usuario.rol))
                .where(Usuario.nombres == payload.username)
            )
            coincidencias = list((await session.execute(stmt)).scalars().all())
            if len(coincidencias) > 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Existe más de un usuario con ese nombre. Ingrese con su teléfono.",
                )
            usuario = coincidencias[0] if coincidencias else None

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de autenticación inválidas.",
            )

        if getattr(usuario, "bloqueado", False) or not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El acceso de este usuario se encuentra bloqueado o inactivo.",
            )

        # 2. Verificar contraseña PBKDF2 (600,000 iteraciones)
        if not verificar_password(payload.password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de autenticación inválidas.",
            )

        rol_codigo = usuario.rol.codigo if usuario.rol else "mecanico"
        token = crear_jwt_token(
            sub=usuario.nombres,
            rol=rol_codigo,
            taller_id=str(usuario.taller_id),
            usuario_id=str(usuario.id),
            extra_claims={"requiere_cambio_password": bool(usuario.debe_cambiar_password)},
        )

        return TokenResponseDTO(
            access_token=token,
            user=UserInfoDTO(
                username=usuario.nombres,
                nombre=f"{usuario.nombres} {usuario.apellidos or ''}".strip(),
                rol=rol_codigo,
                taller_id=str(usuario.taller_id),
                taller_nombre=usuario.taller.nombre if usuario.taller else "Taller Mecánico",
                requiere_cambio_password=bool(usuario.debe_cambiar_password),
            ),
        )


@router.post("/cambiar-password", summary="Cambiar la contraseña del usuario autenticado")
@limiter.limit("5/minute")
async def cambiar_password(
    request: Request,
    payload: CambiarPasswordDTO,
    token_payload: dict = Depends(verificar_jwt_token_sin_restriccion),
):
    """Cambia la contraseña y elimina la marca de cambio obligatorio."""
    if payload.password_actual == payload.password_nuevo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña nueva debe ser diferente de la contraseña actual.",
        )
    if not (
        any(c.islower() for c in payload.password_nuevo)
        and any(c.isupper() for c in payload.password_nuevo)
        and any(c.isdigit() for c in payload.password_nuevo)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña nueva debe incluir mayúsculas, minúsculas y números.",
        )
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    try:
        usuario_id = uuid.UUID(str(token_payload.get("usuario_id", "")))
        taller_id = uuid.UUID(str(token_payload.get("taller_id", "")))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Token de usuario inválido.") from exc

    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        usuario = await session.get(Usuario, usuario_id)
        if not usuario or usuario.taller_id != taller_id:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en el taller.")
        if usuario.bloqueado or not usuario.activo:
            raise HTTPException(status_code=403, detail="Usuario bloqueado o inactivo.")
        if not verificar_password(payload.password_actual, usuario.password_hash):
            raise HTTPException(status_code=401, detail="La contraseña actual no es válida.")

        usuario.password_hash = generar_password_hash(payload.password_nuevo)
        usuario.debe_cambiar_password = False
        await session.commit()

    token_nuevo = crear_jwt_token(
        sub=usuario.nombres,
        rol=str(token_payload.get("rol", "mecanico")),
        taller_id=str(usuario.taller_id),
        usuario_id=str(usuario.id),
        extra_claims={"requiere_cambio_password": False},
    )
    return {
        "mensaje": "Contraseña actualizada correctamente.",
        "access_token": token_nuevo,
    }
