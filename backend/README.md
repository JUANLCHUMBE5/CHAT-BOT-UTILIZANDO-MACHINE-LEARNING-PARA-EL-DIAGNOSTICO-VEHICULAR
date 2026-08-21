# Backend

API y lógica de aplicación de CarBot.

## Organización

- `src/core/`: reglas de negocio, seguridad y servicios de aplicación.
- `src/interfaces/api/v1/`: contratos HTTP, endpoints y webhook.
- `src/infrastructure/`: adaptadores PostgreSQL, ML, RAG, secretos y contenedor.
- `alembic/`: migraciones versionadas de PostgreSQL.
- `scripts/`: administración, mantenimiento y diagnóstico operativo.
- `tests/`: pruebas unitarias, integración, seguridad y rendimiento.

El punto de entrada es `main.py`. El backend consume los artefactos de
`../machine_learning/` mediante rutas centralizadas en `src/config.py`.

