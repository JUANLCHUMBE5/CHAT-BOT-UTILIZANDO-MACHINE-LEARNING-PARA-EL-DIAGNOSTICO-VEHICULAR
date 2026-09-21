# RESULTADOS PRELIMINARES EXISTENTES — AUDITORÍA DE DATOS HISTÓRICOS Y DESARROLLO

**Proyecto:** CarBot — Chatbot con Machine Learning para Diagnóstico Vehicular  
**Tesis:** "Chatbot utilizando machine learning para el diagnóstico vehicular en talleres mecánicos en Carabayllo 2026"  
**Fecha de Auditoría:** 2026-09-19  
**Carácter de la Operación:** ESTRICTAMENTE READ-ONLY (Lectura Exclusiva, sin inserciones, modificaciones ni eliminaciones)  

---

## 1. Resumen Ejecutivo del Estado de los Datos

Se realizó una auditoría forense y de sólo lectura sobre la base de datos PostgreSQL y los archivos de respaldo del proyecto para responder con total precisión qué datos existen realmente, de dónde provienen y qué indicadores pueden o no calcularse legítimamente antes del inicio del trabajo de campo oficial.

Se identificaron **dos universos de datos completamente disjuntos**:

1. **Universo de Diagnósticos Reales de Desarrollo (`diagnosticos` en PostgreSQL):**
   - **79 registros** generados durante las pruebas funcionales del chatbot vía WhatsApp / API entre el **07 de agosto y el 19 de septiembre de 2026**.
   - Poseen trazabilidad real con `conversaciones` (31 conversaciones y 598 mensajes en PostgreSQL).
   - Registran telemetría real de inferencia ML (`tiempo_inferencia_ml_ms` de 10 a 67 ms) y duración total del pipeline (`duracion_ms` de 1 a 10 segundos).
   - Contienen **13 casos con evaluación técnica independiente** (Ground Truth físico aportado por mecánicos), de los cuales **8 fueron aciertos confirmados físicamente** y **5 fueron desaciertos descartados con identificación de la avería alternativa real**.
   - Estos registros pertenecen 100% a la categoría `DEVELOPMENT`.

2. **Universo de Borradores Sintéticos de Tracker (`validaciones_taller` en PostgreSQL):**
   - **1,930 registros** almacenados en `validaciones_taller`, todos en estado `borrador` y con la misma estampa de tiempo exacta de creación: `2026-09-01 23:25:21.903915+00:00`.
   - **Origen confirmado:** Fueron importados de forma masiva desde el archivo sintético `machine_learning/data/tracker_diagnosticos.csv` mediante el script `scripts/importar_tracker_postgresql.py` para probar la infraestructura de base de datos, concurrencia y persistencia.
   - Contienen casos sintéticos repetidos, pruebas de estrés con hilos (`Thread Test Car`) e incluso cadenas de prueba de seguridad e inyección SQL (`'; DROP TABLE vehiculos; -- <img src=x onerror=alert(1)>`).
   - Tienen `conversacion_id = NULL`, `diagnostico_id = NULL`, `mecanico_id = NULL` y `validado_por_id = NULL`.
   - **No representan atenciones reales de taller ni corresponden a la muestra de la tesis.**

---

## 2. Inventario Cuantitativo Global

| Concepto | Cantidad | Detalle / Observación |
|---|---|---|
| **Total de Registros Encontrados en Base de Datos** | **2,009** | 79 diagnósticos reales + 1,930 registros en tabla validaciones_taller |
| **DEVELOPMENT (Desarrollo / Pruebas reales)** | **79** | Diagnósticos interactivos con modelo ML C1 y WhatsApp |
| **REGRESSION (Pruebas de no regresión)** | **0** | No se etiquetaron registros como REGRESSION en base de datos histórica |
| **THESIS_PRETEST (Pre-test Oficial)** | **0 reales** | (30 registros en `validaciones_taller` tienen fase='Pre-test', pero son sintéticos de mayo 2026) |
| **THESIS_POSTTEST (Post-test Oficial)** | **0 reales** | (1,900 registros en `validaciones_taller` tienen fase='Post-test', pero son sintéticos de mayo-agosto 2026) |
| **Registros en Estado Verificado (`estado_registro='verificado'`)** | **0** | Ningún registro ha sido marcado como verificado oficial |
| **Registros en Estado Borrador (`estado_registro='borrador'`)** | **1,930** | Todos los registros de `validaciones_taller` están en borrador |
| **Registros en Estado Confirmado (`diagnosticos.estado='confirmado'`)** | **8** | Falla predicha confirmada físicamente por el mecánico en taller |
| **Registros en Estado Descartado (`diagnosticos.estado='descartado'`)** | **8** | Descartados por mecánico (5 con avería real especificada, 3 chats de prueba) |
| **Registros en Estado Generado (`diagnosticos.estado='generado'`)** | **63** | Consultas atendidas por CarBot sin retroalimentación de taller |
| **Casos con Ground Truth (Falla Real Confirmada Independientemente)** | **13** | 8 confirmados coincidentes + 5 descartados con avería real identificada |
| **Casos sin Ground Truth** | **66** | Diagnósticos de desarrollo sin comprobación física documentada |
| **Casos con Tiempo Válido de Taller en Minutos (`duracion_minutos`)** | **0 reales** | (Los 1,930 sintéticos tienen números mock de 1 a 41 min; los 79 reales tienen telemetría en ms) |
| **Casos con Ficha 2 Reconstruible (8 Campos Completos)** | **0** | Ningún caso de desarrollo posee los 8 campos formales auditables (`detalles_campos`) |

