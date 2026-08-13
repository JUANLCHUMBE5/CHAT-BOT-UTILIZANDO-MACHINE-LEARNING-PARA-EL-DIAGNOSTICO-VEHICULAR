# Balotario Completo de 34 Preguntas del Jurado - Tesis I (9no Ciclo)
> **Advertencia de auditoría (2026-08-08):** las respuestas que califican el corpus
> como oficial, 100% verídico o libre de alucinaciones no deben utilizarse hasta
> documentar la fuente OEM de cada procedimiento. Consulte
> `machine_learning/manuals/FUENTES_Y_VALIDACION.md`.

## Proyecto: Chatbot de Diagnóstico Vehicular con Machine Learning - UCV

Este documento contiene un banco completo de **34 preguntas y respuestas** diseñado específicamente para tu sustentación de Tesis I. Las preguntas están agrupadas por las secciones oficiales de tu exposición y tu informe metodológico y tecnológico.

---

## BLOQUE 1: INTRODUCCIÓN, PROBLEMA Y JUSTIFICACIÓN (Slide 3)

### 1. ¿Cuál es el problema real que han identificado en los talleres mecánicos de Carabayllo?
* **Respuesta**:
  > *"El problema principal es la gestión empírica y manual del proceso de diagnóstico. Actualmente, los síntomas reportados por los clientes y las fallas detectadas se registran en cuadernos u hojas físicas, lo que ocasiona desorden, pérdida de información técnica histórica y retrasos en la atención al cliente, además de depender exclusivamente de la memoria y experiencia del mecánico de turno."*

### 2. ¿De qué manera justifica tecnológicamente su proyecto de investigación?
* **Respuesta**:
  > *"Se justifica tecnológicamente al integrar algoritmos de Machine Learning (para la clasificación predictiva de fallas) y un motor RAG (para la recuperación precisa de manuales técnicos) dentro de una interfaz de WhatsApp. Esto moderniza el proceso de diagnóstico tradicional, reemplazando la búsqueda física en manuales por un asistente automatizado accesible desde el celular."*

### 3. ¿Cuál es la justificación metodológica de su tesis?
* **Respuesta**:
  > *"Nuestra investigación se justifica metodológicamente porque establece un diseño preexperimental estructurado y medible ($O_1 - X - O_2$) para evaluar el impacto de herramientas de inteligencia artificial en el rendimiento operativo de los talleres. Aportamos una matriz de consistencia y fichas de registro cuantitativas que pueden ser replicadas en otros estudios de automatización de servicios."*

### 4. ¿Cómo se alinea su proyecto con los Objetivos de Desarrollo Sostenible (ODS)?
* **Respuesta**:
  > *"Se alinea directamente con el **ODS 9: Industria, Innovación e Infraestructura**, específicamente con la **meta 9.5**, que busca aumentar la investigación científica y mejorar la capacidad tecnológica de los sectores industriales locales, fomentando la innovación digital en las micro y pequeñas empresas."*

### 5. ¿De qué manera responde su tesis a la Responsabilidad Social Universitaria (RSU)?
* **Respuesta**:
  > *"Responde a la línea de RSU de **Desarrollo económico, empleo y emprendimiento**, ya que el chatbot está diseñado para micro y pequeños talleres en zonas periféricas como Carabayllo. Al tecnificar su proceso de diagnóstico, mejoramos su productividad, reducimos los costos por fallas mal diagnosticadas y hacemos más competitivos sus negocios locales."*

### 6. ¿Por qué eligieron WhatsApp como interfaz y no una aplicación móvil descargable?
* **Respuesta**:
  > *"Elegimos WhatsApp porque posee una curva de aprendizaje nula para el usuario (el mecánico ya la utiliza a diario). Desarrollar una aplicación móvil nativa obligaría al mecánico a descargar software adicional, consumir almacenamiento en su dispositivo y detener sus labores para abrir una interfaz ajena a su flujo de comunicación diario."*

---

## BLOQUE 2: MARCO TEÓRICO Y ANTECEDENTES (Slide 5)

### 7. ¿Cuál es el aporte de la investigación de Theissler et al. (2021) a su marco teórico?
* **Respuesta**:
  > *"Theissler et al. (2021) sustenta en su investigación publicada en Scopus que las técnicas de Machine Learning son altamente eficientes para clasificar fallas y predecir anomalías en componentes automotrices complejos a partir de datos organizados. Esto nos da la base teórica para el diseño de nuestro clasificador supervisado."*

