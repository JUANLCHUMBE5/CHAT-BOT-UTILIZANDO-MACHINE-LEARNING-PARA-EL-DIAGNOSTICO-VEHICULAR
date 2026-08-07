# Evaluación y Validación Metodológica en 6 Pasos para el Proyecto de Tesis

## 📢 Dictamen Metodológico: ¡100% DE ACUERDO!

La propuesta metodológica planteada en 6 fases es **rigurosa, coherente y metodológicamente impecable** para una tesis de ingeniería de sistemas / software en el área de Inteligencia Artificial. Cumple tanto con los estándares del estándar industrial de minería de datos **CRISP-DM** como con el marco ágil de desarrollo de software **Scrum** y la arquitectura limpia por capas.

A continuación, se detalla la alineación paso por paso entre la propuesta planteada y el código/arquitectura implementado en el proyecto:

---

### Paso 1: Fase de Requerimientos del Sistema
- **Tu propuesta**: Identificar qué necesita el chatbot para funcionar (síntomas a registrar, información faltante requerida, estructura de respuesta con posible falla, recomendación y tiempo de respuesta).
- **Alineación con el Proyecto**:
  - Definición formal en la matriz de operativización de variables ([explicacion_teorica_operacionalizacion.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/documentacion/notas/explicacion_teorica_operacionalizacion.md)).
  - La respuesta estructurada entrega: 1) Falla inferida por ML, 2) Procedimiento técnico RAG del manual, 3) Recomendaciones sintetizadas por LLM, y 4) Registro del tiempo de procesamiento.

---

### Paso 2: Planificación del Chatbot mediante Scrum
- **Tu propuesta**: Organizar el trabajo en Sprints (Sprint 1: Registro de síntomas; Sprint 2: Modelo predictivo ML; Sprint 3: Base RAG; Sprint 4: Integración del Chatbot).
- **Alineación con el Proyecto**:
  - **Sprint 1**: Recolección de síntomas y estructura CSV (`data/dataset_sintomas.csv`).
  - **Sprint 2**: Algoritmo de clasificación supervisada (`src/infrastructure/modelo_ml.py`).
  - **Sprint 3**: Motor de recuperación RAG (`src/infrastructure/motor_rag.py`).
  - **Sprint 4**: Integración Webhook WhatsApp FastAPI + LLM (`src/interfaces/api/v1/endpoints/webhook.py` y `main.py`).

---

### Paso 3: Preparación de Datos mediante CRISP-DM
- **Tu propuesta**: Limpiar y organizar los registros de diagnóstico vehicular para entrenar el modelo de Machine Learning y alimentar la base de conocimientos RAG.
- **Alineación con el Proyecto**:
  - Limpieza de stopwords y acentos en español peruano mediante `TfidfVectorizer(strip_accents='unicode')`.
  - División de manuales técnicos en bloques temáticos delimitados por secciones en `manuales_taller/manual_procedimientos.txt`.

---

### Paso 4: Fase de Modelado y Evaluación con Machine Learning
- **Tu propuesta**: Entrenar el modelo predictivo relacionando síntomas con fallas vehiculares y evaluarlo con métricas (exactitud, precisión, recall, F1-score y matriz de confusión).
- **Alineación con el Proyecto**:
  - Script oficial de entrenamiento: `training/entrenar_modelo.py`.
  - Script de análisis de resultados e indicadores: `training/analizar_resultados_tesis.py`.
  - Generación de reportes de clasificación de Scikit-Learn e imágenes comparativas en `documentacion/graficas/`.

---

### Paso 5: Desarrollo e Integración con Arquitectura Modular por Capas
- **Tu propuesta**: Estructurar el sistema en Capa de Presentación (Interfaz WhatsApp), Capa de Aplicación (Flujo), Capa de IA (Conexión ML + RAG + LLM) y Capa de Datos (Almacenamiento).
- **Alineación con el Proyecto**:
  - Coincidencia exactísima con la arquitectura modular `src/`:
    - **Capa Presentación**: `src/interfaces/api/v1/`
    - **Capa Aplicación**: `src/core/gestor_diagnostico.py`
    - **Capa IA (Sub-sistema Tripartito)**: ML + RAG + LLM
    - **Capa Datos**: `data/`, `models/`, `manuales_taller/`

---

### Paso 6: Pruebas, Validación y Evaluación de Variables Dependientes
- **Tu propuesta**: Validar el funcionamiento correcto del chatbot, comprobar predicciones del ML, pertinencia del RAG, coherencia técnica del LLM y evaluar las variables dependientes (predicción correcta, registros completos, tiempo promedio de respuesta).
- **Alineación con el Proyecto**:
  - Automatización del registro operacional y de auditoría en PostgreSQL; el archivo `data/tracker_diagnosticos.csv` se conserva como instrumento experimental exportable.
  - Evaluación experimental de tiempos de respuesta (< 3.5 segundos con RAG/LLM) y precisión predictiva del modelo ML.
  - Validación con scripts de prueba en `pruebas/`.