---

## 3. Clasificación de Calidad Metodológica (Niveles A, B, C, D)

Siguiendo las directrices de auditoría de la investigación:

- **NIVEL A — VALIDABLE (13 casos):**
  - Posee predicción CarBot, diagnóstico/falla real independiente confirmada por el mecánico, resultado binario (acierto/desacierto) y trazabilidad completa de sesión.
  - Corresponden a los 13 diagnósticos reales de desarrollo donde el mecánico validó la falla física en el vehículo.
- **NIVEL B — PARCIAL (66 casos):**
  - Posee predicción CarBot y conversación en WhatsApp, pero carece de confirmación técnica independiente en taller (`SIN_GROUND_TRUTH`) o contiene interacciones exploratorias.
- **NIVEL C — SOLO DESARROLLO (1,874 casos):**
  - Registros sintéticos importados de `tracker_diagnosticos.csv`. Útiles para pruebas de carga y persistencia, pero sin base empírica en talleres de Carabayllo.
- **NIVEL D — NO UTILIZABLE (56 casos):**
  - Registros de pruebas de estrés y seguridad: 16 casos con payloads de inyección SQL (`'; DROP TABLE vehiculos; --`) y 40 casos de `Thread Test Car`.

---

## 4. Auditoría de Indicadores de Tesis: ¿Qué es Legitímamente Calculable?

### Ficha 1: Predicción de Fallas Vehiculares (PPCF)
$$\text{PPCF} = \left(\frac{\text{Predicciones Correctas}}{\text{Total Predicciones Evaluadas}}\right) \times 100$$

- **Para la Muestra Oficial de Tesis (PRE-TEST y POST-TEST):**
  - **Estado:** `NO_CALCULABLE_CON_DATOS_EXISTENTES`
  - **Justificación Metodológica:** No se han realizado aún las 60 atenciones oficiales de campo en los talleres de Carabayllo. Cualquier cálculo sobre datos simulados violaría la integridad académica del proyecto.
- **Para los Casos Reales de Desarrollo (Nivel A):**
  - **Estado:** `CALCULABLE_CON_DATOS_EXISTENTES` *(Exclusivo para auditoría técnica de desarrollo)*
  - **Total de casos evaluados con Ground Truth independiente:** 13
  - **Aciertos confirmados físicamente:** 8
  - **Desaciertos con avería alternativa identificada:** 5
  - **PPCF Preliminar de Desarrollo:**
    $$\text{PPCF}_{\text{dev}} = \frac{8}{13} \times 100 = \mathbf{61.5\%}$$

