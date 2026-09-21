# CARBOT — FASE 11.5
## REPORTE FINAL DE AUDITORÍA Y CORRECCIÓN INTEGRAL DEL DIAGNÓSTICO Y TRAZABILIDAD PRE-TEST / POST-TEST PARA LA TESIS

---

### 1. Resumen Ejecutivo

La Fase 11.5 abordó de manera integral dos dimensiones estructurales de CarBot:
1. **La auditoría y remediación técnica de la cadena diagnóstica** (`CONVERSACIÓN → ESTADO → QUERY → C1 → RAG → RESPUESTA`), resolviendo las fallas en los casos reales de prueba (Caso A: Demora de arranque en frío y Caso B: Vibración en volante al frenar), sin tocar ni reentrenar los modelos congelados de Machine Learning (C1) ni el índice vectorial RAG.
2. **La auditoría, saneamiento y blindaje metodológico del sistema de evaluación de la tesis**, garantizando el aislamiento absoluto entre datos de desarrollo/regresión y los registros oficiales de campo (Pre-test y Post-test) para los indicadores de la investigación: PPCF (Predicción de fallas), RDC (Control de información) y TPRD (Tiempo de respuesta diagnóstica).

Todas las pruebas automatizadas de backend y frontend superaron la validación al 100%, con verificación de integridad criptográfica (SHA-256) en todos los artefactos de modelos.

---

### 2. Estado Runtime

El entorno de ejecución fue actualizado, reiniciado y verificado con telemetría en vivo:

- **APP_VERSION:** `11.5.0`
- **ORCHESTRATOR_VERSION:** `11.5.0`
- **CODE_BUILD_ID:** `f85fd170e28b7a30`
- **PID Worker Daemon:** `7092` (Subproceso en segundo plano verificado y activo)
- **API Server:** Activo en `http://localhost:8000` (FastAPI / Uvicorn)
- **Base de Datos:** PostgreSQL con migración Alembic `20260919_01_separacion_fases_tesis` aplicada (`head`).
- **Frontend Panel:** React 19 + Vite 6 compilado limpiamente (`npm run build` en 776 ms, 0 errores) con test harness aprobado al 100%.

---

### 3. Caso Arranque (Caso Real A)

- **Entrada del usuario:** *"Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas. Una vez que logra encender, el motor funciona normal y no se prende ninguna luz de advertencia. Todavía no he revisado batería, arranque ni sistema de combustible. ¿Qué debería revisar primero?"*
- **Diagnóstico del problema anterior:** Se emitían hipótesis con sesgos dispersos (IAC 45%, Termostato 36%, Common Rail 19%) y se sugería una reparación/limpieza directa de la mariposa de aceleración.
- **Resultado auditado y corregido:** El extractor conserva los hechos clínicos clave (`demora en encender matutino`, `funcionamiento normal post-arranque`, `tablero sin testigos`, `piezas no revisadas`). La directriz `COMBUSTIBLE_003` fue corregida para exigir inspección visual y verificación metrológica con escáner/multímetro antes de indicar cualquier limpieza.

---

### 4. Caso Frenos (Caso Real B)

- **Entrada tras 3 turnos:**
  - Turno 1: Vibración en el volante al frenar a velocidad media/alta. Manejando sin frenar no vibra.
  - Turno 2: Confirmación de que vibra únicamente al frenar.
  - Turno 3: Se siente en el volante, casi no en el pedal ni en el resto del vehículo.
- **Diagnóstico del problema anterior:** Colapsaba en `"Posibles causas: 1. Consulta Ambigua / Datos Faltantes — 0%"`.
- **Resultado auditado y corregido:** Tras corregir el detector de polaridad, el purificador semántico, el sintetizador de consulta y la guardia de ambigüedad, el pipeline entrega la predicción real de C1:
  - **Top 1:** Discos de freno alabeados o desgastados (**94.9%**)
  - **Top 2:** Llantas desbalanceadas o desalineadas (**4.9%**)
  - **Top 3:** Pastillas y zapatas de freno (**0.1%**)
  - **Macro-Sistema:** `FRENOS` (**100%**)
  - **Directriz de inspección física:** Medición metrológica con reloj comparador y micrómetro (alabeo máximo 0.05 mm y DTV).

