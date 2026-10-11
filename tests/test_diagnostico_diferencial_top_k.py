"""Pruebas de regresión para la obtención, filtrado y persistencia del diagnóstico diferencial Top-K."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico
from src.core.gemini_queue.models import SolicitudGeminiEncolada
from src.core.gemini_queue.summary_formatter import crear_resumen_whatsapp
from src.core.security import hash_identificador_persistencia
from src.core.services.webhook.diagnostic_persister import DiagnosticPersister
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico, HipotesisDiagnostico
from src.infrastructure.database.models.messaging import Conversacion
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@pytest.fixture
async def setup_persister_db():
    if not database_configurada():
        pytest.skip("PostgreSQL no está configurado para pruebas.")

    engine = obtener_engine()
    taller_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        taller_repo = TallerRepository(session)
        user_repo = UsuarioRepository(session)

        taller = await taller_repo.crear_taller(
            nombre=f"Taller TopK Test {taller_id.hex[:6]}",
            ruc=f"20{uuid.uuid4().int % 1000000000:09d}",
            taller_id=taller_id,
            telefono_id_meta=f"META_{taller_id.hex[:8]}",
        )
        roles = await user_repo.asegurar_roles_estandar()

        tel = f"+51 983 {uuid.uuid4().int % 1000000:06d}"
        usuario = await user_repo.crear_usuario(
            taller_id=taller.id,
            rol_id=roles["mecanico"].id,
            nombres="Mecanico TopK",
            whatsapp_hash=hash_identificador_persistencia(tel, "telefono"),
            whatsapp_ultimos4=tel[-4:],
            usuario_id=user_id,
        )
        conv_repo = ConversacionRepository(session)
        await conv_repo.crear_conversacion(
            taller_id=taller.id,
            usuario_id=usuario.id,
            conversacion_id=conv_id,
        )
        await session.commit()

    yield {
        "engine": engine,
        "taller_id": taller_id,
        "usuario_id": user_id,
        "conv_id": conv_id,
    }


def test_summary_formatter_presenta_top3_completo():
    solicitud = SolicitudGeminiEncolada(
        id="sol-1",
        sintoma="Motor cascabelea y pierde fuerza",
        diagnostico_ml="Falla en bujias o bobinas de encendido (misfire)",
        confianza_ml=0.78,
        predicciones_ml=[
            {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.78},
            {"falla": "Falla en sensor de oxigeno o mezcla rica", "probabilidad": 0.12},
            {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.08},
        ],
    )
    texto_llm = "Se detectó misfire severo en cilindro 1. Procedimiento: Revisar bobinas con osciloscopio."
    resumen = crear_resumen_whatsapp(solicitud, texto_llm)

    assert "Hipótesis ML: *Falla en bujias o bobinas de encendido (misfire)*" in resumen
    assert "🔍 *Otras posibilidades (ML):*" in resumen
    assert "• Falla en sensor de oxigeno o mezcla rica (12%)" in resumen
    assert "• Bomba de gasolina quemada o con baja presion (8%)" in resumen


def test_summary_formatter_con_solo_una_hipotesis_no_inventa_resultados():
    solicitud = SolicitudGeminiEncolada(
        id="sol-2",
        sintoma="Ruido seco en arrancador",
        diagnostico_ml="Falla en motor de arranque o solenoide defectuoso",
        confianza_ml=0.92,
        predicciones_ml=[
            {"falla": "Falla en motor de arranque o solenoide defectuoso", "probabilidad": 0.92},
            {"falla": "Causa residual espuria", "probabilidad": 0.02},  # < 5%, debe ser descartada
        ],
    )
    texto_llm = "Revisar solenoide y carbones del arrancador."
    resumen = crear_resumen_whatsapp(solicitud, texto_llm)

    assert "Hipótesis ML: *Falla en motor de arranque o solenoide defectuoso*" in resumen
    # No debe inventar bloques diferenciales vacíos o con causas bajo el 5%
    assert "🔍 *Otras posibilidades (ML):*" not in resumen
    assert "Causa residual espuria" not in resumen


@pytest.mark.anyio
async def test_diagnostic_persister_guarda_top3_e_informa_trazabilidad(setup_persister_db):
    data = setup_persister_db
    dto = ResultadoDiagnostico(
        respuesta_texto="Diagnóstico preliminar completado.",
        diagnostico_ml="Falla en termostato trabado cerrado",
        confianza_ml=0.82,
        contexto_manual="Procedimiento de verificación de termostato OEM",
        titulo_manual="Manual Refrigeración OEM",
        similitud_rag=0.88,
        sintoma_evaluado="el carro calienta y la manguera inferior esta fria",
        predicciones_ml=[
            PrediccionML(falla="Falla en termostato trabado cerrado", probabilidad=0.82),
            PrediccionML(falla="Electroventilador no enciende o fusible quemado", probabilidad=0.11),
            PrediccionML(falla="Fuga en radiador o manguera de refrigerante", probabilidad=0.06),
        ],
        predicciones_ml_raw=[
            PrediccionML(falla="Falla en termostato trabado cerrado", probabilidad=0.82),
            PrediccionML(falla="Electroventilador no enciende o fusible quemado", probabilidad=0.11),
            PrediccionML(falla="Fuga en radiador o manguera de refrigerante", probabilidad=0.06),
            PrediccionML(falla="Bomba de agua con aspas desgastadas", probabilidad=0.01),
        ],
    )

    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        user = await session.get(Usuario, data["usuario_id"])
        conv = await session.get(Conversacion, data["conv_id"])

        res, costo = await DiagnosticPersister.persistir_y_responder(
            session=session,
            dto=dto,
            usuario=user,
            conversacion=conv,
            texto_cliente="el carro calienta y la manguera inferior esta fria",
            meta_message_id=f"wamid_topk_{uuid.uuid4().hex}",
            remitente="+51983000000",
            proveedor="meta",
            placa="TOP3001",
            marca_modelo="Nissan Versa 2017",
            duracion_ms=120,
            corpus_version="v1.0",
        )
        await session.commit()
        diag_id = uuid.UUID(res["diagnostico_id"])

    # Verificar que se persistieron exactamente 3 hipótesis en hipotesis_diagnostico
    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        hipotesis = (
            await session.execute(
                select(HipotesisDiagnostico)
                .where(HipotesisDiagnostico.diagnostico_id == diag_id)
                .order_by(HipotesisDiagnostico.orden)
            )
        ).scalars().all()

        assert len(hipotesis) == 3
        assert hipotesis[0].orden == 1
        assert hipotesis[0].falla_probable == "Falla en termostato trabado cerrado"
        assert float(hipotesis[0].confianza) == pytest.approx(0.82, abs=0.01)

        assert hipotesis[1].orden == 2
        assert hipotesis[1].falla_probable == "Electroventilador no enciende o fusible quemado"
        assert float(hipotesis[1].confianza) == pytest.approx(0.11, abs=0.01)

        assert hipotesis[2].orden == 3
        assert hipotesis[2].falla_probable == "Fuga en radiador o manguera de refrigerante"
        assert float(hipotesis[2].confianza) == pytest.approx(0.06, abs=0.01)

        # Comprobar la trazabilidad científica guardada en el diagnóstico
        diag_db = await session.get(Diagnostico, diag_id)
        assert diag_db is not None
        traza = diag_db.trazabilidad
        assert len(traza["predicciones_ml"]) == 3
        assert len(traza["predicciones_ml_raw"]) == 4
