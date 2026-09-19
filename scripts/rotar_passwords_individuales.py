#!/usr/bin/env python3
"""
Script de seguridad administrativa:
Genera contraseñas temporales criptográficamente seguras e independientes
para cada usuario en PostgreSQL con salts y hashes PBKDF2 únicos (600,000 iteraciones).
"""

import asyncio
import csv
import os
import secrets
import string
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from dotenv import load_dotenv

load_dotenv(RAIZ_PROYECTO.parent / ".env")

os.environ["DATABASE_ENABLED"] = "true"

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generar_password_hash
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.catalogs import Usuario


def generar_password_segura(longitud: int = 12) -> str:
    """Genera una contraseña aleatoria con mayúsculas, minúsculas, dígitos y símbolos seguros."""
    alfabeto = string.ascii_letters + string.digits + "!@#$%&*"
    while True:
        password = "".join(secrets.choice(alfabeto) for _ in range(longitud))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%&*" for c in password)
        ):
            return password


async def main():
    engine = obtener_engine()
    credenciales_generadas = []

    async with AsyncSession(engine) as session:
        res = await session.execute(select(Usuario).order_by(Usuario.nombres))
        usuarios = res.scalars().all()

        if not usuarios:
            print("[INFO] No se encontraron usuarios en la base de datos PostgreSQL.")
            return

        for u in usuarios:
            pwd_temporal = generar_password_segura(12)
            u.password_hash = generar_password_hash(pwd_temporal)
            u.debe_cambiar_password = True
            credenciales_generadas.append({
                "id": str(u.id),
                "nombres": u.nombres,
                "ultimos4": u.whatsapp_ultimos4,
                "password_temporal": pwd_temporal,
            })

        await session.commit()

    directorio_seguro = Path(os.getenv("LOCALAPPDATA", Path.home())) / "CarBot"
    directorio_seguro.mkdir(parents=True, exist_ok=True)
    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_salida = directorio_seguro / f"credenciales_temporales_{marca_tiempo}.csv"

    with archivo_salida.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(
            archivo,
            fieldnames=["id", "nombres", "ultimos4", "password_temporal"],
        )
        writer.writeheader()
        writer.writerows(credenciales_generadas)

    if os.name == "nt":
        usuario_windows = os.getenv("USERNAME", "")
        if usuario_windows:
            subprocess.run(
                [
                    "icacls",
                    str(archivo_salida),
                    "/inheritance:r",
                    "/grant:r",
                    f"{usuario_windows}:(F)",
                ],
                check=False,
                capture_output=True,
            )
    else:
        archivo_salida.chmod(0o600)

    print("Rotación completada sin mostrar contraseñas en pantalla.")
    print(f"Usuarios actualizados: {len(credenciales_generadas)}")
    print(f"Archivo local protegido: {archivo_salida}")
    print("Elimine el archivo después de entregar cada clave por un canal privado.")


if __name__ == "__main__":
    asyncio.run(main())