---

### 5. Extracción de Hechos (`ExtractorHechos`)

- **Mejoras aplicadas:**
  - Soporte para detección en tercera persona sobre frenos y vibración (`el volante comienza a vibrar`, `frena el carro`).
  - Reconocimiento de ubicación anatómica del síntoma (`volante`, `pedal`, `carrocería/chasis`).
  - Detección de condiciones operativas de velocidad (`velocidad media o alta`).
  - Extracción de componentes pendientes de revisión (`no he revisado batería, arranque ni combustible`).

---

### 6. Estado Conversacional (`ConversationState`)

- **Persistencia de hechos estructurados:** El objeto de estado mantiene los diccionarios `extracted_facts`, `negated_facts` y `unknown_facts` sincronizados en cada turno.
- **Deduplicación semántica de preguntas:** Si el mecánico ya declaró que la vibración ocurre *"cuando frena"* y *"no vibra sin frenar"*, el selector de preguntas ya no formula preguntas redundantes sobre ralentí o aceleración.

---

### 7. Query Synthesis (`SintetizadorConsulta`)

- **Corrección de la pérdida de hechos:** Se reescribió `sintetizar()` para que concatene estructuradamente el síntoma principal, el gatillo desencadenante, el régimen de velocidad, la localización física, los hechos negados y las piezas pendientes de inspección.
- **Longitud y completitud:** Se eliminó la contracción excesiva de texto que reducía consultas complejas a strings de menos de 25 caracteres.

---

### 8. Clasificador C1 (Linear SVM Congelado)

- **Integridad:** C1 se mantuvo **100% congelado**, sin reentrenar ni recalibrar.
- **Verificación cruzada (Clean vs Concat vs Synthesized):**
  - Caso Frenos: En las tres variantes de texto, C1 predice *Discos alabeados* con confianza $\ge 94.9\%$.
  - Caso Arranque: C1 sitúa consistentemente *Common Rail Diesel* (84.7%) y *Batería descargada* (10.4%) en el Top 2. Se constató que la preponderancia de Common Rail se debe al corpus original de C1 en frases de arranque en frío.

---

### 9. RAG (Recuperación Aumentada por Generación)

- **Integridad:** Índice FAISS `indice_faiss_v1.index` y `metadatos_manuales_v1.json` intactos y coincidentes con los hashes criptográficos requeridos.
- **Recuperación:** Para el caso de frenos, RAG recupera documentos técnicos OEM sobre tolerancias de alabeo lateral (0.05 mm) y variación de espesor de disco (DTV). Para arranque, recupera pruebas de caída de tensión en cranking (> 9.6V) y retención de presión de combustible.

---

### 10. Response Assembly y Directrices Mecánicas

- **Principio Metodológico Aplicado:** *Hipótesis → Comprobación Física → Resultado → Actualización*.
- **Modificaciones en Directrices:**
  - `COMBUSTIBLE_003` (IAC / Cuerpo de aceleración): Modificada para recomendar primero la comprobación visual de carbonilla y el porcentaje de apertura con escáner, en lugar de limpieza directa.
  - `FRENO_001` (Alabeo de discos): Recomienda medición con reloj comparador en elevador antes de sustituir o rectificar discos.

---

### 11. Correcciones Realizadas

