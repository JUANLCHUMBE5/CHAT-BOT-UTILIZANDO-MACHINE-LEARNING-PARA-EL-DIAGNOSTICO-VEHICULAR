from __future__ import annotations

import csv
from pathlib import Path

import pytest
from training.preparar_candidatos_gemacar import generar_derivados, preparar, verificar_fuente

from src.infrastructure.motor_rag import MotorRAG


def test_dataset_gemacar_se_genera_como_candidatos_multicausa(tmp_path):
    salida = tmp_path / "candidatos.csv"
    reporte = tmp_path / "reporte.json"
    taxonomia = Path(__file__).resolve().parents[2] / "machine_learning/data/dataset_sintomas_limpio.csv"

    resumen = preparar(salida, reporte, taxonomia)

    with salida.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))

    assert resumen["registros"] == 149
    assert len(filas) == 149
    assert len({fila["id_candidato"] for fila in filas}) == len(filas)
    assert {fila["apto_entrenamiento"] for fila in filas} == {"NO"}
    assert {fila["validado_por_mecanico"] for fila in filas} == {"NO"}
    assert any(fila["estado_mapeo"] == "MAPEO_PROPUESTO" for fila in filas)
    assert any(fila["estado_mapeo"] == "DESCARTAR_NO_FALLA" for fila in filas)

    entrenamiento = tmp_path / "entrenamiento.csv"
    rag = tmp_path / "rag.txt"
    derivados = generar_derivados(salida, entrenamiento, rag)
    with entrenamiento.open(encoding="utf-8-sig", newline="") as archivo:
        filas_entrenamiento = list(csv.DictReader(archivo))

    assert derivados == {
        "registros_ml_experimentales": 5,
        "secciones_rag_secundarias": 26,
    }
    assert len(filas_entrenamiento) == 5
    assert rag.read_text(encoding="utf-8").count("=== ORIENTACION SECUNDARIA") == 26
    assert "no confirmar una pieza" in rag.read_text(encoding="utf-8").lower()


def test_fuente_gemacar_rechaza_un_texto_distinto(tmp_path):
    fuente = tmp_path / "fuente.txt"
    fuente.write_text("contenido alterado", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256 inesperado"):
        verificar_fuente(fuente, "fallas_comunes")


def test_rag_indexa_gemacar_como_fuente_secundaria_no_validada():
    motor = MotorRAG()

    _, titulo, similitud, metadatos = motor.recuperar_procedimiento_con_metadatos(
        "el auto vibra al frenar", umbral=0.25
    )

    assert titulo == "ORIENTACION SECUNDARIA NO VALIDADA: VIBRACION AL FRENAR"
    assert similitud >= 0.25
    assert metadatos["estado_validacion"] == "fuente_secundaria_no_validada"
    assert metadatos["auditoria"]["verificado_documental"] is False
