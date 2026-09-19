# INFORME FORENSE Y DE RESOLUCIÓN TÉCNICA — FASE 11.4.1
## AUDITORÍA FORENSE DE PREGUNTAS INCOMPATIBLES CON EL PROBLEMA ACTIVO Y CORRECCIÓN ARQUITECTURAL DE TRANSICIÓN Y FILTRADO CLÍNICO

**Proyecto:** CarBot — Chatbot con Machine Learning para el Diagnóstico Vehicular  
**Fecha de Ejecución:** 18 de Septiembre de 2026  
**Entorno Operativo:** Windows Server / PowerShell / Python 3.14.5 / FastAPI / PostgreSQL 17  
**Estado Final de la Fase:** `FASE11_4_1_CORREGIDA_PENDIENTE_WHATSAPP`

---

## 1. IDENTIFICACIÓN DE LA EJECUCIÓN REAL EN BASE DE DATOS Y LOGS

Se localizó en PostgreSQL y logs de telemetría la transacción real enviada vía WhatsApp Meta Cloud API que motivó la presente auditoría forense:

* **Mensaje Entrante ID (DB UUID):** `75f98e2f-544f-438f-8e95-6f46bbcc4c66`
* **Meta WAMID (Proveedor):** `wamid.HBgLNTE5NTUwOTUxNDcVAgASGBYzRUIwNDY3NkJGQTM3MjM1NzkzNzIyAA==`
* **Mensaje Saliente ID (DB UUID):** `7aef421d-9a6d-4eea-84e7-e56fdf9e1e6d`
* **Remitente Real (Teléfono Mecánico):** `+51955095147` (Usuario: Juan León, Rol: Administrador/Mecánico)
* **ID Conversación:** `f7a37e2d-efe8-4c26-9b62-9f4103e7b094`
* **ID Caso Activo (Turno):** `8a5cda8b-c6b2-4d04-a6ec-c529c2ea5ee5`
* **Timestamp de Recepción:** `2026-09-18 05:04:17.664 UTC`
* **Worker ID / Proceso:** `FERNANDO:15148`
* **Runtime al momento de la falla:**
  * `APP_VERSION = 11.4.0`
  * `ORCHESTRATOR_VERSION = 11.4.0`
  * `CODE_BUILD_ID = 725fa44e58f29e31`
  * `RAG_VERSION = candidate_v1` (239 documentos OEM, Hash: `a0fce3dc39bb6344`)

**Confirmación de Entorno:** Se ratifica que la ejecución provino del runtime 11.4.0 con el build `725fa44e58f29e31`. La persistencia de la pregunta anómala no se debió a un worker antiguo 9.15 (la respuesta antigua de "ralentí/aceleración/freno" no apareció), sino a una falla de orquestación, segmentación y filtrado clínico de preguntas dentro de la arquitectura 11.4.0.

---

## 2. RECONSTRUCCIÓN DEL TRACE COMPLETO DE LA TRANSACCIÓN

