# Guía del repositorio

## Estructura del proyecto y organización de módulos

CarBot es un sistema por capas construido con React y FastAPI. El backend se encuentra en `backend/src/`: mantenga los casos de uso en `application/`, las reglas de negocio y DTOs en sus módulos actuales, la persistencia y adaptadores externos en `infrastructure/`, y los contratos HTTP en `interfaces/`. Las pruebas están en `backend/tests/` y las migraciones Alembic en `backend/alembic/versions/`. El cliente React/Vite está en `frontend/src/`; sus pruebas se ubican en `frontend/tests/harness/`. Use `machine_learning/` para entrenamiento y artefactos ML, `infrastructure/` para recursos de despliegue, `scripts/` para automatizaciones y `docs/` para documentación técnica.

## Límite de tamaño de archivos y modularidad (Clean Architecture)

- **Límite de líneas**: Ningún archivo fuente debe superar las 400-500 líneas de código (estricto: nunca más de 1000). Si un componente o servicio supera este tamaño, debe modularizarse inmediatamente en subcarpetas y submódulos especializados por responsabilidad única (Single Responsibility Principle).
- **Estructura jerárquica en subcarpetas**: Cada módulo funcional debe organizarse en subcarpetas y sub-subcarpetas bien delimitadas (`models/`, `services/`, `repositories/`, `hooks/`, `components/`). Evitar carpetas planas con decenas de scripts acumulados.
- **Aislamiento de versiones y experimentos**: Todo script de prueba, prototipo, versión previa o experimento exploratorio (especialmente en `machine_learning/`) debe ubicarse dentro de subcarpetas `experiments/` o `versions/`, manteniendo la carpeta principal reservada estrictamente para el pipeline canónico y reproducible.
- **Reutilización y Hooks en Frontend**: Extraer lógica de estado, efectos y llamadas HTTP de componentes React extensos hacia custom hooks modulares (`hooks/`), manteniendo las vistas (`views/`) enfocadas únicamente en composición visual (< 350 líneas).
- **Servicio Webhook**: Desacoplar la recepción de webhooks en submódulos dedicados (`identity_resolver.py`, `validation_workflow.py`, `diagnostic_persister.py`, `offline_processor.py`), manteniendo `webhook_service.py` como un orquestador conciso (< 350 líneas).
- **Reglas de interacción en WhatsApp**:
  - No repetir la transcripción de notas de voz al mecánico (`🎤 Entendí: "..."`).
  - No interrumpir con preguntas genéricas de combustible cuando ya existen códigos DTC (`P0301`, etc.) o piezas mecánicas identificadas.
  - Procesar respuestas directas (`GLP`, `GNV`, `gasolina`) sin bucles de aclaración redundantes.
  - Proveer diagnóstico diferencial (Top 2 y Top 3 de probabilidades ML) en el resumen para comparación técnica del mecánico.
  - Para averías mecánicas puras sin control electrónico (desbalanceo/desalineación de ruedas, alabeo de discos, desgaste de pastillas, holgura de rótulas/bieletas o embrague patinando), nunca sugerir escaneo DTC. La primera prueba sugerida debe ser siempre física o metrológica (balanceo dinámico, alineación láser, reloj comparador, inspección en elevador).


## Comandos de desarrollo, compilación y pruebas

- `./iniciar_carbot.cmd`: inicia verificaciones de PostgreSQL, API, worker de colas, panel Vite y túnel de WhatsApp en Windows.
- `./scripts/verificar_proyecto.ps1`: ejecuta la validación completa: Ruff, Pytest, Oxlint, compilación TypeScript y pruebas del frontend.
- `cd backend; ../.venv/Scripts/python.exe -m alembic upgrade head`: aplica las migraciones de base de datos.
- `cd backend; ../.venv/Scripts/python.exe -m pytest -q`: ejecuta únicamente las pruebas del backend.
- `cd frontend; npm ci; npm run verify`: instala dependencias bloqueadas y valida el frontend.
- `docker compose up --build`: levanta API, worker, PostgreSQL y Redis en contenedores.

## Estilo de código y convenciones de nombres

Respete `.editorconfig`: UTF-8, salto de línea final y cuatro espacios en Python. Ruff controla importaciones y errores esenciales, con un límite de 110 caracteres. Use `snake_case` para funciones y variables de Python, `PascalCase` para clases y anotaciones de tipo en interfaces públicas. En TypeScript use dos espacios, `camelCase` internamente, `PascalCase` para componentes y tipos, y `snake_case` solo al reproducir contratos JSON. Las variables de entorno deben usar `UPPER_SNAKE_CASE` y documentarse en `.env.example`.

## Criterios para las pruebas

Pytest descubre archivos `test_*.py` dentro de `backend/tests/`. Marque con `real_gemini` las pruebas externas que consuman cuota. La cobertura de `backend/src` debe mantenerse en 55 % o más. Agregue regresiones para estados de cola, aislamiento entre talleres, autenticación y rutas de error. Los cambios del frontend deben superar `npm run test:harness`.

## Commits y pull requests

