#!/usr/bin/env python3
"""
Script utilitario para consultar y establecer credenciales de administrador en PostgreSQL.

Uso:
  python scripts/gestionar_admin.py --listar
  python scripts/gestionar_admin.py --usuario "Juan Carlos Chumbe"

La contraseña se solicita mediante una entrada oculta y nunca viaja en la
línea de comandos ni se imprime en pantalla.
"""

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

# Configurar encoding UTF-8 seguro para consolas de Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Configurar sys.path
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.security import generar_password_hash, hash_identificador_persistencia
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Usuario
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


async def listar_administradores():
    if not database_configurada():
        print("❌ PostgreSQL no está configurado o DATABASE_ENABLED=false")
        return

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.taller), selectinload(Usuario.rol))
            .where(Usuario.rol_id.in_([1, 2, 3]))
        )
        usuarios = (await session.execute(stmt)).scalars().all()

        print("\n" + "=" * 60)
        print("👥 USUARIOS DEL PERSONAL / ADMINISTRADORES REGISTRADOS")
        print("=" * 60)
        if not usuarios:
            print("No hay usuarios registrados con rol administrativo.")
        for u in usuarios:
            print(f"• Nombre (Username) : {u.nombres} {u.apellidos or ''}".strip())
            print(f"  Rol               : {u.rol.nombre if u.rol else 'N/A'} ({u.rol.codigo if u.rol else ''})")
            print(f"  Taller            : {u.taller.nombre if u.taller else 'N/A'}")
            print(f"  Teléfono últimos4 : *** *** {u.whatsapp_ultimos4}")
            print(f"  Tiene Contraseña  : {'Sí' if u.password_hash else 'No'}")
            print(f"  Estado            : {'ACTIVO' if u.activo and not u.bloqueado else 'INACTIVO/BLOQUEADO'}")
            print("-" * 60)


async def establecer_password(nombres: str, nuevo_password: str, telefono: str = None):
    if not database_configurada():
        print("❌ PostgreSQL no está configurado.")
        return

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        taller_repo = TallerRepository(session)

        # Buscar si ya existe el usuario
        usuario = None
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.taller), selectinload(Usuario.rol))
            .where(Usuario.nombres.ilike(nombres.strip()))
        )
        usuario = (await session.execute(stmt)).scalars().first()

        password_hash = generar_password_hash(nuevo_password)

        if usuario:
            usuario.password_hash = password_hash
            usuario.debe_cambiar_password = False
            usuario.activo = True
            usuario.bloqueado = False
            await session.commit()
            print(f"\n✅ Contraseña actualizada exitosamente para el usuario '{usuario.nombres}'.")
            print("👉 Puedes iniciar sesión en la web con:")
            print(f"   • Usuario    : {usuario.nombres}")
            print("   • Contraseña : actualizada de forma segura\n")
        else:
            # Crear administrador en el taller activo
            taller = await taller_repo.obtener_primer_taller_activo()
            if not taller:
                print("❌ No se encontró ningún taller activo en la base de datos.")
                return

            roles = await user_repo.asegurar_roles_estandar()
            rol_admin = roles.get("administrador")

            if not telefono:
                raise ValueError("El teléfono es obligatorio para crear un administrador nuevo.")
            tel = telefono
            digits = "".join(c for c in tel if c.isdigit())
            ult4 = digits[-4:] if len(digits) >= 4 else "9999"
            w_hash = hash_identificador_persistencia(tel, "telefono")

            nuevo_u = await user_repo.crear_usuario(
                taller_id=taller.id,
                rol_id=rol_admin.id,
                nombres=nombres.strip(),
                whatsapp_hash=w_hash,
                whatsapp_ultimos4=ult4,
                password_hash=password_hash,
                debe_cambiar_password=False,
                activo=True,
            )
            await session.commit()
            print(f"\n✅ Administrador '{nuevo_u.nombres}' creado exitosamente en '{taller.nombre}'.")
            print("👉 Puedes iniciar sesión en la web con:")
            print(f"   • Usuario    : {nuevo_u.nombres}")
            print("   • Contraseña : configurada de forma segura\n")


def main():
    parser = argparse.ArgumentParser(description="Gestor de credenciales de administrador")
    parser.add_argument("--listar", action="store_true", help="Listar administradores registrados")
    parser.add_argument("--usuario", type=str, help="Nombre de usuario del administrador")
    parser.add_argument("--telefono", type=str, help="Teléfono de contacto (opcional al crear)")

    args = parser.parse_args()

    if args.listar or not args.usuario:
        asyncio.run(listar_administradores())
    else:
        password = getpass.getpass("Nueva contraseña (mínimo 12 caracteres): ")
        confirmation = getpass.getpass("Repita la contraseña: ")
        if password != confirmation:
            raise SystemExit("Las contraseñas no coinciden.")
        if len(password) < 12:
            raise SystemExit("La contraseña debe tener al menos 12 caracteres.")
        asyncio.run(establecer_password(args.usuario, password, args.telefono))


if __name__ == "__main__":
    main()
