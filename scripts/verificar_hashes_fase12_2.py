import hashlib
import json
import sys
from pathlib import Path

def verificar_hashes():
    root = Path(__file__).resolve().parent.parent
    manifest_path = root / "docs" / "fase11_6" / "CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json"
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
        print("\n[EXITO] TODOS LOS 13 COMPONENTES CONGELADOS PERMANECEN 100% IDENTICOS.")

if __name__ == "__main__":
    verificar_hashes()
