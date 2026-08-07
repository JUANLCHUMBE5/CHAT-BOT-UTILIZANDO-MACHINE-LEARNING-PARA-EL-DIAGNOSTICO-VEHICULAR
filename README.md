# 🚗 Chatbot Híbrido de Diagnóstico Vehicular asistido por Machine Learning, RAG y LLM

> **Proyecto de Tesis:** Sistema inteligente para el diagnóstico preliminar de fallas automotrices, integrando traducción de jerga mecánica peruana, algoritmos de aprendizaje automático, recuperación aumentada de información (RAG) y razonamiento generativo (LLM) con persistencia en PostgreSQL y webhook para WhatsApp.

## Estado tecnico verificado

- El asistente esta dirigido al mecanico; sus resultados son hipotesis y requieren comprobacion fisica.
- El webhook persiste la entrada antes de confirmar el HTTP 200.
- Las salidas Meta/Twilio usan un outbox PostgreSQL durable con reintentos e identificador externo.
- La cola Gemini y sus cuotas RPM/RPD son persistentes y coordinadas entre workers.
- Los telefonos pendientes quedan cifrados y la privacidad falla de forma cerrada.
- El audio esta desactivado por defecto y, al habilitarse, se descarga y transcribe realmente; no se simula.
- El esquema vigente es `20260807_06` y guarda las versiones ML y RAG de cada diagnostico.
- Las integraciones solo se prueban contra una base cuyo nombre termine en `_test`.
- Se incluyen Docker, CI, health checks, retencion y descarga del modelo verificada por SHA-256.

El modelo debe reentrenarse y superar una evaluacion externa con mecanicos antes de considerarlo validado cientificamente para produccion.

---

## 📌 Descripción del Proyecto de Tesis

Este proyecto desarrolla un **Asistente Virtual Híbrido para Diagnóstico Vehicular** diseñado para ayudar a conductores y mecánicos a identificar averías en vehículos automotrices a partir de descripciones en lenguaje natural (incluyendo jergas y modismos coloquiales) o códigos de error OBD-II.

El sistema utiliza una **Arquitectura Tripartita Secuencial (ML + RAG + LLM)** donde los tres modelos trabajan conjuntamente en cada consulta para generar un diagnóstico certero, enriquecido con procedimientos de manuales de taller y sintetizado de forma conversacional:

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
* **Algoritmo:** Clasificador Random Forest / TF-IDF Vectorizer entrenado sobre un dataset multisistema automotriz.
* **Salida:** Etiqueta predictiva y confianza numérica para condicionar el razonamiento.

### 3. 📚 Paso 2: Motor RAG (Retrieval-Augmented Generation)
* **Función:** Recuperación del procedimiento técnico y pasos de inspección desde la base de conocimientos de manuales de taller indexados.
* **Mecanismo:** Búsqueda vectorial mediante índice FAISS / similitud semántica.
* **Salida:** Pasos específicos de desmontaje, verificación y pruebas de comprobación.

### 4. 🧠 Paso 3: Síntesis con LLM (Google Gemini gemini-3.5-flash-lite)
* **Función:** Recibe la consulta original + la predicción del modelo ML + el manual técnico recuperado por el RAG, y sintetiza la explicación técnica estructurada en **3 secciones exactas**:
  1. 🛠️ **Posible Falla Vehicular** (Diagnóstico principal y confianza).
  2. 📖 **Procedimiento Técnico de Reparación** (Pasos del manual RAG).
  3. ⏱️ **Tiempo Estimado y Gravedad** (Tiempo de taller y criticidad).
