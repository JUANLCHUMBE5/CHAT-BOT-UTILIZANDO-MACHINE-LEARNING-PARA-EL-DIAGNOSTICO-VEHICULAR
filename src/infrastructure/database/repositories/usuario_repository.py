"""Repositorio para la gestión y autenticación de mecánicos y administradores."""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.security import hash_identificador_persistencia
from src.infrastructure.database.models.catalogs import Rol, Usuario


class UsuarioRepository:
    """Acceso a datos asíncrono para usuarios, mecánicos y roles."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def obtener_o_crear_rol(
        self,
        rol_id: int,
        codigo: str,
        nombre: str,
        descripcion: Optional[str] = None,
    ) -> Rol:
        """Obtiene un rol por su código o ID, o lo crea si no existe."""
        stmt = select(Rol).where(or_(Rol.codigo == codigo, Rol.id == rol_id))
        result = await self.session.execute(stmt)
        rol = result.scalars().first()
        if rol is None:
            rol = Rol(id=rol_id, codigo=codigo, nombre=nombre, descripcion=descripcion)
            self.session.add(rol)
            await self.session.flush()
        return rol

    async def asegurar_roles_estandar(self) -> dict[str, Rol]:
        """Asegura que los roles básicos del sistema existan en la base de datos."""
        roles_data = [
            (1, "administrador", "Administrador", "Administra el taller y sus usuarios."),
            (2, "mecanico", "Mecánico", "Registra y confirma diagnósticos."),
            (3, "supervisor", "Supervisor", "Revisa diagnósticos y métricas."),
        ]
        roles = {}
        for r_id, codigo, nombre, desc in roles_data:
            roles[codigo] = await self.obtener_o_crear_rol(r_id, codigo, nombre, desc)
        # Alias de entrada para integraciones anteriores; no crea otro rol.
        roles["admin"] = roles["administrador"]
        return roles

    async def buscar_por_whatsapp_hash(self, whatsapp_hash: str) -> Optional[Usuario]:
        """
        Busca un mecánico o administrador por el hash HMAC-SHA256 de su número de WhatsApp.
        Carga sus relaciones de taller y rol de forma ansiosa (eager loading).
        """
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.taller), selectinload(Usuario.rol))
            .where(Usuario.whatsapp_hash == whatsapp_hash)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def buscar_por_telefono(self, telefono_str: str) -> Optional[Usuario]:
        """Calcula el hash del teléfono y busca al usuario en PostgreSQL."""
        whatsapp_hash = hash_identificador_persistencia(telefono_str, "telefono")
        return await self.buscar_por_whatsapp_hash(whatsapp_hash)

    async def crear_usuario(
        self,
        taller_id: uuid.UUID,
        rol_id: int,
        nombres: str,
        whatsapp_hash: str,
        whatsapp_ultimos4: str,
        apellidos: Optional[str] = None,
        activo: bool = True,
        usuario_id: Optional[uuid.UUID] = None,
    ) -> Usuario:
        """Crea y persiste un nuevo usuario o mecánico en el taller."""
        usuario = Usuario(
            id=usuario_id or uuid.uuid4(),
            taller_id=taller_id,
            rol_id=rol_id,
            nombres=nombres,
            apellidos=apellidos,
            whatsapp_hash=whatsapp_hash,
            whatsapp_ultimos4=whatsapp_ultimos4,
            activo=activo,
        )
        self.session.add(usuario)
        await self.session.flush()
        return usuario

    async def obtener_por_id(self, usuario_id: uuid.UUID) -> Optional[Usuario]:
        """Obtiene un usuario por su UUID."""
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.taller), selectinload(Usuario.rol))
            .where(Usuario.id == usuario_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def listar_por_taller(self, taller_id: uuid.UUID) -> Sequence[Usuario]:
        """Lista todos los usuarios pertenecientes a un taller."""
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.rol))
            .where(Usuario.taller_id == taller_id)
            .order_by(Usuario.nombres.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