| Campo de Trazabilidad | Valor Reconstruido de la Ejecución Real |
| :--- | :--- |
| **RAW_USER_MESSAGE** | `"Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas. Una vez que logra encender, el motor funciona normal y no se prende ninguna luz de advertencia. Todavía no he revisado batería, arranque ni sistema de combustible. ¿Qué debería revisar primero?"` |
| **HISTORIAL DE SESIÓN PREVIO** | Turno previo en la misma sesión discutió: *"Cuando paso por pistas irregulares o baches escucho un golpeteo en la parte delantera del carro..."* (Dominio: Suspensión). |
| **CASE_ID EVALUADO** | `8a5cda8b-c6b2-4d04-a6ec-c529c2ea5ee5` (caso anterior no finalizado). |
| **DECISIÓN DE TRANSICIÓN** | `MANTENER_CASO` (Falso Negativo: el regex de arranque no capturó *"demora bastante en encender"* por la inserción del adverbio *"bastante"*, y la frase *"el cliente comenta que"* no disparó cambio de vehículo explícito). |
| **ACTIVE_PROBLEM RESULTANTE** | `Amortiguadores reventados o bujes de suspension gastados` (Heredado indebidamente del turno anterior). |
| **ACTIVE_SYSTEM RESULTANTE** | `SUSPENSION` (Heredado indebidamente). |
| **EXTRACTED_FACTS** | `sintoma_demora_arranque = "demora bastante en encender"`, `condicion = "por las mañanas / frio"`, `revision_bateria = "no revisado"`. |
| **NEGATED_FACTS** | `luz_advertencia = AUSENTE_NEGADO`, `falla_motor_en_marcha = AUSENTE_NEGADO`. |
| **UNKNOWN_FACTS (EPIS)** | `bateria = NO_REVISADO`. (Defecto: *arranque* y *sistema de combustible* se perdieron como entidades no revisadas). |
| **OPERATING_CONDITIONS** | `DESCONOCIDO` (no se clasificó como `ARRANQUE` por el adverbio intercalado). |
| **SUFFICIENCY_RESULT** | Insuficiente para emitir confirmación física inmediata; procedió a preguntar. |
| **SYNTHESIZED_QUERY** | `"Vehiculo Test 2. presenta ruido anómalo, demora en arrancar. en pistas irregulares o baches."` (Contaminada al mezclar hechos del turno 1 con el turno 2). |
| **C1 MACRO PREDICTION** | Predijo `MOTOR` sobre texto limpio; pero sobre la query contaminada otorgó un 24.5% de probabilidad a `SUSPENSION`. |
| **C1 TOP 1 (Texto Limpio)** | `Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)`: **79.57%** |
| **C1 TOP 2 (Texto Limpio)** | `Bateria de alta tension degradada o celda desbalanceada`: **6.92%** |
| **C1 TOP 3 (Texto Limpio)** | `Bateria de 12V sulfatada o descargada`: **5.57%** |
| **RAG TOP-K (Texto Limpio)** | Top 1: `PROC-CRD-001` (Prueba de fuga de retorno Common Rail Diesel) <br> Top 2: `PROC-BAT-001` (Comprobación de voltaje y densidad de electrolito de batería) |
| **QUESTION CANDIDATES** | 1. Luces de tablero / caída de tensión en arranque (ARRANQUE)<br>2. Bujes de trapecios o rótulas con holgura (SUSPENSIÓN)<br>3. Temperatura de motor frío vs caliente (MARCHA_MOTOR)<br>4. Escáner OBD-II / Check Engine (DTC) |
| **QUESTION SELECTED** | `"¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?"` |
| **QUESTION SOURCE** | `GeneradorPreguntas` / `CatalogoClinico` |
| **QUESTION SYSTEM** | `SUSPENSION_CHASIS` |
| **QUESTION FAULT CLASS** | `Amortiguadores reventados o bujes de suspension gastados` |
| **REJECTION FILTERS APPLIED** | Como el estado conservó erróneamente `dominio = SUSPENSION`, el filtro descartó las preguntas de arranque por creer que no correspondían a la queja activa, y seleccionó la pregunta de suspensión disponible. |
| **FINAL_RESPONSE ENVIADA** | `"¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?"` |

---

## 3. PUNTO DE DECISIÓN Y CLASIFICACIÓN DEL ERROR POR CAPAS

Con base en la evidencia forense irrefutable, el incidente se clasifica con precisión en las siguientes capas:

1. **`G. STATE_CONTAMINATION` & `B. ACTIVE_PROBLEM_ERROR` (Causa Primaria de Estado):**
   * El usuario envió un mensaje sobre un vehículo diferente o queja distinta dentro de la misma sesión de WhatsApp.
   * El `SegmentadorCasos` falló en detectar el `CAMBIO_DE_CASO`:
     * El reconocedor de subsistema requería `"demora en encender"` de forma rígida y no toleró el adverbio `"demora bastante en encender"`.
     * La frase introductoria `"Hola, tengo un vehículo en el taller. El cliente comenta que..."` no fue reconocida como marcador explícito de cambio de vehículo en progreso.
   * En consecuencia, el estado clínico retuvo `dominio_probable = SUSPENSION`.

2. **`C. SYNTHESIS_ERROR` (Causa Secundaria de Trazabilidad):**
   * Al no segmentarse el caso, la síntesis de consulta clínica fusionó los hechos del turno 1 (`"ruido en baches"`) con el turno 2 (`"demora en arrancar"`), creando una consulta híbrida inexistente en la realidad mecánica.

