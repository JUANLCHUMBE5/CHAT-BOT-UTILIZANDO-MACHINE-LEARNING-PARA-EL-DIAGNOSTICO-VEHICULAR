from fastapi import APIRouter

from src.interfaces.api.v1.endpoints.auth import router as auth_router
from src.interfaces.api.v1.endpoints.clientes import router as clientes_router
from src.interfaces.api.v1.endpoints.diagnostico import router as diagnostico_router
from src.interfaces.api.v1.endpoints.mecanicos import router as mecanicos_router
from src.interfaces.api.v1.endpoints.metricas import router as metricas_router
from src.interfaces.api.v1.endpoints.validacion_taller import router as validacion_taller_router
from src.interfaces.messaging.whatsapp import router as webhook_router

api_router = APIRouter()

# Registrar sub-enrutadores modulares v1
api_router.include_router(auth_router, prefix="/auth", tags=["Autenticación JWT"])
api_router.include_router(webhook_router, prefix="/webhook", tags=["Webhook WhatsApp"])
api_router.include_router(diagnostico_router, prefix="/diagnostico", tags=["Diagnóstico REST"])
api_router.include_router(mecanicos_router, prefix="/mecanicos", tags=["Gestión Mecánicos"])
api_router.include_router(clientes_router, prefix="/clientes", tags=["Clientes y Solicitudes"])
api_router.include_router(metricas_router, prefix="/metricas", tags=["Métricas Ejecutivas"])
api_router.include_router(validacion_taller_router, prefix="/validacion-taller", tags=["Validación Real Taller"])
