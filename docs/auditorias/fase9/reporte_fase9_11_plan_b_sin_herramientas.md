# REPORTE FASE 9.11 — AUDITORÍA Y CORRECCIÓN DE PLAN B SIN HERRAMIENTAS

**Fecha de Ejecución**: 2026-09-16  
**Versión del Sistema**: `APP_VERSION = 9.11.0` | `ORCHESTRATOR_VERSION = 9.11.0`  
**Build ID**: `CODE_BUILD_ID = 9b6fedc24bb51ec1`  
**Integridad Metodológica de Tesis**: 19/19 Hashes SHA-256 Fase 8.3 Inmutables (100% idénticos)  
**Estado del Modelo ML**: Inalterado (Linear SVM + TF-IDF, Cero Reentrenamientos, Cero Mutaciones en RAG/FAISS)  

---

## 1. RESUMEN EJECUTIVO DEL INCIDENTE REAL

Durante las pruebas en WhatsApp real tras el cierre de Fase 9.10, se registró la siguiente interacción técnica:

* **Turno 1**: El usuario reportó tirones y pérdida de potencia en marcha bajo demanda de carga (*"Cuando voy avanzando y acelero, el motor comienza a tironear y pierde fuerza. En ralentí se mantiene normal. Empeora al subir una pendiente o acelerar fuerte."*).
* **Turno 2**: Tras responder la pregunta de temperatura (*"Se siente tanto en frío como en caliente..."*), CarBot presentó el diagnóstico técnico:
  * Top 1: *Bujías o bobinas de encendido (misfire)* — 70%
  * Top 2: *Bomba de gasolina quemada o con baja presión* — 20%
  * *Primero revisa:* Salto de chispa en las bobinas y estado/calibración de bujías.
  * Pregunta de cierre: *"¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?"*
* **Turno 3 (Incidente)**: El usuario respondió con honestidad operativa:
  > *"No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina."*
* **Comportamiento Anómalo Observado**: CarBot volvió a emitir prácticamente el mismo reporte, insistió en revisar chispa/bujías con instrumental y reiteró la pregunta: *"¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?"*.

---

## 2. AUDITORÍA FORENSE DE LA TRAZA REAL EN POSTGRESQL

Se extrajo el historial directamente de la base de datos PostgreSQL (`mensajes`, `conversaciones`, `diagnosticos`) de la conversación `f7a37e2d-efe8-4c26-9b62-9f4103e7b094` (Caso `2521e354-0adc-44d1-9345-ecf7c404c6c5`):

| Parámetro Auditado | Registro Real Turno 2 (Previo) | Registro Real Turno 3 (Incidente) |
| :--- | :--- | :--- |
| **Mensaje RAW** | *"Se siente tanto en frío como en caliente..."* | *"No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina."* |
| **Case ID** | `2521e354-0adc-44d1-9345-ecf7c404c6c5` | `2521e354-0adc-44d1-9345-ecf7c404c6c5` |
| **Pregunta Anterior** | *"¿El problema aparece con el motor en frío...?"* | *"¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?"* |
| **Intent Anterior** | `QuestionIntent.TEMPERATURA_APARICION` | `QuestionIntent.GENERAL` |
| **Clasificación Contextual** | `CONDICION` (temperatura = fría y caliente) | `None` *(Fallo de detección contextual)* |
| **Hechos Nuevos Extraídos** | `temperatura: "frío y caliente"` | Ninguno *(Extracción vacía)* |
| **Disponibilidad Herramienta**| No evaluada | `herramientas_no_disponibles = []` *(No persistido)* |
| **Estado NO_APLICA** | No generado | No generado |
| **Estado Operativo** | `EstadoOperativo.MARCHA` | `EstadoOperativo.MARCHA` |
| **Top 3 ML RAW** | Bujías 70%, Bomba 20%, Inyectores 10% | Bujías 70%, Bomba 20%, Inyectores 10% *(Idéntico)* |
| **Plan Técnico Seleccionado**| Salto de chispa en bobinas / bujías | Salto de chispa en bobinas / bujías *(Repetido)* |
| **Pregunta Siguiente** | *¿Deseas que te detalle el procedimiento...?* | *¿Has podido verificar este punto o deseas procedimiento...?* |

