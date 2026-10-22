from types import SimpleNamespace

import pytest

from src.config import PathConfig
from src.infrastructure.motor_rag import (
    MotorRAG,
    _candidato_trata_fuga_refrigerante,
    _validar_coherencia_vectorial,
)


def test_rag_experimental_no_es_la_version_predeterminada(monkeypatch):
    monkeypatch.delenv("CARBOT_RAG_VERSION", raising=False)

    assert PathConfig().rag_version == "baseline_f8_3"


def test_candidato_explicito_rechaza_vectorizador_incompatible():
    vectorizador = SimpleNamespace(vocabulary_={"alternador": 0, "bateria": 1})
    indice = SimpleNamespace(d=3, ntotal=1)

    with pytest.raises(ValueError, match="incompatibles"):
        _validar_coherencia_vectorial(vectorizador, indice, cantidad_documentos=1)


def test_candidato_explicito_rechaza_corpus_desalineado():
    vectorizador = SimpleNamespace(vocabulary_={"alternador": 0, "bateria": 1})
    indice = SimpleNamespace(d=2, ntotal=2)

    with pytest.raises(ValueError, match="misma cantidad"):
        _validar_coherencia_vectorial(vectorizador, indice, cantidad_documentos=1)


def test_filtro_rag_conserva_deteccion_de_documentos_sobre_fugas():
    fuga = {"metadatos": {"falla": "Fuga de refrigerante en radiador"}}
    freno = {"metadatos": {"falla": "Desgaste de pastillas de freno"}}

    assert _candidato_trata_fuga_refrigerante(fuga) is True
    assert _candidato_trata_fuga_refrigerante(freno) is False


def test_candidato_incompleto_no_activa_baseline_silenciosamente(tmp_path):
    motor = MotorRAG.__new__(MotorRAG)
    motor.manual_path = tmp_path / "manuales"

    with pytest.raises(FileNotFoundError, match="selección experimental explícita rechazada"):
        motor._cargar_candidato_v1()
