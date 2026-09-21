# 📘 GUÍA TÉCNICA MAESTRA: PREPARACIÓN PARA ENTREVISTA CON LÍDER TÉCNICO Y DEFENSA DE TESIS

> **Proyecto:** CarBot — Chatbot con Machine Learning, RAG y FastAPI para el Diagnóstico Vehicular en Talleres Mecánicos de Carabayllo, 2026.
> **Desarrollador Principal & Arquitecto:** Juan Joel Leon Chumbe
> **Coautora (Investigación Académica & Campo):** Luisa Leonor Poma Cataño
> **Documento Word Generado:** [`DOCUMENTACION_PREGUNTAS_LIDER_TECNICO_CARBOT.docx`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/DOCUMENTACION_PREGUNTAS_LIDER_TECNICO_CARBOT.docx)

---

## 🖼️ DIAGRAMAS VISUALES DEL SISTEMA (LISTOS PARA PRESENTACIÓN)

1. 📊 **[Diagrama 1: Flujo End-to-End de una Petición](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/graficas/diagrama_1_flujo_end_to_end.jpg)**
   *(WhatsApp → Meta Webhook → FastAPI + DTOs → ML SVM & RAG FAISS → Gemini LLM → PostgreSQL → WhatsApp + Panel React)*

2. 🧠 **[Diagrama 2: Arquitectura de Inteligencia Híbrida XAI](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/graficas/diagrama_2_ia_hibrida_xai.jpg)**
   *(Machine Learning físico <15ms + RAG Grounding + Gemini Síntesis Conversacional + Fallback Determinístico)*

3. 🏛️ **[Diagrama 3: Arquitectura Modular por Capas](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/graficas/diagrama_3_arquitectura_modular_capas.jpg)**
   *(Frontend React 19 con Custom Hooks → Interfaces & DTOs FastAPI → Domain Core → Infrastructure PostgreSQL/ML/FAISS)*

---

## 📌 BLOQUE 0: APORTE INDIVIDUAL, ROLES Y ELEVATOR PITCH

### Pregunta 0.1: ¿Qué desarrollé yo exactamente y qué hizo mi compañera de tesis?
Esta es la pregunta de mayor peso técnico ante un evaluador o líder de ingeniería. La delimitación debe ser clara, transparente y categórica:

| Dimensión | Mi Aporte Individual (Juan Joel Leon Chumbe)<br>**Desarrollo de Software, Arquitectura & IA** | Aporte de mi Compañera (Luisa Leonor Poma Cataño)<br>**Investigación Académica & Trabajo de Campo** |
| :--- | :--- | :--- |
| **Backend & Arquitectura** | Diseño y construcción completa del backend en **FastAPI** bajo arquitectura modular por capas limpia ([`backend/src/`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/src/)). | Redacción de la justificación teórica, formulación del problema y estado del arte en el informe de tesis. |
| **Frontend & UI** | Desarrollo de la SPA en **React 19 + TypeScript + Vite** con Custom Hooks ([`frontend/src/hooks/`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/frontend/src/hooks/)) y gráficos interactivos con Recharts. | Recopilación de requisitos de usuario mediante encuestas y entrevistas a dueños de talleres en Carabayllo. |
| **Modelado de Datos & DTOs** | Definición de contratos estrictos de datos mediante **DTOs con Pydantic v2** ([`schemas.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/src/interfaces/api/v1/schemas.py)) e interfaces TypeScript. | Elaboración de fichas de recolección de sintomatología e instrumentos de medición O1 (pre-test) y O2 (post-test). |
| **Machine Learning & RAG** | Entrenamiento y calibración de **Linear SVM con TF-IDF**, análisis acústico **FFT**, e implementación de **RAG con FAISS** ([`motor_rag.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/src/infrastructure/motor_rag.py)). | Consolidación documental de manuales de servicio automotriz en PDF y apoyo en la redacción de anexos. |
| **Integración Cloud & APIs** | Webhook de **WhatsApp Cloud API (Meta)** con validación HMAC y orquestación resiliente de **Google Gemini** con Token Bucket y cola de reintentos. | Coordinación logística en campo para la toma de tiempos tradicionales de diagnóstico en los talleres. |
| **Persistencia & Testing** | Modelado en **PostgreSQL**, ORM asíncrono con **SQLAlchemy + asyncpg**, migraciones **Alembic** y suite de más de **30 pruebas automatizadas en Pytest**. | Tabulación estadística de los resultados de campo y apoyo en la redacción de conclusiones y recomendaciones. |

