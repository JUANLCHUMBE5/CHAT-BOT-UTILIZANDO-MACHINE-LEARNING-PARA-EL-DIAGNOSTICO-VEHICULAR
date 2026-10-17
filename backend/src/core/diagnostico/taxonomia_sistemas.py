"""
Puente al contrato y taxonomía canónica de Machine Learning (`machine_learning/models/taxonomia_sistemas.py`).
Garantiza que `carbot-machine-learning` sea la única fuente de verdad (Single Source of Truth)
para las 61 clases entrenadas, los 7 macro-sistemas, las subáreas técnicas y el contrato de inferencia,
fallando explícitamente si el despliegue no incluye el contrato canónico compatible.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ML_TAXONOMY_PATH = _REPO_ROOT / "machine_learning" / "models" / "taxonomia_sistemas.py"


def _cargar_modulo_ml():
    from src.infrastructure.ml_contract import taxonomy as bundled

    bundle_dir = Path(bundled.__file__).parent
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf8"))
    expected = manifest["sha256"]
    if hashlib.sha256(Path(bundled.__file__).read_text(encoding="utf8").encode("utf8")).hexdigest() != expected:
        raise RuntimeError("Contrato ML empaquetado no coincide con su manifiesto")
    if not _ML_TAXONOMY_PATH.exists():
        return bundled
    if hashlib.sha256(_ML_TAXONOMY_PATH.read_text(encoding="utf8").encode("utf8")).hexdigest() != expected:
        raise RuntimeError("Contrato ML canónico y paquete backend incompatibles; sincronice versiones")
    spec = importlib.util.spec_from_file_location("ml_taxonomia_sistemas", str(_ML_TAXONOMY_PATH))
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules["ml_taxonomia_sistemas"] = mod
        spec.loader.exec_module(mod)
        return mod
    raise RuntimeError("No se pudo cargar el contrato ML verificado")


_ml_mod = _cargar_modulo_ml()

if _ml_mod is not None:
    MODEL_VERSION: str = _ml_mod.MODEL_VERSION
    TAXONOMY_VERSION: str = _ml_mod.TAXONOMY_VERSION
    TAXONOMIA_MACRO_SISTEMAS: Dict[str, List[str]] = _ml_mod.TAXONOMIA_MACRO_SISTEMAS
    FALLA_A_SISTEMA: Dict[str, str] = _ml_mod.FALLA_A_SISTEMA
    CLASS_ID_POR_FALLA: Dict[str, str] = _ml_mod.CLASS_ID_POR_FALLA
    FALLA_POR_CLASS_ID: Dict[str, str] = _ml_mod.FALLA_POR_CLASS_ID
    CLASES_ENTRENADAS_61: Tuple[str, ...] = _ml_mod.CLASES_ENTRENADAS_61
    SUBAREAS_POR_CLASE: Dict[str, Set[str]] = _ml_mod.SUBAREAS_POR_CLASE
    DTC_A_SISTEMA: Dict[str, Tuple[str, List[str]]] = _ml_mod.DTC_A_SISTEMA
    ContratoPrediccionML = _ml_mod.ContratoPrediccionML
    es_clase_entrenada_svm = _ml_mod.es_clase_entrenada_svm
    obtener_class_id = _ml_mod.obtener_class_id
    obtener_subareas_de_clase = _ml_mod.obtener_subareas_de_clase
    obtener_macro_sistema = _ml_mod.obtener_macro_sistema
    obtener_sistema_por_dtc = _ml_mod.obtener_sistema_por_dtc
    construir_contrato_prediccion = _ml_mod.construir_contrato_prediccion
else:
    raise RuntimeError(
        "Taxonomía ML canónica no disponible. Instale el paquete ML compatible "
        "en machine_learning/models antes de iniciar el backend; no se usa una taxonomía alternativa."
    )
