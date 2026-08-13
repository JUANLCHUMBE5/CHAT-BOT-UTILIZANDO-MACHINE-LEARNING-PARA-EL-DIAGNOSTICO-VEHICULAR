"""Endpoints de administración de mecánicos para el taller en PostgreSQL."""

from __future__ import annotations

import re
import uuid
from typing import List, Literal

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
    telefono_whatsapp: str
    password: str
    rol: Literal["mecanico", "jefe_taller", "administrador"] = "mecanico"


class CambiarRolDTO(BaseModel):
    nuevo_rol: Literal["mecanico", "jefe_taller", "administrador"]


class MecanicoResponseDTO(BaseModel):
    id: str
    nombres: str
    telefono: str
    rol: str
    activo: bool
    bloqueado: bool
    fecha_registro: str
    total_diagnosticos: int
    ultimo_acceso: str


def exigir_rol_administrativo(payload: dict = Depends(verificar_jwt_token)) -> dict:
    """Asegura que el usuario tenga rol de administrador, jefe_taller o supervisor."""
    rol = payload.get("rol", "")
    if rol not in ("administrador", "jefe_taller", "supervisor", "admin"):
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
    """Registra y autoriza a un nuevo mecánico en el taller en PostgreSQL con contraseña obligatoria."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)
    if not dto.password or len(dto.password.strip()) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña es obligatoria y debe contener al menos 6 caracteres.",
        )
    raw_password = dto.password.strip()
    digits = re.sub(r"\D", "", dto.telefono_whatsapp)
    if len(digits) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de teléfono WhatsApp debe contener al menos 6 dígitos válidos.",
        )
    ultimos4 = digits[-4:] if len(digits) >= 4 else digits.zfill(4)
    w_hash = hash_identificador_persistencia(dto.telefono_whatsapp, "telefono")

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            identidad_repo = IdentidadWhatsAppRepository(session)
            solicitud_repo = SolicitudAccesoRepository(session)
            operaciones_repo = OperacionesRepository(session)
            roles = await user_repo.asegurar_roles_estandar()
            rol_obj = roles.get(dto.rol, roles["mecanico"])

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
                existente.rol_id = rol_obj.id
                existente.password_hash = generar_password_hash(raw_password)
                existente.debe_cambiar_password = True
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
                    whatsapp_hash=w_hash,
                    whatsapp_ultimos4=ultimos4,
                    activo=True,
                )
                usuario.password_hash = generar_password_hash(raw_password)
                usuario.debe_cambiar_password = True
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

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            usuario = await user_repo.obtener_por_id(uuid.UUID(mecanico_id))
            if not usuario or usuario.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Mecánico no encontrado en este taller.")

            usuario.activo = not usuario.activo
            await session.commit()
            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
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

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user_repo = UsuarioRepository(session)
            usuario = await user_repo.obtener_por_id(uuid.UUID(mecanico_id))
            if not usuario or usuario.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Mecánico no encontrado en este taller.")

            usuario.bloqueado = not getattr(usuario, "bloqueado", False)
            if usuario.bloqueado:
                usuario.activo = False

            await session.commit()
            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
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

            roles = await user_repo.asegurar_roles_estandar()
            rol_obj = roles.get(dto.nuevo_rol, roles["mecanico"])
            usuario.rol_id = rol_obj.id

            await session.commit()
            return MecanicoResponseDTO(
                id=str(usuario.id),
                nombres=usuario.nombres,
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
                    detail="No se puede revocar un administrador desde Gestión de Mecánicos.",
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
