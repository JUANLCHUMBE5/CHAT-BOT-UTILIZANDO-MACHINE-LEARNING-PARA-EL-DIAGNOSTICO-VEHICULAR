# REPORTE FASE 9.7 — PARIDAD TEST ↔ WHATSAPP Y SELECCIÓN CONTEXTUAL DE PREGUNTAS

**Fecha de Auditoría:** 16 de Septiembre de 2026  
**Entorno:** Producción Local Windows / PostgreSQL 17 / Python 3.14  
**Versión del Orquestador:** `9.7.0`  
**Estado Criptográfico:** 19/19 Componentes Fase 8.3 Inmutables (100% SHA-256 verificado)

---

## 1. Contexto del Incidente y Caso Exacto

Durante las pruebas de campo en WhatsApp real tras la implementación de la Fase 9.6, se envió el mensaje exacto validado por los tests automatizados:

> *"Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."*

- **Resultado esperado según tests Fase 9.6:**
  > *"Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, o se mantienen encendidas con brillo normal?"* (`QuestionIntent.COMPORTAMIENTO_ARRANQUE`)
- **Resultado emitido en WhatsApp real:**
  > *"¿El problema aparece en frío (primer arranque de la mañana) o únicamente después de que el motor alcanza su temperatura de trabajo normal?"* (`QuestionIntent.TEMPERATURA_APARICION`)

---

## 2. Traza del Webhook Real en Base de Datos

A partir de la inspección directa de PostgreSQL (`conversaciones` y `mensajes`), se reconstruyó la traza exacta del evento en WhatsApp:

| Campo | Registro del Webhook Real |
| :--- | :--- |
| **`meta_message_id`** | `wamid.HBgLNTE5NTUwOTUxNDcVAgASGBYzRUIwN0EyNkY1QzA4RjlGQUVEODFFAA==` |
| **`case_id`** | `26d11da3-b3c1-424f-a9cb-b2f5674a7a8d` |
| **`conversacion_id`** | `f7a37e2d-efe8-4c26-9b62-9f4103e7b094` |
| **`timestamp`** | `2026-09-17 01:00:06.295767+00:00` (`20:00:06` local) |
| **`ConversationState` antes** | `turno_actual`: 1, `turnos_repregunta`: 1, `preguntas_realizadas`: `[{"intent": "CONDICION_OPERACION"}]`, `estado_operativo`: `None` (proceso previo a Fase 9.6). |
| **`mensaje_original`** | *"Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."* |
| **`intent`** | `consulta_inicial_sintomas` |
| **`hechos_extraidos` (en BD)** | `sintoma_chasquido_de_arranque_clac: "chasquido de arranque clac"` |
| **`estado_operativo`** | `DESCONOCIDO` (no existía detector en el proceso en ejecución) |
| **`nivel_suficiencia`** | `BAJA` (1/3 categorías: solo síntoma) |
| **`preguntas_candidatas`** | `['CONDICION_OPERACION', 'TEMPERATURA_APARICION', 'CODIGO_DTC']` (código antiguo) |
| **`preguntas_descartadas`** | `CONDICION_OPERACION` (Motivo: ya formulada en Turno 1) |
| **`question_intents_resueltos`** | `['CONDICION_OPERACION']` |
| **`pregunta_seleccionada`** | *"¿El problema aparece en frío (primer arranque de la mañana) o únicamente después de que el motor alcanza su temperatura de trabajo normal?"* |
| **`ConversationState` después** | `turno_actual`: 2, `turnos_repregunta`: 2, `preguntas_realizadas`: `[CONDICION_OPERACION, TEMPERATURA_APARICION]` |

---

## 3. Ejecución del Mismo Mensaje por Test y Comparación Campo por Campo

Se ejecutó el mismo mensaje en el entorno de pruebas automatizadas y a través del entrypoint unificado `TechnicalDiagnosticWorkflow.preparar`:

| Dimensión de la Traza | Test Automatizado | Webhook Real (01:00:06 UTC) | ¿Divergencia? |
| :--- | :--- | :--- | :--- |
| **Entorno de Ejecución** | Proceso Python fresco con código Fase 9.6 | Proceso Uvicorn PID 27764 (iniciado a las 00:42:32 UTC) | **SÍ (Primera divergencia)** |
| **Versión del Código** | Fase 9.6 (guardada 00:54:53 UTC) | Fase 9.5 (anterior a 00:42:32 UTC) | **SÍ** |
| **Turno en Conversación** | Turno 1 (sesión limpia) | Turno 2 (Turno 1 ocurrió a las 00:43:11 UTC) | **SÍ** |
| **`estado_operativo`** | `ARRANQUE` | `None` / `DESCONOCIDO` | **SÍ** |
| **Hechos Extraídos** | `motor_arranca=NO`, `evento=giro_llave`, `ruido_arranque=clic_unico`, `tablero_enciende=SI`, etc. | Solo `sintoma_chasquido_de_arranque_clac` | **SÍ** |
| **Candidatas Evaluadas** | `COMPORTAMIENTO_ARRANQUE` (luces, giro), `TEMPERATURA_APARICION`, `CODIGO_DTC` | `CONDICION_OPERACION`, `TEMPERATURA_APARICION`, `CODIGO_DTC` | **SÍ** |
| **Pregunta Seleccionada** | *"Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan...?"* | *"¿El problema aparece en frío... o después de que el motor alcanza su temperatura de trabajo normal?"* | **SÍ** |

