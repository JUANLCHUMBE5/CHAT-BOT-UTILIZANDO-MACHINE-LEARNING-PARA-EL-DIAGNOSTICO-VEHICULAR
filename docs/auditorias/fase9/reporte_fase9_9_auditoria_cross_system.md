# Reporte de Auditoría: Fase 9.9 — Auditoría de Fallo Cross-System en WhatsApp Real

**Fecha de Auditoría:** 16 de Septiembre de 2026  
**Sistema:** CarBot — Chatbot de Diagnóstico Vehicular con Inteligencia Artificial  
**Alcance Técnico:** Auditoría forense exhaustiva de extremo a extremo sin modificación de pesos ni código ML.  
**Estado Criptográfico:** 19/19 Componentes Fase 8.3 Inmutables (100% SHA-256 verificado).

---

## 1. Contexto del Incidente y Objetivo de la Fase

Durante las pruebas de campo en WhatsApp real tras las fases previas, se produjo un fallo crítico de coherencia técnica: un mensaje que describía de forma inequívoca un problema mecánico de **frenos y vibración en el volante a alta velocidad** fue diagnosticado por CarBot con:
- **Batería descargada o bornes sulfatados — 98%**
- **Bujías o bobinas de encendido — 3%**
- **Discos de freno alabeados o desgastados — 2%**
- Recomendación de voltaje de batería, solicitud de multímetro y pregunta de validación `¿Fue correcta? SÍ/NO`.

El objetivo de esta **Fase 9.9** es realizar una auditoría forense rigurosa, aislando la primera divergencia del pipeline sin modificar ni reentrenar los modelos de Machine Learning (Linear SVM), TF-IDF, RAG, FAISS ni los conjuntos de datos.

---

## 2. Traza End-to-End Obligatoria del Caso Real en Base de Datos

A partir de la inspección directa de PostgreSQL (`mensajes`, `conversaciones`, `diagnosticos`, `hipotesis_diagnostico`), se recuperó el registro completo del incidente:

| Parámetro de Traza | Registro Forense en Base de Datos |
| :--- | :--- |
| **`meta_message_id`** | `wamid.HBgLNTE5NTUwOTUxNDcVAgASGBYzRUIwRkUxM0VFNTYyNEExMzZCRjg3AA==` |
| **`case_id`** | `26d11da3-b3c1-424f-a9cb-b2f5674a7a8d` |
| **`conversacion_id`** | `f7a37e2d-efe8-4c26-9b62-9f4103e7b094` |
| **`timestamp_recepcion`** | `2026-09-17 02:11:06.878995+00:00` (21:11:06 hora local) |
| **`diagnostico_id`** | `0dd52f1b-8523-4c5e-80a7-6b4e432d15ff` |
| **`version_orquestador`** | `"9.7.0"` (proceso en memoria no reiniciado) |
| **`estado_sesion_antes`** | Turno 6 activo. Hechos confirmados en memoria: `motor_arranca=NO`, `ruido_arranque=clic_unico`, `sintoma_chasquido_de_arranque_clac`, `descarte_bateria`, `nueva_observacion_tecnica=920 809 965`. `hipotesis_descartadas: ["Bateria descargada o bornes sulfatados"]`. `estado_operativo: ARRANQUE`. |
| **`mensaje_whatsapp_raw`** | *"Buenas, tengo un problema con mi carro. Cuando manejo normalmente todo va bien, pero cuando freno desde una velocidad más o menos alta empiezo a sentir una vibración fuerte en el volante. A baja velocidad casi no se siente. No se prende ninguna luz en el tablero y el carro sí frena, pero la vibración me preocupa. ¿Qué podría ser?"* |
| **`intent`** | `consulta_inicial_sintomas` / `desconocido` en clasificación de turno |
| **`hechos_extraidos`** | `sintoma_vibración`: `"vibración"`, `condicion_operacion`: `"al frenar"`, `conflicto_operativo`: `"arranque_vs_marcha"` |
| **`estado_operativo`** | `ARRANQUE` (debido al conflicto no resuelto entre los hechos heredados de arranque y el nuevo síntoma de frenado) |
| **`consulta_consolidada_ml`** | `"a gasolina. presenta clic_unico, motor no arranca, chasquido de arranque clac, vibracion. cuando está al frenar. antecedente: bateria descargada o bornes sulfatados descartada."` |
| **`macro_system_raw`** | `ELECTRICO` (79.62%), `FRENOS` (14.20%), `MOTOR` (6.03%) |
| **`top10_ml_raw`** | Ver Sección 3 (Tabla comparativa Caso A vs Caso B) |
| **`top3_despues_jerarquia`** | 1. Bateria descargada (97.66%), 2. Bujías/bobinas (1.17%), 3. Discos de freno (0.66%) |
| **`top3_compatibilidad`** | No evaluado en runtime debido a ejecución sobre worker desfasado |
| **`rag_query`** | `"Bateria descargada o bornes sulfatados"` |
| **`resultado_rag`** | `"PROCEDIMIENTO: COMPROBACIÓN DE CAÍDA DE TENSIÓN EN TERMINALES 30/50, CONTACTOS DE SOLENOIDE Y LONGITUD DE CARBONES EN MOTOR DE ARRANQUE"` (Corpus ID: `15f3f12516518e87`, Similitud: `0.2331`) |
| **`cache_hit` / `cache_key`** | `desde_cache: False` (Inferencia ejecutada en tiempo real: ML = 67 ms, RAG = 19 ms, Gemini degradado = 1515 ms, Total = 1606 ms) |
| **`respuesta_final_whatsapp`** | `1. Bateria descargada o bornes sulfatados — 98%`<br>`2. Falla en bujias o bobinas de encendido (misfire) — 3%`<br>`3. Discos de freno alabeados o desgastados — 2%`<br>🛠️ *Primero revisa:* voltaje de batería...<br>¿Tienes multímetro...? 🔎 ¿Fue correcta? SÍ / NO |

