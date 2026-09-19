# PLAN MAESTRO DE MEJORA CONTROLADA DEL RAG — CARBOT

**Fase**: RAG-PLAN — Planificación Maestra para la Mejora Controlada del RAG
**Fecha de Elaboración**: 17 de Septiembre de 2026
**Modo de Ejecución**: **ESTRICTAMENTE DE LECTURA, ANÁLISIS Y DISEÑO** (Zero Implementation)
**Documento de Evidencia Previa**: `FASE_RAG_AUDIT_REPORTE_FINAL.md`
**Objetivo**: Diseñar y especificar con rigor forense, matemático y de arquitectura de software el plan de transformación integral del subsistema RAG de CarBot, preservando el baseline congelado y garantizando cero regresiones en el clasificador ML C1 y la seguridad de taller.

> [!IMPORTANT]
> **DECLARACIÓN DE INMUTABILIDAD Y LÍMITES OPERATIVOS**:
> En esta fase **NO** se implementó ningún cambio de código, **NO** se alteró `metadatos_manuales.json`, **NO** se modificó `indice_faiss.index`, **NO** se reconstruyeron embeddings, **NO** se corrigieron las 10 etiquetas todavía, **NO** se descargaron bases externas y **NO** se utilizaron casos de `TEST10` ni la muestra oficial de 60 registros de campo de la tesis. Esta fase entrega única y exclusivamente la especificación técnica completa, ejecutable y auditable.

---

## 1. CONTEXTO DEL SISTEMA Y ROL DEL RAG EN CARBOT

CarBot es un sistema de asistencia y apoyo al diagnóstico para mecánicos en talleres automotrices, fundamentado en una arquitectura desacoplada en capas:

```
MECÁNICO / WHATSAPP  ───>  EXTRACTOR DE EVIDENCIA (Parsing / Jerga)
                                      │
                                      ▼
                             MODELO ML C1 (Linear SVM + TF-IDF)
                             [Predicción Top-3 + Probabilidades]
                                      │
                                      ▼
                              SUBSISTEMA RAG (FAISS + Re-ranking)
                             [Recuperación de Evidencia Técnica OEM]
                                      │
                                      ▼
                             POLÍTICA DE FUSIÓN DIAGNÓSTICA
                             [Ponderación Multiseñal: DTC + ML + RAG]
                                      │
                                      ▼
                             AUTO-INTERROGADOR / ORQUESTADOR
                             [Suficiencia de Información y Descarte]
                                      │
                                      ▼
                             LLM GEMINI / WORKER RESILIENTE
                             [Generación de Reporte Técnico Formal]
```

### El Flujo Objetivo de Razonamiento Clínico:
$$\text{Cliente describe} \rightarrow \text{Mecánico consulta} \rightarrow \text{CarBot propone Hipótesis} \rightarrow \text{CarBot sugiere Comprobación/Pregunta} \rightarrow \text{Mecánico realiza Medición Física} \rightarrow \text{CarBot interpreta Lectura} \rightarrow \text{CarBot Descarta/Refuerza} \rightarrow \text{CarBot propone Siguiente Paso} \rightarrow \text{Confirmación Física Final}$$

CarBot **NO** sustituye la inspección física, el escáner, los instrumentos metrológicos ni el manual OEM de taller. Su valor reside en reducir la incertidumbre diagnóstica y guiar el descarte sistemático.

---

## 2. AUDITORÍA DEL PIPELINE DE CONSTRUCCIÓN ACTUAL

Para planificar cualquier modificación futura, es imprescindible auditar cómo se procesa y consume actualmente el conocimiento en el código de producción.

### TABLA 1 — Pipeline Real de Construcción y Recuperación RAG

| Etapa | Componente / Script | Entrada | Proceso Interno | Salida | Vulnerabilidad o Riesgo Detectado |
|:---:|:---|:---|:---|:---|:---|
| **1. Almacenamiento Fuente** | `machine_learning/manuals/**/*.txt` | Archivos de texto sin procesar. | Estructuración manual con delimitador `=== TITULO ===\n CUERPO`. | 11 archivos de texto en disco. | Chunks stub de 56 car.; 90.4% concentrado en 2 compendios genéricos. |
| **2. Catálogo Metadatos** | `metadatos_manuales.json` | JSON estructurado (239 entradas). | Mapeo asociativo `titulo.lower() -> dict_metadato`. | Diccionario en memoria `mapa_metadatos`. | 10 inconsistencias semánticas en atributo `falla`; no indexa archivos no registrados. |
| **3. Parseo y Extracción** | `MotorRAG._indexar_manuales_multimarca` | Archivos `.txt` registrados en catálogo. | Regex `r'^===\s*(.*?)\s*===\s*$\n(.*?)(?=^===|\Z)'`. Deduplicación por hash SHA-256 de texto. | Listas en memoria: `titulos`, `documentos`, `metadatos_procedimientos`. | **Riesgo crítico de desalineación posicional** si se altera el orden de lectura de archivos. |
| **4. Vectorización TF-IDF** | `sklearn.TfidfVectorizer` | Lista combinada `[f'{t}\n{c}']`. | Fit-transform dinámico con $n$-gramas (1,2), sublinear TF, 32,596 dimensiones. | Matriz dispersa `matriz_tfidf` ($239 \times 32596$). | Solo vectoriza título y cuerpo; NO vectoriza `falla` ni `sistema` de la metadata. |
| **5. Indexación FAISS** | `faiss.IndexFlatIP` | `matriz_tfidf` normalizada $L_2$. | `faiss.normalize_L2` + `self.faiss_index.add()`. | Índice FAISS en RAM (32,596 dimensiones). | En runtime se crea en RAM; `indice_faiss.index` en disco debe sincronizarse explícitamente. |
| **6. Construcción de Consulta** | `query_builder.py` | Consulta usuario + Macro-Sistema + Top ML. | Concatenación de texto: síntoma, nombre del macro-sistema y nombres de fallas predictivas. | String de consulta enriquecida. | Si la predicción ML inicial es errónea, puede sesgar la consulta hacia el sistema incorrecto. |
| **7. Expansión Léxica** | `MotorRAG._expandir_consulta` | Consulta enriquecida. | Sustitución por diccionario determinista de DTCs (ej. P0301 $\rightarrow$ bujías misfire) y jerga peruana. | Consulta expandida ($<4000$ caracteres). | Diccionario estático cableado; no cubre códigos DTC propietarios B, C, U de fabricante. |
| **8. Recuperación Primaria** | `MotorRAG.faiss_index.search` | Vector TF-IDF de consulta normalizado $L_2$. | Búsqueda por producto interno exacto ($k=25$). | Top 25 índices y similitudes preliminares. | Vocabulario TF-IDF puro sufre dispersión léxica ante sinónimos mecánicos ausentes. |
| **9. Re-ranking Multiseñal** | `relevance_filter.py` | 25 candidatos + DTCs + Macro ML + Confianza. | Ponderación adaptativa: DTC $\times 3.50$, Macro $\times 1.60$ (o supresión $\times 0.35/0.80$), Fallas Top ML. | Candidatos reordenados con similitud normalizada $[0, 1]$. | Si la metadata tiene la `falla` errónea (los 10 casos), la bonificación ML premia al candidato incorrecto. |
| **10. Inyección en Pipeline** | `text_processor.py` | Top 1 candidato (`cuerpo`, `titulo`, `similitud`). | Paso a `PoliticaFusionDiagnostica` y síntesis final en `generar_respuesta_con_metadatos`. | Reporte al mecánico vía WhatsApp / Web. | Si el RAG no entrega descarte ni seguridad, el LLM debe deducirlos sin anclaje normativo. |

### Respuestas a Preguntas Críticas del Pipeline:

1. **¿Cambiar solamente `metadatos_manuales.json` es suficiente?**
   - **SÍ**, para corregir fallas de clasificación (`falla`, `sistema`, `codigos_dtc`) que afectan el re-ranking multiseñal. Dado que `TfidfVectorizer` solo procesa `titulo` y `cuerpo`, modificar los atributos semánticos de la metadata no altera los vectores ni el índice FAISS.
   - **NO**, si se modifica el `titulo` del procedimiento en la metadata, ya que `titulo` sí entra en la matriz TF-IDF y alteraría los vectores.
2. **¿El índice debe reconstruirse si cambia únicamente metadata?**
   - **NO**. Los vectores de FAISS corresponden a las palabras del título y cuerpo de los archivos `.txt`. La metadata externa no forma parte del espacio vectorial.
3. **¿El índice debe reconstruirse si cambia el texto de un documento?**
   - **SÍ, OBLIGATORIAMENTE**. Cualquier adición, edición o eliminación de texto altera las frecuencias de términos ($TF$), el vocabulario global y las frecuencias inversas de documento ($IDF$), cambiando los 239 vectores. Se debe reentrenar el vectorizador, regenerar el índice FAISS y reescribir `indice_faiss.index` en disco.
4. **¿Existe riesgo de desalinear posición FAISS $\leftrightarrow$ procedimiento $\leftrightarrow$ metadata?**
   - **SÍ, ES EL RIESGO MÁS SEVERO DEL SISTEMA**. En `motor_rag.py`, la asociación entre el vector de FAISS en la posición $i$ y el metadato en la posición $i$ depende de que los archivos se lean en idéntico orden determinista (`sorted(glob('**/*.txt'))`). Si se inserta un archivo nuevo o cambia el ordenamiento, los índices se desfasan y FAISS retornará el texto de una falla con los metadatos de otra. Se requiere un manifiesto con identificadores explícitos.
