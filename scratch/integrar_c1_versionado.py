import os
import sys
import json
import hashlib
import shutil
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
src_c1 = base_dir / "machine_learning" / "training" / "fase10" / "final_candidate" / "C1"
dest_c1 = base_dir / "machine_learning" / "models" / "c1_fase10_final"
dest_c1.mkdir(parents=True, exist_ok=True)

expected_hashes = {
    "vectorizador_c1.pkl": "060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7",
    "modelo_diagnostico_c1.pkl": "24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c",
    "modelo_sistema_c1_macrofix.pkl": "dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c",
}

for fname, exp_hash in expected_hashes.items():
    src_f = src_c1 / fname
    dest_f = dest_c1 / fname
    assert src_f.exists(), f"Source file {src_f} does not exist!"
    src_bytes = src_f.read_bytes()
    src_h = hashlib.sha256(src_bytes).hexdigest()
    assert src_h == exp_hash, f"Source hash mismatch for {fname}: got {src_h}, expected {exp_hash}"
    
    shutil.copy2(src_f, dest_f)
    dest_bytes = dest_f.read_bytes()
    dest_h = hashlib.sha256(dest_bytes).hexdigest()
    assert dest_h == exp_hash, f"Copied hash mismatch for {fname}: got {dest_h}, expected {exp_hash}"
    print(f"OK: {fname} -> {dest_f} ({len(dest_bytes)} bytes) [SHA256: {dest_h}]")

# Copy metadata manifests as well
for extra in ["metadata_c1_macrofix.json", "C1_FINAL_MANIFEST.json", "C1_FINAL_HASH_MANIFEST.json"]:
    src_extra = src_c1 / extra
    if src_extra.exists():
        shutil.copy2(src_extra, dest_c1 / extra)
        print(f"OK: Copied manifest {extra}")

print("\nIntegración de artefactos en machine_learning/models/c1_fase10_final/ completada exitosamente!")
