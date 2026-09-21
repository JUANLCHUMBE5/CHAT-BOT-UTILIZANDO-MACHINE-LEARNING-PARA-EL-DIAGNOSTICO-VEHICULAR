# INVESTIGACIÓN FORENSE DE BUG CONVERSACIONAL (FASE 13.2)
## CARBOT_PRECAMPO_FROZEN — AUDITORÍA CAUSAL END-TO-END

**Fecha de Auditoría:** 2026-09-20  
**Entorno Evaluado:** PILOTO / TEST / RUNTIME POSTGRESQL (Conversación real: `f7a37e2d-efe8-4c26-9b62-9f4103e7b094`)  
**Tipo de Fase:** READ-ONLY / FORENSE / NO OPTIMIZACIÓN / NO IMPLEMENTACIÓN  
**Estado de Componentes Congelados:** 13/13 INTACTOS (0 modificaciones)  
**Registros Oficiales de Tesis Modificados:** 0 (Blindaje de tesis 0/30 PRE, 0/30 POST preservado)

---

## 1. RESUMEN EJECUTIVO DEL HALLAZGO

Durante una prueba manual real en el frontend posterior a FASE 13.1, se observó que ante la secuencia:
1. Pregunta de CarBot: *"Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"*
2. Respuesta afirmativa y detallada del usuario: *"Sí. Con el probador de chispa conectado se observa una chispa azulada, constante y uniforme durante el arranque en las cuatro bobinas."*
3. **Fallo:** CarBot repitió idénticamente: *"Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"* en bucle sin avanzar de estado.
4. Adicionalmente, se observó que la hipótesis Top-2 para un Nissan Sentra 2018 1.8 atmosférico fue *"Fuga en mangueras de intercooler o turbocompresor dañado"* (32%) y que el porcentaje de bujías (51%) se repitió a pesar de indicar que habían sido revisadas.

La investigación forense en base de datos PostgreSQL, registros de trazabilidad JSON y ejecución controlada determinó que:
- **El bug es 100% REPRODUCIBLE (`BUG_REPRODUCIBLE = TRUE`).**
- **El modelo de Machine Learning (Linear SVM), TF-IDF y RAG FAISS NO son la causa del bucle ni tienen errores de pesos.**
- La causa raíz del bucle reside en la capa de **gestión conversacional y procesamiento de lenguaje (`gestor_plan_b.py`, `interprete_respuestas_cortas.py` y `orquestador_conversacion.py`)**:
  - Un matching defectuoso de subcadena (`"si" in texto`) detectó la letra "si" dentro de palabras castellanas ("considerando", "siguiente") y al inicio del mensaje.
  - El sistema clasificó la respuesta del usuario NO como el **resultado exitoso de la prueba**, sino como un **evento de adquisición de herramienta** (`chispa_disponible = SI`).
  - La rama 0.2 de `orquestador_conversacion.py` carece de verificación de pregunta previa (`estado.ya_preguntado_texto`), forzando la repetición infinita de la misma pregunta.
- La aparición de "turbocompresor/intercooler" (32%) se debió a **contaminación entre turnos previos dentro de la misma sesión conversacional de WhatsApp**, donde existía una consulta previa de fuga de sobrealimentación no limpiada al no invocarse un comando de reinicio explícito (`nuevo diagnóstico`).

---

## 2. REPRODUCCIÓN FORENSE CONTROLADA

### 2.1 Evidencia en Base de Datos PostgreSQL
Se localizó en PostgreSQL la conversación exacta donde ocurrió el incidente (`id: f7a37e2d-efe8-4c26-9b62-9f4103e7b094`) y los registros diagnósticos generados:
- **Diagnóstico 1:** `3e27d933-fed9-4a6e-85e3-c55caba6ed9e` (2026-09-20 05:28:33 UTC)
  - Mensaje: *"Cuando estoy parado en el semáforo el carro empieza a temblar..."*
  - Top 3: Bujías/bobinas (50.51% -> 51%), Turbo/intercooler (32.20% -> 32%), IAC (17.30% -> 17%).
- **Diagnóstico 2:** `58f72415-de87-434b-850d-168ad8e1c15e` (2026-09-20 05:29:34 UTC)
  - Mensaje: *"Se revisaron las bujías y las bobinas..."*
  - Top 3: Repite exactamente 51% / 32% / 17%.
