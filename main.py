import subprocess
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Cargar variables de entorno automáticamente desde .env
load_dotenv()

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from src.limiter import limiter
from src.interfaces.api.v1.router import api_router
from src.core.gestor_diagnostico import GestorDiagnostico
from src.config import settings
from src.core.logger import logger
from src.infrastructure.database.connection import cerrar_conexion, comprobar_conexion
from src.core.gemini_queue import gemini_rate_limiter
from scripts.descargar_modelo import asegurar_artefactos_modelo
from src.core.services.retention_service import aplicar_retencion_datos

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de Ciclo de Vida de FastAPI (Singleton).
    Carga el GestorDiagnostico, Modelo ML (540MB) y FAISS RAG 1 SOLA VEZ en app.state para todos los workers.
    Inicia el worker background de la cola real de Gemini (12 req/min).
    """
    settings.validar_seguridad_produccion()
    if settings.database.enabled:
        try:
            await comprobar_conexion()
            logger.info(
                "PostgreSQL conectado correctamente en %s:%s/%s.",
                settings.database.host,
                settings.database.port,
                settings.database.database,
            )
        except Exception as exc:
            if settings.database.required or settings.environment.lower() in ("production", "prod"):
                raise RuntimeError("No fue posible conectar con PostgreSQL.") from exc
            logger.warning("PostgreSQL no está disponible; el sistema continuará sin SQL: %s", exc)
        else:
            await aplicar_retencion_datos()

    artefactos_ml = asegurar_artefactos_modelo()
    if not artefactos_ml and settings.environment.lower() in ("production", "prod"):
        raise RuntimeError("El artefacto ML verificado no está disponible en producción.")
    logger.info("Cargando GestorDiagnostico (Modelo ML + FAISS RAG) 1 sola vez en el estado de la app...")
    app.state.gestor_diagnostico = GestorDiagnostico()
    logger.info("¡Instancia global Singleton cargada exitosamente!")

    # Iniciar worker background para la cola real de Gemini
    gemini_rate_limiter.iniciar_worker()

    try:
        yield
    finally:
        await gemini_rate_limiter.detener_worker()
        await cerrar_conexion()
        logger.info("Cerrando recursos de la aplicación...")


# Inicializar aplicación FastAPI con soporte modular y versionamiento
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def agregar_request_id(request: Request, call_next):
    import uuid
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Incluir las rutas modulares versionadas bajo /api/v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "estado": "online",
        "sistema": settings.PROJECT_NAME,
        "taller": "Taller Mecánico en Carabayllo",
        "seguridad": "JWT Bearer Token (2 Horas Exp.) + Validación Firma HMAC + Rate Limiting + Concurrencia Thread-Safe",
        "documentacion": "Módulos de la arquitectura modular cargados correctamente: Presentación (api/v1), Aplicación, Infraestructura."
    }


@app.get("/health/live", include_in_schema=False)
async def health_live():
    return {"status": "alive"}


@app.get("/health/ready", include_in_schema=False)
async def health_ready(request: Request):
    componentes = {
        "postgresql": not settings.database.enabled,
        "worker_gemini": bool(gemini_rate_limiter._worker_corriendo),
        "modelo_ml": False,
        "rag": False,
    }
    if settings.database.enabled:
        try:
            await comprobar_conexion()
            componentes["postgresql"] = True
        except Exception:
            componentes["postgresql"] = False
    gestor = getattr(request.app.state, "gestor_diagnostico", None)
    if gestor:
        componentes["modelo_ml"] = bool(getattr(gestor.modelo_ml, "modelo", None))
        componentes["rag"] = bool(getattr(gestor.motor_rag, "faiss_index", None))
    listo = all(componentes.values())
    return JSONResponse(
        status_code=200 if listo else 503,
        content={"status": "ready" if listo else "not_ready", "componentes": componentes},
    )

def _iniciar_ngrok_autonomo(puerto: int, dominio: str):
    """Arranca automáticamente el túnel de Ngrok en segundo plano con tu dominio estático sin shell=True."""
    try:
        comando = ["ngrok", "http", f"--domain={dominio}", str(puerto)]
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Túnel estático Ngrok activado: https://{dominio}")
        logger.info(f"URL de Webhook WhatsApp para Meta: https://{dominio}/api/v1/webhook")
    except Exception as e:
        logger.warning(f"No se pudo iniciar el túnel automático de Ngrok: {e}")

if __name__ == "__main__":
    if settings.NGROK_DOMAIN:
        _iniciar_ngrok_autonomo(settings.PORT, settings.NGROK_DOMAIN)
        
    logger.info(f"Iniciando servidor del Chatbot Vehicular en el puerto {settings.PORT}...")
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=False)
