"""
Cálculo de Hashes Criptográficos SHA-256 para Congelamiento Final de CarBot (Iteración 8.3).
Congela absolutamente todos los componentes del sistema antes de las etapas D y E.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def calcular_sha256(ruta_archivo: Path) -> str:
    h = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    archivos_congelados = {
        "dataset_train": BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv",
        "benchmark_dev_60": BASE_DIR / "machine_learning" / "data" / "benchmark_dev_60_casos.py",
        "modelo_diagnostico_falla_prod": BASE_DIR / "machine_learning" / "models" / "modelo_diagnostico.pkl",
        "modelo_sistema_prod": BASE_DIR / "machine_learning" / "models" / "modelo_sistema.pkl",
        "vectorizador_tfidf_prod": BASE_DIR / "machine_learning" / "models" / "vectorizador_tfidf.pkl",
        "modelo_diagnostico_candidata": BASE_DIR / "machine_learning" / "models" / "fase8_candidata" / "modelo_diagnostico.pkl",
        "modelo_sistema_candidata": BASE_DIR / "machine_learning" / "models" / "fase8_candidata" / "modelo_sistema.pkl",
        "vectorizador_tfidf_candidata": BASE_DIR / "machine_learning" / "models" / "fase8_candidata" / "vectorizador_tfidf.pkl",
        "corpus_metadatos_rag": BASE_DIR / "machine_learning" / "manuals" / "metadatos_manuales.json",
        "indice_faiss": BASE_DIR / "machine_learning" / "manuals" / "indice_faiss.index",
        "adaptador_modelo_ml": BASE_DIR / "backend" / "src" / "infrastructure" / "modelo_ml.py",
        "motor_rag": BASE_DIR / "backend" / "src" / "infrastructure" / "motor_rag.py",
        "rag_relevance_filter": BASE_DIR / "backend" / "src" / "infrastructure" / "rag" / "relevance_filter.py",
        "auto_interrogador": BASE_DIR / "backend" / "src" / "core" / "diagnostico" / "auto_interrogador.py",
        "politica_fusion": BASE_DIR / "backend" / "src" / "core" / "diagnostico" / "politica_fusion.py",
        "prompt_builder": BASE_DIR / "backend" / "src" / "core" / "diagnostico" / "prompt_builder.py",
        "text_processor": BASE_DIR / "backend" / "src" / "core" / "diagnostico" / "text_processor.py",
        "taxonomia_sistemas": BASE_DIR / "backend" / "src" / "core" / "diagnostico" / "taxonomia_sistemas.py",
        "gestor_diagnostico": BASE_DIR / "backend" / "src" / "core" / "gestor_diagnostico.py",
    }

    reporte = {
        "version": "8.3-FINAL-FROZEN",
        "fecha_congelamiento": datetime.now().isoformat(),
        "estado": "CONGELADO_INMUTABLE",
        "hashes_sha256": {},
    }

    print("=" * 100)
    print("REPORTE OFICIAL DE CONGELAMIENTO CRIPTOGRÁFICO SHA-256 — CARBOT 8.3")
    print("=" * 100)

    for nombre, ruta in archivos_congelados.items():
        if not ruta.exists():
            print(f"[ERROR] Archivo no encontrado: {ruta}")
            sys.exit(1)
        sha = calcular_sha256(ruta)
        rel = ruta.relative_to(BASE_DIR)
        reporte["hashes_sha256"][nombre] = {
            "archivo": str(rel).replace("\\", "/"),
            "sha256": sha,
            "tamano_bytes": ruta.stat().st_size,
        }
        print(f"{nombre:<32} | {sha} | {rel}")

    print("=" * 100)

    salida_json = BASE_DIR / "machine_learning" / "models" / "reporte_fase8_3_congelado.json"
    salida_json.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Reporte de congelamiento guardado exitosamente en:\n{salida_json}")

if __name__ == "__main__":
    main()
