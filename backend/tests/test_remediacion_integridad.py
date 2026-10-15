"""Contratos de integridad y evaluación sin resultados clínicos fabricados."""
from pathlib import Path

from src.core.evaluacion_referencias import auditar_referencias, etiqueta_exacta
from src.infrastructure.integridad_artefactos import verificar_manifest


def test_substring_no_es_acierto_clinico():
    assert not etiqueta_exacta("Falla de bobina", "bobina")
    assert etiqueta_exacta("C1_01", "C1_01")


def test_banco_sin_evidencia_no_produce_precision():
    filas = [{"sintoma": "ejemplo sintético", "falla": "bobina"}] * 32
    r = auditar_referencias(filas, ["Falla de bobina"])
    assert r["denominador_original"] == 32
    assert r["filas_con_limitaciones"] == 32
    assert r["precision_clinica"] is None


def test_manifest_canonico_sin_reescrituras():
    root = Path("/app") if Path("/app").exists() else Path(__file__).resolve().parents[2]
    manifest = Path(__file__).parent / "fixtures/ml_42d607_integridad.json"
    resultado = verificar_manifest(root, manifest)
    assert len(resultado) == 8
    assert all(resultado.values()), resultado


def test_desajuste_no_se_oculta(tmp_path):
    import hashlib
    import json

    artifact = tmp_path / "index.bin"
    artifact.write_bytes(b"frozen")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"artifacts": {"index.bin": hashlib.sha256(b"other").hexdigest()}}))
    before = artifact.read_bytes()
    assert verificar_manifest(tmp_path, manifest) == {"index.bin": False}
    assert artifact.read_bytes() == before
