import os
import sys
import json
import hashlib
import shutil
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
ml_models = base_dir / "machine_learning" / "models"
f83_frozen = ml_models / "fase8_3_frozen"
f83_frozen.mkdir(parents=True, exist_ok=True)

files_to_backup = [
    ("modelo_diagnostico.pkl", ml_models / "modelo_diagnostico.pkl"),
    ("modelo_sistema.pkl", ml_models / "modelo_sistema.pkl"),
    ("vectorizador_tfidf.pkl", ml_models / "vectorizador_tfidf.pkl"),
]

backup_manifest = []
for name, src in files_to_backup:
    dest = f83_frozen / name
    if not dest.exists():
        shutil.copy2(src, dest)
    src_bytes = src.read_bytes()
    dest_bytes = dest.read_bytes()
    src_h = hashlib.sha256(src_bytes).hexdigest()
    dest_h = hashlib.sha256(dest_bytes).hexdigest()
    assert src_h == dest_h, f"Backup hash mismatch for {name}"
    backup_manifest.append({
        "nombre": name,
        "ruta_produccion_original": str(src.relative_to(base_dir)).replace("\\", "/"),
        "ruta_respaldo_inmutable": str(dest.relative_to(base_dir)).replace("\\", "/"),
        "sha256": src_h,
        "bytes": len(src_bytes),
    })

other_files = [
    "machine_learning/models/fase8_candidata/modelo_diagnostico.pkl",
    "machine_learning/models/fase8_candidata/modelo_sistema.pkl",
    "machine_learning/models/fase8_candidata/vectorizador_tfidf.pkl",
    "backend/src/config.py",
    "backend/src/infrastructure/modelo_ml.py",
    "backend/src/infrastructure/container.py",
    "backend/src/core/gestor_diagnostico.py",
    "backend/src/core/diagnostico/taxonomia_sistemas.py",
]

file_entries = list(backup_manifest)
for rel in other_files:
    p = base_dir / rel
    if p.exists():
        b = p.read_bytes()
        file_entries.append({
            "nombre": p.name,
            "ruta": rel.replace("\\", "/"),
            "sha256": hashlib.sha256(b).hexdigest(),
            "bytes": len(b),
        })

manifest = {
    "fase": "FASE 11",
    "etapa": "ETAPA 1 - PRE-INTEGRACION CANDIDATO C1",
    "timestamp": "2026-09-17T23:58:00Z",
    "estado_produccion_actual": "F8.3_BASELINE_ACTIVO",
    "configuracion_actual": {
        "modelo_falla": "machine_learning/models/modelo_diagnostico.pkl",
        "modelo_falla_sha256": backup_manifest[0]["sha256"],
        "modelo_falla_clases": 48,
        "modelo_macro": "machine_learning/models/modelo_sistema.pkl",
        "modelo_macro_sha256": backup_manifest[1]["sha256"],
        "modelo_macro_clases": 7,
        "vectorizador": "machine_learning/models/vectorizador_tfidf.pkl",
        "vectorizador_sha256": backup_manifest[2]["sha256"],
        "calibrador": "CalibratedClassifierCV(base_estimator=LinearSVC, method=sigmoid)",
        "variables_entorno_intervinientes": [
            "MODEL_VERSION",
            "MODEL_PKL_PATH",
            "VECTORIZER_PKL_PATH",
            "MODELO_SISTEMA_PKL_PATH",
            "MODEL_PKL_SHA256",
            "VECTORIZER_PKL_SHA256",
            "ML_ROOT",
        ],
        "servicios_dependientes": [
            "ServiceContainer (Singleton DI)",
            "ModeloML (Infrastructure Adapter)",
            "GestorDiagnostico (Core Application Service)",
            "WebhookService (WhatsApp / Meta / Twilio Inbound)",
            "DiagnosticoEndpoints (FastAPI REST Router)",
            "SystemWorker (Background Diagnostics Worker)",
        ],
    },
    "archivos_registrados": file_entries,
    "mecanismo_rollback": {
        "disponible": True,
        "estrategia": "Configuracion explicita MODEL_VERSION=F8.3 o restauracion directa desde machine_learning/models/fase8_3_frozen/",
        "directorio_respaldo_inmutable": "machine_learning/models/fase8_3_frozen/",
    },
}

out_path = base_dir / "FASE11_PRE_INTEGRATION_MANIFEST.json"
out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print("FASE11_PRE_INTEGRATION_MANIFEST.json creado con exito!")
print(f"Archivos F8.3 respaldados en: {f83_frozen}")
for m in backup_manifest:
    print(f"  {m['nombre']}: {m['sha256']} ({m['bytes']} bytes)")