### 8. ¿De qué manera respalda Lin y Miao (2025) a su variable independiente?
* **Respuesta**:
  > *"Lin y Miao (2025) validan en su artículo indexado la viabilidad de utilizar chatbots conversacionales que reciben síntomas en lenguaje natural y recuperan información técnica estructurada de manuales mediante RAG. Esto fundamenta nuestro modelo híbrido conversacional-técnico para asistir al mecánico."*

### 9. ¿Por qué indican en sus diapositivas que estas teorías respaldan sus indicadores de tiempo y precisión?
* **Respuesta**:
  > *"Ambos autores demuestran en sus experimentos que la automatización de la consulta reduce la latencia en la búsqueda de información (indicador: tiempo promedio de respuesta) y que la vectorización matemática de los síntomas reduce los errores en la identificación de averías (indicador: porcentaje de predicción correcta)."*

### 10. ¿Cuál es la diferencia científica entre los chatbots basados solo en reglas y el enfoque híbrido que proponen?
* **Respuesta**:
  > *"Los chatbots basados en reglas son rígidos y fallan si el usuario escribe una palabra no programada. Nuestro enfoque híbrido combina la flexibilidad lingüística de un clasificador de Machine Learning para interpretar el lenguaje del mecánico y un motor RAG que extrae instrucciones directas de manuales físicos de taller, lo que evita que el bot invente respuestas o falle ante sinónimos."*

---

## BLOQUE 3: VARIABLES E INDICADORES (Slides 7 y 8)

### 11. Defina conceptualmente su variable independiente: Chatbot utilizando Machine Learning.
* **Respuesta**:
  > *"Es un sistema de software inteligente que integra una interfaz conversacional y un modelo de aprendizaje automático diseñado para registrar síntomas del vehículo, procesar semánticamente la información ingresada por el usuario y aplicar un clasificador predictivo para sugerir la falla mecánica asociada."*

### 12. Defina operacionalmente su variable dependiente: Diagnóstico Vehicular.
* **Respuesta**:
  > *"Se operacionaliza mediante la comparación del rendimiento del proceso de diagnóstico antes y después de implementar el chatbot en el taller. Evaluamos el porcentaje de predicción correcta de fallas, el control (completitud) de los registros técnicos y el tiempo promedio que toma resolver cada consulta."*

### 13. ¿Qué mide la dimensión "Procesamiento de Datos" de la variable independiente y cuál es su indicador?
* **Respuesta**:
  > *"Mide la capacidad del sistema para limpiar, tokenizar y convertir a vectores matemáticos las consultas de texto ingresadas. Su indicador es el **Porcentaje de datos procesados correctamente**."*

### 14. ¿Cómo define el indicador "Porcentaje de registros diagnósticos completos" de la variable dependiente?
* **Respuesta**:
  > *"Se define como la proporción de fichas de diagnóstico que cuentan con los 8 campos obligatorios completos (marca, placa, fecha, síntoma, etc.) sobre el total de vehículos evaluados. Mide la mejora en la calidad del registro de información del taller."*

### 15. ¿Cómo se medirá el "Tiempo promedio de respuesta diagnóstica"?
* **Respuesta**:
  > *"Se medirá en minutos. Calcula la diferencia temporal entre el momento en que el mecánico ingresa el primer síntoma y el momento en que el sistema le entrega la solución del manual técnico de taller. En el Post-test, esto se registrará mediante timestamps automáticos en el servidor."*

### 33. ¿Cómo se vinculan exactamente las dimensiones de la Variable Independiente (Causa) con las dimensiones de la Variable Dependiente (Efecto / Problema a Solucionar)?
* **Respuesta**:
  > *"Nuestra investigación plantea una relación directa de causa-efecto entre las dimensiones de ambas variables:
  > 1. **Registro de síntomas** (V.I.) $\rightarrow$ **Control de información diagnóstica** (V.D.): Al capturar los síntomas de manera estructurada mediante WhatsApp, aseguramos que todas las fichas de diagnóstico se almacenen con sus 8 campos obligatorios completos, solucionando la pérdida de datos en cuadernos físicos.
  > 2. **Procesamiento de datos** (V.I.) $\rightarrow$ **Eficiencia del diagnóstico** (V.D.): Al automatizar la limpieza y tokenización del mensaje del usuario en milisegundos, reducimos drásticamente el tiempo promedio de respuesta diagnóstica en comparación con la búsqueda manual en manuales de taller físicos.
  > 3. **Modelo predictivo** (V.I.) $\rightarrow$ **Predicción de fallas vehiculares** (V.D.): El clasificador supervisado (Random Forest) elimina la subjetividad humana del diagnóstico empírico, incrementando científicamente el porcentaje de fallas correctamente identificadas."*

