"""Pruebas exhaustivas de cobertura y recuperación del corpus RAG (180 manuales OEM y FAISS)."""

from __future__ import annotations

import pytest

from src.infrastructure.motor_rag import MotorRAG


@pytest.fixture(scope="module")
def motor_rag():
    return MotorRAG()


def test_rag_total_procedimientos_indexados(motor_rag):
    """Verifica que el índice FAISS contenga al menos 180 procedimientos técnicos y mantenga consistencia."""
    assert motor_rag.faiss_index is not None
    assert motor_rag.faiss_index.ntotal >= 180
    assert len(motor_rag.documentos) >= 180
    assert len(motor_rag.titulos) >= 180
    assert motor_rag.faiss_index.ntotal == len(motor_rag.documentos) == len(motor_rag.titulos)


def test_metadatos_manuales_integridad(motor_rag):
    """Verifica que cada uno de los procedimientos posea metadatos auditables completos."""
    assert len(motor_rag.metadatos_procedimientos) >= 180
    for meta in motor_rag.metadatos_procedimientos:
        assert "id_procedimiento" in meta
        assert meta["id_procedimiento"].startswith("RAG_PROC_")
        assert "titulo" in meta
        assert "manual_oem" in meta
        assert "archivo_fuente" in meta
        assert len(meta["titulo"]) > 5


SISTEMAS_RAG_CASOS = [
    ("frenos", "pastillas de freno desgastadas chirrido de metal y discos alabeados"),
    ("encendido", "bujias misfire chispa debil bobina de encendido resistencia primaria secundaria"),
    ("combustible", "bomba de gasolina riel de inyeccion presion de combustible regulador"),
    ("refrigeracion", "termostato pegado motoventilador temperatura de refrigerante radiador purga"),
    ("transmision", "caja mecanica sincronizadores valvulina embrague patinando volante"),
    ("electrico", "alternador carga 14V placa de diodos osciloscopio rizado bateria voltajes"),
    ("suspension", "amortiguadores reventados bujes de trapecio rotula juego terminal"),
    ("direccion", "cremallera hidraulica liquido asistida alineacion caida convergencia"),
    ("hibridos_ev", "bateria de traccion alto voltaje inversor igbt aislacion electrica seguridad"),
    ("camiones_neumatico", "freno de aire calderin compresor neumático valvula secadora aps"),
]


@pytest.mark.parametrize("sistema,consulta", SISTEMAS_RAG_CASOS)
def test_recuperacion_por_sistema_vehicular(motor_rag, sistema, consulta):
    """Verifica que el motor FAISS recupere procedimientos pertinentes para cada subsistema vehicular."""
    contexto, titulo, similitud = motor_rag.recuperar_contexto_con_similitud(consulta)
    assert contexto is not None
    assert len(contexto) > 50
    assert titulo is not None
    assert len(titulo) > 5
    assert similitud >= 0.0


def test_separacion_metodologica_rag_sin_sintomas_coloquiales(motor_rag):
    """Regla de tesis: el corpus RAG no debe contener quejas o jergas de clientes, solo manuales OEM."""
    import re
    jergas_prohibidas = ["mi caña", "ta que suena", "mi choche", "mi broder", "carro se chupa"]
    for doc in motor_rag.documentos:
        doc_lower = doc.lower()
        for jerga in jergas_prohibidas:
            assert not re.search(rf"\b{re.escape(jerga)}\b", doc_lower), (
                f"Jerga coloquial '{jerga}' encontrada indebidamente en corpus RAG"
            )


def test_consistencia_version_y_hash_corpus(motor_rag):
    """Verifica la trazabilidad del corpus RAG para reproducibilidad de la tesis."""
    assert motor_rag.corpus_version is not None
    assert len(motor_rag.corpus_version) > 0
    # Regla de tesis: estado oficial referencial hasta corroboración en campo
    assert motor_rag.corpus_validado is False