#### Detalle de los 13 Casos Nivel A Evaluados:
1. `c9996cd2` | **Acierto (1)** | Pred: *Caja robotizada Dualogic/I-Motion* (29.3%) | Falla real: Confirmada físicamente.
2. `4b980774` | **Acierto (1)** | Pred: *Llantas desbalanceadas o desalineadas* (40.1%) | Falla real: Confirmada físicamente.
3. `fa5a72f3` | **Acierto (1)** | Pred: *Falla en bujías o bobinas de encendido (misfire)* (88.0%) | Falla real: Confirmada físicamente.
4. `c4abb355` | **Acierto (1)** | Pred: *Falla en servofreno (booster) o línea de vacío* (96.9%) | Falla real: Confirmada físicamente.
5. `2213092a` | **Acierto (1)** | Pred: *Disco de embrague desgastado o patinando* (80.0%) | Falla real: Confirmada físicamente.
6. `07f5c59d` | **Acierto (1)** | Pred: *Bomba de gasolina quemada o baja presión* (59.1%) | Falla real: Confirmada físicamente.
7. `8e2be030` | **Acierto (1)** | Pred: *Alternador defectuoso o placa de diodos* (71.0%) | Falla real: Confirmada físicamente.
8. `2cc4b9f0` | **Acierto (1)** | Pred: *Batería descargada o bornes sulfatados* (78.5%) | Falla real: Confirmada físicamente.
9. `d8e31b5a` | **Desacierto (0)** | Pred: *Rodajes de caja mecánica* (15.9%) | Falla real aportada por mecánico: *Consumo excesivo de gasolina / Inyectores*.
10. `e5851d95` | **Desacierto (0)** | Pred: *Llantas desbalanceadas* (37.9%) | Falla real aportada por mecánico: *Bieletas de la barra estabilizadora desgastadas*.
11. `3c28c12a` | **Desacierto (0)** | Pred: *Empaque de culata* (68.7%) | Falla real aportada por mecánico: *Falla en termostato o motoventilador de radiador*.
12. `95eebe8f` | **Desacierto (0)** | Pred: *Empaque de culata* (63.7%) | Falla real aportada por mecánico: *Fuga en mangueras de refrigerante o radiador picado*.
13. `6049fc31` | **Desacierto (0)** | Pred: *Falla en sensor de oxígeno* (98.3%) | Falla real aportada por mecánico: *Bomba de gasolina quemada o baja presión*.

---

### Ficha 2: Control de Información Diagnóstica (RDC)
$$\text{RDC} = \left(\frac{\text{Registros con los 8 Campos Completos}}{\text{Total Registros Evaluados}}\right) \times 100$$

- **Estado:** `NO_CALCULABLE_CON_DATOS_EXISTENTES`
- **Justificación Metodológica:**
  - En los 79 diagnósticos de WhatsApp, la interacción conversacional no recolectó la totalidad de los 8 campos formales (especialmente placa, kilometraje, año, combustible y registro de tiempo en minutos cronometrados en taller).
  - Los 1,930 registros sintéticos de `validaciones_taller` poseen un flag booleano arbitrario (`campos_completos = 1` en 1922 casos) generado automáticamente por un script mock, sin desglose ni auditoría de subcampos (`detalles_campos = NULL`).
  - Por tanto, no existe ningún caso histórico que cumpla de forma verificable los 8 campos documentados en la Fase 11.5.1. RDC debe evaluarse exclusivamente con los instrumentos oficiales de campo.

---

### Ficha 3: Eficiencia del Diagnóstico (TPRD)
$$\text{TPRD} = \frac{\sum \text{Tiempo Diagnóstico en Minutos}}{\text{Total Diagnósticos Evaluados}}$$

- **Estado:** `NO_CALCULABLE_CON_DATOS_EXISTENTES`
- **Justificación Metodológica:**
  - El indicador TPRD mide el tiempo en minutos del proceso diagnóstico del mecánico en el taller mecánico (desde la recepción del automóvil hasta el dictamen técnico).
  - En los registros reales de desarrollo sólo se dispone de la telemetría del software:
    - Tiempo de inferencia ML: **10 a 67 ms** (promedio: **35.2 ms**).
    - Tiempo de respuesta del chatbot: **1.3 a 5.8 segundos**.
  - No se dispone de la medición física del tiempo de taller en minutos. Los números de 1 a 41 minutos presentes en los 1,930 registros de `validaciones_taller` son sintéticos y no corresponden a observaciones empíricas.

---

## 5. Auditoría Forense de los 1,930 Borradores en `validaciones_taller`

1. **¿Por qué existen?**
   Fueron importados a PostgreSQL el 01 de septiembre de 2026 para validar la infraestructura relacional de la aplicación, comprobar que las vistas del panel no colapsaran con volumen de datos y certificar las consultas concurrentes.
2. **Rango de Fechas:**
   Fechas asignadas en el CSV: del `2026-05-01` al `2026-08-31`. Fecha real de inserción en PostgreSQL: `2026-09-01 23:25:21`.
3. **Origen:**
   Archivo CSV local: `machine_learning/data/tracker_diagnosticos.csv`, procesado por `scripts/importar_tracker_postgresql.py`.
