import time
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.concurrency import run_in_threadpool
from src.interfaces.api.v1.schemas import ConsultaDiagnostico, ResultadoDiagnostico
from src.core.gestor_diagnostico import GestorDiagnostico, ResultadoDiagnostico as DTOInternal
from src.core.security import verificar_jwt_token, anonimizar_identificador
from src.core.logger import logger
from src.config import settings
from src.core.gemini_queue import gemini_rate_limiter
from src.infrastructure.database.connection import database_configurada

from src.limiter import limiter

router = APIRouter()

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
    gestor: GestorDiagnostico = Depends(obtener_gestor_diagnostico)
):
    """
    Endpoint seguro con Autenticación JWT para analizar síntomas vehiculares.
    Valida la validez de 2 horas del token y elimina condiciones de carrera.
    """
    if not consulta.sintoma.strip():
        raise HTTPException(status_code=400, detail="El síntoma no puede estar vacío.")

    t_inicio = time.time()
    try:
        placa_anonima = anonimizar_identificador(consulta.placa or "REST-API")
        logger.info(f"Procesando petición HTTP REST autenticada para Placa: {placa_anonima}")

        marca_modelo = f"{consulta.marca} {consulta.modelo}".strip()

        slot_gemini = None
        if settings.GEMINI_API_KEY and database_configurada():
            slot_gemini, _ = await gemini_rate_limiter.intentar_adquirir_slot_db()

        # Ejecutar en threadpool de forma thread-safe retornando DTO inmutable
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
            requiere_revision_humana=dto_resultado.requiere_revision_humana,
            procedimiento_tecnico=dto_resultado.contexto_manual,
            respuesta_explicativa=dto_resultado.respuesta_texto,
            tiempo_respuesta_ms=round(elapsed_ms, 2)
        )
    except Exception as e:
        logger.error(f"Error al procesar diagnóstico en API REST: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar el diagnóstico.")
