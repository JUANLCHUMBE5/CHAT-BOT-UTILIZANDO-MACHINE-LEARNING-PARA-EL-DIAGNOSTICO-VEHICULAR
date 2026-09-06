# Guía del repositorio

## Estructura del proyecto y organización de módulos

CarBot es un sistema por capas construido con React y FastAPI. El backend se encuentra en `backend/src/`: mantenga los casos de uso en `application/`, las reglas de negocio y DTOs en sus módulos actuales, la persistencia y adaptadores externos en `infrastructure/`, y los contratos HTTP en `interfaces/`. Las pruebas están en `backend/tests/` y las migraciones Alembic en `backend/alembic/versions/`. El cliente React/Vite está en `frontend/src/`; sus pruebas se ubican en `frontend/tests/harness/`. Use `machine_learning/` para entrenamiento y artefactos ML, `infrastructure/` para recursos de despliegue, `scripts/` para automatizaciones y `docs/` para documentación técnica.

## Comandos de desarrollo, compilación y pruebas

- `./iniciar_carbot.cmd`: inicia verificaciones de PostgreSQL, API, worker de colas, panel Vite y túnel de WhatsApp en Windows.
- `./scripts/verificar_proyecto.ps1`: ejecuta la validación completa: Ruff, Pytest, Oxlint, compilación TypeScript y pruebas del frontend.
- `cd backend; ../.venv/Scripts/python.exe -m alembic upgrade head`: aplica las migraciones de base de datos.
- `cd backend; ../.venv/Scripts/python.exe -m pytest -q`: ejecuta únicamente las pruebas del backend.
- `cd frontend; npm ci; npm run verify`: instala dependencias bloqueadas y valida el frontend.
- `docker compose up --build`: levanta API, worker, PostgreSQL y Redis en contenedores.

## Estilo de código y convenciones de nombres

Respete `.editorconfig`: UTF-8, salto de línea final y cuatro espacios en Python. Ruff controla importaciones y errores esenciales, con un límite de 110 caracteres. Use `snake_case` para funciones y variables de Python, `PascalCase` para clases y anotaciones de tipo en interfaces públicas. En TypeScript use dos espacios, `camelCase` internamente, `PascalCase` para componentes y tipos, y `snake_case` solo al reproducir contratos JSON. Las variables de entorno deben usar `UPPER_SNAKE_CASE` y documentarse en `.env.example`.

## Criterios para las pruebas

Pytest descubre archivos `test_*.py` dentro de `backend/tests/`. Marque con `real_gemini` las pruebas externas que consuman cuota. La cobertura de `backend/src` debe mantenerse en 55 % o más. Agregue regresiones para estados de cola, aislamiento entre talleres, autenticación y rutas de error. Los cambios del frontend deben superar `npm run test:harness`.

## Commits y pull requests

El historial sigue Conventional Commits, normalmente en español: `feat: ...`, `fix(carbot): ...`, `refactor: ...` y `docs: ...`. Mantenga cada commit enfocado. El pull request debe resumir el cambio, indicar las validaciones ejecutadas, advertir migraciones o nuevas variables, vincular la incidencia e incluir capturas cuando modifique la interfaz. Nunca confirme `.env`, credenciales, datos operativos, cachés generadas ni modelos binarios sin revisión.
