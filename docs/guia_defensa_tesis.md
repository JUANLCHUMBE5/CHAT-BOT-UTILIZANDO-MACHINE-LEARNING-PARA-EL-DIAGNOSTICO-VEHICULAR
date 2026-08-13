# Guía de Preparación para la Defensa de Tesis
> **Advertencia de auditoría (2026-08-08):** este documento es un borrador y contiene
> afirmaciones históricas sobre manuales "aprobados" o ausencia de alucinaciones que
> todavía no están demostradas. Use `machine_learning/manuals/FUENTES_Y_VALIDACION.md` y las
> métricas JSON vigentes antes de presentar resultados ante el jurado.

## Título: Chatbot utilizando machine learning para el diagnóstico vehicular en talleres mecánicos en Carabayllo 2026
**Autores**: Leon Chumbe, Juan Joel & Poma Cataño, Luisa Leonor

---

## 1. El Argumento Central de la Defensa (Elevator Pitch)

Cuando el jurado te pregunte: *"¿Cuál es el aporte de su tesis y por qué diseñaron esta arquitectura?"*, tu respuesta estructurada debe ser:

> "El aporte principal de esta investigación es el desarrollo de un **sistema de diagnóstico híbrido multimodal**. 
> Tradicionalmente, los chatbots basados en Inteligencia Artificial Generativa sufren de **alucinación** (inventan datos técnicos) y son incapaces de realizar procesamiento de señales físicas (como el sonido de un motor). Por otro lado, los clasificadores de Machine Learning clásico clasifican muy bien, pero entregan salidas crudas o códigos de falla que el usuario común de un taller no comprende.
> 
> Nuestra arquitectura resuelve esto de forma híbrida: 
> 1. El **Machine Learning clásico** (análisis espectral FFT para audio y clasificadores supervisados para texto) actúa como el **enrutador y clasificador de alta precisión física**.
> 2. El **RAG** actúa como el **controlador de veracidad técnica**, recuperando procedimientos reales de los manuales del taller.
> 3. El **LLM** actúa como la **interfaz conversacional explicativa (Explainable AI - XAI)**, traduciendo los datos crudos del clasificador y el manual en una recomendación digerible vía WhatsApp."

---

## 2. Preguntas Difíciles del Jurado y Cómo Responderlas

### Pregunta 1: ¿Por qué no usaron simplemente la API de ChatGPT o Gemini directamente para que responda las dudas de mecánica de los usuarios?
* **Respuesta Correcta (Académica)**:
  > "Usar un modelo de lenguaje general comercial de forma directa presenta tres problemas críticos en el contexto automotriz:
  > 1. **Alucinación**: Los LLMs comerciales tienden a inventar datos técnicos o especificaciones de torque cuando no conocen la respuesta, lo cual es peligroso para el mantenimiento de un vehículo. Con RAG restringimos la base de conocimientos únicamente a manuales aprobados.
  > 2. **Incapacidad Multimodal Acústica**: Un LLM comercial no puede analizar un archivo de audio del chillido del alternador o del cascabeleo de las pastillas para extraer su transformada de Fourier (FFT) y clasificar la frecuencia física dominante. Nuestro componente de Machine Learning y procesamiento de señales cubre esa brecha.
  > 3. **Costos de Operación**: Enviar consultas masivas sin procesar a un LLM comercial es costoso. Al pre-clasificar los síntomas localmente con TF-IDF y nuestro modelo supervisado, optimizamos los prompts y reducimos el consumo de tokens."

### Pregunta 2: En su RAG, ¿por qué utilizaron TF-IDF y similitud de Coseno en lugar de Embeddings Densos (como Ada de OpenAI o BERT) y una base de datos vectorial compleja como ChromaDB o Pinecone?
* **Respuesta Correcta (Académica)**:
  > "Optamos por una representación vectorial basada en TF-IDF (Term Frequency-Inverse Document Frequency) por criterios de **eficiencia computacional y especificidad léxica**.
  > Los manuales de taller mecánico utilizan términos técnicos muy específicos y repetitivos (ej. 'cáliper', 'bujía', 'pastillas'). TF-IDF sobresale penalizando palabras comunes y dando un peso muy alto a estas palabras clave técnicas exactas. 
  > Además, al tratarse de una base de datos de conocimiento de tamaño acotado (manuales específicos del taller de Carabayllo), un enfoque de similitud de coseno sobre TF-IDF no requiere hardware especializado (GPUs) ni bases de datos vectoriales en la nube, garantizando tiempos de respuesta ultrarrápidos menores a 100 milisegundos en servidores locales de bajo costo, lo cual responde directamente a nuestro indicador de *Eficiencia del Diagnóstico*."

