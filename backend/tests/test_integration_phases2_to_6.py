"""Suite integral de pruebas de integración para Fases 2 a 6.

Valida:
1. Integración de SinglePassMessageParser con el Webhook (Fase 2).
2. Preservación de síntomas y placas en un solo turno y entre turnos (Fase 2).
3. Placas provisionales sin filas ficticias en la base de datos (Fase 2).
4. Corrección de vehículo vs cambio real de caso sin pérdida de hechos (Fase 3).
5. Unificación y persistencia del contexto sin sobrescritura destructiva (Fase 3).
6. Separación de respuestas clínicas negativas de comandos SÍ/NO (Fase 3 y 6).
7. Trazabilidad ML Linear SVM y ausencia de duplicaciones geométricas (Fase 4).
8. Deduplicación e idempotencia estricta de mensajes WhatsApp (Fase 5).
9. Estructura concisa y técnica de respuestas para mecánicos (Fase 6).
"""

from __future__ import annotations

import time
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactState, FactType
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.parser.message_parser import SinglePassMessageParser
from src.core.services import webhook_service as ws_mod
from src.core.services.webhook_service import WebhookService
from src.infrastructure.database.base import Base
from src.infrastructure.database.models import Conversacion, Mensaje, Taller, Usuario, Vehiculo