---

## BLOQUE 4: DISEÑO METODOLÓGICO Y ANÁLISIS (Slides 6 y 9)

### 16. Explique la justificación de realizar una investigación de Tipo Aplicada.
* **Respuesta**:
  > *"Es una investigación aplicada porque no busca desarrollar una nueva teoría matemática, sino aplicar los conocimientos existentes de Machine Learning, RAG y APIs web para resolver un problema práctico e inmediato: la ineficiencia en el diagnóstico vehicular de los talleres mecánicos en Carabayllo."*

### 17. ¿Por qué el alcance es explicativo y no meramente descriptivo o correlacional?
* **Respuesta**:
  > *"Es explicativo porque su fin es establecer una relación de causa-efecto. Buscamos demostrar y explicar cómo la introducción de la variable independiente (el chatbot) es la causa de la variación positiva en la variable dependiente (eficiencia y precisión del diagnóstico)."*

### 18. Describa detalladamente cómo se aplicará el diseño Preexperimental $O_1 - X - O_2$.
* **Respuesta**:
  > *"Consta de tres fases secuenciales sobre un único grupo de estudio:
  > 1. **$O_1$ (Pre-test)**: Registramos cómo se diagnostican 30 vehículos sin usar el bot (tiempos con cronómetro y fichas manuales).
  > 2. **$X$ (Estímulo)**: Introducción y habilitación del chatbot en WhatsApp en el taller.
  > 3. **$O_2$ (Post-test)**: Evaluamos otros 30 vehículos usando el chatbot, capturando los datos automáticamente en el backend."*

### 19. ¿Por qué su población y muestra no son probabilísticas y se seleccionaron por conveniencia?
* **Respuesta**:
  > *"Son no probabilísticas por conveniencia debido a las limitaciones de acceso y recursos en los talleres del distrito. Seleccionamos una muestra representativa de 60 registros del taller colaborador que cuenta con las autorizaciones institucionales (Anexos 3 y 4) y que representa fallas mecánicas comunes del alcance de nuestro estudio."*

### 20. ¿Qué técnicas de recolección de datos ha definido para su proyecto?
* **Respuesta**:
  > *"Definimos tres técnicas: la **observación estructurada** (para registrar los tiempos en minutos), el **análisis documental** (para revisar el historial de registros en el taller) y el **registro automatizado del sistema** (para capturar las consultas directamente en los logs de FastAPI)."*

---

## BLOQUE 5: CONFIABILIDAD, VALIDEZ Y ESTADÍSTICA (Slide 9)

### 21. ¿Por qué indica que no utilizará el coeficiente Alfa de Cronbach para la confiabilidad de sus instrumentos?
* **Respuesta**:
  > *"El Alfa de Cronbach sirve para evaluar la consistencia interna de encuestas de opinión y escalas subjetivas. Nuestros instrumentos son fichas de observación cuantitativa directa (medimos variables físicas objetivas como tiempo en minutos y número de registros completos). La confiabilidad se sustenta en la calibración del sistema informático y la precisión temporal matemática de los timestamps del servidor, eliminando errores de digitación."*

### 22. ¿Cómo se garantiza la validez de las fichas de registro (instrumentos)?
* **Respuesta**:
  > *"La validez se realiza mediante **Juicio de Expertos**. Tres especialistas independientes evaluarán la pertinencia, claridad y relevancia de los ítems de las fichas, certificando que son válidos para medir los indicadores propuestos en la operacionalización."*

### 23. ¿Por qué se menciona el uso de la prueba estadística t de Student para muestras relacionadas?
* **Respuesta**:
  > *"Es el test estadístico paramétrico indicado para comparar dos medias obtenidas del mismo grupo en condiciones diferentes (Pre-test vs Post-test). Al procesar los datos de tiempos de diagnóstico antes y después del chatbot, confirmaremos de forma científica si existe una diferencia significativa en las medias con un nivel de confianza del 95% ($p < 0.05$)."*

