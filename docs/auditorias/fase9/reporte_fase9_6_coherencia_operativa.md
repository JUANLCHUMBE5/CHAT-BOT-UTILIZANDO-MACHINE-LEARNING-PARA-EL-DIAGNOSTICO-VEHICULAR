# REPORTE OFICIAL FASE 9.6: COHERENCIA OPERATIVA DE PREGUNTAS Y ANTI-LOOP SEMÁNTICO

**Fecha:** 16 de Septiembre de 2026  
**Sistema:** CarBot — Chatbot con Machine Learning para Diagnóstico Vehicular  
**Capa Afectada:** Conversacional / Orquestación  
**Estado ML / RAG:** Intacto (Linear SVM + TF-IDF y FAISS inmutables, 19/19 hashes SHA-256 verificados)  

---

## 1. OBJETIVO DE LA FASE

Corregir la deficiencia conversacional observada en producción real donde CarBot conocía que el vehículo **NO ARRANCABA**, pero el generador de preguntas formulaba consultas físicamente absurdas e incompatibles correspondientes a ralentí, carretera o frenado.

La intervención se realizó **estrictamente en la capa conversacional y de orquestación**:
- **Cero reentrenamiento o modificación de modelos ML.**
- **Cero alteración de TRAIN, DEV, calibración, RAG ni artefactos congelados de Fase 8.3.**
- **Cero reglas diagnósticas rígidas:** El estado operativo delimita la compatibilidad lógica de las preguntas, no determina la avería ni sustituye al clasificador SVM.

---

## 2. REPRODUCCIÓN DEL CASO REAL DE WHATSAPP

### 2.1 Mensaje del Usuario
> *"Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."*

### 2.2 Trace Antes de Fase 9.6 (Comportamiento Erróneo)
```json
{
  "mensaje_actual": "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también.",
  "hechos_extraidos": [
    "sintoma_chasquido_de_arranque_clac"
  ],
  "estado_operativo": "NO_EXISTE",
  "question_intent": "CONDICION_OPERACION",
  "preguntas_candidatas": [
    "CONDICION_OPERACION",
    "TEMPERATURA_APARICION",
    "CODIGO_DTC"
  ],
  "preguntas_descartadas": [],
  "pregunta_final": "¿La falla se presenta cuando el vehículo está detenido en ralentí, al acelerar con fuerza en carretera o únicamente al pisar el pedal de freno?"
}
```

**Causa Raíz de la Falla:**
1. Inexistencia del concepto de `EstadoOperativo` en `ConversationState`.
2. Extracción incompleta de hechos de arranque: la expresión coloquial *"no quiso arrancar"* no coincidía con el patrón de motor no arranca, ni se extrajeron *"evento = giro_llave"*, *"ruido_arranque = clic_unico"*, *"tablero_enciende = SI"*, *"radio_enciende = SI"*.
3. `GeneradorPreguntas` evaluaba `already_known(CONDICION_OPERACION)` buscando únicamente el hecho literal `condicion_operacion`. Al no hallarlo, disparaba la pregunta de ralentí/carretera/frenado sin advertir que el motor ni siquiera arrancaba.
4. Inexistencia de un filtro de compatibilidad operacional (`es_pregunta_compatible`) que impidiera el envío de preguntas físicamente incompatibles con los hechos observados.

### 2.3 Trace Después de Fase 9.6 (Comportamiento Corregido)
```json
{
  "mensaje_actual": "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también.",
  "hechos_extraidos": [
    {"campo": "motor_arranca", "valor": "NO", "categoria": "condicion"},
    {"campo": "evento", "valor": "giro_llave", "categoria": "condicion"},
    {"campo": "ruido_arranque", "valor": "clic_unico", "categoria": "sintoma"},
    {"campo": "tablero_enciende", "valor": "SI", "categoria": "condicion"},
    {"campo": "radio_enciende", "valor": "SI", "categoria": "condicion"},
    {"campo": "sintoma_chasquido_de_arranque_clac", "valor": "chasquido de arranque clac", "categoria": "sintoma"},
    {"campo": "sintoma_motor_no_arranca", "valor": "motor no arranca", "categoria": "sintoma"}
  ],
  "estado_operativo": "ARRANQUE",
  "question_intent": "COMPORTAMIENTO_ARRANQUE",
  "preguntas_candidatas": [
    "COMPORTAMIENTO_ARRANQUE",
    "COMPORTAMIENTO_ARRANQUE",
    "TEMPERATURA_APARICION",
    "CODIGO_DTC"
  ],
  "preguntas_descartadas": [
    {
      "intent": "COMPORTAMIENTO_ARRANQUE",
      "pregunta": "Al intentar arrancar: ¿el motor hace algún intento de girar (gira pesado o lento) o no gira absolutamente nada (solo se oye el clic)?",
      "motivo": "HECHO_YA_CONOCIDO"
    }
  ],
  "pregunta_final": "Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, o se mantienen encendidas con brillo normal?"
}
```

