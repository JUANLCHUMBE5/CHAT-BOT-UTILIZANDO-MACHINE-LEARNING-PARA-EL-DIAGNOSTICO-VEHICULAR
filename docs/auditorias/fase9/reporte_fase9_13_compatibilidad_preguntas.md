# Fase 9.13 — Auditoría de Compatibilidad de Preguntas y Aislamiento de Estado

**Fecha local:** 16 de septiembre de 2026  
**Alcance:** Incidente físico real en WhatsApp, auditoría forense de primera divergencia, aislamiento estricto de estado conversacional al cambiar de caso, compatibilidad semántica de preguntas por dominio técnico y regresión completa.  
**Restricción metodológica obligatoria:** No se modificaron ni reentrenaron ML, TRAIN, TF-IDF, calibración, RAG, FAISS ni los benchmarks congelados. No se inició la Fase 10.

---

## 1. Conclusión Ejecutiva

La segmentación introducida en Fase 9.12 funcionó según diseño: al ingresar la queja de transmisión, el caso previo de motor (`case_id A: 2521e354...`) fue cerrado y se abrió un caso nuevo de transmisión (`case_id B: d8dad4f9...`) con decisión `CAMBIO_DE_CASO`.

La **primera divergencia** no se debió a una respuesta copiada ni a una consulta ML/RAG errónea, sino a la arquitectura de `GeneradorPreguntas`:
1. El sistema determinó que requería interrogar antes de ejecutar inferencia ML (`requiere_interrogacion = True`).
2. Las preguntas de tipo `TEMPERATURA_APARICION` estaban registradas como candidatas universales.
3. El selector evaluaba directamente la ganancia de información (`information_gain` / score de prioridad base: 50 para motor, 45 para arranque, frente a 40 para DTC) **sin someter la pregunta a una compuerta previa de compatibilidad semántica de dominio**.
4. Como resultado, ganó la pregunta térmica de motor (score 50) a pesar de que el dominio detectado era `TRANSMISION`.

Adicionalmente, se detectó una brecha de aislamiento: aunque el nuevo caso reseteaba hechos y preguntas, conservaba el `historial_mensajes_usuario` y la `falla_principal` del caso anterior. Ambas brechas quedaron corregidas y blindadas mediante regresiones.

---

## 2. Traza Física Obligatoria del Incidente Real

| Parámetro Requerido | Valor Real Auditado |
|---|---|
| **`meta_message_id`** | `wamid.HBgLNTE5NTUwOTUxNDcVAgASGBYzRUIwMTdDRTBGRURFRTJBNjlCQ0YzAA==` |
| **`conversation_id`** | `f7a37e2d-efe8-4c26-9b62-9f4103e7b094` |
| **Fecha / Hora de Recepción** | `2026-09-17 04:27:54.658212+00:00` |
| **`case_id anterior → case_id actual`** | `2521e354-0adc-44d1-9345-ecf7c404c6c5` → `d8dad4f9-8ddb-443d-ace5-bacbf56b1f84` |
| **`SegmentadorCasos.decision`** | `CAMBIO_DE_CASO` |
| **Motivo de Transición** | `NUEVA_QUEJA_PRINCIPAL: MARCHA_MOTOR_A_TRANSMISION` |
| **Dominio anterior** | `MARCHA_MOTOR` |
| **Dominio detectado actual** | `TRANSMISION` |
| **Estado operativo** | `MARCHA` (en transición inicial) / `DESCONOCIDO` (en extractor de hechos) |
| **Hechos mensaje actual** | • `condicion_operacion`: "al seleccionar reversa"<br>• `sintoma_demora_acople_reversa`: "reversa demora en enganchar"<br>• `sintoma_golpe_acople_reversa`: "reversa entra con golpe"<br>• `sintoma_ruido_anómalo`: "ruido anómalo" |
| **Hechos caso activo** | Los 4 hechos extraídos del mensaje actual (los hechos del caso A fueron archivados en `hechos_historicos`) |
| **Consulta sintetizada** | `"a Gasolina. presenta reversa demora en enganchar, reversa entra con golpe, ruido anómalo. cuando está al seleccionar reversa."` |
| **Macro ML RAW** | `null` (no ejecutado; el flujo derivó a interrogar antes de inferencia) |
| **Top3 ML** | `null` (vacío en este turno) |
| **`requiere_interrogacion`** | `True` |
| **Preguntas candidatas antes de filtros** | 1. Térmica Motor (`TEMPERATURA_APARICION`, prio 50)<br>2. Térmica Arranque (`TEMPERATURA_APARICION`, prio 45)<br>3. Escáner / DTC (`CODIGO_DTC`, prio 40) |
| **`QuestionIntent` de candidatas** | `TEMPERATURA_APARICION`, `TEMPERATURA_APARICION`, `CODIGO_DTC` |
| **Score / `information_gain`** | 50, 45, 40 |
| **Preguntas eliminadas y motivo (9.12)** | Ninguna eliminada (no existía validación de dominio previa al score) |
| **Pregunta finalmente seleccionada (9.12)** | *"¿El problema aparece con el motor en frío (...) o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?"* |
| **Preguntas y estado heredados del caso anterior** | `preguntas_realizadas`: `[]`, `top3_actual`: `[]`, `hechos`: `[]` (reseteados).<br>*(Anomalía detectada: `historial_mensajes_usuario` y `falla_principal` no se vaciaban)* |
| **Respuesta WhatsApp física enviada** | *"¿El problema aparece con el motor en frío (primeros minutos tras arrancar) o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?"* |