5. **¿Los hashes de fragmentos deben regenerarse?**
   - **SÍ**. Cada procedimiento tiene un campo `sha256_fragmento` calculado como `sha256(f'{titulo}\n{cuerpo}')`. Modificar una sola coma exige recalcular este hash para no romper `scripts/verificar_metadatos.py` ni `test_metadatos_corpus.py`.

---

## 3. PRESERVACIÓN DEL BASELINE Y ESTRATEGIA CANDIDATO / ROLLBACK

Para cumplir con los principios metodológicos de la tesis y garantizar reproducibilidad científica, el RAG actual no debe ser destruido ni sobrescrito.

### Definición de Entornos:
- **`RAG_BASELINE_F8_3`**: Representa el estado actual auditado, congelado criptográficamente en Fase 8.3.
  - Índice FAISS SHA-256: `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082`
  - Metadatos SHA-256: `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625`
- **`RAG_CANDIDATO_V1`**: Directorio y artefactos de desarrollo aislados donde se implementarán las mejoras.

### TABLA 2 — Artefactos que Deben Versionarse Juntos

| Artefacto | Rol en el Sistema | Ubicación Baseline (Fase 8.3) | Ubicación Candidata (Futura) | Mecanismo de Integridad |
|:---|:---|:---|:---|:---:|
| **Catálogo de Metadatos** | Atributos diagnósticos y trazabilidad | `machine_learning/manuals/metadatos_manuales.json` | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | SHA-256 de archivo |
| **Archivos Fuente TXT** | Chunks textuales con delimitadores | `machine_learning/manuals/**/*.txt` | `machine_learning/manuals/candidates/v1/texts/**/*.txt` | SHA-256 por fragmento |
| **Índice FAISS Binario** | Búsqueda vectorial exacta | `machine_learning/manuals/indice_faiss.index` | `machine_learning/manuals/candidates/v1/indice_faiss.index` | SHA-256 de archivo binario |
| **Vectorizador TF-IDF** | Vocabulario y pesos normalizados | Serializado en RAM en `MotorRAG` | `machine_learning/manuals/candidates/v1/vectorizador_tfidf.pkl` | Checksum pickle y n-features |
| **Manifiesto de Mapeo** | Alineación posición FAISS $\leftrightarrow$ ID | *No existía formalmente* | `machine_learning/manuals/candidates/v1/corpus_manifest.json` | Hash global y lista de IDs |
| **Filtro de Relevancia** | Lógica de re-ranking multiseñal | `backend/src/infrastructure/rag/relevance_filter.py` | Inmutable o parametrizable por configuración | Pruebas unitarias de regresión |

### Mecanismo de Rollback Instantáneo:
El backend debe permitir conmutar entre `RAG_BASELINE` y `RAG_CANDIDATO` mediante una variable de entorno en `.env`:
```bash
CARBOT_RAG_VERSION=baseline_f8_3  # O bien: candidate_v1
```
Si se detecta cualquier anomalía en el candidato, basta con restaurar la variable a `baseline_f8_3` sin necesidad de restaurar backups de base de datos ni recompilar contenedores.

---

## 4. ANÁLISIS EXHAUSTIVO DE LAS 10 METADATA INCORRECTAS

La auditoría forense descubrió 10 procedimientos con asignación errónea en el atributo `falla` de `metadatos_manuales.json`.

### TABLA 3 — Análisis Detallado de las 10 Asignaciones Incorrectas

| ID Procedimiento | Título del Procedimiento | Sistema Actual | Falla Asignada Actual | Causa Raíz del Error | Sistema Correcto | Clase Canónica C1 Correcta | ¿Es Conocimiento Transversal? | Impacto en Re-ranking |
|:---:|:---|:---:|:---|:---|:---:|:---|:---:|:---|
| **`RAG_PROC_047`** | Válvula solenoide sincronización variable VVT/OCV Kia Rio | `ELECTRICO` | Falla en motor de arranque o solenoide defectuoso | Coincidencia de la palabra 'solenoide'. | `MOTOR` | **`Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)`** (Clase 12) | No; mapeo C1 exacto. | Bonifica falsamente en fallas de arranque; penaliza en cascabeleo VVT. |
| **`RAG_PROC_060`** | Reparación de embrague electromagnético y compresor de A/C | `TRANSMISION` | Disco de embrague desgastado o patinando | Coincidencia de la palabra 'embrague'. | `CLIMATIZACION` | **`Falla en compresor de aire acondicionado o fuga de gas R134a`** (Clase 54) | No; mapeo C1 exacto. | Compite contra embrague de caja manual; se suprime en consultas de aire tibio. |
| **`RAG_PROC_061`** | Mecatrónica y embrague doble en transmisión DSG/DCT | `TRANSMISION` | Disco de embrague desgastado o patinando | Confusión entre embrague manual seco y doble embrague robotizado. | `TRANSMISION` | **`Sobrecalentamiento o solenoides en caja automatica CVT / DSG`** (Clase 38) | Parcialmente transversal a transmisiones robotizadas. | Contamina consultas de caja manual y se diluye en DSG. |
| **`RAG_PROC_067`** | Limpieza de válvulas solenoides VVT-i/CVVT y filtro OCV | `ELECTRICO` | Falla en motor de arranque o solenoide defectuoso | Coincidencia de la palabra 'solenoide'. | `MOTOR` | **`Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)`** (Clase 12) | No; mapeo C1 exacto. | Idéntico a RAG_PROC_047. |
| **`RAG_PROC_075`** | Sistema de evaporación de emisiones (EVAP) y purga de cánister | `MOTOR` | Falla en bujias o bobinas de encendido (misfire) | Regla heurística agrupó EVAP en encendido/misfire. | `MOTOR` | **`Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)`** (Clase 22) | No; mapeo C1 exacto. | Recomienda prueba EVAP de 5 PSI ante códigos P0300-P0304 de bujías. |
| **`RAG_PROC_109`** | Válvula de purga del sistema EVAP y fugas de gases | `MOTOR` | Falla en bujias o bobinas de encendido (misfire) | Regla heurística asoció fallo de ralentí con misfire. | `MOTOR` | **`Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)`** (Clase 22) | No; mapeo C1 exacto. | Idéntico a RAG_PROC_075. |
| **`RAG_PROC_113`** | Diagnóstico sistema TPMS y reaprendizaje de sensores | `MOTOR` | Falla en bujias o bobinas de encendido (misfire) | Asignación forzada por falta de clase TPMS en C1. | `SUSPENSION_CHASIS` | **NINGUNA CLASE C1 DIRECTA** (Clase C1 más cercana: *Llantas desbalanceadas*, Clase 44). | **SÍ, 100% TRANSVERSAL**. Monitoreo de presión y radiofrecuencia. | Grave contaminación: ante queja de misfire de motor sugiere calibrar TPMS. |
| **`RAG_PROC_114`** | Embrague del convertidor de par TCC en transmisión automática | `TRANSMISION` | Disco de embrague desgastado o patinando | Confusión de la palabra 'embrague' (TCC vs disco de fricción manual). | `TRANSMISION` | **`Sobrecalentamiento o solenoides en caja automatica CVT / DSG`** (Clase 38) | Transversal a cajas automáticas hidrostáticas / planetarias. | Falso positivo en pruebas de embrague patinando de caja mecánica. |
| **`RAG_PROC_142`** | Solenoide actuador de distribución variable VVT/VTC/VANOS | `ELECTRICO` | Falla en motor de arranque o solenoide defectuoso | Coincidencia de la palabra 'solenoide'. | `MOTOR` | **`Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)`** (Clase 12) | No; mapeo C1 exacto. | Idéntico a RAG_PROC_047 y 067. |
| **`RAG_PROC_154`** | Electroválvula de purga de cánister EVAP | `MOTOR` | Falla en bujias o bobinas de encendido (misfire) | Agrupación automática en encendido. | `MOTOR` | **`Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)`** (Clase 22) | No; mapeo C1 exacto. | Idéntico a RAG_PROC_075 y 109. |

---

## 5. DESACOPLAMIENTO DE LA TAXONOMÍA ML Y LA BASE DE CONOCIMIENTO RAG

Un principio arquitectónico fundamental que debe corregir el RAG candidato es la **separación estricta entre la taxonomía supervisada de clasificación (C1) y la ontología técnica del conocimiento automotriz (RAG)**.

### Fundamento Metodológico:
- **Clasificador C1**: Modelo probabilístico supervisado que asigna probabilidades sobre un espacio discreto y cerrado de 61 clases ($Y \in \{1..61\}$) para determinar la avería más probable a partir del relato del síntoma.
- **Corpus RAG**: Base de conocimiento técnico de ingeniería automotriz que describe subsistemas, piezas, tolerancias, pruebas físicas, circuitos eléctricos y normas de seguridad.

> [!WARNING]
> **El Error Conceptual Detectado**: Forzar a que cada documento técnico tenga como clave primaria obligatoria una de las 61 etiquetas de C1 obligó a meter 'TPMS' en 'Misfire'. La realidad física de un taller contiene subsistemas auxiliares (TPMS, redes multiplexadas CAN bus, fusileras, bombas de vacío) que son transversales a múltiples fallas.

### Modelo de Mapeo Desacoplado Propuesto:
- Cada procedimiento tendrá atributos taxonómicos independientes de C1: `system`, `subsystem`, `component`, `procedure_type`.
- La vinculación con C1 se realiza mediante:
  - `primary_class`: Clase canónica principal si existe coincidencia directa 1-a-1 (ej. Clase 12 para VVT). Si es conocimiento transversal, este campo se fija en `null`.
  - `related_classes`: Lista de clases canónicas para las cuales este procedimiento sirve como **prueba diferencial o criterio de descarte** (ej. para TPMS: `['Llantas desbalanceadas o desalineadas']`).