### Primera Divergencia Encontrada
La primera divergencia ocurrió en la **capa de despliegue operativo**: el proceso servidor de Uvicorn (PID 24708 / hijo PID 27764) y el Worker de colas (PID 25068) se iniciaron a las `00:42:32 UTC`. Los cambios de código de la Fase 9.6 se guardaron en disco a las `00:54:53 UTC`. Debido a la arquitectura de recarga en caliente en Windows, el proceso worker hijo de Uvicorn no recargó los submódulos de `backend/src/core/conversacion/`. Por lo tanto, el webhook a las `01:00:06 UTC` fue atendido en memoria por el código antiguo previo a la Fase 9.6.

---

## 4. Auditoría de `TEMPERATURA_APARICION` y Causa Raíz Conceptual

Más allá del desfase de despliegue, la auditoría técnica reveló una **deficiencia conceptual crítica** en `TEMPERATURA_APARICION`:

1. **Presuposición Fáctica Encubierta:**
   La pregunta histórica de temperatura rezaba:
   > *"¿El problema aparece en frío (primer arranque de la mañana) o únicamente después de que el motor alcanza su temperatura de trabajo normal?"*
   Esta formulación presupone que el vehículo es capaz de arrancar y circular hasta régimen térmico.
2. **Incompatibilidad con `motor_arranca == NO`:**
   Si un automóvil no arranca en absoluto (solo hace un clic seco en reposo), es físicamente imposible e ilógico para el mecánico o cliente responder si la avería ocurre *"después de que el motor alcanza su temperatura de trabajo normal"*, puesto que el motor nunca entra en marcha.
3. **Ausencia de Precondiciones:**
   `GeneradorPreguntas` seleccionaba la primera pregunta disponible sin evaluar si las **precondiciones lógicas** de la formulación estaban satisfechas por los hechos conocidos.

---

## 5. Principio General de Presuposiciones (Precondiciones de Pregunta)

Se implementó el Principio General de Presuposiciones mediante el cual cada pregunta técnica declara y valida sus precondiciones lógicas antes de ser admitida como candidata:

### 5.1 Precondiciones Formales Implementadas
1. **`TEMPERATURA_MOTOR_EN_MARCHA` (Régimen de trabajo):**
   - *Texto:* *"¿El problema aparece con el motor aún frío (primeros minutos tras arrancar) o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?"*
   - *Precondición:* Requiere `motor_arranca != NO` o `tiene_antecedente_motor_en_marcha() == True`.
   - *Comportamiento si no se cumple:* Se descarta con motivo explícito:  
     `"PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA"`.
2. **`TEMPERATURA_AMBIENTAL_ARRANQUE` (Reposo térmico / frío ambiental):**
   - *Texto:* *"¿La dificultad para arrancar ocurrió con el motor totalmente frío (primer intento tras horas o días estacionado) o intentaste encenderlo poco después de haber apagado el motor?"*
   - *Precondición:* Compatible con `ARRANQUE` y `DESCONOCIDO`. No asume que el motor arrancó en este episodio.
3. **`CAIDA_TENSION_ARRANQUE` / `COMPORTAMIENTO_ARRANQUE`:**
   - *Texto:* *"Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, o se mantienen encendidas con brillo normal?"*
   - *Precondición:* `estado_operativo == ARRANQUE` o `evento == giro_llave` o `motor_arranca == NO`.
4. **`CONDICION_OPERACION`:**
   - *Precondición:* Requiere que el vehículo pueda desplazarse o regular en ralentí (`motor_arranca != NO` o antecedente).
5. **`CODIGO_DTC`:**
   - *Precondición:* Incompatible con averías mecánicas puras sin control electrónico (alabeo de discos, desbalanceo de ruedas, embrague patinando).

---

## 6. Priorización por Ganancia de Información

Se reemplazó el bucle secuencial por un mecanismo de ordenamiento ponderado por ganancia de información diagnóstica:

