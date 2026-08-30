import hmac
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.core.login_attempt_store import login_attempt_store
from src.core.refresh_token_store import refresh_token_store
from src.core.security import (
    JWT_EXPIRATION_SECONDS,
    JWT_REFRESH_EXPIRATION_SECONDS,
    crear_jwt_token,
    crear_refresh_token,
    generar_password_hash,
    verificar_jwt_token_sin_restriccion,
    verificar_password,
    verificar_refresh_token,
)
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Usuario
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository
from src.limiter import limiter

router = APIRouter()


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
    mensaje: str = "Token válido por 2 horas. Incluir en header: Authorization: Bearer <token>"
    user: Optional[UserInfoDTO] = None


def _guardar_cookie_refresh(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=JWT_REFRESH_EXPIRATION_SECONDS,
        httponly=True,
        secure=settings.is_production,
        samesite=settings.refresh_cookie_samesite,
        path="/api/v1/auth",
    )


async def _registrar_refresh(response: Response, token: str) -> dict:
    payload = verificar_refresh_token(token)
    await refresh_token_store.registrar(payload)
    _guardar_cookie_refresh(response, token)
    return payload


def _refresh_compatible(token: str) -> Optional[str]:
    return token if settings.legacy_refresh_token_body else None


@router.post("/login", response_model=TokenResponseDTO, summary="Generar Token JWT con validez de 2 horas")
@limiter.limit("5/minute")
async def login(request: Request, response: Response, payload: LoginRequestDTO):
    """
    Endpoint de Autenticación seguro que valida la contraseña almacenada en PostgreSQL.
    Rechaza usuarios no registrados, bloqueados o contraseñas inválidas.
    """
    clave_intentos = login_attempt_store.clave(
        payload.username,
        request.client.host if request.client else "unknown",
    )
    if not await login_attempt_store.permitido(clave_intentos):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intente nuevamente más tarde.",
            headers={"Retry-After": str(settings.login_lockout_seconds)},
        )

    # Fallback para entorno de pruebas unitarias sin PostgreSQL
    if not database_configurada():
        expected_user = settings.fallback_auth_username
        expected_pass = settings.fallback_auth_password
        if not expected_user or not expected_pass:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="La autenticación local no está configurada.",
            )
        u_valid = hmac.compare_digest(payload.username.encode(), expected_user.encode())
        p_valid = hmac.compare_digest(payload.password.encode(), expected_pass.encode())
        if u_valid and p_valid:
            await login_attempt_store.limpiar(clave_intentos)
            token = crear_jwt_token(sub=payload.username, rol="administrador")
            refresh_token = crear_refresh_token(sub=payload.username, rol="administrador")
            await _registrar_refresh(response, refresh_token)
            return TokenResponseDTO(
                access_token=token,
                refresh_token=_refresh_compatible(refresh_token),
                user=UserInfoDTO(
                    id="00000000-0000-0000-0000-000000000001",
                    username=payload.username,
                    nombre="Juan Carlos Chumbe",
                    rol="administrador",
                    taller_id="00000000-0000-0000-0000-000000000001",
                    taller_nombre="Taller Autorizado Carabayllo",
                    requiere_cambio_password=False,
                ),
            )
        await login_attempt_store.registrar_fallo(clave_intentos)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación inválidas.",
        )

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)

        # 1. Buscar usuario en PostgreSQL por teléfono/WhatsApp, username o nombres (fallback)
        usuario = None
        if sum(c.isdigit() for c in payload.username) >= 6:
            usuario = await user_repo.buscar_por_telefono(payload.username)

        if not usuario:
            usuario = await user_repo.buscar_por_username(payload.username)

        if not usuario:
            stmt = (
                select(Usuario)
                .options(selectinload(Usuario.taller), selectinload(Usuario.rol))
                .where(func.lower(Usuario.nombres) == payload.username.strip().lower())
            )
            coincidencias = list((await session.execute(stmt)).scalars().all())
            if len(coincidencias) > 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Existe más de un usuario con ese nombre. Ingrese con su nombre de usuario o teléfono.",
                )
            usuario = coincidencias[0] if coincidencias else None

        if not usuario:
            await login_attempt_store.registrar_fallo(clave_intentos)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de autenticación inválidas.",
            )

        if getattr(usuario, "bloqueado", False) or not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El acceso de este usuario se encuentra bloqueado o inactivo.",
            )

        rol_codigo = usuario.rol.codigo if usuario.rol else "cliente"
        if rol_codigo not in {"administrador", "admin"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El panel web es exclusivo para administradores. Los mecánicos trabajan mediante el chatbot de WhatsApp.",
            )

        # 2. Verificar contraseña PBKDF2 (600,000 iteraciones)
        if not verificar_password(payload.password, usuario.password_hash):
            await login_attempt_store.registrar_fallo(clave_intentos)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de autenticación inválidas.",
            )

        await login_attempt_store.limpiar(clave_intentos)
        token = crear_jwt_token(
            sub=usuario.username or usuario.nombres,
            rol=rol_codigo,
            taller_id=str(usuario.taller_id),
            usuario_id=str(usuario.id),
            extra_claims={"requiere_cambio_password": bool(usuario.debe_cambiar_password)},
        )
        refresh_token = crear_refresh_token(
            sub=usuario.username or usuario.nombres,
            rol=rol_codigo,
            taller_id=str(usuario.taller_id),
            usuario_id=str(usuario.id),
            extra_claims={"requiere_cambio_password": bool(usuario.debe_cambiar_password)},
        )
        await _registrar_refresh(response, refresh_token)

        display_username = usuario.username or usuario.nombres
        return TokenResponseDTO(
            access_token=token,
            refresh_token=_refresh_compatible(refresh_token),
            user=UserInfoDTO(
                id=str(usuario.id),
                username=display_username,
                nombre=f"{usuario.nombres} {usuario.apellidos or ''}".strip(),
                rol=rol_codigo,
                taller_id=str(usuario.taller_id),
                taller_nombre=usuario.taller.nombre if usuario.taller else "Taller Mecánico",
                requiere_cambio_password=bool(usuario.debe_cambiar_password),
            ),
        )


