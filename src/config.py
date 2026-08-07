import os
from pathlib import Path
from pydantic import BaseModel, Field, SecretStr

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(nombre: str, predeterminado: bool = False) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return predeterminado
    return valor.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}

class PathConfig(BaseModel):
    data_dir: Path = BASE_DIR / "data"
    dataset_csv: Path = BASE_DIR / "data" / "dataset_sintomas.csv"
    tracker_csv: Path = BASE_DIR / "data" / "tracker_diagnosticos.csv"
    manuals_dir: Path = BASE_DIR / "manuales_taller"
    manual_file: Path = BASE_DIR / "manuales_taller" / "manual_procedimientos.txt"
    model_pkl: Path = BASE_DIR / "models" / "modelo_diagnostico.pkl"
    vectorizer_pkl: Path = BASE_DIR / "models" / "vectorizador_tfidf.pkl"
    temp_audio: Path = BASE_DIR / "grabacion.wav"

class DiagnosticConfig(BaseModel):
    confidence_threshold: float = Field(default=0.70, description="Umbral mínimo de confianza para diagnóstico automático")
    rms_silence_threshold: float = Field(default=0.01, description="Umbral de energía RMS para detectar silencio")
    treble_ratio_threshold: float = Field(default=15.0, description="Porcentaje de frecuencias agudas (>2000Hz) para ruido mecánico")


class DatabaseConfig(BaseModel):
    """Configuración de PostgreSQL para desarrollo local y despliegue futuro en AWS RDS."""

    enabled: bool = _env_bool("DATABASE_ENABLED", False)
    required: bool = _env_bool("DATABASE_REQUIRED", False)
    url: str = os.getenv("DATABASE_URL", "")
    host: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port: int = int(os.getenv("POSTGRES_PORT", 5432))
    database: str = os.getenv("POSTGRES_DB", "carbot_db")
    user: str = os.getenv("POSTGRES_USER", "carbot_app")
    password: SecretStr = SecretStr(os.getenv("POSTGRES_PASSWORD", ""))
    echo_sql: bool = _env_bool("DATABASE_ECHO", False)
    pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", 5))
    max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", 10))
    pool_timeout_seconds: int = int(os.getenv("DATABASE_POOL_TIMEOUT", 30))