---

## 3. Prueba Directa del Modelo ML Congelado (Fase 8.3)

Se ejecutó el clasificador Linear SVM congelado de forma aislada e independiente en el script de prueba, contrastando dos escenarios:

- **CASO A:** El texto del mensaje de WhatsApp RAW directo y sin contaminar.
- **CASO B:** La consulta clínica consolidada que el orquestador conversacional envió al modelo.

### 3.1 Resultados del Caso A vs. Caso B

```text
======================================================================
CASO A: Mensaje WhatsApp RAW exacto (Aislado)
======================================================================
Texto: "Buenas, tengo un problema con mi carro. Cuando manejo normalmente todo va bien,
pero cuando freno desde una velocidad más o menos alta empiezo a sentir una vibración
fuerte en el volante. A baja velocidad casi no se siente. No se prende ninguna luz en el
tablero y el carro sí frena, pero la vibración me preocupa. ¿Qué podría ser?"

1. Macro-Sistema L1:
   - FRENOS: 79.05%
   - SUSPENSION_CHASIS: 18.17%
   - ELECTRICO: 2.53%
   - TRANSMISION: 0.17%
   - MOTOR: 0.09%

2. Linear SVM Nivel 2 RAW (antes de jerarquía):
   #1: Discos de freno alabeados o desgastados          -> 42.31%
   #2: Llantas desbalanceadas o desalineadas            -> 27.74%
   #3: Falla en sensor de oxigeno o mezcla rica         -> 13.21%
   #4: Bomba de gasolina quemada o baja presion         ->  6.76%
   ...
   #7: Bateria descargada o bornes sulfatados           ->  1.39%

3. Predicción Final Jerárquica (L1 + L2 combinado):
   #1: Discos de freno alabeados o desgastados          -> 83.58% (Top 1)
   #2: Llantas desbalanceadas o desalineadas            -> 14.93% (Top 2)
   #3: Fuga hidraulica o aire en sistema de frenos      ->  0.55% (Top 3)
   ...
   #7: Bateria descargada o bornes sulfatados           ->  0.07%
```

