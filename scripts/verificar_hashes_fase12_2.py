import argparse
import hashlib
import json
import sys
from pathlib import Path


def verificar_hashes(manifest_name: str) -> None:
    root = Path(__file__).resolve().parent.parent
    manifest_path = root / "docs" / "fase11_6" / manifest_name
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No existe el manifiesto de integridad: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    errors = []
    print(f"=== VERIFICACION DE HASHES CONGELADOS: {data['version']} ({data['fase']}) ===")
    for k, v in data["hashes_sha256"].items():
        p = root / v["ruta_relativa"]
        if not p.exists():
            errors.append(f"[FALTA] {k}: archivo no existe en {p}")
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        expected = v["sha256"]
        if h != expected:
            errors.append(f"[DIFERENCIA] {k}: esperado {expected}, obtenido {h}")
        else:
            print(f"[OK] {k}: {h}")
            
    if errors:
        print("\nERRORES ENCONTRADOS:")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        total = len(data["hashes_sha256"])
        print(f"\n[EXITO] TODOS LOS {total} COMPONENTES CONGELADOS PERMANECEN 100% IDENTICOS.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verifica un manifiesto de integridad CarBot.")
    parser.add_argument(
        "--manifest",
        default="CARBOT_PRECAMPO_COHERENCIA_HASH_MANIFEST.json",
        help="Nombre de archivo dentro de docs/fase11_6/.",
    )
    args = parser.parse_args()
    verificar_hashes(args.manifest)
