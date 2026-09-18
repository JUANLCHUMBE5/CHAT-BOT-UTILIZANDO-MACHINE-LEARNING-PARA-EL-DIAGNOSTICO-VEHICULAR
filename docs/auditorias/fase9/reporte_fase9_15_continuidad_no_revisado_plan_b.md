# REPORTE FASE 9.15 — AUDITORÍA DE CONTINUIDAD ANTE NO_REVISADO / USUARIO NO SABE REALIZAR LA PRUEBA

**Fecha:** 2026-09-17  
**Estado:** COMPLETADO CON ÉXITO  
**Versión de despliegue:** CarBot `9.15.0` (Orquestador `9.15.0`)  
**Componentes ML y RAG:** 100% INMUTABLES (19/19 hashes SHA-256 certificados)

---

## 1. Incidente Físico Auditado (Traza Real WhatsApp)

### Conversación Cronológica en Taller
1. **Turno 1 (Usuario):**
   > *"Hola, ahora quisiera revisar otro problema. Cuando paso por pistas irregulares o baches escucho un golpeteo en la parte delantera del carro. En pista lisa casi no se escucha. Al frenar no vibra el volante y el motor funciona normal. Todavía no he revisado la suspensión."*  
   **CarBot:**  
   > *“Al pasar por el bache, ¿el sonido es un golpe seco y sordo con rebote continuo, o un cascabeleo metálico al trabajar la suspensión?”* (`QuestionIntent.PRESENCIA_RUIDO`)

2. **Turno 2 (Usuario):**
   > *"Es más como un cascabeleo metálico cuando paso por baches. En pista lisa casi no se escucha."*  
   **CarBot:**  
   > *“¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?”* (`QuestionIntent.COMPONENTE_REVISADO`)

3. **Turno 3 (Usuario - Incidente):**
   > *"No, todavía no los he revisado y no sé bien cómo comprobar si tienen holgura."*  
   **CarBot (Comportamiento anómalo en producción 9.14):**  
   > *“Para mayor precisión: ¿se ha conectado un escáner automotriz OBD-II o el tablero muestra encendido el testigo Check Engine?”* (`QuestionIntent.CODIGO_DTC`)

---

## 2. Reconstrucción Forense por Turno (PostgreSQL & Estado Operativo)

| Variable de Auditoría | Turno 1 (Inicial) | Turno 2 (Aclaración Ruido) | Turno 3 (Incidente Físico Auditado) |
|---|---|---|---|
| `meta_message_id` | `wamid...ECQ0MzMgA=` | `wamid...NkEyMTM4...` | `wamid...NTI0NwA=` |
| `case_id` | `20260917-053610-097561` | `20260917-053610-097561` | `20260917-053610-097561` |
| `dominio` | `SUSPENSION` | `SUSPENSION` | `SUSPENSION` |
| `estado_operativo` | `EN_EVALUACION` | `EN_EVALUACION` | `EN_EVALUACION` |
| `QuestionIntent anterior` | Ninguno (inicio) | `PRESENCIA_RUIDO` | `COMPONENTE_REVISADO` |
| `Respuesta contextual interpretada` | N/A | `"cascabeleo metalico"` | `"desconocido"` (por regex genérico `PATRON_NO_SE`) |
| `FactState generado` | `sintoma_ruido_baches: PRESENTE`<br>`frenado_vibra: NEGADO`<br>`inspeccion_suspension: NO_REVISADO` | `ruido_cascabeleo_metalico: PRESENTE` | `desconocido: DESCONOCIDO`<br>*(Omisión del estado conceptual procedural)* |
| `Hechos activos` | 4 hechos (3 presentes, 1 negado) | 5 hechos | 6 hechos (incluye `desconocido`) |
| `Top 3 Actual` | 1. Amortiguador desgastado (42%)<br>2. Terminales dirección (31%)<br>3. Rótulas suspensión (19%) | 1. Rótulas de suspensión (44%)<br>2. Terminales de dirección (32%)<br>3. Amortiguador desgastado (18%) | 1. Rótulas de suspensión (44%)<br>2. Terminales de dirección (32%)<br>3. Amortiguador desgastado (18%) |
| `Preguntas candidatas` | `PRESENCIA_RUIDO`, `COMPONENTE_REVISADO`, `CODIGO_DTC` | `COMPONENTE_REVISADO`, `CODIGO_DTC` | `COMPONENTE_REVISADO`, `CODIGO_DTC` |
| `Descartes y motivos` | `COMPONENTE_REVISADO` (menor IG que `PRESENCIA_RUIDO`) | `PRESENCIA_RUIDO` (ya respondida) | `COMPONENTE_REVISADO` descartada por `PREGUNTA_REPETIDA` |
| `Activación GestorPlanB` | Inactivo (sin bloqueo de herramientas) | Inactivo | **Inactivo** (no reconocía falta de conocimiento procedural) |
| `Pregunta seleccionada` | `PRESENCIA_RUIDO` | `COMPONENTE_REVISADO` | `CODIGO_DTC` |