---

## 6. DISEÑO DEL SCHEMA RAG CANDIDATO (`schema_v2`)

Se especifica el schema JSON estructurado para el catálogo de metadatos candidato:

### TABLA 4 — Especificación del Schema RAG Candidato

| Categoría | Nombre del Campo | Tipo de Dato | Regla | Descripción Técnica | Ejemplo en Taller |
|:---|:---|:---:|:---:|:---|:---|
| **Identificación** | `doc_id` | `string` | **OBLIGATORIO** | Identificador unívoco del procedimiento. | `"RAG_PROC_047"` |
| | `chunk_id` | `string` | **OBLIGATORIO** | Identificador del bloque decisional. | `"RAG_PROC_047_CHK01"` |
| | `title` | `string` | **OBLIGATORIO** | Título técnico normalizado. | `"DIAGNÓSTICO DE VÁLVULA SOLENOIDE VVT..."` |
| **Procedencia** | `source` | `string` | **OBLIGATORIO** | Ruta o nombre del documento base. | `"manual_kia_rio.txt"` |
| | `source_type` | `string` | **OBLIGATORIO** | `OEM_MANUAL`, `SAE_ISO_STANDARD`, `AFTERMARKET_TECH`.| `"OEM_MANUAL"` |
| | `organization` | `string` | **OBLIGATORIO** | Entidad u organización técnica emisora. | `"Kia Motors Corporation"` |
| | `url` | `string` | OPCIONAL | Enlace o portal oficial de consulta. | `"https://www.kiatechinfo.com"` |
| | `license` | `string` | **OBLIGATORIO** | Términos de uso y licenciamiento de investigación. | `"Investigación Académica / Tesis"` |
| | `version` | `string` | **OBLIGATORIO** | Versión documental del procedimiento. | `"2.0"` |
| | `publication_date` | `string` | OPCIONAL | Fecha original del manual OEM (ISO 8601). | `"2020-03-15"` |
| | `ingestion_date` | `string` | **OBLIGATORIO** | Fecha de indexación en el corpus (ISO 8601). | `"2026-09-17"` |
| **Taxonomía** | `system` | `string` | **OBLIGATORIO** | Macro-sistema canónico (`MOTOR`, `FRENOS`, etc.). | `"MOTOR"` |
| | `subsystem` | `string` | **OBLIGATORIO** | Subsistema mecánico/eléctrico específico. | `"distribucion_variable"` |
| | `component` | `string` | **OBLIGATORIO** | Pieza o componente físico objetivo. | `"valvula_solenoide_ocv"` |
| | `primary_class` | `string` | OPCIONAL | Clase C1 exacta asociada (o `null`). | `"Falla en sistema de sincronizacion variable..."` |
| | `related_classes` | `list[string]` | **MULTIVALOR** | Clases C1 vinculadas como diagnóstico diferencial. | `["Falla en bujias o bobinas...", ...]` |
| | `procedure_type` | `string` | **OBLIGATORIO** | `COMPROBACION_METROLOGICA`, `DESCARTE`, `REPARACION`. | `"COMPROBACION_METROLOGICA"` |
| **Cuadro Clínico** | `symptoms` | `list[string]` | **MULTIVALOR** | Lista de síntomas observables en taller. | `["cascabeleo en aceleración", "ralentí inestable"]` |
| | `customer_language`| `list[string]` | **MULTIVALOR** | Expresiones y quejas coloquiales del conductor. | `["suena como matraca al acelerar"]` |
| | `dtc_codes` | `list[string]` | **MULTIVALOR** | Códigos OBD-II / DTC directamente asociados. | `["P0011", "P0016"]` |
| **Cadena Diagnóstica**| `diagnostic_questions`| `list[string]` | **MULTIVALOR** | Preguntas discriminantes dirigidas al mecánico. | `["¿El cascabeleo ocurre en frío o motor caliente?"]`|
| | `test_description` | `string` | **OBLIGATORIO** | Protocolo de prueba física paso a paso. | *Texto del procedimiento técnico* |
| | `tools_required` | `list[string]` | **MULTIVALOR** | Herramientas e instrumental metrológico. | `["multimetro_digital", "manometro_presion_aceite"]`|
| | `preconditions` | `string` | OPCIONAL | Estado del vehículo previo al ensayo. | `"Motor a temperatura de régimen (85°C), apagado"` |
| | `expected_quantity`| `string` | OPCIONAL | Parámetro numérico o rango de referencia. | `"6.8 a 8.2"` |
| | `units` | `string` | OPCIONAL | Unidad física normalizada (`V`, `PSI`, `Ohm`, `bar`). | `"ohm"` |
| | `possible_results` | `list[string]` | **MULTIVALOR** | Resultados típicos del ensayo. | `["<6 ohm (corto)", "7.5 ohm (normal)", "infinito"]`|
| | `interpretation` | `string` | **OBLIGATORIO** | Significado físico de cada lectura. | *'Si marca infinito, bobina abierta; cambiar OCV'* |
| | `reinforces` | `string` | OPCIONAL | Evidencia que confirma la hipótesis. | `"Resistencia fuera de rango confirma actuador trabado"` |
| | `discards` | `string` | **OBLIGATORIO** | Condición que descarta la pieza sin sustituirla. | `"Si marca 7.5 ohm y pulsa con 12V, solenoide OK"` |
| | `next_action` | `string` | **OBLIGATORIO** | Siguiente paso condicional secuencial. | `"Medir presión de aceite en culata (>18 PSI ralentí)"`|
| **Alcance Vehicular**| `vehicle_scope` | `string` | **OBLIGATORIO** | `UNIVERSAL`, `BRAND_SPECIFIC`, `ENGINE_SPECIFIC`. | `"ENGINE_SPECIFIC"` |
| | `make` | `string` | OPCIONAL | Marca específica aplicable (o `"MULTIMARCA"`). | `"Kia"` |
| | `model` | `string` | OPCIONAL | Modelo específico aplicable. | `"Rio"` |
| | `engine_code` | `string` | OPCIONAL | Código de motor aplicable. | `"Kappa 1.4L MPI"` |
| | `requires_oem_spec`| `boolean` | **OBLIGATORIO** | Bandera de advertencia de tolerancia específica. | `true` |
| **Seguridad** | `safety_level` | `string` | **OBLIGATORIO** | `LOW`, `MODERATE`, `HIGH`, `SPECIALIST_ONLY`. | `"MODERATE"` |
| | `safety_warning` | `string` | OPCIONAL | Advertencia explícita de seguridad y EPP. | `"Esperar enfriamiento de culata para evitar quemaduras"`|
| **Integridad** | `source_fragment_hash`| `string` | **OBLIGATORIO** | Hash SHA-256 del fragmento textual exacto. | `"a5c04f472297a1ed..."` |

---

## 7. CLASIFICACIÓN DE VALORES TÉCNICOS Y REGLA DE ESPECIFICACIÓN OEM

El RAG candidato debe erradicar la presentación de valores técnicos de un compendio como si fueran leyes universales.

### Taxonomía de Parámetros Físicos:
1. **UNIVERSAL**: Invariante por leyes físicas o normas electrónicas estándar.
   - Masa vehicular: $0.0\text{ V}$.
   - Voltaje de referencia de sensores analógicos: $5.0\text{ V} \pm 0.1\text{ V}$.
   - Rango de voltaje de sensor de oxígeno circonio convencional: $100\text{ a } 900\text{ mV}$.
   - Relación estequiométrica de gasolina: $14.7:1$ (Lambda $\lambda = 1.0$).
2. **ESTÁNDAR GENERAL (Requiere contextualización)**:
   - Presión de riel de inyección multipunto (MPI): $45 \text{ a } 55\text{ PSI}$ (válido para aspirados comunes, pero NO para inyección directa GDI que opera a $500 - 2,500\text{ PSI}$).
   - Voltaje de alternador en carga: $13.8 \text{ a } 14.4\text{ V}$ (en vehículos con alternador inteligente / Smart Charge con batería EFB/AGM puede variar de $12.2\text{ V}$ a $14.9\text{ V}$ dinámicamente).
   - Resistencia de inyectores MPI: $12 \text{ a } 16\ \Omega$ (en inyectores de baja impedancia o GDI pico-sostenido es de $1.5 \text{ a } 3\ \Omega$).
3. **DEPENDIENTE DEL MOTOR / VEHÍCULO (`requires_oem_spec = true`)**:
   - Luz de válvulas en frío (admisión/escape).
   - Torques de apriete de culata y bielas (grados angulares).
   - Tolerancia de alabeo de discos de freno ($0.03\text{ a } 0.05\text{ mm}$ según fabricante).
   - Presión de neumáticos recomendada (marcada en parante de puerta).
   - Resistencia de sensor de temperatura de refrigerante ECT (curva NTC dependiente del fabricante).
4. **DEPENDIENTE DE CONDICIONES DE PRUEBA**:
   - Presiones de manifold de A/C (depende fuertemente de la temperatura ambiental exterior: no es lo mismo diagnosticar A/C a 18°C que a 36°C en verano).

> [!IMPORTANT]
> **Directiva de Generación Futura**: Cuando `requires_oem_spec = true`, el RAG debe inyectar obligatoriamente la cláusula: *'Valor referencial para sistemas convencionales. Verificar tolerancia exacta en manual OEM del fabricante para {marca}/{modelo}/{motor}'*.

---

## 8. PLAN ESPECÍFICO PARA LA CLASE AIRE ACONDICIONADO

