"""Endpoints de administración de clientes y solicitudes de acceso."""

from __future__ import annotations

import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    generar_password_hash,
    verificar_jwt_token,
)
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.solicitud_acceso_repository import SolicitudAccesoRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository

router = APIRouter()


# DTOs
class ClienteResponseDTO(BaseModel):
    id: str
    nombres: str
    telefono: str
    tipo_identificador: str
    activo: bool
    bloqueado: bool
    fecha_registro: str
    ultima_interaccion: str
    tiene_solicitud_pendiente: bool = False
    solicitud_id: Optional[str] = None


class SolicitudAccesoResponseDTO(BaseModel):
    id: str
    usuario_id: str
    usuario_nombre: str
    telefono: str
    rol_solicitado: str
    estado: str
    solicitado_en: str
    revisado_por: Optional[str] = None
    revisado_en: Optional[str] = None
    observaciones: Optional[str] = None


class AprobarSolicitudResponseDTO(BaseModel):
    mensaje: str
    solicitud_id: str
    usuario_id: str
    nuevo_rol: str
    password_temporal: str


class RechazarSolicitudDTO(BaseModel):
    motivo: Optional[str] = None


def exigir_rol_administrativo(payload: dict = Depends(verificar_jwt_token)) -> dict:
    """Asegura que el usuario tenga rol de administrador, jefe_taller o supervisor."""
    rol = payload.get("rol", "")
    if rol not in ("administrador", "jefe_taller", "supervisor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol administrativo.",
        )
    return payload


def _generar_password_temporal() -> str:
    """Genera una contraseña temporal segura y fácil de ingresar."""
    caracteres = string.ascii_letters + string.digits
    clave = "".join(secrets.choice(caracteres) for _ in range(8))
    return f"Mec_{clave}"


# ==========================================
# RUTAS DE CLIENTES
# ==========================================

@router.get("", response_model=List[ClienteResponseDTO], summary="Listar clientes del taller")
async def listar_clientes(
    busqueda: Optional[str] = Query(None, description="Búsqueda por nombre o últimos 4 dígitos"),
    payload: dict = Depends(exigir_rol_administrativo),
):
    """Lista todos los clientes registrados del taller con su última interacción y estado de solicitud."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        solicitud_repo = SolicitudAccesoRepository(session)

        usuarios = await user_repo.listar_clientes_por_taller(taller_uuid, busqueda=busqueda)
        solicitudes_pendientes = await solicitud_repo.listar_por_taller(taller_uuid, estado="pendiente")
        mapa_solicitudes = {s.usuario_id: s for s in solicitudes_pendientes}

        resultado = []
        for u in usuarios:
            tipo_id = "telefono"
            ult_interaccion = "Sin actividad"
            if u.identidades_whatsapp:
                ident = u.identidades_whatsapp[0]
                tipo_id = ident.tipo_identificador
                ult_interaccion = (
                    ident.ultima_interaccion.strftime("%Y-%m-%d %H:%M")
                    if ident.ultima_interaccion
                    else "Reciente"
                )

            sol = mapa_solicitudes.get(u.id)
            resultado.append(
                ClienteResponseDTO(
                    id=str(u.id),
                    nombres=u.nombres,
                    telefono=(
                        f"+51 *** *** {u.whatsapp_ultimos4}"
                        if tipo_id != "user_id"
                        else f"Meta ID (***{u.whatsapp_ultimos4})"
                    ),
                    tipo_identificador=tipo_id,
                    activo=u.activo,
                    bloqueado=getattr(u, "bloqueado", False),
                    fecha_registro=u.creado_en.strftime("%Y-%m-%d") if u.creado_en else "2026-01-01",
                    ultima_interaccion=ult_interaccion,
                    tiene_solicitud_pendiente=sol is not None,
                    solicitud_id=str(sol.id) if sol else None,
                )
            )
        return resultado


@router.patch("/{cliente_id}/bloquear", summary="Bloquear o desbloquear contacto cliente")
async def toggle_bloquear_cliente(
    cliente_id: str,
    payload: dict = Depends(exigir_rol_administrativo),
):
    """Bloquea o desbloquea a un contacto cliente verificando el taller_id."""
    try:
        target_uuid = uuid.UUID(cliente_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de cliente inválido.")

    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        usuario = await user_repo.obtener_por_id(target_uuid)
        if not usuario or usuario.taller_id != taller_uuid:
            raise HTTPException(status_code=404, detail="Cliente no encontrado en este taller.")

        if usuario.rol_id != 4 and getattr(usuario.rol, "codigo", "") != "cliente":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden bloquear o desbloquear usuarios con rol de cliente desde esta sección.",
            )

        usuario_actualizado = await user_repo.toggle_bloqueo(target_uuid)
        await session.commit()
        return {
            "mensaje": (
                f"Cliente {usuario.nombres} {'bloqueado' if usuario_actualizado.bloqueado else 'desbloqueado'} con éxito."
            ),
            "bloqueado": usuario_actualizado.bloqueado,
        }


# ==========================================
# RUTAS DE SOLICITUDES DE ACCESO
# ==========================================

@router.get("/solicitudes/listar", response_model=List[SolicitudAccesoResponseDTO], summary="Listar solicitudes de acceso")
async def listar_solicitudes_acceso(
    estado: Optional[str] = Query(None, description="Filtro por estado: pendiente, aprobada, rechazada"),
    payload: dict = Depends(exigir_rol_administrativo),
):
    """Lista las solicitudes de acceso para el taller autenticado."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        solicitud_repo = SolicitudAccesoRepository(session)
        solicitudes = await solicitud_repo.listar_por_taller(taller_uuid, estado=estado)

        return [
            SolicitudAccesoResponseDTO(
                id=str(s.id),
                usuario_id=str(s.usuario_id),
                usuario_nombre=s.usuario.nombres if s.usuario else "Desconocido",
                telefono=(
                    f"+51 *** *** {s.usuario.whatsapp_ultimos4}"
                    if s.usuario
                    else "0000"
                ),
                rol_solicitado=s.rol_solicitado,
                estado=s.estado,
                solicitado_en=s.solicitado_en.strftime("%Y-%m-%d %H:%M"),
                revisado_por=s.revisado_por.nombres if s.revisado_por else None,
                revisado_en=s.revisado_en.strftime("%Y-%m-%d %H:%M") if s.revisado_en else None,
                observaciones=s.observaciones,
            )
            for s in solicitudes
        ]


