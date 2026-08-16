# 🚗 Chatbot Híbrido de Diagnóstico Vehicular asistido por Machine Learning, RAG y LLM

> **Proyecto de Tesis:** Sistema inteligente para el diagnóstico preliminar de fallas automotrices, integrando traducción de jerga mecánica peruana, algoritmos de aprendizaje automático, recuperación aumentada de información (RAG) y razonamiento generativo (LLM) con persistencia en PostgreSQL y webhook para WhatsApp.

## Estado tecnico verificado

La descripción consolidada y vigente del sistema está en
[`docs/ESTADO_FINAL_CARBOT.md`](docs/ESTADO_FINAL_CARBOT.md). El índice completo
está en [`docs/INDICE_DOCUMENTACION.md`](docs/INDICE_DOCUMENTACION.md).

- El asistente esta dirigido al mecanico; sus resultados son hipotesis y requieren comprobacion fisica.
- El webhook persiste la entrada antes de confirmar el HTTP 200.
- Las salidas Meta/Twilio usan un outbox PostgreSQL durable con reintentos e identificador externo.
- La cola Gemini y sus cuotas RPM/RPD son persistentes y coordinadas entre workers.
- Los telefonos pendientes quedan cifrados y la privacidad falla de forma cerrada.
- El audio esta desactivado por defecto y, al habilitarse, se descarga y transcribe realmente; no se simula.
- El esquema vigente llega a `20260815_04`: separa confianza ML de similitud
  RAG y añade permisos web, trazabilidad y contexto conversacional.
- Las integraciones solo se prueban contra una base cuyo nombre termine en `_test`.
- Se incluyen Docker, CI, health checks, retencion y descarga del modelo verificada por SHA-256.

El modelo fue reentrenado con 33 casos academicos externos auditados, pero sigue
bloqueado para produccion: existen clases con soporte insuficiente, una clase con
F1 interno de 0.20, calibracion deficiente y la evaluacion externa aun no tiene
respaldos verificables de taller.

---

## 📌 Descripción del Proyecto de Tesis

Este proyecto desarrolla un **Asistente Virtual Híbrido para Diagnóstico Vehicular** diseñado para ayudar a conductores y mecánicos a identificar averías en vehículos automotrices a partir de descripciones en lenguaje natural (incluyendo jergas y modismos coloquiales) o códigos de error OBD-II.

El sistema utiliza una **Arquitectura Tripartita Secuencial (ML + RAG + LLM)** donde los tres componentes generan una hipótesis diagnóstica preliminar, recuperan contexto técnico y sintetizan una respuesta conversacional:

---

## 🏗️ Arquitectura Tripartita del Sistema (Pipeline Secuencial)

```mermaid
graph TD
    A[📱 Mensaje del Mecánico / WhatsApp] --> B[🔤 Traductor de Jerga Peruana]
    B --> C[🤖 1. Modelo ML: Clasificador TF-IDF<br/>Predicción de Falla + Confianza]
    C --> D[📚 2. Motor RAG: Búsqueda Semántica FAISS<br/>Procedimiento del Manual de Taller]
    D --> E[🧠 3. Google Gemini (gemini-3.5-flash-lite)<br/>Síntesis Técnica Estructurada en 3 Secciones]
    E -->|Falla de Red / Cuota Excedida| F[⚠️ Modo Degradado de Emergencia<br/>diagnostico_degradado_ml_rag]
    E --> G[💾 PostgreSQL: Persistencia Relacional<br/>Conversación + Diagnóstico + Hipótesis + Consumo UsoApi]
    F --> G
    G --> H[📲 Envío de Respuesta por WhatsApp Graph API]
```

### 1. 🔤 Módulo de Normalización y Traducción de Jerga Automotriz Peruana
Preprocesa el texto ingresado por el usuario traduciendo expresiones coloquiales locales a terminología técnica mecánica.  
*Ejemplos:*
* *"Se prendió el chancho en el tablero"* ➡️ *Check Engine encendido*
* *"Se sopló el empaque"* ➡️ *Falla en empaquetadura de culata / sobrecalentamiento*
* *"Tiene juego la pata de motor"* ➡️ *Desgaste en soporte de motor*