Se aborda la omisión detectada en la auditoría: **'El vehículo enfría bien en carretera pero sale aire tibio detenido o en tráfico'**.

### TABLA 7 — Plan de Cadena Diagnóstica Dinámica para A/C

| Paso Diagnóstico | Acción / Protocolo de CarBot | Instrumento / Inspección | Condición o Lectura Posible | Interpretación Técnica Rigurosa | Siguiente Acción Guiada |
|:---:|:---|:---|:---|:---|:---|
| **1. Síntoma Reportado** | Recepción de queja: *'Enfría circulando, pero parado no enfría nada'* | Conversación técnica con mecánico | Auto detenido en ralentí; A/C encendido en LOW. | Falla de intercambio térmico en condensador o baja eficiencia del compresor a bajas RPM. | Solicitar verificación del motoventilador frontal. |
| **2. Pregunta Discriminante** | CarBot pregunta: *'¿Al activar el A/C con motor en ralentí, enciende el electroventilador frontal del condensador en velocidad baja o alta?'* | Inspección visual y auditiva en vano motor | - Caso A: Electroventilador NO gira.<br>- Caso B: Electroventilador gira con fuerza.<br>- Caso C: Gira muy lento / intermitente. | - Caso A: Falla eléctrica de ventilación forzada.<br>- Caso B: Condensador tapado externamente o compresor desgastado.<br>- Caso C: Resistencia PWM o carbones gastados. | Proceder a la prueba eléctrica o manométrica según corresponda. |
| **3. Comprobación Física 1** | Si el electroventilador no enciende: comprobar relé y alimentación. | Multímetro digital en conector del motoventilador | - Llegan 12V pero motor no gira.<br>- No llegan 12V en terminal positivo. | - Si llegan 12V: motor del electroventilador quemado.<br>- Si no llegan 12V: fusible quemado o módulo PWM de control averiado. | Descartar motor aplicando 12V directos de batería con cables puente. |
| **4. Comprobación Física 2** | Si el ventilador funciona normalmente: conectar manifold de manómetros. | Manifold de A/C en puertos de servicio L y H | En ralentí (800 RPM):<br>- Baja pres.: 50-60 PSI (muy alta).<br>- Alta pres.: 120-140 PSI (muy baja). | Pérdida de rendimiento volumétrico del compresor: válvulas de lengüeta internas con fuga o desgaste de anillos de pistón a bajas RPM. | Acelerar el motor a 2,000 RPM sostenidas. |
| **5. Interpretación Dinámica** | Comparar presiones a 800 RPM vs 2,000 RPM. | Manómetros en aceleración | Al acelerar a 2,000 RPM:<br>- Baja cae a 30 PSI.<br>- Alta sube a 190 PSI y enfría. | **CONFIRMA DESGASTE DE COMPRESOR**. El régimen de giro compensa la fuga interna de compresión. | Recomendar reemplazo de compresor, filtro desecante y válvula de expansión TXV. |
| **6. Descarte de Condensador Sucio**| Si la presión de alta se dispara a >300 PSI en ralentí y el compresor corta. | Termómetro láser en entrada vs salida de condensador | Condensador saturado de barro/insectos entre aletas. | El refrigerante no condensa por falta de paso de aire; el presostato corta por sobrepresión. | Lavado cuidadoso a baja presión del condensador antes de cambiar piezas. |

---

## 9. MATRIZ DE ESTADO Y COMPONENTES FALTANTES EN LAS 61 CLASES

Se audita clase por clase qué componentes de razonamiento diagnóstico deben agregarse en la fase de implementación.

### TABLA 5 — Estado de Cadena Diagnóstica y Faltantes por Clase (61 Clases Canónicas)

| ID | Clase Canónica C1 | Macro-Sistema | Cadena Actual | Componentes Faltantes Obligatorios a Incorporar |
|:---:|:---|:---|:---:|:---|
| 1 | Falla en bujias o bobinas de encendido (misfire) | MOTOR | **COMPLETA** | Preguntas discriminantes, Fallas similares, Siguiente comprobación |
| 2 | Bomba de gasolina quemada o con baja presion | MOTOR | **COMPLETA** | Fallas similares, Siguiente comprobación |
| 3 | Inyectores sucios o filtro de combustible obstruido | MOTOR | **COMPLETA** | Preguntas discriminantes, Fallas similares, Siguiente comprobación |
| 4 | Falla en sensor de oxigeno o mezcla rica | MOTOR | **COMPLETA** | Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 5 | Cuerpo de aceleracion o valvula IAC sucia | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 6 | Empaque de culata soplado o danado | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 7 | Falla en termostato o motoventilador de radiador | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 8 | Fuga en mangueras de refrigerante o radiador picado | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 9 | Consumo de aceite por desgaste de anillos o retenes | MOTOR | **COMPLETA** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 10 | Baja presion de aceite o bomba de aceite defectuosa | MOTOR | **COMPLETA** | Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 11 | Faja o cadena de distribucion destensada o con salto de punto | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 12 | Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 13 | Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 14 | Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 15 | Fuga en mangueras de intercooler o turbocompresor danado | MOTOR | **PARCIAL** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 16 | Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 17 | Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet) | MOTOR | **AUSENTE** | Fallas similares, Criterio de descarte, Siguiente comprobación |
| 18 | Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 19 | Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 20 | Falla en sistema Flex / Bi-combustible (Alcohol/Etanol) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 21 | Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP) | MOTOR | **PARCIAL** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP |
| 22 | Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 23 | Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430) | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 24 | Falla en regulador de presion de combustible o diafragma roto | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación |
| 25 | Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208) | MOTOR | **AUSENTE** | Preguntas discriminantes, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 26 | Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados | MOTOR | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 27 | Desgaste de pastillas y zapatas de freno | FRENOS | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 28 | Discos de freno alabeados o desgastados | FRENOS | **PARCIAL** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 29 | Falla en servofreno (booster) o linea de vacio | FRENOS | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 30 | Fuga hidraulica o aire en el sistema de frenos | FRENOS | **COMPLETA** | Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 31 | Falla en sensor de velocidad de rueda ABS | FRENOS | **COMPLETA** | Preguntas discriminantes, Siguiente comprobación |
| 32 | Falla en sistema de frenado regenerativo (EV / Hibridos) | FRENOS | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 33 | Caliper de freno trabado o mordaza pegada (piston agarrotado) | FRENOS | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 34 | Disco de embrague desgastado o patinando | TRANSMISION | **AUSENTE** | Preguntas discriminantes, Siguiente comprobación, Tolerancia OEM específica |
| 35 | Falla en bombin o bomba hidraulica de embrague | TRANSMISION | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 36 | Falta o degradacion de aceite de caja de cambios | TRANSMISION | **COMPLETA** | Preguntas discriminantes, Siguiente comprobación, Tolerancia OEM específica |
| 37 | Rodajes de caja mecanica o diferencial gastados | TRANSMISION | **PARCIAL** | Preguntas discriminantes, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 38 | Sobrecalentamiento o solenoides en caja automatica CVT / DSG | TRANSMISION | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 39 | Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW) | TRANSMISION | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 40 | Desgaste en collarin de empuje o crapodina de embrague | TRANSMISION | **PARCIAL** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 41 | Rodajes de transmision manual o eje primario gastados | TRANSMISION | **AUSENTE** | Preguntas discriminantes, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 42 | Amortiguadores reventados o bujes de suspension gastados | SUSPENSION_CHASIS | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 43 | Juntas homocineticas o palieres danados | SUSPENSION_CHASIS | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 44 | Llantas desbalanceadas o desalineadas | SUSPENSION_CHASIS | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 45 | Cremallera de direccion asistida con holgura o fuga | SUSPENSION_CHASIS | **COMPLETA** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 46 | Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura) | SUSPENSION_CHASIS | **AUSENTE** | Preguntas discriminantes, Criterio de descarte, Siguiente comprobación |
| 47 | Alternador defectuoso o placa de diodos quemada | ELECTRICO | **AUSENTE** | Preguntas discriminantes, Siguiente comprobación |
| 48 | Bateria descargada o bornes sulfatados | ELECTRICO | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 49 | Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos) | ELECTRICO | **COMPLETA** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 50 | Fallo en inversor de corriente IGBT o motor electrico (EV) | ELECTRICO | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 51 | Foco o falla en sistema de refrigeracion de bateria/inversor (EV) | ELECTRICO | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 52 | Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados) | ELECTRICO | **COMPLETA** | Preguntas discriminantes, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 53 | Fuga parasita de corriente en reposo (consumo nocturno de bateria) | ELECTRICO | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 54 | Falla en compresor de aire acondicionado o fuga de gas R134a | CLIMATIZACION | **COMPLETA** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 55 | Falla electrica del cierre centralizado o actuador de puerta | CARROCERIA_NEUMATICA | **AUSENTE** | Preguntas discriminantes, Fallas similares, Siguiente comprobación, Tolerancia OEM específica |
| 56 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | CARROCERIA_NEUMATICA | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 57 | Elevalunas electrico o guaya de alzacristales rota o trabada | CARROCERIA_NEUMATICA | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 58 | Limpiaparabrisas o motor pluma quemado | CARROCERIA_NEUMATICA | **AUSENTE** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 59 | Fugas de aire o fallos en el sistema de frenos neumático (Camiones) | CARROCERIA_NEUMATICA | **PARCIAL** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Advertencia de seguridad/EPP, Tolerancia OEM específica |
| 60 | Válvula de freno de aire o secador APS obstruido (Camiones) | CARROCERIA_NEUMATICA | **PARCIAL** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |
| 61 | Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire) | CARROCERIA_NEUMATICA | **PARCIAL** | Preguntas discriminantes, Fallas similares, Criterio de descarte, Siguiente comprobación, Tolerancia OEM específica |