@router.post("/solicitudes/{solicitud_id}/aprobar", response_model=AprobarSolicitudResponseDTO, summary="Aprobar solicitud de acceso como mecánico")
async def aprobar_solicitud_acceso(
    solicitud_id: str,
    payload: dict = Depends(exigir_rol_administrativo),
):
    """
    Aprueba la solicitud de acceso:
    1. Promueve al usuario a rol mecánico.
    2. Genera una contraseña temporal segura con debe_cambiar_password = True.
    3. Registra la auditoría del revisor.
    4. Encola la notificación de WhatsApp para el nuevo mecánico con su destinatario real descifrable.
    """
    try:
        sol_uuid = uuid.UUID(solicitud_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de solicitud inválido.")

    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    revisor_id_str = payload.get("usuario_id")
    taller_uuid = uuid.UUID(taller_id_str)
    revisor_uuid = uuid.UUID(revisor_id_str) if revisor_id_str else None

    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        solicitud_repo = SolicitudAccesoRepository(session)
        user_repo = UsuarioRepository(session)
        conv_repo = ConversacionRepository(session)
        msg_repo = MensajeRepository(session)
        operaciones_repo = OperacionesRepository(session)

        solicitud = await solicitud_repo.obtener_por_id(sol_uuid)
        if not solicitud or solicitud.taller_id != taller_uuid:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada en este taller.")

        if solicitud.estado != "pendiente":
            raise HTTPException(status_code=400, detail="Solo se puede aprobar una solicitud pendiente.")

        if not revisor_uuid:
            raise HTTPException(status_code=401, detail="Token administrativo incompleto.")
        revisor = await user_repo.obtener_por_id(revisor_uuid)
        if (
            not revisor
            or revisor.taller_id != taller_uuid
            or not revisor.rol
            or revisor.rol.codigo not in {"administrador", "supervisor", "jefe_taller"}
        ):
            raise HTTPException(status_code=403, detail="Revisor administrativo no válido para este taller.")

        usuario_solicitante = solicitud.usuario
        if not usuario_solicitante.rol or usuario_solicitante.rol.codigo != "cliente":
            raise HTTPException(status_code=409, detail="El solicitante ya no tiene rol de cliente.")

        identidad_envio = next(
            (
                identidad
                for identidad in usuario_solicitante.identidades_whatsapp
                if identidad.destinatario_cifrado
            ),
            None,
        )
        if identidad_envio is None:
            raise HTTPException(
                status_code=409,
                detail="El cliente no posee un destinatario WhatsApp recuperable; debe escribir nuevamente al bot.",
            )

        # 1. Generar contraseña temporal
        password_temporal = _generar_password_temporal()
        p_hash = generar_password_hash(password_temporal)

        # 2. Promover usuario a mecánico
        usuario = await user_repo.promover_a_mecanico(solicitud.usuario_id, password_hash=p_hash)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario asociado no encontrado.")

        # 3. Actualizar estado de solicitud
        await solicitud_repo.responder_solicitud(
            solicitud_id=sol_uuid,
            nuevo_estado="aprobada",
            revisado_por_id=revisor.id,
            observaciones="Aprobado desde panel administrativo",
        )

        # 4. Encolar notificación por WhatsApp
        conversacion = await conv_repo.obtener_o_crear_activa(
            taller_id=taller_uuid,
            usuario_id=usuario.id,
            canal="whatsapp",
            ventana_horas=24,
        )

        mensaje_whatsapp = (
            "✅ *Tu acceso como mecánico ha sido autorizado*\n\n"
            "Ahora puedes enviar síntomas vehiculares o notas de voz para obtener apoyo técnico inteligente.\n\n"
            "⚠️ *Nota técnica:* Los resultados son hipótesis orientativas que deben ser validadas físicamente en el taller.\n\n"
            f"🔑 *Tu contraseña temporal para el panel web es:* `{password_temporal}`\n"
            "_(Deberás cambiarla al ingresar por primera vez al panel)_"
        )

        await msg_repo.crear_mensaje(
            conversacion_id=conversacion.id,
            taller_id=taller_uuid,
            usuario_id=usuario.id,
            meta_message_id=f"out_aprob_{uuid.uuid4().hex}",
            direccion="salida",
            tipo="texto",
            texto=mensaje_whatsapp,
            categoria_cobro="servicio",
            estado_entrega="pendiente",
            costo_estimado=0,
            moneda="USD",
            proveedor=identidad_envio.proveedor,
            destinatario_cifrado=identidad_envio.destinatario_cifrado,
            disponible_entrega_en=datetime.now(timezone.utc),
        )

        await operaciones_repo.registrar_auditoria(
            accion="aprobacion_solicitud_mecanico",
            entidad="solicitud_acceso",
            entidad_id=sol_uuid,
            taller_id=taller_uuid,
            usuario_id=revisor.id,
            detalles={"usuario_promovido_id": str(usuario.id), "rol_nuevo": "mecanico"},
        )

        await session.commit()

        return AprobarSolicitudResponseDTO(
            mensaje=f"Usuario {usuario.nombres} promovido a mecánico exitosamente.",
            solicitud_id=str(solicitud.id),
            usuario_id=str(usuario.id),
            nuevo_rol="mecanico",
            password_temporal=password_temporal,
        )


@router.post("/solicitudes/{solicitud_id}/rechazar", summary="Rechazar solicitud de acceso")
async def rechazar_solicitud_acceso(
    solicitud_id: str,
    dto: Optional[RechazarSolicitudDTO] = None,
    payload: dict = Depends(exigir_rol_administrativo),
):
    """Rechaza una solicitud de acceso pendiente."""
    try:
        sol_uuid = uuid.UUID(solicitud_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de solicitud inválido.")

    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    revisor_id_str = payload.get("usuario_id")
    taller_uuid = uuid.UUID(taller_id_str)
    revisor_uuid = uuid.UUID(revisor_id_str) if revisor_id_str else None

    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        solicitud_repo = SolicitudAccesoRepository(session)
        user_repo = UsuarioRepository(session)
        operaciones_repo = OperacionesRepository(session)

        solicitud = await solicitud_repo.obtener_por_id(sol_uuid)
        if not solicitud or solicitud.taller_id != taller_uuid:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada en este taller.")
        if solicitud.estado != "pendiente":
            raise HTTPException(status_code=400, detail="Solo se puede rechazar una solicitud pendiente.")
        if not revisor_uuid:
            raise HTTPException(status_code=401, detail="Token administrativo incompleto.")
        revisor = await user_repo.obtener_por_id(revisor_uuid)
        if (
            not revisor
            or revisor.taller_id != taller_uuid
            or not revisor.rol
            or revisor.rol.codigo not in {"administrador", "supervisor", "jefe_taller"}
        ):
            raise HTTPException(status_code=403, detail="Revisor administrativo no válido para este taller.")

        await solicitud_repo.responder_solicitud(
            solicitud_id=sol_uuid,
            nuevo_estado="rechazada",
            revisado_por_id=revisor.id,
            observaciones=dto.motivo if dto else "Rechazado por el administrador",
        )
        await operaciones_repo.registrar_auditoria(
            accion="rechazo_solicitud_mecanico",
            entidad="solicitud_acceso",
            entidad_id=sol_uuid,
            taller_id=taller_uuid,
            usuario_id=revisor.id,
            detalles={"usuario_id": str(solicitud.usuario_id)},
        )
        await session.commit()
        return {"mensaje": "Solicitud rechazada con éxito.", "solicitud_id": str(solicitud.id)}
