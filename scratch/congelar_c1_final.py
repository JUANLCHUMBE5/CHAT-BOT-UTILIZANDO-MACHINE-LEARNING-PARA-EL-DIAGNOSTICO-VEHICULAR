import shutil
import hashlib
import json
import time
from pathlib import Path

base_dir = Path('.').resolve()
src_dir = base_dir / "machine_learning/training/fase10/candidates/C1"
dest_dir = base_dir / "machine_learning/training/fase10/final_candidate/C1"
dest_dir.mkdir(parents=True, exist_ok=True)

files_to_copy = [
    "vectorizador_c1.pkl",
    "modelo_diagnostico_c1.pkl",
    "modelo_sistema_c1_macrofix.pkl",
    "metadata_c1_macrofix.json"
]

manifest_entries = []
for fname in files_to_copy:
    src_file = src_dir / fname
    dest_file = dest_dir / fname
    shutil.copy2(src_file, dest_file)
    
    src_h = hashlib.sha256(src_file.read_bytes()).hexdigest()
    dest_h = hashlib.sha256(dest_file.read_bytes()).hexdigest()
    assert src_h == dest_h, f"Hash mismatch after copying {fname}!"
    
    manifest_entries.append({
        "archivo": f"machine_learning/training/fase10/final_candidate/C1/{fname}",
        "sha256": dest_h,
        "bytes": dest_file.stat().st_size
    })
    print(f"Congelado {fname} -> SHA-256: {dest_h} ({dest_file.stat().st_size} bytes)")

# C1_FINAL_HASH_MANIFEST.json
with open(base_dir / "C1_FINAL_HASH_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "archivos": manifest_entries}, f, indent=2)

with open(dest_dir / "C1_FINAL_HASH_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "archivos": manifest_entries}, f, indent=2)

# C1_FINAL_MANIFEST.json
c1_final_manifest = {
    "candidate": "C1",
    "falla_classes": 61,
    "macro_classes": 7,
    "hash_vectorizer": hashlib.sha256((dest_dir / "vectorizador_c1.pkl").read_bytes()).hexdigest(),
    "hash_falla": hashlib.sha256((dest_dir / "modelo_diagnostico_c1.pkl").read_bytes()).hexdigest(),
    "hash_macro": hashlib.sha256((dest_dir / "modelo_sistema_c1_macrofix.pkl").read_bytes()).hexdigest(),
    "hash_metadata": hashlib.sha256((dest_dir / "metadata_c1_macrofix.json").read_bytes()).hexdigest(),
    "train_utilizado": "machine_learning/data/fase10/train10_v1_1_macrofix.csv",
    "train_hash": hashlib.sha256((base_dir / "machine_learning/data/fase10/train10_v1_1_macrofix.csv").read_bytes()).hexdigest(),
    "dev_utilizado": "machine_learning/data/fase10/dev10_v1_1_macrofix.csv",
    "dev_hash": hashlib.sha256((base_dir / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv").read_bytes()).hexdigest(),
    "arquitectura": "Hierarchical LinearSVM + Isotonic Calibration (TF-IDF word 1-2 25k features)",
    "tfidf_params": {
        "ngram_range": [1, 2],
        "max_features": 25000,
        "sublinear_tf": True,
        "strip_accents": "unicode",
        "min_df": 1
    },
    "linearsvc_params": {
        "falla": {"C": 1.2, "class_weight": "balanced", "max_iter": 3500, "random_state": 42},
        "macro": {"C": 1.0, "class_weight": "balanced", "max_iter": 3000, "random_state": 42}
    },
    "calibracion": "CalibratedClassifierCV(method='isotonic', cv=StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42))",
    "seed": 42,
    "fecha_congelamiento": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "estado": "FROZEN_BEFORE_TEST10"
}

with open(base_dir / "C1_FINAL_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump(c1_final_manifest, f, indent=2)

with open(dest_dir / "C1_FINAL_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump(c1_final_manifest, f, indent=2)

print("\nManifiestos C1_FINAL_MANIFEST.json y C1_FINAL_HASH_MANIFEST.json creados exitosamente!")
