# MATRIZ DE TRAZABILIDAD: INSTRUMENTO DE RECOLECCIÓN VS. SISTEMA CARBOT
**CARBOT — TESIS DE GRADO 2026**  
**Fecha de emisión:** 20 de Septiembre de 2026  
**Documento Oficial:** MATRIZ METODOLÓGICA Y TÉCNICA DE RECOLECCIÓN EN TALLER  
**Área:** Metodología de Investigación y Arquitectura de Datos  

---

## 1. INTRODUCCIÓN Y ALINEACIÓN METODOLÓGICA

El presente documento establece la correspondencia unívoca entre la **operacionalización de variables de la tesis**, las **fichas de recolección de datos (Anexo 2 del proyecto)**, el modelo relacional de base de datos (`ValidacionTaller` en PostgreSQL), la interfaz de usuario en React y el archivo de exportación tabular oficial en formato **LONG**.

### Declaración de Invariantes Metodológicos:
1. **Población y Muestra:** La muestra oficial comprende un total de **60 observaciones diagnósticas reales e independientes** distribuidas en:
   - **30 registros Pre-test ($N_{pre} = 30$):** Diagnóstico tradicional sin asistencia del chatbot.
   - **30 registros Post-test ($N_{post} = 30$):** Diagnóstico asistido tecnológicamente por CarBot.
2. **Estructura Tabular LONG:** Cada fila del dataset de exportación representa una **unidad observacional vehicular única**. Queda estrictamente prohibido generar identificadores ficticios de emparejamiento (`caso_pareja_id`) o transformar forzadamente los datos a formato WIDE, dado que los vehículos atendidos en la fase Pre-test y en la fase Post-test corresponden a unidades automotrices distintas ingresadas al taller.
3. **Definición de Prueba Estadística:**  
   `PENDIENTE_CONFIRMACION_ASESOR_ESTADISTICO = TRUE`  
   El contraste inferencial final (e.g., prueba $U$ de Mann-Whitney / $t$ de Student para muestras independientes o prueba de proporciones según corresponda a la normalidad de los datos) será determinado conjuntamente con el asesor estadístico de la tesis sobre la muestra real de 60 casos.

---

## 2. MATRIZ DE TRAZABILIDAD COMPLETA: VARIABLES, INDICADORES Y SISTEMA

| VARIABLE DE TESIS | DIMENSIÓN | INDICADOR | CAMPO EN BASE DE DATOS (`ValidacionTaller`) | CAMPO EN INTERFAZ (UI) | COLUMNA DE EXPORTACIÓN OFICIAL | FUENTE PRE-TEST | FUENTE POST-TEST |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V.I.: Chatbot con Machine Learning** | Registro de Entrada | **Indicador 1:** % de síntomas registrados correctamente | `sintoma_registrado_correctamente` (INTEGER 0/1) | Switch "Síntoma Registrado Correctamente" | `Ind1_Sintoma_Validado` | N/A (Diagnóstico tradicional sin chatbot) | Registro estructurado comparado contra síntoma expresado por el cliente en WhatsApp |
| **V.I.: Chatbot con Machine Learning** | Procesamiento Pipeline | **Indicador 2:** % de datos procesados correctamente | `procesamiento_validado` (INTEGER 0/1) | Indicador "Procesamiento Validado" | `Ind2_Procesamiento_Validado` | N/A (Diagnóstico tradicional sin chatbot) | Evaluación de 3 etapas: `normalizacion_correcta`, `extraccion_correcta` y `clasificacion_procesada` |
| **V.I.: Chatbot con Machine Learning** | Clasificación Algorítmica | **Indicador 3:** Exactitud del modelo de Machine Learning | `prediccion_correcta` (INTEGER 0/1) | Selector "Resultado del Diagnóstico" | `PPCF_Ficha1_Prediccion_Correcta` | N/A (En Pre-test evalúa hipótesis del mecánico tradicional) | Comparación entre `chatbot_prediccion` (Linear SVM) y `falla_real` confirmada físicamente |
| **V.D.: Eficacia del Diagnóstico Vehicular** | Acierto Diagnóstico | **PPCF (Ficha 1):** Porcentaje de predicciones correctas de falla | `prediccion_correcta` (INTEGER 0/1) | Selector "¿Diagnóstico / Hipótesis Correcta?" | `PPCF_Ficha1_Prediccion_Correcta` | Coincidencia de la hipótesis tradicional del mecánico vs. falla física real | Coincidencia de la sugerencia diagnóstica de CarBot vs. falla física real |
| **V.D.: Eficacia del Diagnóstico Vehicular** | Completitud Documental | **PRDC (Ficha 2):** Porcentaje de registros diagnósticos completos | `campos_completos` (INTEGER 0/1) y `cantidad_campos_completos` (INTEGER 0..8) | Badge "Campos Completos (8/8)" | `PRDC_Ficha2_Campos_Completos` & `Ficha2_Cantidad_Campos_Completos` | Verificación de 8 campos obligatorios de la orden física de trabajo | Verificación de 8 campos estructurados capturados en la ficha técnica digital |
| **V.D.: Eficacia del Diagnóstico Vehicular** | Eficiencia Temporal | **TPRD (Ficha 3):** Tiempo promedio de respuesta / diagnóstico | `tiempo_diagnostico_minutos` (INTEGER > 0) | Input "Tiempo Diagnóstico (minutos) *" | `TPRD_Ficha3_Tiempo_Minutos` | Cronometraje manual del proceso diagnóstico tradicional en taller | Cronometraje manual del proceso diagnóstico asistido con CarBot |