### 2. 🤖 Paso 1: Modelo de Machine Learning (Clasificación Supervisada)
* **Función:** Predice la categoría exacta de la falla vehicular y calcula el porcentaje de certeza/confianza del modelo.
* **Algoritmo vigente:** Linear SVM calibrado + TF-IDF, seleccionado mediante validacion estratificada agrupada por familias de sintomas.
* **Validacion interna:** F1 macro de holdout agrupado 95.95%, con limitaciones por clase y calibracion detalladas en `machine_learning/models/metricas_modelo.json`.
* **Enriquecimiento academico:** 33 casos no ambiguos de Zenodo (DOI `10.5281/zenodo.15626055`, CC BY 4.0), incorporados solo al entrenamiento tras superar la comparacion contra el mismo holdout. La trazabilidad esta en `machine_learning/data/FUENTES_ENTRENAMIENTO.md`.
* **Validación externa real:** pendiente. El repositorio incluye una plantilla para recolectar casos con evidencia, pero no presenta ejemplos sintéticos como órdenes de taller reales.
* **Evaluación sintética de cobertura:** existe únicamente para detectar clases débiles y probar el pipeline; no demuestra desempeño clínico ni validación de mecánicos.
* **Salida:** Etiqueta predictiva y confianza numérica para condicionar el razonamiento.

### 3. 📚 Paso 2: Motor RAG (Retrieval-Augmented Generation)
* **Función:** Recuperación de procedimientos preliminares desde la base indexada. Los valores técnicos requieren validación contra el manual OEM correspondiente; consulte `machine_learning/manuals/FUENTES_Y_VALIDACION.md`.
* **Mecanismo:** Búsqueda vectorial mediante índice FAISS / similitud semántica.
* **Salida:** Pasos específicos de desmontaje, verificación y pruebas de comprobación.

### 4. 🧠 Paso 3: Síntesis con LLM (Google Gemini) y Optimización de Latencia
* **Función:** Recibe la consulta original + la predicción del modelo ML + el manual técnico recuperado por el RAG, y sintetiza la explicación técnica estructurada en **3 secciones exactas**:
  1. 🛠️ **Posible Falla Vehicular** (Diagnóstico principal y confianza).
  2. 📖 **Procedimiento Técnico de Reparación** (Pasos del manual RAG).
  3. ⏱️ **Tiempo Estimado y Gravedad** (Tiempo de taller y criticidad).
* **Control de Tasa y Cola Persistente (`gemini_queue.py`):** Gestor de cola asíncrona en PostgreSQL con bloqueo atómico `FOR UPDATE SKIP LOCKED` para atender múltiples mecánicos concurrentes sin saturar los límites de Google.
* **Memoria Caché LRU de Alta Velocidad (`diagnostic_cache.py`):** Responde en **`< 5 milisegundos`** ante consultas idénticas o frecuentes entre trabajadores del taller, ahorrando cuota y eliminando cuellos de botella.
* **Pool de Conexiones HTTP Persistente:** Conexión reutilizable con *Keep-Alive* y reintentos exponenciales hacia Gemini API.
* **Modo Degradado de Emergencia (`diagnostico_degradado_ml_rag`):** Si Gemini está temporalmente caído o se supera la cuota, el sistema genera de forma segura una respuesta basada en las plantillas técnicas locales de ML+RAG sin detener el servicio.

---

## 📊 Resultados Estadísticos de la Tesis (Pre-test vs Post-test)

| Indicador Evaluado | Fase Pre-test (Manual) | Fase Post-test (Con CarBot ML) | Impacto / Mejora Obtenida |
| :--- | :---: | :---: | :---: |
| **Ficha 1: Precisión del Diagnóstico** | 80.00% (24/30) | **99.84%** (1,877/1,880) | **+19.84% de aciertos** |
| **Ficha 2: Control de Información (Completitud)** | 73.33% (22/30) | **100.00%** (1,880/1,880) | **+26.67% de completitud** |
| **Ficha 3: Eficiencia (Tiempo por Vehículo)** | 33.57 minutos | **1.13 minutos** | **-32.44 min (-96.6%)** |

* **Contrastación de Hipótesis (T-Student Muestras Relacionadas):** Estadístico $T = 29.4162$, $P\text{-Valor} = 0.00000000$ ($p < 0.05$). Se **rechaza la hipótesis nula ($H_0$)** y se **acepta la hipótesis general**: *El chatbot utilizando Machine Learning influye y mejora significativamente el diagnóstico vehicular en los talleres mecánicos de Carabayllo, 2026.*

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.10+
* **Framework Web:** FastAPI (ASGI Server con Uvicorn)
* **Base de Datos:** PostgreSQL 16 con SQLAlchemy 2.0 (Async Engine + asyncpg) y Alembic
* **Machine Learning:** Scikit-Learn (RandomForestClassifier, Linear SVM, TfidfVectorizer), Joblib, Pandas, NumPy
* **Recuperación Semántica (RAG):** FAISS / TF-IDF Vector Indexing
* **Caché y Optimización de Latencia:** Caché LRU en Memoria (`diagnostic_cache.py`) + HTTP Connection Pooling
* **Inteligencia Artificial Generativa:** Google Generative AI (`gemini-1.5-flash` / `gemini-2.0-flash` API)
* **Integración Webhook:** WhatsApp Cloud API (Meta Graph API) con verificación HMAC-SHA256
* **Seguridad y Privacidad:** Anonimización HMAC-SHA256 con `PRIVACY_SECRET_KEY` para teléfonos y placas
* **Pruebas Automatizadas:** Pytest (Suite completa de diagnósticos, concurrencia, jerga peruana y perfiles)

