"""La recuperación conserva el índice y nunca sirve textos históricos retirados."""

import hashlib
import json
import shutil

import pytest

from src.config import settings
from src.infrastructure.motor_rag import MotorRAG
from src.infrastructure.rag_checks.canonical_loader import _ruta_segura
from src.infrastructure.rag_checks.frozen_integrity import FrozenRAGMismatch

BASE = settings.paths.manual_file.parent / "candidates" / "v1"


@pytest.fixture(scope="module")
def rag_verificado():
    return MotorRAG(rag_version="candidate_v1")


def test_paquete_original_carga_sin_cambiar_indice(rag_verificado):
    assert rag_verificado.faiss_index is not None
    assert rag_verificado.faiss_index.d == 32708
    assert rag_verificado.faiss_index.ntotal == len(rag_verificado.documentos) == 239
    assert hashlib.sha256((BASE / "indexes/indice_faiss_v1.index").read_bytes()).hexdigest() == (
        "729ca17ed63c7902a4d5eab8fd791409666ad7509e208572abeee36a2edc308f"
    )


def test_revision_map_segura_prevalece_sobre_snapshot_historico(rag_verificado):
    texto, _, _, meta = rag_verificado.recuperar_procedimiento_hibrido(
        "sensor MAP presión absoluta P0106", umbral=0.0,
    )
    assert meta["id_procedimiento"] == "RAG_PROC_116"
    assert "boschdiagnostics.com" in texto
    assert "no asumir pinout" in texto.lower()
    assert "pin 1: 5.0V" not in texto


def test_frenos_no_recupera_advertencia_common_rail_ajena(rag_verificado):
    texto, titulo, _, _ = rag_verificado.recuperar_procedimiento_hibrido(
        "pedal de frenos esponjoso purga líquido de frenos", umbral=0.0,
    )
    assert "freno" in titulo.lower()
    assert "common rail" not in texto.lower()


@pytest.mark.parametrize("tipo", ["texto", "indice", "orden"])
def test_paquete_manipulado_se_rechaza_sin_reconstruccion(tmp_path, monkeypatch, tipo):
    base = tmp_path / "candidates" / "v1"
    manifest = json.loads((BASE / "manifests/verified_frozen_bundle.json").read_text(encoding="utf-8"))
    paths = [*manifest["files"], "indexes/indice_faiss_v1.index", "manifests/verified_frozen_bundle.json"]
    for relative in paths:
        target = base / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASE / relative, target)
    if tipo == "texto":
        target = base / next(p for p in manifest["files"] if p.startswith("texts/"))
        target.write_text("Contenido alterado", encoding="utf-8")
    elif tipo == "indice":
        (base / "indexes/indice_faiss_v1.index").write_bytes(b"indice corrupto de prueba")
    else:
        manifest["entries"][0], manifest["entries"][1] = manifest["entries"][1], manifest["entries"][0]
        (base / "manifests/verified_frozen_bundle.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(
        MotorRAG, "_indexar_manuales_multimarca",
        lambda self: pytest.fail("No reconstruir ni cambiar a otro índice ante corrupción"),
    )
    motor = MotorRAG(manual_path=str(tmp_path), rag_version="candidate_v1")
    assert motor.faiss_index is None
    assert "INCOMPATIBLE" in motor.rag_version


def test_ruta_de_snapshot_no_puede_salir_del_paquete(tmp_path):
    with pytest.raises(FrozenRAGMismatch):
        _ruta_segura(tmp_path, "../../fuera-del-corpus")


@pytest.mark.parametrize("hipotesis,esperado", [
    ("Inyectores sucios o filtro de combustible obstruido", True),
    ("Termostato defectuoso", False),
    ("Falla en sensor ABS", False),
])
def test_procedimiento_transversal_no_reemplaza_hipotesis(hipotesis, esperado):
    from src.core.diagnostico.rag_hypothesis_compatibility import procedimiento_apoya_hipotesis

    assert procedimiento_apoya_hipotesis(
        hipotesis, "Diagnóstico de mezcla pobre y datos STFT LTFT",
        {"falla": "Falla en sensor de oxigeno o mezcla rica", "knowledge_type": "PROCEDURAL"},
    ) is esperado


def test_documento_no_validado_sigue_fuera_del_prompt_y_no_se_fabrica_validacion():
    from src.core.diagnostico.coherencia_evidencia import preparar_contexto_rag_para_llm

    meta = {"manual_oem": "Manual sintético de prueba", "estado_validacion": "corpus_preliminar_taller"}
    assert preparar_contexto_rag_para_llm("Procedimiento", "Título", meta, False)[0] == ""
    meta.update(estado_validacion="validado_oem", auditoria={
        "verificado_documental": True, "auditoria_mecanica_formal_firmada": True,
    })
    assert preparar_contexto_rag_para_llm("Procedimiento", "Título", meta, True) == (
        "Procedimiento", "Título",
    )