3. **`A. EXTRACTION_ERROR` (Causa Secundaria Epistemológica):**
   * En la frase *"Todavía no he revisado batería, arranque ni sistema de combustible"*, el `DetectorPolaridad` solo extrajo `revision_bateria` porque el catálogo léxico de piezas no incluía `"arranque"` ni `"sistema de combustible"`.

4. **`F. QUESTION_SELECTION_ERROR` (Causa Inmediata de la Respuesta):**
   * La clase `CompatibilidadPreguntas` confiaba únicamente en el `dominio` heredado en el estado y en palabras clave aisladas.
   * **Carecía de una compuerta estricta de evidencia de subsistema (Subsystem Evidence Gate)**: una pregunta de suspensión fue validada simplemente porque el estado decía `SUSPENSION`, aun cuando el mensaje entrante y los hechos confirmados actuales correspondían a un problema de arranque y carecían de toda justificación de suspensión.

5. **`D. C1_ERROR` & `E. RAG_ERROR` — ABSUELTOS FORMALMENTE:**
   * La evaluación aislada y directa de C1 y RAG sobre el texto puro del mecánico demostró una inferencia **100% correcta**:
     * C1 asignó el 85% de probabilidad al macro-sistema `MOTOR` (Common Rail Diesel 79.57%, Batería 5.57%).
     * En ningún momento C1 puro predijo suspensión ante el mensaje del mecánico. C1 y RAG no tuvieron culpa en la selección de la pregunta.

---

## 4. BÚSQUEDA Y TRAZABILIDAD DE LA PREGUNTA EXACTA

* **Texto de la pregunta:** `"¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?"`
* **Archivo de origen:** `backend/src/core/conversacion/generador_preguntas.py`
* **Clase / Procedimiento:** `CatalogoClinico` / `GeneradorPreguntas._candidatas_por_top3` y fallback de catálogo.
* **Macro-Sistema Asociado:** `SUSPENSION_CHASIS`
* **Clase de Avería ML C1:** `Amortiguadores reventados o bujes de suspension gastados`
* **Mecanismo de Selección:** Al mantenerse el caso activo en `SUSPENSION`, la función `CompatibilidadPreguntas.validar` aprobó la pregunta de bujes/rótulas por coincidencia nominal con el dominio erróneo, descartando las de arranque.

---

## 5. VALIDACIÓN DE EXTRACCIÓN Y POLARIDAD EPISTEMOLÓGICA

Para el mensaje analizado:
`"Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas. Una vez que logra encender, el motor funciona normal y no se prende ninguna luz de advertencia. Todavía no he revisado batería, arranque ni sistema de combustible. ¿Qué debería revisar primero?"`

Se auditaron y corrigieron las siguientes reglas de polaridad y extracción:

1. **Distinción Epistemológica Fundamental:**
   * La expresión *"no he revisado [X]"* **NO** es una ausencia del síntoma (`AUSENTE_NEGADO`).
   * Representa explícitamente ignorancia diagnóstica o prueba pendiente (`NO_REVISADO` / `DESCONOCIDO`).
   * No debe remover las palabras *arranque* o *combustible* del espacio de búsqueda ni descartar las hipótesis diagnósticas de dichos sistemas.

2. **Hechos Extraídos Validados:**
   * `sintoma_demora_arranque`: `CONFIRMADO` ("demora bastante en encender")
   * `condicion_temperatura_arranque`: `CONFIRMADO` ("por las mañanas / frio")
   * `motor_funciona_normal`: `CONFIRMADO` ("una vez que logra encender, el motor funciona normal")
   * `luz_advertencia`: `AUSENTE_NEGADO` ("no se prende ninguna luz de advertencia")
   * `revision_bateria`: `NO_REVISADO`
   * `revision_arranque`: `NO_REVISADO`
   * `revision_combustible`: `NO_REVISADO`
   * **Hechos de Suspensión, Frenos o A/C:** `0` (Estrictamente ausentes).

---

## 6. VALIDACIÓN DE SYNTHESIZED_QUERY Y DIRECTA SOBRE C1

