"""Módulo de procesamiento de contingencia para Webhook sin base de datos activa."""

from __future__ import annotations

import time
from typing import Any, Optional

from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.services.whatsapp_provider import whatsapp_provider_service


class OfflineProcessor:
    """Procesa consultas en memoria de forma segura cuando PostgreSQL está inactivo."""

    @staticmethod
    async def procesar_sin_base_datos(
        gestor: GestorDiagnostico,
        remitente: str,
        tipo_mensaje: str,
        texto_cliente: str,
        audio_id: str,
        placa: str,
        marca_modelo: str,
        session_id: Optional[str],
        proveedor: str = "meta",
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        if tipo_mensaje == "audio":
            respuesta = (
                "No puedo procesar audios sin persistencia y control de cuota activos. "
                "Envia el sintoma por texto para continuar de forma segura."
            )
            diag_ml = "Audio no procesado"
            conf = 0.0
        else:
            dto = gestor.procesar_consulta_texto(
                texto_usuario=texto_cliente,
                placa=placa,
                marca_modelo=marca_modelo,
                session_id=session_id or remitente,
                proveedor=proveedor,
                slot_gemini_preconcedido=False,
            )
            respuesta = dto.respuesta_texto
            diag_ml = dto.diagnostico_ml
            conf = dto.confianza_ml

        await whatsapp_provider_service.enviar(proveedor, remitente, respuesta)
        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "status": "completado_offline",
            "diagnostico_ml": diag_ml,
            "confianza": conf,
            "tiempo_ms": round(elapsed, 2),
        }