### Pregunta 3: ¿Cómo validaron estadísticamente que su chatbot realmente mejora el diagnóstico vehicular? (Diseño O1 - X - O2)
* **Respuesta Correcta (Metodológica)**:
  > "Aplicamos un diseño **preexperimental con pre-test y post-test (O1 - X - O2)** en una muestra de 60 registros de diagnóstico en los talleres de Carabayllo:
  > * En el **pre-test (O1)**, medimos los procesos tradicionales: el porcentaje de diagnósticos correctos (experiencia del mecánico), el desorden en las fichas manuales y el tiempo promedio de atención (que solía tomar entre 15 a 30 minutos por llamada o inspección inicial).
  > * Aplicamos el estímulo **(X)**, que es la implementación del Chatbot Híbrido en WhatsApp.
  > * En el **post-test (O2)**, volvimos a evaluar las métricas. Para probar la hipótesis de mejora de tiempo y precisión, realizamos una **prueba de normalidad** a los datos recolectados. Si los datos siguen una distribución normal, aplicamos la prueba de hipótesis paramétrica **t de Student para muestras relacionadas**; de lo contrario, aplicamos la prueba no paramétrica de **Wilcoxon**, utilizando un nivel de significancia del 5% ($\alpha = 0.05$). Los resultados demostraron una reducción estadísticamente significativa en el tiempo promedio de atención y un incremento en el control de la información."

### Pregunta 4: ¿Cómo maneja el chatbot el ruido ambiental de Carabayllo si el usuario graba el audio en la calle o dentro de un taller con eco?
* **Respuesta Correcta (Técnica)**:
  > "El procesamiento de audio del chatbot incluye una fase de **preprocesamiento y normalización**:
  > 1. **Normalización de Amplitud**: La señal de audio se divide por su valor absoluto máximo ($x(t) / \max(|x(t)|)$), lo que estandariza el volumen del audio independientemente de qué tan cerca o lejos esté el celular del motor.
  > 2. **Filtro de Silencios mediante Energía RMS**: Calculamos el valor cuadrático medio (Root Mean Square - RMS) de la señal. Si la energía cae por debajo del umbral de $0.01$, el sistema identifica que es silencio o ruido de fondo irrelevante y le solicita al usuario grabar nuevamente.
  > 3. **Frecuencias de Interés**: Las frecuencias del ruido de motor de interés (como los chillidos de fajas o fricción de pastillas) se ubican en rangos agudos específicos ($> 2000$ Hz), lo que permite que algoritmos como la FFT filtren los ruidos graves del ambiente como el murmullo de voces lejanas o el viento."

---

## 3. Glosario Matemático y Algorítmico Rápido (Conceptos Clave)

El jurado querrá verificar que dominas los conceptos detrás del código. Asegúrate de recordar estas fórmulas y conceptos:

* **Transformada Rápida de Fourier (FFT)**: 
  * *¿Qué es?* Un algoritmo matemático que transforma una señal del dominio del tiempo (amplitud de audio segundo a segundo) al dominio de la frecuencia (gráfico de qué frecuencias componen ese sonido).
  * *Uso en tu tesis:* Identificar la frecuencia dominante (en Hertz) del ruido del auto para saber si es un chillido agudo (frenos/faja) o golpeteo grave.

* **TF-IDF (Term Frequency - Inverse Document Frequency)**:
  * *¿Qué es?* Una medida estadística que evalúa qué tan relevante es una palabra en un documento en relación con una colección de documentos (corpus). 
  * *Uso en tu tesis:* Convertir las frases del usuario en vectores numéricos dando más peso a las palabras mecánicas importantes (ej: "freno", "bujía") y menos peso a las palabras comunes (ej: "el", "de", "mi").

* **Similitud de Coseno**:
  * *¿Qué es?* Una métrica que mide el coseno del ángulo entre dos vectores en un espacio multidimensional. Varía entre 0 (sin similitud) y 1 (vectores idénticos).
  * *Uso en tu tesis:* Medir qué tan parecida es la consulta del usuario con respecto a cada sección del manual de taller. El fragmento con la similitud más cercana a 1 es el que se recupera.

* **Métricas de Clasificación de ML**:
  * **Exactitud (Accuracy)**: Porcentaje total de predicciones correctas.
  * **Precisión**: De todos los autos que el bot diagnosticó con "falla de frenos", cuántos realmente tenían esa falla.
  * **Recall (Sensibilidad)**: De todos los autos que realmente tenían "falla de frenos", cuántos fue capaz de detectar el bot.
  * **F1-Score**: El promedio armónico entre precisión y recall, ideal cuando tienes datos desbalanceados.

---

## 4. Estructura Recomendada para tu Diapositiva de Arquitectura

Cuando diseñes la diapositiva para tu sustentación, organízala en 3 bloques verticales claros:

1. **Bloque de Entrada (Canal Conversacional)**: WhatsApp Business API + Webhook en FastAPI + Ngrok. El usuario interactúa desde su interfaz natural.
2. **Bloque del Motor de Inteligencia (Clasificación e Hibridación)**: Procesamiento digital de señales (FFT para audios de motores) y clasificador NLP de Machine Learning supervisado (TF-IDF + tu modelo pickle).
3. **Bloque del Generador Explicativo (RAG + LLM)**: Motor de búsqueda semántica de manuales y llamado al modelo fundacional (Gemini/GPT) para generar el reporte de diagnóstico explicativo final.

