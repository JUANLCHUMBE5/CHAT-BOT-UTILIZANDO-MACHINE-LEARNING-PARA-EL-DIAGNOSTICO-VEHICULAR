"""Endpoints de administración de mecánicos para el taller en PostgreSQL."""

from __future__ import annotations

import re
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    cifrar_texto_reversible,
    generar_password_hash,
    hash_identificador_persistencia,
    verificar_jwt_token,
)
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.identidad_whatsapp_repository import IdentidadWhatsAppRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.solicitud_acceso_repository import SolicitudAccesoRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository

router = APIRouter()


class MecanicoCreateDTO(BaseModel):
    nombres: str
    username: Optional[str] = None
    telefono_whatsapp: str
    password: Optional[str] = None
    rol: Literal["mecanico", "jefe_taller", "administrador"] = "mecanico"


class MecanicoUpdateDTO(BaseModel):
    nombres: Optional[str] = None
    username: Optional[str] = None
    telefono_whatsapp: Optional[str] = None
    password: Optional[str] = None



class CambiarRolDTO(BaseModel):
    nuevo_rol: Literal["mecanico", "jefe_taller", "administrador"]
    password: Optional[str] = None


class MecanicoResponseDTO(BaseModel):
    id: str
    nombres: str
    username: Optional[str] = None
    telefono: str
    rol: str
    activo: bool
    bloqueado: bool
    fecha_registro: str
    total_diagnosticos: int
    ultimo_acceso: str


def exigir_rol_administrativo(payload: dict = Depends(verificar_jwt_token)) -> dict:
    """Asegura que solo un administrador pueda operar el panel."""
    rol = payload.get("rol", "")
    if rol not in ("administrador", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol administrativo.",
        )
    return payload