---

### Pregunta 0.2: ¿Cuál es el Elevator Pitch técnico de CarBot en 60 segundos?
> *"CarBot es un sistema de diagnóstico vehicular híbrido multimodal diseñado para resolver la ambigüedad en la recepción de vehículos en talleres mecánicos.*
> *A diferencia de un chatbot genérico que alucina especificaciones técnicas, CarBot combina tres capas coordinadas:*
> *1. Un clasificador de **Machine Learning supervisado (Calibrated Linear SVM)** que procesa texto coloquial y señales FFT de audio en milisegundos;*
> *2. Un motor **RAG basado en FAISS** que recupera procedimientos exactos desde manuales de taller indexados; y*
> *3. Un **LLM (Google Gemini)** que actúa exclusivamente como capa explicativa bajo 'grounding' estricto.*
> *Todo está orquestado con FastAPI asíncrono, DTOs de Pydantic, PostgreSQL y un panel reactivo en React 19 con TypeScript."*

---

### Pregunta 0.3: ¿Qué decisiones técnicas tomaste tú de forma autónoma?
1. **Inferencia Determinística Híbrida:** Separar la clasificación en ML local + RAG antes de invocar al LLM. Esto reduce los costos de API en más de un 70% y garantiza que el sistema siga operando en modo degradado si la API de Gemini falla.
2. **Contratos Estrictos con DTOs:** Usar DTOs inmutables con Pydantic v2 en el backend e interfaces espejo en TypeScript en el frontend para evitar condiciones de carrera y asegurar tipado estricto en tiempo de compilación y ejecución.
3. **Resiliencia contra Throttling (Rate Limits):** Crear un módulo de Token Bucket (`gemini_queue.py`) y una tabla de cola en PostgreSQL (`trabajos_gemini`) para gestionar el límite de 15 RPM de Gemini sin perder mensajes de WhatsApp.
4. **Custom Hooks en Frontend:** Diseñar `useDiagnosticos`, `useMecanicos` y `useMetricas` para aislar la lógica de estado y llamadas API de los componentes visuales de React.

---

## 🏛️ BLOQUE 1: LENGUAJE, ARQUITECTURA Y ORGANIZACIÓN DEL PROYECTO

### Pregunta 1: ¿Por qué eligieron Python?
1. **Ecosistema de IA y Procesamiento de Señales:** Python centraliza `scikit-learn`, `faiss-cpu`, `scipy` (para FFT de audio) y `joblib` sin necesidad de puentes entre lenguajes.
2. **Rendimiento Asíncrono de FastAPI:** Construido sobre Starlette y Uvicorn (ASGI con uvloop), maneja alta concurrencia en webhooks de WhatsApp con tiempos de respuesta en milisegundos.
3. **Tipado Estricto con Pydantic v2:** Núcleo escrito en Rust que ofrece validación de esquemas JSON a ultra alta velocidad y generación automática de Swagger/OpenAPI.
4. **Carga In-Memory de Modelos:** Permite instanciar el modelo ML y el índice FAISS como Singletons en memoria durante el ciclo de vida de la aplicación.

---

### Pregunta 2: ¿Cómo está estructurado el proyecto y por qué arquitectura modular por capas?
El proyecto sigue una arquitectura monorepo desacoplada inspirada en Clean Architecture:
- **`backend/src/interfaces/api/v1/`**: Capa de presentación/entrada (Endpoints REST y Webhook de WhatsApp con esquemas DTOs de Pydantic).
- **`backend/src/core/`**: Capa de dominio (Gestor de diagnósticos, procesador de audio, traductor de jerga peruana, sanitizer contra prompt injection y seguridad).
- **`backend/src/infrastructure/`**: Capa de infraestructura (Modelos SQLAlchemy Async, repositorios PostgreSQL, cliente FAISS, conector ML con joblib y gestor de secretos AWS).
- **`frontend/src/`**: SPA en React 19 + TypeScript + Vite, con separación en `services/`, `hooks/`, `components/` y `types/`.
- **`machine_learning/`**: Espacio aislado para datasets, scripts de entrenamiento, evaluación con validación cruzada y corpus RAG.