---

## 3. Demostración de la Causa Raíz

La auditoría demostró 4 fallas encadenadas en el flujo conversacional:

1. **Colisión de interpretación en `InterpreteRespuestasCortas`:**
   Al evaluar el texto *"No, todavía no los he revisado y no sé bien cómo comprobar si tienen holgura"*, el evaluador disparaba prematuramente `PATRON_NO_SE = re.compile(r"\b(no\s+s[eé]|desconozco|ni\s+idea)\b")`, asignando `campo="desconocido"` y `FactState.DESCONOCIDO`. No se capturaba el hecho de que la prueba específica de holgura **no se sabe realizar**.
2. **Bloqueo rígido por `PREGUNTA_REPETIDA`:**
   En `ConversationState.puede_preguntar()`, `COMPONENTE_REVISADO` registraba 1 intento y 1 respuesta recibida (`"desconocido"`). El generador la descartaba categóricamente como `PREGUNTA_REPETIDA` sin ofrecer explicación ni método alternativo.
3. **Restricción de `GestorPlanB` a herramientas físicas:**
   `GestorPlanB` solo se activaba ante ausencia de herramientas registradas en `CATALOGO_HERRAMIENTAS` (escáner, multímetro, manómetro, vacuómetro). No existía soporte para **falta de conocimiento procedural / metrológico** ni un procedimiento seguro para suspensión física.
4. **Fuga hacia `CODIGO_DTC` por falta de filtro de pertinencia electrónica:**
   `CODIGO_DTC` tenía categoría `GENERAL` y sobrevivía como la única candidata disponible tras agotarse las preguntas de suspensión, sin verificar si el dominio era puramente mecánico (ruido en baches sin testigos).

---

## 4. Distinción Conceptual de los Cuatro Estados Operativos

En Fase 9.15 se formalizó la distinción técnica estricta entre cuatro situaciones que anteriormente se trataban de manera difusa:

```
                                    ¿Se intentó la prueba?
                                   /                      \
                                 SÍ                        NO
                                /                            \
                 ¿Se pudo ejecutar?                     ¿Por qué no?
                 /               \                     /            \
               SÍ                 NO                 No sabe       No tiene
               |                  |                  cómo          herramienta
               v                  v                  v             v
       RESULTADO_NEGATIVO   HERRAMIENTA_         NO_SABE_REALIZAR  HERRAMIENTA_
       (Comprobó y NO hay   INDISPONIBLE         (Requiere guía    INDISPONIBLE
        holgura / falla)    (Se interrumpió      o alternativa     (Falta multímetro,
                            por falta de útil)   observable)       manómetro, etc.)
                                                     |
                                                     v
                                                NO_REVISADO
                                                (Pendiente pero
                                                 sabe cómo o no
                                                 declaró duda)
```

1. **`NO_REVISADO` (`FactState.NO_REVISADO`):**  
   El usuario declara que aún no realiza la comprobación, pero no indica incapacidad técnica ni falta de herramientas. Permite seguir indagando o mantener la prueba pendiente.
2. **`NO_SABE_REALIZAR_PRUEBA` (`FactState.NO_SABE_REALIZAR`):**  
   El usuario manifiesta explícitamente desconocimiento procedimental (*"no sé cómo comprobar si tienen holgura"*, *"cómo se mide el espesor"*). Dispara de inmediato una guía segura o una alternativa observable (Plan B).
3. **`HERRAMIENTA_NO_DISPONIBLE` (`FactState.HERRAMIENTA_INDISPONIBLE`):**  
   El usuario no cuenta con el instrumento de diagnóstico (*"no tengo multímetro"*, *"no tengo manómetro"*). Dispara el Plan B sin herramientas.
4. **`RESULTADO_NEGATIVO` (`FactState.NEGADO`):**  
   El usuario ejecutó la comprobación y el componente se encuentra en buen estado (*"ya revisé las rótulas y están perfectas, no tienen nada de holgura"*). Descarta la hipótesis correspondiente en el diferencial.

---

## 5. Implementación Arquitectónica de la Solución

### A. Modelo de Estado (`models.py`)
- Se incorporó `FactState.NO_SABE_REALIZAR = "no_sabe_realizar"`.
- Métodos añadidos al `ConversationState`:
  - `es_prueba_no_sabe_realizar(campo: str = "") -> bool`: Determina si el usuario desconoce cómo realizar la prueba activa.
  - `tiene_inspeccion_pendiente(campo: str = "") -> bool`: Comprueba si existe una inspección en estado pendiente (`NO_REVISADO` o `NO_SABE_REALIZAR`).
  - `obtener_hecho_no_sabe_realizar() -> Optional[Fact]`: Recupera el hecho procedural activo para guiar la alternativa.