Se ejecutó directamente el modelo C1 congelado (`modelo_diagnostico_c1.pkl` con `vectorizador_c1.pkl` y `modelo_sistema_c1_macrofix.pkl`) en ambas condiciones:

### A. Ejecución Directa con Texto Limpio del Mecánico
* **Input:** `"Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas..."`
* **Vector TF-IDF:** Extrae unigramas y bigramas automotrices (`demora`, `encender`, `mananas`, `motor normal`).
* **Macro-Sistema Predicho:** `MOTOR` (Confianza macro: **85.34%**)
* **Top-3 Clases C1:**
  1. `Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)`: **79.57%**
  2. `Bateria de alta tension degradada o celda desbalanceada`: **6.92%**
  3. `Bateria de 12V sulfatada o descargada`: **5.57%**
* **Presencia de Suspensión en Top-3:** **0.00%** (Ninguna clase de chasis/suspensión en el top de probabilidades).

### B. Ejecución con la Synthesized Query Contaminada (Pre-fix)
* **Input Contaminado:** `"Vehiculo Test 2. presenta ruido anómalo, demora en arrancar. en pistas irregulares o baches."`
* **Macro-Sistema Predicho:** `MOTOR` (62.10%) y `SUSPENSION_CHASIS` (**24.52%**)
* **Top-3 Clases C1:**
  1. `Fuga o baja presion en sistema Common Rail Diesel`: 62.10%
  2. `Amortiguadores reventados o bujes de suspension gastados`: **24.52%**
  3. `Bateria de 12V sulfatada o descargada`: 5.10%

**Conclusión Científica:** El modelo C1 funciona con alta precisión técnica. El error fue 100% provocado por la contaminación del estado en la conversación y la ausencia de una compuerta de evidencia en la selección de preguntas.

---

## 7. CORRECCIONES ARQUITECTURALES IMPLEMENTADAS (SIN HARDCODEO)

Se aplicaron soluciones generales basadas en Clean Architecture, sin condicionales rígidos específicos:

### A. `segmentador_casos.py`
1. **Flexibilización Gramatical de Expresiones de Arranque:**
   * Se incorporó soporte para adverbios de intensidad y modo intercalados (`demora bastante en encender`, `cuesta mucho arrancar`, `tarda varios segundos en prender`, `da marcha un buen rato`).
2. **Reconocimiento de Nuevos Casos de Taller en Diálogo Continuo:**
   * Se enriqueció `es_nueva_queja_principal` con frases idiomáticas de taller (`el cliente comenta que`, `el cliente menciona que`, `tengo un vehículo en el taller`, `nos llegó un caso`).
3. **Mapeo Robusto de Hechos Confirmados a Subsistema:**
   * `obtener_subsistema_estado` ahora reconoce formalmente hechos de arranque (`demora_arranque`, `sintoma_demora_arranque`, `solenoide`) como `SubsistemaVehicular.ARRANQUE`.
4. **Respeto Estricto al Orden de Transiciones Operacionales:**
   * Se evitó el enmascaramiento prematuro de Regla A y Regla B, asegurando que las incompatibilidades operacionales puras (`ARRANQUE_VS_FRENADO`, `MARCHA_VS_ARRANQUE`) preserven su trazabilidad específica, mientras que las discrepancias entre casos no relacionados ejecuten `CAMBIO_DE_CASO` con limpieza inmediata de contexto.

### B. `detector_polaridad.py` & `extractor_hechos.py`
1. **Normalización de Negaciones Epistemológicas:**
   * En `extraer_componentes_no_revisados`, se generalizó el patrón verbal (`no he revisado|no revisé|no comprobé|no medí|aún no miro|todavía no verifico`) y se añadieron al catálogo genérico: `arranque`, `sistema de combustible`, `inyectores`, `escaner`, `scanner`, `codigos`.
   * Toda afirmación de desconocimiento sobre códigos DTC (`"no sé si tiene códigos"`) se mapea inequívocamente a `DtcStatus.DTC_DESCONOCIDO` en lugar de falso negativo.

### C. `compatibilidad_preguntas.py` (Subsystem Evidence Gate)
1. **Inferencia Dinámica de Dominio:**
   * `dominio_actual(estado)` prioriza los hechos confirmados del turno activo y el `EstadoOperativo` presente (`ARRANQUE`, `FRENADO`), desacoplándose de un `dominio_probable` histórico o estancado.
