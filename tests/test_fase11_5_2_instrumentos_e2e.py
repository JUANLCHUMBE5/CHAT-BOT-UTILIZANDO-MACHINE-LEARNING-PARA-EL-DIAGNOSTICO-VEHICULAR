"""Fase 11.5.2: validacion E2E de instrumentos de tesis sin contaminar muestra oficial."""

from __future__ import annotations

import asyncio
import csv
import io
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.validacion_taller import (
    ServicioValidacionTaller,
    calcular_detalles_campos_ficha2,
    construir_datos_generales_vehiculo,
    resumir_fases,
)
from src.config import settings
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.catalogs import Taller
from src.interfaces.api.v1.dtos.validacion import CrearCasoValidacionDTO
from src.interfaces.api.v1.endpoints.validacion_taller import _sanitizar_campo_csv


def _datos_vehiculo(**overrides):
    datos = {
        "marca_modelo": "Toyota Yaris",
        "anio": 2020,
        "kilometraje": 85000,
        "combustible": "Gasolina",
        "transmision": "Automatica",
    }
    datos.update(overrides)
    return construir_datos_generales_vehiculo(**datos)


def _campos_base(**overrides):
    campos = {
        "codigo_registro": "PRE-SIM-001",
        "fecha_atencion": "2026-09-19",
        "datos_generales_vehiculo": _datos_vehiculo(),
        "sintomas_reportados": "Vibracion al frenar",
        "descripcion_sintoma": "El volante vibra solo cuando pisa el freno a velocidad media.",
        "sistema_afectado_probable": "FRENOS",
        "diagnostico_confirmado": "Discos de freno alabeados",
        "tiempo_atencion_minutos": 20,
    }
    campos.update(overrides)
    return campos


def test_ficha2_trazabilidad_8_7_1_0_campos():
    casos = [
        (_campos_base(), 8, 1, None),
        (_campos_base(sistema_afectado_probable=""), 7, 0, "campo_6"),
        ({**{k: "" for k in _campos_base()}, "codigo_registro": "PRE-SIM-002"}, 1, 0, "campo_1"),
        ({k: "" for k in _campos_base()}, 0, 0, "campo_1"),
    ]
    for entrada, cantidad_esperada, completo_esperado, campo_a_revisar in casos:
        completo, cantidad, detalles = calcular_detalles_campos_ficha2(**entrada)
        assert cantidad == cantidad_esperada
        assert completo == completo_esperado
        assert set(detalles) == {f"campo_{i}" for i in range(1, 9)}
        if campo_a_revisar:
            assert detalles[campo_a_revisar]["completo"] is (cantidad_esperada == 1 and campo_a_revisar == "campo_1")


def test_ficha2_no_duplica_sintoma_como_descripcion():
    completo, cantidad, detalles = calcular_detalles_campos_ficha2(
        **_campos_base(descripcion_sintoma="")
    )
    assert cantidad == 7
    assert completo == 0
    assert detalles["campo_4"]["completo"] is True
    assert detalles["campo_5"]["completo"] is False


def test_datos_generales_vehiculo_exige_subcampos_del_anexo2():
    completo, cantidad, detalles = calcular_detalles_campos_ficha2(
        **_campos_base(datos_generales_vehiculo=_datos_vehiculo(anio=None))
    )
    assert cantidad == 7
    assert completo == 0
    assert detalles["campo_3"]["completo"] is False
    assert "anio=" in detalles["campo_3"]["valor_resumen"]


def test_ppcf_rdc_tprd_pre_post_y_zero_division():
    resumen = resumir_fases(
        [
            {"fase": "Pre-test", "total": 4, "aciertos": 2, "completos": 2, "minutos": 140},
            {"fase": "Post-test", "total": 4, "aciertos": 3, "completos": 3, "minutos": 60},
        ]
    )
    assert resumen["tasa_acierto_pretest_porcentaje"] == 50.0
    assert resumen["tasa_acierto_posttest_porcentaje"] == 75.0
    assert resumen["registros_completos_pretest_porcentaje"] == 50.0
    assert resumen["registros_completos_posttest_porcentaje"] == 75.0
    assert resumen["tiempo_promedio_pretest_min"] == 35.0
    assert resumen["tiempo_promedio_posttest_min"] == 15.0

    vacio = resumir_fases([])
    assert vacio["tasa_acierto_global_porcentaje"] == 0.0
    assert vacio["tiempo_promedio_pretest_min"] == 0.0


def test_persistencia_e2e_development_y_exclusion_oficial():
    asyncio.run(_persistencia_e2e_development_y_exclusion_oficial())