### B. Intérprete de Respuestas Cortas (`interprete_respuestas_cortas.py`)
- **Bloque 0.05:** Detección prioritaria de `NO_SABE_REALIZAR_PRUEBA` antes de los patrones genéricos de duda o negación. Si el usuario indica *"no sé cómo comprobar"*, se mapea al componente de la pregunta activa con estado `FactState.NO_SABE_REALIZAR`.
- **Bloque 7b:** Detección de `RESULTADO_NEGATIVO` con negación de anomalía (*"las revisé y no tienen juego"*, *"están bien sin holgura"*).
- **Protección de `PATRON_NO_SE`:** Se impide que expresiones con verbos de acción ("comprobar", "medir", "probar", "usar") caigan en el cajón genérico `desconocido`.

### C. Procedimientos Seguros y Plan B Procedural (`gestor_plan_b.py`)
Se crearon planes de contingencia procedural seguros para los 6 macro-sistemas automotrices:

| Dominio | Inspección donde no sabe realizar | Procedimiento Seguro / Alternativa Observable (Plan B) |
|---|---|---|
| **Suspensión** | Holgura en rótulas / bujes | *Prueba segura en suelo:* Girar la dirección completa con el auto apoyado y balancear lateralmente, o prueba de rebote sobre la aleta. Si requiere elevador o palanca de fuerza, se recomienda inspección profesional. |
| **Frenos** | Medición de espesor de pastillas/discos | Inspección visual entre los radios del aro con linterna (espesor mínimo respecto al respaldo metálico) o verificar nivel de líquido de frenos en reservorio. |
| **Motor** | Prueba de salto de chispa en bujías | Descarte auditivo y visual seguro: verificar si hay rateo en ralentí, olor a gasolina cruda o humo negro sin manipular alta tensión. |
| **Eléctrico** | Tensión de batería / alternador | Prueba de intensidad con luces altas y ventilador: verificar si la luz tenue decae al acelerar o si el tablero parpadea. |
| **Transmisión** | Nivel y condición de ATF | Comprobación de retardo de acople en frío vs caliente y color del fluido en papel blanco si la varilla es accesible. |
| **Climatización** | Acople del embrague del compresor | Inspección visual del plato central del compresor con A/C encendido (gira vs detenido) y temperatura de las tuberías. |

### D. Reglas de Pertinencia para OBD-II / DTC (`compatibilidad_preguntas.py`)
Se implementó `es_pertinente_obd2()` sin recurrir a bloqueos estáticos:
- En **`SUSPENSION`** y **`FRENOS`**: `CODIGO_DTC` solo es elegible si existe evidencia electrónica activa (testigo Check Engine, ABS, ESC, suspensión adaptativa, sensores de rueda o mención previa de escáner). En ruidos mecánicos puros en baches, se descarta con motivo `SIN_JUSTIFICACION_ELECTRONICA`.
- En **`MOTOR`**, **`ELECTRICO`**, **`TRANSMISION`** o **`DESCONOCIDO`**: `CODIGO_DTC` es admisible como método de triaje técnico.

### E. Priorización Dinámica de Plan B (`generador_preguntas.py`)
Cuando `estado.es_prueba_no_sabe_realizar()` es verdadero:
- `QuestionIntent.PLAN_B_SIN_HERRAMIENTAS` recibe un boost de prioridad a **85 puntos** (superando a `COMPONENTE_REVISADO` que tiene 80).
- Se evita el descarte prematuro de la pregunta cuando el usuario solicita orientación.

---

## 6. Validación de Regresión y Matriz de 6 Dominios

Se diseñó la suite automatizada `test_continuidad_no_revisado_fase9_15.py` que evaluó los siguientes escenarios:

```
============================== test session starts ==============================
backend/tests/test_continuidad_no_revisado_fase9_15.py::test_incidente_whatsapp_continuidad_suspension_no_revisado PASSED [ 25%]
backend/tests/test_continuidad_no_revisado_fase9_15.py::test_distincion_conceptual_cuatro_estados PASSED             [ 50%]
backend/tests/test_continuidad_no_revisado_fase9_15.py::test_matriz_seis_dominios_no_sabe_realizar_plan_b PASSED     [ 75%]
backend/tests/test_continuidad_no_revisado_fase9_15.py::test_pertinencia_obd2_control_mecanico_vs_electronico PASSED [100%]
============================== 4 passed in 0.18s ==============================
```

