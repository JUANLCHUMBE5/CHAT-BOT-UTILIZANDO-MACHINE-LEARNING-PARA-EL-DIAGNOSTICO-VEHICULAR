"""Flujo de respuesta para contactos con rol de cliente en WhatsApp."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.security import cifrar_texto_reversible
from src.core.services.cliente_service import ClienteService
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository

COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))


class ClientWorkflow:
    """Genera y deja en el outbox la respuesta dirigida a un cliente."""

    @staticmethod
    async def procesar_y_persistir(
        session: AsyncSession,
        usuario: Any,
        conversacion: Any,
        texto_cliente: str,
        meta_message_id: str,
        proveedor: str,
        remitente: str,
    ) -> dict[str, Any]:
        respuesta_texto = await ClienteService(session).procesar_mensaje_cliente(
            usuario=usuario,
            taller=usuario.taller,
            texto_usuario=texto_cliente,
        )
        await MensajeRepository(session).crear_mensaje(
            conversacion_id=conversacion.id,
            taller_id=usuario.taller_id,
            usuario_id=usuario.id,
            meta_message_id=f"out_{meta_message_id or uuid.uuid4()}",
            direccion="salida",
            tipo="texto",
            texto=respuesta_texto,
            categoria_cobro="servicio",
            estado_entrega="pendiente",
            costo_estimado=(
                Decimal(str(settings.twilio_message_price_usd))
                if proveedor == "twilio"
                else COSTO_META_MENSAJE_SERVICIO_USD
            ),
            moneda="USD",
            proveedor=proveedor,
            destinatario_cifrado=cifrar_texto_reversible(remitente),
            disponible_entrega_en=datetime.now(timezone.utc),
        )
        await session.commit()
        return {
            "status": "completado_cliente",
            "conversacion_id": str(conversacion.id),
            "respuesta": respuesta_texto,
        }
