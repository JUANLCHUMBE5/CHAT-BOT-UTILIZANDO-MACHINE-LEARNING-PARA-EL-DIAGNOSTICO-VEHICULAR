"""Verificación de hashes congelados para FASE 12.3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "docs" / "fase11_6" / "CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json"


def verificar_hashes() -> bool:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("=============================================================================================================================================")
    print(f"{'COMPONENTE':<30} | {'HASH ESPERADO':<64} | {'HASH ACTUAL':<64} | {'COINCIDE':<8}")
    print("=============================================================================================================================================")

    all_matched = True
    for name, info in manifest["hashes_sha256"].items():
        rel_path = info["ruta_relativa"]
        expected_hash = info["sha256"]
        file_path = ROOT / rel_path

        if not file_path.exists():
            print(f"{name:<30} | {expected_hash:<64} | {'ARCHIVO_NO_EXISTE':<64} | NO")
            all_matched = False
            continue

        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        coincide = "SI" if actual_hash == expected_hash else "NO"
        if coincide == "NO":
            all_matched = False

        print(f"{name:<30} | {expected_hash:<64} | {actual_hash:<64} | {coincide:<8}")

    print("=============================================================================================================================================")
    print(f"DICTAMEN HASHES CONGELADOS: {'APROBADO (13/13 COINCIDEN)' if all_matched else 'FALLIDO'}")
    return all_matched


if __name__ == "__main__":
    verificar_hashes()
