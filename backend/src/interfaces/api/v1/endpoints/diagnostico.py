import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.borrador_consulta import (
    case_id_sesion_activa,
    registrar_borrador_consulta,
)
from src.config import settings
from src.core.authorization import (
    exigir_creacion_diagnosticos,
    exigir_lectura_diagnosticos,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.session_persistence import (
    persistir_sesion_en_almacenes,
    sincronizar_sesion_desde_persistencia,
)
from src.core.gemini_queue import gemini_rate_limiter
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.gestor_diagnostico import ResultadoDiagnostico as DTOInternal
from src.core.identidad_conversacional import clave_sesion_rest, identificador_provisional
from src.core.logger import logger
from src.core.security import anonimizar_identificador
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository
from src.infrastructure.database.repositories.vehiculo_repository import VehiculoRepository, normalizar_placa
from src.interfaces.api.v1.dtos.diagnosticos import ItemDiagnosticoDTO as ItemDiagnosticoDTO
from src.interfaces.api.v1.dtos.historial_diagnostico import (
    _es_procedimiento_rag_real as _es_procedimiento_rag_real,
)
from src.interfaces.api.v1.schemas import ConsultaDiagnostico, ResultadoDiagnostico
from src.limiter import limiter

router = APIRouter()


def obtener_gestor_diagnostico(request: Request) -> GestorDiagnostico:
    """Dependency Provider para reutilizar el GestorDiagnostico en app.state o instanciarlo."""
    if hasattr(request.app.state, "gestor_diagnostico"):
        return request.app.state.gestor_diagnostico
    return GestorDiagnostico()


@router.post("/analizar-asincrono", status_code=202, summary="Encolar diagnóstico pesado")
async def analizar_sintoma_asincrono(
    consulta: ConsultaDiagnostico,
    token_payload: dict = Depends(exigir_creacion_diagnosticos),
):
    if not consulta.placa:
        raise HTTPException(status_code=400, detail="La placa es obligatoria antes de iniciar un diagnostico.")
    try:
        placa = normalizar_placa(consulta.placa)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Se requiere una placa real válida.") from exc
    if not database_configurada():
        raise HTTPException(status_code=503, detail="El procesamiento asíncrono requiere PostgreSQL.")
    if not consulta.sintoma.strip():
        raise HTTPException(status_code=400, detail="El síntoma no puede estar vacío.")
    taller_id = uuid.UUID(token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
    payload = {
        "sintoma": consulta.sintoma,
        "placa": placa,
        "marca_modelo": f"{consulta.marca or ''} {consulta.modelo or ''}".strip(),
        "session_id": clave_sesion_rest(str(taller_id), str(token_payload["usuario_id"]), consulta.session_id, placa),
        "taller_id": str(taller_id),
        "usuario_id": str(token_payload["usuario_id"]),
    }
    try:
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                trabajo, _ = await TrabajoSistemaRepository(session).crear_trabajo(
                    tipo="diagnostico_api",
                    cola="diagnosticos",
                    payload=payload,
                    taller_id=taller_id,
                    prioridad=70,
                )
    except OverflowError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers={"Retry-After": "30"}) from exc
    return {"status": "pendiente", "trabajo_id": str(trabajo.id)}


@router.get("/trabajos/{trabajo_id}", summary="Consultar resultado de diagnóstico encolado")
async def consultar_trabajo_diagnostico(
    trabajo_id: uuid.UUID,
    token_payload: dict = Depends(exigir_lectura_diagnosticos),
):
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_id = uuid.UUID(token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        trabajo = await TrabajoSistemaRepository(session).obtener_para_taller(trabajo_id, taller_id)
    if trabajo is None or trabajo.tipo != "diagnostico_api":
        raise HTTPException(status_code=404, detail="Trabajo no encontrado.")
    resultado = None
    if trabajo.resultado_resumen:
        try:
            resultado = json.loads(trabajo.resultado_resumen)
        except ValueError:
            resultado = {"detalle": trabajo.resultado_resumen}
    return {
        "trabajo_id": str(trabajo.id),
        "estado": trabajo.estado,
        "intentos": trabajo.intentos,
        "resultado": resultado,
        "error": trabajo.error_ultimo if trabajo.estado == "fallido" else None,
    }


@router.post("/analizar", response_model=ResultadoDiagnostico, summary="Analizar síntoma vehicular autenticado")
@limiter.limit("60/minute")
async def analizar_sintoma(
    request: Request,
    consulta: ConsultaDiagnostico,
    token_payload: dict = Depends(exigir_creacion_diagnosticos),
    gestor: GestorDiagnostico = Depends(obtener_gestor_diagnostico),
):
    """Endpoint seguro con Autenticación JWT para analizar síntomas vehiculares."""
    inicio_peticion = time.perf_counter()
    if not consulta.sintoma.strip():
        raise HTTPException(status_code=400, detail="El síntoma no puede estar vacío.")

    placa_candidata = consulta.placa
    if not placa_candidata and not consulta.session_id:
        try:
            from src.core.parser.message_parser import SinglePassMessageParser

            parsed = SinglePassMessageParser.parse(consulta.sintoma)
            if parsed.vehiculo and parsed.vehiculo.placa:
                placa_candidata = parsed.vehiculo.placa
        except Exception:
            pass

    if not placa_candidata and not consulta.session_id:
        raise HTTPException(status_code=400, detail="La placa es obligatoria antes de iniciar un diagnostico.")

    try:
        placa_normalizada = normalizar_placa(placa_candidata) if placa_candidata else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    solo_lectura = ExtractorHechos.es_consulta_memoria(consulta.sintoma)
    sesion_efectiva = clave_sesion_rest(
        str(token_payload["taller_id"]), str(token_payload["usuario_id"]),
        consulta.session_id, placa_normalizada,
    )
    taller_id = uuid.UUID(token_payload["taller_id"])
    mecanico_id = uuid.UUID(token_payload["usuario_id"])

    # Restaurar sesión si no reside en memoria local (ej. reinicio de API)
    if database_configurada():
        try:
            async with AsyncSession(obtener_engine(), expire_on_commit=False) as session_init:
                conv_repo = ConversacionRepository(session_init)
                conv_activa = await conv_repo.obtener_conversacion_activa(
                    taller_id=taller_id, usuario_id=mecanico_id, canal="api"
                )
                ctx_db = conv_activa.contexto if conv_activa else None
                await sincronizar_sesion_desde_persistencia(gestor, sesion_efectiva, ctx_db)
        except Exception as exc:
            logger.debug("[REST API] Error al sincronizar sesión de PostgreSQL: %s", exc)
            await sincronizar_sesion_desde_persistencia(gestor, sesion_efectiva, None)
    else:
        await sincronizar_sesion_desde_persistencia(gestor, sesion_efectiva, None)

    if solo_lectura:
        from src.core.conversacion.models import ConversationState
        from src.core.conversacion.resumen_memoria import generar_resumen_memoria
        sesion_leida = gestor.session_manager.obtener_sesion(sesion_efectiva)
        estado_leido = (
            sesion_leida.conversation_state if sesion_leida else ConversationState(session_id=sesion_efectiva)
        )
        return ResultadoDiagnostico(
            sintoma=consulta.sintoma, falla_predicha=estado_leido.falla_principal or "Sin diagnóstico registrado",
            confianza=round(estado_leido.confianza_actual * 100, 2), similitud_rag=0,
            procedimiento_tecnico="", respuesta_explicativa=generar_resumen_memoria(estado_leido),
            tiempo_respuesta_ms=round((time.perf_counter() - inicio_peticion) * 1000, 2), modo_diagnostico="consulta_memoria", diagnostico_id=None,
        )

    # case_id pertenece a SessionManager; no se copia del identificador del cliente.
    if not solo_lectura:
        sesion = gestor.session_manager.obtener_o_crear_sesion(sesion_efectiva)
        if not sesion.case_id:
            sesion.case_id = sesion.conversation_state.case_id or str(uuid.uuid4())
            sesion.conversation_state.case_id = sesion.case_id

    t_inicio = time.time()
    try:
        placa_anonima = anonimizar_identificador(placa_normalizada)
        logger.info(f"Procesando petición HTTP REST autenticada para Placa: {placa_anonima}")

        marca_modelo = f"{consulta.marca or ''} {consulta.modelo or ''}".strip()

        slot_gemini = None
        if not solo_lectura and settings.gemini_api_key and database_configurada():
            slot_gemini, _ = await gemini_rate_limiter.intentar_adquirir_slot_db()

        taller_id = uuid.UUID(token_payload["taller_id"])
        mecanico_id = uuid.UUID(token_payload["usuario_id"])

        dto_resultado: DTOInternal = await run_in_threadpool(
            gestor.procesar_consulta_texto,
            consulta.sintoma,
            placa=placa_normalizada,
            marca_modelo=marca_modelo,
            session_id=sesion_efectiva,
            proveedor="api",
            slot_gemini_preconcedido=slot_gemini,
            diferir_encolado_persistente=True,
            taller_id=str(taller_id),
            usuario_id=str(mecanico_id),
            case_id=sesion.case_id if not solo_lectura else None,
        )
        case_id_activo = case_id_sesion_activa(gestor, sesion_efectiva) or (
            sesion.case_id if not solo_lectura else None
        )
        if not solo_lectura:
            await gemini_rate_limiter.persistir_estado_local_db()

        t_final = time.time()
        elapsed_ms = (t_final - t_inicio) * 1000
        confianza_pct = round(dto_resultado.confianza_ml * 100, 2)

        # REST debe dejar la misma trazabilidad persistida que WhatsApp.
        diagnostico_id = None
        if database_configurada() and not solo_lectura:
            try:
                async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
                    async with session.begin():
                        conv_repo = ConversacionRepository(session)
                        conversacion = await conv_repo.obtener_o_crear_activa(
                            taller_id=taller_id, usuario_id=mecanico_id, canal="api"
                        )
                        vehiculo = None
                        if placa_normalizada:
                            vehiculo = await VehiculoRepository(session).obtener_o_crear(
                                taller_id=taller_id, registrado_por_id=mecanico_id,
                                placa_str=placa_normalizada, marca=consulta.marca or "Generico",
                                modelo=consulta.modelo or "Generico", anio=consulta.anio,
                            )
                        repo = DiagnosticoRepository(session)
                        diag = await repo.crear_diagnostico(
                            taller_id=taller_id, mecanico_id=mecanico_id, vehiculo_id=vehiculo.id if vehiculo else None,
                            conversacion_id=conversacion.id,
                            sintoma_original=consulta.sintoma, falla_predicha=dto_resultado.diagnostico_ml,
                            confianza=dto_resultado.confianza_ml, similitud_rag=dto_resultado.similitud_rag,
                            fuente="hibrido", modo_diagnostico=(
                                dto_resultado.modo_diagnostico
                                if dto_resultado.modo_diagnostico in {
                                    "completo_ml_rag_llm", "diagnostico_degradado_ml_rag",
                                    "en_cola_gemini", "audio_espectral", "saludo",
                                    "baja_confianza", "esperando_clarificacion",
                                }
                                else "diagnostico_degradado_ml_rag"
                            ),
                            duracion_ms=round(elapsed_ms), tiempo_inferencia_ml_ms=dto_resultado.tiempo_ml_ms,
                            version_modelo_ml=settings.model_version,
                            predicciones_svm_raw=[
                                pred.model_dump() for pred in dto_resultado.predicciones_svm_raw
                            ],
                            motivo_abstencion=dto_resultado.motivo_abstencion,
                            tiempos_tprd_ms={
                                "ml": dto_resultado.tiempo_ml_ms,
                                "rag": dto_resultado.tiempo_rag_ms,
                                "llm": dto_resultado.tiempo_llm_ms,
                                "total": round(elapsed_ms),
                            },
                            trazabilidad={
                                "origen": "REST",
                                "tiempo_total_ms": round(elapsed_ms),
                                # session_id identifica sesión, no necesariamente caso.
                                "session_id": sesion_efectiva,
                                "case_id": case_id_activo,
                                "identificador_provisional": (
                                    identificador_provisional(str(taller_id), str(conversacion.id), case_id_activo)
                                    if not vehiculo and case_id_activo else None
                                ),
                                "predicciones_ml": [
                                    pred.model_dump() for pred in dto_resultado.predicciones_ml
                                ],
                                "desde_cache": dto_resultado.desde_cache,
                            },
                        )
                        if case_id_activo:
                            conversacion.case_id = case_id_activo
                        await persistir_sesion_en_almacenes(
                            gestor, sesion_efectiva, conversacion=conversacion, case_id=case_id_activo
                        )
                        await registrar_borrador_consulta(
                            session, diag, vehiculo, case_id=case_id_activo
                        )
                        for orden, prediccion in enumerate(dto_resultado.predicciones_ml[:3], start=1):
                            await repo.agregar_hipotesis(
                                diag.id, orden, prediccion.falla, prediccion.probabilidad
                            )
                        if dto_resultado.modo_diagnostico == "en_cola_gemini" and dto_resultado.solicitud_id:
                            await gemini_rate_limiter.persistir_solicitud_en_sesion(
                                session,
                                solicitud_id=dto_resultado.solicitud_id,
                                sintoma=dto_resultado.sintoma_evaluado or consulta.sintoma,
                                diagnostico_ml=dto_resultado.diagnostico_ml,
                                confianza_ml=dto_resultado.confianza_ml,
                                contexto_manual=dto_resultado.contexto_manual,
                                titulo_manual=dto_resultado.titulo_manual,
                                requiere_revision_humana=dto_resultado.requiere_revision_humana,
                                diagnostico_id=str(diag.id),
                                conversacion_id=str(conversacion.id),
                                proveedor="api",
                                taller_id=str(taller_id),
                                usuario_id=str(mecanico_id),
                            )
                        diagnostico_id = str(diag.id)
                # El commit duradero precede a la publicación del contexto en caché.
                await persistir_sesion_en_almacenes(gestor, sesion_efectiva, case_id=case_id_activo)
            except Exception as exc:
                logger.error("[REST Diagnostico] Falló la persistencia durable: %s", type(exc).__name__)
                raise HTTPException(status_code=503, detail="No se pudo conservar el diagnóstico. Reintente la consulta.") from exc
        elif not solo_lectura:
            await persistir_sesion_en_almacenes(
                gestor, sesion_efectiva, conversacion=None, case_id=case_id_activo
            )

        modo_final = dto_resultado.modo_diagnostico
        solicitud_id_final = dto_resultado.solicitud_id
        if modo_final == "en_cola_gemini" and not diagnostico_id:
            logger.error("[REST Diagnostico] modo en_cola_gemini sin persistencia; degradando a respuesta ML+RAG")
            modo_final = "diagnostico_degradado_ml_rag"
            solicitud_id_final = None

        return ResultadoDiagnostico(
            sintoma=consulta.sintoma,
            falla_predicha=dto_resultado.diagnostico_ml,
            confianza=confianza_pct,
            origen_confianza=dto_resultado.origen_confianza,
            similitud_rag=round(dto_resultado.similitud_rag * 100, 2),
            requiere_revision_humana=dto_resultado.requiere_revision_humana,
            procedimiento_tecnico=dto_resultado.contexto_manual,
            respuesta_explicativa=dto_resultado.respuesta_texto,
            tiempo_respuesta_ms=round(elapsed_ms, 2),
            modo_diagnostico=modo_final,
            solicitud_id=solicitud_id_final,
            diagnostico_id=diagnostico_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al procesar diagnóstico en API REST: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar el diagnóstico.")


from .diagnostico_historial import confirmar_diagnostico as confirmar_diagnostico
from .diagnostico_historial import consultar_historial as consultar_historial
from .diagnostico_historial import consultar_historial_por_placa as consultar_historial_por_placa
from .diagnostico_historial import obtener_conversacion_diagnostico as obtener_conversacion_diagnostico
from .diagnostico_historial import router as historial_router

router.include_router(historial_router)
