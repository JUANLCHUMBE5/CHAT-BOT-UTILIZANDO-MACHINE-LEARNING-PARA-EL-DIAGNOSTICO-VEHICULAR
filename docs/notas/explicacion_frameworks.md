# Explicación de Frameworks y Tecnologías del Proyecto
## Tesis: Chatbot de Diagnóstico Vehicular Híbrido

Para la sustentación de la tesis, es fundamental detallar las herramientas del desarrollo de software y justificar por qué se eligieron. Este proyecto utiliza una combinación de **frameworks de alto rendimiento** y **bibliotecas científicas** en el ecosistema de Python.

---

## 1. Frameworks Principales

### A. FastAPI (Backend y Webhook API)
FastAPI es el framework web principal utilizado para construir la API que recibe y procesa los mensajes de WhatsApp en tiempo real.
* **Tipo**: Framework de desarrollo web asíncrono para APIs.
* **Justificación de uso**: 
  * **Alto Rendimiento**: Es uno de los frameworks de Python más rápidos del mercado (comparable con NodeJS o Go).
  * **Asincronía Nativa**: Soporta `async/await` de forma nativa, lo que permite atender decenas de mensajes entrantes de WhatsApp en paralelo sin bloquear el servidor.
  * **Validación de Datos**: Utiliza Pydantic en segundo plano para validar que los datos enviados por Meta (WhatsApp) cumplan con la estructura de datos correcta antes de procesarlos.

### B. Streamlit (Frontend y Dashboard de Pruebas)
Streamlit se utiliza para levantar la aplicación web de pruebas de escritorio (`pruebas/app_chatbot_hibrido.py`).
* **Tipo**: Framework de desarrollo rápido de aplicaciones web de datos.
* **Justificación de uso**:
  * Permite construir interfaces gráficas de usuario interactivas en pocas líneas de código, facilitando las demostraciones del modelo predictivo y del análisis espectral de audio directamente en la computadora sin pasar por WhatsApp.

---

## 2. Bibliotecas Científicas y de Inteligencia Artificial

### A. Scikit-Learn (Machine Learning)
Es la biblioteca científica núcleo responsable de la inteligencia del chatbot.
* **Componentes clave usados**:
  * `RandomForestClassifier`: Algoritmo de clasificación supervisada basado en árboles de decisión múltiples. Es sumamente robusto para la clasificación de frases cortas.
  * `TfidfVectorizer`: Transforma los textos de los síntomas a formato numérico (vectores) mediante frecuencias de palabras, permitiendo que el clasificador los entienda.

### B. NumPy / SciPy (Procesamiento y Matemáticas)
Son bibliotecas esenciales para el análisis matemático de señales.
* **Justificación de uso**:
  * Proveen las herramientas rápidas para manipular los vectores de datos de audio física.
  * `np.fft`: Realiza la Transformada Rápida de Fourier (FFT) que convierte el sonido del vehículo (gráfico de tiempo) a una firma espectral de frecuencias (Hz) para aislar ruidos como chillidos de faja o frenos.

---

## 3. Servidores y Herramientas Auxiliares

* **Uvicorn**: Servidor web de tipo ASGI encargado de levantar y ejecutar la aplicación de FastAPI localmente en el puerto `8000`.
* **Ngrok**: Herramienta de túnel inverso (tunnelling) que crea una dirección HTTPS pública temporal para que los servidores en la nube de Meta puedan enviar mensajes webhook directo a tu servidor local de forma segura.

---

## 4. Guía de Defensa ante el Jurado

Si te preguntan **"¿Qué tecnologías y frameworks usó y por qué?"**, responde así:

> *"El desarrollo técnico se diseñó en el lenguaje de programación Python. Para el backend y la integración con la API de Meta, se seleccionó el framework **FastAPI** debido a su velocidad y su arquitectura asíncrona nativa, lo cual garantiza que las consultas de WhatsApp se atiendan en milisegundos. Para el modelo de inteligencia artificial, empleamos la biblioteca **Scikit-Learn**, específicamente con el algoritmo **Random Forest** y vectorización **TF-IDF**, por ser el estándar para la clasificación supervisada de texto corto. En paralelo, para la fase acústica, implementamos un procesador espectral de audio mediante Transformadas Rápidas de Fourier (FFT). Finalmente, implementamos una interfaz interactiva de pruebas utilizando el framework **Streamlit**."*

