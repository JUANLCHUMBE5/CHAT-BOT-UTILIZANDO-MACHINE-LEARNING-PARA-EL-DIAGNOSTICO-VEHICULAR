"""Regresiones de compatibilidad temática previas a entregar contexto RAG."""

from src.core.diagnostico.coherencia_evidencia import documento_compatible
from src.core.diagnostico.enrutador_sistema import (
    detectar_areas_tecnicas,
    filtrar_candidatos_por_area,
)
from src.infrastructure.rag.relevance_filter import tiene_anclaje_lexico


def _candidato(titulo, documento):
    return {"titulo": titulo, "documento": documento, "metadatos": {}}


def test_cuerpo_aceleracion_descarta_frenos():
    areas = detectar_areas_tecnicas("reaprendizaje de marcha mínima del cuerpo de aceleración")
    candidatos = [
        _candidato("Purga de frenos", "pastillas, discos y líquido de frenos"),
        _candidato("Reaprendizaje", "calibrar cuerpo de aceleración y marcha mínima"),
    ]
    assert [c["titulo"] for c in filtrar_candidatos_por_area(candidatos, areas)] == ["Reaprendizaje"]


def test_caja_termostatica_no_se_confunde_con_caja_cambios():
    areas = detectar_areas_tecnicas("fuga por caja termostática y pérdida de refrigerante")
    candidatos = [
        _candidato("Caja de cambios", "aceite de transmisión y sincronizadores"),
        _candidato("Refrigeración", "caja termostática, termostato y refrigerante"),
    ]
    assert areas == ["REFRIGERACION"]
    assert [c["titulo"] for c in filtrar_candidatos_por_area(candidatos, areas)] == ["Refrigeración"]


def test_common_rail_y_gasolina_son_incompatibles():
    assert not documento_compatible(
        "motor 4JJ1 common rail diésel con baja presión",
        "Bomba de gasolina",
        "medición de bomba de gasolina y tanque",
    )
    assert not documento_compatible(
        "motor gasolina con baja presión",
        "Prueba Common Rail",
        "SCV, bomba diésel e inyectores common rail",
    )


def test_suspension_descarta_documento_motor():
    areas = detectar_areas_tecnicas("golpeteo de suspensión en baches y amortiguador con juego")
    candidatos = [
        _candidato("Motor", "compresión, pistones y válvulas del motor"),
        _candidato("Suspensión", "amortiguadores, rótulas y prueba en baches"),
    ]
    assert [c["titulo"] for c in filtrar_candidatos_por_area(candidatos, areas)] == ["Suspensión"]


def test_consulta_ambigua_no_inventa_area():
    assert detectar_areas_tecnicas("hace una cosa rara a veces") == []
    assert not tiene_anclaje_lexico(
        "hace una cosa rara a veces",
        _candidato("Purga de frenos", "pastillas y líquido de frenos"),
    )


def test_dos_averias_permiten_documentos_de_ambas_areas():
    areas = detectar_areas_tecnicas("pedal de freno esponjoso y amortiguador golpea en baches")
    candidatos = [
        _candidato("Frenos", "purga de frenos y pedal"),
        _candidato("Suspensión", "amortiguador y rótula"),
        _candidato("Motor", "compresión del motor"),
    ]
    assert {c["titulo"] for c in filtrar_candidatos_por_area(candidatos, areas)} == {"Frenos", "Suspensión"}


def test_negacion_de_frenado_no_desvia_vibracion_de_direccion():
    areas = detectar_areas_tecnicas("el volante vibra a 90 km/h; no vibra al frenar")
    candidatos = [
        _candidato("Frenos", "discos de freno alabeados"),
        _candidato("Dirección", "alineación, llantas y vibración del volante a velocidad"),
    ]
    filtrados = filtrar_candidatos_por_area(candidatos, areas)
    assert [c["titulo"] for c in filtrados] == ["Dirección"]
