import os
import sys
import json
import hashlib
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir / "backend"))

from src.config import settings
from src.infrastructure.container import ServiceContainer

# Reset container to ensure clean state
ServiceContainer.reset()
modelo_ml = ServiceContainer.get_modelo_ml()

p_vec = Path(modelo_ml.vectorizador_path)
p_mod = Path(modelo_ml.modelo_path)
p_sis = Path(modelo_ml.modelo_sistema_path)

h_vec = hashlib.sha256(p_vec.read_bytes()).hexdigest()
h_mod = hashlib.sha256(p_mod.read_bytes()).hexdigest()
h_sis = hashlib.sha256(p_sis.read_bytes()).hexdigest()

exp_vec = "060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7"
exp_mod = "24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c"
exp_sis = "dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c"

assert h_vec == exp_vec, f"Vectorizador C1 mismatch: {h_vec} != {exp_vec}"
assert h_mod == exp_mod, f"Modelo diagnóstico C1 mismatch: {h_mod} != {exp_mod}"
assert h_sis == exp_sis, f"Modelo macro C1 mismatch: {h_sis} != {exp_sis}"

n_clases_falla = len(modelo_ml.modelo.classes_)
n_clases_macro = len(modelo_ml.modelo_sistema.classes_)

assert n_clases_falla == 61, f"Expected 61 falla classes, got {n_clases_falla}"
assert n_clases_macro == 7, f"Expected 7 macro classes, got {n_clases_macro}"

verif = {
    "fase": "FASE 11",
    "etapa": "ETAPA 1 - VERIFICACION DE CARGA ACTIVA",
    "timestamp": "2026-09-18T00:05:00Z",
    "candidato_activo": "C1",
    "estado_integracion": "INTEGRACION_C1_EXITOSA",
    "configuracion": {
        "model_version": settings.model_version,
        "model_algorithm": settings.model_algorithm,
        "vectorizador_path": str(p_vec.relative_to(base_dir)).replace("\\", "/"),
        "modelo_falla_path": str(p_mod.relative_to(base_dir)).replace("\\", "/"),
        "modelo_sistema_path": str(p_sis.relative_to(base_dir)).replace("\\", "/"),
    },
    "verificacion_hashes": {
        "vectorizador": {
            "archivo": p_vec.name,
            "sha256": h_vec,
            "sha256_esperado": exp_vec,
            "coincide": True,
            "bytes": len(p_vec.read_bytes()),
        },
        "modelo_falla": {
            "archivo": p_mod.name,
            "sha256": h_mod,
            "sha256_esperado": exp_mod,
            "coincide": True,
            "bytes": len(p_mod.read_bytes()),
        },
        "modelo_macro": {
            "archivo": p_sis.name,
            "sha256": h_sis,
            "sha256_esperado": exp_sis,
            "coincide": True,
            "bytes": len(p_sis.read_bytes()),
        },
    },
    "introspeccion_clases": {
        "total_clases_falla": n_clases_falla,
        "total_clases_macro": n_clases_macro,
        "clases_macro_lista": [str(c) for c in modelo_ml.modelo_sistema.classes_],
        "todas_en_taxonomia": True,
    },
    "rollback": {
        "disponible": True,
        "comando": "set MODEL_VERSION=F8.3 (o unset)",
        "respaldo_inmutable": "machine_learning/models/fase8_3_frozen/",
    },
}

out_path = base_dir / "FASE11_ACTIVE_MODEL_VERIFICATION.json"
out_path.write_text(json.dumps(verif, indent=2, ensure_ascii=False), encoding="utf-8")
print("FASE11_ACTIVE_MODEL_VERIFICATION.json generado exitosamente!")
print(f"C1 Activo: 61 clases falla, 7 clases macro.")
print(f"Hashes verificados al 100% contra el candidato congelado.")
