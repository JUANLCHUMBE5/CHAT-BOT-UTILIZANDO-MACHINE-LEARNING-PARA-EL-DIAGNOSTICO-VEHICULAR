from typing import Optional

from pydantic import BaseModel, Field

# --- DTOs de Entrada (Request Schemas) ---

class SymptomRequestDTO(BaseModel):
    sintoma: str = Field(..., max_length=500, description="Texto con la descripción del síntoma o problema del auto", json_schema_extra={"example": "siento un chillido feo al frenar el carro"})
    marca: Optional[str] = Field(default=None, max_length=50, description="Marca opcional del vehículo", json_schema_extra={"example": "Toyota"})
    modelo: Optional[str] = Field(default=None, max_length=50, description="Modelo opcional del vehículo", json_schema_extra={"example": "Yaris"})
    anio: Optional[int] = Field(default=None, ge=1900, le=2100, description="Año opcional de fabricación", json_schema_extra={"example": 2018})
    placa: Optional[str] = Field(default=None, max_length=20, description="Placa del vehículo", json_schema_extra={"example": "ABC-123"})
    session_id: Optional[str] = Field(default=None, max_length=100, description="ID de sesión para el seguimiento conversacional", json_schema_extra={"example": "sess-12345"})

class WhatsAppWebhookPayloadDTO(BaseModel):
    from_number: str = Field(..., max_length=50, description="Número remitente del WhatsApp", json_schema_extra={"example": "whatsapp:+51987654321"})
    message_type: str = Field(default="text", max_length=20, description="Tipo de entrada: text o audio", json_schema_extra={"example": "text"})
    body_text: Optional[str] = Field(default=None, max_length=500, description="Texto enviado en la consulta")
    media_url: Optional[str] = Field(default=None, max_length=500, description="URL del archivo multimedia/audio si aplica")

# --- DTOs de Salida (Response Schemas) ---

class DiagnosticResponseDTO(BaseModel):
    similitud_rag: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Similitud de recuperacion RAG (0-100), independiente de la confianza ML",
    )
    sintoma: str = Field(..., description="Síntoma o consulta ingresada por el usuario")
    falla_predicha: str = Field(..., description="Falla vehicular estimada por el modelo ML")
    confianza: float = Field(..., description="Porcentaje de confianza del diagnóstico (0-100)", json_schema_extra={"example": 95.5})
    requiere_revision_humana: bool = Field(default=False, description="Flag que indica si la confianza es baja y requiere mecánico")
    procedimiento_tecnico: Optional[str] = Field(default=None, description="Pasos de reparación recuperados del manual técnico vía RAG")
    respuesta_explicativa: Optional[str] = Field(default=None, description="Respuesta completa sintetizada por Gemini o plantilla de 3 secciones")
    tiempo_respuesta_ms: float = Field(..., description="Tiempo total de procesamiento en milisegundos")

class HealthCheckDTO(BaseModel):
    status: str = "healthy"
    app_name: str
    version: str

# Aliases de compatibilidad directa
ConsultaDiagnostico = SymptomRequestDTO
ResultadoDiagnostico = DiagnosticResponseDTO
