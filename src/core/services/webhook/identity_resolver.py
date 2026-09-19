"""Módulo de resolución de identidad y auto-registro para el Webhook de WhatsApp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.core.security import (
    anonimizar_identificador,
    cifrar_texto_reversible,
    hash_identificador_persistencia,
)
from src.infrastructure.database.repositories.identidad_whatsapp_repository import (
    IdentidadWhatsAppRepository,
)
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@dataclass
class ResultadoIdentidad:
    """Resultado de la resolución del remitente."""
    usuario: Any = None
    identidad: Any = None
    status: str = "ok"
    mensaje_error: Optional[str] = None


class IdentityResolver:
    """Resuelve o autoregistra contactos en el sistema de mensajería multi-rol."""

    @staticmethod
    async def resolver_o_registrar(
        session: AsyncSession,
        remitente: str,
        proveedor: str,
        tipo_identificador: str = "telefono",
        telefono_id_meta: Optional[str] = None,
        nombre_contacto: Optional[str] = None,
    ) -> ResultadoIdentidad:
        rem_anon = anonimizar_identificador(remitente)
        usuario_repo = UsuarioRepository(session)
        identidad_repo = IdentidadWhatsAppRepository(session)
        taller_repo = TallerRepository(session)

        # Normalizar tipo de identificador
        tipo_id_norm = (
            tipo_identificador
            if tipo_identificador in ("telefono", "wa_id", "user_id")
            else "telefono"
        )
        id_hash = hash_identificador_persistencia(remitente, tipo_id_norm)

        # Extraer últimos 4 dígitos
        digits = "".join(c for c in remitente if c.isdigit())
        ultimos4 = digits[-4:] if len(digits) >= 4 else (digits.zfill(4) if digits else "0000")
        dest_cifrado = cifrar_texto_reversible(remitente)

        # 1. Buscar en identidades_whatsapp
        identidad = await identidad_repo.buscar_por_hash(id_hash)
        usuario = identidad.usuario if identidad else None

        # 2. Fallback a búsqueda directa en usuarios
        if usuario is None:
            usuario = await usuario_repo.buscar_por_whatsapp_hash(id_hash)
            if usuario and not identidad:
                identidad = await identidad_repo.registrar_identidad(
                    usuario_id=usuario.id,
                    identificador_hash=id_hash,
                    tipo_identificador=tipo_id_norm,
                    ultimos4=ultimos4,
                    proveedor=proveedor,
                    destinatario_cifrado=dest_cifrado,
                )

        # 3. Si no existe usuario -> Auto-registro como Cliente
        if usuario is None:
            taller_asociado = await taller_repo.obtener_taller_para_webhook(telefono_id_meta)
            if taller_asociado is None:
                logger.error(
                    f"[Webhook Error] No se encontró taller activo para telefono_id_meta='{telefono_id_meta}'. "
                    "Se rechaza auto-registro para evitar cruce de datos."
                )
                return ResultadoIdentidad(status="taller_no_encontrado")

            nombre_nuevo = (
                nombre_contacto.strip()
                if nombre_contacto and nombre_contacto.strip()
                else f"Cliente {ultimos4}"
            )
            usuario = await usuario_repo.crear_cliente_automatico(
                taller_id=taller_asociado.id,
                nombres=nombre_nuevo,
                whatsapp_hash=id_hash,
                whatsapp_ultimos4=ultimos4,
            )
            identidad = await identidad_repo.registrar_identidad(
                usuario_id=usuario.id,
                identificador_hash=id_hash,
                tipo_identificador=tipo_id_norm,
                ultimos4=ultimos4,
                proveedor=proveedor,
                destinatario_cifrado=dest_cifrado,
            )
            logger.info(
                f"[Webhook Auto-Registro] Contacto {rem_anon} registrado como cliente en taller {taller_asociado.nombre}."
            )
        else:
            if identidad:
                await identidad_repo.actualizar_destinatario(
                    identidad.id,
                    destinatario_cifrado=dest_cifrado,
                    proveedor=proveedor,
                )

        # 4. Verificación de bloqueo y estado activo
        if getattr(usuario, "bloqueado", False) or not getattr(usuario, "activo", True):
            logger.warning(
                f"[Webhook Acceso Denegado] Contacto {rem_anon} bloqueado={getattr(usuario, 'bloqueado', False)} o activo={getattr(usuario, 'activo', True)}."
            )
            mensaje_bloqueo = (
                "🚫 *Acceso Restringido*\n\n"
                "Tu número o usuario se encuentra temporalmente inactivo o bloqueado para interactuar con este servicio."
            )
            return ResultadoIdentidad(
                usuario=usuario,
                identidad=identidad,
                status="bloqueado",
                mensaje_error=mensaje_bloqueo,
            )

        # 5. Verificación de taller activo
        if not usuario.taller or not usuario.taller.activo:
            logger.warning(f"[Webhook Taller Inactivo] Taller inactivo para usuario {rem_anon}.")
            mensaje_inactivo = (
                "🔒 *Taller Temporalmente Fuera de Servicio*\n\n"
                "El taller asociado a tu cuenta se encuentra en mantenimiento o inactivo."
            )
            return ResultadoIdentidad(
                usuario=usuario,
                identidad=identidad,
                status="taller_inactivo",
                mensaje_error=mensaje_inactivo,
            )

        return ResultadoIdentidad(usuario=usuario, identidad=identidad, status="ok")
