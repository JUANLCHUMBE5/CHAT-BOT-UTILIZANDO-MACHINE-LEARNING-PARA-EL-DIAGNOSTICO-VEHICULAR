# Metodología y Software Utilizado en el Proyecto
## Tesis: Chatbot de Diagnóstico Vehicular Híbrido

Para la sustentación ante el jurado, es vital separar y justificar el **Software Utilizado** (las herramientas de construcción) y la **Metodología de Desarrollo** (los pasos lógicos del proyecto).

---

## 1. ¿Qué Software se está utilizando? (Herramientas Técnicas)

Estas son las herramientas de software y plataformas que hacen posible que el sistema funcione y se comunique con WhatsApp:

| Software / Herramienta | Tipo de Herramienta | Función en el Proyecto |
| :--- | :--- | :--- |
| **Python (3.10+)** | Lenguaje de Programación | Lenguaje base en el que está escrito todo el chatbot, los modelos y la API. |
| **Visual Studio Code (VS Code)** | IDE (Entorno de Desarrollo) | El editor de código utilizado para escribir, depurar y estructurar el proyecto. |
| **Git / GitHub** | Control de Versiones y Nube | Almacenamiento seguro del código fuente y control del historial de cambios. |
| **Ngrok** | Servidor de Túnel Inverso | Expone el puerto `8000` de tu PC local a internet a través de una URL HTTPS segura para que Meta pueda enviar mensajes. |
| **Uvicorn** | Servidor Web ASGI | Levanta y ejecuta el framework FastAPI localmente en tu computadora. |
| **Meta Developers Portal** | Plataforma de Desarrollo | Consola en la nube donde se configura el Webhook, se obtienen los tokens y se administran los números de prueba. |
| **WhatsApp Messenger** | Aplicación Cliente | El canal final en tu celular desde donde el mecánico interactúa con el bot. |

---

## 2. ¿Qué Metodología de Desarrollo se está usando?

Para una tesis de Inteligencia Artificial y Machine Learning, debes responder que utilizaste **dos metodologías complementarias**:

### A. Metodología del Desarrollo del Software: SCRUM (Ágil)
* **Justificación**: Se seleccionó Scrum porque permitió un desarrollo iterativo e incremental. El proyecto se dividió en fases cortas (Sprints) para probar y validar componentes de forma independiente (primero el modelo de ML, luego el RAG, después la API de FastAPI, y finalmente la integración con WhatsApp).

### B. Metodología de Ciencia de Datos: CRISP-DM
*Esta es la metodología estándar de la industria y la academia para proyectos de Machine Learning.*
Consta de **6 etapas lógicas** que aplicaste en tu tesis:
1. **Comprensión del Negocio**: Identificación de la lentitud y errores en el diagnóstico de vehículos en los talleres de Carabayllo.
2. **Comprensión de los Datos**: Recopilación de los síntomas que los mecánicos reportan comúnmente.
3. **Preparación de los Datos**: Creación del dataset de síntomas (`dataset_sintomas.csv`), limpieza del texto en minúsculas y eliminación de acentos.
4. **Modelado**: Selección y entrenamiento del clasificador **Random Forest** usando vectorización **TF-IDF**.
5. **Evaluación**: Comparación del rendimiento en términos de precisión y tiempos de diagnóstico (Pre-test vs Post-test).
6. **Despliegue (Deployment)**: Conexión de la API del bot a la red de WhatsApp Business usando Ngrok como servidor de puente.

### C. Diseño Metodológico de la Tesis (Enfoque Científico)
* **Enfoque**: Cuantitativo (porque medimos tiempos de diagnóstico en minutos y porcentajes de precisión).
* **Tipo**: Aplicada (porque soluciona un problema práctico en un taller mecánico mediante tecnología).
* **Diseño**: Pre-experimental con pre-test y post-test (evaluamos los tiempos de diagnóstico de 30 vehículos antes de usar el chatbot y luego de usarlo).

---

## 3. Guía de Defensa ante el Jurado

Si el jurado te pregunta: **"¿Qué metodología usó y qué herramientas de software empleó?"**, responde así:

> *"Para el diseño científico y el desarrollo del modelo predictivo empleamos la metodología **CRISP-DM**, la cual nos guio en el ciclo de vida del dato: desde la comprensión de las fallas del taller, la preparación del dataset de síntomas, hasta el modelado con Random Forest y la evaluación del sistema. Para la construcción del software, adoptamos la metodología ágil **Scrum** por sprints iterativos. 
> 
> A nivel de herramientas de software, todo el entorno fue codificado en **Python** usando **Visual Studio Code**, administrado con **Git** y **GitHub**, expuesto públicamente mediante **Ngrok**, y conectado a la **Cloud API de WhatsApp Business** para el canal de atención final."*