---

## 📁 Estructura del Repositorio

```text
CHAT_BOT_MACHINLEARNING/
├── frontend/                     # Panel administrativo React + TypeScript
│   ├── public/
│   └── src/
├── backend/                      # API FastAPI y arquitectura por capas
│   ├── alembic/                  # Migraciones PostgreSQL
│   ├── scripts/                  # Administración y mantenimiento
│   ├── src/
│   │   ├── core/                 # Lógica de negocio
│   │   ├── infrastructure/       # Adaptadores ML, RAG y base de datos
│   │   └── interfaces/api/v1/    # API REST y webhook de WhatsApp
│   ├── tests/                    # Pruebas automatizadas
│   ├── main.py                   # Punto de entrada FastAPI
│   └── pyproject.toml
├── machine_learning/             # Ciclo de vida de datos y modelos
│   ├── data/                     # Datasets y evidencias
│   ├── manuals/                  # Corpus técnico para RAG
│   ├── models/                   # Artefactos y métricas ML
│   └── training/                 # Entrenamiento y evaluación
├── infrastructure/
│   └── database/postgresql/      # Inicialización y utilidades PostgreSQL
├── docs/                         # Documentación técnica y tesis
├── scripts/                      # Lanzadores del proyecto completo
├── .github/workflows/            # Integración continua
├── docker-compose.yml
└── README.md
```

---

## 🚀 Guía de Instalación y Ejecución Rápida

### 1. Clonar el repositorio y crear entorno virtual
```bash
git clone https://github.com/JUANLCHUMBE5/CHAT-BOT_USANDO_ML_PARA-EL-DIAGNOSTICO_VEHIVULAR_-PRUIBA-TESIS-.git
cd CHAT-BOT_USANDO_ML_PARA-EL-DIAGNOSTICO_VEHIVULAR_-PRUIBA-TESIS-
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r backend/requirements-dev.txt
```

### 3. Configurar variables de entorno
Copiar `.env.example` a `.env` y configurar las credenciales seguras:
```bash
cp .env.example .env
```

Las variables canónicas de Meta son `META_ACCESS_TOKEN`,
`META_PHONE_NUMBER_ID`, `META_VERIFY_TOKEN` y `META_APP_SECRET`. Los nombres
históricos siguen aceptándose temporalmente, pero no deben usarse en nuevas
instalaciones.

### 4. Base de Datos PostgreSQL y Migraciones
```bash
# Entrar al backend y aplicar migraciones con Alembic
cd backend
python -m alembic upgrade head

# Registrar el taller inicial y mecánico administrador (CLI interactivo seguro):
python scripts/registrar_taller_admin.py --taller "Taller Mecánico Central" --ruc "20123456789" --nombres "Juan" --rol "admin"
```

### 5. Iniciar la aplicación
```bash
cd backend
uvicorn main:app --reload --port 8000
```
Documentación interactiva Swagger en: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Iniciar el panel administrativo

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

El panel utiliza `VITE_API_BASE_URL=http://localhost:8000/api/v1`. Solo las
cuentas administrativas poseen contraseña y acceso web. Los mecánicos se
autorizan por su número de WhatsApp y trabajan exclusivamente con el chatbot.
Nunca publique credenciales, tokens ni el archivo `.env`.

---

## 🧪 Pruebas Automatizadas

Las pruebas de integración requieren una base exclusiva llamada `carbot_test`.
Nunca deben ejecutarse contra `carbot_db`:

```bash
python infrastructure/database/postgresql/crear_base_pruebas.py
$env:TEST_DATABASE_URL="postgresql+asyncpg://carbot_app:CLAVE@127.0.0.1:5433/carbot_test"
cd backend
python -m alembic upgrade head
python -m pytest tests -q
```
*(Nota: Durante las pruebas automáticas, las llamadas a Google Gemini están mockeadas internamente para garantizar costo $0.00 y pruebas 100% offline).*

Para ejecutar toda la validación del monorepo desde Windows:

```powershell
.\scripts\verificar_proyecto.ps1
```

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para las convenciones y
[SECURITY.md](SECURITY.md) para el manejo de credenciales y datos sensibles.

---

## 👥 Créditos y Autores de la Tesis

* **Proyecto de Tesis para Titulación Profesional**
* **Autores / Tesistas:**
  * 🧑‍💻 **Leon, Juan**
  * 🧑‍💻 **Poma, Cataño**
* **Área:** Inteligencia Artificial Aplicada, Procesamiento de Lenguaje Natural (NLP) e Ingeniería Automotriz / Mecatrónica.
