#!/usr/bin/env python3
"""
Script de línea de comandos para registrar de forma segura el primer taller
mecánico y su administrador/mecánico principal en PostgreSQL.

Seguridad:
- NUNCA almacena el número de WhatsApp en texto plano.
- Calcula el hash HMAC-SHA256 con PRIVACY_SECRET_KEY.
- Guarda únicamente whatsapp_hash (64 caracteres) y los últimos 4 dígitos.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
from pathlib import Path
import sys
from typing import Optional

# Configurar encoding UTF-8 seguro para consolas de Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Asegurar que el directorio raíz esté en sys.path para ejecuciones directas
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from dotenv import load_dotenv

# Cargar variables de entorno automáticamente
load_dotenv(RAIZ_PROYECTO / ".env")

from sqlalchemy.ext.asyncio import AsyncSession

# Importar configuración y repositorios
from src.config import settings
from src.core.security import hash_identificador_persistencia
from src.infrastructure.database.connection import (
    cerrar_conexion,
    database_configurada,
    obtener_engine,
)
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


async def registrar_taller_y_administrador(
    nombre_taller: str,
    ruc: Optional[str],
    direccion: Optional[str],
    telefono_taller: Optional[str],
    nombres: str,
    apellidos: Optional[str],
    telefono_whatsapp: str,
    codigo_rol: str = "administrador",
) -> dict:
    """Registra el taller y el usuario con su hash de WhatsApp de forma transaccional."""
    if not database_configurada():
        raise RuntimeError(
            "PostgreSQL no está habilitado. Asegúrese de configurar DATABASE_ENABLED=true en .env"
        )

    # Validar teléfono
    telefono_limpio = "".join(c for c in telefono_whatsapp if c.isdigit())
    if len(telefono_limpio) < 6:
        raise ValueError("El número de WhatsApp debe contener al menos 6 dígitos válidos.")

    whatsapp_ultimos4 = telefono_limpio[-4:]
    whatsapp_hash = hash_identificador_persistencia(telefono_whatsapp, "telefono")

    engine = obtener_engine()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        async with session.begin():
            taller_repo = TallerRepository(session)
            usuario_repo = UsuarioRepository(session)

            # 1. Asegurar roles estándar
            roles = await usuario_repo.asegurar_roles_estandar()
            rol = roles.get(codigo_rol)
            if not rol:
                raise RuntimeError(f"No se encontró el rol '{codigo_rol}'.")

            # 2. Buscar o crear taller
            taller = None
            if ruc:
                taller = await taller_repo.obtener_por_ruc(ruc)

            if taller is None:
                taller = await taller_repo.crear_taller(
                    nombre=nombre_taller,
                    ruc=ruc,
                    direccion=direccion,
                    telefono=telefono_taller,
                    activo=True,
                )

            # 3. Buscar si el usuario ya está registrado por su hash
            usuario = await usuario_repo.buscar_por_whatsapp_hash(whatsapp_hash)
            if usuario:
                return {
                    "estado": "existente",
                    "taller_id": str(taller.id),
                    "taller_nombre": taller.nombre,
                    "taller_ruc": taller.ruc,
                    "usuario_id": str(usuario.id),
                    "usuario_nombres": f"{usuario.nombres} {usuario.apellidos or ''}".strip(),
                    "rol": rol.nombre,
                    "whatsapp_ultimos4": usuario.whatsapp_ultimos4,
                    "whatsapp_hash": usuario.whatsapp_hash,
                }

            # 4. Crear nuevo usuario / mecánico
            usuario = await usuario_repo.crear_usuario(
                taller_id=taller.id,
                rol_id=rol.id,
                nombres=nombres,
                apellidos=apellidos,
                whatsapp_hash=whatsapp_hash,
                whatsapp_ultimos4=whatsapp_ultimos4,
                activo=True,
            )

            return {
                "estado": "creado",
                "taller_id": str(taller.id),
                "taller_nombre": taller.nombre,
                "taller_ruc": taller.ruc,
                "usuario_id": str(usuario.id),
                "usuario_nombres": f"{usuario.nombres} {usuario.apellidos or ''}".strip(),
                "rol": rol.nombre,
                "whatsapp_ultimos4": usuario.whatsapp_ultimos4,
                "whatsapp_hash": usuario.whatsapp_hash,
            }


async def _ejecutar_cli(args, telefono: str):
    try:
        resultado = await registrar_taller_y_administrador(
            nombre_taller=args.taller,
            ruc=args.ruc,
            direccion=args.direccion,
            telefono_taller=args.telefono_taller,
            nombres=args.nombres,
            apellidos=args.apellidos,
            telefono_whatsapp=telefono,
            codigo_rol=args.rol,
        )

        estado_txt = "REGISTRADO EXITOSAMENTE" if resultado["estado"] == "creado" else "YA ESTABA REGISTRADO"
        print("\n" + "=" * 60)
        print(f"[OK] TALLER Y MECANICO {estado_txt}")
        print("=" * 60)
        print(f"[*] Taller: {resultado['taller_nombre']} (ID: {resultado['taller_id']})")
        if resultado["taller_ruc"]:
            print(f"[*] RUC: {resultado['taller_ruc']}")
        print(f"[*] Usuario: {resultado['usuario_nombres']} (ID: {resultado['usuario_id']})")
        print(f"[*] Rol: {resultado['rol']}")
        print(f"[*] WhatsApp (Protegido): *******{resultado['whatsapp_ultimos4']}")
        print("[*] Privacidad: Telefono protegido criptograficamente (no guardado en plano).")
        print("=" * 60 + "\n")
    finally:
        await cerrar_conexion()


def main():
    parser = argparse.ArgumentParser(
        description="Registra de forma segura el taller y el administrador inicial en CarBot PostgreSQL."
    )
    parser.add_argument(
        "--taller",
        default="Taller Mecánico Carabayllo Motors",
        help="Nombre del taller mecánico",
    )
    parser.add_argument("--ruc", default=None, help="RUC del taller (11 dígitos)")
    parser.add_argument("--direccion", default=None, help="Dirección del taller")
    parser.add_argument("--telefono-taller", default=None, help="Teléfono fijo o central del taller")
    parser.add_argument("--nombres", default="Administrador", help="Nombres del usuario/mecánico")
    parser.add_argument("--apellidos", default="Principal", help="Apellidos del usuario/mecánico")
    parser.add_argument(
        "--telefono",
        default=None,
        help="Número de WhatsApp (opcional por CLI; si se omite se solicita de forma segura por prompt oculto)",
    )
    parser.add_argument(
        "--rol",
        default="administrador",
        choices=["administrador", "admin", "mecanico", "supervisor"],
        help="Código de rol asignado (administrador / mecanico / supervisor)",
    )

    args = parser.parse_args()

    telefono = args.telefono
    if not telefono:
        print("\n========================================================")
        print("REGISTRO SEGURO DE ADMINISTRADOR / MECANICO EN CARBOT")
        print("========================================================")
        print("El número no se mostrará en pantalla ni se guardará en texto plano.")
        try:
            telefono = getpass.getpass("Ingrese el número de WhatsApp (ej. +51987654321): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            sys.exit(1)

    if not telefono:
        print("Error: El número de WhatsApp es obligatorio.")
        sys.exit(1)

    try:
        asyncio.run(_ejecutar_cli(args, telefono))
    except Exception as exc:
        print(f"\nError al registrar en PostgreSQL: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