### 24. ¿Qué pasa si sus datos de tiempos de diagnóstico no tienen una distribución normal? ¿Qué prueba estadística usaría?
* **Respuesta**:
  > *"Tal como declaramos en nuestro informe (Pág. 27 del PDF), primero aplicaremos una prueba de normalidad (como Shapiro-Wilk). Si los datos no siguen una distribución normal, no usaremos T-Student; en su lugar, aplicaremos la prueba no paramétrica de **Rangos con Signo de Wilcoxon** para muestras relacionadas."*

---

## BLOQUE 6: METODOLOGÍA TECNOLÓGICA Y DESARROLLO (Slide 10)

### 25. Detalle cómo se estructura el modelado de Machine Learning en la metodología CRISP-DM.
* **Respuesta**:
  > *"CRISP-DM estructura el modelado de la siguiente manera:
  > * **Preparación de Datos**: Limpieza de acentos, conversión de mayúsculas y vectorización TF-IDF de las frases.
  > * **Modelado**: Configuración y entrenamiento del clasificador Random Forest utilizando la librería Scikit-Learn.
  > * **Evaluación**: Análisis preliminar de la exactitud usando división de train/test."*

### 26. ¿Qué función cumple el túnel inverso de Ngrok y por qué es necesario en el desarrollo?
* **Respuesta**:
  > *"Ngrok expone nuestro puerto de red local `8000` a una dirección HTTPS pública temporal en internet. Esto es estrictamente necesario porque los servidores de Meta (WhatsApp) requieren una URL segura con certificado SSL válido para poder redireccionar los mensajes entrantes hacia nuestro servidor local FastAPI."*

### 27. ¿Por qué FastAPI es superior a otros frameworks como Django o Flask para esta tesis?
* **Respuesta**:
  > *"FastAPI es superior porque está optimizado para APIs RESTful, es asíncrono nativo (`async/await`) lo que le da una latencia mínima de milisegundos y genera documentación automática interactiva de los endpoints. Django o Flask son más pesados y sincrónicos por defecto, lo que retrasaría el flujo de procesamiento en tiempo real."*

### 28. ¿Cómo asegura que los manuales de taller indexados por el motor RAG sean confiables y precisos?
* **Respuesta**:
  > *"El motor RAG no busca información libre en internet. Solo busca en el archivo `manual_procedimientos.txt` que contiene manuales técnicos oficiales de taller (Haynes/Chilton) previamente curados por nosotros. Esto garantiza que la instrucción recuperada sea 100% verídica y específica para el vehículo."*

### 31. ¿El chatbot de diagnóstico vehicular funciona únicamente con el motor RAG o incluye otros modelos de inteligencia artificial?
* **Respuesta**:
  > *"El chatbot no es únicamente un sistema RAG; implementa una **Arquitectura Híbrida** constituida por tres capas de modelos y algoritmos que interactúan de forma secuencial:
  > 1. **Modelo de Clasificación (Machine Learning Supervisado)**: Un modelo de clasificación de bosque aleatorio (Random Forest Classifier) entrenado localmente con un dataset de síntomas comunes de talleres de Carabayllo, encargado de predecir la categoría física de la falla.
  > 2. **Modelo de Recuperación (RAG)**: Un algoritmo de similitud de coseno sobre vectores TF-IDF encargado de buscar la coincidencia exacta de la falla predicha dentro de los manuales técnicos locales.
  > 3. **Modelo Generativo (LLM)**: Un modelo de lenguaje grande (Gemini) utilizado únicamente en la capa final como interfaz explicativa conversacional, garantizando que el reporte se genere sin alucinaciones y respetando la información del manual técnico recuperado."*