@router.post("/refresh", response_model=TokenResponseDTO, summary="Renovar automáticamente la sesión")
@limiter.limit("30/minute")
async def refresh_session(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenDTO] = None,
):
    """Rota el refresh token y emite un acceso nuevo tras validar la cuenta."""
    refresh_recibido = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_recibido and payload:
        refresh_recibido = payload.refresh_token
    if not refresh_recibido:
        raise HTTPException(status_code=401, detail="Falta la sesión de renovación segura.")
    token_payload = verificar_refresh_token(refresh_recibido)
    rol_claim = str(token_payload.get("rol", ""))
    if rol_claim not in {"administrador", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El panel web es exclusivo para administradores.",
        )

    if not database_configurada():
        sub = str(token_payload.get("sub", "admin"))
        taller_id = str(token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
        usuario_id = str(token_payload.get("usuario_id", "00000000-0000-0000-0000-000000000001"))
        requiere_cambio = bool(token_payload.get("requiere_cambio_password", False))
        refresh_nuevo = crear_refresh_token(
            sub=sub,
            rol=rol_claim,
            taller_id=taller_id,
            usuario_id=usuario_id,
            extra_claims={"requiere_cambio_password": requiere_cambio},
        )
        payload_nuevo = verificar_refresh_token(refresh_nuevo)
        if not await refresh_token_store.rotar(token_payload, payload_nuevo):
            raise HTTPException(status_code=401, detail="La sesión ya fue utilizada o revocada.")
        _guardar_cookie_refresh(response, refresh_nuevo)
        return TokenResponseDTO(
            access_token=crear_jwt_token(
                sub=sub,
                rol=rol_claim,
                taller_id=taller_id,
                usuario_id=usuario_id,
                extra_claims={"requiere_cambio_password": requiere_cambio},
            ),
            refresh_token=_refresh_compatible(refresh_nuevo),
        )

    try:
        usuario_id_uuid = uuid.UUID(str(token_payload.get("usuario_id", "")))
        taller_id_uuid = uuid.UUID(str(token_payload.get("taller_id", "")))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Refresh token de usuario inválido.") from exc

    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.taller), selectinload(Usuario.rol))
            .where(Usuario.id == usuario_id_uuid, Usuario.taller_id == taller_id_uuid)
        )
        usuario = (await session.execute(stmt)).scalar_one_or_none()
        if not usuario or usuario.bloqueado or not usuario.activo:
            raise HTTPException(status_code=403, detail="La cuenta fue bloqueada, desactivada o eliminada.")
        rol_codigo = usuario.rol.codigo if usuario.rol else "cliente"
        if rol_codigo not in {"administrador", "admin"}:
            raise HTTPException(status_code=403, detail="La cuenta ya no posee acceso administrativo.")

        requiere_cambio = bool(usuario.debe_cambiar_password)
        claims = {"requiere_cambio_password": requiere_cambio}
        refresh_nuevo = crear_refresh_token(
            sub=usuario.nombres,
            rol=rol_codigo,
            taller_id=str(usuario.taller_id),
            usuario_id=str(usuario.id),
            extra_claims=claims,
        )
        payload_nuevo = verificar_refresh_token(refresh_nuevo)
        if not await refresh_token_store.rotar(token_payload, payload_nuevo):
            raise HTTPException(status_code=401, detail="La sesión ya fue utilizada o revocada.")
        _guardar_cookie_refresh(response, refresh_nuevo)
        return TokenResponseDTO(
            access_token=crear_jwt_token(
                sub=usuario.nombres,
                rol=rol_codigo,
                taller_id=str(usuario.taller_id),
                usuario_id=str(usuario.id),
                extra_claims=claims,
            ),
            refresh_token=_refresh_compatible(refresh_nuevo),
            user=UserInfoDTO(
                id=str(usuario.id),
                username=usuario.nombres,
                nombre=f"{usuario.nombres} {usuario.apellidos or ''}".strip(),
                rol=rol_codigo,
                taller_id=str(usuario.taller_id),
                taller_nombre=usuario.taller.nombre if usuario.taller else "Taller Mecánico",
                requiere_cambio_password=requiere_cambio,
            ),
        )


