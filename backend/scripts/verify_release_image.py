"""Smoke test del paquete congelado dentro de la imagen, sin red ni proveedores."""

import hashlib
import json
from pathlib import Path

from src.infrastructure.modelo_ml import ModeloML
from src.infrastructure.motor_rag import MotorRAG


def main() -> None:
    root = Path('/app/machine_learning')
    models = root / 'models/c1_fase10_final'
    manifest = json.loads((models / 'C1_FINAL_HASH_MANIFEST.json').read_text())
    for item in manifest['archivos']:
        name = Path(item['archivo']).name
        if name.endswith('.pkl'):
            actual = hashlib.sha256((models / name).read_bytes()).hexdigest()
            if actual != item['sha256']:
                raise ValueError(f'Hash congelado incompatible: {name}')
    model = ModeloML(
        modelo_path=str(models / 'modelo_diagnostico_c1.pkl'),
        vectorizador_path=str(models / 'vectorizador_c1.pkl'),
        modelo_sistema_path=str(models / 'modelo_sistema_c1_macrofix.pkl'),
        temperatura=1.0,
    )
    assert model.modelo is not None and model.modelo_sistema is not None
    assert len(model.modelo.classes_) == 61
    result = model.predecir_top_fallas('demora cinco segundos en arrancar en frio', limite=3)
    assert len(result) == 3 and all(row['falla'] != 'Error de prediccion' for row in result)
    rag = MotorRAG(manual_path=str(root / 'manuals'), rag_version='candidate_v1')
    assert rag.faiss_index is not None
    assert rag.faiss_index.d == 32708 and rag.faiss_index.ntotal == 239
    assert len(rag.documentos) == 239
    print(json.dumps({'svm_classes': 61, 'top3_loaded': True, 'rag_vectors': 239,
                      'rag_dimension': 32708, 'frozen_hashes_verified': True}))


if __name__ == '__main__':
    main()
