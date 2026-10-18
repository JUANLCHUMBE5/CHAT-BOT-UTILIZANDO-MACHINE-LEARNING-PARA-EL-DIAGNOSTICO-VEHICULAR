"""Integridad: corrupción en copias, sin escribir modelos ni corpus originales."""

import copy
import shutil
from pathlib import Path

import pytest

from src.infrastructure.motor_rag import MotorRAG
from src.infrastructure.rag.paquete_experimental import cargar_paquete, validar_vectores, verificar_manifiesto

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = "machine_learning/rag/experimentos/rag03c/manifiesto_rag03g.json"


@pytest.fixture(scope="module")
def package():
    return cargar_paquete(ROOT)


def test_verificar_256_vectores(package):
    corpus, vec, index, manifest = package
    ok, errors, reason = validar_vectores(corpus, vec, index, manifest, ROOT)
    assert ok and not errors and "máximo 0.0" in reason
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


@pytest.mark.parametrize("modo", ["orden", "metadata", "texto"])
def test_modificacion_en_memoria_se_rechaza(package, modo):
    corpus, vec, index, manifest = package
    c = copy.deepcopy(corpus)
    if modo == "orden":
        c[0], c[1] = c[1], c[0]
    elif modo == "metadata":
        c[-1]["pagina"] = 999
    else:
        c[0]["texto"] += " adulterado"
    assert not validar_vectores(c, vec, index, manifest, ROOT)[0]


def test_paquete_incompleto_no_tiene_fallback(tmp_path):
    path = tmp_path / MANIFEST
    path.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / MANIFEST, path)
    with pytest.raises(ValueError, match="ausente"):
        cargar_paquete(tmp_path)


def test_selector_explicito_y_desconocido():
    with pytest.raises(ValueError, match="no soportado"):
        MotorRAG(rag_version="rag_version_inventada")
    rag = MotorRAG(rag_version="rag03g")
    assert not rag.corpus_validado and rag.faiss_index.ntotal == 256