- **Mensaje Turno 3:** (2026-09-20 05:30:00 UTC)
  - Entrada usuario: *"Ya se verificaron bujías y bobinas y se descarta falla... continúa considerando esta evidencia."*
  - Salida CarBot: *"Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"*
- **Mensaje Turno 4:** (2026-09-20 05:30:18 UTC)
  - Entrada usuario: *"Sí. Con el probador de chispa conectado se observa una chispa azulada, constante y uniforme durante el arranque en las cuatro bobinas."*
  - Salida CarBot: *"Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"* (BUCLE).

### 2.2 Reproducción en Script Aislado
Al reproducir la secuencia con `OrquestadorConversacion`:
```text
Turno 3: Pregunta final = 'Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?'
Turno 4: Pregunta final = 'Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?'
Preguntas realizadas acumuladas:
  - [GENERAL]: ¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?
  - [COMPONENTE_REVISADO]: Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?
  - [COMPONENTE_REVISADO]: Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?
Hipótesis descartadas: [] (VACÍO)
```
Resultado: **BUG_REPRODUCIBLE = TRUE**.

---

## 3. AUDITORÍA DETALLADA POR COMPONENTES

### 3.1 Frontend y Canal de Comunicación
- **Payload recibido:** El frontend/webhook envía texto plano en UTF-8 (`texto_cliente` o `sintoma`). No existen botones estructurados para las respuestas intermedias de comprobaciones clínicas en WhatsApp Webhook; el mecánico responde escribiendo en lenguaje natural.
- **Trazabilidad de IDs:** `conversation_id`, `taller_id`, `mecanico_id` y `diagnostico_id` se vinculan adecuadamente.
- **Persistencia de mensajes:** El backend registra el 100% de los mensajes en la tabla `mensajes` de PostgreSQL.

### 3.2 Análisis de `gestor_plan_b.py` y `interprete_respuestas_cortas.py`
En `gestor_plan_b.py`, la función `detectar_recuperacion_herramienta`:
```python
# CÓDIGO ACTUAL (CON BUG):
es_afirmacion_directa = any(
    w in texto_l
    for w in (
        "si", "sí", "si tengo", "sí tengo", "tengo uno", "tengo tester",
        "dispongo", "lo tengo", "ya lo conecte", "ya lo conecté", "cuento con",
        "sí maestro", "si maestro", "tengo un", "tengo una",
    )
)
```
**Fallo Forense 1:** `w in texto_l` con `w = "si"` evalúa verdadero para cualquier palabra que contenga "si":
- `"...con la si-guiente comprobación..."` -> Contiene "si".
- `"...con-si-derando esta evidencia..."` -> Contiene "si".
- `"Sí. Con el probador..."` -> Contiene "sí".

**Fallo Forense 2:** Evalúa `tiene_mencion_herramienta_pregunta`. Como la pregunta previa contenía `"probador de chispa"`, `tiene_mencion_herramienta_pregunta` fue `True`. Por tanto, `detectar_recuperacion_herramienta` retornó `["chispa"]`.

**Fallo Forense 3:** `interprete_respuestas_cortas.py` (Línea 378) recibió `recuperadas = ["chispa"]` y generó:
```python
{
    "categoria_respuesta": "AFIRMACION",
    "campo": "chispa_disponible",
    "valor": "SI",
    "herramientas": ["chispa"]
}
```
El sistema confundió *"el mecánico observó la chispa requerida"* con *"el mecánico acaba de conseguir la herramienta probador de chispa"*.

### 3.3 Análisis de `orquestador_conversacion.py` (Bucle Infinito)
En `orquestador_conversacion.py`, Líneas 306-336:
```python
# CÓDIGO ACTUAL (CON BUG):
elif cat_ic == "HERRAMIENTA_RECUPERADA" or (valor_ic == "SI" and campo_ic and "disponible" in campo_ic):
    if campo_ic and "manometro" in campo_ic:
        ...
    elif campo_ic and "chispa" in campo_ic:
        pregunta_elegida = "Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"
        intent_elegido, decision = QuestionIntent.COMPONENTE_REVISADO.value, "PREGUNTAR"
        motivo_decision = "Usuario cuenta con probador de chispa: solicitando comprobación"
```
**Fallo Forense 4:** Esta rama se ejecuta de forma incondicional cada vez que `chispa_disponible == "SI"`.
- NO verifica si `estado.ya_preguntado_texto(pregunta_elegida)` es verdadero.
- NO registra la prueba como completada (`estado.registrar_prueba_completada`).
- NO descarta bujías/bobinas a pesar de que la chispa es constante y azulada.
- Retorna de inmediato en la línea 335 con `decision = "PREGUNTAR"`, impidiendo que el flujo avance al diagnóstico o a la siguiente comprobación.

