# Explicación de Base de Datos y Arquitectura de Software
## Tesis: Chatbot de Diagnóstico Vehicular Híbrido

## 1. ¿Qué almacenamiento utiliza el sistema?

El proyecto utiliza una estrategia de persistencia híbrida, porque los datos de entrenamiento y los datos operacionales tienen necesidades diferentes.

### PostgreSQL: información operacional

PostgreSQL conserva los registros que necesitan integridad, relaciones, concurrencia y trazabilidad:

- Talleres y usuarios mecánicos autorizados.
- Vehículos registrados.
- Conversaciones y mensajes de WhatsApp.
- Diagnósticos e hipótesis confirmadas o descartadas.
- Consumo y costo estimado de APIs.
- Auditoría de acciones importantes.

SQLAlchemy 2.0 implementa el mapeo objeto-relacional y el pool asíncrono de conexiones. Alembic controla las versiones del esquema para reproducirlo en desarrollo, pruebas y posteriormente en Amazon RDS.

### Archivos especializados: entrenamiento y RAG

- `machine_learning/data/dataset_sintomas.csv`: dataset versionable utilizado para entrenar y evaluar el clasificador.
- `machine_learning/manuals/manual_procedimientos.txt`: corpus técnico utilizado por el motor RAG local.
- `machine_learning/models/*.pkl`: artefactos producidos por el entrenamiento; se cargan en memoria para inferencia.

Los CSV no funcionan como sustituto de PostgreSQL. PostgreSQL atiende las operaciones concurrentes del chatbot; los archivos mantienen artefactos reproducibles de ciencia de datos.

## 2. ¿Qué arquitectura de software utiliza?

El proyecto implementa una arquitectura modular por capas:

1. **Interfaces (`backend/src/interfaces/`)**: recibe webhooks y peticiones HTTP.
2. **Core (`backend/src/core/`)**: coordina reglas y flujo del diagnóstico.
3. **Infraestructura (`backend/src/infrastructure/`)**: adapta ML, RAG, PostgreSQL y servicios externos.
4. **Persistencia (`backend/src/infrastructure/database/`)**: contiene conexión, modelos y sesiones SQLAlchemy; Alembic mantiene el esquema.

El flujo inteligente conserva tres componentes complementarios:

```text
Mensaje del mecánico
        ↓
Clasificación ML
        ↓
Recuperación RAG
        ↓
Síntesis explicativa LLM o fallback local
        ↓
Registro PostgreSQL y respuesta por WhatsApp
```

## 3. Respuesta recomendada ante el jurado

> El sistema utiliza una arquitectura modular por capas que separa la interfaz de WhatsApp, la lógica del diagnóstico y los adaptadores de infraestructura. La persistencia es híbrida: PostgreSQL registra de forma relacional y trazable los talleres, mecánicos, vehículos, conversaciones y diagnósticos; mientras que los archivos CSV, manuales y modelos binarios se conservan como artefactos especializados de Machine Learning y RAG. SQLAlchemy administra el acceso asíncrono y Alembic garantiza que el mismo esquema pueda reproducirse localmente y en Amazon RDS.

