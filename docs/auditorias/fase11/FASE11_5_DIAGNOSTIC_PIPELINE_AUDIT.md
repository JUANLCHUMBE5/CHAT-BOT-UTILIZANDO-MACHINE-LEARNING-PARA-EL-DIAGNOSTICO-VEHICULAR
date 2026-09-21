# FASE 11.5 — AUDITORÍA INTEGRAL DEL PIPELINE DIAGNÓSTICO
## Auditoría E2E: Conversación → Estado → Query → C1 → RAG → Respuesta

**Proyecto:** CarBot — Chatbot con Machine Learning para Diagnóstico Vehicular  
**Fecha:** 2026-09-19  
**Estado:** AUDITORÍA Y REMEDIACIÓN COMPLETADA  
**Modelos ML & RAG:** C1 Freeze (`060d...`, `2474...`, `dec3...`) | RAG Freeze Candidate V1 (`a2a0...`, `8b42...`)  

---

## 1. Resumen Ejecutivo del Pipeline Diagnóstico

Durante la Fase 11.4 y 11.4.1 se identificaron dos comportamientos anómalos en casos reales:
1. **Caso B (Vibración al Frenar):** Tras 3 turnos conversacionales coherentes donde el usuario confirmó que la vibración ocurría *únicamente al frenar* a velocidad media/alta y *en el volante*, el sistema colapsaba devolviendo:
   `"Posibles causas: 1. Consulta Ambigua / Datos Faltantes — 0%"`
2. **Caso A (Demora de Arranque en Frío):** El sistema respondía con hipótesis dispersas (IAC 45%, Termostato 36%, Common Rail 19%) y sugería inmediatamente una reparación/limpieza agresiva de cuerpo de aceleración antes de indicar comprobaciones físicas o metrológicas básicas.

La presente auditoría ejecutó una trazabilidad completa capa por capa para aislar la causa raíz exacta de cada síntoma, respetando la regla inviolable de **congelamiento absoluto de C1 y RAG**.

---

## 2. Trace Completo: Caso Real B — Vibración al Frenar

### 2.1 Variables del Pipeline E2E (Trace Oficial)

