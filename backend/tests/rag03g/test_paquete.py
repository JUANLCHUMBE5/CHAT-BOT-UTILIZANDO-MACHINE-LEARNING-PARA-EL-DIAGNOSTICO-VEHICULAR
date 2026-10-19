"""Integridad: corrupción en copias, sin escribir modelos ni corpus originales."""

import copy
from pathlib import Path

import pytest

from src.infrastructure.rag.paquete_experimental import cargar_paquete, validar_vectores, verificar_manifiesto

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = "machine_learning/rag/experimentos/rag03c/manifiesto_rag03g.json"


@pytest.fixture(scope="module")
def package():
    return cargar_paquete(ROOT)


def test_verificar_256_vectores(package):
    corpus, vec, index, manifest = package
    ok, errors, reason = validar_vectores(corpus, vec, index, manifest, ROOT)
    assert ok and not errors and ("máximo 0.0" in reason or "error máximo" in reason)
    assert len(corpus) == index.ntotal == 256 and index.d == 35240


@pytest.mark.parametrize(
    "campo,valor",
    [("schema", "old"), ("version", "RAG-03F"), ("dimension", 35181), ("corpus_validado", True)],
)
def test_manifiesto_incompatible(package, campo, valor):
    corpus, vec, index, manifest = package
    manifest = copy.deepcopy(manifest)
    manifest[campo] = valor
    assert not validar_vectores(corpus, vec, index, manifest, ROOT)[0]


def test_hash_manipulado_no_se_ignora(package):
    *_, manifest = package
    m = copy.deepcopy(manifest)
    m["archivos"][m["roles"]["corpus"]]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Hash"):
        verificar_manifiesto(m, ROOT)
