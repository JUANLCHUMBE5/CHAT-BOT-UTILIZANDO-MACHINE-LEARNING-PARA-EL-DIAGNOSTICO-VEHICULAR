"""Modelos de datos y DTOs para la cola de procesamiento asíncrono de Gemini."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable, List, Optional

from src.config import settings

# Costo de WhatsApp Meta en ventana de servicio (24h) = $0.00
COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))


@dataclass
class SolicitudGeminiEncolada:
    """Representa una solicitud de diagnóstico vehicular encolada para procesamiento."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_ingreso: float = field(default_factory=time.time)
    sintoma: str = ""
    diagnostico_ml: str = ""
    confianza_ml: float = 0.0
    contexto_manual: str = ""
    titulo_manual: str = ""
    tipo_consulta: str = "diagnostico"
    requiere_revision_humana: bool = False
    predicciones_ml: List[dict] = field(default_factory=list)
    callback_completado: Optional[Callable] = None
    futuro_resultado: Optional[Any] = None

    # Contexto para persistencia en DB y notificación WhatsApp
    diagnostico_id: Optional[str] = None
    remitente: Optional[str] = None
    taller_id: Optional[str] = None
    usuario_id: Optional[str] = None
    conversacion_id: Optional[str] = None
    placa: Optional[str] = None
    marca_modelo: Optional[str] = None

    # Proveedor de entrega y referencias de mensaje
    proveedor: str = "meta"  # "meta" | "twilio" | "api"
    mensaje_inicial_id: Optional[str] = None
    mensaje_salida_preliminar_id: Optional[str] = None