---

## 10. MATRIZ DE PRIORIZACIÓN DE INTERVENCIÓN (P0 A P4)

No todas las clases requieren la misma urgencia. Se estructuran 5 niveles de prioridad basados en riesgo humano, contaminación de retrieval y frecuencia en taller:

### TABLA 6 — Niveles de Prioridad para la Mejora del RAG

| Nivel | Denominación | Criterio de Inclusión | Clases / Procedimientos Afectados | Justificación Técnica |
|:---:|:---|:---|:---|:---|
| **P0** | **SEGURIDAD CRÍTICA** | Riesgo de muerte, electrocución, amputación por fluido a alta presión, incendio o pérdida total de control del vehículo. | • Vehículos Híbridos/EV (Clases 49, 50, 51)<br>• Common Rail Diésel 1,600+ bar (Clase 19)<br>• Combustible presurizado (Clases 2, 24)<br>• Refrigerante caliente (Clases 7, 8)<br>• Cámaras Maxi-Brake camiones (Clase 61)<br>• Frenos hidráulicos (Clases 27, 30) | Un asistente de IA que omita advertir sobre alta tensión o microchorros diésel es un riesgo inaceptable para la integridad del técnico. |
| **P1** | **METADATA Y CONTAMINACIÓN DE RETRIEVAL** | Errores de asignación semántica en el catálogo que distorsionan directamente el re-ranking multiseñal de producción. | • Las 10 asignaciones erróneas (VVT, EVAP, Compresor A/C, DSG, TCC, TPMS)<br>• 2 chunks stub de 56 caracteres (Versa y Corolla) | Corregir estas etiquetas repara inmediatamente el re-ranking en producción sin necesidad de alterar código ni modelos ML. |
| **P2** | **CADENA DIAGNÓSTICA EN GRUPOS CONFUNDIBLES** | Averías de alta recurrencia en taller que presentan síntomas similares y requieren preguntas discriminantes y pruebas de descarte. | • Grupo A: Combustible (Bomba vs Inyectores vs Regulador vs FSCM)<br>• Grupo B: Encendido/Ralentí (Misfire vs IAC vs Compresión vs Inyector)<br>• Grupo C: Vibraciones (Discos vs Balanceo vs Rodaje vs Palier)<br>• Grupo D: Eléctrico (Batería vs Alternador vs Fuga vs Arranque)<br>• Grupo E: Embrague (Disco vs Collarín vs Bombín)<br>• Caso especial A/C (Carretera vs Detenido) | Resuelve el 70% de las consultas reales de taller y evita que CarBot entre en bucles de preguntas redundantes. |
| **P3** | **COBERTURA Y COMPLETITUD DIAGNÓSTICA** | Clases con cadena diagnóstica 'AUSENTE' pero sin riesgo crítico de seguridad. | • 30 clases restantes con cadena ausente (Dirección asistida, amortiguadores, limpiaparabrisas, caja manual, sensores CKP/CMP, etc.) | Eleva la completitud del corpus del 21.3% actual al 100% de clases con razonamiento clínico completo. |
| **P4** | **MEJORA EVOLUTIVA DE INFRAESTRUCTURA** | Optimizaciones de arquitectura, integración de bases externas y modelos de embedding avanzados. | • Catálogo SQLite de DTCs (18,805 códigos)<br>• Evaluación de embeddings densos multilingües<br>• Enriquecimiento con boletines TSB de NHTSA | Mejoras de largo plazo para la fase posterior a la tesis experimental. |

---

## 11. PLAN DE SEGURIDAD INDUSTRIAL Y PROTOCOLOS DE TALLER

Se diseña la política de clasificación de seguridad documental que regirá todo el contenido del RAG candidato:

### TABLA 8 — Protocolos de Seguridad por Nivel de Riesgo

| Nivel de Seguridad | Definición | Requisitos de EPP Obligatorios | Procedimientos Afectados | Protocolo de CarBot ante el Mecánico |
|:---:|:---|:---|:---|:---|
| **`LOW`** | Intervenciones no invasivas sin riesgo de contacto eléctrico ni fluidos peligrosos. | Gafas de seguridad básicas con protección lateral. | Escaneo OBD-II, inspección visual de fajas, prueba de luces, filtro de cabina antipolen, switch de elevalunas. | Provee el procedimiento directamente sin advertencias invasivas. |
| **`MODERATE`** | Intervenciones mecánicas convencionales o sistema eléctrico de 12V de baja potencia. | Guantes de nitrilo/mecánicos, gafas de impacto, calzado con puntera de seguridad. | Cambio de pastillas de freno, bujías de encendido, limpieza de cuerpo mariposa, batería de 12V, amortiguadores. | Incluye advertencias estándar de soporte de carga con caballetes y desconexión de borne negativo. |
| **`HIGH`** | Intervenciones con fluidos presurizados, calor extremo, sustancias corrosivas o energía mecánica almacenada. | Guantes de cuero/nitrilo grueso, careta facial completa, mandil resistente a hidrocarburos. | • **Gasolina**: despresurizar riel extrayendo fusible de bomba antes de abrir acoples.<br>• **Refrigerante**: motor $<40^\circ\text{C}$ antes de abrir radiador.<br>• **A/C**: manifold con sellos herméticos anti-congelación.<br>• **Maxi-Brake**: perno de destrabe instalado antes de desmontar cámara de freno. | **BLOQUE DE SEGURIDAD OBLIGATORIO** al inicio de la respuesta antes de describir cualquier paso técnico. |
| **`SPECIALIST_ONLY`** | Intervenciones de Alta Tensión ($>60\text{V DC}$) en vehículos Híbridos (HEV/PHEV) y Eléctricos Puros (BEV). | Guantes dieléctricos Clase 0 ($1,000\text{V}$) certificados con prueba de inflado previa y sobreguante de cuero; multímetro CAT III $1,000\text{V}$ / CAT IV $600\text{V}$. | Desconexión de tapón de servicio naranja (Service Plug), apertura de inversor IGBT, batería de tracción HV, compresor de A/C eléctrico naranja de 200V-650V. | **ADVERTENCIA EXTREMA**: Indica que la intervención exige técnico certificado en HV. Si el mecánico no confirma tener equipo dieléctrico, CarBot no emite instrucciones de desarmado. |

---

## 12. EVALUACIÓN Y GOBERNANZA DE FUENTES EXTERNAS

Para evitar la incorporación indiscriminada de datos que contamine el RAG o infrinja reglas de tesis, se establece una matriz de gobernanza documental:

### TABLA 9 — Matriz de Fuentes Candidatas y su Función Permitida

| Fuente de Información | Categoría Metodológica | Función Técnica Permitida | Función Estrictamente Prohibida | Criterio de Validación Previa |
|:---|:---:|:---|:---|:---|
| **Manuales de Taller Oficiales OEM** (Toyota TIS, Nissan TechInfo, Hyundai GSW) | **FUENTE PRIMARIA** | Extracción de tolerancias exactas, torques de apriete, diagramas de pines y procedimientos metrológicos paso a paso. | NINGUNA (Fuente de máxima autoridad técnica). | Verificación de número de publicación y edición oficial. |
| **Normas SAE e ISO** (SAE J1939, J2012, ISO 14229 UDS) | **NORMA TÉCNICA** | Definiciones estandarizadas de códigos DTC genéricos (P0xxx) y modos de diagnóstico de escáner. | No usar como sustituto de procedimientos específicos de montaje mecánico. | Verificación de código de estándar oficial. |
| **Bases de Datos DTC Especializadas** (DTC Database, OBDex) | **CATÁLOGO ESTRUCTURADO** | Provisión de definiciones canónicas, subsistema asociado y severidad para lookup relacional $O(1)$. | **PROHIBIDO indexar como texto masivo en FAISS**. | Filtrado de duplicados y homologación de terminología en español. |
| **Manuales de Fabricantes Tier-1** (Bosch, Denso, Delphi, Valeo, ZF, Schaeffler) | **FUENTE PRIMARIA DE COMPONENTES** | Procedimientos metrológicos de componentes de inyección Common Rail, alternadores, módulos ABS y embragues. | No aplicar tolerancias universales si el vehículo equipa un sistema de otro fabricante. | Verificación de manual de servicio del fabricante de la pieza. |
| **Boletines Técnicos de Servicio (TSB) y Recalls** (NHTSA) | **CONTEXTO VEHICULAR** | Identificación de fallas recurrentes conocidas por año/marca/modelo (ej. fallo de módulo FSCM en Ford). | No generalizar un fallo endémico de un modelo a todo el parque automotor. | Verificación de código de boletín oficial NHTSA / TSB. |
| **Comunidades y Muestras Públicas** (MechanicDB, OBDb) | **FUENTE SECUNDARIA** | Extracción de sinónimos coloquiales de taller para el diccionario de consulta (`_expandir_consulta`). | **PROHIBIDO utilizarlas como procedimientos de reparación**. | Validación por técnico mecánico colegiado. |
| **Blogs Comerciales SEO y Foros no Moderados** | **NO ACEPTADA** | **NINGUNA**. Exclusión total del corpus. | Prohibido indexar contenido generado para posicionamiento web o sin autoría técnica verificable. | Descarte automático. |

---

## 13. ARQUITECTURA DE INTEGRACIÓN DE CÓDIGOS DTC

Se compara rigurosamente cómo debe gestionarse el conocimiento de códigos OBD-II / DTC:

### TABLA 10 — Comparativa de Arquitecturas para Códigos DTC

