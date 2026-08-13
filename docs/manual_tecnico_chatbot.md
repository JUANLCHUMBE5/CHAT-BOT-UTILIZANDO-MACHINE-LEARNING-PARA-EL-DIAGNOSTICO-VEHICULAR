# Manual Técnico del Código y Módulos de Diagnóstico
## Proyecto: Chatbot de Diagnóstico Vehicular Híbrido

> **Alcance vigente:** audio desactivado por defecto. Solo funciona con
> `AUDIO_ENABLED=true`, credenciales oficiales y aprobación de privacidad.
> La implementación descarga y transcribe audio real; no usa señales sintéticas.

Este manual técnico describe la estructura de archivos, el funcionamiento del código y aborda la discrepancia de la funcionalidad de audio entre tu borrador de informe de tesis y los scripts reales desarrollados en el proyecto.

---

## 1. El Mapeo del Audio en tu Tesis: Análisis y Recomendación

> [!WARNING]
> **Existe una discrepancia en tu informe actual**:
> En las páginas 4, 14 y 15 de tu borrador de tesis escribiste frases como:
> * *"Aunque la presente investigación no contempló la implementación de sensores físicos..."* (Pág 4)
> * *"Aunque el presente proyecto no se centró en el análisis de sonido..."* (Pág 14 y 15)
>
> **Sin embargo, en tu código fuente tienes archivos clave de audio** como `chatbot_voz_y_ruido.py` y `analizar_tipo_audio.py` que procesan señales físicas de sonido usando la transformada de Fourier (FFT) para diagnosticar fallas de motor por ruido.

### ¿Cómo defender esto ante el jurado? Te recomendamos dos enfoques:

#### Enfoque A (Recomendado - Mayor Valor Académico):
Presenta el procesamiento de sonido como un **Módulo Multimodal Acústico de Entrada**. En tu informe, modifica las frases restrictivas para indicar que el chatbot es de entrada multimodal:
> *"El sistema permite al usuario ingresar síntomas mediante texto o mediante una grabación de audio directa del ruido de su motor en WhatsApp. El sistema procesa el audio espectralmente para determinar si contiene voz o un patrón acústico de avería."*
* **Por qué ayuda**: Aumenta notablemente el nivel técnico de tu tesis de Ingeniería de Sistemas frente al jurado. Demuestra que no es solo un formulario web de texto, sino un sistema capaz de interactuar con datos analógicos de audio.

#### Enfoque B (Conservador - Alcance Limitado):
Declara el análisis acústico de ruido de motor como una **Funcionalidad Prototipo de Trabajo Futuro (Future Work)** implementada a nivel de servidor pero fuera del alcance de la validación estadística de la muestra actual de 60 casos.

---

## 2. Inventario y Descripción de Archivos del Proyecto

El proyecto está estructurado de la siguiente forma para mantener las buenas prácticas arquitectónicas y de limpieza de código:

### A. Módulos Principales de la Aplicación (`backend/src/`)

* **[main.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/main.py)**:
  Punto de entrada principal del backend. Configura FastAPI, importa las rutas modularizadas y arranca el servidor web asíncrono con Uvicorn en el puerto 8000.
  
* **[backend/src/interfaces/api/v1/router.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/backend/src/interfaces/api/v1/router.py)**:
  Agrupa y centraliza todas las rutas modulares de la versión 1 de la API (`api_router`).
  
* **[backend/src/interfaces/api/v1/endpoints/webhook.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/backend/src/interfaces/api/v1/endpoints/webhook.py)**:
  Implementa los endpoints de webhook de Meta expuestos bajo el prefijo `/api/v1/webhook` para integrar las notas de texto y audio de WhatsApp.
  
* **[backend/src/interfaces/api/v1/endpoints/diagnostico.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/backend/src/interfaces/api/v1/endpoints/diagnostico.py)**:
  Nuevo endpoint REST genérico `POST /api/v1/diagnostico/analizar` que permite a clientes de terceros (como dashboards web o apps) consultar diagnósticos directamente.
  
* **[backend/src/core/gestor_diagnostico.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/backend/src/core/gestor_diagnostico.py)**:
  El orquestador de la lógica del chatbot. Vincula el clasificador de Machine Learning, la extracción del manual en RAG y la formulación conversacional del LLM.
  
* **[backend/src/core/audio_processor.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/backend/src/core/audio_processor.py)**:
  Procesa y analiza las señales de audio (Transformada de Fourier - FFT, cálculo de energía RMS y normalizaciones de volumen).
  
* **[backend/src/infrastructure/modelo_ml.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/backend/src/infrastructure/modelo_ml.py)**:
  Encapsula el cargado y ejecución de los modelos de Machine Learning guardados en la carpeta `machine_learning/models/`.
  
* **[backend/src/infrastructure/motor_rag.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/backend/src/infrastructure/motor_rag.py)**:
  Indexa y busca procedimientos mecánicos del taller (`manual_procedimientos.txt`) mediante similitud de coseno vectorial sobre pesos TF-IDF.

---

### B. Módulos de Entrenamiento y Datos (`machine_learning/training/` y `machine_learning/data/`)

* **[machine_learning/training/generar_dataset.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/machine_learning/training/generar_dataset.py)**:
  Genera el dataset sintético inicial de síntomas vehiculares y lo guarda en `machine_learning/data/dataset_sintomas.csv`.
  
* **[machine_learning/training/entrenar_modelo.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/machine_learning/training/entrenar_modelo.py)**:
  Entrena el clasificador `RandomForestClassifier` y guarda los binarios resultantes (`modelo_diagnostico.pkl` y `vectorizador_tfidf.pkl`) en la carpeta `machine_learning/models/`.
  
* **[machine_learning/training/generar_tracker_excel.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/machine_learning/training/generar_tracker_excel.py)**:
  Simula los 60 registros del pre-test y post-test del diseño experimental guardándolos en `machine_learning/data/tracker_diagnosticos.csv`.
  
* **[machine_learning/training/analizar_resultados_tesis.py](file:///C:/Users/Juan/.gemini/antigravity-ide/scratch/chatbot-diagnostico-vehicular/machine_learning/training/analizar_resultados_tesis.py)**:
  Script estadístico que procesa las fichas del capítulo IV aplicando t de Student y Wilcoxon sobre la simulación de casos.

---

### C. Directorio Experimental (`pruebas/`)

* **`pruebas/`**:
  Contiene los prototipos de consola iniciales y libretas Jupyter (`probar_*.py`, `chatbot_voz_y_ruido.py`, `notebook.ipynb`) que sirvieron como bocetos durante el diseño del sistema pero que están fuera del código de producción de la aplicación.

---

## 3. Cómo Ejecutar el Proyecto Localmente

Para realizar pruebas locales y simular el comportamiento de WhatsApp:

1. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Entrenar el Modelo** (Si no tienes los archivos `.pkl` creados):
   ```bash
   python machine_learning/training/entrenar_modelo.py
   ```
3. **Configurar Claves de Entorno (Opcional)**:
   Si tienes una API Key de Gemini para respuestas conversacionales, configúrala en tu sistema:
   * **Windows (PowerShell)**: `$env:GEMINI_API_KEY="tu-clave-api-aqui"`
   * **Windows (CMD)**: `set GEMINI_API_KEY=tu-clave-api-aqui`
4. **Iniciar el Servidor**:
   ```bash
   python main.py
   ```
5. **Iniciar Ngrok** para hacerlo público:
   ```bash
   ngrok http 8000
   ```
6. Vincula la URL generada por Ngrok (`https://xxxx.ngrok-free.app/webhook`) en el panel de configuración de Meta for Developers.
