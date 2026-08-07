# Guía para la Obtención y Configuración de la API de Gemini
## Tesis: Chatbot de Diagnóstico Vehicular Híbrido en Carabayllo

Esta guía explica paso a paso cómo obtener la clave API (API Key) de Google AI Studio, la configuración del modelo mediante `GEMINI_MODEL`, las cuotas de tasa (RPM / RPD), el nivel gratuito vs pagado, la cola de trabajos persistente y el modo degradado de contingencia.

---

## 1. Obtención de la API Key

La clave de API se obtiene desde el portal oficial **Google AI Studio**:

1. **Ingresar a la plataforma**:
   Navega a [https://aistudio.google.com/](https://aistudio.google.com/)

2. **Iniciar sesión**:
   Inicia sesión con tu cuenta de Google / Gmail personal o institucional.

3. **Generar la clave de API**:
   - En la barra lateral izquierda, haz clic en **"Get API key"** (Obtener clave de API).
   - Haz clic en **"Create API key"** -> *"Create API key in new project"*.
   - Copia la clave generada (comienza con el prefijo `AIzaSy...`).

4. **Configurar en el proyecto**:
   Abre el archivo `.env` en la raíz de tu proyecto ([.env](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/.env)) y configura las variables:

   ```env
   GEMINI_API_KEY="AIzaSy...tu_clave_copiada_aqui..."
   GEMINI_MODEL="gemini-3.5-flash-lite"
   GEMINI_USE_FREE_TIER=true
   GEMINI_INPUT_PRICE_PER_MILLION=0.075
   GEMINI_OUTPUT_PRICE_PER_MILLION=0.300
   GEMINI_MAX_REQUESTS_PER_MINUTE=12
   GEMINI_MAX_REQUESTS_PER_DAY=18
   ```

---

## 2. Configuración del Modelo y Gestión de Tarifas

El modelo predeterminado es **`gemini-3.5-flash-lite`**, configurable mediante la variable de entorno `GEMINI_MODEL`.

### Nivel Gratuito (`GEMINI_USE_FREE_TIER=true`)
- **Costo en DB (`uso_api.costo_estimado`)**: Se registra como `$0.000000 USD`.
- **Conteo de Tokens**: Los tokens de entrada (`promptTokenCount`) y salida (`candidatesTokenCount`) se cuantifican y registran en PostgreSQL independientemente del costo.

### Plan Pagado (`GEMINI_USE_FREE_TIER=false`)
- **Cálculo de Tarifas**: Aplica las tarifas por millón de tokens configuradas en `GEMINI_INPUT_PRICE_PER_MILLION` (default `$0.075 USD`) y `GEMINI_OUTPUT_PRICE_PER_MILLION` (default `$0.300 USD`).

---

## 3. Control de Cuotas (RPM / RPD) y Cola Persistente (`trabajos_gemini`)

 Para proteger la cuota del taller en Carabayllo y evitar sobrecostos o bloqueos HTTP 429 de Google, el sistema implementa:

1. **Límite de Tasa por Minuto (RPM = 12)**:
   - Controlado vía `GeminiRateLimiter` en ventana deslizante de 60 segundos.
   - Las consultas dentro de los primeros 12 slots por minuto se procesan inmediatamente.

2. **Límite Diario (RPD = 18)**:
   - Controlado vía `GEMINI_MAX_REQUESTS_PER_DAY`.
   - Al alcanzar el tope diario, las solicitudes recurren de forma segura al **Modo Degradado (`diagnostico_degradado_ml_rag`)** o quedan pendientes en cola sin saturar la API de Google.

3. **Cola de Trabajos Persistente (`trabajos_gemini`)**:
   - Las solicitudes que superan la ventana deslizante se almacenan en la tabla relacional `trabajos_gemini` de PostgreSQL.
   - El worker asíncrono background descola las solicitudes pendientes en estricto orden FIFO a medida que se liberan slots de cuota.
   - Al descolar y procesar una solicitud, se actualiza el estado de la fila en `diagnosticos` de `en_cola_gemini` a `completo_ml_rag_llm` y se envía automáticamente el segundo mensaje con la síntesis final al mecánico por WhatsApp (Meta Graph API o Twilio).

4. **Modo Degradado de Contingencia (`diagnostico_degradado_ml_rag`)**:
   - Si la API de Gemini falla (ej. error HTTP 500 o falta de red), el sistema genera instantáneamente una respuesta estructurada en 3 secciones combinando la predicción del **Modelo ML** y el fragmento del **Motor RAG**, garantizando continuidad operativa en el taller.
