import json
import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.authorization import (
    exigir_confirmacion_diagnosticos,
    exigir_creacion_diagnosticos,
    exigir_lectura_diagnosticos,
)
from src.core.gemini_queue import gemini_rate_limiter
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.gestor_diagnostico import ResultadoDiagnostico as DTOInternal
from src.core.logger import logger
from src.core.security import anonimizar_identificador
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository
from src.infrastructure.database.repositories.vehiculo_repository import VehiculoRepository, normalizar_placa
from src.interfaces.api.v1.dtos.diagnosticos import (
    ActualizarEstadoDTO,
    EtapaProcesamientoDTO,
    ItemDiagnosticoDTO,
    MensajeConversacionDTO,
    PrediccionMLDTO,
)
from src.interfaces.api.v1.schemas import ConsultaDiagnostico, ResultadoDiagnostico
from src.limiter import limiter

router = APIRouter()


def _es_procedimiento_rag_real(valor: Optional[str]) -> bool:
    if not valor or not valor.strip():
        return False
    normalizado = valor.strip().lower()
    indicadores_ausencia = (
        "sin procedimiento rag",
        "inspección directa de componentes",
        "no se encontró un procedimiento",
        "no se encontro un procedimiento",
        "manual técnico no indexado",
        "manual tecnico no indexado",
        "error al buscar",
    )
    return not any(indicador in normalizado for indicador in indicadores_ausencia)


