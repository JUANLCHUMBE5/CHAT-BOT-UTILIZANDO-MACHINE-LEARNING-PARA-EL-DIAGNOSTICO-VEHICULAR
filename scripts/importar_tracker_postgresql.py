"""Importa una sola vez el tracker CSV histórico a PostgreSQL de forma idempotente."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import hmac
import sys
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from src.config import settings  # noqa: E402
from src.infrastructure.database.connection import obtener_engine  # noqa: E402
from src.infrastructure.database.models.catalogs import Taller, Usuario  # noqa: E402
from src.infrastructure.database.models.validation import ValidacionTaller  # noqa: E402

TALLER_SEED = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _entero(valor: str | None, predeterminado: int) -> int:
    try:
        return int(float(valor or predeterminado))
    except (TypeError, ValueError):
        return predeterminado


def _uuid_opcional(valor: str | None) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(valor)) if valor else None
    except ValueError:
        return None


def _hash_placa(placa: str) -> str:
    normalizada = "".join(c for c in placa.upper() if c.isalnum())
    return hmac.new(
        settings.privacy_secret_key.encode("utf-8"),
        normalizada.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _leer(
    csv_path: Path,
    talleres: set[uuid.UUID],
    usuarios: set[uuid.UUID],
    taller_predeterminado: uuid.UUID | None,
) -> list[dict[str, Any]]:
    registros: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as archivo:
        for numero_linea, fila in enumerate(csv.DictReader(archivo), start=2):
            taller_id = _uuid_opcional(fila.get("taller_id")) or TALLER_SEED
            if taller_id == TALLER_SEED and taller_id not in talleres and taller_predeterminado:
                taller_id = taller_predeterminado
            if taller_id not in talleres:
                continue
            mecanico_id = _uuid_opcional(fila.get("mecanico_id"))
            if mecanico_id not in usuarios:
                mecanico_id = None
            placa = (fila.get("placa") or "***").strip()
            clave_origen = hashlib.sha256(
                f"{csv_path.resolve()}:{numero_linea}:{fila}".encode("utf-8")
            ).hexdigest()
            registros.append(
                {
                    "id": uuid.uuid4(),
                    "item": _entero(fila.get("item"), len(registros) + 1),
                    "origen_clave": clave_origen,
                    "taller_id": taller_id,
                    "mecanico_id": mecanico_id,
                    "fase": fila.get("fase") or "Piloto",
                    "fecha": date.fromisoformat(fila.get("fecha") or date.today().isoformat()),
                    "placa_enmascarada": placa[:15],
                    "placa_hash": (fila.get("placa_hash") or _hash_placa(placa))[:64],
                    "marca_modelo": (fila.get("marca_modelo") or "Sin identificar")[:100],
                    "sintoma": fila.get("sintoma") or "Sin detalle",
                    "falla_real": fila.get("falla_real") or "Sin confirmar",
                    "chatbot_prediccion": fila.get("chatbot_prediccion") or "Sin predicción",
                    "campos_completos": _entero(fila.get("campos_completos"), 0),
                    "tiempo_diagnostico_minutos": _entero(
                        fila.get("tiempo_diagnostico_minutos"), 1
                    ),
                    "prediccion_correcta": _entero(fila.get("prediccion_correcta"), 0),
                    "metodo_confirmacion": (fila.get("metodo_confirmacion") or None),
                    "evidencia_ref": fila.get("evidencia_ref") or None,
                }
            )
    return registros


async def importar(
    csv_path: Path,
    dry_run: bool,
    taller_id_forzado: uuid.UUID | None = None,
    reemplazar: bool = False,
) -> tuple[int, int]:
    engine = obtener_engine()
    async with engine.begin() as session:
        talleres = set((await session.execute(select(Taller.id))).scalars().all())
        usuarios = set((await session.execute(select(Usuario.id))).scalars().all())
        if taller_id_forzado and taller_id_forzado not in talleres:
            raise ValueError("El --taller-id indicado no existe en PostgreSQL.")
        taller_predeterminado = taller_id_forzado or (next(iter(talleres)) if len(talleres) == 1 else None)
        registros = _leer(csv_path, talleres, usuarios, taller_predeterminado)
        if reemplazar:
            if not taller_id_forzado:
                raise ValueError("--reemplazar exige indicar --taller-id explícitamente.")
            await session.execute(
                delete(ValidacionTaller).where(ValidacionTaller.taller_id == taller_id_forzado)
            )
        existentes_antes = int(
            (await session.execute(select(func.count()).select_from(ValidacionTaller))).scalar_one()
        )
        if not dry_run:
            for inicio in range(0, len(registros), 500):
                sentencia = insert(ValidacionTaller).values(registros[inicio : inicio + 500])
                await session.execute(
                    sentencia.on_conflict_do_nothing(index_elements=["origen_clave"])
                )
            await session.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('validaciones_taller', 'item'), "
                    "GREATEST(COALESCE((SELECT MAX(item) FROM validaciones_taller), 1), 1), true)"
                )
            )
        existentes_despues = existentes_antes if dry_run else int(
            (await session.execute(select(func.count()).select_from(ValidacionTaller))).scalar_one()
        )
    await engine.dispose()
    return len(registros), existentes_despues - existentes_antes


async def listar_talleres() -> list[tuple[uuid.UUID, str]]:
    engine = obtener_engine()
    async with engine.connect() as session:
        talleres = list((await session.execute(select(Taller.id, Taller.nombre))).all())
    await engine.dispose()
    return talleres


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=settings.paths.tracker_csv)
    parser.add_argument("--taller-id", type=uuid.UUID)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--reemplazar",
        action="store_true",
        help="Reemplaza solo los registros del --taller-id usando el CSV como respaldo.",
    )
    parser.add_argument("--listar-talleres", action="store_true")
    args = parser.parse_args()
    if args.listar_talleres:
        for taller_id, nombre in asyncio.run(listar_talleres()):
            print(f"{taller_id}  {nombre}")
        return 0
    if not args.csv.is_file():
        parser.error(f"No existe el archivo: {args.csv}")
    leidos, insertados = asyncio.run(
        importar(args.csv.resolve(), args.dry_run, args.taller_id, args.reemplazar)
    )
    modo = "validados" if args.dry_run else "insertados"
    print(f"Registros CSV leídos: {leidos}; registros {modo}: {insertados}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