### Resultados de la Matriz de Pruebas:
1. **Incidente Real WhatsApp (Suspensión):**  
   Ante *"No, todavía no los he revisado y no sé bien cómo comprobar si tienen holgura"*, CarBot ya **NO** pregunta por OBD-II. Genera la alternativa segura:
   > *“Para comprobar la holgura de forma segura sin desmontar: gira la dirección a tope y frena suave en terreno irregular para notar si el cascabeleo aumenta, o haz presión sobre la aleta delantera. ¿El sonido metálico se siente más al girar la dirección o al presionar hacia abajo?”*
2. **Distinción de 4 estados:** Confirmada en tests unitarios para `NO_REVISADO`, `NO_SABE_REALIZAR`, `HERRAMIENTA_INDISPONIBLE` y `NEGADO`.
3. **Matriz de 6 Dominios:** Superada al 100% con planes B procedurales funcionales para suspensión, frenos, motor, eléctrico, transmisión y climatización.
4. **Controles OBD-II:** Confirmado que en suspensión mecánica pura se descarta OBD-II, mientras que ante presencia de testigo ABS o falla de motor, OBD-II se mantiene plenamente elegible.

---

## 7. Verificación Criptográfica de Inmutabilidad (19/19 Hashes)

De acuerdo con las Reglas Metodológicas de Tesis de CarBot, ningún modelo, vectorizador ni corpus RAG fue alterado durante esta fase:

```
Auditando 19 componentes congelados Fase 8.3...
[OK] dataset_train                  -> c94d6e7b88ef72ea... (Inmutable)
[OK] benchmark_dev_60               -> 113b5f190758346a... (Inmutable)
[OK] modelo_diagnostico_falla_prod  -> 3d8199595b69bb01... (Inmutable)
[OK] modelo_sistema_prod            -> 22d11492e9576664... (Inmutable)
[OK] vectorizador_tfidf_prod        -> 8b8e8c3b3571fe96... (Inmutable)
[OK] modelo_diagnostico_candidata   -> 3d8199595b69bb01... (Inmutable)
[OK] modelo_sistema_candidata       -> 22d11492e9576664... (Inmutable)
[OK] vectorizador_tfidf_candidata   -> 8b8e8c3b3571fe96... (Inmutable)
[OK] corpus_metadatos_rag           -> 2f0684477522efb6... (Inmutable)
[OK] indice_faiss                   -> 757c4b006a8995f4... (Inmutable)
[OK] adaptador_modelo_ml            -> 014d3e6f6f9f5c5b... (Inmutable)
[OK] motor_rag                      -> eaa316a87ecaa1be... (Inmutable)
[OK] rag_relevance_filter           -> fa3d6aef13639bc3... (Inmutable)
[OK] auto_interrogador              -> 2e746e498facea34... (Inmutable)
[OK] politica_fusion                -> 073b97fe07c88918... (Inmutable)
[OK] prompt_builder                 -> e0b26f32f278bb10... (Inmutable)
[OK] text_processor                 -> f7075605f6a0e325... (Inmutable)
[OK] taxonomia_sistemas             -> 561e95c952effcd0... (Inmutable)
[OK] gestor_diagnostico             -> 66bead0526763314... (Inmutable)

RESULTADO FINAL: 19/19 artefactos 100% IDÉNTICOS E INMUTABLES.
```

---

## 8. Cumplimiento de Límites de Tamaño y Calidad de Código

| Archivo | Líneas Actuales | Límite Máximo | Estado |
|---|:---:|:---:|:---:|
| `backend/src/core/conversacion/models.py` | 551 | < 1000 | Conforme |
| `backend/src/core/conversacion/gestor_plan_b.py` | 481 | < 500 | Conforme |
| `backend/src/core/conversacion/interprete_respuestas_cortas.py` | 420 | < 500 | Conforme |
| `backend/src/core/conversacion/compatibilidad_preguntas.py` | 204 | < 500 | Conforme |
| `backend/src/core/conversacion/generador_preguntas.py` | 479 | < 500 | Conforme |
| `backend/src/core/conversacion/orquestador_conversacion.py` | 533 | < 1000 | Conforme |
| `backend/src/core/version.py` | 74 | < 500 | Conforme |

- **Linter Ruff (`ruff check src/core/conversacion`):** `All checks passed!`
- **Regresión completa Fase 9 (12 suites):** `102 passed, 0 failed in 12.59s`.

---

## 9. Conclusión y Cierre de Fase 9.15

Fase 9.15 concluyó con éxito demostrando la causa física del incidente, distinguiendo formalmente los 4 estados conceptuales de inspección (`NO_REVISADO`, `NO_SABE_REALIZAR`, `HERRAMIENTA_INDISPONIBLE`, `NEGADO`), implementando planes B procedurales en 6 macro-sistemas y gobernando la pertinencia técnica de preguntas OBD-II sin afectar en absoluto la inmutabilidad de los modelos ni del corpus RAG.

**SE PROCEDE A DETENERSE ANTES DE FASE 10.**
