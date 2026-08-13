# Propuesta de División del Proyecto de Tesis para 2 Integrantes (Pareja de Tesis)

Para garantizar un trabajo equitativo, especializado y alineado a las exigencias académicas universitarias, el proyecto **Chatbot de Diagnóstico Vehicular Híbrido Modular (ML + RAG + LLM)** se dividirá en **dos grandes roles complementarios**.

---

## 👤 ESTUDIANTE 1: Especialista en Inteligencia Artificial, Ciencia de Datos & Metodología CRISP-DM

### Responsabilidad Principal:
Diseño, desarrollo, entrenamiento y evaluación del **Sub-sistema Tripartito de Inteligencia Artificial (Módulos ML y RAG)**, así como la preparación y calidad del dataset vehicular bajo la metodología CRISP-DM.

### Tareas y Entregables Específicos:

1. **Fase de Preparación de Datos (CRISP-DM)**:
   - Recolección, limpieza, etiquetado y tokenización del dataset de síntomas vehiculares en español peruano ([dataset_sintomas.csv](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/machine_learning/data/dataset_sintomas.csv)).
   - Vectorización de textos utilizando técnicas de PLN (`TfidfVectorizer` con remoción de acentos y stopwords).

2. **Desarrollo del Módulo 1: Machine Learning Supervisado**:
   - Entrenamiento del modelo predictivo de clasificación con Random Forest (`backend/src/infrastructure/modelo_ml.py`).
   - Ajuste de hiperparámetros (`n_estimators`, `random_state`, profundidad de árboles).
   - Generación de artefactos binarios `.pkl` ([modelo_diagnostico.pkl](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/machine_learning/models/modelo_diagnostico.pkl)).

3. **Desarrollo del Módulo 2: Motor RAG (Retrieval-Augmented Generation)**:
   - Estructuración e indexación del manual técnico de procedimientos de taller ([manual_procedimientos.txt](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/machine_learning/manuals/manual_procedimientos.txt)).
   - Implementación del algoritmo de recuperación semántica mediante distancia de coseno (`backend/src/infrastructure/motor_rag.py`).

4. **Evaluación Científica de la IA (Fase de Pruebas y Métricas)**:
   - Cálculo y graficación de métricas de desempeño del modelo: **Exactitud (Accuracy), Precisión, Recall, F1-Score y Matriz de Confusión**.
   - Redacción del capítulo de resultados de la variable independiente (Algoritmo predictivo y RAG).

---

## 👤 ESTUDIANTE 2: Especialista en Arquitectura de Software, Backend FastAPI, Webhook WhatsApp & Integración LLM

### Responsabilidad Principal:
Construcción de la **Arquitectura Modular por Capas**, implementación de la interfaz conversacional de WhatsApp Cloud API (Meta), orquestación de la Capa de Aplicación e integración del sintetizador LLM (Gemini API).

### Tareas y Entregables Específicos:

1. **Fase de Requerimientos y Gestión Metodológica (Scrum)**:
   - Levantamiento de requerimientos funcionales y no funcionales del chatbot (registro de síntomas, datos faltantes, tiempos de respuesta).
   - Gestión del proyecto mediante marcos ágiles (Scrum): Organización del Backlog de Producto y planificación de Sprints.

2. **Desarrollo de la Capa de Presentación (Interfaz WhatsApp)**:
   - Configuración e implementación del **Webhook HTTP asíncrono** en FastAPI (`backend/src/interfaces/api/v1/endpoints/webhook.py`).
   - Integración con la API de WhatsApp Cloud de Meta y validación de seguridad mediante `Verify Token`.

3. **Desarrollo de la Capa de Aplicación e Integración LLM (Módulo 3)**:
   - Implementación del orquestador central `GestorDiagnostico` (`backend/src/core/gestor_diagnostico.py`).
   - Integración del LLM (Google Gemini gemini-3.5-flash-lite API) mediante prompts aumentados con el contexto de ML y RAG.
   - Manejo del procesador de señales de audio (`backend/src/core/audio_processor.py`) e implementación de fallbacks de contingencia.

4. **Evaluación de Variables Dependientes del Sistema**:
   - Medición e investigación del **Tiempo Promedio de Respuesta (segundos)** del sistema end-to-end.
   - Implementación del registrador de diagnósticos y métricas de registros completos ([tracker_diagnosticos.csv](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/machine_learning/data/tracker_diagnosticos.csv)).
   - Redacción del capítulo de resultados del sistema web/backend conversacional.

---

## 🤝 Matriz de Co-responsabilidad y Colaboración

| Componente del Proyecto | Estudiante 1 (IA & Datos) | Estudiante 2 (Software & Webhook) |
| :--- | :---: | :---: |
| **Limpieza y Estructuración de Datos** | Lidera 🔴 | Apoya 🔵 |
| **Modelo ML Supervisado (Random Forest)** | Lidera 🔴 | Apoya 🔵 |
| **Base de Conocimientos RAG** | Lidera 🔴 | Apoya 🔵 |
| **Backend FastAPI & Webhook WhatsApp** | Apoya 🔵 | Lidera 🔴 |
| **Integración LLM (Gemini API)** | Apoya 🔵 | Lidera 🔴 |
| **Métricas de Evaluación y Gráficos** | Lidera 🔴 (ML/RAG) | Lidera 🔴 (Tiempo/HTTP) |
| **Redacción de Documento de Tesis** | Sección IA / Métricas | Sección Software / Metodología |