```text
======================================================================
CASO B: Consulta Consolidada generada por WhatsApp (Contaminada)
======================================================================
Texto: "a gasolina. presenta clic_unico, motor no arranca, chasquido de arranque clac,
vibracion. cuando está al frenar. antecedente: bateria descargada o bornes sulfatados descartada."

1. Macro-Sistema L1:
   - ELECTRICO: 79.62%
   - FRENOS: 14.20%
   - MOTOR: 6.03%

2. Linear SVM Nivel 2 RAW (antes de jerarquía):
   #1: Bateria descargada o bornes sulfatados           -> 76.78%
   #2: Falla en bujias o bobinas de encendido (misfire) -> 11.90%
   #3: Discos de freno alabeados o desgastados          ->  4.31%

3. Predicción Final Jerárquica (L1 + L2 combinado):
   #1: Bateria descargada o bornes sulfatados           -> 97.66% (Top 1)
   #2: Falla en bujias o bobinas de encendido           ->  1.17% (Top 2)
   #3: Discos de freno alabeados o desgastados          ->  0.66% (Top 3)
```

### 3.2 Dictamen Concluyente sobre el Modelo ML

- **El modelo de Machine Learning es 100% INOCENTE y TÉCNICAMENTE PRECISO.**
- Cuando se le proporciona el mensaje limpio, el Linear SVM predice con **83.58%** la falla exacta (**Discos de freno alabeados**) y con **14.93%** el diferencial físico directo (**Llantas desbalanceadas**), identificando el macro-sistema **FRENOS** con **79.05%**.
- Por consiguiente:
  $$\text{Clasificación del Hallazgo} = \text{\textbf{A) La extracción y memoria conversacional contaminó la entrada}}$$
  $$\text{\textbf{NO ES UN ERROR REAL DEL CLASIFICADOR (NO REENTRENAR ML)}}$$

---

## 4. Auditoría del Estado Operativo (¿Por qué no fue FRENADO?)

En `ExtractorHechos.inferir_estado_operativo`:
```python
senial_arranque = bool(
    hechos_confirmados.get("motor_arranca") == "NO"
    or hechos_confirmados.get("ruido_arranque") in ("clic_unico", "clics_repetidos")
    ...
)
senial_frenado = bool(
    hechos_confirmados.get("condicion_operacion") == "al frenar"
    or re.search(r"\b(al\s+frenar|frenando|cuando\s+freno)\b", texto_l)
)

# Detección de Contradicción Operativa (Escenario H)
if senial_arranque and (senial_marcha or senial_frenado):
    return EstadoOperativo.ARRANQUE, True
```

1. La conversación mantenía activos en `hechos_confirmados` los atributos del caso anterior (`motor_arranca=NO`, `clic_unico`). Por tanto, `senial_arranque` evaluó a `True`.
2. El mensaje nuevo aportó `"cuando freno"`, activando `senial_frenado = True`.
3. La condición de la línea 393 detectó un conflicto y forzó por diseño el retorno de `EstadoOperativo.ARRANQUE`, catalogándolo como contradicción en lugar de reconocer un **cambio de caso clínico**.
4. Al permanecer en `ARRANQUE`, el orquestador priorizó los hechos de arranque sobre los de frenado.

---

## 5. Auditoría de Paridad Fase 9.8 (Preguntas Dobles Observadas)

Se auditó por qué el mensaje devuelto en WhatsApp volvió a contener simultáneamente `¿Tienes multímetro?` y `¿Fue correcta? SÍ/NO` a pesar de que la Fase 9.8 resolvió dicha condición (`preguntas_dobles = 0`):

1. **Desfase de Procesos en Ejecución (Windows):**
   - Los procesos en segundo plano fueron inspeccionados con `Get-CimInstance Win32_Process`:
     * `PID 21764 / 21192`: `python.exe -m src.application.jobs.worker` (Iniciados a las **20:22:01**).
     * `PID 5720 / 26976`: `python.exe -m uvicorn main:app --reload --port 8000` (Iniciados a las **20:22:02**).
   - El mensaje del incidente ingresó por WhatsApp a las **21:11:06**.
   - Los archivos de la Fase 9.8 fueron editados y validados entre las **20:47 y las 21:03**.
   - El worker de colas **no posee recarga en caliente (`--reload`)** y Uvicorn mantuvo módulos pre-compilados en memoria de los subprocesos iniciados a las 20:22:01.
