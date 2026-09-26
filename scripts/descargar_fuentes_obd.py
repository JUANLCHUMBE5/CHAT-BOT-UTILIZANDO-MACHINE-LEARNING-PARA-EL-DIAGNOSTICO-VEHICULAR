"""Script para descargar fuentes abiertas automotrices (OBDex y DTC Database)."""

import os
import sys
import urllib.request
from pathlib import Path

DESTINO_BASE = Path("machine_learning/data/fuentes_abiertas")
DESTINO_OBDEX = DESTINO_BASE / "obdex"

DESTINO_BASE.mkdir(parents=True, exist_ok=True)
DESTINO_OBDEX.mkdir(parents=True, exist_ok=True)

RECURSOS = [
    {
        "nombre": "DTC Database (SQLite - 18,805 códigos)",
        "url": "https://raw.githubusercontent.com/Wal33D/dtc-database/main/data/dtc_codes.db",
        "archivo": DESTINO_BASE / "dtc_codes.db",
    },
    {
        "nombre": "OBDex P0xxx Enriched (Powertrain / Motor y Transmisión)",
        "url": "https://raw.githubusercontent.com/foerbsnavi/OBDex/main/data/generic/P0xxx_enriched.yaml",
        "archivo": DESTINO_OBDEX / "P0xxx_enriched.yaml",
    },
    {
        "nombre": "OBDex Generic DTC Bundle (CDN oficial del proyecto)",
        "url": "https://foerbsnavi.github.io/obdex/generic.min.json",
        "archivo": DESTINO_BASE / "obdex_generic.min.json",
    },
    {
        "nombre": "OBDex C0xxx Enriched (Chassis / Frenos, ABS, Dirección)",
        "url": "https://raw.githubusercontent.com/foerbsnavi/OBDex/main/data/generic/C0xxx_enriched.yaml",
        "archivo": DESTINO_OBDEX / "C0xxx_enriched.yaml",
    },
    {
        "nombre": "OBDex B0xxx Enriched (Body / Carrocería, Cierres, Airbag)",
        "url": "https://raw.githubusercontent.com/foerbsnavi/OBDex/main/data/generic/B0xxx_enriched.yaml",
        "archivo": DESTINO_OBDEX / "B0xxx_enriched.yaml",
    },
]


def descargar_archivo(recurso: dict):
    nombre = recurso["nombre"]
    url = recurso["url"]
    destino = recurso["archivo"]

    print(f"Descargando {nombre}...")
    print(f"  URL: {url}")
    print(f"  Destino: {destino}")

    req = urllib.request.Request(url, headers={"User-Agent": "CarBot-Downloader/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response, open(destino, "wb") as f_out:
        total_size = int(response.headers.get("content-length", 0))
        descargado = 0
        bloque = 65536

        while True:
            buffer = response.read(bloque)
            if not buffer:
                break
            f_out.write(buffer)
            descargado += len(buffer)
            if total_size > 0:
                pct = (descargado / total_size) * 100
                sys.stdout.write(f"\r  Progreso: {descargado // 1024} KB / {total_size // 1024} KB ({pct:.1f}%)")
            else:
                sys.stdout.write(f"\r  Descargado: {descargado // 1024} KB")
            sys.stdout.flush()

    print(f"\n  [OK] Guardado exitosamente ({destino.stat().st_size // 1024} KB)\n")


def main():
    print("=================================================================")
    print("   DESCARGA DE RECURSOS AUTOMOTRICES OFICIALES (OBDex + DTC DB)  ")
    print("=================================================================\n")

    for r in RECURSOS:
        try:
            descargar_archivo(r)
        except Exception as e:
            print(f"  [ERROR] Falló la descarga de {r['nombre']}: {e}\n")

    print("Descargas completadas.")


if __name__ == "__main__":
    main()