async def _persistencia_e2e_development_y_exclusion_oficial():
    settings.database.enabled = True
    engine = obtener_engine()
    taller_id = uuid.uuid4()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        trans = await session.begin()
        try:
            schema_probe = (
                await session.execute(
                    text(
                        """
                        select current_database() as db, inet_server_port() as port,
                               to_regclass('validaciones_taller')::text as tabla,
                               exists (
                                   select 1 from information_schema.columns
                                   where table_schema = 'public'
                                     and table_name = 'validaciones_taller'
                                     and column_name = 'descripcion_sintoma'
                               ) as tiene_descripcion
                        """
                    )
                )
            ).mappings().one()
            assert schema_probe["tiene_descripcion"], dict(schema_probe)
            session.add(Taller(id=taller_id, nombre="Taller Fase 11.5.2"))
            await session.flush()
            servicio = ServicioValidacionTaller(session)
            dto = CrearCasoValidacionDTO(
                fase="Pre-test",
                fecha="2026-09-19",
                placa="SIM001",
                marca_modelo="Toyota Yaris",
                descripcion_sintoma="Vibra el volante solamente al frenar.",
                vehiculo_anio=2020,
                vehiculo_kilometraje=85000,
                vehiculo_combustible="Gasolina",
                vehiculo_transmision="Automatica",
                sintoma="Vibracion al frenar",
                falla_real="Discos de freno alabeados",
                chatbot_prediccion="Discos de freno alabeados",
                sistema_afectado_probable="FRENOS",
                campos_completos=0,
                tiempo_diagnostico_minutos=20,
                prediccion_correcta=1,
                estado_registro="verificado",
                tipo_registro="DEVELOPMENT",
                metodo_confirmacion="Inspeccion fisica",
                evidencia_ref="PRE-SIM-001",
            )
            caso = await servicio.crear(taller_id, None, dto, "SIM-***", "a" * 64)
            await session.flush()

            row = (
                await session.execute(
                    text(
                        """
                        select descripcion_sintoma, vehiculo_anio, vehiculo_kilometraje,
                               vehiculo_combustible, vehiculo_transmision,
                               sistema_afectado_probable, cantidad_campos_completos,
                               campos_completos, tipo_registro
                        from validaciones_taller
                        where id = :id
                        """
                    ),
                    {"id": caso.id},
                )
            ).mappings().one()
            assert row["descripcion_sintoma"] == dto.descripcion_sintoma
            assert row["vehiculo_anio"] == 2020
            assert row["vehiculo_kilometraje"] == 85000
            assert row["vehiculo_combustible"] == "Gasolina"
            assert row["vehiculo_transmision"] == "Automatica"
            assert row["sistema_afectado_probable"] == "FRENOS"
            assert row["cantidad_campos_completos"] == 8
            assert row["campos_completos"] == 1
            assert row["tipo_registro"] == "DEVELOPMENT"

            listado = await servicio.listar(taller_id, tipo_registro="DEVELOPMENT")
            recuperado = listado["casos"][0]
            assert recuperado["descripcion_sintoma"] == dto.descripcion_sintoma
            assert recuperado["cantidad_campos_completos"] == 8

            metricas = await servicio.metricas(taller_id)
            assert metricas["total_casos"] == 0
            assert metricas["casos_pretest"] == 0
            assert metricas["registros_completos_pretest_porcentaje"] == 0.0
        finally:
            await trans.rollback()
            await engine.dispose()


def test_csv_reconstruye_indicadores_y_sanitiza_formulas():
    registros = [
        {"fase": "Pre-test", "prediccion_correcta": 1, "campos_completos": 1, "tiempo_diagnostico_minutos": 20},
        {"fase": "Pre-test", "prediccion_correcta": 0, "campos_completos": 0, "tiempo_diagnostico_minutos": 30},
        {"fase": "Post-test", "prediccion_correcta": 1, "campos_completos": 1, "tiempo_diagnostico_minutos": 10},
        {"fase": "Post-test", "prediccion_correcta": 1, "campos_completos": 1, "tiempo_diagnostico_minutos": 20},
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(registros[0].keys()))
    writer.writeheader()
    writer.writerows(registros)
    output.seek(0)
    leidos = list(csv.DictReader(output))
    grupos = []
    for fase in ("Pre-test", "Post-test"):
        subset = [r for r in leidos if r["fase"] == fase]
        grupos.append(
            {
                "fase": fase,
                "total": len(subset),
                "aciertos": sum(int(r["prediccion_correcta"]) for r in subset),
                "completos": sum(int(r["campos_completos"]) for r in subset),
                "minutos": sum(int(r["tiempo_diagnostico_minutos"]) for r in subset),
            }
        )
    resumen = resumir_fases(grupos)
    assert resumen["tasa_acierto_pretest_porcentaje"] == 50.0
    assert resumen["registros_completos_posttest_porcentaje"] == 100.0
    assert resumen["tiempo_promedio_posttest_min"] == 15.0
    assert _sanitizar_campo_csv("=cmd|' /C calc'!A0").startswith("'=")
    assert _sanitizar_campo_csv("+SUM(A1:A2)").startswith("'+")
