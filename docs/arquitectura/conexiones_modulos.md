# Conexiones entre los módulos

## Vista general

```mermaid
flowchart LR
    WA[WhatsApp Meta o Twilio] -->|Webhook HTTPS| WAI[Interfaz WhatsApp]
    FE[Frontend React] -->|REST /api/v1| API[Interfaz FastAPI]
    WAI --> APP[Casos de uso]
    API --> APP
    APP --> DOM[Dominio vehicular]
    APP --> PORTS[Puertos]
    PORTS --> DB[(PostgreSQL)]
    PORTS --> CACHE[(Redis)]
    PORTS --> ML[Clasificador ML]
    PORTS --> RAG[Motor RAG / FAISS]
    PORTS --> LLM[Gemini]
    APP -->|respuesta| WAI
    WAI --> WA
```

## Flujo de un diagnóstico

```mermaid
sequenceDiagram
    actor U as Usuario
    participant C as WhatsApp o frontend
    participant I as Interfaces
    participant A as GestorDiagnostico
    participant M as Modelo ML
    participant R as RAG
    participant G as Gemini
    participant D as PostgreSQL

    U->>C: Envía síntomas y datos del vehículo
    C->>I: Webhook o petición REST
    I->>A: DTO o parámetros validados
    A->>M: Clasifica la posible falla
    M-->>A: Categoría y confianza
    A->>R: Recupera contexto técnico
    R-->>A: Fragmentos y fuente
    A->>G: Solicita una respuesta estructurada
    G-->>A: Orientación conversacional
    A->>D: Guarda diagnóstico y trazabilidad
    A-->>I: Resultado
    I-->>C: Respuesta
    C-->>U: Hipótesis y comprobaciones seguras
```

Machine Learning propone una clasificación; RAG aporta evidencia recuperada;
Gemini redacta y organiza la respuesta. El gestor de diagnóstico coordina los
tres y conserva las reglas de seguridad. Ninguno reemplaza la validación física
del mecánico.

## Ubicación de las conexiones

| Responsabilidad | Punto de entrada canónico |
| --- | --- |
| Cliente HTTP del frontend | `frontend/src/shared/api/` |
| Contratos compartidos del frontend | `frontend/src/shared/types/` |
| Caso de uso de diagnóstico | `backend/src/application/services/` |
| Cola y límites de Gemini | `backend/src/application/jobs/` |
| Canal WhatsApp | `backend/src/interfaces/messaging/whatsapp/` |
| Adaptador ML | `backend/src/infrastructure/ml/` |
| Adaptador RAG | `backend/src/infrastructure/rag/` |
| PostgreSQL y repositorios | `backend/src/infrastructure/database/` |
| Artefactos ML/RAG | `machine_learning/` |
| PostgreSQL para despliegue | `infrastructure/database/postgresql/` |

Las claves se cargan desde variables de entorno centralizadas por
`backend/src/config.py`; `.env.example` documenta los nombres y `.env` no debe
versionarse.
