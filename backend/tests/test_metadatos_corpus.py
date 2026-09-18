"""Pruebas automatizadas de integridad y consistencia del catálogo de metadatos RAG."""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
METADATOS_JSON = RAIZ / "machine_learning" / "manuals" / "metadatos_manuales.json"
MANUALS_DIR = RAIZ / "machine_learning" / "manuals"


def test_existencia_y_volumen_metadatos_manuales():
    assert METADATOS_JSON.exists(), f"No se encontró {METADATOS_JSON}"
    with open(METADATOS_JSON, "r", encoding="utf-8") as f:
        datos = json.load(f)

    assert isinstance(datos, list)
    assert len(datos) >= 60, f"Se esperaban al menos 60 procedimientos con metadatos, hay {len(datos)}"


def test_campos_obligatorios_en_cada_metadato():
    with open(METADATOS_JSON, "r", encoding="utf-8") as f:
        datos = json.load(f)

    campos_requeridos = {
        "id_procedimiento",
        "titulo",
        "marca",
        "modelo",
        "manual_oem",
        "pagina",
        "codigos_dtc",
        "archivo_fuente",
        "sha256_fragmento",
        "estado_validacion",
        "auditoria",
    }

    for item in datos:
        proc_id = item.get("id_procedimiento")
        assert proc_id, "id_procedimiento no puede ser vacío"
        faltantes = campos_requeridos - set(item.keys())
        assert not faltantes, f"Procedimiento {proc_id} carece de campos obligatorios: {faltantes}"
        assert len(item["sha256_fragmento"]) == 64, f"Hash SHA-256 inválido en {proc_id}"
        assert (MANUALS_DIR / item["archivo_fuente"]).exists(), f"Archivo fuente no existe: {item['archivo_fuente']}"


def test_integridad_hashes_sha256_muestra_corpus():
    with open(METADATOS_JSON, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # Validar que los hashes sean hexadecimales de 64 caracteres válidos
    for item in datos:
        h = item["sha256_fragmento"]
        assert int(h, 16) >= 0, f"Hash no hexadecimal en {item['id_procedimiento']}"


def test_rag_operativo_excluye_fuentes_secundarias_y_fragmentos_sin_catalogar():
    from src.config import settings
    from src.infrastructure.motor_rag import MotorRAG

    motor = MotorRAG(settings.paths.manual_file)

    assert len(motor.documentos) == len(motor.metadatos_procedimientos) >= 180
    assert all(
        item["estado_validacion"] == "corpus_preliminar_taller"
        for item in motor.metadatos_procedimientos
    )
    assert not any("GemaCar" in item.get("manual_oem", "") for item in motor.metadatos_procedimientos)


def test_vibracion_en_neutro_recupera_procedimiento_tecnico_no_guia_web():
    from src.config import settings
    from src.infrastructure.motor_rag import MotorRAG

    motor = MotorRAG(settings.paths.manual_file)
    _, titulo, _, metadatos = motor.recuperar_procedimiento_con_metadatos(
        "el motor vibra en neutro y golpea al acelerar; revisar soportes de motor",
        umbral=0.0,
    )

    assert "SOPORTES DE MOTOR" in titulo.upper()
    assert metadatos["estado_validacion"] == "corpus_preliminar_taller"