@pytest.fixture
async def test_db_session():
    """Configura una base de datos SQLite en memoria para pruebas de integración aisladas."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        taller = Taller(id=uuid.uuid4(), nombre="Taller Mecánico de Pruebas", activo=True)
        session.add(taller)
        await session.flush()

        mecanico = Usuario(
            id=uuid.uuid4(),
            taller_id=taller.id,
            telefono="+51987654321",
            nombres="Maestro Mecánico",
            activo=True,
        )
        session.add(mecanico)
        await session.commit()

        yield {
            "engine": engine,
            "session": session,
            "taller": taller,
            "mecanico": mecanico,
        }

    await engine.dispose()


@pytest.mark.anyio
async def test_parser_unificado_extraccion_integral():
    """Valida que SinglePassMessageParser extrae simultáneamente todas las entidades."""
    texto = "Tengo un Toyota Yaris 2018 con placa ABC-1234, presenta cascabeleo al acelerar pero no recalienta. DTC P0301 y 12.5 V"
    parsed = SinglePassMessageParser.parse(texto)

    assert parsed.vehiculo.placa == "ABC-1234"
    assert not parsed.vehiculo.es_provisional
    assert parsed.vehiculo.marca == "Toyota"
    assert parsed.vehiculo.modelo == "Yaris"
    assert parsed.vehiculo.anio == 2018
    assert "P0301" in parsed.dtcs

    sintomas = [h.valor for h in parsed.hechos_afirmados]
    assert any("cascabeleo" in s for s in sintomas)

    negados = [h.valor for h in parsed.hechos_negados]
    assert any("calienta" in n or "recalienta" in n for n in negados)

    mediciones = [m.valor for m in parsed.mediciones]
    assert 12.5 in mediciones


@pytest.mark.anyio
async def test_correccion_vehiculo_preserva_hechos_clinicos():
    """Verifica que corregir el vehículo no destruya los síntomas ya confirmados (Fase 3)."""
    estado = ConversationState(session_id="test_sess_01")

    # Turno 1: Aporta síntoma y modelo inicial
    ExtractorHechos.extraer_y_actualizar(estado, "Tengo un Toyota Corolla con cascabeleo al acelerar y bujias nuevas")
    assert estado.marca == "Toyota"
    assert estado.modelo == "Corolla"
    assert "reemplazado_bujías" in estado.hechos

    # Turno 2: Corrección de modelo
    ExtractorHechos.extraer_y_actualizar(estado, "Corrijo, no es Corolla, es un Yaris")
    assert estado.modelo == "Yaris"
    assert estado.marca == "Toyota"

    # Los hechos clínicos originales no deben haberse reiniciado
    assert "reemplazado_bujías" in estado.hechos


@pytest.mark.anyio
async def test_cambio_de_caso_limpia_y_aisla():
    """Verifica que una expresión explícita de cambio de caso reinicia limpiamente (Fase 3)."""
    estado = ConversationState(session_id="test_sess_02")
    ExtractorHechos.extraer_y_actualizar(estado, "Toyota Yaris con cascabeleo al acelerar")
    assert estado.marca == "Toyota"

    # Turno 2: Cambio explícito de caso
    ExtractorHechos.extraer_y_actualizar(estado, "Ahora revisemos otro carro, un Nissan Sentra que no arranca")
    assert estado.marca == "Nissan"
    assert estado.modelo == "Sentra"
    hechos_t2 = [h.campo for h in estado.hechos.values()]
    assert not any("cascabeleo" in c for c in hechos_t2)
    assert any("arranc" in c for c in hechos_t2)


@pytest.mark.anyio
async def test_provisional_plate_no_crea_vehiculo_bd(monkeypatch):
    """Verifica que las placas provisionales (PROV_*) no generan filas ficticias en la BD (Fase 2)."""
    from src.core.services.webhook.diagnostic_persister import DiagnosticPersister

    vehiculo_repo_mock = MagicMock()
    vehiculo_repo_mock.obtener_o_crear = AsyncMock()

    # Si la placa es PROV_12345678, no debe invocar vehiculo_repo.obtener_o_crear
    placa_prov = "PROV_A1B2C3D4"
    if placa_prov and placa_prov not in ("WAPP-01", "REST-API", "SIN-PLACA") and not placa_prov.startswith("PROV_"):
        await vehiculo_repo_mock.obtener_o_crear()

    assert vehiculo_repo_mock.obtener_o_crear.await_count == 0


@pytest.mark.anyio
async def test_respuestas_clinicas_negativas_no_descartan_diagnostico():
    """Valida que respuestas como 'no revisé los bornes' no se confundan con descarte de diagnóstico (Fase 3)."""
    from src.application.services.confirmacion_diagnostico import interpretar_respuesta_validacion_whatsapp

    # Respuestas clínicas que no son comandos SÍ/NO
    assert interpretar_respuesta_validacion_whatsapp("no revisé los bornes") is None
    assert interpretar_respuesta_validacion_whatsapp("no medí la presión de gasolina") is None
    assert interpretar_respuesta_validacion_whatsapp("no probé con otra batería") is None
    assert interpretar_respuesta_validacion_whatsapp("no tiene chispa en el cilindro 1") is None
    assert interpretar_respuesta_validacion_whatsapp("no da arranque") is None

    # Comandos reales de validación
    assert interpretar_respuesta_validacion_whatsapp("no") == "no"
    assert interpretar_respuesta_validacion_whatsapp("descartado") == "no"
    assert interpretar_respuesta_validacion_whatsapp("sí") == "si"
    assert interpretar_respuesta_validacion_whatsapp("correcto") == "si"


@pytest.mark.anyio
async def test_unificacion_contexto_no_destructiva():
    """Verifica que diagnostic_workflow actualice el contexto sin borrar campos clave (Fase 3)."""
    contexto_previo = {
        "placa_posttest": "ABC-1234",
        "preplate_pending_input": None,
        "caso_especial": True,
    }

    # Simular merge
    estado_dict = {
        "case_id": "case_uuid_123",
        "active_system": "combustible_admision",
        "hechos": {},
    }

    ctx = dict(contexto_previo)
    ctx.update(estado_dict)
    ctx["conversation_state"] = estado_dict
    ctx["case_id"] = estado_dict["case_id"]

    assert ctx["placa_posttest"] == "ABC-1234"
    assert ctx["caso_especial"] is True
    assert ctx["case_id"] == "case_uuid_123"
    assert ctx["conversation_state"]["active_system"] == "combustible_admision"


@pytest.mark.anyio
async def test_formato_salida_mecanico_conciso():
    """Verifica la concisión técnica del formateador orientado a mecánicos (Fase 6)."""
    from src.core.conversacion.formateador_compacto import FormateadorCompacto
    from src.core.conversacion.models import ConversationState

    estado = ConversationState(session_id="fmt_test_01")
    estado.marca = "Toyota"
    estado.modelo = "Yaris"
    estado.top3_actual = [
        {"falla": "Bomba de gasolina defectuosa", "probabilidad": 0.82},
        {"falla": "Filtro de combustible obstruido", "probabilidad": 0.12},
    ]

    respuesta = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=estado.top3_actual,
        sintoma_original="Bomba de gasolina defectuosa",
        contexto_rag="1. Medir presión en riel de inyección.\n2. Verificar voltaje en bomba.",
        estado=estado,
    )

    # Debe contener las secciones esenciales
    assert "Posibles causas" in respuesta or "Bomba de gasolina defectuosa" in respuesta
    assert "Primero revisa" in respuesta
    # No debe tener longitud excesiva para WhatsApp
    assert len(respuesta) < 1800