| Variable del Pipeline | Valor Auditado (Turno 1) | Valor Auditado (Turno 2) | Valor Auditado Final (Turno 3) |
|---|---|---|---|
| **RAW_MESSAGES** | "El cliente indica que cuando frena el carro el volante comienza a vibrar, sobre todo cuando va a una velocidad media o alta. Cuando maneja sin frenar no siente esa vibración. Todavía no he revisado el vehículo. ¿Qué debería revisar primero?" | "Únicamente vibra cuando piso el pedal de freno. Si voy a la misma velocidad sin frenar, el volante no vibra." | "Se siente principalmente en el volante. En el pedal casi no siento vibración y el resto del vehículo tampoco vibra de forma notable." |
| **SESSION_ID** | `sess-frenos-fase11-5-audit` | `sess-frenos-fase11-5-audit` | `sess-frenos-fase11-5-audit` |
| **CASE_ID** | `CASO-FRENOS-001` | `CASO-FRENOS-001` | `CASO-FRENOS-001` |
| **ACTIVE_PROBLEM** | Vibración en frenada | Vibración en frenada | Discos de freno alabeados / Vibración al frenar |
| **ACTIVE_SYSTEM** | `FRENOS` | `FRENOS` | `FRENOS` |
| **EXTRACTED_FACTS** | `[sintoma: vibracion, gatillo: frenar, condicion: velocidad media/alta, sin_frenar: no_vibra, componente_sin_inspeccionar: vehiculo]` | `[gatillo_confirmado: solo_al_frenar, sin_frenar_volante_no_vibra]` | `[ubicacion_principal: volante, pedal: no_vibra, resto_vehiculo: no_vibra]` |
| **NEGATED_FACTS** | `[vibra_sin_frenar: False]` | `[vibra_sin_frenar: False]` | `[vibra_pedal: False, vibra_chasis: False]` |
| **UNKNOWN_FACTS** | `[ubicacion_exacta_vibracion, estado_discos_pastillas]` | `[ubicacion_exacta_vibracion]` | `[alabeo_medido_reloj_comparador]` |
| **OPERATING_CONDITIONS** | `velocidad: media/alta, accion: frenado` | `velocidad: media/alta, accion: frenado` | `velocidad: media/alta, accion: frenado` |
| **COMPLETED_QUESTIONS** | `[]` | `[regimen_marcha_vs_frenado]` | `[regimen_marcha_vs_frenado, ubicacion_vibracion]` |
| **PENDING_QUESTION** | "¿Al frenar, la vibración se siente en volante, pedal o chasis?" | "¿Al frenar, la vibración se siente en volante, pedal o carrocería?" | `None` (Evidencia suficiente alcanzada) |
| **SUFFICIENCY_RESULT** | `False` (Requiere precisión de ubicación) | `False` (Pendiente confirmación pedal vs volante) | `True` (`es_suficiente = True`, score >= 0.70) |
| **SYNTHESIZED_QUERY** | "vibracion volante al frenar velocidad media alta" | "vibracion solo al frenar velocidad media alta sin frenar no vibra" | "sintoma: vibracion en volante solo al frenar a velocidad media o alta sin frenar no vibra en volante no vibra en pedal no revisado" |
| **C1_MACRO** | `FRENOS` | `FRENOS` | `FRENOS` (100% de probabilidad en clasificador Nivel 1) |
| **C1_TOP10** | 1. Discos de freno alabeados (98.5%)<br>2. Llantas desbalanceadas (0.9%)<br>3. Freno regenerativo (0.3%) | 1. Discos de freno alabeados (97.6%)<br>2. Llantas desbalanceadas (2.1%)<br>3. Booster/vacío (0.1%) | 1. Discos de freno alabeados o desgastados (94.9%)<br>2. Llantas desbalanceadas o desalineadas (4.9%)<br>3. Pastillas y zapatas (0.1%) |
| **C1_CONFIDENCES** | Top 1: 0.985 | Top 1: 0.976 | Top 1: 0.949 |
| **HIERARCHICAL_RERANKING** | Filtro Macro `FRENOS` activo | Filtro Macro `FRENOS` activo | Filtro Macro `FRENOS` activo |
| **RAG_QUERY** | "alabeo de discos de freno tolerancia dial gauge vibracion volante frenar" | "alabeo de discos de freno tolerancia dial gauge vibracion volante frenar" | "alabeo de discos de freno variacion de espesor dtv tolerancia alabeo reloj comparador micrometro" |
| **RAG_TOP5** | 1. Manual OEM Frenos — Alabeo y DTV en discos (Score: 0.89)<br>2. Procedimiento de medición con reloj comparador (Score: 0.86)<br>3. Tolerancia máxima de alabeo lateral 0.05 mm (Score: 0.84)<br>4. Procedimiento rectificado y par de apriete pernos (Score: 0.79)<br>5. Guía de desgaste de pastillas y mordazas (Score: 0.75) | Ídem | Ídem |
| **DTC_ENRICHMENT** | Ninguno (Avería puramente mecánica/metrológica) | Ninguno | Ninguno (Sin DTC electrónico en alabeo) |
| **RESPONSE_HYPOTHESES** | Orientación conversacional preliminar | Orientación conversacional preliminar | 1. Discos de freno alabeados o con variación de espesor (DTV) — 95%<br>2. Llantas desbalanceadas o desalineadas — 5% |
| **QUESTION_SELECTED** | "¿la vibración se siente en el volante, en el pedal o en todo el vehículo?" | `None` (Se emite diagnóstico) | `None` |
| **FINAL_RESPONSE** | Solicitud de confirmación de volante vs pedal | Solicitud de confirmación | Diagnóstico estructurado recomendando comprobación física con reloj comparador y micrómetro. |

---

### 2.2 Diagnóstico de Causas Raíz en Caso B

La investigación técnica demostró que el error **no** estaba en el modelo ML C1 (el cual predice Discos Alabeados con 94.9% - 98.5% en todas las variantes de texto limpio), sino en una concatenación de 4 bugs de integración en las capas intermedias:

1. **`detector_polaridad.py` (Capa Extracción):**
   - *Comportamiento erróneo:* Evaluaba la presencia de cláusulas condicionales como `"sin frenar no siente esa vibración"`. El parser determinaba erróneamente que la frase completa estaba negada (`es_condicion_negada = True`), anulando el hecho afirmativo principal `"cuando frena el volante comienza a vibrar"`.
   - *Corrección:* Se introdujo separación estricta de cláusulas subordinadas (`sin frenar`, `al no frenar`, `fuera de frenada`) para no contaminar la polaridad de la acción desencadenante.
2. **`semantic_purifier.py` (Capa Purificación ML):**
   - *Comportamiento erróneo:* Detectaba el substring `"sin frenar"` mediante regex estricto y eliminaba todas las raíces `fren*` del texto, inyectando erróneamente términos de suspensión (`"llantas desbalanceadas"`).
   - *Corrección:* El purificador ahora respeta el contexto afirmativo de frenada. Solo purga si no existe una condición de activación por pedal de freno.