* **Control de Tasa y Cola:** Limitado a 12 solicitudes por minuto para evitar sobrecostos.
* **Modo Degradado de Emergencia (`diagnostico_degradado_ml_rag`):** Si Gemini está temporalmente caído o se supera la cuota, el sistema genera de forma segura una respuesta basada en las plantillas técnicas locales de ML+RAG sin detener el servicio.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.10+
* **Framework Web:** FastAPI (ASGI Server con Uvicorn)
* **Base de Datos:** PostgreSQL 16 con SQLAlchemy 2.0 (Async Engine + asyncpg) y Alembic
* **Machine Learning:** Scikit-Learn (RandomForestClassifier, TfidfVectorizer), Joblib, Pandas, NumPy
* **Recuperación Semántica:** FAISS / TF-IDF Vector Indexing
* **Inteligencia Artificial Generativa:** Google Generative AI (`gemini-3.5-flash-lite` API)
* **Integración Webhook:** WhatsApp Cloud API (Meta Graph API) con verificación HMAC-SHA256
* **Seguridad y Privacidad:** Anonimización HMAC-SHA256 con `PRIVACY_SECRET_KEY` para teléfonos y placas
* **Pruebas Automatizadas:** Pytest (73 pruebas unitarias, de integración, persistencia y seguridad)

---

## 📁 Estructura del Repositorio

```bash
CHAT_BOT_MACHINLEARNING/
├── alembic/                      # Versionamiento y migraciones de esquemas PostgreSQL
├── data/                         # Datasets de síntomas y códigos OBD-II (CSV)
│   ├── dataset_sintomas.csv
│   └── tracker_diagnosticos.example.csv
├── documentacion/                # Documentación técnica y arquitectura
│   └── arquitectura_modular/
├── manuales_taller/              # Manuales de procedimientos para el motor RAG
│   └── manual_procedimientos.txt
├── models/                       # Binarios serializados de los modelos ML (.pkl)
├── scripts/                      # Utilidades y CLI seguro
│   ├── registrar_taller_admin.py # Registro seguro de taller y admin por hash
│   └── postgresql/
├── src/                          # Código fuente modular por capas
│   ├── config.py                 # Configuración y variables Pydantic Settings
│   ├── core/                     # Lógica de negocio (Gestor Tripartito, Jerga, Queue, Audio)
│   │   ├── gestor_diagnostico.py
│   │   ├── gemini_queue.py       # Rate limiter de 12 req/min
│   │   ├── audio_processor.py
│   │   ├── session_manager.py
│   │   └── traductor_jerga.py
│   ├── infrastructure/           # Adaptadores ML, RAG y Repositorios DB
│   │   ├── database/             # Modelos y repositorios SQLAlchemy
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── modelo_ml.py
│   │   └── motor_rag.py
│   └── interfaces/api/v1/        # Endpoints REST y Webhook WhatsApp
│       ├── endpoints/
│       │   └── webhook.py
│       └── schemas.py
├── tests/                        # Suite Pytest completa (73 pruebas)
├── main.py                       # Punto de entrada FastAPI
├── pyproject.toml                # Manifiesto del proyecto
└── README.md                     # Documentación general
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
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Copiar `.env.example` a `.env` y configurar las credenciales seguras:
```bash
cp .env.example .env
```

### 4. Base de Datos PostgreSQL y Migraciones
```bash
# Aplicar migraciones con Alembic
alembic upgrade head

# Registrar el taller inicial y mecánico administrador (CLI interactivo seguro):
python scripts/registrar_taller_admin.py --taller "Taller Mecánico Central" --ruc "20123456789" --nombres "Juan" --rol "admin"
```

### 5. Iniciar la aplicación
```bash
uvicorn main:app --reload --port 8000
```
Documentación interactiva Swagger en: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Pruebas Automatizadas

Para ejecutar las 73 pruebas de integración, seguridad y persistencia:
```bash
pytest -v
```
*(Nota: Durante las pruebas automáticas, las llamadas a Google Gemini están mockeadas internamente para garantizar costo $0.00 y pruebas 100% offline).*

---

## 👥 Créditos y Autores de la Tesis

* **Proyecto de Tesis para Titulación Profesional**
* **Autores / Tesistas:**
  * 🧑‍💻 **Leon, Juan**
  * 🧑‍💻 **Poma, Cataño**
* **Área:** Inteligencia Artificial Aplicada, Procesamiento de Lenguaje Natural (NLP) e Ingeniería Automotriz / Mecatrónica.