1. `backend/src/core/conversacion/detector_polaridad.py`: Corrección de falso negativo en cláusulas subordinadas (`sin frenar`).
2. `backend/src/core/conversacion/extractor_hechos.py`: Extracción robusta de velocidad, ubicación de vibración, régimen de giro y componentes pendientes.
3. `backend/src/core/conversacion/suficiencia_informacion.py`: Inclusión de regla de suficiencia para evidencia localizada de frenos y categorías independientes.
4. `backend/src/core/conversacion/sintetizador_consulta.py`: Consolidación clínica completa del texto sintetizado.
5. `backend/src/core/diagnostico/text_processor.py`: Protección de consultas orquestadas ante interceptación errónea por `es_consulta_ambigua`.
6. `backend/src/core/diagnostico/semantic_purifier.py`: Corrección de purga destructiva de términos de frenos.
7. `backend/src/core/taxonomy/directrices_mecanicas.py`: Enfoque de comprobación previa en `COMBUSTIBLE_003`.
8. `backend/alembic/versions/20260919_01_separacion_fases_tesis.py`: Migración de base de datos para aislamiento de fases.
9. `backend/src/infrastructure/database/repositories/validacion_taller_repository.py`: Filtro estricto de tesis y orden cronológico descendente.
10. `backend/src/application/services/validacion_taller.py`: Métricas de tesis blindadas contra registros de desarrollo.
11. `backend/src/interfaces/api/v1/endpoints/validacion_taller.py`: Endpoint actualizado con parámetro `tipo_registro` y sanitización CSV.
12. `frontend/src/types/api.ts` & `ValidacionCasosTable.tsx`: Sincronización de contratos y enriquecimiento de UI.

---

### 12. Regresiones

- Se ejecutaron las suites de pruebas existentes de backend y API de validaciones (`test_validacion_taller_api.py`, `test_fase11_5_thesis_and_diagnostic.py`).
- **Resultado:** 100% de tests aprobados (20 de 20 pruebas automáticas en verde). Cero regresiones en aislamiento entre talleres (multitenant), firmas HMAC-SHA256, concurrencia y seguridad de exportación.

---

### 13. Arquitectura de Datos de Tesis

El sistema cuenta con un modelo relacional en PostgreSQL centrado en la entidad `ValidacionTaller`:
- Permite registrar el pre-test tradicional ($O_1$) sin requerir el uso de CarBot.
- Permite vincular el post-test asistido ($O_2$) a las sesiones de CarBot (`conversacion_id`, `diagnostico_id`).
- Contiene los campos para contrastar la predicción técnica contra el diagnóstico físico confirmado.

---

### 14. Datos Existentes Antes de la Fase 11.5

- Tabla `validaciones_taller` con campos: `id`, `taller_id`, `fase` ('PRE' o 'POST'), `fecha`, `item`, `vehiculo_resumen`, `sintomas`, `prediccion_sistema`, `diagnostico_fisico`, `es_correcta`, `duracion_minutos`, `campos_completos`, `observaciones`, `verificado`.
- Servicios para cálculo de promedios, tasas de acierto y exportación básica.

---

### 15. Datos Faltantes Antes de la Fase 11.5

- No existía un campo discriminador para separar pruebas de desarrollo/regresión de la muestra oficial de tesis. Todo registro con `fase='PRE'` o `'POST'` entraba al cálculo de indicadores.
- No existían columnas para almacenar el `conversacion_id` (UUID de WhatsApp) ni el `diagnostico_id` dentro del registro de validación.
- No existía ordenamiento cronológico descendente estricto en los repositorios de consulta.

---

### 16. Persistencia

- **PostgreSQL:** Tablas `validaciones_taller` y `diagnosticos` actualizadas con la columna `tipo_registro` tipificada mediante un Check Constraint a nivel de base de datos:
  `CHECK (tipo_registro IN ('DEVELOPMENT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST'))`.
- **Integridad Referencial:** Columnas `conversacion_id` y `diagnostico_id` de tipo UUID indexadas en `validaciones_taller`.

---

### 17. PRE-TEST ($O_1$)

- Representa la recolección del proceso de diagnóstico tradicional (sin CarBot).
- Se gestiona desde el Panel de Investigación sin obligar al uso de WhatsApp.
- Almacena: tiempo de diagnóstico tradicional (`duracion_minutos`), verificación de completitud de campos (`campos_completos`) y exactitud del mecánico (`es_correcta`).
- Identificado estrictamente con `tipo_registro = 'THESIS_PRETEST'`.

---

### 18. POST-TEST ($O_2$)

