"""Módulo seguro para la carga de credenciales desde AWS Secrets Manager en producción."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from src.core.logger import logger


def cargar_secretos_aws(
    secret_name: Optional[str] = None, region_name: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Carga de forma segura los secretos desde AWS Secrets Manager para producción (AWS ECS / App Runner).
    Si no está disponible boto3 o no se encuentra en AWS, retorna un diccionario vacío sin fallar en local.
    """
    nombre = secret_name or os.getenv("AWS_SECRETS_NAME", "carbot/production/credentials")
    
    # Evitar llamadas de red en local/desarrollo a menos que esté explícitamente configurado
    if os.getenv("ENVIRONMENT", "development").lower() == "development" and not os.getenv("FORCE_AWS_SECRETS"):
        return {}

    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("secretsmanager", region_name=region_name)
        response = client.get_secret_value(SecretId=nombre)
        secret_string = response.get("SecretString", "{}")
        secretos = json.loads(secret_string)
        logger.info(f"[AWS Secrets Manager] Secretos cargados exitosamente desde '{nombre}'.")
        return secretos
    except ImportError:
        logger.debug("[AWS Secrets Manager] Boto3 no está instalado en este entorno.")
        return {}
    except Exception as e:
        logger.warning(f"[AWS Secrets Manager] No se pudo cargar el secreto '{nombre}': {e}")
        return {}