El historial sigue Conventional Commits, normalmente en español: `feat: ...`, `fix(carbot): ...`, `refactor: ...` y `docs: ...`. Mantenga cada commit enfocado. El pull request debe resumir el cambio, indicar las validaciones ejecutadas, advertir migraciones o nuevas variables, vincular la incidencia e incluir capturas cuando modifique la interfaz. Nunca confirme `.env`, credenciales, datos operativos, cachés generadas ni modelos binarios sin revisión.

## Reglas Metodológicas de Tesis y Arquitectura CarBot (Obligatorias)

1. **Arquitectura ML del Proyecto**:
   - El modelo de Machine Learning es estrictamente **Linear SVM con vectorización TF-IDF** (clasificador multiclase vehicular). Nunca hacer referencia a Random Forest ni XGBoost para el clasificador principal.

2. **Integridad Académica y Resultados de Tesis**:
   - **Cero resultados simulados como oficiales**: Nunca presentar datos sintéticos o de prueba como "Muestra Oficial" ni declarar hipótesis aceptadas ($HE_1, HE_2, HE_3$ o valores $p$) antes de que los mecánicos registren los 60 casos reales en el taller.
   - **Estado del trabajo de campo**: Siempre mostrar el estado real: *"Trabajo de campo pendiente. Los resultados pretest y postest se calcularán exclusivamente con registros reales recopilados y verificados durante la aplicación de los instrumentos. Avance actual: {reales} de 60 registros"*.
   - **Aislamiento de datos demo**: Cualquier dato sintético o de maqueta debe estar en un modo demostración explícito, con advertencia visible, y totalmente excluido de las métricas y exportaciones oficiales de la tesis.

3. **Operacionalización de la Variable Independiente (CarBot con ML)**:
   - Indicador 1: **Porcentaje de síntomas registrados correctamente** (mensaje original vs. registro estructurado validado).
   - Indicador 2: **Porcentaje de datos procesados correctamente** (casos que completan normalización, extracción y clasificación / total evaluados).
   - Indicador 3: **Exactitud del modelo de Machine Learning** (predicciones coincidentes con la falla confirmada físicamente en taller / total evaluados).
   - Las métricas de tiempo, F1-macro y uso de RAG/Gemini son complementarias.

4. **Telemetría y Tiempos de Respuesta**:
   - No usar rangos prefijados o estáticos (e.g. "<25 ms"). Calcular a partir de mediciones reales.
   - Separar con claridad:
     - a) **Tiempo de inferencia del modelo ML** (procesamiento del vector TF-IDF + Linear SVM).
     - b) **Tiempo total de respuesta del pipeline** (desde recepción del webhook de WhatsApp hasta envío del mensaje al mecánico).

5. **Pruebas Estadísticas de Contraste**:
   - No fijar la prueba inferencial como "pareada" por defecto. Mantener el contraste como "Pendiente de definición con el asesor estadístico según la naturaleza de la muestra (pareada vs. muestras independientes)".

6. **Separación entre Dataset ML y Corpus RAG**:
   - Los síntomas coloquiales de clientes/mecánicos pertenecen exclusivamente al dataset de entrenamiento de Machine Learning (clasificación multiclase).
   - El corpus RAG está reservado estrictamente para manuales técnicos de servicio de fabricantes (OEM), diagramas eléctricos, torques, tolerancias y procedimientos formales de taller. Nunca mezclar quejas o síntomas dentro de FAISS/RAG.

7. **Orden Cronológico de Historiales y Consultas**:
   - Todos los listados, tablas de diagnósticos y registros históricos en el backend y frontend deben ordenarse de forma descendente (`creado_en DESC`) para mostrar las consultas más recientes en primer lugar.

8. **Invariante de Entrega de Mensajes y Manejo de Cola (Gemini Worker)**:
   - **Garantía de respuesta**: Todo mensaje recibido por webhook que genere un acuse preliminar ("⏳ Analizando consulta...") DEBE culminar con el envío del reporte de diagnóstico al usuario.
   - **Comprobación de cuota previa a la reserva**: El bucle del worker (`rate_limiter.py`) debe comprobar cuota y tiempos de enfriamiento antes de reservar registros en PostgreSQL (`obtener_siguiente_pendiente_bloqueado`), impidiendo bloqueos huérfanos.
   - **Fallback degradado obligatorio**: Si un trabajo encolado supera el límite máximo de reintentos o la API externa no responde, el sistema debe activar automáticamente el modo degradado (`forzar_degradado=True`) utilizando ML + RAG para enviar el diagnóstico a WhatsApp sin dejar al mecánico en espera.

9. **Expansión y Calidad del Conocimiento Técnico (ML y RAG)**:
   - **Dataset ML (Linear SVM)**: Las expansiones de datos deben incluir cadenas sintomáticas causales (causa en marcha vs. consecuencia en reposo) para que el clasificador pondere con certidumbre >= 70% las averías de origen dinámico.
   - **Corpus RAG (FAISS)**: Los procedimientos técnicos añadidos deben incluir tolerancias eléctricas y metrológicas específicas de taller (voltajes de reposo, rangos de carga 13.8V-14.4V, pruebas de rizado de diodos con osciloscopio, consumos parásitos) respaldados en manuales OEM.