| Criterio de Comparación | Enfoque A: Indexar DTCs en FAISS | Enfoque B: Base Relacional Pura (SQLite) | Enfoque C: Modelo Híbrido en 2 Etapas (RECOMENDADO) |
|:---|:---|:---|:---|
| **Mecanismo Operativo** | Inyectar 18,805 documentos cortos en FAISS junto con los procedimientos de taller. | Crear tabla SQLite y responder únicamente la definición del código sin procedimiento. | 1. Lookup estructurado $O(1)$ en SQLite al detectar regex DTC.<br>2. Inyección de la definición oficial a la consulta RAG.<br>3. Búsqueda en FAISS con bonificación DTC $\times 3.50$. |
| **Precisión de Recuperación** | **Baja-Media**: Provoca dispersión léxica extrema en TF-IDF por colisión de términos idénticos ('Sensor O2', 'Misfire'). | **Alta para la definición**, pero **Nula para el procedimiento de reparación**. | **Máxima**: Garantiza recuperar el código exacto y el procedimiento físico completo de taller. |
| **Consumo de Memoria RAM** | Muy alto: Matriz TF-IDF crecería a más de 100,000 dimensiones; índice FAISS $>200\text{ MB}$. | Mínimo: Archivo SQLite en disco ($<15\text{ MB}$) con índices B-Tree. | Mínimo: Mantiene FAISS compacto (239-350 procedimientos) y SQLite ultraligero en disco. |
| **Riesgo de Alucinación** | Alto: El LLM recibe múltiples definiciones idénticas y fragmentadas. | Bajo: Definición cerrada estática. | Mínimo: El LLM recibe la definición oficial verificada + el procedimiento metrológico de descarte. |
| **Veredicto Técnico** | **RECHAZADO**. Destruiría la precisión del FAISS actual. | **INSUFICIENTE**. No asiste al mecánico en las pruebas de taller. | **SELECCIONADO COMO ARQUITECTURA OBJETIVO**. |

---

## 14. ESTRATEGIA FUTURA DE CHUNKING SEMÁNTICO

Se evalúa la unidad mínima de conocimiento indexable para la futura versión del RAG:

### TABLA 11 — Evaluación de Estrategias de Fragmentación (Chunking)

| Estrategia de Chunking | Tamaño Típico | Ventajas | Desventajas / Riesgos | Veredicto |
|:---|:---:|:---|:---|:---:|
| **A. Procedimiento Completo (Actual)** | 1,200 - 2,500 car. (1 chunk = 1 doc) | Mantiene todo el contexto de la pieza, síntomas, prueba y torques en un solo bloque. | Mezcla intenciones diagnósticas; vector TF-IDF promedio diluye la similitud ante preguntas específicas. | **Válido para Baseline** (mantener en Fase experimental). |
| **B. Chunking por Tokens Arbitrarios** | Fijo: 256 o 512 tokens con solapamiento | Fácil de automatizar con splitters estándar. | Corta tablas de torques a la mitad, separa advertencias de seguridad de la prueba física; inaceptable en ingeniería. | **ESTRICTAMENTE RECHAZADO**. |
| **C. Chunking Semántico por Decisión Técnica (Candidato)** | 400 - 800 car. (3-4 chunks por procedimiento vinculados a `parent_id`) | Máxima precisión de recuperación: chunk de síntomas para inicio, chunk de prueba para medición, chunk de torques para cierre. | Requiere curaduría técnica especializada y reordenador adaptativo consciente de jerarquía padre-hijo. | **SELECCIONADO PARA RAG CANDIDATO**. |

#### Estructura de Chunks Jerárquicos Propuesta:
```
PROCEDIMIENTO PADRE (RAG_PROC_047: Válvula Solenoide VVT Kia Rio)
 ├── CHUNK 1: Cuadro Clínico y Preguntas Discriminantes (Síntomas, Cascabeleo, P0011/P0016)
 ├── CHUNK 2: Comprobación Metrológica y Descarte (Resistencia 6.8-8.2 Ohm, Prueba 12V directa)
 └── CHUNK 3: Protocolo de Seguridad y Especificaciones OEM (Presión aceite >18 PSI, Torque 10 Nm)
```

---

## 15. PLAN EXPERIMENTAL DE MEJORA DEL RETRIEVAL

Para asegurar que cada cambio incremente el rendimiento de forma medible, las mejoras del retrieval deben ejecutarse mediante **estudios de ablación progresivos (un cambio a la vez)**:

### TABLA 12 — Secuencia de Pruebas de Ablación para Retrieval

| Experimento | Cambio Único Introducido | Hipótesis Técnica | Métrica Objetivo | Criterio de Éxito |
|:---:|:---|:---|:---:|:---|
| **EXP-01 (Línea Base)** | Ninguno (`RAG_BASELINE_F8_3`). | Establecer la medición de referencia sobre el nuevo benchmark independiente. | Hit@1, Hit@3, Hit@5, MRR | Hit@1 = 64.6%, Hit@5 = 92.7%, MRR = 0.758. |
| **EXP-02** | Corrección de las 10 asignaciones erróneas en `metadatos_manuales.json`. | Suprimir la penalización errónea de ML en VVT, EVAP, A/C y DSG elevará Hit@1 en esas clases. | Hit@1 en clases corregidas y global | Aumento de Hit@1 global de $\ge +4.0\%$ (alcanzar $\ge 68.5\%$). |
| **EXP-03** | Reemplazo de los 2 chunks stub de 56 car. por manuales de mantenimiento reales. | Elimina ruido léxico en búsquedas de afinamiento y mantenimiento preventivo. | Hit@1 en consultas de mantenimiento | Cero fragmentos vacíos recuperados en Top 5. |
| **EXP-04** | Integración del Lookup relacional DTC previo a la consulta FAISS. | Coincidencia determinista $O(1)$ de códigos DTC elevará drásticamente el ordenamiento en consultas con escáner. | Hit@1 en consultas con DTC | Hit@1 en subconjunto con DTC $\ge 95.0\%$. |
| **EXP-05** | Incorporación de términos de descarte y cuadro clínico en chunks de texto. | Enriquecer el vocabulario de síntomas específicos mejora la recuperación léxica en consultas coloquiales. | Hit@3 y Hit@5 global | Hit@5 global $\ge 96.0\%$. |
| **EXP-06 (Avanzado)** | Evaluación de Dense Embeddings multilingües (`all-MiniLM-L6-v2`) vs TF-IDF. | Los embeddings semánticos reducen la fragilidad ante variaciones léxicas sin códigos DTC. | MRR y Hit@1 en consultas sin DTC | Aumento de MRR $\ge +0.06$ frente a TF-IDF sin degradar latencia ($<50\text{ ms}$). |

---

## 16. PROTOCOLO DE EVALUACIÓN Y BENCHMARK INDEPENDIENTE

> [!CAUTION]
> **REGLA METODOLÓGICA DE TESIS**: Queda terminantemente prohibido utilizar `TEST10` o los registros de campo de la tesis para evaluar o afinar el RAG. Se debe construir un banco de pruebas RAG estrictamente desacoplado.

### TABLA 13 — Especificación del Benchmark RAG Independiente (120 Consultas)

| Dimensión de Prueba | N.º Casos | Propósito de Evaluación | Ejemplo de Consulta de Prueba | Métrica Requerida |
|:---|:---:|:---|:---|:---:|
| **1. Cobertura Canónica C1** | 61 | Verificar recuperabilidad básica de cada una de las 61 clases. | *'Procedimiento de comprobación para Bomba de gasolina quemada...'* | Hit@1 $\ge 70\%$ |
| **2. Jerga Técnica de Taller** | 10 | Evaluar capacidad con vocabulario técnico formal de mecánicos. | *'Caída de tensión en solenoide terminal 50 motor de arranque'* | Hit@1 $\ge 80\%$ |
| **3. Lenguaje Coloquial Conductor**| 10 | Evaluar traducción de quejas subjetivas sin términos mecánicos. | *'Mi carro cabecea feo en subida y huele a huevo podrido'* | Hit@3 $\ge 85\%$ |
| **4. Formato WhatsApp / Chatbot** | 10 | Evaluar resiliencia ante mensajes cortos sin signos de puntuación. | *'hola maestro no prende mi yaris da arranque pero nada'* | Hit@3 $\ge 80\%$ |
| **5. Consultas con Código DTC** | 10 | Evaluar respuesta determinista ante códigos estándar OBD-II. | *'Escaner arrojo codigo P0011 sincronizacion variable banco 1'* | Hit@1 $\ge 95\%$ |
| **6. Averías Mecánicas Puras** | 10 | Evaluar consultas sin DTC donde NUNCA debe sugerirse escaneo. | *'Pedal de freno vibra fuerte solo cuando freno a alta velocidad'* | Hit@1 $\ge 85\%$ |
| **7. Grupos Confundibles A–E** | 10 | Evaluar capacidad de recuperar el procedimiento discriminante correcto. | *'Zumbido que aumenta al doblar a la derecha pero calla al frenar'* | Hit@1 $\ge 80\%$ |
| **8. Caso A/C Carretera vs Parado**| 3 | Evaluar el caso térmico específico de electroventilador y condensador. | *'El aire acondicionado enfria en pista pero en semaforos bota tibio'* | Hit@1 $\ge 90\%$ |
| **9. Seguridad de Alto Riesgo** | 5 | Evaluar recuperación de procedimientos con protocolos EPP y despresurización. | *'Procedimiento para desmontar riel de inyectores common rail hilux'* | 100% con aviso EPP |
| **10. Mediciones Físicas Numéricas**| 5 | Evaluar manejo de valores numéricos de presión, voltaje y resistencia. | *'Presion de combustible marca 52 psi con switch en contacto'* | Hit@1 $\ge 80\%$ |
| **11. Información Insuficiente** | 3 | Evaluar comportamiento ante quejas ambiguas que requieren aclaración. | *'Mi auto hace un ruido raro'* | Coincidencia baja / Aclaración |
| **12. Descarte / Confirmación** | 3 | Evaluar respuesta ante mecánico que ya realizó la primera medición. | *'Medí bobina de solenoide y marca 7.5 ohm que prueba sigue'* | Siguiente acción correcta |
| **TOTAL** | **120** | **Evaluación integral de 360 grados del subsistema RAG** | | **Hit@1 $\ge 75\%$, MRR $\ge 0.82$** |

