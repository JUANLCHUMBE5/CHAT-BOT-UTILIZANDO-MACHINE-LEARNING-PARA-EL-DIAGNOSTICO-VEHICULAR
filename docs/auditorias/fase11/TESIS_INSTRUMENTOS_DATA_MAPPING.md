# =====================================================================
# CARBOT — FASE 11.5: MAPEO DE DATOS DE INSTRUMENTOS DE TESIS
# DOCUMENTO: TESIS_INSTRUMENTOS_DATA_MAPPING.md
# =====================================================================

## 1. Contexto de la Investigación
- **Título de la Tesis**: *"Chatbot utilizando machine learning para el diagnóstico vehicular en talleres mecánicos en Carabayllo 2026"*
- **Diseño Experimental**: Preexperimental con medición Pre-test ($O_1$) y Post-test ($O_2$) sobre una muestra representativa de 60 casos reales de diagnóstico en el taller CARTER MOTOR'S E.I.R.L.
- **Variable Dependiente**: Diagnóstico Vehicular (Dimensiones: Predicción, Control de Información y Eficiencia).
- **Variable Independiente**: CarBot con Clasificador Linear SVM + TF-IDF y Asistente RAG.

---

## 2. Matriz Exhaustiva de Mapeo de Instrumentos (Anexo 2: Fichas 1, 2 y 3)

| Ficha Oficial | Campo de la Ficha | Origen en el Sistema | Tabla / Campo en Base de Datos | Automático / Manual | Aplicabilidad Fase | Validación Metodológica y Regla de Negocio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ficha 1** | Item | Contador incremental por registro | `validaciones_taller.item` | Automático | Pre-test y Post-test | Clave de ordenación secuencial de recolección en taller. |
| **Ficha 1** | Fecha | Fecha de atención del caso | `validaciones_taller.fecha` | Automático / Formulario | Pre-test y Post-test | Formato ISO `YYYY-MM-DD`. En Post-test deriva del inicio de atención. |
| **Ficha 1** | N.° Vehículos Atendidos | Placa pseudonimizada de vehículo | `validaciones_taller.placa_enmascarada`, `placa_hash` | Automático / Formulario | Pre-test y Post-test | Hash criptográfico HMAC-SHA256 (64 chars) para anonimización GDPR/LPDP. |
| **Ficha 1** | Diagnóstico Propuesto / Hipótesis | Hipótesis previa (Pre) o Predicción Top 1 ML (Post) | `validaciones_taller.chatbot_prediccion` / `diagnosticos.falla_predicha` | Pre: Manual / Post: Automático | Pre-test y Post-test | En Pre-test es la hipótesis manual del mecánico; en Post-test es la clase ML Top 1. |
| **Ficha 1** | Total Predicciones Realizadas | Conteo de casos evaluados con hipótesis emitida | `COUNT(validaciones_taller.prediccion_correcta)` | Automático | Pre-test y Post-test | Cada caso de diagnóstico equivale a una (1) predicción principal evaluable. |
| **Ficha 1** | Diagnóstico Físico Confirmado | Hallazgo real verificado en taller por mecánico | `validaciones_taller.falla_real` / `diagnosticos.conclusion_mecanico` | Manual (Mecánico / Validador) | Pre-test y Post-test | Desarme, prueba en elevador, reloj comparador, multímetro o escáner OBD. |
| **Ficha 1** | N.° Predicciones Correctas | Comparación validada (Predicción == Falla Real) | `validaciones_taller.prediccion_correcta` | Manual / Validación técnica | Pre-test y Post-test | Valor booleano/entero (1 = Acierto, 0 = Desacierto). Prohibida auto-asignación por IA. |
| **Ficha 1** | % Predicción Correcta (PPCF) | Cálculo agregado | `SUM(prediccion_correcta) / COUNT(*) * 100` | Automático (Cálculo) | Pre-test y Post-test | Fórmula: $\text{PPCF} = \frac{\sum \text{Aciertos}}{\text{Total Evaluados}} \times 100$. Maneja división por cero (0.0%). |
| **Ficha 2** | Item | Contador incremental | `validaciones_taller.item` | Automático | Pre-test y Post-test | Identificador correlativo del registro de control. |
| **Ficha 2** | Fecha | Fecha de registro | `validaciones_taller.fecha` | Automático / Formulario | Pre-test y Post-test | Fecha de la ficha de recepción e inspección técnica. |
| **Ficha 2** | Total Registros Evaluados (TRE) | Conteo de fichas inspeccionadas | `COUNT(validaciones_taller.id)` | Automático | Pre-test y Post-test | Total de casos con estado verificado en el período. |
| **Ficha 2** | Registros con 8 Campos Completos (RC) | Fichas que cumplen los 8 campos requeridos | `validaciones_taller.campos_completos` | Manual (Investigador) | Pre-test y Post-test | 1 si la ficha física/digital cuenta con los 8 campos completos; 0 si falta información. |
| **Ficha 2** | % Registros Completos (PRDC / RDC) | Ratio de completitud | `SUM(campos_completos) / COUNT(*) * 100` | Automático (Cálculo) | Pre-test y Post-test | Fórmula: $\text{RDC} = \frac{\text{RC}}{\text{TRE}} \times 100$. |
| **Ficha 3** | Item | Contador incremental | `validaciones_taller.item` | Automático | Pre-test y Post-test | Identificador del registro de eficiencia. |
| **Ficha 3** | Fecha | Fecha de atención | `validaciones_taller.fecha` | Automático / Formulario | Pre-test y Post-test | Fecha de ejecución del proceso diagnóstico. |
| **Ficha 3** | N.° Diagnósticos Evaluados | Conteo de atenciones con tiempo medido | `COUNT(validaciones_taller.id)` | Automático | Pre-test y Post-test | Casos diagnósticos auditados cronométricamente. |
| **Ficha 3** | Tiempo de Respuesta (minutos) | Duración de la sesión diagnóstica | `validaciones_taller.tiempo_diagnostico_minutos` | Pre: Cronómetro / Post: Telemetría | Pre-test y Post-test | En Pre-test es medido con cronómetro de taller; en Post-test deriva de inicio y fin de interacción. |
| **Ficha 3** | Suma Total de Tiempos (minutos) | Acumulador de tiempo de diagnóstico | `SUM(tiempo_diagnostico_minutos)` | Automático (Cálculo) | Pre-test y Post-test | Sumatoria de tiempos de respuesta diagnóstica en minutos. |
| **Ficha 3** | Tiempo Promedio de Respuesta (TPRD) | Promedio de duración | `AVG(tiempo_diagnostico_minutos)` | Automático (Cálculo) | Pre-test y Post-test | Fórmula: $\text{TPRD} = \frac{\sum \text{Tiempos}}{\text{Total Diagnósticos}}$. |