---

## 3. ARQUITECTURA E IMPLEMENTACIÓN TÉCNICA

### 3.1 Concepto de `EstadoOperativo`
Se incorporó el enum `EstadoOperativo` en `src/core/conversacion/models.py`:
- `ARRANQUE`: El usuario describe un intento de encendido o arranque fallido.
- `RALENTI`: El síntoma ocurre exclusivamente con motor encendido detenido (semáforo, neutro).
- `MARCHA`: El síntoma ocurre en circulación (carretera, aceleración bajo carga, alta velocidad).
- `FRENADO`: El síntoma ocurre exclusivamente al pisar el pedal de freno o decelerar con frenos.
- `ESTACIONADO`: Vehículo en reposo sin intento de arranque ni marcha.
- `DESCONOCIDO`: Falla genérica inicial sin contexto operacional reportado (ej. *"mi carro falla"*).

> **Aclaración Arquitectónica:** `EstadoOperativo` **NO** es un nuevo clasificador de averías ni sustituye al SVM TF-IDF. Representa única y exclusivamente la condición física y operacional descrita por el conductor.

### 3.2 Representación Rigurosa de Hechos de Arranque
Se implementaron analizadores deterministas en `ExtractorHechos`:
- `motor_arranca = NO`
- `evento = giro_llave`
- `ruido_arranque = clic_unico` (o `clics_repetidos`)
- `tablero_enciende = SI`
- `radio_enciende = SI`
- `luces_se_atenuan = SI`

**Reglas de Inferencia Estricta:**
- **PROHIBIDO** inferir `bateria_buena = SI`: El encendido de accesorios (luces de tablero, radio) consume entre 2 y 5 amperios, lo cual no demuestra que la batería conserve capacidad de entrega bajo la carga real del motor de arranque (150 a 200 amperios).
- **PROHIBIDO** inferir `motor_arranque_averiado = SI`: La presencia de un clic seco puede originarse por solenoide atascado, carbones gastados, caída de tensión en bornes sulfatados o relevador de arranque con contactos flameados.

### 3.3 Filtro de Compatibilidad Operacional y Detección de Preguntas Imposibles
Antes de formular cualquier pregunta, se evalúa mediante `GeneradorPreguntas.es_pregunta_compatible(intent, texto, estado)`.

Si devuelve `False`, se rechaza registrando uno de los 4 motivos canónicos:
1. `INCOMPATIBLE_ESTADO_OPERATIVO`: Bloquea preguntas de ralentí, aceleración o frenado si el estado es `ARRANQUE`; o preguntas de arranque si el vehículo circula en `MARCHA`.
2. `HECHO_YA_CONOCIDO`: Bloquea preguntas sobre hechos ya confirmados (ej. no volver a preguntar si hace un clic si ya se confirmó `ruido_arranque = clic_unico`).
3. `INTENT_YA_RESUELTO`: Bloquea `CONDICION_OPERACION` si el estado operativo ya es conocido y distinto de `DESCONOCIDO`.
4. `PREGUNTA_REPETIDA`: Bloquea preguntas ya realizadas o con intent ya abordado y respondido.

---

## 4. MATRIZ DE ESCENARIOS OPERACIONALES (A - H)

A continuación se detalla la traza `mensaje → hechos → estado operativo → candidatos → filtros → pregunta elegida`:

### Escenario A: No arranca + clic único + accesorios encienden
- **Mensaje:** *"no arranca, hace un solo clic seco al girar la llave pero la radio y tablero prenden"*
- **Hechos Extraídos:** `motor_arranca: NO`, `evento: giro_llave`, `ruido_arranque: clic_unico`, `tablero_enciende: SI`, `radio_enciende: SI`.
- **Estado Operativo:** `ARRANQUE`.
- **Candidatos Evaluados:** `['COMPORTAMIENTO_ARRANQUE' (giro), 'COMPORTAMIENTO_ARRANQUE' (luces), 'TEMPERATURA_APARICION', 'CODIGO_DTC']`.
- **Filtros Aplicados:** Descartada pregunta de giro por `HECHO_YA_CONOCIDO` (menciona clic). Bloqueada `CONDICION_OPERACION` por `INTENT_YA_RESUELTO`.
- **Pregunta Elegida:** *"Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan / apagan por completo, o se mantienen encendidas con brillo normal?"*
- **Resultado:** **Aprobado**. Cero menciones a ralentí, carretera ni frenado.

### Escenario B: No arranca + clac-clac + luces se atenúan
- **Mensaje:** *"al darle a la llave no arranca, hace tac-tac rápido y las luces del tablero se atenúan"*
- **Hechos Extraídos:** `motor_arranca: NO`, `evento: giro_llave`, `ruido_arranque: clics_repetidos`, `luces_se_atenuan: SI`.
- **Estado Operativo:** `ARRANQUE`.
- **Candidatos Evaluados:** Preguntas específicas de arranque vs. diagnóstico directo.
- **Filtros Aplicados:** Bloqueo total de ralentí, frenado y marcha (`INCOMPATIBLE_ESTADO_OPERATIVO`).
- **Pregunta Elegida:** Pregunta de giro del motor o diagnóstico diferencial inmediato por evidencia fuerte (solenoide + caída de tensión).
- **Resultado:** **Aprobado**. Exclusivamente compatible con arranque.

### Escenario C: Tiembla únicamente en ralentí
- **Mensaje:** *"el motor tiembla únicamente cuando está detenido en ralentí en el semáforo"*
- **Hechos Extraídos:** `condicion_operacion: detenido en ralentí`, `sintoma: vibración`.
- **Estado Operativo:** `RALENTI`.
- **Candidatos Evaluados:** `['TEMPERATURA_APARICION', 'CODIGO_DTC']`.
- **Filtros Aplicados:** Descartada `CONDICION_OPERACION` por `INTENT_YA_RESUELTO`. Descartadas preguntas de frenos por `INCOMPATIBLE_ESTADO_OPERATIVO`.
- **Pregunta Elegida:** *"¿El problema aparece en frío (primer arranque de la mañana) o únicamente después de que el motor alcanza su temperatura de trabajo normal?"*
- **Resultado:** **Aprobado**. Cero preguntas de frenado.

### Escenario D: Pierde potencia después de 20 minutos circulando
- **Mensaje:** *"pierde potencia después de 20 minutos circulando en carretera a 90 km/h"*
- **Hechos Extraídos:** `condicion_operacion: en carretera a velocidad`, `sintoma: pérdida de potencia`.
- **Estado Operativo:** `MARCHA`.
- **Candidatos Evaluados:** `['TEMPERATURA_APARICION', 'CODIGO_DTC']`.
- **Filtros Aplicados:** Bloqueo de preguntas de arranque por `INCOMPATIBLE_ESTADO_OPERATIVO`.
- **Pregunta Elegida:** Pregunta técnica de temperatura o diagnóstico ML según suficiencia.
- **Resultado:** **Aprobado**. Cero preguntas de intento de encendido.

### Escenario E: Vibra únicamente al frenar
- **Mensaje:** *"el timón vibra únicamente cuando piso el pedal de freno"*
- **Hechos Extraídos:** `condicion_operacion: al frenar`, `sintoma: vibración`.
- **Estado Operativo:** `FRENADO`.
- **Candidatos Evaluados:** `['TEMPERATURA_APARICION', 'CODIGO_DTC']`.
- **Filtros Aplicados:** Descartado cualquier escenario de no-arranque o fallo de encendido.
- **Pregunta Elegida:** Consulta específica de escáner / velocidad o diagnóstico de alabeo/pastillas.
- **Resultado:** **Aprobado**. Priorización de frenado y cero arranque.