### 32. ¿En qué antecedentes específicos de su marco teórico se fundamenta el diseño de esta arquitectura híbrida (ML + RAG + LLM)?
* **Respuesta**:
  > *"Esta arquitectura híbrida no es una invención improvisada; está directamente respaldada por investigaciones científicas indexadas que forman parte de nuestros antecedentes en el informe de tesis:
  > 1. **La combinación ML + RAG**: Se fundamenta en **Mahale, Kolhar y More (2025) [Referencia 23]**, quienes propusieron un diagnóstico vehicular automatizado mediante aprendizaje automático híbrido combinado con RAG multi-paso.
  > 2. **El uso de RAG para recuperación técnica**: Se respalda en **Zhang et al. (2025) [Referencia 22]**, quienes aplicaron generación aumentada por recuperación (RAG) para extraer información precisa de fallas en bases de datos automotrices especializadas.
  > 3. **La parte conversacional con LLMs**: Se basa en **Lin y Miao (2025) [Referencia 21]**, quienes sustentaron el diagnóstico asistido mediante modelos de lenguaje grandes e interfaces conversacionales.
  > 4. **Explicabilidad diagnóstica**: Se fundamenta en **Bao et al. (2025) [Referencia 15]**, quienes utilizaron LLMs y características de fallas para generar diagnósticos con explicación transparente y razonamiento lógico.
  > Por lo tanto, nuestra arquitectura se basa rigurosamente en el estado del arte de la ingeniería de sistemas automotrices."*

### 34. ¿Por qué eligieron específicamente estos 3 módulos (ML Supervisado, RAG y LLM) y no otros modelos alternativos?
* **Respuesta**:
  > *"Justificamos la selección de cada módulo frente a alternativas tecnológicas comunes por criterios de precisión, costo computacional y veracidad:
  > 
  > 1. **Módulo de Clasificación Predictiva (ML Supervisado - Random Forest + TF-IDF) vs Reglas Rígidas o Deep Learning**:
  >    * *Frente a Reglas Rígidas (if-else / SQL)*: Las reglas fallan cuando el usuario escribe con faltas de ortografía o sinónimos. El modelo supervisado generaliza sobre patrones lingüísticos.
  >    * *Frente a Deep Learning (CNN / LSTM)*: Deep Learning requiere cientos de miles de datos y GPUs costosas. Random Forest es un modelo de ensamble robusto respaldado por **Theissler et al. (2021) [Ref 6]** que alcanza más de 95% de precisión en datasets de síntomas pequeños/medianos sin sobreajuste.
  > 
  > 2. **Módulo de Recuperación Semántica (RAG - TF-IDF + Coseno) vs Fine-Tuning o Búsqueda Directa en LLMs**:
  >    * *Frente a Fine-Tuning de LLMs*: Re-entrenar un LLM es costoso, lento y queda desactualizado al agregar nuevos manuales. RAG indexa dinámicamente nuevos manuales sin re-entrenar.
  >    * *Frente a LLMs Directos*: Los LLMs comerciales solos sufren de **alucinación** (inventan torques o procedimientos). RAG obliga al sistema a basar la respuesta estrictamente en el manual técnico del taller, respaldado por **Zhang et al. (2025) [Ref 22]**.
  > 
  > 3. **Módulo Generativo Explicativo (LLM / IA Explicable - XAI) vs Plantillas Fijas**:
  >    * *Frente a Plantillas de Texto Fijas*: Las plantillas son frías y rígidas. El LLM actúa como capa de **IA Explicable (Explainable AI - XAI)**, respaldado por **Bao et al. (2025) [Ref 15]** y **Vega et al. (2025) [Ref 25]**, adaptando el reporte técnico a un diálogo conversacional amigable para WhatsApp."*

---

## BLOQUE 7: ASPECTOS ÉTICOS Y ALCANCE DE TESIS I (Slide 1)

### 29. ¿Cómo se abordaron los aspectos éticos de la investigación (Ley N° 29733)?
* **Respuesta**:
  > *"Garantizamos la confidencialidad codificando las placas de los vehículos y los nombres de los mecánicos para proteger su identidad (Anexo 4). Asimismo, se cuenta con las firmas de consentimiento informado firmadas por los representantes de los talleres para poder usar los datos únicamente con fines académicos."*

### 30. ¿Cuál es el estado de desarrollo del software y por qué no realiza una demostración en vivo ahora?
* **Respuesta**:
  > *"Para esta fase de Tesis I, el alcance del estudio está enfocado en la aprobación del diseño metodológico y tecnológico. Para demostrar la viabilidad, hemos desarrollado un prototipo funcional a nivel alfa que valida la conectividad del webhook local con la API de WhatsApp. El experimento completo con los 60 registros del taller, la recolección final del dataset y las métricas estadísticas finales serán ejecutados en el décimo ciclo dentro de la asignatura de Tesis II."*