3. **`sintetizador_consulta.py` (Capa Síntesis de Consulta):**
   - *Comportamiento erróneo:* El sintetizador colapsaba las entidades clínicas del `ConversationState`, perdiendo la velocidad (media/alta) y la localización (`volante`), generando un texto de solo 19 caracteres.
   - *Corrección:* Reescritura integral del sintetizador para consolidar síntoma, gatillo, velocidad, ubicación y pruebas pendientes en una consulta clínica estructurada.
4. **`text_processor.py` (Capa Orquestación / Diagnóstico):**
   - *Comportamiento erróneo:* Cuando la consulta sintetizada tenía menos de 25 caracteres, la función `es_consulta_ambigua()` la interceptaba y retornaba inmediatamente un resultado mock: `"Consulta Ambigua / Datos Faltantes — 0%"`.
   - *Corrección:* Las consultas generadas por el orquestador conversacional (`orquestado=True` o `diagnostico_forzado=True`) tienen inmunidad ante `es_consulta_ambigua()`, obligando al clasificador C1 a emitir sus probabilidades reales.

---

## 3. Trace Completo: Caso Real A — Demora de Arranque en Frío

### 3.1 Variables del Pipeline E2E (Trace Oficial)

| Variable del Pipeline | Valor Auditado |
|---|---|
| **RAW_MESSAGES** | "Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas. Una vez que logra encender, el motor funciona normal y no se prende ninguna luz de advertencia. Todavía no he revisado batería, arranque ni sistema de combustible. ¿Qué debería revisar primero?" |
| **SESSION_ID** | `sess-arranque-fase11-5-audit` |
| **CASE_ID** | `CASO-ARRANQUE-001` |
| **ACTIVE_PROBLEM** | Demora en arranque en frío |
| **ACTIVE_SYSTEM** | `MOTOR` / `ELECTRICO` |
| **EXTRACTED_FACTS** | `[sintoma: demora en encender, condicion_temporal: por las mananas / frio, post_arranque: motor funciona normal, tablero: sin luz advertencia, pendiente_inspeccion: bateria, arranque, combustible]` |
| **NEGATED_FACTS** | `[luz_advertencia_encendida: False, falla_en_marcha: False]` |
| **UNKNOWN_FACTS** | `[velocidad_giro_arrancador, voltaje_bateria_en_reposo_y_cranking, presion_riel_combustible]` |
| **OPERATING_CONDITIONS** | `condicion: motor frio / arranque matutino` |
| **COMPLETED_QUESTIONS** | `[]` |
| **PENDING_QUESTION** | "Al dar arranque por la mañana, ¿el motor de arranque gira con buena velocidad o se escucha lento y pesado?" |
| **SUFFICIENCY_RESULT** | `False` (Requiere distinguir velocidad de cranking vs caída de presión de combustible) |
| **SYNTHESIZED_QUERY** | "demora bastante en encender por las mananas una vez que logra encender motor funciona normal no revisado bateria arranque combustible" |
| **C1_MACRO** | `MOTOR` (85%) / `ELECTRICO` (15%) |
| **C1_TOP10** | 1. Fuga o baja presión en sistema Common Rail Diesel (84.7%)<br>2. Batería descargada o bornes sulfatados (10.4%)<br>3. Falla de descarbonización e inyección directa GDI (2.0%)<br>4. Bomba de gasolina quemada o baja presión (1.7%)<br>5. Inyectores sucios o filtro de combustible obstruido (0.6%)<br>6. Falla en motor de arranque o solenoide (0.3%) |
| **C1_CONFIDENCES** | Top 1: 0.847, Top 2: 0.104, Top 3: 0.020 |
| **HIERARCHICAL_RERANKING** | Filtros Macro `MOTOR` / `ELECTRICO` activos |
| **RAG_QUERY** | "diagnostico demora arranque en frio caida de tension cranking presion de combustible" |
| **RAG_TOP5** | 1. Manual de Servicio: Prueba de caída de tensión en batería durante arranque (Score: 0.91)<br>2. Circuito de alimentación de combustible: Retención de presión de línea y válvula check (Score: 0.88)<br>3. Diagnóstico de motor de arranque y consumo de corriente (Score: 0.84)<br>4. Procedimiento de medición de presión residual con manómetro (Score: 0.81)<br>5. Inspección de bujías incandescentes y precalentamiento (Score: 0.77) |
| **DTC_ENRICHMENT** | Ninguno (Sin luz de advertencia / sin códigos almacenados) |
| **RESPONSE_HYPOTHESES** | 1. Pérdida de presión residual en línea de combustible / Common Rail (85%)<br>2. Batería con baja capacidad de arranque en frío o bornes sulfatados (10%)<br>3. Descarbonización / Válvula check de combustible (2%) |
| **QUESTION_SELECTED** | "¿El motor de arranque gira rápido o se siente pesado al intentar encender?" |
| **FINAL_RESPONSE** | Orientación técnica priorizando comprobación metrológica (prueba de caída de tensión de batería > 9.6V durante cranking y medición de presión residual de combustible con manómetro) antes de cualquier desmontaje. |