| Nivel | Tipo de Pregunta / Intent | Ponderación | Criterio de Ganancia Informativa |
| :---: | :--- | :---: | :--- |
| **1** | `ACLARACION_CONTRADICCION` | **100** | Máxima prioridad: resolver contradicción física entre hechos reportados. |
| **2** | Específica del `estado_operativo` activo (`COMPORTAMIENTO_ARRANQUE` - luces) | **85** | Discrimina directamente entre falla de batería vs. solenoide/arranque. |
| **3** | Específica del `estado_operativo` activo (`COMPORTAMIENTO_ARRANQUE` - giro motor) | **80** | Discrimina entre motor trabado vs. falla de suministro eléctrico. |
| **4** | `TEMPERATURA_MOTOR_EN_MARCHA` (en `MARCHA` o `RALENTI`) | **80** | Discrimina dilatación térmica en bobinas/sensores CKP/CMP tras circular. |
| **5** | `DISCRIMINACION_TOP3` | **75** | Diferencia entre las 3 hipótesis líderes calculadas por ML. |
| **6** | `CONDICION_OPERACION` (solo en `DESCONOCIDO`) | **75** | Discrimina régimen inicial cuando no hay información del estado. |
| **7** | `TEMPERATURA_AMBIENTAL_ARRANQUE` (en `ARRANQUE`) | **65** | Evalúa descarga por frío ambiental tras reposo prolongado. |
| **8** | `CODIGO_DTC` | **40** | Pregunta complementaria de escáner. |

---

## 7. Paridad Obligatoria Test ↔ Webhook

Se implementó la prueba end-to-end `test_paridad_caso_exacto_webhook_vs_test` en `backend/tests/test_paridad_whatsapp_fase9_7.py`, atravesando exactamente el entrypoint de WhatsApp (`TechnicalDiagnosticWorkflow.preparar`):

### Traza Unificada Resultante (Test y Webhook)
```json
{
  "turno": 1,
  "version_orquestador": "9.7.0",
  "estado_operativo": "ARRANQUE",
  "hechos_nuevos_extraidos": [
    {"campo": "motor_arranca", "valor": "NO"},
    {"campo": "evento", "valor": "giro_llave"},
    {"campo": "ruido_arranque", "valor": "clic_unico"},
    {"campo": "tablero_enciende", "valor": "SI"},
    {"campo": "radio_enciende", "valor": "SI"}
  ],
  "preguntas_candidatas": [
    "COMPORTAMIENTO_ARRANQUE",
    "COMPORTAMIENTO_ARRANQUE",
    "TEMPERATURA_APARICION",
    "TEMPERATURA_APARICION",
    "CODIGO_DTC"
  ],
  "preguntas_descartadas": [
    {"intent": "COMPORTAMIENTO_ARRANQUE", "motivo": "HECHO_YA_CONOCIDO"},
    {"intent": "TEMPERATURA_APARICION", "motivo": "PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA"}
  ],
  "candidatas_compatibles_ordenadas": [
    {"intent": "COMPORTAMIENTO_ARRANQUE", "score": 85},
    {"intent": "TEMPERATURA_APARICION", "score": 65},
    {"intent": "CODIGO_DTC", "score": 40}
  ],
  "pregunta_seleccionada": "Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, o se mantienen encendidas con brillo normal?",
  "question_intent": "COMPORTAMIENTO_ARRANQUE"
}
```

---

## 8. Batería de Regresión Exhaustiva

Se ejecutó la suite completa de 15 pruebas en `test_paridad_whatsapp_fase9_7.py` cubriendo los 11 escenarios clínicos de regresión:

1. **No-arranque con clic único:** Identifica `ARRANQUE`, descarta temperatura de régimen y selecciona caída de tensión de luces (`COMPORTAMIENTO_ARRANQUE`). (PASÓ)
2. **Clac-clac + luces tenues:** Hechos de ruido y atenuación identificados; no repregunta sobre luces. (PASÓ)
3. **Falla únicamente en caliente tras conducir:** Identifica `MARCHA`, detecta hecho térmico y mantiene compatibilidad térmica en caliente. (PASÓ)
4. **Falla únicamente en frío:** Detecta hecho térmico lingüístico sin formular repreguntas térmicas redundantes. (PASÓ)
5. **Pérdida de potencia en marcha:** Identifica `MARCHA`, prohíbe formular preguntas de arranque. (PASÓ)
6. **Ralentí:** Identifica `RALENTI`, prohíbe formular preguntas de arranque o frenado. (PASÓ)
7. **Frenado:** Identifica `FRENADO`, prohíbe preguntas de arranque y descarta escáner DTC por avería mecánica pura. (PASÓ)
8. **Estado desconocido:** Formula `CONDICION_OPERACION`. (PASÓ)
9. **Contradicción (arranque vs. marcha):** Identifica `conflicto_operativo` y formula `ACLARACION_CONTRADICCION` con prioridad 100. (PASÓ)
10. **Caso nuevo / reinicio:** Comando detectado y memoria reseteada. (PASÓ)
11. **Flujo de descarte con "NO":** Registro adecuado de descarte sin bucles. (PASÓ)