class AppSettings(BaseModel):
    app_name: str = "Chatbot Diagnostico Vehicular ML+RAG"
    version: str = "1.0.0"
    description: str = "Chatbot utilizando machine learning para el diagnóstico vehicular en talleres mecánicos de Carabayllo"
    debug: bool = True
    environment: str = os.getenv("ENVIRONMENT", "development")
    port: int = int(os.getenv("PORT", 8000))
    ngrok_domain: str = os.getenv("NGROK_DOMAIN", "")

    # API Keys & Credentials
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    gemini_use_free_tier: bool = _env_bool("GEMINI_USE_FREE_TIER", True)
    gemini_input_price_per_million: float = float(os.getenv("GEMINI_INPUT_PRICE_PER_MILLION", "0.30"))
    gemini_output_price_per_million: float = float(os.getenv("GEMINI_OUTPUT_PRICE_PER_MILLION", "2.50"))
    gemini_max_requests_per_minute: int = int(os.getenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "12"))
    gemini_max_requests_per_day: int = int(os.getenv("GEMINI_MAX_REQUESTS_PER_DAY", "18"))
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    twilio_message_price_usd: float = float(os.getenv("TWILIO_MESSAGE_PRICE_USD", "0.005"))
    verify_token: str = os.getenv("VERIFY_TOKEN", "MI_TOKEN_DE_VERIFICACION_SEC_123")
    meta_verify_token: str = os.getenv("META_VERIFY_TOKEN", os.getenv("VERIFY_TOKEN", "MI_TOKEN_DE_VERIFICACION_SEC_123"))
    meta_app_secret: str = os.getenv("META_APP_SECRET", "")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "super_secret_carbot_key_ucv_2026_carabayllo")
    token_whatsapp: str = os.getenv("TOKEN_WHATSAPP", "")
    telefono_id: str = os.getenv("TELEFONO_ID", "")
    meta_graph_api_version: str = os.getenv("META_GRAPH_API_VERSION", "v23.0")
    meta_message_price_usd: float = float(os.getenv("META_MESSAGE_PRICE_USD", "0.0"))

    webhook_max_body_bytes: int = int(os.getenv("WEBHOOK_MAX_BODY_BYTES", "1048576"))
    user_text_max_chars: int = int(os.getenv("USER_TEXT_MAX_CHARS", "500"))
    audio_max_bytes: int = int(os.getenv("AUDIO_MAX_BYTES", "10485760"))
    habilitar_audio: bool = _env_bool("HABILITAR_AUDIO", False)
    data_retention_days: int = int(os.getenv("DATA_RETENTION_DAYS", "180"))
    model_artifact_url: str = os.getenv("MODEL_ARTIFACT_URL", "")
    model_artifact_sha256: str = os.getenv("MODEL_ARTIFACT_SHA256", "")
    model_version: str = os.getenv("MODEL_VERSION", "local-unversioned")

    privacy_secret_key: str = os.getenv("PRIVACY_SECRET_KEY", "carbot_privacy_hmac_secret_key_2026")

    # Credenciales de autenticación JWT (configurables vía .env)
    auth_username: str = os.getenv("AUTH_USERNAME", "admin")
    auth_password: str = os.getenv("AUTH_PASSWORD", "carbot2026")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "carbot-api")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "carbot-clients")
    rate_limit_storage_uri: str = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")

    # Sub-configuraciones
    paths: PathConfig = Field(default_factory=PathConfig)
    diagnostic: DiagnosticConfig = Field(default_factory=DiagnosticConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    def validar_seguridad_produccion(self):
        """Valida que no existan secretos predeterminados ni faltantes si el entorno es producción."""
        if self.environment.lower() in ("production", "prod"):
            errores = []
            if not self.meta_app_secret or "change-me" in self.meta_app_secret.lower():
                errores.append("META_APP_SECRET es obligatorio en producción y no puede ser el valor por defecto.")
            if not self.jwt_secret_key or self.jwt_secret_key == "super_secret_carbot_key_ucv_2026_carabayllo":
                errores.append("JWT_SECRET_KEY utiliza el valor predeterminado inseguro.")
            if self.auth_username == "admin" or self.auth_password == "carbot2026":
                errores.append("AUTH_USERNAME y AUTH_PASSWORD utilizan credenciales predeterminadas.")
            if self.rate_limit_storage_uri == "memory://":
                errores.append("RATE_LIMIT_STORAGE_URI debe ser compartido en producción.")
            usa_meta = bool(self.token_whatsapp or self.telefono_id)
            usa_twilio = bool(self.twilio_account_sid or self.twilio_auth_token)
            if not usa_meta and not usa_twilio:
                errores.append("Debe configurarse Meta WhatsApp o Twilio para producción.")
            if usa_meta and not (self.token_whatsapp and self.telefono_id):
                errores.append("Meta requiere TOKEN_WHATSAPP y TELEFONO_ID.")
            if usa_twilio and not (self.twilio_account_sid and self.twilio_auth_token):
                errores.append("Twilio requiere TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN.")
            if not self.privacy_secret_key or self.privacy_secret_key == "carbot_privacy_hmac_secret_key_2026":
                errores.append("PRIVACY_SECRET_KEY utiliza la clave predeterminada.")
            if self.database.required and not self.database.enabled:
                errores.append("PostgreSQL es obligatorio, pero DATABASE_ENABLED está desactivado.")
            if self.database.enabled and not (self.database.url or self.database.password.get_secret_value()):
                errores.append("PostgreSQL está habilitado, pero no tiene DATABASE_URL ni POSTGRES_PASSWORD.")

            if errores:
                msg = "Fallo de validación de seguridad en PRODUCCIÓN:\n - " + "\n - ".join(errores)
                raise RuntimeError(msg)


    # Aliases de compatibilidad directa (Mayúsculas y Minúsculas)
    @property
    def PROJECT_NAME(self) -> str:
        return self.app_name

    @property
    def DESCRIPTION(self) -> str:
        return self.description

    @property
    def VERSION(self) -> str:
        return self.version

    @property
    def PORT(self) -> int:
        return self.port

    @property
    def NGROK_DOMAIN(self) -> str:
        return self.ngrok_domain

    @property
    def MODELO_ML_PATH(self) -> str:
        return str(self.paths.model_pkl)

    @property
    def VECTORIZADOR_PATH(self) -> str:
        return str(self.paths.vectorizer_pkl)

    @property
    def VECTORIZADOR_TFIDF_PATH(self) -> str:
        return str(self.paths.vectorizer_pkl)

    @property
    def MANUAL_PATH(self) -> str:
        return str(self.paths.manual_file)

    @property
    def MANUAL_TALLER_PATH(self) -> str:
        return str(self.paths.manual_file)

    @property
    def MANUAL_PROCEDIMIENTOS_PATH(self) -> str:
        return str(self.paths.manual_file)

    @property
    def TRACKER_PATH(self) -> str:
        return str(self.paths.tracker_csv)

    @property
    def DATASET_PATH(self) -> str:
        return str(self.paths.dataset_csv)

    @property
    def GEMINI_API_KEY(self) -> str:
        return self.gemini_api_key

    @property
    def GEMINI_MODEL(self) -> str:
        return self.gemini_model

    @property
    def OPENAI_API_KEY(self) -> str:
        return self.openai_api_key

    @property
    def TWILIO_ACCOUNT_SID(self) -> str:
        return self.twilio_account_sid

    @property
    def TWILIO_AUTH_TOKEN(self) -> str:
        return self.twilio_auth_token

    @TWILIO_AUTH_TOKEN.setter
    def TWILIO_AUTH_TOKEN(self, value: str):
        self.twilio_auth_token = value

    @property
    def VERIFY_TOKEN(self) -> str:
        return self.verify_token

    @property
    def META_VERIFY_TOKEN(self) -> str:
        return self.meta_verify_token

    @META_VERIFY_TOKEN.setter
    def META_VERIFY_TOKEN(self, value: str):
        self.meta_verify_token = value

    @property
    def META_APP_SECRET(self) -> str:
        return self.meta_app_secret

    @META_APP_SECRET.setter
    def META_APP_SECRET(self, value: str):
        self.meta_app_secret = value

    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.jwt_secret_key

    @JWT_SECRET_KEY.setter
    def JWT_SECRET_KEY(self, value: str):
        self.jwt_secret_key = value

    @property
    def TOKEN_WHATSAPP(self) -> str:
        return self.token_whatsapp

    @property
    def TELEFONO_ID(self) -> str:
        return self.telefono_id

    @property
    def PRIVACY_SECRET_KEY(self) -> str:
        return self.privacy_secret_key

    @PRIVACY_SECRET_KEY.setter
    def PRIVACY_SECRET_KEY(self, value: str):
        self.privacy_secret_key = value


# Instancia global de configuración centralizada
settings = AppSettings()