4. **¿Fueron generados automáticamente?**
   Sí. Se generaron mediante scripts sintéticos de generación de pruebas de carga y concurrencia.
5. **¿Son duplicados?**
   Presentan alta redundancia: 901 registros de *Toyota Yaris* con *Pedal de freno esponjoso* o *Chillido de frenos*, y 705 registros de *Vehiculo Generico*.
6. **¿Corresponden a conversaciones de WhatsApp?**
   No. El 100% de los 1,930 registros tienen `conversacion_id = NULL`.
7. **¿Tienen `diagnostico_id`?**
   No. El 100% de los 1,930 registros tienen `diagnostico_id = NULL`.
8. **¿Tienen `falla_real` y `prediccion_correcta`?**
   Poseen cadenas de texto sintéticas (`falla_real` rellenada con textos mock y `prediccion_correcta = 1` en el 99.5% de los casos).
9. **¿Contienen datos útiles para la tesis?**
   No contienen valor empírico para la contrastación de hipótesis de la tesis.
10. **Recomendación Operativa para el Trabajo de Campo:**
    - Los registros NO deben borrarse durante las fases de auditoría técnica para preservar la reproducibilidad histórica.
    - Sin embargo, gracias a la migración de Fase 11.5 (`20260919_01_separacion_fases_tesis.py`), estos 1,930 registros están en estado `borrador` y su visualización y cómputo está aislada de la muestra oficial de 60 casos reales de tesis mediante el filtro `tipo_registro IN ('THESIS_PRETEST', 'THESIS_POSTTEST')` en conjunción con `estado_registro = 'verificado'`.
    - Antes de iniciar la recolección oficial con los mecánicos, se recomienda reclasificarlos administrativamente o excluirlos formalmente (`estado_registro = 'excluido'`) para dejar la bandeja oficial completamente limpia.

---

## 6. Estado Actual Real de CarBot

### A. Infraestructura de Tesis
- **Persistencia:** Implementada y validada en PostgreSQL con esquemas para las 3 fichas y auditoría de 8 campos (Fase 11.5.1).
- **Aislamiento Muestral:** Creado y blindado a nivel de base de datos con Check Constraints (`DEVELOPMENT`, `REGRESSION`, `THESIS_PRETEST`, `THESIS_POSTTEST`).
- **Exportación CSV:** Implementada con sanitización estricta contra inyección de fórmulas.
- **Preparación para los 60 Casos:** La arquitectura está lista para recibir las 60 atenciones reales de campo sin restricciones de esquema.

### B. Motor Diagnóstico (Machine Learning & RAG)
- **Modelos ML C1:** Vectorizador TF-IDF, clasificador Linear SVM multiclase y modelo macro-sistema congelados e inmutables (hashes SHA-256 certificados al 100%).
- **RAG Candidate V1:** Índice FAISS de 239 procedimientos técnicos automotrices congelado e inmutable.
- **Exactitud en Desarrollo:** 61.5% de acierto en los 13 casos con confirmación física independiente en taller.
- **Comportamiento Conversacional:** Pipeline auditado y corregido (detección de polaridad, suficiencia de información, directrices de comprobación física preliminar).

### C. Integración y Runtime
- **API Server (FastAPI):** Operativo y receptivo en puerto 8000.
- **Worker Daemon:** Activo en segundo plano (PID 7092, versión 11.5.0).
- **Frontend (React / Vite):** Compilado sin errores y sincronizado con contratos de validación.
- **WhatsApp Cloud API:** Integración implementada a nivel de orquestador y webhook; declarada en estado `WHATSAPP_PENDING_MANUAL_VALIDATION` a la espera de las pruebas en vivo con dispositivos móviles en el taller.

---

## 7. Lista de Aspectos Pendientes Antes del Trabajo de Campo

1. Realizar la prueba manual en vivo vía WhatsApp (Meta Cloud API) con teléfono real para verificar la interacción natural del mecánico en taller.
2. Definición formal/administrativa sobre el destino de los 1,930 borradores sintéticos (mantenerlos en `borrador` / marcarlos `excluido` para que no estorben la vista del evaluador).
3. Capacitación breve al evaluador/investigador en el uso del formulario de registro de Ficha 1, 2 y 3 en el panel administrativo.
4. Inicio ordenado del trabajo de campo: recolección de los primeros casos del Pre-test tradicional ($O_1$) y posterior aplicación asistida por CarBot ($O_2$).