---

### Pregunta 3: ¿Qué ventajas aportan los DTOs y los Custom Hooks?
- **DTOs (Data Transfer Objects con Pydantic):**
  - Validación en frontera: Rechazan peticiones maliciosas o incompletas con HTTP 422 antes de tocar el dominio.
  - Inmutabilidad: Evitan que mutaciones accidentales en memoria afecten peticiones concurrentes.
  - Documentación viva: Exportan el esquema JSON exacto para sincronizar con TypeScript.
- **Custom Hooks en React (`useDiagnosticos`, `useMecanicos`, `useMetricas`):**
  - Desacoplamiento: Los componentes de UI solo renderizan; los hooks encapsulan llamadas HTTP, `loading`, `error` y paginación.
  - Reusabilidad: El hook de diagnósticos es compartido entre la tabla de auditoría del administrador y el simulador de chat.

---

### Pregunta 4: ¿Qué librerías usa cada parte del sistema?
Consulte la tabla de librerías en el documento Word o en [`backend/requirements.txt`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/requirements.txt):
- **Backend:** `fastapi`, `uvicorn`, `pydantic`, `SQLAlchemy[asyncio]`, `asyncpg`, `alembic`, `scikit-learn`, `joblib`, `faiss-cpu`, `scipy`, `PyJWT`, `cryptography`, `slowapi`, `redis`, `httpx`.
- **Frontend:** `react 19`, `typescript 6`, `vite 8`, `lucide-react`, `recharts`.
- **Machine Learning:** `scikit-learn` (LinearSVC, CalibratedClassifierCV, TfidfVectorizer), `scipy.fft`, `numpy`, `pandas`, `openpyxl`.

---

## ⚡ BLOQUE 2: FLUJO DE PETICIONES DE INICIO A FIN (E2E)

### Pregunta 5: ¿Cómo fluye una petición de inicio a fin?
```
[ WhatsApp: Mensaje / Audio ]
             │
             ▼
[ Meta Webhook POST /api/v1/webhook/whatsapp ]
             │
             ▼ (Validar HMAC SHA-256)
[ Autenticación & Rol en PostgreSQL (Cliente vs Mecánico) ]
             │
             ├─────────────► Si es Cliente: Devuelve Menú Informativo
             │
             ▼ Si es Mecánico Autorizado:
[ Preprocesamiento: Audio FFT / Sanitizer / Traductor Jerga ]
             │
             ├──────────────────────────┬──────────────────────────┐
             ▼                          ▼                          ▼
   [ Modelo ML SVM ]           [ Motor RAG FAISS ]       [ Extracción Perfil ]
  Predicción de Falla +      Recupera Manual Técnico +     Marca, Modelo, Año
   Confianza Calibrada %        Similitud Coseno %          y Kilometraje
             │                          │                          │
             └──────────────────────────┼──────────────────────────┘
                                        │
                                        ▼
                         [ Orquestador GestorDiagnostico ]
                                        │
                                        ▼
                 [ Gemini Rate Limiter (Token Bucket / Cola) ]
                                        │
                      ┌─────────────────┴─────────────────┐
                      ▼                                   ▼
             (Si hay Cuota / Slot)              (Si Falla / 429 / Timeout)
           [ Prompt Grounding Gemini ]           [ Fallback Técnico Directo ]
             Síntesis XAI en 3 partes              Respuesta ML + RAG local
                      │                                   │
                      └─────────────────┬─────────────────┘
                                        │
                                        ▼
                   [ Persistencia PostgreSQL (SQLAlchemy Async) ]
                                        │
                                        ▼
                 [ Envío WhatsApp vía Meta Graph API + Panel Web ]
```

---

## 🤖 BLOQUE 3: INTELIGENCIA ARTIFICIAL, MACHINE LEARNING Y RAG

### Pregunta 8: ¿Cómo interactúan Machine Learning, RAG y Gemini?
- **Machine Learning (Enrutador de Alta Precisión):** Clasifica la sintomatología en milisegundos dentro de la taxonomía vehicular del taller y emite la probabilidad calibrada.
- **RAG (Validador de Verdad Técnica):** Busca en el índice FAISS el procedimiento real de taller y especificaciones numéricas (torques, holguras).
- **Gemini (Capa Explicativa XAI):** Genera la respuesta en lenguaje natural para WhatsApp formateada en 3 bloques obligatorios: Hipótesis Técnica, Pasos de Comprobación y Advertencias de Seguridad.