### Escenario F: Usuario dice solamente "mi carro falla"
- **Mensaje:** *"mi carro falla"*
- **Hechos Extraídos:** `ninguno` (información insuficiente).
- **Estado Operativo:** `DESCONOCIDO`.
- **Candidatos Evaluados:** `['CONDICION_OPERACION', 'TEMPERATURA_APARICION', 'CODIGO_DTC']`.
- **Filtros Aplicados:** Ninguno (estado desconocido legitima la discriminación inicial).
- **Pregunta Elegida:** *"Para orientar el diagnóstico: ¿la falla se presenta cuando el vehículo está detenido en ralentí, al acelerar con fuerza en carretera o únicamente al pisar el pedal de freno?"*
- **Resultado:** **Aprobado**. La pregunta general es válida únicamente ante estado desconocido.

### Escenario G: Usuario cambia de síntoma o caso
- **Flujo:** Turno 1 con no arranque (`ARRANQUE`) seguido de reinicio de caso (`iniciar_nuevo_caso()`) y nuevo síntoma al frenar.
- **Hechos Extraídos en Turno 2:** Memoria anterior limpia, nuevo hecho `condicion_operacion: al frenar`.
- **Estado Operativo:** Transiciona de `ARRANQUE` → `DESCONOCIDO` → `FRENADO`.
- **Resultado:** **Aprobado**. No hereda hechos ni estado operativo del vehículo previo.

### Escenario H: Información contradictoria
- **Mensaje:** *"el carro no arranca y cuando voy a 80 vibra"*
- **Hechos Extraídos:** `motor_arranca: NO`, `condicion_operacion: en carretera a velocidad`, `sintoma: vibración`, `conflicto_operativo: arranque_vs_marcha`.
- **Estado Operativo:** `ARRANQUE` (con bandera de conflicto activo).
- **Candidatos Evaluados:** `['ACLARACION_CONTRADICCION', 'COMPORTAMIENTO_ARRANQUE', 'CODIGO_DTC']`.
- **Filtros Aplicados:** Prioridad máxima a la resolución de inconsistencia operativa.
- **Pregunta Elegida:** *"Para orientar bien el diagnóstico: mencionas que el vehículo no arranca, pero también una condición en marcha. ¿La falla en marcha ocurrió antes como antecedente, o describes dos situaciones distintas?"*
- **Resultado:** **Aprobado**. No asume silenciosamente ni descarta hechos arbitrariamente.

---

## 5. RESULTADOS DE LA PRUEBA ANTI-LOOP MULTI-TURNO

Se evaluó la interacción multi-turno continua midiendo los 3 indicadores estipulados:

| Métrica Evaluada | Objetivo | Resultado Obtenido | Estado |
| :--- | :---: | :---: | :---: |
| **preguntas_incompatibles** | 0 | **0** | **CUMPLIDO** |
| **preguntas_repetidas_semanticamente** | 0 | **0** | **CUMPLIDO** |
| **hechos_confirmados_preguntados_nuevamente** | 0 | **0** | **CUMPLIDO** |

---

## 6. MATRIZ DE REGRESIÓN Y CALIDAD DEL CÓDIGO

### 6.1 Suite de Pruebas Ejecutada
1. **Fase 9.6 (`test_coherencia_operativa_fase9_6.py`):** 10 passed (100%).
2. **Fase 9.5 (`test_integridad_conversacional_fase9_5.py`):** 9 passed (100%).
3. **Flujo Interactivo (`test_flujo_descarte_interactivo.py`):** 10 passed (100%).
4. **Total de Pruebas Conversacionales Ejecutadas:** **29/29 PASSED** en 24.41s.

### 6.2 Límites de Tamaño y Arquitectura Limpia (AGENTS.md)
| Archivo | Líneas Finales | Límite Máximo | Estado |
| :--- | :---: | :---: | :---: |
| `src/core/conversacion/models.py` | 377 | 450 - 500 | **CUMPLIDO** |
| `src/core/conversacion/extractor_hechos.py` | 403 | 450 - 500 | **CUMPLIDO** |
| `src/core/conversacion/generador_preguntas.py` | 315 | 450 - 500 | **CUMPLIDO** |
| `src/core/conversacion/orquestador_conversacion.py` | 381 | 450 - 500 | **CUMPLIDO** |
| `src/core/conversacion/interprete_respuestas_cortas.py` | 214 | 450 - 500 | **CUMPLIDO** |
| `src/core/conversacion/guardia_contexto.py` | 95 | 450 - 500 | **CUMPLIDO** |

