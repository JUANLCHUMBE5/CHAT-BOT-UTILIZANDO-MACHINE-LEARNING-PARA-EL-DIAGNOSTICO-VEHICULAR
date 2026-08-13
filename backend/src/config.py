"""Configuración centralizada y tipada de CarBot.

Los nombres internos siguen ``snake_case``. Las variables antiguas del entorno
se aceptan temporalmente para no romper instalaciones existentes.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field, SecretStr

from src.config_bootstrap import cargar_variables_entorno

cargar_variables_entorno()

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
ML_ROOT = Path(os.getenv("ML_ROOT") or PROJECT_ROOT / "machine_learning")

TRUE_VALUES = {"1", "true", "yes", "on", "si", "sí"}
PRODUCTION_ENVIRONMENTS = {"production", "prod"}


def _env_first(*names: str, default: str = "") -> str:
    """Devuelve la primera variable definida, incluyendo valores vacíos explícitos."""
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


def _env_bool(*names: str, default: bool = False) -> bool:
    value = _env_first(*names)
    return default if value == "" else value.strip().lower() in TRUE_VALUES


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return default if value in (None, "") else int(value)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser un número entero.") from exc


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    try:
        return default if value in (None, "") else float(value)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser un número.") from exc


def _env_csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if not value:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


class PathConfig(BaseModel):
    data_dir: Path = ML_ROOT / "data"
    dataset_csv: Path = ML_ROOT / "data" / "dataset_sintomas.csv"
    tracker_csv: Path = ML_ROOT / "data" / "tracker_diagnosticos.csv"
    manuals_dir: Path = ML_ROOT / "manuals"
    manual_file: Path = ML_ROOT / "manuals" / "manual_procedimientos.txt"
    model_pkl: Path = ML_ROOT / "models" / "modelo_diagnostico.pkl"
    vectorizer_pkl: Path = ML_ROOT / "models" / "vectorizador_tfidf.pkl"
    temp_audio: Path = BACKEND_DIR / "grabacion.wav"


class DiagnosticConfig(BaseModel):
    rag_min_similarity: float = Field(
        default=_env_float("RAG_MIN_SIMILARITY", 0.25),
        ge=0.0,
        le=1.0,
        description="Similitud mínima provisional para aceptar una respuesta RAG.",
    )
    confidence_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    rms_silence_threshold: float = Field(default=0.01, ge=0.0)
    treble_ratio_threshold: float = Field(default=15.0, ge=0.0)


class DatabaseConfig(BaseModel):
    """Configuración de PostgreSQL para desarrollo y producción."""

    enabled: bool = _env_bool("DATABASE_ENABLED")
    required: bool = _env_bool("DATABASE_REQUIRED")
    url: str = os.getenv("DATABASE_URL", "")
    host: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port: int = _env_int("POSTGRES_PORT", 5432)
    database: str = os.getenv("POSTGRES_DB", "carbot_db")
    user: str = os.getenv("POSTGRES_USER", "carbot_app")
    password: SecretStr = SecretStr(os.getenv("POSTGRES_PASSWORD", ""))
    echo_sql: bool = _env_bool("DATABASE_ECHO")
    pool_size: int = _env_int("DATABASE_POOL_SIZE", 5)
    max_overflow: int = _env_int("DATABASE_MAX_OVERFLOW", 10)
    pool_timeout_seconds: int = _env_int("DATABASE_POOL_TIMEOUT", 30)


class AppSettings(BaseModel):
    app_name: str = "CarBot — Diagnóstico Vehicular ML+RAG"
    version: str = "1.0.0"
    description: str = "Chatbot de diagnóstico vehicular para talleres mecánicos."
    environment: str = os.getenv("ENVIRONMENT", "development").strip().lower()
    debug: bool = _env_bool("DEBUG")
    port: int = _env_int("PORT", 8000)
    ngrok_domain: str = os.getenv("NGROK_DOMAIN", "")
    cors_allowed_origins: tuple[str, ...] = Field(
        default_factory=lambda: _env_csv("CORS_ALLOWED_ORIGINS", ("http://localhost:5173",))
    )

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    gemini_use_free_tier: bool = _env_bool("GEMINI_USE_FREE_TIER", default=True)
    gemini_input_price_per_million: float = _env_float("GEMINI_INPUT_PRICE_PER_MILLION", 0.30)
    gemini_output_price_per_million: float = _env_float("GEMINI_OUTPUT_PRICE_PER_MILLION", 2.50)
    gemini_max_requests_per_minute: int = _env_int("GEMINI_MAX_REQUESTS_PER_MINUTE", 12)
    gemini_max_requests_per_day: int = _env_int("GEMINI_MAX_REQUESTS_PER_DAY", 18)

    # META_ACCESS_TOKEN y META_PHONE_NUMBER_ID son los nombres preferidos.
    # TOKEN_WHATSAPP y TELEFONO_ID se mantienen como compatibilidad temporal.
    meta_access_token: str = _env_first("META_ACCESS_TOKEN", "TOKEN_WHATSAPP")
    meta_phone_number_id: str = _env_first("META_PHONE_NUMBER_ID", "TELEFONO_ID")
    meta_graph_api_version: str = os.getenv("META_GRAPH_API_VERSION", "v25.0")
    meta_verify_token: str = _env_first("META_VERIFY_TOKEN", "VERIFY_TOKEN")
    meta_app_secret: str = os.getenv("META_APP_SECRET", "")
    meta_message_price_usd: float = _env_float("META_MESSAGE_PRICE_USD", 0.0)

    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    twilio_message_price_usd: float = _env_float("TWILIO_MESSAGE_PRICE_USD", 0.005)

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "carbot-api")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "carbot-clients")
    privacy_secret_key: str = os.getenv("PRIVACY_SECRET_KEY", "")
    fallback_auth_username: str = _env_first("LOCAL_AUTH_USERNAME", "AUTH_USERNAME")
    fallback_auth_password: str = _env_first("LOCAL_AUTH_PASSWORD", "AUTH_PASSWORD")
    rate_limit_storage_uri: str = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")

    webhook_max_body_bytes: int = _env_int("WEBHOOK_MAX_BODY_BYTES", 1_048_576)
    user_text_max_chars: int = _env_int("USER_TEXT_MAX_CHARS", 500)
    audio_max_bytes: int = _env_int("AUDIO_MAX_BYTES", 10_485_760)
    audio_enabled: bool = _env_bool("AUDIO_ENABLED", "HABILITAR_AUDIO")
    data_retention_days: int = _env_int("DATA_RETENTION_DAYS", 180)
    model_artifact_url: str = os.getenv("MODEL_ARTIFACT_URL", "")
    model_artifact_sha256: str = os.getenv("MODEL_ARTIFACT_SHA256", "")
    model_version: str = os.getenv("MODEL_VERSION", "2.1.0-grouped-calibrated")

    paths: PathConfig = Field(default_factory=PathConfig)
    diagnostic: DiagnosticConfig = Field(default_factory=DiagnosticConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    @property
    def is_production(self) -> bool:
        return self.environment in PRODUCTION_ENVIRONMENTS

    def validate_production_security(self) -> None:
        """Impide iniciar producción con configuración insegura o incompleta."""
        if not self.is_production:
            return

        errors: list[str] = []
        if len(self.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY debe tener al menos 32 caracteres.")
        if len(self.privacy_secret_key) < 32:
            errors.append("PRIVACY_SECRET_KEY debe tener al menos 32 caracteres.")
        if self.rate_limit_storage_uri == "memory://":
            errors.append("RATE_LIMIT_STORAGE_URI debe usar almacenamiento compartido.")
        if "*" in self.cors_allowed_origins:
            errors.append("CORS_ALLOWED_ORIGINS no puede contener '*' en producción.")

        uses_meta = bool(self.meta_access_token or self.meta_phone_number_id)
        uses_twilio = bool(self.twilio_account_sid or self.twilio_auth_token)
        if not uses_meta and not uses_twilio:
            errors.append("Debe configurarse Meta WhatsApp o Twilio.")
        if uses_meta and not (self.meta_access_token and self.meta_phone_number_id):
            errors.append("Meta requiere META_ACCESS_TOKEN y META_PHONE_NUMBER_ID.")
        if uses_meta and not self.meta_verify_token:
            errors.append("Meta requiere META_VERIFY_TOKEN.")
        if uses_meta and not self.meta_app_secret:
            errors.append("Meta requiere META_APP_SECRET.")
        if uses_twilio and not (self.twilio_account_sid and self.twilio_auth_token):
            errors.append("Twilio requiere TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN.")
        if self.database.required and not self.database.enabled:
            errors.append("DATABASE_REQUIRED exige DATABASE_ENABLED=true.")
        if not self.database.enabled:
            errors.append("PostgreSQL debe estar habilitado en producción.")
        if self.database.enabled and not (self.database.url or self.database.password.get_secret_value()):
            errors.append("PostgreSQL requiere DATABASE_URL o POSTGRES_PASSWORD.")

        if errors:
            raise RuntimeError("Configuración de producción inválida:\n - " + "\n - ".join(errors))


settings = AppSettings()
