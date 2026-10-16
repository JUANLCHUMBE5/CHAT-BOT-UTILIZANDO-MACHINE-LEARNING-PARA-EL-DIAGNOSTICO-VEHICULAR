"""Barreras obligatorias antes de cargar configuración o conectarse al stack."""
import os
from urllib.parse import urlparse


def require_lab_environment(env=None):
    env = os.environ if env is None else env
    if env.get('CARBOT_LAB_ENABLED') != 'true' or env.get('ENVIRONMENT') != 'test':
        raise RuntimeError('Laboratorio deshabilitado fuera del entorno test explícito')
    if env.get('CARBOT_BLOCK_DOTENV') != 'true':
        raise RuntimeError('El laboratorio requiere bloqueo de dotenv')
    for key in ('GEMINI_API_KEY', 'GROQ_API_KEY', 'META_ACCESS_TOKEN'):
        if env.get(key):
            raise RuntimeError(f'Credencial externa prohibida: {key}')
    db = urlparse(env.get('DATABASE_URL', '').replace('+asyncpg', ''))
    redis = urlparse(env.get('REDIS_URL', ''))
    if db.hostname != 'postgres' or db.path != '/carbot_e2e' or redis.hostname != 'redis':
        raise RuntimeError('Solo se permiten PostgreSQL/Redis del stack Docker aislado')
    api = urlparse(env.get('E2E_API_URL', 'http://api:8000/api/v1/webhook/meta'))
    if api.scheme != 'http' or api.hostname != 'api' or api.port != 8000:
        raise RuntimeError('Solo se permite la API Docker aislada')