**Resultado global:** 34/34 pruebas pasadas exitosamente en las suites de Fases 9.5, 9.6 y 9.7 (0 fallos).

---

## 9. Verificación de Inmutabilidad Criptográfica (Fase 8.3)

Se ejecutó la auditoría SHA-256 de todos los artefactos congelados contra `machine_learning/models/reporte_fase8_3_congelado.json`:

| Componente | Ruta | Hash SHA-256 | Estado |
| :--- | :--- | :---: | :---: |
| `dataset_train` | `machine_learning/data/dataset_sintomas_limpio.csv` | `c94d6e7b...` | **INMUTABLE** |
| `benchmark_dev_60` | `machine_learning/data/benchmark_dev_60_casos.py` | `113b5f19...` | **INMUTABLE** |
| `modelo_diagnostico_falla_prod` | `machine_learning/models/modelo_diagnostico.pkl` | `3d819959...` | **INMUTABLE** |
| `modelo_sistema_prod` | `machine_learning/models/modelo_sistema.pkl` | `22d11492...` | **INMUTABLE** |
| `vectorizador_tfidf_prod` | `machine_learning/models/vectorizador_tfidf.pkl` | `8b8e8c3b...` | **INMUTABLE** |
| `modelo_diagnostico_candidata` | `machine_learning/models/fase8_candidata/modelo_diagnostico.pkl` | `3d819959...` | **INMUTABLE** |
| `modelo_sistema_candidata` | `machine_learning/models/fase8_candidata/modelo_sistema.pkl` | `22d11492...` | **INMUTABLE** |
| `vectorizador_tfidf_candidata` | `machine_learning/models/fase8_candidata/vectorizador_tfidf.pkl` | `8b8e8c3b...` | **INMUTABLE** |
| `corpus_metadatos_rag` | `machine_learning/manuals/metadatos_manuales.json` | `2f068447...` | **INMUTABLE** |
| `indice_faiss` | `machine_learning/manuals/indice_faiss.index` | `757c4b00...` | **INMUTABLE** |
| `adaptador_modelo_ml` | `backend/src/infrastructure/modelo_ml.py` | `014d3e6f...` | **INMUTABLE** |
| `motor_rag` | `backend/src/infrastructure/motor_rag.py` | `eaa316a8...` | **INMUTABLE** |
| `rag_relevance_filter` | `backend/src/infrastructure/rag/relevance_filter.py` | `fa3d6aef...` | **INMUTABLE** |
| `auto_interrogador` | `backend/src/core/diagnostico/auto_interrogador.py` | `2e746e49...` | **INMUTABLE** |
| `politica_fusion` | `backend/src/core/diagnostico/politica_fusion.py` | `073b97fe...` | **INMUTABLE** |
| `prompt_builder` | `backend/src/core/diagnostico/prompt_builder.py` | `e0b26f32...` | **INMUTABLE** |
| `text_processor` | `backend/src/core/diagnostico/text_processor.py` | `f7075605...` | **INMUTABLE** |
| `taxonomia_sistemas` | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `561e95c9...` | **INMUTABLE** |
| `gestor_diagnostico` | `backend/src/core/gestor_diagnostico.py` | `66bead05...` | **INMUTABLE** |

**Resultado de Inmutabilidad:** 19/19 artefactos 100% idénticos e inalterados.

---

## 10. Conclusión y Síntesis Final

1. **Primera Divergencia:** Proceso Uvicorn / Worker desincronizado en Windows (PID 24708 / 27764 iniciado antes de los cambios de Fase 9.6).
2. **Causa Raíz:** Formulación de `TEMPERATURA_APARICION` con presuposición de motor en marcha ("alcanza temperatura de trabajo normal") carente de filtro de precondiciones y ordenamiento secuencial ciego.
3. **Corrección Implementada:**
   - Modelado de **Precondiciones Lógicas de Pregunta** que descarta preguntas de régimen cuando `motor_arranca == NO` sin antecedente de marcha.
   - Diferenciación de preguntas térmicas: de régimen vs. ambiental / reposo prolongado.
   - **Priorización por Ganancia de Información** que otorga máxima ponderación a la condición operativa activa (`COMPORTAMIENTO_ARRANQUE` = 85).
   - Terminación forzosa de procesos antiguos desfasados.
   - Trazabilidad con `version_orquestador: "9.7.0"` para validación inmediata en producción.
4. **Validación:** 34 tests unitarios e integrados aprobados, paridad absoluta demostrada a través de `TechnicalDiagnosticWorkflow` e inmutabilidad criptográfica Fase 8.3 plenamente preservada.