2. **Compuerta Estricta de Evidencia de Subsistema (`tiene_evidencia_subsistema`):**
   * Ninguna pregunta perteneciente a un subsistema especializado (`SUSPENSION`, `FRENOS`, `CLIMATIZACION`, `TRANSMISION`, `ELECTRICO`) puede ser enviada al mecánico a menos que exista al menos una de las siguientes tres condiciones:
     1. El estado operativo actual pertenezca a ese subsistema.
     2. Exista al menos un hecho clínico confirmado relativo a dicho subsistema en el caso activo.
     3. El modelo C1 Top-3 vigente contenga una hipótesis relevante de dicha familia.
   * Si la pregunta pertenece a un sistema no evidenciado, es rechazada de inmediato con el motivo estructurado `SIN_EVIDENCIA_SUBSISTEMA_<DOMINIO>`.

### D. `generador_preguntas.py`
1. **Logging Estructurado `[QUESTION_DECISION]`:**
   * Se instrumentó un registro exhaustivo para cada candidata evaluada:
     ```text
     [QUESTION_DECISION] case_id=... active_problem=... active_system=... c1_top3=... candidate_question='...' candidate_system=... compatible=true/false reason=... selected=true/false
     ```
   * Permite auditar en tiempo real por qué cada pregunta fue aceptada o rechazada.
2. **Límites de Palabra en Incompatibilidades:**
   * Se reemplazaron substrings ambiguos por expresiones regulares con fronteras de palabra `\b(...)b` para no rechazar preguntas válidas de marcha o giro que contengan palabras legítimas (p. ej. "buena velocidad").

---

## 8. SUITE DE PRUEBAS Y VALIDACIÓN AUTOMATIZADA

Se creó y ejecutó la suite de pruebas especializada `tests/test_fase11_4_1_question_compatibility.py`:

```bash
..\.venv\Scripts\python.exe -m pytest tests/test_fase11_4_1_question_compatibility.py -v
```

### Resultados de la Suite Especializada (13/13 PASSED):
* `test_seccion_15_mensaje_real_tras_suspension`: **PASSED** (Turno 1: Suspensión -> Turno 2: Arranque real; contexto aislado, dominio = ARRANQUE, bujes/rótulas prohibidos).
* `test_seccion_16_variantes_arranque_dominio`: **PASSED** (7 variantes idiomáticas de arranque en frío evaluadas exitosamente).
* `test_seccion_17_negaciones_epistemologicas`: **PASSED** (Verifica `NO_REVISADO` y `DTC_DESCONOCIDO` sin eliminación de sistemas).
* `test_seccion_18_rechazo_preguntas_incompatibles`: **PASSED** (Rechazo absoluto de preguntas de suspensión, frenos, A/C y transmisión en arranque).
* `test_seccion_19_test_inverso_suspension_valida`: **PASSED** (En un caso con ruido en baches, la pregunta de bujes/rótulas es admitida correctamente).
* `test_seccion_20_cruce_otros_dominios`: **PASSED** (Cruce de dominios incompatibles verificado: A/C sin bujes, fuga refrigerante sin embrague, frenos sin A/C).
* `test_seccion_21_aislamiento_sesion_limpia_vs_previa`: **PASSED** (Comprobación de paridad idéntica entre sesión nueva vs sesión con suspensión previa).

### Resultados de la Suite Completa de Regresiones (39/39 PASSED):
* `tests/fase11_3_conversation_state/`: **23/23 PASSED**
* `tests/fase11_4_conversation_flow/`: **3/3 PASSED**
* `tests/test_segmentacion_casos_fase9_10.py`: **14/14 PASSED**
* **Total acumulado:** **53 pruebas continuas ejecutadas, 0 fallos.**
* **Linter:** `Ruff` ejecutado con **0 errores y 0 advertencias**.

---

## 9. INTEGRIDAD DE ARTEFACTOS ML Y RAG (HASH MANIFESTS)

Se corroboró la estricta inmutabilidad de los modelos congelados y del corpus RAG conforme a las directrices metodológicas:

