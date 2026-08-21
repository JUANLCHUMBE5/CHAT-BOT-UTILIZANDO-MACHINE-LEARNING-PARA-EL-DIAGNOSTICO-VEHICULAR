# Estructura profesional del proyecto

CarBot utiliza un monorepo con responsabilidades separadas:

- `backend/`: API, negocio, persistencia, migraciones y pruebas Python.
- `frontend/`: aplicación React y contratos TypeScript.
- `machine_learning/`: datasets, corpus RAG, modelos y entrenamiento.
- `infrastructure/`: recursos operativos de PostgreSQL.
- `docs/`: documentación técnica y académica.
- `scripts/`: lanzadores y verificaciones que coordinan el monorepo.

```text
CHAT_BOT_MACHINLEARNING/
├── backend/
│   ├── src/{core,interfaces,infrastructure}/
│   ├── scripts/diagnostics/
│   ├── tests/performance/
│   └── alembic/
├── frontend/
│   ├── src/{components,hooks,services,types,utils}/
│   └── tests/harness/
├── machine_learning/{data,manuals,models,training}/
├── infrastructure/database/postgresql/
├── scripts/
├── docs/{arquitectura,operacion,proyecto}/
├── docker-compose.yml
└── README.md
```

Los archivos de configuración, gobierno y arranque permanecen en la raíz por
convención: `.env.example`, `.gitignore`, `docker-compose.yml`, `README.md`,
`CONTRIBUTING.md`, `SECURITY.md` e `iniciar_carbot.cmd`.

## Reglas de dependencia

1. Las interfaces del backend pueden depender del núcleo, no al contrario.
2. Los adaptadores de infraestructura implementan las necesidades del núcleo.
3. El frontend consume contratos HTTP y no importa código del backend.
4. Entrenamiento produce artefactos en `machine_learning/models/`; el backend solo los consume.
5. La configuración externa se centraliza en `backend/src/config.py` y se documenta en `.env.example`.

El detalle de integración está en `docs/arquitectura/conexiones_modulos.md`.
