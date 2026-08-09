"""Carga opcional y fail-closed de AWS Secrets Manager antes de crear settings."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("ChatbotVehicular.aws_secrets")

CLAVES_PERMITIDAS = {
    "DATABASE_URL", "GEMINI_API_KEY", "TOKEN_WHATSAPP", "TELEFONO_ID",
    "META_APP_SECRET", "META_VERIFY_TOKEN", "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM", "JWT_SECRET_KEY",
    "PRIVACY_SECRET_KEY", "AUTH_USERNAME", "AUTH_PASSWORD",
    "RATE_LIMIT_STORAGE_URI",
}


def cargar_secretos_aws(secret_name: str, region_name: str) -> dict[str, Any]:
    """Obtiene un JSON; cualquier error es fatal si la integracion fue activada."""
    try:
        import boto3

        cliente = boto3.client("secretsmanager", region_name=region_name)
        respuesta = cliente.get_secret_value(SecretId=secret_name)
        secretos = json.loads(respuesta["SecretString"])
    except Exception as exc:
        raise RuntimeError("No fue posible cargar AWS Secrets Manager.") from exc

    if not isinstance(secretos, dict):
        raise RuntimeError("El secreto de AWS debe ser un objeto JSON.")
    desconocidas = set(secretos) - CLAVES_PERMITIDAS
    if desconocidas:
        raise RuntimeError(
            "El secreto contiene claves no permitidas: " + ", ".join(sorted(desconocidas))
        )
    return secretos


def aplicar_secretos_aws() -> None:
    """Inyecta secretos antes de importar src.config; nunca imprime sus valores."""
    habilitado = os.getenv("AWS_SECRETS_ENABLED", "false").lower() in {
        "1", "true", "yes", "on"
    }
    if not habilitado:
        return

    nombre = os.getenv("AWS_SECRETS_NAME", "").strip()
    region = os.getenv("AWS_REGION", "us-east-1").strip()
    if not nombre:
        raise RuntimeError("AWS_SECRETS_NAME es obligatorio si AWS_SECRETS_ENABLED=true.")

    for clave, valor in cargar_secretos_aws(nombre, region).items():
        os.environ[clave] = str(valor)
    logger.info("Credenciales de produccion cargadas desde AWS Secrets Manager.")
