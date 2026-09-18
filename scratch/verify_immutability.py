import hashlib
import json
from pathlib import Path

def main():
    base = Path(".")
    rep_path = base / "machine_learning" / "models" / "reporte_fase8_3_congelado.json"
    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    
    ok = 0
    total = len(rep["hashes_sha256"])
    print(f"Auditando {total} componentes congelados Fase 8.3...")
    for k, v in rep["hashes_sha256"].items():
        p = base / v["archivo"]
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == v["sha256"], f"DIVERGENCIA EN: {k} ({v['archivo']})"
        ok += 1
        print(f"[OK] {k:<30} -> {h[:16]}... (Inmutable)")

    print(f"\nRESULTADO FINAL: {ok}/{total} artefactos 100% IDÉNTICOS E INMUTABLES.")

if __name__ == "__main__":
    main()
