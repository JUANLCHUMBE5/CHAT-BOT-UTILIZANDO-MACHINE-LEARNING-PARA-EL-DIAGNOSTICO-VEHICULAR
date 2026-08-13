import time
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.gemini_queue import gemini_rate_limiter
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.gestor_diagnostico import ResultadoDiagnostico as DTOInternal
from src.core.logger import logger
from src.core.security import anonimizar_identificador, verificar_jwt_token
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
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


class ActualizarEstadoDTO(BaseModel):
    nuevo_estado: Literal["generado", "en_revision", "confirmado", "descartado"]
    notas_mecanico: Optional[str] = None


class ItemDiagnosticoDTO(BaseModel):
    id: str
    sintoma_original: str
    sintoma_normalizado: str
    falla_predicha: str
    confianza: float
    similitud_rag: float = 0.0
    modo_diagnostico: str
    estado: str
    fuente: str
    mecanico_id: str
    mecanico_nombre: str
    placa_vehiculo: str
    marca_modelo: str
    fecha_hora: str
    duracion_ms: int
    procedimiento_rag: str
    fuente_manual: Optional[str] = None
    version_corpus_rag: Optional[str] = None
    tiempo_gravedad: str
    sintesis_llm: Optional[str] = None
    notas_mecanico: Optional[str] = None
    fecha_confirmacion: Optional[str] = None


def obtener_gestor_diagnostico(request: Request) -> GestorDiagnostico:
    """Dependency Provider para reutilizar el GestorDiagnostico en app.state o instanciarlo."""
    if hasattr(request.app.state, "gestor_diagnostico"):
        return request.app.state.gestor_diagnostico
    return GestorDiagnostico()


@router.post("/analizar", response_model=ResultadoDiagnostico, summary="Analizar síntoma vehicular (Requiere Token JWT de 2 horas)")
@limiter.limit("60/minute")
async def analizar_sintoma(
    request: Request,
    consulta: ConsultaDiagnostico,
    token_payload: dict = Depends(verificar_jwt_token),
    gestor: GestorDiagnostico = Depends(obtener_gestor_diagnostico),
):
    """Endpoint seguro con Autenticación JWT para analizar síntomas vehiculares."""
    if not consulta.sintoma.strip():
        raise HTTPException(status_code=400, detail="El síntoma no puede estar vacío.")

    t_inicio = time.time()
    try:
        placa_anonima = anonimizar_identificador(consulta.placa or "REST-API")
        logger.info(f"Procesando petición HTTP REST autenticada para Placa: {placa_anonima}")

        marca_modelo = f"{consulta.marca} {consulta.modelo}".strip()

        slot_gemini = None
        if settings.gemini_api_key and database_configurada():
            slot_gemini, _ = await gemini_rate_limiter.intentar_adquirir_slot_db()

        dto_resultado: DTOInternal = await run_in_threadpool(
            gestor.procesar_consulta_texto,
            consulta.sintoma,
            placa=consulta.placa or "REST-API",
            marca_modelo=marca_modelo,
            session_id=consulta.session_id,
            proveedor="api",
            slot_gemini_preconcedido=slot_gemini,
        )

        t_final = time.time()
        elapsed_ms = (t_final - t_inicio) * 1000
        confianza_pct = round(dto_resultado.confianza_ml * 100, 2)

        return ResultadoDiagnostico(
            sintoma=consulta.sintoma,
            falla_predicha=dto_resultado.diagnostico_ml,
            confianza=confianza_pct,
            similitud_rag=round(dto_resultado.similitud_rag * 100, 2),
            requiere_revision_humana=dto_resultado.requiere_revision_humana,
            procedimiento_tecnico=dto_resultado.contexto_manual,
            respuesta_explicativa=dto_resultado.respuesta_texto,
            tiempo_respuesta_ms=round(elapsed_ms, 2),
        )
    except Exception as e:
        logger.error(f"Error al procesar diagnóstico en API REST: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar el diagnóstico.")


@router.get("/historial", response_model=List[ItemDiagnosticoDTO], summary="Consultar historial de diagnósticos del taller")
async def consultar_historial(
    busqueda: Optional[str] = None,
    estado: Optional[str] = None,
    modo: Optional[str] = None,
    mecanico_id: Optional[uuid.UUID] = None,
    token_payload: dict = Depends(verificar_jwt_token),
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
                limite=100,
            )
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
                        fecha_confirmacion=d.actualizado_en.strftime("%Y-%m-%d %H:%M") if d.actualizado_en else None,
                    )
                )
            return res_items

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.patch("/{diagnostico_id}/confirmar", summary="Confirmar o modificar estado de diagnóstico")
async def confirmar_diagnostico(
    diagnostico_id: str,
    dto: ActualizarEstadoDTO,
    token_payload: dict = Depends(verificar_jwt_token),
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

            await session.commit()
            return {"mensaje": f"Diagnóstico {diagnostico_id} actualizado a {dto.nuevo_estado} en PostgreSQL."}

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

