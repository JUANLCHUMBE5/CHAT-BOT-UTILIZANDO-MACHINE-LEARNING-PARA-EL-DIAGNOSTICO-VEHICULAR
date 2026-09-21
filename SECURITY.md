# Política de seguridad

## Secretos

- Nunca confirme `.env`, tokens de Meta/Twilio, claves JWT ni credenciales de PostgreSQL.
- Producción debe inyectar secretos mediante el proveedor de despliegue o AWS Secrets Manager.
- `JWT_SECRET_KEY` y `PRIVACY_SECRET_KEY` deben tener al menos 32 caracteres aleatorios.
- Rote inmediatamente cualquier secreto expuesto y revise el historial de Git.

## Reporte de vulnerabilidades

No publique credenciales ni detalles explotables en un issue público. Comuníquese de forma privada con los responsables del proyecto y adjunte pasos mínimos de reproducción, impacto y versión afectada.

## Datos sensibles

Los números telefónicos y placas deben persistirse anonimizados. Los datasets operativos y las evidencias externas privadas no deben añadirse al repositorio.

## Sesiones web

- El access token se conserva únicamente en memoria del frontend.
- El refresh token se entrega mediante cookie `HttpOnly`, `Secure` en producción
  y `SameSite=lax` o `strict`.
- Cada refresh token es de un solo uso; su reutilización invalida la renovación.
- En producción configure `LEGACY_REFRESH_TOKEN_BODY=false` y Redis mediante
  `RATE_LIMIT_STORAGE_URI` para compartir revocaciones y límites entre workers.

## Endurecimiento de producción

- Configure `TRUSTED_HOSTS` y orígenes CORS explícitos.
- Mantenga `EXPOSE_HEALTH_DETAILS=false`.
- Configure los SHA-256 de modelo y vectorizador antes de cargar archivos
  `joblib`, que nunca deben proceder de una fuente no verificada.
- Termine TLS en el proxy y conserve HSTS y los encabezados defensivos.
- Ejecute `pip-audit`, `npm audit`, Ruff Security y Gitleaks en cada cambio.

## Inteligencia artificial

El contenido del usuario y del corpus RAG se trata como dato no confiable. Se
limita su tamaño, se delimitan las instrucciones, se redactan teléfonos y placas
antes de Gemini y se limita la salida. Ninguna respuesta del modelo autoriza una
reparación sin validación física.
