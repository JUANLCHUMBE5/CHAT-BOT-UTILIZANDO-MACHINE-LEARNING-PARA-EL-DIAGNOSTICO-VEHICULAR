"""Pruebas de tolerancias metrológicas, eléctricas y procedimientos OEM en el corpus RAG (FAISS)."""

from __future__ import annotations

import pytest

from src.infrastructure.motor_rag import MotorRAG


@pytest.fixture(scope="module")
def motor_rag():
    return MotorRAG()


def test_rag_recupera_tolerancia_carga_alternador(motor_rag):
    """El procedimiento de carga de alternador debe contener tolerancias 13.8V - 14.4V o 13.5V."""
    doc, titulo, sim = motor_rag.recuperar_contexto_con_similitud(
        "alternador no carga testigo bateria encendido regulador diodos"
    )
    assert sim > 0.10, f"Similitud muy baja ({sim}) para alternador"
    doc_l = doc.lower()
    assert (
        "13.8" in doc_l or "14.4" in doc_l or "13.5" in doc_l or "14.5" in doc_l or "volt" in doc_l
    ), "No se encontró tolerancia de voltaje para alternador en el manual"


def test_rag_recupera_tolerancia_alabeo_discos(motor_rag):
    """El procedimiento de discos debe contener reloj comparador y tolerancia milimétrica (0.05 mm)."""
    doc, titulo, sim = motor_rag.recuperar_contexto_con_similitud(
        "discos de freno alabeados pedal vibra rectificado"
    )
    assert sim > 0.10, f"Similitud muy baja ({sim}) para discos alabeados"
    doc_l = doc.lower()
    assert "reloj comparador" in doc_l or "0.05" in doc_l or "alabeo" in doc_l or "micrómetro" in doc_l


def test_rag_recupera_tolerancia_bateria_y_arrancador(motor_rag):
    """El procedimiento de arranque/batería debe especificar voltaje o caída de tensión."""
    doc, titulo, sim = motor_rag.recuperar_contexto_con_similitud(
        "bateria descargada motor de arranque solenoide borne sulfatado"
    )
    assert sim > 0.10
    doc_l = doc.lower()
    assert "volt" in doc_l or "12" in doc_l or "cca" in doc_l or "caída" in doc_l or "caida" in doc_l


def test_rag_recupera_presion_riel_o_bomba_combustible(motor_rag):
    """El procedimiento de combustible debe mencionar presión de riel, psi o bar."""
    doc, titulo, sim = motor_rag.recuperar_contexto_con_similitud(
        "bomba de gasolina baja presion riel inyectores manometro"
    )
    assert sim > 0.10
    doc_l = doc.lower()
    assert "psi" in doc_l or "bar" in doc_l or "presión" in doc_l or "presion" in doc_l or "bomba" in doc_l


def test_rag_rechaza_consultas_completamente_ajenas(motor_rag):
    """Consultas sin relación automotriz deben tener coincidencia baja."""
    doc, titulo, sim = motor_rag.recuperar_contexto_con_similitud(
        "receta de tallarines rojos con pollo y ensalada rusa"
    )
    assert titulo == "Coincidencia baja" or sim < 0.12
    assert "no se encontro un procedimiento" in doc.lower() or "coincidencia baja" in titulo.lower()


def test_rag_metadatos_procedimiento_contiene_campos_clave(motor_rag):
    """`recuperar_procedimiento_con_metadatos` debe entregar metadatos estructurados."""
    doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_con_metadatos(
        "bujias bobinas encendido misfire p0301"
    )
    assert sim > 0.10
    assert isinstance(meta, dict)
    assert len(meta) > 0, "Los metadatos del procedimiento no deben estar vacíos"
