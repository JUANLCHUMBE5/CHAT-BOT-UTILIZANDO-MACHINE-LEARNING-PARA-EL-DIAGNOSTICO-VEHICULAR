"""
Prueba técnica única DEVELOPMENT para auditar la durabilidad de la cola Gemini.
Comprueba el flujo completo:
consulta -> encolado -> UUID persistido -> worker -> diagnóstico final -> persistencia -> recuperación.
NO crea datos de tesis ni modifica V1/V2.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Configurar entorno
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ["ENVIRONMENT"] = "development"

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.config import settings
from src.core.gemini_queue import gemini_rate_limiter, SolicitudGeminiEncolada
from src.core.gemini_queue.db_persistence import actualizar_diagnostico_y_trabajo_db
from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.database.connection import cerrar_conexion, database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico, HipotesisDiagnostico, Vehiculo
from src.infrastructure.database.models.jobs import TrabajoGemini
from src.infrastructure.database.models.messaging import Conversacion
from src.infrastructure.database.models.operations import UsoApi
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.trabajo_gemini_repository import TrabajoGeminiRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository
from src.interfaces.api.v1.endpoints.diagnostico import analizar_sintoma
from src.interfaces.api.v1.schemas import ConsultaDiagnostico


async def ejecutar_prueba_tecnica_development() -> dict:
    if not database_configurada():
        raise RuntimeError("PostgreSQL no está configurado para la prueba técnica.")

    engine = obtener_engine()
    evidencias = {}

    # Paso 0: Preparar taller y usuario de prueba técnica DEVELOPMENT
    taller_id_str = str(uuid.uuid4())
    taller_id = uuid.UUID(taller_id_str)
    usuario_id_str = str(uuid.uuid4())
    usuario_id = uuid.UUID(usuario_id_str)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        taller_repo = TallerRepository(session)
        usuario_repo = UsuarioRepository(session)
        taller = await taller_repo.crear_taller(
            nombre=f"Taller Auditoria Dev {taller_id_str[:8]}",
            taller_id=taller_id,
        )
        roles = await usuario_repo.asegurar_roles_estandar()
        usuario = await usuario_repo.crear_usuario(
            taller_id=taller.id,
            rol_id=roles["mecanico"].id,
            nombres="Mecánico Prueba Durabilidad",
            whatsapp_hash=uuid.uuid4().hex * 2,
            whatsapp_ultimos4="9901",
            usuario_id=usuario_id,
        )
        await session.commit()

    evidencias["taller_id"] = taller_id_str
    evidencias["usuario_id"] = usuario_id_str

    try:
        # Paso 1: Forzar que el rate limiter no conceda slot inmediato para probar encolado
        original_intentar = gemini_rate_limiter.intentar_adquirir_slot_db
        async def slot_simulado_agotado():
            return False, "rpd_excedido"
        gemini_rate_limiter.intentar_adquirir_slot_db = slot_simulado_agotado

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/diagnostico/analizar",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
        dummy_request = Request(scope)
        consulta = ConsultaDiagnostico(
            sintoma="El motor tiembla en ralenti, bota humo negro por el escape y el escaner arroja codigo P0301",
            placa="DEV-VERIF01",
            marca="Toyota",
            modelo="Yaris",
            anio=2020,
        )
        payload = {"taller_id": taller_id_str, "usuario_id": usuario_id_str}
        gestor = GestorDiagnostico()
        gestor.api_key = "clave-desarrollo"

        # Paso 2: Consulta -> Encolado
        resultado_rest = await analizar_sintoma(
            request=dummy_request,
            consulta=consulta,
            token_payload=payload,
            gestor=gestor,
        )

        evidencias["paso_1_respuesta_cliente"] = {
            "modo_diagnostico": resultado_rest.modo_diagnostico,
            "solicitud_id": resultado_rest.solicitud_id,
            "diagnostico_id": resultado_rest.diagnostico_id,
            "falla_predicha": resultado_rest.falla_predicha,
            "confianza": resultado_rest.confianza,
        }

        solicitud_uuid = uuid.UUID(resultado_rest.solicitud_id)
        diagnostico_uuid = uuid.UUID(resultado_rest.diagnostico_id)

        # Paso 3: Verificar que el UUID existe en trabajos_gemini en PostgreSQL ANTES del worker
        async with AsyncSession(engine, expire_on_commit=False) as session:
            trabajo_repo = TrabajoGeminiRepository(session)
            diag_repo = DiagnosticoRepository(session)

            trabajo_antes = await trabajo_repo.obtener_por_id(solicitud_uuid)
            diag_antes = await diag_repo.obtener_por_id(diagnostico_uuid)

            assert trabajo_antes is not None, "El UUID NO existe en trabajos_gemini tras responder al cliente!"
            assert trabajo_antes.estado == "pendiente", f"Estado inesperado: {trabajo_antes.estado}"
            assert trabajo_antes.diagnostico_id == diagnostico_uuid, "No coincide diagnostico_id en el trabajo!"
            assert trabajo_antes.conversacion_id is not None, "El trabajo no tiene conversacion_id asignada!"
            assert diag_antes is not None, "El diagnóstico no existe en base de datos!"
            assert diag_antes.conversacion_id == trabajo_antes.conversacion_id, "Discrepancia en conversacion_id!"

            evidencias["paso_2_uuid_persistido_antes_worker"] = {
                "uuid_en_trabajos_gemini": str(trabajo_antes.id),
                "estado_trabajo": trabajo_antes.estado,
                "diagnostico_id_asociado": str(trabajo_antes.diagnostico_id),
                "conversacion_id_asociada": str(trabajo_antes.conversacion_id),
                "proveedor": trabajo_antes.proveedor,
                "creado_en": trabajo_antes.creado_en.isoformat(),
            }

            # Paso 4: Comprobar que el worker recupera ese mismo UUID bloqueado
            trabajo_recuperado_worker = await trabajo_repo.obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=60)
            assert trabajo_recuperado_worker is not None, "El worker no pudo recuperar el trabajo pendiente!"
            assert trabajo_recuperado_worker.id == solicitud_uuid, "El worker recuperó un UUID distinto!"
            await session.commit()

            evidencias["paso_3_worker_recupera_mismo_uuid"] = {
                "uuid_recuperado_por_worker": str(trabajo_recuperado_worker.id),
                "coincide_con_solicitud": trabajo_recuperado_worker.id == solicitud_uuid,
            }

        # Paso 5: Ejecutar la finalización del worker y persistir resultado durable
        solicitud_worker = SolicitudGeminiEncolada(
            id=str(solicitud_uuid),
            diagnostico_id=str(diagnostico_uuid),
            conversacion_id=str(trabajo_antes.conversacion_id),
            taller_id=taller_id_str,
            usuario_id=usuario_id_str,
            proveedor="api",
            sintoma=consulta.sintoma,
            diagnostico_ml=resultado_rest.falla_predicha,
            confianza_ml=resultado_rest.confianza / 100.0,
        )
        sintesis_prueba = (
            "🛠️ **1. Posible Falla Vehicular (Modo Durable):**\n"
            "• **Diagnóstico Sugerido (ML):** Falla de encendido en cilindro 1\n"
            "• **Certeza del Modelo:** 85%\n\n"
            "📖 **2. Procedimiento Técnico de Reparación:**\n"
            "Intercambiar bobina de encendido del cilindro 1 al cilindro 2 y verificar si la falla se traslada.\n\n"
            "⏱️ **3. Tiempo Estimado y Gravedad:**\n"
            "30 minutos de diagnóstico. Gravedad media."
        )
        metadatos_worker = {
            "usado": True,
            "modelo": "gemini-2.0-flash",
            "modo": "completo_ml_rag_llm",
            "tiempo_llm_ms": 120,
            "tokens_entrada": 45,
            "tokens_salida": 90,
        }
        await actualizar_diagnostico_y_trabajo_db(solicitud_worker, sintesis_prueba, metadatos_worker)

        # Paso 6: Nueva conexión independiente para verificar persistencia durable post-worker
        async with AsyncSession(engine, expire_on_commit=False) as session:
            trabajo_repo = TrabajoGeminiRepository(session)
            diag_repo = DiagnosticoRepository(session)

            trabajo_despues = await trabajo_repo.obtener_por_id(solicitud_uuid)
            diag_despues = await diag_repo.obtener_por_id(diagnostico_uuid)

            assert trabajo_despues is not None, "El trabajo desapareció tras el worker!"
            assert trabajo_despues.estado == "completado", f"El trabajo no quedó completado: {trabajo_despues.estado}"
            assert diag_despues is not None, "El diagnóstico desapareció tras el worker!"
            assert diag_despues.modo_diagnostico == "completo_ml_rag_llm", "El modo_diagnostico no se actualizó!"
            assert diag_despues.sintesis_llm == sintesis_prueba, "La síntesis LLM no quedó persistida!"

            evidencias["paso_4_resultado_durable_post_worker"] = {
                "uuid_trabajo": str(trabajo_despues.id),
                "estado_final_trabajo": trabajo_despues.estado,
                "diagnostico_id": str(diag_despues.id),
                "modo_diagnostico_final": diag_despues.modo_diagnostico,
                "sintesis_llm_persistida": diag_despues.sintesis_llm[:80] + "...",
                "mismo_uuid_antes_y_despues": trabajo_antes.id == trabajo_despues.id,
            }

        # Paso 7: Recuperación posterior simulando consulta de panel / API
        async with AsyncSession(engine, expire_on_commit=False) as session:
            diag_repo = DiagnosticoRepository(session)
            diag_recuperado = await diag_repo.obtener_por_id(diagnostico_uuid)
            assert diag_recuperado is not None
            assert diag_recuperado.conversacion_id == trabajo_antes.conversacion_id

            evidencias["paso_5_recuperacion_posterior"] = {
                "recuperado_exitoso": True,
                "diagnostico_id": str(diag_recuperado.id),
                "conversacion_id": str(diag_recuperado.conversacion_id),
                "sintoma_original": diag_recuperado.sintoma_original,
                "falla_predicha": diag_recuperado.falla_predicha,
                "sintesis_longitud": len(diag_recuperado.sintesis_llm or ""),
                "fecha_creacion": diag_recuperado.creado_en.isoformat(),
            }

    finally:
        # Restaurar método original
        gemini_rate_limiter.intentar_adquirir_slot_db = original_intentar

        # Limpiar datos de prueba DEVELOPMENT
        async with AsyncSession(engine, expire_on_commit=False) as session:
            await session.execute(delete(TrabajoGemini).where(TrabajoGemini.taller_id == taller_id))
            await session.execute(delete(UsoApi).where(UsoApi.taller_id == taller_id))
            await session.execute(delete(HipotesisDiagnostico).where(HipotesisDiagnostico.diagnostico_id == diagnostico_uuid))
            await session.execute(delete(Diagnostico).where(Diagnostico.taller_id == taller_id))
            await session.execute(delete(Vehiculo).where(Vehiculo.taller_id == taller_id))
            await session.execute(delete(Conversacion).where(Conversacion.taller_id == taller_id))
            await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
            await session.execute(delete(Taller).where(Taller.id == taller_id))
            await session.commit()

    return evidencias


if __name__ == "__main__":
    resultado = asyncio.run(ejecutar_prueba_tecnica_development())
    print("=== RESULTADO AUDITORIA DURABILIDAD DEVELOPMENT ===")
    print(json.dumps(resultado, indent=2, ensure_ascii=True))