@router.post("/cambiar-password", summary="Cambiar la contraseña del usuario autenticado")
@limiter.limit("5/minute")
async def cambiar_password(
    request: Request,
    response: Response,
    payload: CambiarPasswordDTO,
    token_payload: dict = Depends(verificar_jwt_token_sin_restriccion),
):
    """Cambia la contraseña y elimina la marca de cambio obligatorio."""
    if token_payload.get("rol") not in {"administrador", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores poseen credenciales para el panel web.",
        )
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
    refresh_nuevo = crear_refresh_token(
        sub=usuario.nombres,
        rol=str(token_payload.get("rol", "administrador")),
        taller_id=str(usuario.taller_id),
        usuario_id=str(usuario.id),
        extra_claims={"requiere_cambio_password": False},
    )
    refresh_anterior = request.cookies.get(settings.refresh_cookie_name)
    if refresh_anterior:
        try:
            await refresh_token_store.revocar(verificar_refresh_token(refresh_anterior))
        except (HTTPException, ValueError):
            pass
    await _registrar_refresh(response, refresh_nuevo)
    return {
        "mensaje": "Contraseña actualizada correctamente.",
        "access_token": token_nuevo,
        "refresh_token": _refresh_compatible(refresh_nuevo),
    }


@router.post("/logout", summary="Cerrar y revocar la sesión actual")
@limiter.limit("30/minute")
async def logout(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenDTO] = None,
):
    refresh_recibido = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_recibido and payload:
        refresh_recibido = payload.refresh_token
    if refresh_recibido:
        try:
            await refresh_token_store.revocar(verificar_refresh_token(refresh_recibido))
        except (HTTPException, ValueError):
            pass
    response.delete_cookie(
        settings.refresh_cookie_name,
        path="/api/v1/auth",
        secure=settings.is_production,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
    )
    return {"mensaje": "Sesión cerrada correctamente."}
