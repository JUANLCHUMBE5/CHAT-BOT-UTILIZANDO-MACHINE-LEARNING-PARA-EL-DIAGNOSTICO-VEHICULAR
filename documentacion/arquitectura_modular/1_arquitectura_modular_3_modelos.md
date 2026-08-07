# Arquitectura Modular por Capas y Sub-sistema Tripartito de IA (ML + RAG + LLM)

## 1. Visión General de la Arquitectura
El sistema de **Chatbot Vehicular para Diagnóstico Mecánico** está diseñado bajo una **Arquitectura Modular por Capas (Layered Architecture)** desacoplada. Esta estructura garantiza mantenibilidad, escalabilidad e independencia entre la interfaz conversacional, la lógica de negocio, los motores de Inteligencia Artificial y el almacenamiento persistente en PostgreSQL.

```mermaid
graph TD
    A[Capa de Presentación: WhatsApp Cloud API / FastAPI Webhook] --> B[Capa de Aplicación: WebhookService & GestorDiagnostico]
    B --> C[Capa de Inteligencia Artificial: Sub-sistema Tripartito]
    C --> C1[1. Módulo ML: Clasificador TF-IDF + Random Forest]
    C --> C2[2. Módulo RAG: Búsqueda Semántica FAISS en Manuales]
    C --> C3[3. Módulo LLM: Gemini (gemini-3.5-flash-lite) Sintetizador]
    C3 -->|Fallback de Emergencia| C4[Modo Degradado: diagnostico_degradado_ml_rag]
    B --> D[Capa de Persistencia: PostgreSQL 16 + Repositorios SQLAlchemy Async]
```

---

## 2. Flujo de Ejecución Tripartito Secuencial

En cada consulta de diagnóstico vehicular, los 3 modelos se ejecutan de forma coordinada:

```
Mensaje del Mecánico (WhatsApp)
        ↓
Normalización de Jerga Peruana
        ↓
1. ML predice la falla vehicular y calcula el porcentaje de confianza
        ↓
2. RAG recupera el procedimiento de reparación del manual de taller indexado
        ↓
3. Gemini recibe: Síntoma + Predicción ML + Manual RAG
        ↓
Gemini sintetiza la explicación técnica estructurada en 3 secciones:
   🛠️ 1. Posible Falla Vehicular
   📖 2. Procedimiento Técnico de Reparación
   ⏱️ 3. Tiempo Estimado y Gravedad
        ↓
PostgreSQL guarda la conversación, diagnóstico, hipótesis y consumo de API
        ↓
Respuesta final enviada por WhatsApp al mecánico
```

---

## 3. Descripción Detallada de las 4 Capas del Sistema

### Capa 1: Capa de Presentación (Presentation Layer)
- **Ubicación en Código**: `src/interfaces/api/v1/endpoints/webhook.py`, `src/interfaces/api/v1/router.py`, `main.py`
- **Función**: Maneja la interacción directa con el usuario final y la API de Meta / WhatsApp.
- **Componentes principales**:
  - **Webhook WhatsApp (`POST /webhook`)**: Recibe notificaciones HTTP asíncronas de Meta con verificación HMAC-SHA256.
  - **Deduplicación Inmediata**: Detecta `meta_message_id` para evitar procesar mensajes duplicados de reintentos de Meta.
  - **Respuesta 200 OK en < 500ms**: Responde inmediatamente a Meta para cumplir con el SLA de entrega.

### Capa 2: Capa de Aplicación (Application Layer)
- **Ubicación en Código**: `src/core/services/webhook_service.py`, `src/core/gestor_diagnostico.py`, `src/core/gemini_queue.py`, `src/core/audio_processor.py`
- **Función**: Orquesta el flujo de negocio del taller, autenticación del mecánico y cola de procesamiento.
- **Componentes principales**:
  - **`WebhookService`**: Transacciones de base de datos, deduplicación, validación de autorización y persistencia.
  - **`GestorDiagnostico`**: Coordina el pipeline ML → RAG → Gemini y gestiona las sesiones multiturno.
  - **`GeminiRateLimiter`**: Controla el límite de **12 solicitudes por minuto** hacia la API de Google Gemini para prevenir sobrecostos.
  - **Modo Degradado (`diagnostico_degradado_ml_rag`)**: Cuando la API de Gemini no está disponible o se alcanza la cuota de tasa, el sistema genera la respuesta a partir de plantillas locales enriquecidas de ML+RAG y lo marca explícitamente como diagnóstico degradado.

### Capa 3: Capa de Inteligencia Artificial (Sub-sistema de 3 Modelos)
- **Ubicación en Código**: `src/infrastructure/modelo_ml.py`, `src/infrastructure/motor_rag.py`
- **Función**: Ejecuta las tareas cognitivas complementarias:

#### 🤖 Modelo 1: Machine Learning Supervisado (Clasificación Predictiva)
- **Tecnología**: Scikit-Learn (`RandomForestClassifier` + `TfidfVectorizer`).
- **Función**: Analiza la descripción textual del síntoma ingresado por el mecánico y predice la categoría exacta de la falla.
- **Salida**: Etiqueta predictiva de la falla vehicular y nivel de confianza numérico (0.0 a 1.0).

#### 📚 Modelo 2: RAG - Retrieval-Augmented Generation (Recuperación Semántica)
- **Tecnología**: FAISS Index / TF-IDF Vectorizer sobre `manuales_taller/manual_procedimientos.txt`.
- **Función**: Consulta la base de conocimiento interna del taller para extraer el procedimiento exacto de inspección y reparación.
- **Salida**: Fragmento técnico con pasos de diagnóstico y comprobación.

#### 🧠 Modelo 3: LLM - Large Language Model (Sintetizador Conversacional)
- **Tecnología**: Google Gemini (`gemini-3.5-flash-lite` API).
- **Función**: Toma el diagnóstico predictivo del **Modelo ML** y el procedimiento técnico del **Modelo RAG**, y los sintetiza en una explicación técnica clara y estructurada en 3 secciones para WhatsApp.

### Capa 4: Capa de Datos y Persistencia (Data Layer)
- **Ubicación en Código**: `src/infrastructure/database/repositories/`, `src/infrastructure/database/models/`, `alembic/`.
- **Función**: PostgreSQL 16 gestiona talleres, mecánicos autorizados (mediante `whatsapp_hash`), vehículos (mediante `placa_hash`), conversaciones activas de 24 horas, mensajes, diagnósticos, hipótesis técnicas y registro de costos en `uso_api`.

---

## 4. Beneficios para la Tesis y Evaluación
1. **Precisión Predictiva y Rigor Técnico**: La combinación de ML (para clasificación) y RAG (para procedimientos) evita alucinaciones del LLM.
2. **Cero Costo en Pruebas**: Durante la ejecución de pruebas automatizadas, Gemini está mockeado internamente, garantizando $0.00 de gasto en CI/CD.
3. **Resiliencia Operativa**: La presencia del modo degradado `diagnostico_degradado_ml_rag` asegura que el taller nunca quede inoperativo.