### Identificación de la Primera Divergencia
1. **Punto Ciego en `InterpreteRespuestasCortas`**: El intérprete solo buscaba instrumental cuando la pregunta anterior contenía explícitamente palabras clave de multímetro o tester. Al tener la pregunta anterior el intent `QuestionIntent.GENERAL` (*"¿Has podido verificar este punto...?"*), el intérprete evaluó la respuesta como fuera de contexto y devolvió `None`.
2. **Inexistencia de Estructura de Bloqueo de Herramientas**: El estado (`ConversationState`) carecía de campos como `herramientas_no_disponibles` y `pruebas_no_disponibles`.
3. **Ausencia de Motor de Alternativas Sensoriales (Plan B)**: `FormateadorCompacto` y `OrquestadorConversacion` no contaban con un catálogo de desvío sensorial (visual, auditivo, táctil) cuando una prueba instrumental queda bloqueada por el usuario.

---

## 3. ARQUITECTURA TÉCNICA IMPLEMENTADA

Siguiendo estrictamente los límites de Clean Architecture (< 500 líneas por archivo) y las directrices metodológicas de tesis, se crearon e integraron los siguientes componentes:

### 3.1. Módulo `GestorPlanB` (`src/core/conversacion/gestor_plan_b.py`)
* **Catálogo de Instrumental Automotriz**: Cubre de forma genérica y desacoplada:
  * `multimetro` (tester, voltímetro, multímetro)
  * `manometro` (manómetro de presión de combustible / riel)
  * `chispa` (probador de chispa, chispómetro)
  * `escaner` (escáner OBD2, lector de códigos)
  * `compresimetro` (medidor de compresión de cilindros)
  * `vacuometro` (vacuómetro de admisión)
  * `elevador` (elevador hidráulico, rampa, fosa)
  * `reloj_comparador` (micrómetro, reloj comparador de alabeo)
  * `general` (herramientas en general)
* **Reglas Lógicas Distintivas**:
  * $\text{NO\_TENGO\_HERRAMIENTA} \neq \text{RESULTADO\_NEGATIVO}$ (no inventa 0 V ni 0 PSI).
  * $\text{NO\_LO\_HE\_REVISADO} \neq \text{HIPOTESIS\_DESCARTADA}$ (no descarta bujías ni bomba).
  * $\text{NO\_SE\_USARLO} \rightarrow \text{Alternativa sensorial segura}$.
  * $\text{CONSEGUI\_HERRAMIENTA} \rightarrow \text{Desbloqueo dinámico de pruebas}$.
* **Matriz de Alternativas Sensoriales (Plan B)**:

| Hipótesis Top 1 | Prueba Estándar Bloqueada | Plan B Sensorial (Sin Herramientas) | Siguiente Pregunta Contextual |
| :--- | :--- | :--- | :--- |
| **Bujías / Bobinas (Misfire)** | Comprobar chispa con probador | Inspección visual de bobinas, cables y sulfato / aceite en pozos | *¿Notas grietas, cables resecos o presencia de aceite en los pozos de bujía?* |
| **Bomba de Gasolina** | Medir presión con manómetro en riel | Inspección acústica de zumbido en tanque con llave en ON | *Al girar la llave a contacto ON sin arrancar: ¿se escucha un zumbido de 2 segundos bajo el asiento trasero?* |
| **Batería Descargada** | Medición de voltaje con multímetro | Observación visual de luces del tablero al dar arranque | *Al mantener la llave en arranque: ¿las luces del tablero se atenúan por completo o mantienen brillo normal?* |
| **Inyectores Sucios / Falla GDI** | Prueba de pulsos o banco | Olor a gasolina cruda en el escape o humo negro al acelerar | *¿Percibes olor fuerte a gasolina cruda en el escape o notas humo negro cuando el motor tironea?* |
| **Discos Alabeados** | Medición con reloj comparador | Tacto en pedal de freno y vibración en volante según velocidad | *¿La vibración se siente directamente en el pedal de freno o solo en el volante?* |
| **Alternador Defectuoso** | Prueba de carga con multímetro | Luz de batería encendida en tablero o atenuación de faros en ralentí | *¿El testigo de batería se queda encendido o notas que las luces exteriores bajan de intensidad en ralentí?* |