### 3.4 Análisis de la Repetición de 51% (Turno 2)
En el Turno 2, el mecánico aportó:
*"Se revisaron las bujías y las bobinas. Las bujías presentan desgaste normal y no tienen carbonización anormal. Se comprobó la chispa y las cuatro bobinas funcionan correctamente..."*
- `ExtractorHechos.extraer_y_actualizar` buscaba patrones rígidos en primera persona: `"ya revise"`, `"ya probe"`, `"bujias nuevas"`, `"descarte"`.
- Las expresiones pasivas formales de taller (*"se revisaron"*, *"se comprobó"*, *"presentan desgaste normal"*) no fueron capturadas como hechos clínicos en `estado.hechos`.
- Al no haber hechos nuevos, `consulta_consolidada` fue idéntica a la del Turno 1.
- El modelo ML (que es puramente determinista y sin estado) recibió el mismo texto y devolvió exactamente el mismo vector de probabilidades (51% / 32% / 17%).

### 3.5 Análisis del Origen del 32% Turbo/Intercooler
En la inspección de la conversación `f7a37e2d-efe8-4c26-9b62-9f4103e7b094`:
- En los turnos 1 a 3 anteriores, el usuario había consultado por:
  *"Fuga de aire por conducto rajado del sistema de admisión/sobrealimentación."*
- Al ingresar la queja del Nissan Sentra (*"Cuando estoy parado en el semáforo el carro empieza a temblar..."*), `SegmentadorCasos` evaluó:
  `decision_transicion = MANTENER_CASO` (`motivo = SINTOMAS_COMPATIBLES_MISMO_CASO`).
- Por tanto, `SintetizadorConsulta` concatenó:
  *"Fuga de aire por conducto rajado del sistema de admisión/sobrealimentación.. cuando está detenido en ralentí. mejora al acelerar."*
- El clasificador SVM recibió las palabras *"sobrealimentación"* y *"conducto rajado"*, generando como Top-2 *"Fuga en mangueras de intercooler o turbocompresor danado"* con 32.2%.
- Adicionalmente, `ValidadorCompatibilidad` no posee regla de exclusión de turbo para perfiles atmosféricos conocidos.

---

## 4. MATRIZ DE CAUSA RAÍZ Y DISCREPANCIA CON FASE 13.1

| Componente | Comportamiento Esperado | Comportamiento Real Observado | Capa Responsable |
| :--- | :--- | :--- | :--- |
| **Detección de herramienta** | Distinguir posesión de herramienta de resultado clínico de la prueba. | Trata "Sí, probé y hay chispa" como adquisición de herramienta (`chispa_disponible=SI`). | `gestor_plan_b.py` |
| **Selector de preguntas** | No repetir preguntas ya formuladas (`ya_preguntado_texto`). | Vuelve a seleccionar la misma pregunta técnica en bucle cerrado. | `orquestador_conversacion.py` |
| **Consumo de evidencia** | Descartar bujías/bobinas cuando se confirma chispa correcta. | No registra descarte; mantiene hipótesis 51% en memoria. | `interprete_respuestas_cortas.py` |
| **Aislamiento de casos** | Resetear contexto al ingresar un vehículo y síntoma no relacionado. | Concatenó queja de sobrealimentación anterior con nuevo caso Sentra. | `segmentador_casos.py` |

### ¿Por qué los tests de FASE 13.1 no detectaron el bucle?
En FASE 13.1:
1. Las 10 pruebas E2E automatizadas se ejecutaron creando un `session_id` nuevo e independiente por caso, evitando la contaminación inter-caso de `SegmentadorCasos`.
2. Las pruebas de disponibilidad de herramientas emplearon valores directos aislados (ej. `"tengo multimetro"` -> `"12.6 V"`), sin reproducir la respuesta compuesta natural de comprobación de chispa (*"Sí. Con el probador de chispa conectado se observa..."*).
3. La prueba de intercambio de bobina (Caso 03) evaluó el cambio de DTC P0302 a P0303, no la respuesta verbal afirmativa a la inspección con probador de chispa.

