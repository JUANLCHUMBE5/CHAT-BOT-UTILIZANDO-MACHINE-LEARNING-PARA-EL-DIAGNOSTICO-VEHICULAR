"""
Script de descarga y auditoría de datasets abiertos automotrices para CarBot.
Descarga y cataloga fuentes gratuitas para RAG, DTC y Machine Learning sin contaminar la muestra oficial de tesis.
"""

import os
import sys
import subprocess
import urllib.request
import json
import glob
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FUENTES_DIR = BASE_DIR / "machine_learning" / "data" / "fuentes_abiertas"
FUENTES_DIR.mkdir(parents=True, exist_ok=True)

def ejecutar_git_clone(url: str, destino_nombre: str) -> bool:
    destino = FUENTES_DIR / destino_nombre
    if destino.exists() and (destino / ".git").exists():
        print(f"[OK] Ya existe: {destino_nombre}")
        return True
    
    print(f"[*] Clonando {url} en {destino_nombre}...")
    try:
        res = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(destino)],
            capture_output=True,
            text=True,
            timeout=120
        )
        if res.returncode == 0:
            print(f"[EXITO] Clonado: {destino_nombre}")
            return True
        else:
            print(f"[ERROR] Error al clonar {destino_nombre}: {res.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción clonando {destino_nombre}: {e}")
        return False

def descargar_archivo(url: str, destino_nombre: str) -> bool:
    destino = FUENTES_DIR / destino_nombre
    if destino.exists() and destino.stat().st_size > 0:
        print(f"[OK] Ya existe archivo: {destino_nombre} ({destino.stat().st_size / 1024:.1f} KB)")
        return True
    
    print(f"[*] Descargando {url} -> {destino_nombre}...")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=45) as resp, open(destino, "wb") as f:
            f.write(resp.read())
        print(f"[EXITO] Descargado: {destino_nombre} ({destino.stat().st_size / 1024:.1f} KB)")
        return True
    except Exception as e:
        print(f"[AVISO] No se pudo descargar directamente {destino_nombre}: {e}")
        return False

def main():
    print("=" * 65)
    print("  CARBOT: DESCARGA DE FUENTES ABIERTAS (RAG + DTC + TELEMETRÍA)")
    print("=" * 65)

    # 1. OBDex: se conserva el clon versionado; los endpoints JSON antiguos
    # dejaron de existir y no deben provocar un falso fallo del inventario.
    ejecutar_git_clone("https://github.com/foerbsnavi/obdex.git", "obdex_repo")

    # 2. obd-trouble-codes (mytrile)
    ejecutar_git_clone("https://github.com/mytrile/obd-trouble-codes.git", "obd_trouble_codes_repo")

    # 3. EngineFaultDB (Leo-Thomas)
    ejecutar_git_clone("https://github.com/Leo-Thomas/EngineFaultDB.git", "engine_fault_db_repo")

    # 4. carOBD (Toyota Etios)
    ejecutar_git_clone("https://github.com/eron93br/carOBD.git", "car_obd_etios_repo")

    # 5. OBDb community
    ejecutar_git_clone("https://github.com/obdb/obdb.git", "obdb_repo")

    print("\n" + "=" * 65)
    print("  INVENTARIO COMPLETO EN: machine_learning/data/fuentes_abiertas/")
    print("=" * 65)

    items = list(FUENTES_DIR.iterdir())
    for it in sorted(items, key=lambda x: x.name):
        if it.is_dir():
            conteo = len(list(it.rglob("*")))
            print(f"[DIR] {it.name:<30} (Carpeta / {conteo} elementos)")
        else:
            tam_kb = it.stat().st_size / 1024
            print(f"[FILE] {it.name:<30} ({tam_kb:.1f} KB)")

if __name__ == "__main__":
    main()