### 3.2. Extensión del Estado (`src/core/conversacion/models.py`)
* Se incorporaron `herramientas_no_disponibles: List[str]` y `pruebas_no_disponibles: List[Dict[str, str]]` en `ConversationState`.
* Métodos añadidos: `bloquear_herramienta()`, `desbloquear_herramienta()`, `bloquear_prueba()`, `es_prueba_bloqueada()`, `ya_preguntado_texto()`.
* Nuevo intent: `QuestionIntent.PLAN_B_SIN_HERRAMIENTAS = "PLAN_B_SIN_HERRAMIENTAS"`.

### 3.3. Integración en `InterpreteRespuestasCortas` y `FormateadorCompacto`
* Detección prioritaria de declaraciones de indisponibilidad (*"no tengo herramientas"*, *"tampoco tengo..."*, *"no lo he revisado"*).
* `FormateadorCompacto._extraer_accion_prioritaria` consulta `estado.es_prueba_bloqueada(clave_accion)`: si la acción estándar requiere instrumental no disponible, la reemplaza automáticamente por el Plan B sensorial seguro.
* Si el usuario rechaza múltiples herramientas y no existen alternativas sensoriales viables, el sistema deriva limpiamente a inspección técnica en taller sin bucles infinitos ni invención de datos.

---

## 4. VERIFICACIÓN DE REPRODUCCIÓN EXACTA Y ESCENARIOS

Se ejecutaron pruebas automatizadas exhaustivas (`pytest`) en `backend/tests/test_plan_b_sin_herramientas_fase9_11.py`:

```text
tests/test_plan_b_sin_herramientas_fase9_11.py::test_reproduccion_exacta_incidente_fase_9_11[asyncio] PASSED
tests/test_plan_b_sin_herramientas_fase9_11.py::test_herramienta_no_disponible_activa_plan_b_multimetro[asyncio] PASSED
tests/test_plan_b_sin_herramientas_fase9_11.py::test_herramienta_disponible_da_procedimiento_o_medicion[asyncio] PASSED
tests/test_plan_b_sin_herramientas_fase9_11.py::test_no_lo_revise_no_inventa_resultado_ni_descarta[asyncio] PASSED
tests/test_plan_b_sin_herramientas_fase9_11.py::test_no_se_usarlo_alternativa_segura[asyncio] PASSED
tests/test_plan_b_sin_herramientas_fase9_11.py::test_posteriormente_consigue_herramienta_desbloquea_prueba[asyncio] PASSED
tests/test_plan_b_sin_herramientas_fase9_11.py::test_dos_herramientas_indisponibles_no_alterna_infinitamente[asyncio] PASSED
tests/test_plan_b_sin_herramientas_fase9_11.py::test_formateador_compacto_usa_plan_b_cuando_herramienta_bloqueada[asyncio] PASSED

============================== 8 passed in 2.83s ==============================
```

### Regresión Completa de la Fase 9 (70 Pruebas Pasadas)
```text
============================== 70 passed in 11.71s ==============================
- test_plan_b_sin_herramientas_fase9_11.py:   8/8 PASSED
- test_segmentacion_casos_fase9_10.py:        10/10 PASSED
- test_respuestas_contextuales_fase9_8.py:    13/13 PASSED
- test_paridad_whatsapp_fase9_7.py:          15/15 PASSED
- test_coherencia_operativa_fase9_6.py:       8/8 PASSED
- test_integridad_conversacional_fase9_5.py:  11/11 PASSED
- test_reglas_metodologicas_tesis.py:         5/5 PASSED
```

---

## 5. TRAZA REAL END-TO-END CON PERSISTENCIA EN POSTGRESQL