---

## 17. PLAN DE MIGRACIÓN CONTROLADA EN 9 ETAPAS (A A I)

### TABLA 14 — Fases de la Migración Controlada RAG

| Etapa | Denominación | Actividades Técnicas Específicas | Artefacto Producido | Criterio de Control / Gate |
|:---:|:---|:---|:---|:---:|
| **ETAPA A** | **Congelamiento Formal Baseline** | Snapshot inmutable de `machine_learning/manuals/` y verificación de hashes SHA-256 de Fase 8.3. | `rag_baseline_manifest.json` | 100% paridad con `reporte_fase8_3_congelado.json`. |
| **ETAPA B** | **Aislamiento de Entorno Candidato** | Creación del espacio de trabajo aislado `machine_learning/manuals/candidates/v1/` sin modificar producción. | Rama git / Carpeta de staging | Cero impacto en el backend activo. |
| **ETAPA C** | **Corrección de Metadatos Críticos** | Subsanación de las 10 asignaciones erróneas y eliminación de los 2 chunks stub en la copia candidata. | `candidates/v1/metadatos_manuales.json` | Verificación sintáctica y lógica sin inconsistencias. |
| **ETAPA D** | **Implementación del Schema V2** | Migración de los 239 registros al nuevo schema enriquecido (descarte, seguridad, siguiente paso). | `candidates/v1/metadatos_schema_v2.json` | Validación estricta contra schema Pydantic. |
| **ETAPA E** | **Reconstrucción de Índices Candidatos**| Ajuste de textos en archivos `.txt`, reentrenamiento de TF-IDF y serialización de nuevo índice FAISS. | `candidates/v1/indice_faiss.index` | Creación de `corpus_manifest.json` con hashes 100% alineados. |
| **ETAPA F** | **Ejecución de Benchmark RAG** | Corrida automatizada del benchmark independiente de 120 consultas sobre Baseline y Candidato. | `benchmark_results_comparison.json` | Cero fallos de ejecución; registro de latencias. |
| **ETAPA G** | **Análisis de Ablación y Métricas** | Comparación cuantitativa (Hit@K, MRR) y cualitativa (seguridad, contradicciones, descarte). | `reporte_comparativo_rag_candidato.md` | Superar los umbrales mínimos de promoción definidos. |
| **ETAPA H** | **Revisión Ciega por Especialista** | Auditoría manual de 20 casos aleatorios por un ingeniero mecánico automotriz externo. | Acta de conformidad técnica firmada | Aprobación de pertinencia metrológica y seguridad. |
| **ETAPA I** | **Promoción a Producción o Rollback** | Si cumple todos los gates: conmutación controlada mediante variable de entorno. Si falla: rollback instantáneo. | Actualización de `.env` a versión candidata | Monitoreo de telemetría de producción sin errores. |

---

## 18. CRITERIOS PREVIOS DE PROMOCIÓN Y ROLLBACK

Los criterios de aceptación no deben acomodarse después de ver resultados experimentales; se fijan formalmente a priori:

### TABLA 15 — Criterios de Decisión para Promoción o Rollback

| Criterio de Decisión | Condición para APROBAR PROMOCIÓN | Condición para EJECUTAR ROLLBACK INMEDIATO | Tipo de Métrica |
|:---|:---|:---|:---:|
| **Hit@1 Global** | **$\ge 75.0\%$** (mejora de $+10.4$ puntos porcentuales vs 64.63%). | $< 64.0\%$ (cualquier degradación frente al baseline). | Cuantitativa |
| **Hit@3 Global** | **$\ge 90.0\%$** (mejora vs 87.80%). | $< 85.0\%$. | Cuantitativa |
| **Hit@5 Global** | **$\ge 95.0\%$** (mejora vs 92.68%). | $< 90.0\%$. | Cuantitativa |
| **Mean Reciprocal Rank (MRR)**| **$\ge 0.8200$** (mejora vs 0.7583). | $< 0.7400$. | Cuantitativa |
| **Contaminación Cruzada** | **$\le 2.0\%$** de respuestas de otro macro-sistema ante consultas con DTC. | $> 5.0\%$ de respuestas fuera de sistema con código DTC. | Cuantitativa |
| **Seguridad en Alto Voltaje / Combustible**| **100%** de presencia de advertencia de EPP y protocolo seguro en P0. | **Una sola omisión** de advertencia de seguridad en casos P0. | **Bloqueante Absoluto** |
| **Contradicciones Técnicas** | **0 contradicciones** documentadas en el corpus promovido. | Detección de especificaciones incompatibles no resueltas. | Cualitativa |
| **Latencia de Recuperación** | Tiempo promedio de recuperación en FAISS $< 15\text{ ms}$. | Latencia promedio $> 100\text{ ms}$. | Operativa |
| **Impacto en Modelo ML C1** | **Cero impacto** (exactitud y F1 de C1 inalterados). | Cualquier alteración en la salida probabilística de C1. | **Bloqueante Absoluto** |

---

## 19. REGLAS DE EXCLUSIÓN: QUÉ NO DEBE ENTRAR AL RAG

Para blindar la integridad científica y técnica de CarBot, se definen prohibiciones taxativas de admisión documental:

1. **Blogs de Marketing o SEO**: Sitios web comerciales que recopilan fallas genéricas sin diagramas, tolerancias ni procedimientos de comprobación técnica (ej. `gemacar.com/blog/`).
2. **Respuestas Sintéticas de Modelos de Lenguaje sin Validar**: Textos generados por LLMs comerciales que alucinen torques o secuencias de diagnóstico sin respaldo de un manual OEM firmado.
3. **Procedimientos Invasivos Inseguros**: Métodos empíricos de taller que violen normas de seguridad (ej. *'probar chispa de bujía acercando el cable al bloque en presencia de vapores de gasolina'*, *'abrir inyector common rail con motor en marcha'*, *'manipular batería de alto voltaje sin guantes Clase 0'*).
4. **Valores Numéricos Universales sin Modelo**: Declarar como absoluto un valor que depende de la variante de motor sin fijar `requires_oem_spec = true`.
5. **Fragmentos Duplicados o Stubs**: Textos menores a 200 caracteres que no aporten una prueba física reproducible.
6. **Documentos bajo Licencias Restrictivas Prohibidas**: Material que vulnere propiedad intelectual o que impida su explotación en proyectos de investigación académica.
7. **Muestras de Campo de la Tesis**: Queda terminantemente prohibido incorporar los 60 registros empíricos recopilados en el taller de contrastación dentro del RAG de desarrollo.

---

## 20. MATRIZ DE RIESGOS DE IMPLEMENTACIÓN Y MITIGACIÓN

### TABLA 16 — Matriz de Riesgos Técnicos y Estrategias de Mitigación

| ID Riesgo | Descripción del Riesgo Técnico | Probabilidad | Impacto | Estrategia de Mitigación Previa |
|:---:|:---|:---:|:---:|:---|
| **RSK-01** | **Desalineación posicional vector $\leftrightarrow$ metadata**: Modificar el orden de los archivos `.txt` hace que los IDs de FAISS apunten a procedimientos erróneos. | **ALTA** | **CRÍTICO** | Generar `corpus_manifest.json` con índice determinista fijado y prueba unitaria de verificación cruzada obligatoria en el pipeline de inicio. |
| **RSK-02** | **Ruptura de hashes de congelamiento en tests existentes**: Editar archivos en producción rompe `reporte_fase8_3_congelado.json` y los tests de regresión. | **ALTA** | **ALTO** | Desarrollar 100% de la versión candidata en carpeta aislada `candidates/v1/` sin tocar las rutas vigentes hasta la etapa de promoción. |
| **RSK-03** | **Degradación del clasificador ML C1**: Modificar accidentalmente el vectorizador o pipeline de ML durante la intervención del RAG. | **BAJA** | **CRÍTICO** | Aislamiento total: prohibido tocar `modelo_diagnostico.pkl`, `vectorizador_tfidf.pkl` y `modelo_ml.py`. |
| **RSK-04** | **Sobrecarga de contexto en el LLM**: Chunks excesivamente largos ($>3,000$ car.) saturan la ventana de contexto e incrementan la latencia de Gemini. | **MEDIA** | **MEDIO** | Establecer límite estricto de longitud de fragmento ($1,200 \pm 300$ caracteres / $\approx 250$ tokens). |
| **RSK-05** | **Falsa sensación de seguridad en alta tensión**: Proveer instrucciones paso a paso a usuarios sin cualificación profesional en sistemas híbridos. | **MEDIA** | **CRÍTICO** | Clasificar como `SPECIALIST_ONLY` e imponer directiva obligatoria en el prompt para exigir personal certificado antes de emitir detalles de desarmado. |
| **RSK-06** | **Dispersión léxica por proliferación de términos**: Agregar demasiados sinónimos al TF-IDF reduce el peso de las palabras clave diagnósticas. | **MEDIA** | **MEDIO** | Filtrar vocabulario con umbral mínimo de frecuencia de documento ($min\_df=2$) y pruebas de ablación controladas. |