### Mensaje RAW del Usuario
> *"Hola, tengo un problema con mi carro automático. Cuando pongo la palanca en D entra normal, pero cuando paso a R demora unos segundos en enganchar. A veces tengo que acelerar un poquito para que recién entre la reversa y cuando entra da un golpe. Hacia adelante los cambios se sienten normales. No aparece ninguna luz de advertencia en el tablero y todavía no he revisado nada."*

---

## 3. Punto Crítico: Demostración de Aislamiento de Estado

Se verificó el comportamiento de la transición `MOTOR case_id A → TRANSMISION case_id B`:

| Estructura Conversacional | Estado en 9.12 (Auditoría) | Estado en 9.13 (Corregido y Validado) |
|---|---|---|
| `case_id` | Cambió correctamente (A → B) | Cambió correctamente (A → B) |
| `preguntas_realizadas` | `[]` (Aislado) | `[]` (Aislado y verificado) |
| `pregunta_actual` | `None` (Aislado) | `None` (Aislado y verificado) |
| `question_intent` | `None` (Aislado) | `None` (Aislado y verificado) |
| `estado_interrogador` | `INTERROGAR` | `INTERROGAR` |
| `respuestas_obtenidas` | `[]` (Aislado) | `[]` (Aislado y verificado) |
| `herramientas_no_disponibles` | `[]` (Aislado) | `[]` (Aislado y verificado) |
| `pruebas_no_disponibles` | `[]` (Aislado) | `[]` (Aislado y verificado) |
| `hechos` activos | Solo hechos nuevos (Aislado) | Solo hechos nuevos (Aislado) |
| `historial_mensajes_usuario` | **Heredado de A** (Brecha) | **`[]` Limpio en B; archivado en histórico** |
| `falla_principal` | **Heredado de A** (Brecha) | **`None` Limpio en B; archivado en histórico** |
| `hechos_historicos` | Guardaba snapshot parcial | Guarda snapshot íntegro de caso A |

La función `SegmentadorCasos.archivar_y_limpiar_caso()` ahora garantiza el aislamiento total de todas las estructuras específicas del caso previo, impidiendo cualquier forma de contaminación cruzada.

---

## 4. Compatibilidad Semántica de Preguntas por Dominio

### Diagnóstico de la Causa Raíz
En Fase 9.12, `GeneradorPreguntas` agregaba las preguntas de `TEMPERATURA_APARICION` con prioridad fija (`prio_marcha = 50`, `prio_arr = 45`) y las ordenaba directamente por score frente al escáner OBD-II (`prio = 40`). Dado que 50 > 40, la pregunta de temperatura de motor ganaba en cualquier dominio que no tuviera una pregunta con score superior a 50.

### Principio de Solución (Sin Reglas Ad-hoc)
**Regla Prohibida Evitada:** No se creó ninguna condición ad-hoc del tipo `if "reversa" in texto: prohibir_temperatura()`.

**Diseño Generalizado:** Se implementó el módulo [`CompatibilidadPreguntas`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/src/core/conversacion/compatibilidad_preguntas.py) con una política semántica multidimensional:

$$\text{Elegibilidad} = f(\text{Pregunta}, \text{Dominio Actual}, \text{Estado Operativo}, \text{Hechos Conocidos}, \text{Diferencial Top-3})$$

1. **Compuerta de Aplicabilidad Previa al Score:**  
   El cálculo y ordenamiento por ganancia de información (`information_gain` / score) solo se evalúa sobre las candidatas que superan la compuerta de aplicabilidad semántica.
