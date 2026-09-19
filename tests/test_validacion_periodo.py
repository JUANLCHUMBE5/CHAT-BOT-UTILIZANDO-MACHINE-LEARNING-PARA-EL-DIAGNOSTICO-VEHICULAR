"""Regresiones del período, paginación SQL y fichas pre/post sin datos prefijados."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from src.application.services.validacion_taller import resumir_fases
from src.core.authorization import exigir_lectura_validacion
from src.infrastructure.database.repositories.validacion_taller_repository import ValidacionTallerRepository
from src.interfaces.api.v1.dtos.validacion import CrearCasoValidacionDTO
from src.interfaces.api.v1.endpoints import validacion_taller as endpoints


@pytest.fixture
def cliente(monkeypatch):
    # Lectura completamente aislada: sin PostgreSQL, CSV real ni modelos ML.
    app = FastAPI()
    app.include_router(endpoints.router, prefix="/validacion")
    app.dependency_overrides[exigir_lectura_validacion] = lambda: {"taller_id": "taller-a"}
    monkeypatch.setattr(endpoints, "database_configurada", lambda: False)
    filas = [{
        "item": n, "fase": "Pre-test" if n <= 12 else "Post-test", "fecha": "2026-09-04",
        "placa": "***-123", "placa_hash": "a" * 64, "marca_modelo": "Modelo",
        "sintoma": "Vibración", "falla_real": "Falla", "chatbot_prediccion": "Hipótesis",
        "campos_completos": n % 2, "prediccion_correcta": n % 2,
        "tiempo_diagnostico_minutos": 20 if n <= 12 else 30, "taller_id": "taller-a",
    } for n in range(1, 25)]
    filas += [{**filas[0], "item": 100, "taller_id": "taller-b"},
              {**filas[0], "item": 101, "fecha": "2026-08-01"}]
    monkeypatch.setattr(endpoints, "_cargar_df_tracker", lambda: pd.DataFrame(filas[::-1]))
    return TestClient(app)


def test_historial_diez_por_pagina_ascendente_y_aislado(cliente):
    filtro = "?fecha_desde=2026-09-04&fecha_hasta=2026-09-04"
    primera = cliente.get('/validacion' + filtro).json()
    segunda = cliente.get('/validacion' + filtro + '&skip=10').json()
    ultima = cliente.get('/validacion' + filtro + '&skip=20').json()
    assert primera['total'] == segunda['total'] == 24
    assert [c['item'] for c in primera['casos']] == list(range(1, 11))
    assert [c['item'] for c in segunda['casos']] == list(range(11, 21))
    assert [c['item'] for c in ultima['casos']] == list(range(21, 25))


def test_metricas_incluyen_todo_periodo_y_deterioros(cliente):
    r = cliente.get('/validacion/metricas?fecha_desde=2026-09-04&fecha_hasta=2026-09-04')
    assert r.status_code == 200
    m = r.json()
    assert m['casos_pretest'] == m['casos_posttest'] == 12
    assert m['registros_completos_posttest_porcentaje'] == 50
    assert m['reduccion_tiempo_porcentaje'] == -50


@pytest.mark.parametrize('ruta', ['', '/metricas', '/exportar-csv'])
def test_rango_invertido_rechazado(cliente, ruta):
    assert cliente.get('/validacion' + ruta + '?fecha_desde=2026-09-05&fecha_hasta=2026-09-01').status_code == 422


def test_exportacion_mismo_periodo_y_taller(cliente):
    r = cliente.get('/validacion/exportar-csv?fecha_desde=2026-09-04&fecha_hasta=2026-09-04')
    assert r.status_code == 200
    assert 'taller-b' not in r.text and '2026-08-01' not in r.text
    assert len(r.text.strip().splitlines()) == 25


def test_piloto_no_sustituye_pretest_ausente():
    m = resumir_fases([{'fase': 'Piloto', 'total': 3, 'aciertos': 3, 'completos': 3, 'minutos': 9}])
    assert m['casos_pretest'] == m['casos_posttest'] == 0
    assert m['reduccion_tiempo_porcentaje'] == 0


def test_sql_agrega_y_pagina_sin_cargar_todos_los_registros():
    async def comprobar():
        session = MagicMock()
        count, listado = MagicMock(), MagicMock()
        count.scalar_one.return_value = 21
        listado.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(side_effect=[count, listado])
        repo = ValidacionTallerRepository(session)
        taller = uuid.uuid4()
        total, _ = await repo.listar(taller, skip=10, fecha_desde=date(2026, 9, 1), fecha_hasta=date(2026, 9, 4))
        sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}))
        assert total == 21
        assert 'LIMIT 10 OFFSET 10' in sql
        assert 'fecha ASC' in sql and 'item ASC' in sql and 'id ASC' in sql
        assert str(taller) in sql and "2026-09-01" in sql and "2026-09-04" in sql
        agregado = MagicMock()
        agregado.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=agregado)
        await repo.resumen_por_fase(taller)
        sql = str(session.execute.call_args.args[0])
        assert 'GROUP BY' in sql and 'sum(' in sql and 'count(' in sql
    asyncio.run(comprobar())


def test_hipotesis_manual_y_completitud_explicita():
    datos = dict(fase='Pre-test', placa='ABC123', marca_modelo='Modelo', sintoma='Vibra al frenar',
                 falla_real='Disco', prediccion_inicial='Pastillas', tiempo_diagnostico_minutos=10,
                 prediccion_correcta=0)
    with pytest.raises(ValidationError):
        CrearCasoValidacionDTO(**datos)
    caso = CrearCasoValidacionDTO(**datos, campos_completos=0)
    assert caso.chatbot_prediccion == 'Pastillas'
