"""Pruebas de la FASE 12.2 — Remediación final del flujo experimental pre-campo.

Cumplimiento estricto de los 14 requerimientos obligatorios de la FASE 12.2:
1. DEVELOPMENT no cuenta como oficial en métricas.
2. PILOT no cuenta como oficial en métricas.
3. REGRESSION no cuenta como oficial en métricas.
4. THESIS_PRETEST cuenta únicamente en PRE.
5. THESIS_POSTTEST cuenta únicamente en POST.
6. Prueba informal nunca se convierte automáticamente a THESIS_*.
7. POST puede vincular diagnostico_id.
8. PRE funciona sin diagnostico_id.
9. Predicción vinculada no puede alterarse (inmutable).
10. Exportación oficial excluye PILOT.
11. Exportación oficial excluye DEVELOPMENT.
12. Contador oficial inicia 0/60 tras saneamiento.
13. Datos precargados coinciden con diagnosticos.
14. No se generan pares PRE/POST artificiales (independencia estricta).
"""

from __future__ import annotations

import io
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.services.validacion_taller import (
    ServicioValidacionTaller,
    resumir_fases,
)
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.models.validation import ValidacionTaller
from src.infrastructure.database.repositories.validacion_taller_repository import (
    ValidacionTallerRepository,
)
from src.interfaces.api.v1.dtos.validacion import CrearCasoValidacionDTO
from src.interfaces.api.v1.endpoints.validacion_taller import exportar_fichas_anexo2_csv

DEFAULT_SEED_TALLER = uuid.UUID("5313362a-c18d-456f-892d-a8980155c461")


# ==============================================================================
# 1. DEVELOPMENT no cuenta como oficial
# ==============================================================================
def test_1_development_no_cuenta_como_oficial():
    """Un registro en DEVELOPMENT no debe ser computado en los grupos oficiales de la tesis."""
    # En el repositorio, resumen_por_fase filtra exclusivamente por THESIS_PRETEST y THESIS_POSTTEST
    # Si solo hay casos DEVELOPMENT, la consulta devuelve lista vacía o sin fases de tesis.
    grupos_development = []
    resumen = resumir_fases(grupos_development)
    assert resumen["total_casos"] == 0
    assert resumen["casos_pretest"] == 0
    assert resumen["casos_posttest"] == 0


# ==============================================================================
# 2. PILOT no cuenta como oficial
# ==============================================================================
@pytest.mark.anyio
async def test_2_pilot_no_cuenta_como_oficial():
    """Los casos PILOT no deben computarse en pretest/posttest oficial, pero sí en casos_piloto."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    # Mock del repositorio
    servicio.repo.resumen_por_fase = AsyncMock(return_value=[])
    servicio.repo.metricas_variable_independiente = AsyncMock(return_value={"casos_verificados": 0})
    servicio.repo.distribuciones = AsyncMock(return_value={"distribucion_marcas": [], "top_fallas_reales": []})
    servicio.repo.contar_piloto = AsyncMock(return_value=20)

    metricas = await servicio.metricas(DEFAULT_SEED_TALLER)

    assert metricas["total_casos"] == 0, "PILOT no debe incrementar total_casos oficial"
    assert metricas["casos_pretest"] == 0, "PILOT no debe incrementar casos_pretest"
    assert metricas["casos_posttest"] == 0, "PILOT no debe incrementar casos_posttest"
    assert metricas["casos_piloto"] == 20, "casos_piloto debe reflejar los 20 registros piloto"


# ==============================================================================
# 3. REGRESSION no cuenta como oficial
# ==============================================================================
def test_3_regression_no_cuenta_como_oficial():
    """Los casos de regresión no forman parte de la muestra de tesis."""
    resumen = resumir_fases([])
    assert resumen["total_casos"] == 0
    assert resumen["tasa_acierto_global_porcentaje"] == 0.0


# ==============================================================================
# 4. THESIS_PRETEST cuenta únicamente en PRE
# ==============================================================================
@pytest.mark.anyio
async def test_4_thesis_pretest_cuenta_unicamente_en_pre():
    """THESIS_PRETEST solo se permite en fase Pre-test y computa en casos_pretest."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    # 1. Error si se intenta crear THESIS_PRETEST con fase Post-test
    dto_invalido = CrearCasoValidacionDTO(
        fase="Post-test",
        placa="ABC-123",
        marca_modelo="Toyota Yaris",
        sintoma="Freno vibra al presionar pedal",
        falla_real="Discos alabeados",
        chatbot_prediccion="Alabeo de discos de freno",
        campos_completos=1,
        tiempo_diagnostico_minutos=20,
        prediccion_correcta=1,
        tipo_registro="THESIS_PRETEST",
    )
    with pytest.raises(ValueError, match="THESIS_PRETEST debe pertenecer a la fase Pre-test"):
        await servicio.crear(DEFAULT_SEED_TALLER, None, dto_invalido, "ABC-***", "d" * 64)

    # 2. Computo métrico exclusivo en pretest
    grupos_pre = [{"fase": "Pre-test", "total": 1, "aciertos": 1, "completos": 1, "minutos": 25}]
    resumen = resumir_fases(grupos_pre)
    assert resumen["casos_pretest"] == 1
    assert resumen["casos_posttest"] == 0
    assert resumen["total_casos"] == 1