Ejecutada mediante `scratch/prueba_real_fase9_11.py` sobre la base de datos real PostgreSQL 17:

```text
================================================================================
FASE 9.11 — AUDITORÍA Y COMPROBACIÓN REAL DE PLAN B SIN HERRAMIENTAS
================================================================================

[1] TELEMETRÍA EN RUNTIME Y PARIDAD DE PROCESOS:
  APP_VERSION:          9.11.0
  ORCHESTRATOR_VERSION: 9.11.0
  CODE_BUILD_ID:        9b6fedc24bb51ec1
  PID API:              15212
  PID Worker:           15212
  Paridad API-Worker:   COMPROBADA (100% IDÉNTICO)

[2] CONEXIÓN A POSTGRESQL: EXITOSA

--------------------------------------------------------------------------------
TURNO 1: SÍNTOMA INICIAL (Tirones en marcha)
--------------------------------------------------------------------------------
Usuario >> Cuando voy avanzando y acelero, el motor comienza a tironear y pierde fuerza. En ralentí se mantiene normal. Empeora al subir una pendiente o acelerar fuerte.
CarBot  << [PREGUNTAR] ¿El problema aparece con el motor en frío (primeros minutos tras arrancar) o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?
Traza T1: fase=ACLARANDO, es_pregunta=True, intent=TEMPERATURA_APARICION

--------------------------------------------------------------------------------
TURNO 2: RESPUESTA DE TEMPERATURA
--------------------------------------------------------------------------------
Usuario >> Se siente tanto en frío como en caliente, pero cuando acelero fuerte o subo una pendiente se nota mucho más.
CarBot  << [DIAGNOSTICAR]
🔧 *Posibles causas*
1. Falla en bujias o bobinas de encendido (misfire) — 62%
2. Bomba de gasolina quemada o con baja presion — 25%
3. Falla de descarbonizacion e inyeccion directa GDI — 13%

🛠️ *Primero revisa:* salto de chispa en las bobinas y estado/calibración del electrodo de las bujías.
¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?

--------------------------------------------------------------------------------
TURNO 3: INCIDENTE REAL — INDISPONIBILIDAD EXPLÍCITA DE HERRAMIENTAS
--------------------------------------------------------------------------------
Usuario >> No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina.
CarBot  << [PLAN_B]
Entiendo, sin herramientas para chispa. Al revisar visualmente las bobinas y cables: ¿notas grietas, cables resecos o presencia de aceite en los pozos de bujía?

[3] AUDITORÍA DE ESTADO EN POSTGRESQL TRAS TURNO 3:
  Case ID:                     d66c2345-8f22-428c-b551-d2b84c0cbdb6
  Herramientas No Disponibles: ['manometro', 'chispa']
  Pruebas Bloqueadas:          ['medir_presion_gasolina', 'comprobar_chispa_bobinas']
  Hipótesis descartadas:       []
  Top 3 Actual:                ['Falla en bujias o bobinas de encendido (misfire)', 'Bomba de gasolina quemada o con baja presion', ...]

--------------------------------------------------------------------------------
TURNO 4: RESULTADO DE PLAN B SENSORIAL SIN HERRAMIENTAS
--------------------------------------------------------------------------------
Usuario >> Ya revisé visualmente las bobinas y cables. No se ven rotas ni hay aceite, pero el cable de la bobina 2 tiene como un sulfato blanco en la conexión.
CarBot  << [DIAGNOSTICAR]
🔧 *Posibles causas*
1. Falla en bujias o bobinas de encendido (misfire) — 70%
2. Bomba de gasolina quemada o con baja presion — 20%

🛠️ *Primero revisa:* comprobación de olor a combustible crudo por el tubo de escape al acelerar.
¿Percibes un olor fuerte a gasolina cruda en el escape o notas humo negro cuando el motor tironea?

================================================================================
RESULTADO DE LA AUDITORÍA POSTGRESQL: EXITOSA (100% CONFORME)
================================================================================
```

---

