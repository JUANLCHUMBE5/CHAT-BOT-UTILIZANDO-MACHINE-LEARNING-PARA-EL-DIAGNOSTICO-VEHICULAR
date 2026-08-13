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
