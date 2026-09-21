# Estructura profesional del proyecto

CarBot es un **monorepo con un monolito modular por capas**. El frontend se
organiza por funcionalidades y el backend combina capas, Clean Architecture y
puertos/adaptadores. Esta descripción no implica microservicios.

```text
CHAT_BOT_MACHINLEARNING/
├── backend/
│   ├── src/
│   │   ├── domain/                 # reglas y conceptos del negocio
│   │   ├── application/            # casos de uso, puertos y trabajos
│   │   ├── interfaces/             # API REST y canal WhatsApp
│   │   └── infrastructure/         # base de datos, ML, RAG y proveedores
│   ├── alembic/                    # migraciones PostgreSQL
│   └── tests/
├── frontend/
│   ├── src/features/               # autenticación, panel, gestión y proyecto
│   ├── src/shared/                 # API, layout, navegación y tipos comunes
│   └── src/{components,hooks,services,types,utils}/  # transición compatible
├── machine_learning/
│   ├── data/                       # datasets y reportes de calidad
│   ├── manuals/                    # fuentes del corpus RAG
│   ├── models/                     # artefactos y métricas
│   └── training/                   # entrenamiento y evaluación
├── infrastructure/database/postgresql/ # recursos operativos de despliegue
├── scripts/                        # arranque y verificación del monorepo
├── docs/                           # documentación técnica y académica
└── docker-compose.yml
```

## Reglas de dependencia

1. `domain` no debe depender de FastAPI, PostgreSQL, Gemini ni WhatsApp.
2. `application` coordina el dominio y declara los puertos que necesita.
3. `interfaces` transforma HTTP o mensajes en llamadas a casos de uso.
4. `infrastructure` implementa persistencia y conexiones con ML, RAG y APIs.
5. El frontend consume contratos HTTP; nunca importa Python ni accede a la base.
6. `machine_learning/` produce artefactos; el backend solamente los consume.
7. WhatsApp es un canal del sistema, no una copia independiente del chatbot.

## Compatibilidad durante la reorganización

La estructura anterior se conserva internamente mientras se migra por partes.
Los puntos de entrada nuevos reexportan las implementaciones existentes, por lo
que no cambian las URLs, DTOs, modelos, artefactos ni comandos. Una ruta antigua
solo debe retirarse después de migrar sus consumidores y ejecutar toda la suite.

Los archivos de configuración y gobierno permanecen en la raíz por convención:
`.env.example`, `.gitignore`, `docker-compose.yml`, `README.md`,
`CONTRIBUTING.md`, `SECURITY.md` e `iniciar_carbot.cmd`.

El flujo entre módulos está detallado en
[`conexiones_modulos.md`](conexiones_modulos.md).