---

## 21. PLAN CONCRETO DE CAMBIOS FUTUROS (ESPECIFICACIÓN TÉCNICA EJECUTABLE)

La siguiente tabla define los cambios atómicos y precisos que deberá ejecutar la futura fase de implementación. Cada cambio está acotado, priorizado y asociado a su prueba de validación posterior.

### TABLA 17 — Matriz de Cambios Concretos para la Futura Fase de Implementación

| ID_CAMBIO | PRIORIDAD | ARTEFACTO | RUTA | TIPO_DE_CAMBIO | MOTIVO | EVIDENCIA | RIESGO | REQUIERE_REINDEXACION | REQUIERE_FUENTE_EXTERNA | REQUIERE_VALIDACION_MANUAL | PRUEBA_POSTERIOR |
|:---:|:---:|:---|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---|
| **CHG-001** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` y `sistema` en `RAG_PROC_047` | Solenoide VVT Kia Rio asignado erróneamente a motor de arranque | `RAG_PROC_047` asignado a arranque | Medio | No | No | Sí | `test_retrieval_vvt_kia_rio` |
| **CHG-002** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` y `sistema` en `RAG_PROC_060` | Embrague de compresor A/C asignado erróneamente a embrague de transmisión | `RAG_PROC_060` asignado a transmisión | Medio | No | No | Sí | `test_retrieval_embrague_ac` |
| **CHG-003** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` en `RAG_PROC_061` | Mecatrónica DSG asignada erróneamente a disco de embrague manual | `RAG_PROC_061` asignado a embrague manual | Medio | No | No | Sí | `test_retrieval_dsg_mecatronica` |
| **CHG-004** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` y `sistema` en `RAG_PROC_067` | Solenoide VVT-i Toyota asignado a motor de arranque | `RAG_PROC_067` asignado a arranque | Medio | No | No | Sí | `test_retrieval_vvt_toyota` |
| **CHG-005** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` en `RAG_PROC_075` | Sistema EVAP cánister asignado a bujías/misfire | `RAG_PROC_075` asignado a misfire | Medio | No | No | Sí | `test_retrieval_evap_canister` |
| **CHG-006** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` en `RAG_PROC_109` | Válvula purga EVAP asignada a bujías/misfire | `RAG_PROC_109` asignado a misfire | Medio | No | No | Sí | `test_retrieval_purga_evap` |
| **CHG-007** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Reclasificar `RAG_PROC_113` a `SUSPENSION_CHASIS` transversal | Sensores de presión TPMS asignados a bujías/misfire | `RAG_PROC_113` asignado a misfire | Medio | No | No | Sí | `test_retrieval_tpms_chasis` |
| **CHG-008** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` en `RAG_PROC_114` | Embrague TCC convertidor par asignado a embrague manual | `RAG_PROC_114` asignado a embrague manual | Medio | No | No | Sí | `test_retrieval_tcc_torque_converter` |
| **CHG-009** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` y `sistema` en `RAG_PROC_142` | Solenoide VVT/VANOS asignado a motor de arranque | `RAG_PROC_142` asignado a arranque | Medio | No | No | Sí | `test_retrieval_vanos_vvt` |
| **CHG-010** | **P1** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_manuales.json` | Corregir atributo `falla` en `RAG_PROC_154` | Electroválvula cánister EVAP asignada a bujías/misfire | `RAG_PROC_154` asignado a misfire | Medio | No | No | Sí | `test_retrieval_electrovalvula_evap` |
| **CHG-011** | **P1** | Archivo TXT + Meta | `machine_learning/manuals/candidates/v1/texts/nissan/versa/2021/manual_nissan_versa.txt` | Reemplazar chunk stub de 56 car. por procedimiento de mantenimiento real | Chunk contiene solo 56 car. triviales | Longitud = 56 car. | Bajo | Sí | Sí (Manual OEM Versa) | Sí | `test_integrity_chunk_versa` |
| **CHG-012** | **P1** | Archivo TXT + Meta | `machine_learning/manuals/candidates/v1/texts/toyota/corolla/2019/manual_toyota_corolla.txt`| Reemplazar chunk stub de 56 car. por procedimiento de mantenimiento real | Chunk contiene solo 56 car. triviales | Longitud = 56 car. | Bajo | Sí | Sí (Manual OEM Corolla) | Sí | `test_integrity_chunk_corolla` |
| **CHG-013** | **P0** | Archivos TXT | `machine_learning/manuals/candidates/v1/texts/toyota/prius_hev/` | Incorporar bloque de seguridad obligatorio de Alta Tensión en EV/HV | Faltan cláusulas explícitas de EPP Clase 0 en algunos pasos | Auditoría Seguridad P0 | Alto | Sí | Sí (Norma SAE J2344) | Sí | `test_safety_high_voltage` |
| **CHG-014** | **P0** | Archivos TXT | `machine_learning/manuals/candidates/v1/texts/generales/manual_procedimientos_multimarca.txt` | Incorporar advertencia de inyección subcutánea en Common Rail (1,600+ bar) | 3 procedimientos omiten el peligro de microchorro | Auditoría Seguridad P0 | Alto | Sí | Sí (Norma ISO 2974) | Sí | `test_safety_common_rail` |
| **CHG-015** | **P0** | Archivos TXT | `machine_learning/manuals/candidates/v1/texts/generales/manual_procedimientos_multimarca.txt` | Incorporar protocolo de despresurización de línea de gasolina antes de apertura | Procedimientos de inyectores omiten paso de despresurizar | Auditoría Seguridad P0 | Medio | Sí | Sí (Manuales OEM TIS) | Sí | `test_safety_gasoline_depressurize` |
| **CHG-016** | **P2** | Archivos TXT + Meta | `machine_learning/manuals/candidates/v1/texts/generales/manual_procedimientos_multimarca.txt` | Incorporar procedimiento de diagnóstico dinámico A/C (carretera vs detenido) | Falla totalmente ausente en RAG actual | Auditoría A/C: 0 chunks cubren este síntoma | Medio | Sí | Sí (Manual OEM Denso/Toyota) | Sí | `test_retrieval_ac_condensador_ventilador` |
| **CHG-017** | **P2** | Archivos TXT | Chunks de los Grupos Confundibles A a E | Incorporar preguntas discriminantes explícitas y criterios de descarte en grupos A–E | 40 clases carecen de cadena diagnóstica completa | Auditoría Cadena: 65.6% ausente | Medio | Sí | Sí (Guías OEM de taller) | Sí | `test_diagnostic_chain_groups_a_e` |
| **CHG-018** | **P3** | Metadatos JSON | `machine_learning/manuals/candidates/v1/metadatos_schema_v2.json` | Migración de los 239 registros al formato de schema enriquecido `schema_v2` | Schema actual no soporta descarte ni nivel de seguridad estructurado | Especificación Schema V2 | Bajo | No | No | Sí | `test_schema_v2_pydantic_validation` |
| **CHG-019** | **P4** | Módulo de Base de Datos | `backend/src/infrastructure/dtc/` | Integrar lookup relacional SQLite de catálogo DTC (18,805 códigos) en el query builder | Evita saturar FAISS con miles de definiciones microscópicas | Auditoría DTC Architecture | Bajo | No | No | Sí | `test_dtc_sqlite_lookup_integration` |
| **CHG-020** | **P1** | Pipeline Build | `machine_learning/manuals/candidates/v1/corpus_manifest.json` | Generar manifiesto posicional estricto con hashes SHA-256 para indexación FAISS | Prevenir desalineación posicional vector $\leftrightarrow$ metadata | Riesgo RSK-01 | Alto | Sí | No | Sí | `test_manifest_faiss_vector_alignment` |

---

## 22. ESTADO Y DICTAMEN FINAL DEL PLAN MAESTRO

Sobre la base del análisis forense, el diseño metodológico riguroso y la articulación técnica de las 17 tablas operativas:

```
ESTADO DEL PLAN: RAG_PLAN_APROBADO_PARA_IMPLEMENTACION
```

### Justificación del Dictamen:
1. **Factibilidad Técnica Comprobada**: Todos los cambios están acotados a nivel de metadatos, textos de manuales, scripts de indexación y manifiestos, sin requerir reentrenamiento del modelo ML C1 ni modificaciones destructivas en el backend de producción.
2. **Preservación Absoluta del Baseline**: Se definió la estrategia de aislamiento en `candidates/v1/` con mecanismo de conmutación y rollback instantáneo vía configuración, garantizando paridad e inmutabilidad de Fase 8.3.
3. **Solución a las Causas Raíz Auditadas**: El plan resuelve las 10 asignaciones erróneas de metadatos, los chunks stub, la brecha térmica de A/C, los protocolos de seguridad industrial en 7 subsistemas de riesgo y define la arquitectura híbrida para códigos DTC.
4. **Criterios de Éxito Objetivos y Previamente Fijados**: Se establecieron los umbrales cuantitativos inmutables (Hit@1 $\ge 75\%$, MRR $\ge 0.82$, 100% de advertencias en P0) antes de cualquier implementación.

> [!NOTE]
> **RECORDATORIO OBLIGATORIO**: El dictamen `RAG_PLAN_APROBADO_PARA_IMPLEMENTACION` certifica que el plan es técnicamente sólido, viable y exhaustivo. **NO constituye una autorización para ejecutar cambios**. Ningún archivo del RAG operativo ha sido modificado durante esta fase.

---

*Plan maestro elaborado de forma autónoma en modo estrictamente de lectura y diseño por Antigravity AI.*
*Fin del documento.*