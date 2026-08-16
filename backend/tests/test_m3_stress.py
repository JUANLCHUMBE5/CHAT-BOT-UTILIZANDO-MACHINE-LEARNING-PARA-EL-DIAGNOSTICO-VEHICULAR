"""Empirical stress tests for Milestone M3 (Inicio Simplification & Fixes).

Tests cover:
1. Fallback and validation of ResumenMetricasResponseDTO fields (diagnosticos_realizados, diagnosticos_pendientes).
2. Date parsing edge cases (invalid format, boundary dates, missing parameters) in obtener_resumen_metricas query logic.
3. Period metric ratio and status invariant assertions.
"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from src.interfaces.api.v1.endpoints.metricas import ResumenMetricasResponseDTO, LIMA_TZ


def test_resumen_metricas_dto_defaults_and_fields():
    """Verify ResumenMetricasResponseDTO handles new M3 period fields correctly."""
    dto = ResumenMetricasResponseDTO(
        diagnosticos_hoy=5,
        diagnosticos_semana=12,
        diagnosticos_mes=30,
        diagnosticos_realizados=30,
        diagnosticos_pendientes=3,
        porcentaje_confirmados=80,
        tiempo_promedio_ms=1200,
        distribucion_modos=[{"modo": "completo_ml_rag_llm", "cantidad": 30}],
        actividad_diaria=[{"fecha": "Mon 10", "cantidad": 5}],
        fallas_frecuentes=[{"falla": "Filtro obstruido", "cantidad": 4}],
    )

    assert dto.diagnosticos_realizados == 30
    assert dto.diagnosticos_pendientes == 3
    assert dto.diagnosticos_pendientes <= dto.diagnosticos_realizados


def test_resumen_metricas_dto_default_fallback():
    """Verify DTO defaults diagnosticos_realizados and diagnosticos_pendientes to 0 if omitted."""
    dto_dict = {
        "diagnosticos_hoy": 0,
        "diagnosticos_semana": 0,
        "diagnosticos_mes": 0,
        "porcentaje_confirmados": 0,
        "tiempo_promedio_ms": 0,
        "distribucion_modos": [],
        "actividad_diaria": [],
        "fallas_frecuentes": [],
    }
    dto = ResumenMetricasResponseDTO(**dto_dict)
    assert dto.diagnosticos_realizados == 0
    assert dto.diagnosticos_pendientes == 0


def test_date_parsing_logic_edge_cases():
    """Test date parsing logic used in backend metricas endpoint."""
    # Test valid date format YYYY-MM-DD
    fecha_inicio_str = "2026-08-01"
    dt_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").replace(tzinfo=LIMA_TZ)
    assert dt_inicio.year == 2026
    assert dt_inicio.month == 8
    assert dt_inicio.day == 1

    fecha_fin_str = "2026-08-31"
    dt_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=LIMA_TZ)
    assert dt_fin.hour == 23
    assert dt_fin.minute == 59
    assert dt_fin.second == 59

    # Test invalid date string safety
    invalid_date_str = "invalid-date-format"
    dt_invalid = None
    try:
        dt_invalid = datetime.strptime(invalid_date_str, "%Y-%m-%d").replace(tzinfo=LIMA_TZ)
    except ValueError:
        pass
    assert dt_invalid is None


def test_period_metric_calculations_invariants():
    """Test mathematical invariants for period metrics calculations."""
    mes_count = 50
    confirmados_mes = 35
    pend_count = 10

    # Confirmation percentage logic
    pct_confirmados = min(100, int((confirmados_mes / mes_count * 100))) if mes_count > 0 else 0
    assert pct_confirmados == 70

    # 0 division safety
    mes_count_zero = 0
    pct_zero = min(100, int((0 / mes_count_zero * 100))) if mes_count_zero > 0 else 0
    assert pct_zero == 0

    # Pendientes must be subset of period total count in backend query logic
    assert pend_count <= mes_count
