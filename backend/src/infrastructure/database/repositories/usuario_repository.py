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
            (4, "cliente", "Cliente", "Cliente del taller. Consultas generales, citas y solicitud de acceso."),
        ]
        roles = {}
        for r_id, codigo, nombre, desc in roles_data:
            roles[codigo] = await self.obtener_o_crear_rol(r_id, codigo, nombre, desc)
        # Alias de compatibilidad
        roles["admin"] = roles["administrador"]
        roles["jefe_taller"] = roles["supervisor"]
        return roles

    async def buscar_por_whatsapp_hash(self, whatsapp_hash: str) -> Optional[Usuario]:
        """
        Busca un usuario (cliente o mecánico) por el hash HMAC-SHA256 de su identificador.
        Carga sus relaciones de taller, rol e identidades_whatsapp de forma ansiosa.
        """
        stmt = (
            select(Usuario)
            .options(
                selectinload(Usuario.taller),
                selectinload(Usuario.rol),
                selectinload(Usuario.identidades_whatsapp),
            )
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
        whatsapp_ultimos4: str = "0000",
        apellidos: Optional[str] = None,
        activo: bool = True,
        bloqueado: bool = False,
        debe_cambiar_password: bool = True,
        password_hash: Optional[str] = None,
        usuario_id: Optional[uuid.UUID] = None,
    ) -> Usuario:
        """Crea y persiste un nuevo usuario en el taller."""
        usuario = Usuario(
            id=usuario_id or uuid.uuid4(),
            taller_id=taller_id,
            rol_id=rol_id,
            nombres=nombres,
            apellidos=apellidos,
            whatsapp_hash=whatsapp_hash,
            whatsapp_ultimos4=whatsapp_ultimos4,
            password_hash=password_hash,
            debe_cambiar_password=debe_cambiar_password,
            activo=activo,
            bloqueado=bloqueado,
        )
        self.session.add(usuario)
        await self.session.flush()
        return await self.obtener_por_id(usuario.id)

    async def crear_cliente_automatico(
        self,
        taller_id: uuid.UUID,
        nombres: str,
        whatsapp_hash: str,
        whatsapp_ultimos4: str = "0000",
    ) -> Usuario:
        """Auto-registra a un contacto nuevo con rol cliente sin exigir contraseña."""
        roles = await self.asegurar_roles_estandar()
        rol_cliente = roles["cliente"]
        return await self.crear_usuario(
            taller_id=taller_id,
            rol_id=rol_cliente.id,
            nombres=nombres,
            whatsapp_hash=whatsapp_hash,
            whatsapp_ultimos4=whatsapp_ultimos4,
            password_hash=None,
            debe_cambiar_password=False,
            activo=True,
            bloqueado=False,
        )

    async def obtener_por_id(self, usuario_id: uuid.UUID) -> Optional[Usuario]:
        """Obtiene un usuario por su UUID con rol, taller e identidades cargadas."""
        stmt = (
            select(Usuario)
            .options(
                selectinload(Usuario.taller),
                selectinload(Usuario.rol),
                selectinload(Usuario.identidades_whatsapp),
                selectinload(Usuario.solicitudes_acceso),
            )
            .where(Usuario.id == usuario_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def listar_por_taller(self, taller_id: uuid.UUID, solo_mecanicos: bool = False) -> Sequence[Usuario]:
        """Lista todos los usuarios (o mecánicos) pertenecientes a un taller."""
        stmt = (
            select(Usuario)
            .options(
                selectinload(Usuario.rol),
                selectinload(Usuario.diagnosticos),
                selectinload(Usuario.taller),
                selectinload(Usuario.identidades_whatsapp),
            )
            .where(Usuario.taller_id == taller_id)
        )
        if solo_mecanicos:
            # Excluir rol cliente (id: 4)
            stmt = stmt.where(Usuario.rol_id != 4)

        stmt = stmt.order_by(Usuario.nombres.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def listar_clientes_por_taller(
        self,
        taller_id: uuid.UUID,
        busqueda: Optional[str] = None,
    ) -> Sequence[Usuario]:
        """Lista los usuarios con rol cliente de un taller, con soporte de búsqueda."""
        stmt = (
            select(Usuario)
            .options(
                selectinload(Usuario.rol),
                selectinload(Usuario.identidades_whatsapp),
                selectinload(Usuario.solicitudes_acceso),
                selectinload(Usuario.conversaciones),
            )
            .where(Usuario.taller_id == taller_id, Usuario.rol_id == 4)
        )
        if busqueda:
            term = f"%{busqueda.strip()}%"
            stmt = stmt.where(
                or_(
                    Usuario.nombres.ilike(term),
                    Usuario.whatsapp_ultimos4.ilike(term),
                )
            )

        stmt = stmt.order_by(Usuario.creado_en.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def promover_a_mecanico(
        self,
        usuario_id: uuid.UUID,
        password_hash: str,
    ) -> Optional[Usuario]:
        """Promueve un usuario cliente a rol mecánico asignando una contraseña temporal."""
        usuario = await self.obtener_por_id(usuario_id)
        if not usuario:
            return None

        roles = await self.asegurar_roles_estandar()
        usuario.rol_id = roles["mecanico"].id
        usuario.password_hash = password_hash
        usuario.debe_cambiar_password = True
        usuario.activo = True
        usuario.bloqueado = False
        await self.session.flush()
        return usuario

    async def revocar_acceso_tecnico(self, usuario_id: uuid.UUID) -> Optional[Usuario]:
        """Convierte un usuario interno en cliente conservando identidad e historial."""
        usuario = await self.obtener_por_id(usuario_id)
        if not usuario:
            return None

        roles = await self.asegurar_roles_estandar()
        usuario.rol_id = roles["cliente"].id
        usuario.password_hash = None
        usuario.debe_cambiar_password = False
        usuario.activo = True
        usuario.bloqueado = False
        await self.session.flush()
        return usuario

    async def toggle_bloqueo(self, usuario_id: uuid.UUID) -> Optional[Usuario]:
        """Bloquea o desbloquea a un usuario/contacto."""
        usuario = await self.obtener_por_id(usuario_id)
        if not usuario:
            return None
        usuario.bloqueado = not usuario.bloqueado
        if usuario.bloqueado:
            usuario.activo = False
        else:
            usuario.activo = True
        await self.session.flush()
        return usuario

    async def eliminar_usuario(self, usuario_id: uuid.UUID, taller_id: Optional[uuid.UUID] = None) -> bool:
        """Elimina un usuario de PostgreSQL tras desvincular sus diagnósticos históricos."""
        usuario = await self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        if taller_id and usuario.taller_id != taller_id:
            return False

        from sqlalchemy import update

        from src.infrastructure.database.models.diagnostics import Diagnostico

        # Desvincular diagnósticos previos asignando mecanico_id = None para no perder el historial
        await self.session.execute(
            update(Diagnostico)
            .where(Diagnostico.mecanico_id == usuario_id)
            .values(mecanico_id=None)
        )

        await self.session.delete(usuario)
        await self.session.commit()
        return True