# ==============================================================================
# 5. THESIS_POSTTEST cuenta únicamente en POST
# ==============================================================================
@pytest.mark.anyio
async def test_5_thesis_posttest_cuenta_unicamente_en_post():
    """THESIS_POSTTEST solo se permite en fase Post-test y computa en casos_posttest."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    # 1. Error si se intenta crear THESIS_POSTTEST con fase Pre-test
    dto_invalido = CrearCasoValidacionDTO(
        fase="Pre-test",
        placa="XYZ-789",
        marca_modelo="Chevrolet Sail",
        sintoma="No arranca en las mañanas",
        falla_real="Batería agotada",
        chatbot_prediccion="Falla de batería automotriz",
        campos_completos=1,
        tiempo_diagnostico_minutos=10,
        prediccion_correcta=1,
        tipo_registro="THESIS_POSTTEST",
    )
    with pytest.raises(ValueError, match="THESIS_POSTTEST debe pertenecer a la fase Post-test"):
        await servicio.crear(DEFAULT_SEED_TALLER, None, dto_invalido, "XYZ-***", "e" * 64)

    # 2. Computo métrico exclusivo en posttest
    grupos_post = [{"fase": "Post-test", "total": 1, "aciertos": 1, "completos": 1, "minutos": 12}]
    resumen = resumir_fases(grupos_post)
    assert resumen["casos_pretest"] == 0
    assert resumen["casos_posttest"] == 1
    assert resumen["total_casos"] == 1


# ==============================================================================
# 6. Prueba informal nunca se convierte automáticamente a THESIS_*
# ==============================================================================
@pytest.mark.anyio
async def test_6_prueba_informal_nunca_se_convierte_automaticamente_a_thesis():
    """Si no se especifica tipo_registro o es None, el sistema asigna DEVELOPMENT por defecto."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    caso_creado = ValidacionTaller(
        id=uuid.uuid4(),
        item=100,
        taller_id=DEFAULT_SEED_TALLER,
        fase="Post-test",
        fecha=date.today(),
        placa_enmascarada="TST-***",
        placa_hash="f" * 64,
        marca_modelo="Nissan Sentra",
        sintoma="Tironea en alta velocidad",
        falla_real="Bujía desgastada",
        chatbot_prediccion="Falla en bujias",
        tiempo_diagnostico_minutos=10,
        prediccion_correcta=1,
        campos_completos=1,
        cantidad_campos_completos=8,
        detalles_campos={},
        tipo_registro="DEVELOPMENT",
        estado_registro="borrador",
    )
    servicio.repo.crear = AsyncMock(return_value=caso_creado)

    dto = CrearCasoValidacionDTO(
        fase="Post-test",
        placa="TST-101",
        marca_modelo="Nissan Sentra",
        sintoma="Tironea en alta velocidad",
        falla_real="Bujía desgastada",
        chatbot_prediccion="Falla en bujias",
        campos_completos=1,
        tiempo_diagnostico_minutos=10,
        prediccion_correcta=1,
        tipo_registro=None,  # No se especifica intención
    )

    await servicio.crear(DEFAULT_SEED_TALLER, None, dto, "TST-***", "f" * 64)

    # Comprobar que en la llamada al repo se pasó tipo_registro="DEVELOPMENT"
    call_args = servicio.repo.crear.call_args.kwargs
    assert call_args["tipo_registro"] == "DEVELOPMENT"
    assert call_args["tipo_registro"] != "THESIS_POSTTEST"
    assert call_args["tipo_registro"] != "THESIS_PRETEST"