---

## 5. CLASIFICACIÓN DE SEVERIDAD DE HALLAZGOS

- **QUESTION_REPETITION:** `MAJOR`  
  Bloquea el avance conversacional ante una respuesta afirmativa natural del mecánico en una comprobación física obligatoria.
- **EVIDENCE_USAGE:** `MODERATE`  
  No extrae hechos negativos ante redacciones pasivas formales de taller (*"se revisaron"*, *"chispa correcta"*).
- **SESSION_STATE:** `MODERATE`  
  Falta de particionamiento estricto de casos cuando el usuario cambia de falla en WhatsApp sin teclear "nuevo diagnóstico".
- **VEHICLE_COMPATIBILITY:** `MINOR`  
  El modelo SVM predijo turbo debido a contaminación textual previa; falta una regla de compatibilidad aspirada/turbo.

---

## 6. PROPUESTA DE HOTFIX MÍNIMO (SIN IMPLEMENTAR)

> [!IMPORTANT]
> **REGLA DE CONGELAMIENTO RESPETADA:** Esta propuesta **NO requiere reentrenar ni modificar** el modelo SVM, TF-IDF, RAG, FAISS, dataset, taxonomía ni prompts diagnósticos. Es 100% código de orquestación conversacional en Python.

### Modificaciones propuestas:
1. **`backend/src/core/conversacion/gestor_plan_b.py`**:
   - Reemplazar `w in texto_l` por coincidencia de límites de palabra `re.search(r"\b" + re.escape(w) + r"\b", texto_l)` para evitar falsos positivos con "considerando" o "siguiente".
   - Si la última pregunta era de comprobación de componente (`COMPONENTE_REVISADO`) y no de disponibilidad de herramienta, no clasificar el mensaje como recuperación de herramienta.
2. **`backend/src/core/conversacion/interprete_respuestas_cortas.py`**:
   - Agregar mapeo de resultado de prueba: si la pregunta era sobre salto de chispa y el usuario confirma (*"sí"*, *"chispa azulada"*, *"chispa constante"*), registrar `chispa_confirmada = SI` en `estado.hechos`, marcar la prueba como completada y registrar descarte técnico de bujías/bobinas.
3. **`backend/src/core/conversacion/orquestador_conversacion.py`**:
   - En la rama 0.2 (`cat_ic == "HERRAMIENTA_RECUPERADA"`), verificar si la pregunta ya fue formulada:
     `if estado.ya_preguntado_texto(pregunta_elegida): avanzar_a_siguiente_paso()`
4. **`backend/src/core/conversacion/detector_polaridad.py` y `extractor_hechos.py`**:
   - Incluir expresiones pasivas en la extracción de antecedentes: `"se revisaron"`, `"se verificaron"`, `"se comprobo"`, `"chispa correcta"`.

---

## 7. DISEÑO DE TEST DE REGRESIÓN E2E

Se estructuró el test `test_regresion_bucle_chispa_sentra.py` para validar:
1. **Turno 1:** Síntoma Sentra -> Recibe hipótesis iniciales.
2. **Turno 2:** Usuario indica comprobación de bujías y bobinas -> El sistema avanza sin bucle.
3. **Turno 3:** CarBot formula pregunta técnica sobre probador de chispa.
4. **Turno 4:** Usuario responde *"Sí. Con el probador de chispa conectado se observa salto constante..."* -> El sistema debe:
   - Persistir la evidencia de chispa correcta.
   - Marcar la pregunta como completada.
   - **NO repetir la pregunta sobre el probador de chispa.**
   - Descartar o reducir la probabilidad de falla en bujías/bobinas.
   - Formular una pregunta diferente o emitir conclusión diagnóstica (ej. revisar cuerpo de aceleración o presión de combustible).

---

## 8. CONCLUSIÓN Y RECOMENDACIÓN

El bug reportado es un fallo de lógica de estado conversacional en el backend, no un defecto del clasificador de Machine Learning congelado.

**Recomendación:** `HOTFIX_BEFORE_PILOT`  
Se recomienda aplicar el hotfix mínimo en la lógica de control conversacional antes del piloto presencial en taller, ya que cualquier mecánico que responda afirmativamente a la comprobación de chispa quedará atrapado en el mismo bucle.