2. **Consecuencia:** La solicitud de WhatsApp fue atendida por el proceso en caliente que ejecutaba el código anterior a la Fase 9.8, donde la supresión de `¿Fue correcta? SÍ/NO` aún no estaba cargada en memoria activa.

---

## 6. Auditoría Matemática de Scores (98% + 3% + 2% = 103%)

Se determinó el origen exacto de la suma anómala de porcentajes en WhatsApp:

1. **Inyección de Piso Mínimo en `PoliticaFusionDiagnostica.fusionar_evidencia`:**
   En las líneas 336-338 de `src/core/diagnostico/politica_fusion.py`:
   ```python
   confianza_res = 0.9766  # Linear SVM jerárquico calibrado
   prob_restante = max(0.05, 1.0 - confianza_res)
   prob_d2 = round(prob_restante * 0.65, 3)
   prob_d3 = round(prob_restante * 0.35, 3)
   ```
   - Cálculo real:
     $$1.0 - 0.9766 = 0.0234$$
   - Aplicación de `max(0.05, ...)`:
     $$\text{Como } 0.0234 < 0.05 \implies \text{prob\_restante se fuerza a } 0.05$$
   - Distribución 65% / 35%:
     $$\text{prob\_d2} = 0.05 \times 0.65 = 0.0325 \approx 0.033 \quad (3.3\%)$$
     $$\text{prob\_d3} = 0.05 \times 0.35 = 0.0175 \approx 0.017 \quad (1.7\%)$$
2. **Formateo con Redondeo Entero Independiente en `formateador_compacto.py`:**
   ```python
   conf_pct = int(round(float(prob) * 100))
   ```
   - Top 1: `round(0.9766 * 100) = 98%`
   - Top 2: `round(0.0330 * 100) = 3%`
   - Top 3: `round(0.0170 * 100) = 2%`
   $$\sum = 98\% + 3\% + 2\% = 103\%$$
3. **Conclusión de Scores:** Los valores mostrados no son probabilidades mutuamente excluyentes extraídas directamente de una función Softmax normalizada, sino una probabilidad primaria calibrada combinada con un piso de resguardo del 5% para garantizar que los diagnósticos diferenciales no se impriman en 0%. Al aplicar redondeo entero independiente a valores que ya sumaban `1.0266`, la interfaz visual produjo `103%`.

---

## 7. Auditoría de Caché

- En el registro de PostgreSQL: `trazabilidad["desde_cache"] = False`.
- `tiempo_inferencia_ml_ms = 67 ms`.
- La clave de caché no interfirió en el resultado; no hubo colisión de caché. El modelo procesó efectivamente la cadena de texto recibida.

---

## 8. Tabla Canónica de Trazabilidad Forense

A continuación se resume la cadena de transformación exacta que condujo al fallo:

| Etapa del Pipeline | Estado / Contenido Registrado |
| :--- | :--- |
| **1. Mensaje RAW** | *"Buenas, tengo un problema con mi carro. Cuando manejo normalmente todo va bien, pero cuando freno desde una velocidad más o menos alta empiezo a sentir una vibración fuerte en el volante. A baja velocidad casi no se siente. No se prende ninguna luz en el tablero y el carro sí frena, pero la vibración me preocupa. ¿Qué podría ser?"* |
| **2. Hechos Clínicos en Memoria** | **Heredados (Caso anterior):** `motor_arranca=NO`, `ruido_arranque=clic_unico`, `chasquido_clac`, `descarte_bateria`, `nueva_observacion=920 809 965`.<br>**Nuevos:** `sintoma_vibracion`, `condicion=al frenar`. |
| **3. Estado Operativo** | `ARRANQUE` (Evaluado erróneamente como contradicción operativa `arranque_vs_marcha` por colisión de hechos antiguos con nuevos). |
| **4. Consulta ML Generada** | `"a gasolina. presenta clic_unico, motor no arranca, chasquido de arranque clac, vibracion. cuando está al frenar. antecedente: bateria descargada o bornes sulfatados descartada."` |
| **5. Macro-Sistema RAW** | `ELECTRICO: 79.62%`, `FRENOS: 14.20%`, `MOTOR: 6.03%`. |
| **6. Top 3 RAW (Linear SVM)** | 1. Bateria descargada (76.78%)<br>2. Bujías/bobinas (11.90%)<br>3. Discos de freno (4.31%). |
| **7. Top 3 Final (Jerárquico)** | 1. Bateria descargada (97.66%)<br>2. Bujías/bobinas (1.17%)<br>3. Discos de freno (0.66%). |
| **8. Respuesta WhatsApp** | 🔧 *Posibles causas*<br>1. Bateria descargada o bornes sulfatados — 98%<br>2. Falla en bujias o bobinas de encendido (misfire) — 3%<br>3. Discos de freno alabeados o desgastados — 2%<br>🛠️ *Primero revisa:* voltaje de batería...<br>¿Tienes multímetro...? 🔎 ¿Fue correcta? SÍ / NO |