def _fecha_confirmacion_tecnica(diagnostico, trazabilidad: dict) -> Optional[str]:
    if diagnostico.estado not in {"confirmado", "descartado"}:
        return None
    validacion = trazabilidad.get("validacion_tecnica") or {}
    fecha_iso = validacion.get("validado_en")
    if fecha_iso:
        try:
            return datetime.fromisoformat(str(fecha_iso)).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    return diagnostico.actualizado_en.strftime("%Y-%m-%d %H:%M") if diagnostico.actualizado_en else None


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
    if not database_configurada():
        raise HTTPException(status_code=503, detail="El procesamiento asíncrono requiere PostgreSQL.")
    if not consulta.sintoma.strip():
        raise HTTPException(status_code=400, detail="El síntoma no puede estar vacío.")
    taller_id = uuid.UUID(token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
    payload = {
        "sintoma": consulta.sintoma,
        "placa": consulta.placa,
        "marca_modelo": f"{consulta.marca or ''} {consulta.modelo or ''}".strip(),
        "session_id": consulta.session_id,
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
    if not consulta.placa:
        raise HTTPException(status_code=400, detail="La placa es obligatoria antes de iniciar un diagnostico.")
    """Endpoint seguro con Autenticación JWT para analizar síntomas vehiculares."""
    if not consulta.sintoma.strip():
        raise HTTPException(status_code=400, detail="El síntoma no puede estar vacío.")

    t_inicio = time.time()
    try:
        placa_normalizada = normalizar_placa(consulta.placa)
        placa_anonima = anonimizar_identificador(placa_normalizada)
        logger.info(f"Procesando petición HTTP REST autenticada para Placa: {placa_anonima}")

        marca_modelo = f"{consulta.marca or ''} {consulta.modelo or ''}".strip()

        slot_gemini = None
        if settings.gemini_api_key and database_configurada():
            slot_gemini, _ = await gemini_rate_limiter.intentar_adquirir_slot_db()

        taller_id = uuid.UUID(token_payload["taller_id"])
        mecanico_id = uuid.UUID(token_payload["usuario_id"])

        dto_resultado: DTOInternal = await run_in_threadpool(
            gestor.procesar_consulta_texto,
            consulta.sintoma,
            placa=placa_normalizada,
            marca_modelo=marca_modelo,
            session_id=consulta.session_id,
            proveedor="api",
            slot_gemini_preconcedido=slot_gemini,
            diferir_encolado_persistente=True,
            taller_id=str(taller_id),
            usuario_id=str(mecanico_id),
        )
        await gemini_rate_limiter.persistir_estado_local_db()

        t_final = time.time()
        elapsed_ms = (t_final - t_inicio) * 1000
        confianza_pct = round(dto_resultado.confianza_ml * 100, 2)

        # REST debe dejar la misma trazabilidad persistida que WhatsApp.
        diagnostico_id = None
        if database_configurada():
            async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
                async with session.begin():
                    conv_repo = ConversacionRepository(session)
                    conversacion = await conv_repo.obtener_o_crear_activa(
                        taller_id=taller_id, usuario_id=mecanico_id, canal="api"
                    )
                    vehiculo = await VehiculoRepository(session).obtener_o_crear(
                        taller_id=taller_id, registrado_por_id=mecanico_id,
                        placa_str=placa_normalizada, marca=consulta.marca or "Generico",
                        modelo=consulta.modelo or "Generico", anio=consulta.anio,
                    )
                    repo = DiagnosticoRepository(session)
                    diag = await repo.crear_diagnostico(
                        taller_id=taller_id, mecanico_id=mecanico_id, vehiculo_id=vehiculo.id,
                        conversacion_id=conversacion.id,
                        sintoma_original=consulta.sintoma, falla_predicha=dto_resultado.diagnostico_ml,
                        confianza=dto_resultado.confianza_ml, similitud_rag=dto_resultado.similitud_rag,
                        fuente="hibrido", modo_diagnostico=dto_resultado.modo_diagnostico,
                        duracion_ms=round(elapsed_ms), tiempo_inferencia_ml_ms=dto_resultado.tiempo_ml_ms,
                        version_modelo_ml=settings.model_version,
                        trazabilidad={"origen": "REST", "tiempo_total_ms": round(elapsed_ms)},
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
            similitud_rag=round(dto_resultado.similitud_rag * 100, 2),
            requiere_revision_humana=dto_resultado.requiere_revision_humana,
            procedimiento_tecnico=dto_resultado.contexto_manual,
            respuesta_explicativa=dto_resultado.respuesta_texto,
            tiempo_respuesta_ms=round(elapsed_ms, 2),
            modo_diagnostico=modo_final,
            solicitud_id=solicitud_id_final,
            diagnostico_id=diagnostico_id,
        )
    except Exception as e:
        logger.error(f"Error al procesar diagnóstico en API REST: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar el diagnóstico.")


@router.get("/historial", response_model=List[ItemDiagnosticoDTO], summary="Consultar historial de diagnósticos del taller")
async def consultar_historial(
    response: Response,
    busqueda: Optional[str] = None,
    estado: Optional[str] = None,
    modo: Optional[str] = None,
    mecanico_id: Optional[uuid.UUID] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    limite: Optional[int] = Query(10, ge=1, le=1000, description="Límite de registros a retornar"),
    offset: Optional[int] = Query(0, ge=0, description="Desplazamiento para paginación"),
    token_payload: dict = Depends(exigir_lectura_diagnosticos),
):
    """Retorna la lista de diagnósticos registrados en PostgreSQL filtrando por taller_id y query params."""
    taller_id_str = token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            diag_repo = DiagnosticoRepository(session)
            diag_db_list = await diag_repo.listar_por_taller(
                taller_id=taller_uuid,
                busqueda=busqueda,
                estado=estado,
                modo=modo,
                mecanico_id=mecanico_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                limite=limite,
                offset=offset or 0,
            )
            total = await diag_repo.contar_por_taller(
                taller_id=taller_uuid,
                busqueda=busqueda,
                estado=estado,
                modo=modo,
                mecanico_id=mecanico_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )
            response.headers["X-Total-Count"] = str(total)
            res_items = []
            for d in diag_db_list:
                placa_str = f"***-{d.vehiculo.placa_ultimos4}" if d.vehiculo and d.vehiculo.placa_ultimos4 else "Sin Placa Registrada"
                marca_str = f"{d.vehiculo.marca} {d.vehiculo.modelo}" if d.vehiculo and d.vehiculo.marca else "Vehículo No Registrado"
                confianza_val = round(float(d.confianza) * 100, 1) if d.confianza is not None else 0.0
                similitud_val = round(float(d.similitud_rag) * 100, 1) if d.similitud_rag is not None else 0.0
                duracion_val = int(d.duracion_ms) if d.duracion_ms is not None else 0

                hip = d.hipotesis[0] if d.hipotesis else None
                proc_rag = "Sin procedimiento RAG registrado"
                fuente_ref = None

                if hip:
                    if _es_procedimiento_rag_real(hip.prueba_recomendada):
                        proc_rag = hip.prueba_recomendada
                    elif hip.evidencia and "RAG:" in hip.evidencia:
                        proc_rag = hip.evidencia

                    if hip.evidencia and "Fuente:" in hip.evidencia:
                        fuente_ref = hip.evidencia.split("Fuente:", 1)[1].split(". Corpus:", 1)[0].strip()

                if not fuente_ref and d.version_corpus_rag:
                    fuente_ref = f"Corpus local: {d.version_corpus_rag} (fuente documental no registrada)"

                traza = d.trazabilidad or {}
                duracion_val = int(traza.get("tiempo_total_ms", duracion_val))
                predicciones_traza = traza.get("predicciones_ml") or []
                if predicciones_traza:
                    predicciones = [
                        PrediccionMLDTO(
                            orden=indice,
                            falla=str(item.get("falla", "Sin clasificación")),
                            probabilidad=round(float(item.get("probabilidad", 0)) * 100, 1),
                        )
                        for indice, item in enumerate(predicciones_traza[:3], start=1)
                    ]
                else:
                    predicciones = [
                        PrediccionMLDTO(
                            orden=hipotesis.orden,
                            falla=hipotesis.falla_probable,
                            probabilidad=round(float(hipotesis.confianza or 0) * 100, 1),
                        )
                        for hipotesis in d.hipotesis[:3]
                    ]
                    if not predicciones:
                        predicciones = [
                            PrediccionMLDTO(
                                orden=1,
                                falla=d.falla_predicha or "Sin falla predicha",
                                probabilidad=confianza_val,
                            )
                        ]

                etapas_raw = traza.get("etapas") or []
                etapas = []
                for etapa_raw in etapas_raw:
                    etapa = dict(etapa_raw)
                    if etapa.get("clave") == "ml":
                        etapa["nombre"] = settings.model_algorithm
                    etapas.append(EtapaProcesamientoDTO(**etapa))
                if not etapas:
                    etapas = [
                        EtapaProcesamientoDTO(
                            clave="ml",
                            nombre="Clasificación ML registrada",
                            estado="completado",
                            duracion_ms=duracion_val,
                            detalle="Diagnóstico histórico: solo se conserva el tiempo total.",
                        ),
                        EtapaProcesamientoDTO(
                            clave="rag",
                            nombre="Búsqueda RAG en manuales",
                            estado="completado" if similitud_val > 0 else "sin_resultado",
                            detalle=fuente_ref,
                        ),
                        EtapaProcesamientoDTO(
                            clave="llm",
                            nombre="Síntesis técnica Gemini",
                            estado="completado" if d.sintesis_llm else "sin_registro",
                        ),
                    ]
                gemini = traza.get("gemini") or {}

                cliente_nom = "Cliente WhatsApp"
                cliente_tel = None
                if d.conversacion and d.conversacion.usuario:
                    cliente_nom = d.conversacion.usuario.nombres or "Cliente WhatsApp"
                    cliente_tel = f"+51 *** *** {d.conversacion.usuario.whatsapp_ultimos4}"
                elif d.vehiculo and d.vehiculo.registrado_por:
                    cliente_nom = d.vehiculo.registrado_por.nombres or "Cliente WhatsApp"
                    cliente_tel = f"+51 *** *** {d.vehiculo.registrado_por.whatsapp_ultimos4}"

                res_items.append(
                    ItemDiagnosticoDTO(
                        id=str(d.id),
                        sintoma_original=d.sintoma_original,
                        sintoma_normalizado=d.sintoma_normalizado or d.sintoma_original,
                        falla_predicha=d.falla_predicha or "Sin falla predicha",
                        confianza=confianza_val,
                        similitud_rag=similitud_val,
                        modo_diagnostico=d.modo_diagnostico or "completo_ml_rag_llm",
                        estado=d.estado or "generado",
                        fuente=d.fuente,
                        mecanico_id=str(d.mecanico_id),
                        mecanico_nombre=d.mecanico.nombres if d.mecanico else "Mecánico No Asignado",
                        cliente_nombre=cliente_nom,
                        cliente_telefono=cliente_tel,
                        placa_vehiculo=placa_str,
                        marca_modelo=marca_str,
                        fecha_hora=d.creado_en.strftime("%Y-%m-%d %H:%M") if d.creado_en else "Fecha no registrada",
                        duracion_ms=duracion_val,
                        procedimiento_rag=proc_rag,
                        fuente_manual=fuente_ref,
                        version_corpus_rag=d.version_corpus_rag,
                        tiempo_gravedad=d.conclusion_mecanico or "Sin conclusión registrada",
                        sintesis_llm=d.sintesis_llm,
                        notas_mecanico=d.conclusion_mecanico,
                        fecha_confirmacion=_fecha_confirmacion_tecnica(d, traza),
                        predicciones_ml=predicciones,
                        etapas_procesamiento=etapas,
                        version_modelo_ml=d.version_modelo_ml,
                        llm_usado=bool(gemini.get("usado", bool(d.sintesis_llm))),
                        llm_modelo=gemini.get("modelo"),
                        tokens_entrada=int(gemini.get("tokens_entrada", 0)),
                        tokens_salida=int(gemini.get("tokens_salida", 0)),
                        conversacion_id=str(d.conversacion_id) if d.conversacion_id else None,
                        desde_cache=bool(traza.get("desde_cache", False)),
                    )
                )
            return res_items

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.get("/vehiculos/{placa}/historial", summary="Historial exacto por placa")
async def consultar_historial_por_placa(
    placa: str,
    token_payload: dict = Depends(exigir_lectura_diagnosticos),
):
    """Busca por HMAC normalizado, sin devolver ni persistir la placa completa."""
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    try:
        placa_normalizada = normalizar_placa(placa)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    taller_id = uuid.UUID(token_payload["taller_id"])
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        vehiculo = await VehiculoRepository(session).buscar_por_placa(taller_id, placa_normalizada)
        if vehiculo is None:
            return {"placa": "no_encontrada", "diagnosticos": []}
        diagnosticos = await DiagnosticoRepository(session).listar_por_vehiculo(taller_id, vehiculo.id)
        return {
            "placa": f"***-{vehiculo.placa_ultimos4}", "vehiculo_id": str(vehiculo.id),
            "diagnosticos": [
                {"id": str(diag.id), "fecha": diag.creado_en.isoformat(), "sintoma": diag.sintoma_original,
                 "prediccion": diag.falla_predicha, "estado": diag.estado, "tipo_registro": diag.tipo_registro,
                 "duracion_ms": diag.duracion_ms}
                for diag in diagnosticos
            ],
        }


@router.patch("/{diagnostico_id}/confirmar", summary="Confirmar o modificar estado de diagnóstico")
async def confirmar_diagnostico(
    diagnostico_id: str,
    dto: ActualizarEstadoDTO,
    token_payload: dict = Depends(exigir_confirmacion_diagnosticos),
):
    """Actualiza el estado de validación mecánica en PostgreSQL verificando taller_id y restricciones de enum."""
    taller_id_str = token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            diag_repo = DiagnosticoRepository(session)
            diag = await diag_repo.obtener_por_id(uuid.UUID(diagnostico_id))
            if not diag or diag.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Diagnóstico no encontrado en este taller.")

            diag.estado = dto.nuevo_estado
            if dto.notas_mecanico:
                diag.conclusion_mecanico = dto.notas_mecanico

            usuario_id = token_payload.get("usuario_id")
            await OperacionesRepository(session).registrar_auditoria(
                accion="confirmar_diagnostico",
                entidad="diagnostico",
                entidad_id=diag.id,
                taller_id=taller_uuid,
                usuario_id=uuid.UUID(str(usuario_id)) if usuario_id else None,
                detalles={"estado_nuevo": dto.nuevo_estado},
            )

            await session.commit()
            return {"mensaje": f"Diagnóstico {diagnostico_id} actualizado a {dto.nuevo_estado} en PostgreSQL."}

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.get(
    "/{diagnostico_id}/conversacion",
    response_model=List[MensajeConversacionDTO],
    summary="Obtener trazabilidad cronológica de mensajes de la conversación del diagnóstico",
)
async def obtener_conversacion_diagnostico(
    diagnostico_id: str,
    token_payload: dict = Depends(exigir_lectura_diagnosticos),
):
    """Retorna los mensajes cronológicos reales asociados a la conversación de un diagnóstico."""
    try:
        diag_uuid = uuid.UUID(diagnostico_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de diagnóstico inválido.")

    taller_id_str = token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        diag_repo = DiagnosticoRepository(session)
        diag = await diag_repo.obtener_por_id(diag_uuid)
        if not diag or diag.taller_id != taller_uuid:
            raise HTTPException(status_code=404, detail="Diagnóstico no encontrado en este taller.")

        if not diag.conversacion_id:
            return []

        msg_repo = MensajeRepository(session)
        mensajes = await msg_repo.listar_por_conversacion(diag.conversacion_id, limite=50)
        return [
            MensajeConversacionDTO(
                id=str(m.id),
                direccion=m.direccion,
                texto=m.texto,
                tipo=m.tipo,
                fecha_hora=m.ocurrido_en.strftime("%Y-%m-%d %H:%M") if m.ocurrido_en else "Reciente",
            )
            for m in mensajes
        ]