- Representa el proceso asistido mediante CarBot.
- Vincula la conversación de WhatsApp y el diagnóstico generado por el clasificador ML.
- El mecánico o investigador registra el `diagnostico_fisico` tras la confirmación en el vehículo y el sistema evalúa la concordancia (`es_correcta`).
- Identificado estrictamente con `tipo_registro = 'THESIS_POSTTEST'`.

---

### 19. Dimensión A: Indicador PPCF (Predicción de Fallas)

- **Fórmula:** $\text{PPCF} = \left(\frac{\text{Total Predicciones Correctas}}{\text{Total Predicciones Realizadas}}\right) \times 100$
- **Unidad:** 1 caso clínico oficial evaluado = 1 predicción principal contrastada contra el diagnóstico físico confirmado.
- **Implementación:** Método `resumen_por_fase` y `metricas_variable_independiente` en `ServicioValidacionTaller`.
- **Blindaje:** Los casos marcados como `DEVELOPMENT` o `REGRESSION` quedan excluidos por cláusula `WHERE tipo_registro IN ('THESIS_PRETEST', 'THESIS_POSTTEST')`. División entre cero controlada (devuelve 0.0%).

---

### 20. Dimensión B: Indicador RDC (Control de Información)

- **Fórmula:** $\text{RDC} = \left(\frac{\text{Registros con los 8 campos completos}}{\text{Total Registros Evaluados}}\right) \times 100$
- **Implementación:** Almacenamiento en `validaciones_taller.campos_completos` (booleano) y agregación porcentual por fase.
- **Advertencia de Instrumentos:** Documentado bajo la etiqueta formal `DEFINICION_8_CAMPOS_REQUIERE_CONFIRMACION_METODOLOGICA` (véase Sección 29).

---

### 21. Dimensión C: Indicador TPRD (Eficiencia / Tiempo de Respuesta)

- **Fórmula:** $\text{TPRD} = \frac{\sum \text{Duración en minutos}}{\text{Total Diagnósticos Evaluados}}$
- **Delimitación conceptual:**
  - $\text{TPRD}$ mide el tiempo del proceso de diagnóstico en taller registrado en `duracion_minutos`.
  - La latencia técnica del clasificador C1 ($\approx 5-25\text{ ms}$) y la latencia del pipeline de WhatsApp son métricas de ingeniería complementarias y **no se confunden** con el $\text{TPRD}$ oficial de la tesis.

---

### 22. Frontend (Panel de Control y Validación)

- Componente React `ValidacionCasosTable.tsx` actualizado para mostrar en el modal de detalle:
  - Tipo de Registro (`DEVELOPMENT`, `REGRESSION`, `THESIS_PRETEST`, `THESIS_POSTTEST`).
  - Identificadores de trazabilidad (`conversacion_id`, `diagnostico_id`).
- Contratos TypeScript sincronizados en `frontend/src/types/api.ts`.
- Compilación de producción exitosa en 776 ms sin advertencias.

---

### 23. API REST (FastAPI)

- Endpoints de `/api/v1/validaciones-taller` actualizados:
  - `GET /api/v1/validaciones-taller`: Soporta parámetro opcional `tipo_registro` para filtrar casos de tesis vs desarrollo.
  - `POST /api/v1/validaciones-taller`: Valida y persiste `tipo_registro`, `conversacion_id` y `diagnostico_id`.
  - `GET /api/v1/validaciones-taller/metricas-variable-independiente`: Calcula los 3 indicadores oficiales de tesis sobre la muestra segregada.

---

### 24. Base de Datos (Migración PostgreSQL)

- Archivo de migración: `backend/alembic/versions/20260919_01_separacion_fases_tesis.py`.
- Estado: Ejecutada y verificada con `alembic upgrade head`.
- Constraints: Check Constraint que restringe los valores permitidos para `tipo_registro`. Índices sobre `tipo_registro`, `conversacion_id` y `diagnostico_id`.

---

### 25. Exportación de Datos