---

## 9. Verificación de Inmutabilidad Criptográfica (Fase 8.3)

Se auditó la integridad SHA-256 de los 19 artefactos congelados:

| Componente | Hash SHA-256 (Primeros 8 chars) | Estado |
| :--- | :---: | :---: |
| `dataset_train` | `c94d6e7b...` | **INMUTABLE** |
| `benchmark_dev_60` | `113b5f19...` | **INMUTABLE** |
| `modelo_diagnostico_prod` | `3d819959...` | **INMUTABLE** |
| `modelo_sistema_prod` | `22d11492...` | **INMUTABLE** |
| `vectorizador_tfidf_prod` | `8b8e8c3b...` | **INMUTABLE** |
| `modelo_diagnostico_candidata` | `3d819959...` | **INMUTABLE** |
| `modelo_sistema_candidata` | `22d11492...` | **INMUTABLE** |
| `vectorizador_tfidf_candidata` | `8b8e8c3b...` | **INMUTABLE** |
| `corpus_metadatos_rag` | `2f068447...` | **INMUTABLE** |
| `indice_faiss` | `757c4b00...` | **INMUTABLE** |
| `adaptador_modelo_ml` | `014d3e6f...` | **INMUTABLE** |
| `motor_rag` | `eaa316a8...` | **INMUTABLE** |
| `rag_relevance_filter` | `fa3d6aef...` | **INMUTABLE** |
| `auto_interrogador` | `2e746e49...` | **INMUTABLE** |
| `politica_fusion` | `073b97fe...` | **INMUTABLE** |
| `prompt_builder` | `e0b26f32...` | **INMUTABLE** |
| `text_processor` | `f7075605...` | **INMUTABLE** |
| `taxonomia_sistemas` | `561e95c9...` | **INMUTABLE** |
| `gestor_diagnostico` | `66bead05...` | **INMUTABLE** |

**Resultado:** **19/19 artefactos 100% IDÉNTICOS E INALTERADOS.**

---

## 10. Conclusión y Criterio de Parada

1. **Causa Raíz Principal:** Contaminación por acumulación persistente de hechos entre consultas clínicas no relacionadas. El usuario introdujo una consulta sobre un sistema vehicular distinto (frenos/vibración) dentro de la misma conversación activa de WhatsApp, sin que el sistema detectara la disyunción temática ni purgara los hechos de arranque previos (`motor_arranca=NO`, `clic_unico`, `chasquido clac`).
2. **Evaluación del Clasificador:** El clasificador Linear SVM congelado Fase 8.3 es **completamente inocente y acertado**. Ante el mensaje sin contaminar, predice **Discos de freno alabeados con 83.58%** y **FRENOS con 79.05%**. **NO SE DEBE REENTRENAR EL MODELO ML.**
3. **Causa Secundaria (Scores 103%):** Introducción de un piso artificial de 5% en el diagnóstico diferencial (`politica_fusion.py`) que, sumado a un redondeo independiente, supera el 100%.
4. **Causa Secundaria (Preguntas Dobles):** Desfase de procesos Uvicorn/worker en Windows que ejecutaban código previo a la Fase 9.8.

**DETENIDO FORMALMENTE SEGÚN INSTRUCCIONES. NO SE MODIFICA EL MODELO ML. NO SE INICIA LA FASE 10.**