---

### 3.2 Diagnóstico de Causas Raíz en Caso A

1. **Aparición anómala de IAC y Termostato en respuesta anterior:**
   - En la Fase 11.4.1, la ausencia de hechos estructurados de "arranque en frío" en la síntesis permitía que el clasificador de intención o el vectorizador TF-IDF asociara `"por las mañanas"` con enriquecimientos espurios de temperatura de motor (termostato y válvula IAC).
   - *Corrección:* El extractor ahora captura explícitamente `demora_arranque_frio`, `cranking` y las piezas pendientes de inspección (`bateria`, `arranque`, `combustible`), orientando la síntesis hacia el sistema de encendido y alimentación.
2. **Comportamiento intrínseco de C1 (Linear SVM congelado):**
   - La evaluación directa del clasificador congelado demuestra que frases como `"demora en encender por las mañanas"` activan con 84.7% la clase `Common Rail Diesel` y con 10.4% `Batería descargada`.
   - **Conclusión de Arquitectura:** C1 tiene un sesgo textual inherente hacia Common Rail en expresiones matutinas debido a la distribución del dataset de entrenamiento. Siguiendo estrictamente las directrices del proyecto (**NO TOCAR C1 EN FASE 11.5**), este sesgo se documenta formalmente y se neutraliza en la respuesta diagnóstica exigiendo comprobaciones físicas previas.
3. **Violación de la Regla "Hipótesis → Comprobación → Resultado" (Corregida):**
   - La directriz `COMBUSTIBLE_003` en `directrices_mecanicas.py` sugería directamente: *"limpieza de carbonilla en garganta y mariposa de aceleración..."*.
   - *Corrección:* Se modificó la directriz para obligar a una comprobación física preliminar: *"inspección visual de carbonilla en mariposa de aceleración y verificación del porcentaje de apertura con escáner en línea de datos antes de desmontar o limpiar"*.

---

## 4. Comparación de Predicciones C1 sobre Variantes de Texto

| Caso / Variante de Entrada | Top 1 Predicción (C1) | Top 2 Predicción (C1) | Top 3 Predicción (C1) | Macro Dominante |
|---|---|---|---|---|
| **Caso A — Mensaje Inicial Limpio** | Common Rail Diesel (79.6%) | Batería HV Híbridos (6.9%) | Batería 12V descargada (5.6%) | `MOTOR` (85.7%) |
| **Caso A — Concatenación Limpia** | Common Rail Diesel (86.7%) | Batería 12V descargada (9.5%) | Descarbonización GDI (2.0%) | `MOTOR` (89.3%) |
| **Caso A — Synthesized Query Backend** | Common Rail Diesel (84.7%) | Batería 12V descargada (10.4%)| Descarbonización GDI (2.0%) | `MOTOR` (88.4%) |
| **Caso B — Mensaje Inicial Limpio** | Discos de freno alabeados (98.5%)| Llantas desbalanceadas (0.9%) | Freno regenerativo (0.3%) | `FRENOS` (98.9%) |
| **Caso B — Concatenación Limpia** | Discos de freno alabeados (97.6%)| Llantas desbalanceadas (2.1%) | Booster de freno (0.1%) | `FRENOS` (97.8%) |
| **Caso B — Synthesized Query Backend** | Discos de freno alabeados (94.9%)| Llantas desbalanceadas (4.9%) | Pastillas de freno (0.1%) | `FRENOS` (95.0%) |

---

## 5. Validación de Integridad de Artefactos Congelados

Se corroboró mediante SHA-256 que ningún binario fue modificado:

```
[OK] vectorizador_c1.pkl:            060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7
[OK] modelo_diagnostico_c1.pkl:      24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c
[OK] modelo_sistema_c1_macrofix.pkl: dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c
[OK] indice_faiss_v1.index:          a2a081ffded23d4d727b57780aec26da9167e90f044101e77adbb33cbaa79b40
[OK] metadatos_manuales_v1.json:     8b4244713cfdc2f59af66b4e43bea8532196366ee5b53a98721e96ca6c781dbb
```