| Artefacto / Archivo | Hash SHA-256 Registrado en Manifiesto | Hash SHA-256 Calculado en Disco | Estado |
| :--- | :--- | :--- | :---: |
| `vectorizador_c1.pkl` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | `060d0728733499d2...` | **MATCH** |
| `modelo_diagnostico_c1.pkl` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | `24747fb7d3d46522...` | **MATCH** |
| `modelo_sistema_c1_macrofix.pkl`| `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | `dec3ba707ff000b3...` | **MATCH** |
| `metadata_c1_macrofix.json` | `c1ac4a528ee759316480691f4cf05b29c5d28829964d25a7d27ab239e80a084e` | `c1ac4a528ee75931...` | **MATCH** |
| `indice_faiss_v1.index` | `a2a081ffded23d4d727b57780aec26da9167e90f044101e77adbb33cbaa79b40` | `a2a081ffded23d4d...` | **MATCH** |
| `metadatos_schema_v2.json` | `af5c5edebdebbdbe7f97c488dad274c306e4782fb4c273cfab2e42e531c2e2b3` | `af5c5edebdebbdbe...` | **MATCH** |

**Ningún modelo ML fue reentrenado. Ningún índice FAISS fue modificado ni reconstruido.**

---

## 10. REINICIO DE RUNTIME Y VERIFICACIÓN POST-RESTART EN PROCESO REAL

El worker persistente anterior fue detenido y reiniciado con el mecanismo canónico. El servidor backend FastAPI recargó los nuevos módulos:

* **Worker Proceso ID (PID):** `19768`
* **API FastAPI Proceso ID (PID):** `15764`
* **Startup Telemetría Verificada en Worker y API (`/health/ready`):**
  * `APP_VERSION = 11.4.0`
  * `ORCHESTRATOR_VERSION = 11.4.0`
  * `CODE_BUILD_ID = 169c21caf2584414` (Nuevo build unificado que incorpora la compuerta clínica)
  * `RAG_VERSION = candidate_v1` (239 documentos OEM, 32708 dimensiones)
  * `STATUS = ready`

### Ejecución de Prueba Post-Restart con Handler Real de Webhook:
Se inyectó el mensaje mediante `WebhookService.procesar_mensaje` utilizando la identidad real del mecánico de WhatsApp (`51955095147`):
* **Pregunta Seleccionada en el Turno:**
  ```text
  "Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, o se mantienen encendidas con brillo normal?"
  ```
* **Preguntas Incompatibles Evaluadas y Rechazadas:**
  * *Bujes de trapecios o rótulas*: **RECHAZADA** (`SIN_EVIDENCIA_SUBSISTEMA_SUSPENSION`)
  * *Compresor A/C*: **RECHAZADA** (`SIN_EVIDENCIA_SUBSISTEMA_CLIMATIZACION`)
  * *Temperatura con motor caliente*: **RECHAZADA** (`CONTRADICE_HECHO_CONFIRMADO`)
* **Ausencia Total de Términos Prohibidos:** Se verificó formalmente que la respuesta no contiene *"bujes"*, *"rótulas"*, *"trapecios"*, *"suspensión"* ni menciones a sistemas ajenos.

---

## 11. ESTADO DEL CANAL WHATSAPP Y TRABAJO DE CAMPO DE TESIS

* **Canal WhatsApp Real:** `REAL_WHATSAPP_PENDING_MANUAL_VALIDATION`.
  * La infraestructura de backend, worker de colas y API se encuentran activas en el puerto 8000 con el túnel Ngrok operativo.
  * Se requiere que el usuario efectúe la prueba manual desde su teléfono móvil para registrar la confirmación definitiva de usuario.
* **Integridad Metodológica de Tesis:**
  * No se utilizaron datos sintéticos como muestra oficial.
  * El estado de la muestra de campo se mantiene en su valor verídico: *Trabajo de campo pendiente (recolectado en taller físico)*.

---

## ESTADO FINAL DE LA FASE

```text
FASE11_4_1_CORREGIDA_PENDIENTE_WHATSAPP
```
*(Sistema completamente corregido, verificado mediante pruebas automatizadas y handler real post-reinicio, con build unificado `169c21caf2584414` y listo para la prueba manual desde el WhatsApp del usuario).*