2. **Asignación de Dominio a Preguntas:**  
   Cada pregunta candidata tiene un dominio lógico asociado (`MARCHA_MOTOR`, `TRANSMISION`, `FRENOS`, `SUSPENSION`, `CLIMATIZACION`, `ARRANQUE`, `ELECTRICO`, `GENERAL`).
3. **Preguntas Cruzadas Justificadas:**  
   Una pregunta asociada primariamente a otro dominio solo es elegible si el diferencial técnico o las hipótesis vigentes la justifican:
   - En **Transmisión**, una pregunta térmica solo es elegible si el diferencial activo incluye hipótesis térmicas o reológicas (ej. degradación de ATF, viscosidad, solenoides trabados en caliente).
   - En **Arranque**, una pregunta sobre temperatura de motor solo se admite si existen antecedentes confirmados de funcionamiento previo en marcha.
   - Dominios como **Frenos**, **Suspensión** y **Climatización** descartan preguntas térmicas o de carretera de motor salvo justificación causal explícita.

---

## 5. Regresión de Casos y Validación de Aislamiento

Se diseñaron e incorporaron pruebas formales en [`test_compatibilidad_preguntas_fase9_13.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/tests/test_compatibilidad_preguntas_fase9_13.py):

| Caso de Prueba | Entrada / Condición | Comportamiento Esperado | Resultado |
|---|---|---|---|
| **Transmisión (Incidente Real)** | Demora y golpe al pasar a R, D normal | Descarta térmica de motor antes de score; selecciona inspección de ATF / fugas en caja | **PASÓ** |
| **Frenos** | Vibración en volante al frenar | No pregunta temperatura de trabajo ni condición en carretera; indaga ubicación de la vibración | **PASÓ** |
| **Arranque** | Solo hace clic al girar la llave | No pregunta comportamiento en carretera ni frenos; indaga comportamiento eléctrico / giro | **PASÓ** |
| **Climatización** | A/C no enfría, compresor no acopla | No pregunta frenado ni temperatura de motor; indaga acople de compresor / ventilador | **PASÓ** |
| **Motor con falla térmica** | Tironea y pierde fuerza al acelerar | **SÍ** permite y selecciona pregunta de temperatura frío vs. caliente (intent `TEMPERATURA_APARICION`) | **PASÓ** |
| **Transmisión térmica con hipótesis activa** | Falla en caja con hipótesis de degradación de ATF | **SÍ** permite pregunta térmica específica de transmisión (*"¿cambia cuando la transmisión está fría...?"*) | **PASÓ** |
| **Modificador ambiental vs. avería nueva** | *"Se nota más con el aire acondicionado encendido"* | Se clasifica como modificador de carga, **no** abre caso nuevo de climatización | **PASÓ** |
| **Arranque + Eléctrico coexistente** | Medición de 12.6 V en bornes | Coexiste en el mismo caso de arranque, no genera sobresegmentación | **PASÓ** |
| **Aislamiento Total Caso A → B** | Transición con historial y herramientas bloqueadas | Limpieza total de preguntas, respuestas, historial activo, hechos y herramientas | **PASÓ** |

---

## 6. Validación con el Mensaje Exacto del Incidente

Al reproducir el mensaje exacto con el runtime de Fase 9.13:

```json
{
  "dominio": "TRANSMISION",
  "hechos": {
    "condicion_operacion": "al seleccionar reversa",
    "sintoma_demora_acople_reversa": "reversa demora en enganchar",
    "sintoma_golpe_acople_reversa": "reversa entra con golpe",
    "sintoma_ruido_anómalo": "ruido anómalo"
  },
  "pregunta_seleccionada": "¿Has revisado el nivel y estado del aceite ATF de la transmisión, o si existen fugas visibles debajo de la caja?",
  "intent": "COMPONENTE_REVISADO",
  "descartadas": [
    {
      "intent": "TEMPERATURA_APARICION",
      "pregunta": "¿El problema aparece con el motor en frío (...) o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?",
      "score_information_gain": 50,
      "dominio_pregunta": "MARCHA_MOTOR",
      "motivo": "INCOMPATIBLE_DOMINIO"
    },
    {
      "intent": "TEMPERATURA_APARICION",
      "pregunta": "¿La dificultad para arrancar ocurrió con el motor totalmente frío (...) o intentaste encenderlo poco después de haber apagado el motor?",
      "score_information_gain": 45,
      "dominio_pregunta": "ARRANQUE",
      "motivo": "INCOMPATIBLE_DOMINIO"
    }
  ]
}
```

**Criterios de Éxito Cumplidos:**
1. Dominio y contexto: `TRANSMISION`.
2. Cero evidencia o estado heredado de `MARCHA_MOTOR`.
3. Pregunta clínicamente aplicable al diferencial de transmisión (ATF / fugas).
4. Sin bucles, sin dobles preguntas y sin contaminación entre casos.

---

## 7. Verificación de Integridad de Artefactos (19/19 Hashes Inmutables)

Se ejecutó la verificación estricta contra el manifiesto canónico `machine_learning/models/reporte_fase8_3_congelado.json`:

| ID | Artefacto Canónico | SHA-256 Registrado (Prefijo) | Estado Verificación |
|---|---|---|---|
| 1 | `machine_learning/data/dataset_sintomas_limpio.csv` | `c94d6e7b88ef72ea...` | **COINCIDENTE** |
| 2 | `machine_learning/data/benchmark_dev_60_casos.py` | `113b5f190758346a...` | **COINCIDENTE** |
| 3 | `machine_learning/models/modelo_diagnostico.pkl` | `3d8199595b69bb01...` | **COINCIDENTE** |
| 4 | `machine_learning/models/modelo_sistema.pkl` | `22d11492e9576664...` | **COINCIDENTE** |
| 5 | `machine_learning/models/vectorizador_tfidf.pkl` | `8b8e8c3b3571fe96...` | **COINCIDENTE** |
| 6 | `machine_learning/models/fase8_candidata/modelo_diagnostico.pkl` | `3d8199595b69bb01...` | **COINCIDENTE** |
| 7 | `machine_learning/models/fase8_candidata/modelo_sistema.pkl` | `22d11492e9576664...` | **COINCIDENTE** |
| 8 | `machine_learning/models/fase8_candidata/vectorizador_tfidf.pkl` | `8b8e8c3b3571fe96...` | **COINCIDENTE** |
| 9 | `machine_learning/manuals/metadatos_manuales.json` | `2f0684477522efb6...` | **COINCIDENTE** |
| 10 | `machine_learning/manuals/indice_faiss.index` | `757c4b006a8995f4...` | **COINCIDENTE** |
| 11 | `backend/src/infrastructure/modelo_ml.py` | `014d3e6f6f9f5c5b...` | **COINCIDENTE** |
| 12 | `backend/src/infrastructure/motor_rag.py` | `eaa316a87ecaa1be...` | **COINCIDENTE** |
| 13 | `backend/src/infrastructure/rag/relevance_filter.py` | `fa3d6aef13639bc3...` | **COINCIDENTE** |
| 14 | `backend/src/core/diagnostico/auto_interrogador.py` | `2e746e498facea34...` | **COINCIDENTE** |
| 15 | `backend/src/core/diagnostico/politica_fusion.py` | `073b97fe07c88918...` | **COINCIDENTE** |
| 16 | `backend/src/core/diagnostico/prompt_builder.py` | `e0b26f32f278bb10...` | **COINCIDENTE** |
| 17 | `backend/src/core/diagnostico/text_processor.py` | `f7075605f6a0e325...` | **COINCIDENTE** |
| 18 | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `561e95c952effcd0...` | **COINCIDENTE** |
| 19 | `backend/src/core/gestor_diagnostico.py` | `66bead0526763314...` | **COINCIDENTE** |

**Resultado global:** **19/19 HASHES INTACTOS — 0 DIVERGENCIAS.**

---

## 8. Runtime y Versionado

- **Versión del Incidente:** `APP_VERSION = 9.12.0`, `ORCHESTRATOR_VERSION = 9.12.0`, `CODE_BUILD_ID = dfc3c025481865db`.
- **Versión Oficial Fase 9.13:** `APP_VERSION = 9.13.0`, `ORCHESTRATOR_VERSION = 9.13.0`, `CODE_BUILD_ID = 31bd5de92f4d26ec`.
- **Suite Pytest Fase 9:** **110 passed**, 0 failed en 21.84s.
- **Linter Ruff:** **All checks passed!**

---

## 9. Cierre y Detención de Fase

Conforme a las directivas metodológicas y al mandato estricto de la solicitud:
- La causa raíz quedó demostrada y corregida en la capa conversacional.
- Los 19 artefactos congelados permanecen inmutables.
- **Se finaliza formalmente la Fase 9.13.**
- **DETENIDO: NO SE INICIA LA FASE 10.**