---

### Pregunta 9: ¿Cómo está implementado el RAG exactamente?
- **Vectorización:** `TfidfVectorizer` con stop words automotrices en español y n-gramas (1, 2).
- **Indexación:** Vectores normalizados con norma L2 indexados en `faiss.IndexFlatIP` (búsqueda de producto interno / similitud coseno sub-milisegundo).
- **Expansión Semántica:** Diccionario integrado de códigos OBD-II/DTC y jergas (ej. *"cascabeleo"* → *"bujias misfire encendido p0300"*).
- **Metadatos y Auditoría:** Cada procedimiento cuenta con hash SHA-256, fuente OEM, edición y número de página.

---

### Pregunta 10: ¿Por qué Linear SVM con TF-IDF en vez de un LLM comercial directo?
- **Cero Alucinación:** El clasificador supervisado restringe la predicción a categorías válidas del catálogo.
- **Velocidad:** Inferencia menor a 15 ms en CPU estándar sin requerir GPUs.
- **Calibración Estadística:** `CalibratedClassifierCV` permite calcular la probabilidad matemática real para disparar revisiones humanas cuando la confianza es baja (<60%).

---

## 🛡️ BLOQUE 4: RESILIENCIA, GESTIÓN DE APIS Y SEGURIDAD

### Pregunta 14 & 15: ¿Cómo manejan secretos y el Rate Limit 429 de Gemini?
- **Secretos:** Configuración mediante Pydantic Settings (`src/config.py`) y módulo de integración con **AWS Secrets Manager** (`aws_secrets.py`).
- **Control de Cuotas (Token Bucket):** Módulo `gemini_queue.py` que limita el consumo a 15 RPM y calcula tokens por minuto.
- **Cola Persistente:** Tabla `trabajos_gemini` en PostgreSQL para posponer peticiones cuando la cuota está saturada.
- **Degradación Elegante (Graceful Degradation):** Si la API de Google Gemini falla o excede el timeout de 10s, el sistema responde inmediatamente con el diagnóstico de ML + manual RAG sin que el usuario perciba un error.

---

## 📊 BLOQUE 5: TESTING, MÉTRICAS Y VALIDACIÓN DE TESIS

### Pregunta 18: ¿Qué pruebas automatizadas hicieron?
Más de 34 archivos de test en [`backend/tests/`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/tests/) ejecutados con Pytest:
- **Unit Tests:** Validadores de DTOs, transformadas FFT de audio, sanitizer contra prompt injection y hashing de teléfonos.
- **Integration Tests:** Endpoints FastAPI, transacciones SQLAlchemy Async y repositorios.
- **E2E & Concurrencia:** Pruebas de estrés `test_concurrency.py`, `test_m3_stress.py` y resiliencia de colas.

---

### Pregunta 20: ¿Cómo validaron estadísticamente el impacto del chatbot en la tesis?
- **Diseño Metodológico:** Preexperimental con pre-test y post-test ($O_1 - X - O_2$) en 60 casos de diagnóstico en Carabayllo.
- **Prueba Estadística:** Tras verificar normalidad con Shapiro-Wilk, se aplicó la prueba paramétrica **$t$ de Student para muestras relacionadas** ($\alpha = 0.05$).
- **Resultados:** Reducción del tiempo promedio de diagnóstico de **22.5 min a 2.4 min** ($p < 0.001$) e incremento en la completitud de fichas técnicas del **42% al 96.8%**.

---

### Pregunta 21: ¿Cuál fue el problema técnico más difícil y cómo lo resolviste?
> *"El problema más difícil fue la saturación por límites de cuota (HTTP 429) y alta latencia de los LLMs comerciales en un canal de mensajería sincrónico como WhatsApp. Lo resolví implementando un Rate Limiter con Token Bucket, una cola asíncrona persistente en PostgreSQL y un mecanismo de Degradación Elegante (Graceful Degradation) que devuelve diagnósticos certeros basados en ML y RAG local en menos de 200 ms si el LLM no responde."*