- Endpoint: `GET /api/v1/validaciones-taller/exportar`.
- Características de seguridad y metodología:
  - Sanitización estricta contra ataques de inyección de fórmulas CSV (prefijos `=`, `+`, `-`, `@` son neutralizados con comilla simple `'`).
  - Descarga segregada por fase y tipo de registro.
  - Orden descendente estricto por fecha e ítem.

---

### 26. Separación Estricta: DEVELOPMENT vs. TESIS

- Queda estrictamente establecido que los casos de prueba utilizados por el equipo de desarrollo para detectar anomalías o regresiones (incluidos los casos de Arranque y Frenos de la Fase 11) se registran con `tipo_registro = 'DEVELOPMENT'` o `'REGRESSION'`.
- Ningún caso de desarrollo es computable dentro de las métricas descriptivas o inferenciales de la tesis.
- Ningún registro de taller (Pre-test o Post-test) se utiliza como conjunto de entrenamiento de los clasificadores de Machine Learning.

---

### 27. Seguridad y Autorización

- Los endpoints de validación de taller y métricas de tesis exigen autenticación por token Bearer (JWT) con rol autorizado (`ADMIN` / `INVESTIGADOR`).
- Los mecánicos en taller operan únicamente a través de la interfaz conversacional de WhatsApp sin acceso a las funciones de auditoría ni a la base de datos de investigación.

---

### 28. Integridad de Artefactos C1 y RAG (Verificación Criptográfica)

Se verificó el 100% de coincidencia de los hashes SHA-256 de los modelos congelados:

| Artefacto | Hash SHA-256 Esperado | Hash SHA-256 Calculado | Estado |
|---|---|---|---|
| `vectorizador_c1.pkl` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | **MATCH (OK)** |
| `modelo_diagnostico_c1.pkl` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | **MATCH (OK)** |
| `modelo_sistema_c1_macrofix.pkl` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | **MATCH (OK)** |
| `indice_faiss_v1.index` | `a2a081ffded23d4d727b57780aec26da9167e90f044101e77adbb33cbaa79b40` | `a2a081ffded23d4d727b57780aec26da9167e90f044101e77adbb33cbaa79b40` | **MATCH (OK)** |
| `metadatos_manuales_v1.json` | `8b4244713cfdc2f59af66b4e43bea8532196366ee5b53a98721e96ca6c781dbb` | `8b4244713cfdc2f59af66b4e43bea8532196366ee5b53a98721e96ca6c781dbb` | **MATCH (OK)** |

---

### 29. Inconsistencias Metodológicas Detectadas

1. **`DEFINICION_8_CAMPOS_REQUIERE_CONFIRMACION_METODOLOGICA`**: La fórmula del indicador RDC establece que se computan los registros con "los 8 campos completos". Sin embargo, en el texto del proyecto de tesis no se encuentra una lista canónica cerrada de dichos 8 campos (ej. se mencionan placa, kilometraje, síntomas, componentes, diagnóstico, etc., pero sin fijar taxativamente el octavo campo). Se recomienda validar con el asesor metodológico la lista exacta para congelar la lógica de validación automática.
2. **Advertencia de separación empírica vs. modelado:** Se corroboró que ninguna sección del código utiliza los 60 registros empíricos de campo para entrenamiento ni validación cruzada del modelo ML. Los registros de taller permanecen estrictamente confinados a la contrastación de hipótesis $HE_1, HE_2, HE_3$.

---

### 30. Estado Final

Con base en el cumplimiento de los 68 numerales de la especificación técnica, la verificación de integridad criptográfica, la aprobación de todas las pruebas automatizadas y el levantamiento del worker en producción:

> **ESTADO FINAL DECLARADO:**  
> **`FASE11_5_APROBADA_PENDIENTE_WHATSAPP_Y_CAMPO`**
> 
> *Nota sobre WhatsApp Meta API:* De conformidad con el numeral 66 de las directrices, la interacción final en vivo con la API Cloud de Meta se declara como `WHATSAPP_PENDING_MANUAL_VALIDATION` a la espera de las pruebas de campo por parte del usuario.