---

## 3. SEPARACIÓN METODOLÓGICA: TIEMPO METODOLÓGICO VS. TELEMETRÍA DE SISTEMA

Para evitar cualquier objeción en la sustentación de tesis, se establece la distinción categórica entre la variable metodológica de investigación y las métricas computacionales de telemetría:

### A. Variable Metodológica Oficial de Tesis (Ficha 3 - Anexo 2):
- **Campo:** `tiempo_diagnostico_minutos` (columna exportada: `TPRD_Ficha3_Tiempo_Minutos`).
- **Definición:** Intervalo de tiempo transcurrido, medido en minutos por el observador o mecánico, desde la recepción formal del vehículo y descripción de la queja hasta la determinación y confirmación física concluyente de la causa raíz de la avería.
- **Naturaleza:** Variable de resultado del proceso humano-tecnológico en taller. No puede ser reemplazada por una medición puramente algorítmica.

### B. Telemetría Computacional del Sistema (Métricas Auxiliares de Rendimiento):
- **Campo:** `tiempo_inferencia_ml_ms`
  - *Definición:* Latencia de inferencia computacional del modelo Linear SVM (extracción TF-IDF + cálculo vectorial). Típicamente entre 15 ms y 85 ms.
- **Campos:** `inicio_sistema_at`, `fin_sistema_at`, `duracion_sistema_segundos`
  - *Definición:* Marcas de tiempo ISO UTC y duración de la sesión web/conversacional en CarBot.
- **Rol en la Tesis:** Métricas descriptivas de eficiencia de software que sustentan el rendimiento no funcional de la arquitectura tecnológica, reportadas como información complementaria pero **nunca en sustitución del tiempo de diagnóstico del mecánico**.

---

## 4. DESGLOSE DETALLADO DE LOS 8 CAMPOS DE LA FICHA 2 (ANEXO 2)

El indicador **PRDC** evalúa si la ficha diagnóstica reúne la totalidad de los 8 campos estipulados por el instrumento de recolección validado por juicio de expertos:

| Identificador Campo | Nombre del Campo en Anexo 2 | Campo Relacional DB | Regla de Completitud Técnica |
| :---: | :--- | :--- | :--- |
| **Campo 1** | Código de registro correlativo | `item` | Entero autoincremental asignado por PostgreSQL. |
| **Campo 2** | Fecha de atención del servicio | `fecha` | Formato `YYYY-MM-DD` válido. |
| **Campo 3** | Datos generales del vehículo | `marca_modelo`, `vehiculo_anio`, `vehiculo_kilometraje`, `vehiculo_combustible`, `vehiculo_transmision` | Objeto estructurado con los 5 atributos vehiculares presentes y no vacíos. |
| **Campo 4** | Síntomas reportados | `sintoma` | Cadena no vacía describiendo la manifestación inicial del cliente. |
| **Campo 5** | Descripción del síntoma | `descripcion_sintoma` | Cadena técnica detallando condiciones de falla (carga, RPM, temperatura). |
| **Campo 6** | Sistema afectado probable | `sistema_afectado_probable` | Identificación del macro-sistema o subsistema automotriz preliminar. |
| **Campo 7** | Diagnóstico confirmado | `falla_real` | Diagnóstico mecánico final verificado físicamente mediante prueba de taller. |
| **Campo 8** | Tiempo de atención registrado | `tiempo_diagnostico_minutos` | Valor entero positivo mayor que cero minutos. |

*Cálculo del Indicador:* Si los 8 campos están completos, `campos_completos = 1` y `cantidad_campos_completos = 8`. Si falta cualquiera de ellos, `campos_completos = 0`.

---

## 5. AUDITORÍA DEL ARCHIVO DE EXPORTACIÓN TABULAR (CSV LONG)

El endpoint oficial `/api/v1/validacion-taller/exportar-fichas-anexo2-csv` genera un reporte tabular con las siguientes garantías:
1. **Aislamiento absoluto:** Únicamente exporta registros con `estado_registro = 'verificado'`, `tipo_registro IN ('THESIS_PRETEST', 'THESIS_POSTTEST')` y `fase != 'Piloto'`.
2. **Protección contra inyección:** Cada celda es sanitizada contra *CSV Formula Injection* (prefijando comilla simple a caracteres `=`, `+`, `-`, `@`, `\t`, `\r`).
3. **Encabezado de metadatos:** Incluye constancia institucional de la Universidad César Vallejo, periodo evaluado y nota metodológica sobre el contraste inferencial pendiente de definición con el asesor.
4. **Comportamiento ante muestra en cero (Pre-campo):** Si no existen registros verificados al momento de consultar, el endpoint responde con un código controlado HTTP 400 (`"No existen registros verificados para exportar en el periodo seleccionado."`), certificando que el sistema no exporta datos ficticios ni sintéticos antes del inicio de la recolección presencial.