### 6.3 Linteo y Formato (Ruff)
- Comando: `ruff check src/core/conversacion tests/test_coherencia_operativa_fase9_6.py`
- Resultado: **All checks passed! (0 errores)**

---

## 7. VERIFICACIÓN DE INMUTABILIDAD CRIPTOGRÁFICA (FASE 8.3)

Ejecución del script oficial `machine_learning/training/fase8/calcular_hashes_congelamiento_8_3.py`:

| Componente Congelado | Hash SHA-256 Registrado | Verificación Actual | Estado |
| :--- | :--- | :--- | :---: |
| `dataset_train` | `c94d6e7b88ef72ea20f7be1bbb3d5a61484f33d992dcb52c6b285306f1c52626` | Coincidencia exacta | **INTACTO** |
| `benchmark_dev_60` | `113b5f190758346ab65200daae921b29251871fb842c95f6f2c288750e75592b` | Coincidencia exacta | **INTACTO** |
| `modelo_diagnostico_falla_prod` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | Coincidencia exacta | **INTACTO** |
| `modelo_sistema_prod` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | Coincidencia exacta | **INTACTO** |
| `vectorizador_tfidf_prod` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | Coincidencia exacta | **INTACTO** |
| `modelo_diagnostico_candidata` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | Coincidencia exacta | **INTACTO** |
| `modelo_sistema_candidata` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | Coincidencia exacta | **INTACTO** |
| `vectorizador_tfidf_candidata` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | Coincidencia exacta | **INTACTO** |
| `corpus_metadatos_rag` | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | Coincidencia exacta | **INTACTO** |
| `indice_faiss` | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | Coincidencia exacta | **INTACTO** |
| `adaptador_modelo_ml` | `014d3e6f6f9f5c5bc5e6223e748566ce6a1ecdb70842df7afc7037c51b6a5eb4` | Coincidencia exacta | **INTACTO** |
| `motor_rag` | `eaa316a87ecaa1be9b6702d9807d44ae6cb8a87bc4ce7154c83d6fc09c1c5a3c` | Coincidencia exacta | **INTACTO** |
| `rag_relevance_filter` | `fa3d6aef13639bc38bfe5a1360e13276912c97bababdf94954fc53ee7e2c49cc` | Coincidencia exacta | **INTACTO** |
| `auto_interrogador` | `2e746e498facea34009641c239edf09fbaca1eaaa6771477e666ac2b213be9c2` | Coincidencia exacta | **INTACTO** |
| `politica_fusion` | `073b97fe07c8891807ac63a23994c42dabb17f71062f7af1469a8627d7789c83` | Coincidencia exacta | **INTACTO** |
| `prompt_builder` | `e0b26f32f278bb108126a31242f4eacd100308e517b99095fbc0c422090c33d2` | Coincidencia exacta | **INTACTO** |
| `text_processor` | `f7075605f6a0e32512cfe24cb5cc4ffb01cf72cc1ca1dd1cba3cbadf77d3216e` | Coincidencia exacta | **INTACTO** |
| `taxonomia_sistemas` | `561e95c952effcd002850e484830e0515a2469c152fc7af9933b17e0483f716d` | Coincidencia exacta | **INTACTO** |
| `gestor_diagnostico` | `66bead052676331496a0e737ebe0ab1e6927027e6e19c73c32a43fbe57752330` | Coincidencia exacta | **INTACTO** |

**Conclusión de Inmutabilidad:** 19/19 componentes congelados verificados con 100% de integridad criptográfica.

---

## 8. CONCLUSIÓN Y CIERRE DE FASE 9.6

La **Fase 9.6** queda completada y validada en su totalidad:
1. El incidente real de WhatsApp quedó completamente erradicado y reproducido bajo test automatizado.
2. `ConversationState` ahora gobierna la coherencia operacional mediante `EstadoOperativo`.
3. Ninguna pregunta incompatible con el estado del vehículo puede ser emitida por CarBot.
4. El clasificador Linear SVM con TF-IDF y el motor RAG/FAISS se preservaron 100% inmutables.
5. El sistema cumple estrictamente con los límites de líneas, separación de capas y principios de Clean Architecture.

**Fin de Fase 9.6. No se inicia Fase 10.**