---

## 3. Indicadores de la Variable Independiente (CarBot con Machine Learning)

| Indicador | Definición Operacional | Origen en Base de Datos | Fórmula de Cálculo | Modo |
| :--- | :--- | :--- | :--- | :--- |
| **Indicador 1** | Porcentaje de síntomas registrados correctamente | `validaciones_taller.sintoma_registrado_correctamente` | $\frac{\sum \text{sintoma\_correcto}}{\text{Total Casos Verificados}} \times 100$ | Manual (Validador experto contrasta transcripción/texto vs audio/declaración) |
| **Indicador 2** | Porcentaje de datos procesados correctamente | `validaciones_taller.procesamiento_validado` | $\frac{\sum \text{procesamiento\_validado}}{\text{Total Casos Verificados}} \times 100$ | Automático/Verificado (Cumplimiento de Normalización + Extracción + Clasificación) |
| **Indicador 3** | Exactitud del modelo Machine Learning | `validaciones_taller.prediccion_correcta` (en Post-test) | $\frac{\sum \text{predicciones\_correctas}}{\text{Total Casos Post-test}} \times 100$ | Verificado físicamente contra la avería confirmada en elevador de taller |

---

## 4. Estado de la Definición de los 8 Campos (Ficha 2)

> [!WARNING]
> **ESTADO METODOLÓGICO OBLIGATORIO**:  
> `DEFINICION_8_CAMPOS_REQUIERE_CONFIRMACION_METODOLOGICA`
>
> La tesis y los antecedentes documentales del proyecto especifican la fórmula $RDC = \frac{RC}{TRE} \times 100$, donde $RC$ representa "Registros con los 8 campos completos".  
> No obstante, los 8 campos exactos no se encuentran taxativamente enumerados en una única tabla del marco metodológico institucional.  
> Por tanto, el software CarBot implementa:
> 1. Almacenamiento directo del cumplimiento del estándar por caso (`campos_completos = 1 | 0`).
> 2. Soporte para auditoría de campos mínimos diagnósticos del sistema:
>    - (1) Fecha de atención
>    - (2) Identificación del vehículo (Placa enmascarada / Hash)
>    - (3) Marca y Modelo
>    - (4) Síntoma reportado por el cliente
>    - (5) Hipótesis diagnóstica (Manual o ML)
>    - (6) Falla real comprobada físicamente
>    - (7) Método de confirmación técnica
>    - (8) Evidencia física registrada (foto, video, lectura de osciloscopio o escáner)
> 3. Se mantiene el reporte explícito `DEFINICION_8_CAMPOS_REQUIERE_CONFIRMACION_METODOLOGICA` hasta la validación final por el asesor metodológico de la universidad.

---

## 5. Trazabilidad de Auditoría y Aislamiento de Entornos

Para garantizar que los datos de prueba no contaminen la muestra oficial:
- Cada registro posee la columna `tipo_registro`:
  - `DEVELOPMENT`: Casos de prueba de desarrollo (excluidos de estadísticas).
  - `REGRESSION`: Casos de prueba automatizada y regresión (excluidos).
  - `THESIS_PRETEST`: Casos de trabajo de campo Pre-test oficiales.
  - `THESIS_POSTTEST`: Casos de trabajo de campo Post-test oficiales con CarBot.
- Vinculación relacional transparente:
  - `conversacion_id`: UUID de la sesión de mensajería (WhatsApp / Web).
  - `diagnostico_id`: UUID del diagnóstico generado por el motor CarBot.