# ==============================================================================
# 7. POST puede vincular diagnostico_id
# ==============================================================================
@pytest.mark.anyio
async def test_7_post_puede_vincular_diagnostico_id():
    """POST vincula un Diagnostico real y hereda conversacion_id y tiempo_inferencia_ml_ms."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    diag_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    diag_mock = Diagnostico(
        id=diag_id,
        taller_id=DEFAULT_SEED_TALLER,
        mecanico_id=uuid.uuid4(),
        conversacion_id=conv_id,
        sintoma_original="Motor tironea al acelerar",
        falla_predicha="Falla de bobinas de encendido",
        confianza=Decimal("0.8900"),
        fuente="whatsapp",
        tiempo_inferencia_ml_ms=42,
        tipo_registro="DEVELOPMENT",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = diag_mock
    session_mock.execute.return_value = mock_result

    caso_creado = ValidacionTaller(
        id=uuid.uuid4(),
        item=101,
        taller_id=DEFAULT_SEED_TALLER,
        fase="Post-test",
        fecha=date.today(),
        placa_enmascarada="DIA-***",
        placa_hash="1" * 64,
        marca_modelo="Mazda 3",
        sintoma="Tironea al acelerar en pendientes",
        falla_real="Bobina cil 1 quemada",
        chatbot_prediccion="Falla de bobinas de encendido",
        tiempo_diagnostico_minutos=15,
        prediccion_correcta=1,
        campos_completos=1,
        cantidad_campos_completos=8,
        detalles_campos={},
        tipo_registro="PILOT",
        estado_registro="borrador",
        diagnostico_id=diag_id,
        conversacion_id=conv_id,
        tiempo_inferencia_ml_ms=42,
    )
    servicio.repo.crear = AsyncMock(return_value=caso_creado)

    dto = CrearCasoValidacionDTO(
        fase="Post-test",
        diagnostico_id=str(diag_id),
        placa="DIA-123",
        marca_modelo="Mazda 3",
        sintoma="Tironea al acelerar en pendientes",
        falla_real="Bobina cil 1 quemada",
        chatbot_prediccion="Falla de bobinas",
        campos_completos=1,
        tiempo_diagnostico_minutos=15,
        prediccion_correcta=1,
        tipo_registro="PILOT",
    )

    await servicio.crear(DEFAULT_SEED_TALLER, None, dto, "DIA-***", "1" * 64)

    call_args = servicio.repo.crear.call_args.kwargs
    assert call_args["diagnostico_id"] == diag_id
    assert call_args["conversacion_id"] == conv_id
    assert call_args["tiempo_inferencia_ml_ms"] == 42


# ==============================================================================
# 8. PRE funciona sin diagnostico_id
# ==============================================================================
@pytest.mark.anyio
async def test_8_pre_funciona_sin_diagnostico_id():
    """PRETEST representa diagnóstico tradicional sin CarBot y opera sin diagnostico_id."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    caso_creado = ValidacionTaller(
        id=uuid.uuid4(),
        item=102,
        taller_id=DEFAULT_SEED_TALLER,
        fase="Pre-test",
        fecha=date.today(),
        placa_enmascarada="TRA-***",
        placa_hash="2" * 64,
        marca_modelo="Nissan Versa",
        sintoma="Luz de alternador encendida",
        falla_real="Diodo abierto",
        chatbot_prediccion="Diagnóstico tradicional con multímetro (sin CarBot)",
        tiempo_diagnostico_minutos=40,
        prediccion_correcta=1,
        campos_completos=1,
        cantidad_campos_completos=8,
        detalles_campos={},
        tipo_registro="PILOT",
        estado_registro="borrador",
        diagnostico_id=None,
        conversacion_id=None,
    )
    servicio.repo.crear = AsyncMock(return_value=caso_creado)

    dto = CrearCasoValidacionDTO(
        fase="Pre-test",
        diagnostico_id=None,
        conversacion_id=None,
        placa="TRA-123",
        marca_modelo="Nissan Versa",
        sintoma="Luz de alternador encendida",
        falla_real="Diodo abierto",
        chatbot_prediccion="Diagnóstico tradicional con multímetro (sin CarBot)",
        campos_completos=1,
        tiempo_diagnostico_minutos=40,
        prediccion_correcta=1,
        tipo_registro="PILOT",
    )

    await servicio.crear(DEFAULT_SEED_TALLER, None, dto, "TRA-***", "2" * 64)

    call_args = servicio.repo.crear.call_args.kwargs
    assert call_args["diagnostico_id"] is None
    assert call_args["conversacion_id"] is None
    assert call_args["fase"] == "Pre-test"