@router.get("", response_model=List[MecanicoResponseDTO], summary="Listar mecánicos del taller")
async def listar_mecanicos(payload: dict = Depends(exigir_rol_administrativo)):
    """Retorna la lista de mecánicos pertenecientes al taller autenticado desde PostgreSQL."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            usuarios = await user_repo.listar_por_taller(taller_uuid, solo_mecanicos=True)
            return [
                MecanicoResponseDTO(
                    id=str(u.id),
                    nombres=u.nombres,
                    username=u.username,
                    telefono=f"+51 *** *** {u.whatsapp_ultimos4}",
                    rol=u.rol.codigo if u.rol else "mecanico",
                    activo=u.activo,
                    bloqueado=getattr(u, "bloqueado", False),
                    fecha_registro=u.creado_en.strftime("%Y-%m-%d") if u.creado_en else "2026-01-01",
                    total_diagnosticos=len(u.diagnosticos) if u.diagnosticos else 0,
                    ultimo_acceso=u.actualizado_en.strftime("%Y-%m-%d %H:%M") if u.actualizado_en else "Reciente",
                )
                for u in usuarios
            ]

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.post("", response_model=MecanicoResponseDTO, summary="Registrar nuevo mecánico")
async def registrar_mecanico(
    dto: MecanicoCreateDTO, payload: dict = Depends(exigir_rol_administrativo)
):
    """Registra personal; solo las cuentas administrativas reciben contraseña web."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)
    creador_rol = payload.get("rol", "")
    if dto.rol in ("administrador", "admin") and creador_rol not in ("administrador", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede registrar nuevos usuarios con rol de administrador.",
        )
    es_nuevo_admin = dto.rol in ("administrador", "admin")
    raw_password = dto.password.strip() if dto.password else ""
    if es_nuevo_admin and (
        len(raw_password) < 12
        or not any(c.islower() for c in raw_password)
        or not any(c.isupper() for c in raw_password)
        or not any(c.isdigit() for c in raw_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las cuentas administrativas requieren una contraseña de al menos 12 caracteres, con mayúsculas, minúsculas y números.",
        )
    digits = re.sub(r"\D", "", dto.telefono_whatsapp)
    if len(digits) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de teléfono WhatsApp debe contener al menos 6 dígitos válidos.",
        )
    ultimos4 = digits[-4:] if len(digits) >= 4 else digits.zfill(4)
    w_hash = hash_identificador_persistencia(dto.telefono_whatsapp, "telefono")

    username_limpio = None
    if dto.username:
        username_limpio = dto.username.strip().lower()
        if len(username_limpio) < 3 or not re.match(r"^[a-zA-Z0-9_.-]+$", username_limpio):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario debe tener al menos 3 caracteres y solo contener letras, números, guiones o puntos.",
            )

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            identidad_repo = IdentidadWhatsAppRepository(session)
            solicitud_repo = SolicitudAccesoRepository(session)
            operaciones_repo = OperacionesRepository(session)
            roles = await user_repo.asegurar_roles_estandar()
            rol_obj = roles.get(dto.rol, roles["mecanico"])

            if username_limpio:
                existente_user = await user_repo.buscar_por_username(username_limpio)
                if existente_user:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="El nombre de usuario ya está registrado por otro miembro.",
                    )

            existente = await user_repo.buscar_por_whatsapp_hash(w_hash)
            if existente:
                if existente.taller_id != taller_uuid:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="El número ya está asociado a otro taller.",
                    )
                if not existente.rol or existente.rol.codigo != "cliente":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="El número ya tiene acceso interno en este taller.",
                    )

                existente.nombres = dto.nombres.strip()
                if username_limpio:
                    existente.username = username_limpio
                existente.rol_id = rol_obj.id
                existente.password_hash = generar_password_hash(raw_password) if es_nuevo_admin else None
                existente.debe_cambiar_password = es_nuevo_admin
                existente.activo = True
                existente.bloqueado = False

                if existente.identidades_whatsapp:
                    await identidad_repo.actualizar_destinatario(
                        existente.identidades_whatsapp[0].id,
                        cifrar_texto_reversible(dto.telefono_whatsapp),
                        "meta",
                    )
                else:
                    await identidad_repo.registrar_identidad(
                        usuario_id=existente.id,
                        identificador_hash=w_hash,
                        tipo_identificador="telefono",
                        ultimos4=ultimos4,
                        proveedor="meta",
                        destinatario_cifrado=cifrar_texto_reversible(dto.telefono_whatsapp),
                    )

                revisor_id_str = payload.get("usuario_id")
                if not revisor_id_str:
                    raise HTTPException(status_code=401, detail="Token administrativo incompleto.")
                revisor_id = uuid.UUID(str(revisor_id_str))
                pendiente = await solicitud_repo.obtener_pendiente_por_usuario(
                    existente.id, taller_uuid
                )
                if pendiente:
                    await solicitud_repo.responder_solicitud(
                        pendiente.id,
                        "aprobada",
                        revisor_id,
                        "Autorizado directamente desde Gestión de Mecánicos",
                    )
                await operaciones_repo.registrar_auditoria(
                    accion="promocion_cliente_mecanico",
                    entidad="usuario",
                    entidad_id=existente.id,
                    taller_id=taller_uuid,
                    usuario_id=revisor_id,
                    detalles={"rol_nuevo": rol_obj.codigo, "origen": "panel_web"},
                )
                await session.commit()
                return MecanicoResponseDTO(
                    id=str(existente.id),
                    nombres=existente.nombres,
                    username=existente.username,
                    telefono=f"+51 *** *** {ultimos4}",
                    rol=rol_obj.codigo,
                    activo=True,
                    bloqueado=False,
                    fecha_registro=existente.creado_en.strftime("%Y-%m-%d"),
                    total_diagnosticos=0,
                    ultimo_acceso="Autorizado",
                )

            try:
                usuario = await user_repo.crear_usuario(
                    taller_id=taller_uuid,
                    rol_id=rol_obj.id,
                    nombres=dto.nombres.strip(),
                    username=username_limpio,
                    whatsapp_hash=w_hash,
                    whatsapp_ultimos4=ultimos4,
                    password_hash=generar_password_hash(raw_password) if es_nuevo_admin else None,
                    debe_cambiar_password=es_nuevo_admin,
                    activo=True,
                )
                await identidad_repo.registrar_identidad(
                    usuario_id=usuario.id,
                    identificador_hash=w_hash,
                    tipo_identificador="telefono",
                    ultimos4=ultimos4,
                    proveedor="meta",
                    destinatario_cifrado=cifrar_texto_reversible(dto.telefono_whatsapp),
                )
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                if "whatsapp_hash" in str(exc.orig).lower():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Ya existe un mecánico registrado con este número de teléfono WhatsApp.",
                    ) from exc
                raise

            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
                username=usuario.username,
                telefono=f"+51 *** *** {ultimos4}",
                rol=rol_obj.codigo,
                activo=True,
                bloqueado=False,
                fecha_registro=usuario.creado_en.strftime("%Y-%m-%d"),
                total_diagnosticos=0,
                ultimo_acceso="Nuevo",
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.patch("/{mecanico_id}/activar", response_model=MecanicoResponseDTO, summary="Alternar activación de mecánico")
async def toggle_activar_mecanico(
    mecanico_id: str, payload: dict = Depends(exigir_rol_administrativo)
):
    """Activa o desactiva la cuenta de un mecánico verificando taller_id."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)
    revisor_id_str = str(payload.get("usuario_id") or payload.get("sub") or "")

    if database_configurada():
        try:
            target_uuid = uuid.UUID(mecanico_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de mecánico en formato UUID inválido.",
            )

        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            usuario = await user_repo.obtener_por_id(target_uuid)
            if not usuario or usuario.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Mecánico no encontrado en este taller.")

            esta_desactivando = usuario.activo
            if esta_desactivando:
                if revisor_id_str and revisor_id_str == str(target_uuid):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No puedes desactivar tu propia cuenta de usuario.",
                    )
                es_admin = usuario.rol and usuario.rol.codigo in {"administrador", "admin"}
                if es_admin:
                    admins_activos = await user_repo.contar_administradores_activos(taller_uuid)
                    if admins_activos <= 1:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No se puede desactivar al único administrador activo del taller.",
                        )

            usuario.activo = not usuario.activo
            await session.commit()
            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
                username=usuario.username,
                telefono=f"+51 *** *** {usuario.whatsapp_ultimos4}",
                rol=usuario.rol.codigo if usuario.rol else "mecanico",
                activo=usuario.activo,
                bloqueado=getattr(usuario, "bloqueado", False),
                fecha_registro=usuario.creado_en.strftime("%Y-%m-%d"),
                total_diagnosticos=len(usuario.diagnosticos) if usuario.diagnosticos else 0,
                ultimo_acceso="Reciente",
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.patch("/{mecanico_id}/bloquear", response_model=MecanicoResponseDTO, summary="Alternar bloqueo de mecánico")
async def toggle_bloquear_mecanico(
    mecanico_id: str, payload: dict = Depends(exigir_rol_administrativo)
):
    """Bloquea o desbloquea el acceso de un mecánico verificando taller_id."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)
    revisor_id_str = str(payload.get("usuario_id") or payload.get("sub") or "")

    if database_configurada():
        try:
            target_uuid = uuid.UUID(mecanico_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de mecánico en formato UUID inválido.",
            )

        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            usuario = await user_repo.obtener_por_id(target_uuid)
            if not usuario or usuario.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Mecánico no encontrado en este taller.")

            esta_bloqueando = not getattr(usuario, "bloqueado", False)
            if esta_bloqueando:
                if revisor_id_str and revisor_id_str == str(target_uuid):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No puedes bloquear tu propia cuenta de usuario.",
                    )
                es_admin = usuario.rol and usuario.rol.codigo in {"administrador", "admin"}
                if es_admin:
                    admins_activos = await user_repo.contar_administradores_activos(taller_uuid)
                    if admins_activos <= 1:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No se puede bloquear al único administrador activo del taller.",
                        )

            usuario.bloqueado = esta_bloqueando
            if usuario.bloqueado:
                usuario.activo = False

            await session.commit()
            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
                username=usuario.username,
                telefono=f"+51 *** *** {usuario.whatsapp_ultimos4}",
                rol=usuario.rol.codigo if usuario.rol else "mecanico",
                activo=usuario.activo,
                bloqueado=usuario.bloqueado,
                fecha_registro=usuario.creado_en.strftime("%Y-%m-%d"),
                total_diagnosticos=len(usuario.diagnosticos) if usuario.diagnosticos else 0,
                ultimo_acceso="Reciente",
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.patch("/{mecanico_id}/rol", response_model=MecanicoResponseDTO, summary="Cambiar el rol de un mecánico")
async def cambiar_rol_mecanico(
    mecanico_id: str, dto: CambiarRolDTO, payload: dict = Depends(exigir_rol_administrativo)
):
    """Cambia el rol de un usuario o mecánico en PostgreSQL."""
    taller_uuid = uuid.UUID(str(payload.get("taller_id")))
    revisor_id_str = str(payload.get("usuario_id") or payload.get("sub") or "")
    editor_rol = payload.get("rol", "")
    if dto.nuevo_rol in ("administrador", "admin") and editor_rol not in ("administrador", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede promover usuarios al rol de administrador.",
        )

    password_admin = dto.password.strip() if dto.password else ""
    if dto.nuevo_rol == "administrador" and (
        len(password_admin) < 12
        or not any(c.islower() for c in password_admin)
        or not any(c.isupper() for c in password_admin)
        or not any(c.isdigit() for c in password_admin)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para promover a administrador debe asignar una contraseña de al menos 12 caracteres, con mayúsculas, minúsculas y números.",
        )

    try:
        target_uuid = uuid.UUID(mecanico_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de mecánico en formato UUID inválido.",
        )

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            usuario = await user_repo.obtener_por_id(target_uuid)
            if not usuario or usuario.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Mecánico no encontrado.")

            es_admin_actual = usuario.rol and usuario.rol.codigo in {"administrador", "admin"}
            es_democion = es_admin_actual and dto.nuevo_rol not in {"administrador", "admin"}

            if es_democion:
                if revisor_id_str and revisor_id_str == str(target_uuid):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No puedes reducir tu propio rol de administrador.",
                    )
                admins_activos = await user_repo.contar_administradores_activos(taller_uuid)
                if admins_activos <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No se puede cambiar el rol del único administrador activo del taller.",
                    )

            roles = await user_repo.asegurar_roles_estandar()
            rol_obj = roles.get(dto.nuevo_rol, roles["mecanico"])
            usuario.rol_id = rol_obj.id
            if dto.nuevo_rol == "administrador":
                usuario.password_hash = generar_password_hash(password_admin)
                usuario.debe_cambiar_password = True
            else:
                usuario.password_hash = None
                usuario.debe_cambiar_password = False

            await session.commit()
            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
                username=usuario.username,
                telefono=f"+51 *** *** {usuario.whatsapp_ultimos4}",
                rol=rol_obj.codigo,
                activo=usuario.activo,
                bloqueado=getattr(usuario, "bloqueado", False),
                fecha_registro=usuario.creado_en.strftime("%Y-%m-%d"),
                total_diagnosticos=len(usuario.diagnosticos) if usuario.diagnosticos else 0,
                ultimo_acceso="Reciente",
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.patch("/{mecanico_id}/revocar-acceso", summary="Revocar acceso técnico y regresar a cliente")
@router.delete("/{mecanico_id}", summary="Compatibilidad: revocar acceso técnico", deprecated=True)
async def revocar_acceso_mecanico(
    mecanico_id: str, payload: dict = Depends(exigir_rol_administrativo)
):
    """Retira permisos internos sin borrar identidad, conversaciones ni diagnósticos."""
    try:
        target_uuid = uuid.UUID(mecanico_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de mecánico en formato UUID inválido.",
        )

    revisor_id_str = str(payload.get("usuario_id") or payload.get("sub") or "")
    if revisor_id_str and revisor_id_str == str(target_uuid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes revocar tu propio acceso técnico.",
        )

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            usuario_obj = await user_repo.obtener_por_id(target_uuid)
            taller_id_str = payload.get("taller_id")
            if not usuario_obj or str(usuario_obj.taller_id) != taller_id_str:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="El mecánico no existe en este taller.",
                )

            if usuario_obj.rol and usuario_obj.rol.codigo in {"administrador", "admin"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede revocar el acceso a un administrador. Asigne otro rol previamente.",
                )

            usuario = await user_repo.revocar_acceso_tecnico(target_uuid)
            operaciones_repo = OperacionesRepository(session)
            revisor_id_str = payload.get("usuario_id")
            revisor_id = None
            if revisor_id_str:
                try:
                    revisor_id = uuid.UUID(str(revisor_id_str))
                except ValueError:
                    revisor_id = None

            await operaciones_repo.registrar_auditoria(
                accion="revocacion_acceso_tecnico",
                entidad="usuario",
                entidad_id=target_uuid,
                taller_id=usuario_obj.taller_id,
                usuario_id=revisor_id,
                detalles={"rol_nuevo": "cliente", "historial_conservado": True},
            )
            await session.commit()
            return {
                "mensaje": f"Acceso técnico de {usuario.nombres} revocado; ahora vuelve a ser cliente.",
                "usuario_id": str(usuario.id),
                "nuevo_rol": "cliente",
            }

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.put("/{mecanico_id}", response_model=MecanicoResponseDTO, summary="Actualizar información de un mecánico")
async def actualizar_mecanico(
    mecanico_id: str,
    dto: MecanicoUpdateDTO,
    payload: dict = Depends(exigir_rol_administrativo),
):
    """Actualiza los datos personales de un mecánico (nombres, teléfono WhatsApp, contraseña)."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)
    revisor_id_str = str(payload.get("usuario_id") or payload.get("sub") or "")
    try:
        revisor_uuid = uuid.UUID(revisor_id_str)
    except (ValueError, TypeError):
        revisor_uuid = None
    revisor_rol = payload.get("rol", "")

    try:
        target_uuid = uuid.UUID(mecanico_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de mecánico en formato UUID inválido.",
        )

    if dto.nombres is not None:
        nombres_limpio = dto.nombres.strip()
        if not nombres_limpio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre completo no puede estar vacío.",
            )

    if dto.telefono_whatsapp is not None:
        telefono_raw = dto.telefono_whatsapp.strip()
        digits = re.sub(r"\D", "", telefono_raw)
        if len(digits) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de teléfono WhatsApp debe contener al menos 6 dígitos válidos.",
            )

    if dto.password:
        raw_pass = dto.password.strip()
        if (
            len(raw_pass) < 12
            or not any(c.islower() for c in raw_pass)
            or not any(c.isupper() for c in raw_pass)
            or not any(c.isdigit() for c in raw_pass)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 12 caracteres, incluir mayúsculas, minúsculas y números.",
            )

    if dto.username is not None:
        username_candidate = dto.username.strip().lower()
        if username_candidate and (len(username_candidate) < 3 or not re.match(r"^[a-zA-Z0-9_.-]+$", username_candidate)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario debe tener al menos 3 caracteres y solo contener letras, números, guiones o puntos.",
            )

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            identidad_repo = IdentidadWhatsAppRepository(session)
            operaciones_repo = OperacionesRepository(session)

            usuario = await user_repo.obtener_por_id(target_uuid)
            if not usuario or usuario.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Mecánico no encontrado en este taller.")

            target_es_admin = usuario.rol and usuario.rol.codigo in {"administrador", "admin"}
            revisor_es_admin = revisor_rol in {"administrador", "admin"}

            if target_es_admin and not revisor_es_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para editar a un administrador",
                )
            if dto.password and not target_es_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Los mecánicos no poseen contraseña ni acceso al panel web.",
                )

            detalles_dict = {
                "nombres_modificados": dto.nombres is not None,
                "username_modificado": dto.username is not None,
                "telefono_modificado": dto.telefono_whatsapp is not None,
                "password_modificado": bool(dto.password),
            }

            if dto.nombres is not None:
                usuario.nombres = dto.nombres.strip()

            if dto.username is not None:
                new_username = dto.username.strip().lower()
                if new_username:
                    existente_u = await user_repo.buscar_por_username(new_username)
                    if existente_u and existente_u.id != usuario.id:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="El nombre de usuario ya está en uso por otro miembro.",
                        )
                    usuario.username = new_username
                else:
                    usuario.username = None

            if dto.telefono_whatsapp is not None:
                telefono_raw = dto.telefono_whatsapp.strip()
                digits = re.sub(r"\D", "", telefono_raw)
                ultimos4 = digits[-4:] if len(digits) >= 4 else digits.zfill(4)
                w_hash = hash_identificador_persistencia(telefono_raw, "telefono")

                if w_hash != usuario.whatsapp_hash:
                    existente = await user_repo.buscar_por_whatsapp_hash(w_hash)
                    if existente and existente.id != usuario.id:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="El número de teléfono WhatsApp ya está registrado por otro usuario.",
                        )

                    usuario.whatsapp_hash = w_hash
                    usuario.whatsapp_ultimos4 = ultimos4

                    dest_cifrado = cifrar_texto_reversible(telefono_raw)
                    if usuario.identidades_whatsapp:
                        for ident in usuario.identidades_whatsapp:
                            ident.identificador_hash = w_hash
                            ident.ultimos4 = ultimos4
                            ident.destinatario_cifrado = dest_cifrado
                            ident.proveedor = "meta"
                    else:
                        await identidad_repo.registrar_identidad(
                            usuario_id=usuario.id,
                            identificador_hash=w_hash,
                            tipo_identificador="telefono",
                            ultimos4=ultimos4,
                            proveedor="meta",
                            destinatario_cifrado=dest_cifrado,
                        )

            if dto.password:
                raw_pass = dto.password.strip()
                usuario.password_hash = generar_password_hash(raw_pass)
                usuario.debe_cambiar_password = False

            await operaciones_repo.registrar_auditoria(
                accion="USUARIO_EDITADO",
                entidad="usuario",
                entidad_id=usuario.id,
                taller_id=usuario.taller_id,
                usuario_id=revisor_uuid,
                detalles=detalles_dict,
            )

            await session.commit()
            await session.refresh(usuario)

            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
                username=usuario.username,
                telefono=f"+51 *** *** {usuario.whatsapp_ultimos4}",
                rol=usuario.rol.codigo if usuario.rol else "mecanico",
                activo=usuario.activo,
                bloqueado=getattr(usuario, "bloqueado", False),
                fecha_registro=usuario.creado_en.strftime("%Y-%m-%d") if usuario.creado_en else "2026-01-01",
                total_diagnosticos=len(usuario.diagnosticos) if usuario.diagnosticos else 0,
                ultimo_acceso=usuario.actualizado_en.strftime("%Y-%m-%d %H:%M") if usuario.actualizado_en else "Reciente",
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
