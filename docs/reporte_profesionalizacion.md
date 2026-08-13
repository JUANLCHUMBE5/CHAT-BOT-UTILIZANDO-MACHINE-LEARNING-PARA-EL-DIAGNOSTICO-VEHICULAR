# Reporte de profesionalización de CarBot

Fecha: 11 de agosto de 2026

## Objetivo

Convertir el repositorio existente en un monorepo mantenible, seguro y verificable, conservando la funcionalidad y los cambios locales previos.

## Cambios aplicados

### Arquitectura

- Separación física entre `frontend`, `backend`, `machine_learning`, `infrastructure`, `docs` y scripts coordinadores.
- Corrección de rutas locales, Docker, CI, Alembic, modelos y datasets.
- Documento de reglas de dependencia en `docs/arquitectura/estructura_proyecto.md`.

### Configuración y seguridad

- Configuración tipada y centralizada en `backend/src/config.py`.
- Nombres internos normalizados en `snake_case`.
- Variables canónicas de Meta: `META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID`, `META_VERIFY_TOKEN` y `META_APP_SECRET`.
- Compatibilidad temporal con nombres históricos para no romper instalaciones existentes.
- Eliminación de secretos predeterminados del código.
- Validación estricta de producción para JWT, privacidad, PostgreSQL, mensajería, rate limiting y CORS.
- CORS limitado a orígenes configurables; ya no se permite `*` por defecto.
- `.env.example` actualizado y `.env` local migrado sin exponer valores.
- Claves locales JWT y de privacidad generadas criptográficamente para sustituir fallbacks inseguros.

### Backend

- Eliminación de los alias heredados de configuración en mayúsculas.
- Nombres explícitos para Meta, audio y autenticación local.
- Imports ordenados automáticamente y Ruff ampliado para verificarlos.
- Pruebas aisladas con configuración determinista y secretos exclusivos de test.

### Frontend

- TypeScript en modo estricto.
- Separación de modelos de dominio (`types/domain.ts`) y contratos HTTP (`types/api.ts`).
- Barrel público en `types/index.ts`.
- Eliminación de todos los `any` explícitos.
- Manejo común de errores desconocidos mediante `utils/errors.ts`.
- Roles reutilizables con el tipo `MecanicoRol`.

### Estándares del repositorio

- `.editorconfig` para formato consistente.
- `.gitattributes` para UTF-8, finales de línea y binarios.
- `CONTRIBUTING.md` con flujo de contribución y convenciones.
- `SECURITY.md` con reglas para secretos y datos sensibles.
- `scripts/verificar_proyecto.ps1` como verificación integral local.
- README actualizado con estructura, variables canónicas y comandos vigentes.

## Validación

- Ruff: aprobado.
- Compilación Python: aprobada.
- Pytest: 100 pruebas aprobadas; 41 integraciones omitidas cuando sus servicios no están disponibles.
- Oxlint: aprobado.
- TypeScript y build Vite: aprobados.
- Alembic: una única revisión `head` válida.
- Auditoría de codificación: cero archivos UTF-8 dañados.
- Auditoría de entorno: cero variables utilizadas sin documentar.
- Docker Compose: rutas actualizadas; no se ejecutó el CLI porque Docker no está instalado en el equipo.

## Compatibilidad

Los contratos JSON externos conservan `snake_case` para coincidir con FastAPI. Las variables de entorno antiguas siguen siendo aceptadas temporalmente, pero toda instalación nueva debe usar los nombres documentados en `.env.example`.