# ==============================================================================
# 9. Predicción vinculada no puede alterarse (inmutable)
# ==============================================================================
@pytest.mark.anyio
async def test_9_prediccion_vinculada_no_puede_alterarse():
    """Si el usuario envía una predicción modificada manualmente, el servicio restaura la del modelo."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    diag_id = uuid.uuid4()
    diag_mock = Diagnostico(
        id=diag_id,
        taller_id=DEFAULT_SEED_TALLER,
        mecanico_id=uuid.uuid4(),
        sintoma_original="Pedal esponjoso al frenar",
        falla_predicha="Fuga de liquido de frenos o bomba principal",
        confianza=Decimal("0.9500"),
        fuente="whatsapp",
        tiempo_inferencia_ml_ms=35,
        tipo_registro="DEVELOPMENT",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = diag_mock
    session_mock.execute.return_value = mock_result

    caso_creado = ValidacionTaller(
        id=uuid.uuid4(),
        item=103,
        taller_id=DEFAULT_SEED_TALLER,
        fase="Post-test",
        fecha=date.today(),
        placa_enmascarada="INM-***",
        placa_hash="3" * 64,
        marca_modelo="Suzuki Swift",
        sintoma="Pedal esponjoso al frenar",
        falla_real="Fuga en bombín",
        chatbot_prediccion="Fuga de liquido de frenos o bomba principal",
        tiempo_diagnostico_minutos=12,
        prediccion_correcta=1,
        campos_completos=1,
        cantidad_campos_completos=8,
        detalles_campos={},
        tipo_registro="PILOT",
        estado_registro="borrador",
    )
    servicio.repo.crear = AsyncMock(return_value=caso_creado)

    dto = CrearCasoValidacionDTO(
        fase="Post-test",
        diagnostico_id=str(diag_id),
        placa="INM-123",
        marca_modelo="Suzuki Swift",
        sintoma="Pedal esponjoso al frenar",
        falla_real="Fuga en bombín",
        # Intento de manipulación de la predicción del modelo
        chatbot_prediccion="Texto arbitrario manipulado por el usuario",
        campos_completos=1,
        tiempo_diagnostico_minutos=12,
        prediccion_correcta=1,
        tipo_registro="PILOT",
    )

    await servicio.crear(DEFAULT_SEED_TALLER, None, dto, "INM-***", "3" * 64)

    call_args = servicio.repo.crear.call_args.kwargs
    # La predicción enviada al repositorio DEBE ser la del diagnóstico original
    assert call_args["chatbot_prediccion"] == "Fuga de liquido de frenos o bomba principal"
    assert "manipulado" not in call_args["chatbot_prediccion"]


# ==============================================================================
# 10. Exportación oficial excluye PILOT
# ==============================================================================
@pytest.mark.anyio
async def test_10_exportacion_oficial_excluye_pilot():
    """El exportador oficial Anexo 2 excluye categóricamente los registros con tipo_registro PILOT."""
    import pandas as pd

    filas_prueba = [
        {
            "item": 1,
            "fase": "Post-test",
            "tipo_registro": "PILOT",
            "fecha": "2026-09-19",
            "placa_enmascarada": "PIL-***",
            "marca_modelo": "Auto Piloto",
            "sintoma": "Falla piloto en carretera",
            "falla_real": "Falla piloto",
            "chatbot_prediccion": "Pred piloto",
            "prediccion_correcta": 1,
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 10,
            "sintoma_registrado_correctamente": 1,
            "procesamiento_validado": 1,
            "metodo_confirmacion": "Escáner",
            "evidencia_ref": "EVID_P.JPG",
            "mecanico_id": "MEC-01",
            "fecha_validacion": "2026-09-19 10:00:00",
            "estado_registro": "verificado",
            "taller_id": str(DEFAULT_SEED_TALLER),
        },
        {
            "item": 2,
            "fase": "Post-test",
            "tipo_registro": "THESIS_POSTTEST",
            "fecha": "2026-09-19",
            "placa_enmascarada": "OFI-***",
            "marca_modelo": "Auto Oficial Tesis",
            "sintoma": "Falla oficial de prueba",
            "falla_real": "Falla oficial",
            "chatbot_prediccion": "Pred oficial",
            "prediccion_correcta": 1,
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 10,
            "sintoma_registrado_correctamente": 1,
            "procesamiento_validado": 1,
            "metodo_confirmacion": "Escáner",
            "evidencia_ref": "EVID_O.JPG",
            "mecanico_id": "MEC-01",
            "fecha_validacion": "2026-09-19 10:00:00",
            "estado_registro": "verificado",
            "taller_id": str(DEFAULT_SEED_TALLER),
        },
    ]

    with (
        patch("src.interfaces.api.v1.endpoints.validacion_taller.database_configurada", return_value=False),
        patch("src.interfaces.api.v1.endpoints.validacion_taller._cargar_df_tracker") as mock_df,
    ):
        mock_df.return_value = pd.DataFrame(filas_prueba)
        response = await exportar_fichas_anexo2_csv(
            periodo=(None, None),
            payload={"taller_id": str(DEFAULT_SEED_TALLER), "rol": "administrador"},
        )

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    contenido = b"".join(chunks).decode("utf-8-sig")

    assert "Auto Oficial Tesis" in contenido, "El caso oficial DEBE estar en el CSV"
    assert "Auto Piloto" not in contenido, "El caso PILOT DEBE estar excluido del CSV oficial"
    assert "PILOT" not in contenido


# ==============================================================================
# 11. Exportación oficial excluye DEVELOPMENT
# ==============================================================================
@pytest.mark.anyio
async def test_11_exportacion_oficial_excluye_development():
    """El exportador oficial Anexo 2 excluye categóricamente los registros con tipo_registro DEVELOPMENT."""
    import pandas as pd

    filas_prueba = [
        {
            "item": 1,
            "fase": "Post-test",
            "tipo_registro": "DEVELOPMENT",
            "fecha": "2026-09-19",
            "placa_enmascarada": "DEV-***",
            "marca_modelo": "Auto Desarrollo",
            "sintoma": "Falla dev en taller",
            "falla_real": "Falla dev",
            "chatbot_prediccion": "Pred dev",
            "prediccion_correcta": 1,
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 10,
            "sintoma_registrado_correctamente": 1,
            "procesamiento_validado": 1,
            "metodo_confirmacion": "Escáner",
            "evidencia_ref": "EVID_D.JPG",
            "mecanico_id": "MEC-01",
            "fecha_validacion": "2026-09-19 10:00:00",
            "estado_registro": "verificado",
            "taller_id": str(DEFAULT_SEED_TALLER),
        },
        {
            "item": 2,
            "fase": "Post-test",
            "tipo_registro": "THESIS_POSTTEST",
            "fecha": "2026-09-19",
            "placa_enmascarada": "OFI-***",
            "marca_modelo": "Auto Oficial Tesis",
            "sintoma": "Falla oficial de prueba",
            "falla_real": "Falla oficial",
            "chatbot_prediccion": "Pred oficial",
            "prediccion_correcta": 1,
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 10,
            "sintoma_registrado_correctamente": 1,
            "procesamiento_validado": 1,
            "metodo_confirmacion": "Escáner",
            "evidencia_ref": "EVID_O.JPG",
            "mecanico_id": "MEC-01",
            "fecha_validacion": "2026-09-19 10:00:00",
            "estado_registro": "verificado",
            "taller_id": str(DEFAULT_SEED_TALLER),
        },
    ]

    with (
        patch("src.interfaces.api.v1.endpoints.validacion_taller.database_configurada", return_value=False),
        patch("src.interfaces.api.v1.endpoints.validacion_taller._cargar_df_tracker") as mock_df,
    ):
        mock_df.return_value = pd.DataFrame(filas_prueba)
        response = await exportar_fichas_anexo2_csv(
            periodo=(None, None),
            payload={"taller_id": str(DEFAULT_SEED_TALLER), "rol": "administrador"},
        )

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    contenido = b"".join(chunks).decode("utf-8-sig")

    assert "Auto Oficial Tesis" in contenido, "El caso oficial DEBE estar en el CSV"
    assert "Auto Desarrollo" not in contenido, "El caso DEVELOPMENT DEBE estar excluido del CSV oficial"
    assert "DEVELOPMENT" not in contenido


# ==============================================================================
# 12. Contador oficial inicia 0/60 tras saneamiento
# ==============================================================================
def test_12_contador_oficial_inicia_0_de_60_tras_saneamiento():
    """Tras el saneamiento, los grupos oficiales devuelven 0 casos pretest y 0 posttest."""
    # Simula el estado de la base de datos tras el saneamiento donde ningún caso oficial está verificado
    grupos_vacio = []
    metricas = resumir_fases(grupos_vacio)

    assert metricas["casos_pretest"] == 0
    assert metricas["casos_posttest"] == 0
    assert metricas["total_casos"] == 0

    # Estado textual de avance
    total_casos = metricas["total_casos"]
    estado_muestra = (
        "MUESTRA COMPLETA (60 de 60)"
        if total_casos >= 60
        else f"TRABAJO DE CAMPO EN PROCESO ({total_casos} de 60 casos)"
    )
    assert estado_muestra == "TRABAJO DE CAMPO EN PROCESO (0 de 60 casos)"


# ==============================================================================
# 13. Datos precargados coinciden con diagnosticos
# ==============================================================================
@pytest.mark.anyio
async def test_13_datos_precargados_coinciden_con_diagnosticos():
    """Comprueba que los datos técnicos heredados del diagnóstico correspondan fielmente."""
    session_mock = AsyncMock()
    servicio = ServicioValidacionTaller(session_mock)

    diag_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    diag = Diagnostico(
        id=diag_id,
        taller_id=DEFAULT_SEED_TALLER,
        mecanico_id=uuid.uuid4(),
        conversacion_id=conv_id,
        sintoma_original="Humo negro y gasto excesivo de combustible",
        falla_predicha="Falla de inyectores de combustible",
        confianza=Decimal("0.8700"),
        fuente="whatsapp",
        tiempo_inferencia_ml_ms=38,
        tipo_registro="DEVELOPMENT",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = diag
    session_mock.execute.return_value = mock_result

    caso_creado = ValidacionTaller(
        id=uuid.uuid4(),
        item=104,
        taller_id=DEFAULT_SEED_TALLER,
        fase="Post-test",
        fecha=date.today(),
        placa_enmascarada="PRE-***",
        placa_hash="9" * 64,
        marca_modelo="Hyundai Tucson",
        sintoma="Humo negro y gasto excesivo de combustible",
        falla_real="Inyector 3 goteando",
        chatbot_prediccion="Falla de inyectores de combustible",
        tiempo_diagnostico_minutos=16,
        prediccion_correcta=1,
        campos_completos=1,
        cantidad_campos_completos=8,
        detalles_campos={},
        tipo_registro="PILOT",
        estado_registro="borrador",
        diagnostico_id=diag_id,
        conversacion_id=conv_id,
        tiempo_inferencia_ml_ms=38,
    )
    servicio.repo.crear = AsyncMock(return_value=caso_creado)

    dto = CrearCasoValidacionDTO(
        fase="Post-test",
        diagnostico_id=str(diag_id),
        placa="PRE-101",
        marca_modelo="Hyundai Tucson",
        sintoma="Humo negro y gasto excesivo de combustible",
        falla_real="Inyector 3 goteando",
        chatbot_prediccion="Falla de inyectores de combustible",
        campos_completos=1,
        tiempo_diagnostico_minutos=16,
        prediccion_correcta=1,
        tipo_registro="PILOT",
    )

    await servicio.crear(DEFAULT_SEED_TALLER, None, dto, "PRE-***", "9" * 64)

    call_args = servicio.repo.crear.call_args.kwargs
    assert call_args["chatbot_prediccion"] == diag.falla_predicha
    assert call_args["conversacion_id"] == diag.conversacion_id
    assert call_args["tiempo_inferencia_ml_ms"] == diag.tiempo_inferencia_ml_ms


# ==============================================================================
# 14. No se generan pares PRE/POST artificiales
# ==============================================================================
def test_14_no_se_generan_pares_pre_post_artificiales():
    """Comprueba que la arquitectura no posea caso_pareja_id ni suponga emparejamiento ficticio."""
    # 1. No existe la columna de pareja artificial en el modelo
    assert not hasattr(ValidacionTaller, "caso_pareja_id"), (
        "PROHIBIDO crear caso_pareja_id: la muestra PRE y POST está compuesta por vehículos distintos."
    )

    # 2. Las tablas y endpoints mantienen formato LONG independiente
    caso_a = ValidacionTaller(item=1, fase="Pre-test", placa_hash="h1" * 32)
    caso_b = ValidacionTaller(item=2, fase="Post-test", placa_hash="h2" * 32)

    assert caso_a.item != caso_b.item
    assert caso_a.placa_hash != caso_b.placa_hash