## 6. AUDITORÍA DE INMUTABILIDAD DE ARTEFACTOS CONGELADOS (19/19)

Verificación con `scratch/verify_immutability.py` contra `machine_learning/models/reporte_fase8_3_congelado.json`:

| Componente Oficial Fase 8.3 | Hash SHA-256 Actual | Estado de Integridad |
| :--- | :--- | :--- |
| `dataset_train` | `c94d6e7b88ef72ea...` | **100% Inmutable** |
| `benchmark_dev_60` | `113b5f190758346a...` | **100% Inmutable** |
| `modelo_diagnostico_falla_prod` | `3d8199595b69bb01...` | **100% Inmutable** |
| `modelo_sistema_prod` | `22d11492e9576664...` | **100% Inmutable** |
| `vectorizador_tfidf_prod` | `8b8e8c3b3571fe96...` | **100% Inmutable** |
| `modelo_diagnostico_candidata` | `3d8199595b69bb01...` | **100% Inmutable** |
| `modelo_sistema_candidata` | `22d11492e9576664...` | **100% Inmutable** |
| `vectorizador_tfidf_candidata` | `8b8e8c3b3571fe96...` | **100% Inmutable** |
| `corpus_metadatos_rag` | `2f0684477522efb6...` | **100% Inmutable** |
| `indice_faiss` | `757c4b006a8995f4...` | **100% Inmutable** |
| `adaptador_modelo_ml` | `014d3e6f6f9f5c5b...` | **100% Inmutable** |
| `motor_rag` | `eaa316a87ecaa1be...` | **100% Inmutable** |
| `rag_relevance_filter` | `fa3d6aef13639bc3...` | **100% Inmutable** |
| `auto_interrogador` | `2e746e498facea34...` | **100% Inmutable** |
| `politica_fusion` | `073b97fe07c88918...` | **100% Inmutable** |
| `prompt_builder` | `e0b26f32f278bb10...` | **100% Inmutable** |
| `text_processor` | `f7075605f6a0e325...` | **100% Inmutable** |
| `taxonomia_sistemas` | `561e95c952effcd0...` | **100% Inmutable** |
| `gestor_diagnostico` | `66bead0526763314...` | **100% Inmutable** |

---

## 7. CUMPLIMIENTO DE LÍMITES DE CÓDIGO (CLEAN ARCHITECTURE)

| Archivo Modificado / Creado | Líneas Totales | Límite Máximo (< 500) | Cumplimiento |
| :--- | :--- | :--- | :--- |
| `backend/src/core/version.py` | 67 líneas | 500 | Conforme |
| `backend/src/core/conversacion/gestor_plan_b.py` | 334 líneas | 500 | Conforme |
| `backend/src/core/conversacion/models.py` | 488 líneas | 500 | Conforme |
| `backend/src/core/conversacion/interprete_respuestas_cortas.py` | 373 líneas | 500 | Conforme |
| `backend/src/core/conversacion/formateador_compacto.py` | 391 líneas | 500 | Conforme |
| `backend/src/core/conversacion/orquestador_conversacion.py` | 493 líneas | 500 | Conforme |

---

## 8. CONCLUSIÓN Y ESTADO DEL SISTEMA

La Fase 9.11 queda **auditada, corregida, probada y validada en runtime al 100%**:
1. La indisponibilidad explícita de herramientas se almacena en el estado persistente (`herramientas_no_disponibles`, `pruebas_no_disponibles`).
2. Se respeta rigurosamente el axioma: `NO_TENGO_HERRAMIENTA != RESULTADO_NEGATIVO` y `NO_LO_HE_REVISADO != HIPOTESIS_DESCARTADA`.
3. CarBot activa automáticamente un Plan B sensorial seguro (visual, acústico, táctil) cuando la comprobación prioritaria queda bloqueada.
4. Se previene cualquier bucle repetitivo de preguntas o procedimientos inviables.
5. El runtime se encuentra sincronizado en la versión `9.11.0` con paridad total de procesos.

*(Tal como fue instruido taxativamente en el prompt, el agente se detiene aquí y NO inicia la Fase 10).*
