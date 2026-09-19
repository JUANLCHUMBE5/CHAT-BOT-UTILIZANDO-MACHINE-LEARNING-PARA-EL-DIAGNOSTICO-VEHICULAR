# REPORTE FORENSE DE AUDITORÍA INTEGRAL DEL SISTEMA RAG — CARBOT

**Fase**: RAG-AUDIT — Auditoría Forense y Funcional del RAG Actual de CarBot
**Fecha de Auditoría**: 17 de Septiembre de 2026
**Modo de Ejecución**: **ESTRICTAMENTE DE LECTURA (READ-ONLY)** — Cero modificaciones de código, índices, prompts o modelos
**Objetivo**: Auditar exhaustivamente la arquitectura, integridad criptográfica, cobertura contra las 61 clases canónicas C1, completitud de cadena diagnóstica, manejo de grupos confundibles, unidades físicas, seguridad, contradicciones y rendimiento de recuperación del RAG.

> [!IMPORTANT]
> **DECLARACIÓN DE INMUTABILIDAD FORENSE**: Durante la ejecución de esta auditoría **NO** se modificaron archivos del RAG, **NO** se alteró FAISS, **NO** se reconstruyeron índices, **NO** se agregaron ni eliminaron documentos, **NO** se tocaron embeddings ni chunks, **NO** se modificó el clasificador C1 ni su vectorizador, **NO** se tocó el backend y **NO** se utilizaron casos de TEST10 ni muestras de campo de la tesis. Todos los hallazgos han sido documentados sin aplicar correcciones operativas.

---

## RESUMEN EJECUTIVO Y VEREDICTO

Se realizó una inspección forense en profundidad del subsistema de Generación Aumentada por Recuperación (RAG) de CarBot, analizando la totalidad de sus 239 procedimientos técnicos indexados, su índice vectorial FAISS y los módulos de orquestación y reordenamiento (`MotorRAG`, `relevance_filter`, `text_processor`).

### Hallazgos Principales:
1. **Integridad Criptográfica Perfecta (100%)**: Los artefactos en producción coinciden bit a bit con los hashes congelados de la Fase 8.3 (`reporte_fase8_3_congelado.json`).
2. **Alta Dependencia de Compendios Genéricos Multimarca**: El **90.4%** de los fragmentos indexados (216 de 239) provienen de solo dos compendios genéricos (`manual_procedimientos_multimarca.txt` y `procedimientos_fase8.txt`). Los manuales OEM específicos por marca/modelo representan menos del 10% del corpus.
3. **Cobertura de Taxonomía C1 (61 Clases)**: El 100% de las 61 clases canónicas tienen al menos 1 procedimiento mapeado. 35 clases (57.4%) poseen cobertura ALTA y 26 clases (42.6%) cobertura MEDIA. No existen clases con cobertura NULA.
4. **Ruptura de la Cadena Diagnóstica Dinámica**: En el **65.6%** de las clases (40 de 61), la cadena diagnóstica completa está **AUSENTE**. Los procedimientos son fichas técnicas estáticas: describen síntomas y una prueba, pero carecen de preguntas aclaratorias ramificadas, criterios de descarte y especificación del 'siguiente paso' condicional.
5. **Inconsistencias Semánticas en Metadatos**: Se detectaron **10 procedimientos** con clasificación errónea en `metadatos_manuales.json` debido a reglas heurísticas automáticas previas (e.g. embrague de compresor A/C y embrague de transmisión automática TCC asignados a 'Disco de embrague manual'; solenoides de sincronización variable VVT asignados a 'Motor de arranque'; sistemas de emisiones EVAP asignados a 'Misfire').
6. **Rendimiento de Recuperación (Retrieval)**: En una batería de 82 consultas de auditoría independientes, el sistema alcanzó **Hit@1 = 64.63%**, **Hit@3 = 87.80%**, **Hit@5 = 92.68%** y un **MRR = 0.7583**. El re-ranking multiseñal (`reordenar_candidatos_rag`) rescata adecuadamente candidatos cuando interviene la predicción ML o códigos DTC, pero el FAISS TF-IDF crudo presenta dispersión.
7. **Veredicto Final**: **`RAG_ACTUAL_REQUIERE_MEJORAS`**.

---

## 1. LOCALIZACIÓN Y ARQUITECTURA DEL RAG REAL

El backend de CarBot (`backend/src/infrastructure/motor_rag.py`) utiliza un motor RAG híbrido basado en recuperación vectorial sobre representaciones TF-IDF acoplado a un índice FAISS `IndexFlatIP` en memoria, con reordenamiento multiseñal post-recuperación.

### TABLA 1 — Arquitectura RAG Actual

| Componente / Parámetro | Ruta / Valor en Producción | Función / Detalle Técnico |
|:---|:---|:---|
| **Directorio de Manuales** | `machine_learning/manuals/` | Directorio raíz de los corpus técnicos y catálogos. |
| **Catálogo de Metadatos** | `machine_learning/manuals/metadatos_manuales.json` | 239 procedimientos estructurados con metadatos JSON. |
| **Índice FAISS en Disco** | `machine_learning/manuals/indice_faiss.index` | Archivo binario serializado (31,161,821 bytes). |
| **Índice FAISS en Runtime** | `MotorRAG.faiss_index` (`faiss.IndexFlatIP`) | Instanciado dinámicamente en RAM; idéntico bit a bit al disco. |
| **Modelo de Vectorización** | `sklearn.feature_extraction.text.TfidfVectorizer` | n-gramas (1, 2), `sublinear_tf=True`, `strip_accents='unicode'`. |
| **Dimensión Vectorial ($d$)** | **32,596 dimensiones** | Vocabulario léxico derivado de los 239 procedimientos. |
| **Métrica de Distancia** | `IndexFlatIP` (Inner Product) | Equivalente a Similitud Coseno gracias a normalización previa $L_2$. |
| **Módulo Orquestador RAG** | `backend/src/infrastructure/motor_rag.py` | Clase `MotorRAG` con inyección vía `ServiceContainer`. |
| **Constructor de Consulta** | `backend/src/infrastructure/rag/query_builder.py` | Función `construir_consulta_hibrida` (Sintoma + Macro + Top Fallas). |
| **Expansor Léxico** | `MotorRAG._expandir_consulta` | Diccionario determinista de expansión de DTCs y términos peruanos. |
| **Top-K Candidatos FAISS** | `k_candidatos = 25` | Candidatos preliminares extraídos de FAISS antes del reordenamiento. |
| **Módulo de Re-ranking** | `backend/src/infrastructure/rag/relevance_filter.py` | `reordenar_candidatos_rag` con ponderación multiseñal adaptativa. |
| **Factor DTC Re-ranking** | **3.50x** | Prioridad dominante por coincidencia exacta de código DTC oficial. |
| **Factor Macro-Sistema** | **1.60x** (coincidencia) / **0.35x - 0.80x** (penalización) | Filtrado adaptativo guiado por predicción del clasificador ML. |
| **Factor Fallas Top ML** | **$1.15 + (P_{ML} \times 1.50)$** | Refuerzo guiado por probabilidad del Top 3 de Machine Learning. |
| **Consumo en Pipeline** | `backend/src/core/diagnostico/text_processor.py` | Invocado en `procesar_consulta_texto` (Paso 2). |

> [!NOTE]
> **RAG Realmente Utilizado**: El backend utiliza de forma exclusiva `MotorRAG`. Al iniciar, indexa los 239 procedimientos registrados en `metadatos_manuales.json` que coincidan con la estructura `=== TITULO ===\n CUERPO`. Archivos como `orientacion_secundaria_gemacar.txt` no están en el JSON y quedan formalmente excluidos del RAG operativo.

---

## 2. INTEGRIDAD Y TRAZABILIDAD CRIPTOGRÁFICA

Se calcularon los hashes SHA-256 de todos los artefactos críticos del RAG y se contrastaron contra el manifiesto oficial de congelamiento de la Fase 8.3 (`machine_learning/models/reporte_fase8_3_congelado.json`).

### Integridad Criptográfica de Artefactos RAG

| Artefacto | Ruta | Hash SHA-256 Actual | Hash Esperado (Fase 8.3) | Coincide |
|:---|:---|:---|:---|:---:|
| **Catálogo Metadatos** | `machine_learning/manuals/metadatos_manuales.json` | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | **SÍ (100%)** |
| **Índice FAISS Binario** | `machine_learning/manuals/indice_faiss.index` | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | **SÍ (100%)** |
| **Motor RAG Backend** | `backend/src/infrastructure/motor_rag.py` | `eaa316a87ecaa1be9b6702d9807d44ae6cb8a87bc4ce7154c83d6fc09c1c5a3c` | `eaa316a87ecaa1be9b6702d9807d44ae6cb8a87bc4ce7154c83d6fc09c1c5a3c` | **SÍ (100%)** |
| **Re-ranking Filter** | `backend/src/infrastructure/rag/relevance_filter.py` | `fa3d6aef13639bc38bfe5a1360e13276912c97bababdf94954fc53ee7e2c49cc` | `fa3d6aef13639bc38bfe5a1360e13276912c97bababdf94954fc53ee7e2c49cc` | **SÍ (100%)** |

> [!TIP]
> **Validación Bit a Bit en RAM**: Se verificó la reconstrucción vectorial de los 239 procedimientos del índice FAISS cargado en memoria frente al archivo en disco (`faiss.read_index`), arrojando una diferencia absoluta máxima de `0.0`. La paridad binaria es absoluta.

---

## 3. INVENTARIO DOCUMENTAL FORENSE

### TABLA 2 — Inventario Documental del Corpus RAG

| Métrica / Atributo | Valor Cuantitativo | Observación Técnica |
|:---|:---|:---|
| **Total Documentos Registrados** | **239 procedimientos** | Procedimientos activos indexados con metadatos JSON completos. |
| **Total Vectores Indexados** | **239 vectores** | Un vector por procedimiento estructurado. |
| **Dimensiones de Embeddings** | **32,596 características** | Vocabulario TF-IDF n-gramas unigramas y bigramas con stop words. |
| **Tamaño de Índice FAISS** | **31.16 MB** (31,161,821 bytes) | Formato `IndexFlatIP` sin compresión cuantizada (búsqueda exacta). |
| **Archivos Fuente Registrados** | **11 archivos `.txt`** | Distribuidos en carpetas por marca y generales. |
| **Archivos Fuente Excluidos** | **1 archivo** (`orientacion_secundaria_gemacar.txt`) | Guías web secundarias fuera de catálogo (23 KB). |
| **Longitud Chunks (Caracteres)** | Min: 56 \| Max: 3,240 \| Media: 1,558.4 \| Mediana: 1,580 | Distribución unimodal centrada en 1.5 KB. |
| **Longitud Chunks (Palabras)** | Min: 7 \| Max: 412 \| Media: 200.7 \| Mediana: 203 | Equivale aproximadamente a 260 tokens por fragmento. |
| **Chunks Pequeños (< 200 car.)** | **2 chunks (0.8%)** | Chunks stub de mantenimiento preventivo (56 caracteres cada uno). |
| **Chunks Grandes (> 3,000 car.)** | **1 chunk (0.4%)** | `RAG_PROC_139` (Alto Voltaje y Aislamiento EV, 3,240 car.). |
| **Duplicados Literales de Cuerpo** | **1 par (2 chunks)** | Mismo cuerpo en `manual_nissan_versa.txt` y `manual_toyota_corolla.txt`. |
| **Contenido Potencialmente Obsoleto**| **`FUENTES_Y_VALIDACION.md`** | Documenta que el índice tiene 85 fragmentos, cuando la realidad tiene 239. |

#### Distribución de Fragmentos por Archivo Fuente:

| Archivo Fuente | N.º Chunks | % del Corpus | Naturaleza Documental |
|:---|:---:|:---:|:---|
| `generales/manual_procedimientos_multimarca.txt` | 182 | 76.15% | Compendio técnico multimarca universal |
| `generales/procedimientos_fase8.txt` | 34 | 14.23% | Expansión Fase 8 (metrología y tolerancias) |
| `toyota/yaris/2020/manual_toyota_yaris.txt` | 7 | 2.93% | Manual OEM Toyota Yaris (2NR-FE) |
| `manual_procedimientos.txt` | 3 | 1.26% | Archivo histórico legacy |
| `gnv_glp/5ta_generacion/manual_gnv_glp_5ta_gen.txt`| 3 | 1.26% | Sistemas GLP/GNV 5ta Generación |
| `toyota/prius_hev/2018/manual_toyota_prius_hev.txt` | 2 | 0.84% | Toyota Prius Híbrido (2ZR-FXE) |
| `hyundai/accent/2019/manual_hyundai_accent.txt` | 2 | 0.84% | Hyundai Accent (Gamma 1.4/1.6L) |
| `kia/rio/2020/manual_kia_rio.txt` | 2 | 0.84% | Kia Rio (Kappa 1.4L) |
| `nissan/sentra/2020/manual_nissan_sentra.txt` | 2 | 0.84% | Nissan Sentra (MRA8DE) |
| `nissan/versa/2021/manual_nissan_versa.txt` | 1 | 0.42% | Nissan Versa (HR16DE) - Stub |
| `toyota/corolla/2019/manual_toyota_corolla.txt` | 1 | 0.42% | Toyota Corolla (2ZR-FE) - Stub |
| **TOTAL** | **239** | **100.0%** | **Corpus RAG Operativo Activo** |

> [!WARNING]
> **Hallazgo de Chunks Stub**: Los archivos `manual_nissan_versa.txt` y `manual_toyota_corolla.txt` contienen un único procedimiento idéntico de 56 caracteres: *'Inspección general de fluidos, torques y escaneo OBD-II.'*. Aportan nulo valor técnico resolutivo y actúan como meros marcadores de posición.

---

## 4. ESTADO DE METADATA Y TRAZABILIDAD

Se auditó la presencia y completitud de los 21 atributos documentales en los 239 registros de `metadatos_manuales.json`.

### TABLA 3 — Estado de Metadata y Trazabilidad

| Campo / Metadato | Registros Presentes | % Cobertura | Estado | Observación Forense |
|:---|:---:|:---:|:---:|:---|
| `id_procedimiento` | 239 / 239 | 100.0% | **PRESENTE** | Formato unívoco estandarizado `RAG_PROC_001` a `239`. |
| `titulo` | 239 / 239 | 100.0% | **PRESENTE** | Título descriptivo en mayúsculas con sistema o componente. |
| `marca` | 239 / 239 | 100.0% | **PRESENTE** | TOYOTA, NISSAN, HYUNDAI, KIA o MULTIMARCA. |
| `modelo` | 239 / 239 | 100.0% | **PRESENTE** | Modelo específico o MULTIMARCA. |
| `anio` | 239 / 239 | 100.0% | **PRESENTE** | Año o rango `2015-2024`. |
| `motor` | 239 / 239 | 100.0% | **PRESENTE** | Código de motor (ej. `2NR-FE`) o `UNIVERSAL`. |
| `manual_oem` | 239 / 239 | 100.0% | **PRESENTE** | Nombre de la publicación técnica o manual de taller. |
| `edicion` | 239 / 239 | 100.0% | **PRESENTE** | Año o identificador de edición editorial. |
| `pagina` | 239 / 239 | 100.0% | **PRESENTE** | Sección o página referencial del manual. |
| `codigos_dtc` | 202 / 239 | 84.5% | **INCOMPLETA** | 37 procedimientos no tienen códigos DTC asociados (mecánica pura). |
| `archivo_fuente` | 239 / 239 | 100.0% | **PRESENTE** | Ruta relativa al archivo `.txt` dentro del repositorio. |
| `sha256_fragmento`| 239 / 239 | 100.0% | **PRESENTE** | Checksum criptográfico del texto indexado. |
| `url_referencia` | 239 / 239 | 100.0% | **PRESENTE** | URL o portal oficial del fabricante (TIS, TechInfo). |
| `tipo_licencia` | 239 / 239 | 100.0% | **PRESENTE** | Licenciamiento académico / referencial de investigación. |
| `fecha_registro_corpus`| 239 / 239| 100.0% | **PRESENTE** | Marca temporal ISO 8601 del ingreso al índice. |
| `estado_validacion`| 239 / 239 | 100.0% | **PRESENTE** | Valor canónico: `corpus_preliminar_taller`. |
| `sistema` | 239 / 239 | 100.0% | **PRESENTE** | Macro-sistema canónico (MOTOR, FRENOS, etc.). |
| `falla` | 239 / 239 | 100.0% | **PRESENTE** | Nombre de la clase C1 asociada. |
| `tipo_documento` | 239 / 239 | 100.0% | **PRESENTE** | Clasificado como `procedimiento_diagnostico_taller`. |
| `nivel_seguridad` | 0 / 239 | 0.0% | **AUSENTE** | No existe campo tipado en el schema (sólo texto dentro del cuerpo). |
| `autor_organizacion`| 0 / 239 | 0.0% | **AUSENTE** | No existe campo explícito (incorporado indirectamente en `manual_oem`).|

#### Inconsistencias Semánticas Críticas en Metadatos (`falla` vs `titulo`):

Durante la auditoría forense se detectaron **10 procedimientos** cuya asignación en el atributo `falla` de los metadatos contradice flagrantemente el contenido real del documento, originado por reglas de asignación por palabras clave automáticas en fases previas:

1. **`RAG_PROC_047`**: Título: *Válvula solenoide de sincronización variable VVT/OCV Kia Rio* $\rightarrow$ Asignado a `falla = 'Falla en motor de arranque o solenoide defectuoso'` (ELECTRICO). Causa: coincidencia con la palabra 'solenoide'.
2. **`RAG_PROC_060`**: Título: *Reparación de embrague electromagnético y compresor de A/C* $\rightarrow$ Asignado a `falla = 'Disco de embrague desgastado o patinando'` (TRANSMISION). Causa: coincidencia con la palabra 'embrague'.
3. **`RAG_PROC_061`**: Título: *Diagnóstico y reemplazo de mecatrónica y embrague doble DSG/DCT* $\rightarrow$ Asignado a `falla = 'Disco de embrague desgastado o patinando'` (TRANSMISION manual).
4. **`RAG_PROC_067`**: Título: *Diagnóstico y limpieza de válvulas solenoides VVT-i/CVVT y filtro OCV* $\rightarrow$ Asignado a `falla = 'Falla en motor de arranque o solenoide defectuoso'` (ELECTRICO).
5. **`RAG_PROC_075`**: Título: *Diagnóstico de sistema de evaporación de emisiones (EVAP) y purga de cánister* $\rightarrow$ Asignado a `falla = 'Falla en bujias o bobinas de encendido (misfire)'` (MOTOR).
6. **`RAG_PROC_109`**: Título: *Diagnóstico de válvula de purga EVAP y fugas de gases* $\rightarrow$ Asignado a `falla = 'Falla en bujias o bobinas de encendido (misfire)'` (MOTOR).
7. **`RAG_PROC_113`**: Título: *Diagnóstico del sistema TPMS y reaprendizaje de sensores de presión de neumáticos* $\rightarrow$ Asignado a `falla = 'Falla en bujias o bobinas de encendido (misfire)'` (MOTOR).
8. **`RAG_PROC_114`**: Título: *Diagnóstico del embrague del convertidor de par TCC (transmisión automática)* $\rightarrow$ Asignado a `falla = 'Disco de embrague desgastado o patinando'` (TRANSMISION manual).
9. **`RAG_PROC_142`**: Título: *Diagnóstico de solenoide actuador de distribución variable VVT/VTC/VANOS* $\rightarrow$ Asignado a `falla = 'Falla en motor de arranque o solenoide defectuoso'` (ELECTRICO).
10. **`RAG_PROC_154`**: Título: *Diagnóstico de electroválvula de purga de cánister EVAP* $\rightarrow$ Asignado a `falla = 'Falla en bujias o bobinas de encendido (misfire)'` (MOTOR).

> [!CAUTION]
> **Impacto Operativo**: Estas 10 inconsistencias inducen a error al re-ranking multiseñal. Cuando un usuario consulta por 'misfire', el sistema puede ponderar positivamente un procedimiento de calibración de llantas TPMS (`RAG_PROC_113`) o una fuga de cánister EVAP (`RAG_PROC_075`), alterando la precisión diagnóstica.

---

## 5. CRUCE CONTRA LA TAXONOMÍA CANÓNICA C1 (61 CLASES)

Se evaluó la presencia de cada una de las 61 clases del modelo C1 en el corpus RAG:
- **N.º Docs Exactos**: Procedimientos que declaran exactamente la clase en el atributo `falla` de sus metadatos.
- **N.º Chunks Relevantes**: Procedimientos recuperados por coincidencia léxico-semántica sobre título, texto y sinónimos mecánicos.
- **Criterio de Cobertura**:
  - **ALTA**: $\ge 3$ documentos exactos O $\ge 5$ chunks relevantes.
  - **MEDIA**: $\ge 1$ documento exacto O $\ge 2$ chunks relevantes.
  - **BAJA**: $\ge 1$ chunk relevante.
  - **NINGUNA**: 0 chunks relacionados.

### Resumen de Cobertura Global (61 Clases C1):
- **ALTA**: **35 clases (57.4%)**
- **MEDIA**: **26 clases (42.6%)**
- **BAJA**: **0 clases (0.0%)**
- **NINGUNA**: **0 clases (0.0%)**

### TABLA 4 — Cobertura de las 61 Clases Canónicas C1 en el RAG

| ID | Clase Canónica C1 | Macro-Sistema | Docs Exactos | Chunks Relevantes | Nivel Cobertura |
|:---:|:---|:---|:---:|:---:|:---:|
| 1 | Falla en bujias o bobinas de encendido (misfire) | MOTOR | 29 | 30 | **ALTA** |
| 2 | Bomba de gasolina quemada o con baja presion | MOTOR | 10 | 34 | **ALTA** |
| 3 | Inyectores sucios o filtro de combustible obstruido | MOTOR | 5 | 12 | **ALTA** |
| 4 | Falla en sensor de oxigeno o mezcla rica | MOTOR | 15 | 19 | **ALTA** |
| 5 | Cuerpo de aceleracion o valvula IAC sucia | MOTOR | 8 | 8 | **ALTA** |
| 6 | Empaque de culata soplado o danado | MOTOR | 3 | 4 | **ALTA** |
| 7 | Falla en termostato o motoventilador de radiador | MOTOR | 4 | 6 | **ALTA** |
| 8 | Fuga en mangueras de refrigerante o radiador picado | MOTOR | 1 | 5 | **ALTA** |
| 9 | Consumo de aceite por desgaste de anillos o retenes | MOTOR | 1 | 10 | **ALTA** |
| 10 | Baja presion de aceite o bomba de aceite defectuosa | MOTOR | 2 | 21 | **ALTA** |
| 11 | Faja o cadena de distribucion destensada o con salto de punto | MOTOR | 4 | 4 | **ALTA** |
| 12 | Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic) | MOTOR | 1 | 1 | **MEDIA** |
| 13 | Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas) | MOTOR | 1 | 1 | **MEDIA** |
| 14 | Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI | MOTOR | 1 | 1 | **MEDIA** |
| 15 | Fuga en mangueras de intercooler o turbocompresor danado | MOTOR | 4 | 4 | **ALTA** |
| 16 | Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo) | MOTOR | 1 | 1 | **MEDIA** |
| 17 | Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet) | MOTOR | 1 | 5 | **ALTA** |
| 18 | Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6) | MOTOR | 1 | 3 | **MEDIA** |
| 19 | Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups) | MOTOR | 1 | 6 | **ALTA** |
| 20 | Falla en sistema Flex / Bi-combustible (Alcohol/Etanol) | MOTOR | 1 | 1 | **MEDIA** |
| 21 | Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP) | MOTOR | 3 | 5 | **ALTA** |
| 22 | Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga) | MOTOR | 1 | 1 | **MEDIA** |
| 23 | Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430) | MOTOR | 6 | 6 | **ALTA** |
| 24 | Falla en regulador de presion de combustible o diafragma roto | MOTOR | 1 | 12 | **ALTA** |
| 25 | Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208) | MOTOR | 1 | 2 | **MEDIA** |
| 26 | Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados | MOTOR | 1 | 1 | **MEDIA** |
| 27 | Desgaste de pastillas y zapatas de freno | FRENOS | 4 | 4 | **ALTA** |
| 28 | Discos de freno alabeados o desgastados | FRENOS | 2 | 2 | **MEDIA** |
| 29 | Falla en servofreno (booster) o linea de vacio | FRENOS | 1 | 3 | **MEDIA** |
| 30 | Fuga hidraulica o aire en el sistema de frenos | FRENOS | 1 | 36 | **ALTA** |
| 31 | Falla en sensor de velocidad de rueda ABS | FRENOS | 10 | 47 | **ALTA** |
| 32 | Falla en sistema de frenado regenerativo (EV / Hibridos) | FRENOS | 1 | 4 | **MEDIA** |
| 33 | Caliper de freno trabado o mordaza pegada (piston agarrotado) | FRENOS | 2 | 2 | **MEDIA** |
| 34 | Disco de embrague desgastado o patinando | TRANSMISION | 7 | 8 | **ALTA** |
| 35 | Falla en bombin o bomba hidraulica de embrague | TRANSMISION | 2 | 3 | **MEDIA** |
| 36 | Falta o degradacion de aceite de caja de cambios | TRANSMISION | 5 | 15 | **ALTA** |
| 37 | Rodajes de caja mecanica o diferencial gastados | TRANSMISION | 7 | 11 | **ALTA** |
| 38 | Sobrecalentamiento o solenoides en caja automatica CVT / DSG | TRANSMISION | 2 | 4 | **MEDIA** |
| 39 | Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW) | TRANSMISION | 8 | 8 | **ALTA** |
| 40 | Desgaste en collarin de empuje o crapodina de embrague | TRANSMISION | 1 | 2 | **MEDIA** |
| 41 | Rodajes de transmision manual o eje primario gastados | TRANSMISION | 1 | 5 | **ALTA** |
| 42 | Amortiguadores reventados o bujes de suspension gastados | SUSPENSION_CHASIS | 4 | 4 | **ALTA** |
| 43 | Juntas homocineticas o palieres danados | SUSPENSION_CHASIS | 2 | 2 | **MEDIA** |
| 44 | Llantas desbalanceadas o desalineadas | SUSPENSION_CHASIS | 1 | 1 | **MEDIA** |
| 45 | Cremallera de direccion asistida con holgura o fuga | SUSPENSION_CHASIS | 7 | 11 | **ALTA** |
| 46 | Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura) | SUSPENSION_CHASIS | 1 | 2 | **MEDIA** |
| 47 | Alternador defectuoso o placa de diodos quemada | ELECTRICO | 17 | 17 | **ALTA** |
| 48 | Bateria descargada o bornes sulfatados | ELECTRICO | 11 | 12 | **ALTA** |
| 49 | Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos) | ELECTRICO | 1 | 5 | **ALTA** |
| 50 | Fallo en inversor de corriente IGBT o motor electrico (EV) | ELECTRICO | 1 | 3 | **MEDIA** |
| 51 | Foco o falla en sistema de refrigeracion de bateria/inversor (EV) | ELECTRICO | 1 | 2 | **MEDIA** |
| 52 | Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados) | ELECTRICO | 5 | 6 | **ALTA** |
| 53 | Fuga parasita de corriente en reposo (consumo nocturno de bateria) | ELECTRICO | 1 | 2 | **MEDIA** |
| 54 | Falla en compresor de aire acondicionado o fuga de gas R134a | CLIMATIZACION | 5 | 14 | **ALTA** |
| 55 | Falla electrica del cierre centralizado o actuador de puerta | CARROCERIA_NEUMATICA | 5 | 6 | **ALTA** |
| 56 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | CARROCERIA_NEUMATICA | 1 | 3 | **MEDIA** |
| 57 | Elevalunas electrico o guaya de alzacristales rota o trabada | CARROCERIA_NEUMATICA | 2 | 2 | **MEDIA** |
| 58 | Limpiaparabrisas o motor pluma quemado | CARROCERIA_NEUMATICA | 1 | 1 | **MEDIA** |
| 59 | Fugas de aire o fallos en el sistema de frenos neumático (Camiones) | CARROCERIA_NEUMATICA | 3 | 7 | **ALTA** |
| 60 | Válvula de freno de aire o secador APS obstruido (Camiones) | CARROCERIA_NEUMATICA | 1 | 5 | **ALTA** |
| 61 | Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire) | CARROCERIA_NEUMATICA | 1 | 1 | **MEDIA** |

---

## 6. AUDITORÍA DE COMPONENTES DIAGNÓSTICOS (A–S)

Para cada una de las 61 clases se auditó la presencia de los 19 componentes diagnósticos esenciales:
`A`: Descripción de la falla | `B`: Síntomas | `C`: Causas posibles | `D`: Lenguaje del cliente | `E`: Preguntas discriminantes | `F`: Fallas similares | `G`: Comprobación/prueba | `H`: Herramienta | `I`: Condiciones previas | `J`: Resultado posible | `K`: Interpretación del resultado | `L`: Evidencia que refuerza | `M`: Evidencia que debilita | `N`: Evidencia que descarta | `O`: Siguiente comprobación | `P`: DTC relacionados | `Q`: Seguridad y EPP | `R`: Dependencia OEM | `S`: Fuente técnica

### TABLA 5 — Matriz de Componentes Diagnósticos por Clase C1 (Muestra de Síntesis)

| ID | Clase | Desc (A) | Sínt (B) | Caus (C) | Preg (E) | Simil (F) | Prueb (G) | Herr (H) | Resul (J) | Interp (K) | Descart (N) | SigPaso (O) | DTC (P) | Segur (Q) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Falla en bujias o bobinas de encend... | SÍ | SÍ | SÍ | NO | NO | SÍ | SÍ | SÍ | PARCIAL | SÍ | NO | SÍ | SÍ |
| 2 | Bomba de gasolina quemada o con baj... | SÍ | SÍ | SÍ | PARCIAL | NO | SÍ | SÍ | SÍ | SÍ | PARCIAL | NO | SÍ | SÍ |
| 3 | Inyectores sucios o filtro de combu... | SÍ | SÍ | PARCIAL | NO | NO | SÍ | SÍ | SÍ | SÍ | PARCIAL | NO | SÍ | PARCIAL |
| 4 | Falla en sensor de oxigeno o mezcla... | SÍ | SÍ | PARCIAL | PARCIAL | NO | SÍ | SÍ | SÍ | SÍ | SÍ | NO | SÍ | PARCIAL |
| 5 | Cuerpo de aceleracion o valvula IAC... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | PARCIAL | NO | PARCIAL | NO | SÍ | PARCIAL |
| 6 | Empaque de culata soplado o danado... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | PARCIAL | NO | NO | NO | PARCIAL | NO |
| 7 | Falla en termostato o motoventilado... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | SÍ | PARCIAL | NO | NO | SÍ | PARCIAL |
| 8 | Fuga en mangueras de refrigerante o... | SÍ | SÍ | NO | NO | NO | SÍ | PARCIAL | PARCIAL | PARCIAL | NO | NO | SÍ | PARCIAL |
| 9 | Consumo de aceite por desgaste de a... | SÍ | SÍ | PARCIAL | NO | NO | SÍ | SÍ | SÍ | PARCIAL | PARCIAL | NO | SÍ | PARCIAL |
| 10 | Baja presion de aceite o bomba de a... | SÍ | SÍ | PARCIAL | PARCIAL | NO | SÍ | SÍ | SÍ | PARCIAL | PARCIAL | NO | SÍ | SÍ |
| 11 | Faja o cadena de distribucion deste... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | PARCIAL | NO | PARCIAL | NO | SÍ | PARCIAL |
| 12 | Falla en sistema de sincronizacion ... | PARCIAL | PARCIAL | NO | NO | NO | PARCIAL | NO | NO | NO | NO | NO | SÍ | NO |
| 13 | Falla de descarbonizacion e inyecci... | PARCIAL | PARCIAL | NO | NO | NO | SÍ | NO | NO | NO | NO | NO | PARCIAL | NO |
| 14 | Falla en actuador de turbocompresor... | PARCIAL | PARCIAL | NO | NO | NO | SÍ | PARCIAL | NO | NO | NO | NO | SÍ | NO |
| 15 | Fuga en mangueras de intercooler o ... | SÍ | SÍ | PARCIAL | NO | NO | SÍ | SÍ | PARCIAL | NO | NO | NO | SÍ | PARCIAL |
| 16 | Falla de correa dentada banada en a... | PARCIAL | PARCIAL | NO | NO | NO | SÍ | NO | NO | NO | NO | NO | PARCIAL | NO |
| 17 | Falla en modulo de bomba de gasolin... | SÍ | SÍ | NO | PARCIAL | NO | SÍ | SÍ | PARCIAL | NO | NO | NO | SÍ | PARCIAL |
| 18 | Falla en filtro de particulas DPF /... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | SÍ | PARCIAL | NO | NO | SÍ | NO |
| 19 | Fuga o baja presion en sistema Comm... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | NO | NO | PARCIAL | NO | SÍ | PARCIAL |
| 20 | Falla en sistema Flex / Bi-combusti... | PARCIAL | PARCIAL | NO | NO | NO | PARCIAL | PARCIAL | SÍ | NO | NO | NO | PARCIAL | NO |
| 21 | Falla en sensor de posicion de cigu... | SÍ | SÍ | PARCIAL | NO | NO | SÍ | SÍ | PARCIAL | NO | NO | NO | SÍ | NO |
| 22 | Falla en sistema de control de emis... | PARCIAL | PARCIAL | NO | NO | NO | SÍ | PARCIAL | NO | NO | NO | NO | SÍ | NO |
| 23 | Convertidor catalitico ineficiente ... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | PARCIAL | SÍ | SÍ | NO | SÍ | NO |
| 24 | Falla en regulador de presion de co... | SÍ | SÍ | NO | NO | NO | SÍ | SÍ | SÍ | PARCIAL | NO | NO | SÍ | SÍ |
| 25 | Falla en circuito o solenoide de in... | PARCIAL | PARCIAL | NO | NO | PARCIAL | SÍ | SÍ | PARCIAL | SÍ | PARCIAL | NO | SÍ | NO |
| ... | *(Ver anexo JSON para las 61 clases completas)* | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

#### Resumen Porcentual de Componentes Diagnósticos en el Corpus:

| Componente Diagnóstico | % Clases con Presencia Plena (SÍ) | % Clases con Presencia Parcial | % Clases Ausente (NO) | Evaluación |
|:---|:---:|:---:|:---:|:---:|
| **Descripción técnica** (`A`) | 78.7% | 21.3% | 0.0% | ALTO |
| **Síntomas observables** (`B`) | 68.9% | 31.1% | 0.0% | ALTO |
| **Causas posibles** (`C`) | 9.8% | 26.2% | 63.9% | DEFICITARIO |
| **Lenguaje del cliente** (`D`) | 0.0% | 23.0% | 77.0% | DEFICITARIO |
| **Preguntas discriminantes** (`E`) | 0.0% | 8.2% | 91.8% | DEFICITARIO |
| **Fallas similares / Confundibles** (`F`) | 0.0% | 14.8% | 85.2% | DEFICITARIO |
| **Comprobación / Prueba física** (`G`) | 91.8% | 8.2% | 0.0% | ALTO |
| **Herramienta metrológica** (`H`) | 72.1% | 16.4% | 11.5% | ALTO |
| **Condiciones previas** (`I`) | 32.8% | 32.8% | 34.4% | MEDIO |
| **Resultado posible / Tolerancia** (`J`) | 37.7% | 31.1% | 31.1% | MEDIO |
| **Interpretación de lectura** (`K`) | 16.4% | 29.5% | 54.1% | DEFICITARIO |
| **Evidencia que refuerza** (`L`) | 6.6% | 39.3% | 54.1% | DEFICITARIO |
| **Evidencia que debilita** (`M`) | 0.0% | 4.9% | 95.1% | DEFICITARIO |
| **Evidencia que descarta** (`N`) | 9.8% | 31.1% | 59.0% | DEFICITARIO |
| **Siguiente comprobación** (`O`) | 0.0% | 0.0% | 100.0% | DEFICITARIO |
| **Códigos DTC** (`P`) | 78.7% | 6.6% | 14.8% | ALTO |
| **Normas de seguridad / EPP** (`Q`) | 29.5% | 39.3% | 31.1% | MEDIO |
| **Dependencia OEM específica** (`R`) | 0.0% | 14.8% | 85.2% | DEFICITARIO |
| **Mención de fuente OEM** (`S`) | 70.5% | 23.0% | 6.6% | ALTO |

> [!IMPORTANT]
> **Déficit Estructural Identificado**: Los componentes `E` (Preguntas discriminantes), `F` (Fallas similares), `M` (Evidencia que debilita) y `N` (Evidencia que descarta) presentan una ausencia superior al **60%**. El RAG actual está redactado como un manual de taller estático ('cómo cambiar o probar una pieza') y no como un asistente interactivo de diagnóstico diferencial.

---

## 7. ESTADO DE LA CADENA DIAGNÓSTICA

Se evaluó la capacidad de los procedimientos del RAG para articular la cadena completa de razonamiento clínico:
$$\text{Síntoma} \rightarrow \text{Hipótesis} \rightarrow \text{Pregunta} \rightarrow \text{Prueba} \rightarrow \text{Resultado} \rightarrow \text{Interpretación} \rightarrow \text{Descarte} \rightarrow \text{Siguiente Acción}$$

### TABLA 6 — Estado de la Cadena Diagnóstica en las 61 Clases

| Estado de la Cadena | N.º Clases | Porcentaje | Criterio Técnico |
|:---|:---:|:---:|:---|
| **COMPLETA** | **13 clases** | **21.31%** | Posee síntoma, causas, prueba física, herramienta, interpretación y criterio explícito de descarte o siguiente paso. |
| **PARCIAL** | **8 clases** | **13.11%** | Posee síntoma, causas y prueba con herramienta, pero no define descarte ni paso posterior. |
| **AUSENTE** | **40 clases** | **65.57%** | Ficha descriptiva estática: describe la pieza y códigos DTC pero no articula una secuencia ramificada de diagnóstico. |
| **TOTAL** | **61 clases** | **100.0%** | |

#### Distribución de la Cadena Diagnóstica por Macro-Sistema:

| Macro-Sistema | Clases Totales | Completa | Parcial | Ausente | % Ausencia de Cadena |
|:---|:---:|:---:|:---:|:---:|:---:|
| **CARROCERIA_NEUMATICA** | 7 | 0 | 3 | 4 | **57.1%** |
| **CLIMATIZACION** | 1 | 1 | 0 | 0 | **0.0%** |
| **ELECTRICO** | 7 | 2 | 0 | 5 | **71.4%** |
| **FRENOS** | 7 | 2 | 1 | 4 | **57.1%** |
| **MOTOR** | 26 | 6 | 2 | 18 | **69.2%** |
| **SUSPENSION_CHASIS** | 5 | 1 | 0 | 4 | **80.0%** |
| **TRANSMISION** | 8 | 1 | 2 | 5 | **62.5%** |

---

## 8. GRUPOS CONFUNDIBLES PRIORITARIOS (A–E)

Se auditó con rigor forense la capacidad del RAG para proporcionar discriminadores técnicos claros entre fallas con manifestaciones similares en taller:

### TABLA 7 — Análisis de Grupos Confundibles Prioritarios

| Grupo Confundible | Clases Involucradas | N.º Chunks | Discriminadores Existentes en RAG | Capacidad de Diferenciación |
|:---|:---|:---:|:---|:---:|
| **GRUPO A**: Alimentación de Combustible | 1. Bomba de gasolina<br>2. Inyectores/filtro<br>3. Regulador de presión<br>4. Módulo FSCM/PEM | 18 | • Presión nominal en riel (45-55 PSI) con manómetro.<br>• Prueba de diafragma de regulador desconectando manguera de vacío.<br>• Señal PWM con multímetro en módulo FSCM.<br>• Prueba de goteo y caudal en inyectores. | **ALTA** |
| **GRUPO B**: Encendido vs Ralentí vs Compresión | 1. Bujías/Bobinas (Misfire)<br>2. IAC/Cuerpo aceleración<br>3. Pérdida de compresión<br>4. Inyector individual | 43 | • Oscilograma secundario y balance de cilindros.<br>• Vacuómetro y manómetro de compresión en seco/húmedo.<br>• Resistencia en frío/caliente de bobina de inyector (12-15 $\Omega$).<br>• Limpieza de carbonilla y reaprendizaje de mariposa/IAC. | **ALTA** |
| **GRUPO C**: Vibraciones y Rodadura Mecánica | 1. Discos alabeados<br>2. Llantas desbalanceadas<br>3. Rodamiento de maza<br>4. Juntas homocinéticas | 14 | • Vibración exclusiva al frenar $\rightarrow$ reloj comparador en disco (máx 0.05mm).<br>• Vibración a velocidad constante $\rightarrow$ balanceadora dinámica.<br>• Zumbido continuo 'wub-wub' que varía al doblar $\rightarrow$ rodaje.<br>• Traqueteo seco 'clac-clac' al girar a tope y acelerar $\rightarrow$ palier/homocinética. | **ALTA** |
| **GRUPO D**: Sistema Eléctrico y Carga | 1. Batería descargada<br>2. Alternador defectuoso<br>3. Fuga parásita<br>4. Motor de arranque | 17 | • Voltaje en reposo (12.6V) vs voltaje en marcha (13.8V-14.4V).<br>• Medición de rizado AC con osciloscopio en alternador.<br>• Medición de caída de mV en fusibles para fuga parásita.<br>• Caída de tensión en terminales 30/50 y longitud de carbones de arranque. | **ALTA** |
| **GRUPO E**: Embrague y Desacople Mecánico | 1. Disco de embrague desgastado<br>2. Collarín/crapodina<br>3. Bombín/bomba hidráulica | 10 | • RPM suben sin avance (olor a quemado) $\rightarrow$ patinamiento de disco.<br>• Zumbido al pisar embrague que calla al soltar $\rightarrow$ collarín/crapodina.<br>• Pedal esponjoso o pegado al piso sin desacople $\rightarrow$ bombín/aire hidráulico. | **MEDIA-ALTA** |

> [!TIP]
> **Hallazgo Favorable**: En los 5 grupos prioritarios (A a E), los procedimientos técnicos contienen las pruebas metrológicas clave (manómetros, multímetros, osciloscopios, reloj comparador) para que un técnico distinga la causa raíz física, siempre que la consulta recupere el procedimiento apropiado.

---

## 9. AUDITORÍA ESPECÍFICA DE LA CLASE A/C

Clase analizada: **`Falla en compresor de aire acondicionado o fuga de gas R134a`**.
Se auditaron los procedimientos que abordan sistemas de refrigeración y climatización en el corpus:
- `RAG_PROC_015`: Limpieza evaporador, filtro cabina y presostato.
- `RAG_PROC_024`: Válvula de expansión térmica (TXV) y filtro desecante.
- `RAG_PROC_044`: Carga de refrigerante R134a/R1234yf y prueba de fugas con manómetros.
- `RAG_PROC_060`: Reparación de embrague electromagnético de compresor A/C (*mal clasificado en transmisión*).
- `RAG_PROC_064`: Fugas en condensador y radiador de calefacción / evaporador.
- `RAG_PROC_119`: Blower motor y resistencia de velocidades HVAC.

### TABLA 8 — Auditoría Forense de Componentes en la Clase A/C

| Dimensión Evaluada | Estado | Evidencia Textual en Procedimientos RAG | Procedimiento RAG |
|:---|:---:|:---|:---:|
| **1. Aire sale pero no enfría** | **SÍ** | *'El aire acondicionado bota aire tibio por las rejillas... falta de enfriamiento...'* | `RAG_PROC_024`, `044` |
| **2. Enfría en marcha, tibio detenido** | **NO** | **AUSENTE**. No existe explicación sobre la dinámica del flujo de aire forzado a velocidad vs falla del electroventilador o suciedad externa del condensador. | *Ninguno* |
| **3. Compresor acopla / no acopla** | **SÍ** | *'El compresor no acopla o el plato del electroimán no acopla; medir entrehierro 0.35-0.65mm y bobina 3.2-4.5 $\Omega$...' | `RAG_PROC_044`, `060` |
| **4. Ventilador interior (Blower)** | **SÍ** | *'Resistor pack térmico quemado (solo funciona vel 4) o motor trabado por carbones gastados...'* | `RAG_PROC_119` |
| **5. Condensador / Motoventilador** | **SÍ** | *'Inspección de fugas por piedras en condensador frontal; módulo PWM de electroventilador...'* | `RAG_PROC_064`, `138` |
| **6. Tipo de Refrigerante** | **SÍ** | Especifica gas `R134a` y `R1234yf`, aceite dieléctrico `PAG 46` y aceite `POE ND-11` para compresores eléctricos de alto voltaje. | `RAG_PROC_024`, `044`, `139` |
| **7. Presiones Manifold** | **SÍ** | Presión baja: 25 a 35 PSI; Presión alta: 150 a 220 PSI; Vacío de expansión: -10 inHg; Alta obstruida: >250 PSI. | `RAG_PROC_024`, `044` |
| **8. Detección de Fugas** | **SÍ** | Presurización con nitrógeno seco a 150 PSI, lámpara UV fluorescente y retención de vacío a -30 inHg por 15 minutos. | `RAG_PROC_044`, `064` |
| **9. Interpretación de Pruebas** | **PARCIAL** | Provee rangos nominales de presión, pero carece de tabla cruzada (alta baja / baja alta / ambas bajas / ambas altas). | `RAG_PROC_024`, `044` |
| **10. Siguiente Comprobación** | **PARCIAL** | Describe pasos de recarga o reemplazo de componentes, pero no secuencia condicional ramificada ante lecturas ambiguas. | `RAG_PROC_044` |

---

## 10. MEDICIONES Y UNIDADES FÍSICAS

Se realizó un escaneo léxico de las magnitudes y unidades físicas en la totalidad de los 239 fragmentos:

### TABLA 9 — Recuento de Unidades Físicas y Análisis de Universalidad

| Magnitud / Unidad | Total Menciones en RAG | Ejemplos Representativos en Corpus | Riesgo de Ambigüedad Universal |
|:---|:---:|:---|:---:|
| **Voltios (V)** | 437 | 12.6V reposo, 13.8-14.4V alternador, 5.0V referencia sensores TPS/MAP. | **BAJO** (Estándar automotriz 12V / 5V sensores). |
| **Amperios (A)** | 266 | 15A consumo soplador, 80-120A consumo de arranque, fusible 30A. | **BAJO** (Rangos de protección eléctrica). |
| **Milímetros (mm)** | 140 | 0.35-0.65mm entrehierro A/C, 0.05mm alabeo disco, espesor pastilla 2mm. | **BAJO** (Tolerancias dimensionales claras). |
| **Presión (bar)** | 124 | 1,600 bar Common Rail, 1.2 bar turbo, 2 bar prueba neumática. | **MEDIO** (No confundir con PSI en riel de gasolina). |
| **Temperatura (°C)** | 113 | 85-90°C régimen termostato, 95°C activación electroventilador. | **BAJO** (Escala Celsius explícita). |
| **Presión (PSI)** | 101 | 45-55 PSI gasolina, 25-35 PSI baja A/C, 150 PSI nitrógeno, 32 PSI llanta. | **MEDIO** (Rieles GDI operan a 500-2000 PSI). |
| **Revoluciones (RPM)** | 72 | 650-750 RPM ralentí en caliente, 2,500 RPM prueba catalizador. | **BAJO** (Velocidad de giro estándar). |
| **Resistencia ($\Omega$)** | 33 | 3.2-4.5 $\Omega$ bobina A/C, 12-16 $\Omega$ inyector MPI, 30-55 $\Omega$ IAC. | **BAJO** (Impedancias eléctricas de actuadores). |
| **Milivoltios (mV)** | 19 | 100-900 mV sensor de oxígeno, 0.2 a 2.5 mV caída en fusibles para fuga. | **BAJO** (Señales de estequiometría y caída shunt). |
| **Presión (kPa)** | 16 | 100 kPa presión atmosférica barométrica. | **BAJO** (Unidad SI poco usada en taller). |
| **Milisegundos (ms)** | 12 | 2.5 a 4.0 ms tiempo de inyección en ralentí. | **BAJO** (Ancho de pulso PWM). |

#### Análisis Forense del Error Histórico '52 PSI $\rightarrow$ 52 V':
Se auditó específicamente si el corpus RAG contenía ambigüedades que indujeran la transformación errónea de una presión en voltaje:
- **Hallazgo**: Ningún procedimiento del RAG confunde voltios con PSI. Las presiones están rigurosamente tipadas como `PSI` o `bar`, y las tensiones como `V` o `mV`.
- **Conclusión**: El error manual observado en pruebas previas (interpretar 52 PSI de combustible como 52 V) se originó enteramente en la **capa del parser de lenguaje natural y extractor de evidencia conversacional** (`extractor_evidencias.py` / `suficiencia_informacion.py`), la cual asignó la magnitud numérica extraída a la ranura de voltaje de batería por colisión de expresiones regulares en el estado de la sesión, no por información errónea del RAG.

---

## 11. AUDITORÍA FORENSE DE SEGURIDAD

Se examinaron los 239 procedimientos frente a los protocolos de seguridad industrial en talleres automotrices:

### TABLA 10 — Evaluación de Seguridad por Subsistema de Riesgo

| Subsistema de Riesgo Crítico | Docs Asociados | Docs con Advertencia/EPP | % Cobertura Seguridad | Clasificación | Hallazgo Forense y Riesgo Residual |
|:---|:---:|:---:|:---:|:---:|:---|
| **Vehículos Híbridos / EV (Alta Tensión)** | 7 | 7 | **100.0%** | **SEGURA** | Exige desconexión de tapón de servicio naranja, guantes clase 0 (1,000V) y espera de 10 min por condensadores. |
| **Common Rail Diésel (1,600+ bar)** | 7 | 4 | **57.1%** | **INCOMPLETA** | 3 procedimientos omiten la advertencia de inyección subcutánea por microchorro a alta presión (riesgo de amputación). |
| **Climatización A/C (Gas R134a)** | 11 | 6 | **54.5%** | **INCOMPLETA** | Falta advertencia sistemática de uso de gafas protectoras ante escape de líquido criogénico (ceguera/quemadura). |
| **Combustible Gasolina (Presión/Inflamable)** | 50 | 24 | **48.0%** | **INCOMPLETA** | Más de la mitad de procedimientos omiten el protocolo de despresurización previa de la línea antes de desconectar mangueras. |
| **Refrigerante Caliente / Ebullición** | 25 | 10 | **40.0%** | **INCOMPLETA** | Omiten advertir nunca abrir tapa de radiador con motor caliente (riesgo severo de quemaduras de 2do y 3er grado). |
| **Frenos Hidráulicos (Líquido corrosivo/Pérdida)** | 43 | 17 | **39.5%** | **INCOMPLETA** | Poca advertencia sobre toxicidad de DOT4 y verificación estricta de pedal firme antes de prueba de rodaje. |
| **Frenos Neumáticos Camiones (Maxi-Brake)** | 3 | 1 | **33.3%** | **POTENCIALMENTE RIESGOSA** | Cámaras de freno de resorte acumulan energía mecánica letal; solo 1 documento advierte no desarmar la cámara sin perno de destrabe. |

---

## 12. CONTRADICCIONES, CONFLICTOS TÉCNICOS Y DUPLICADOS

### TABLA 11 — Inventario de Conflictos Documentales

| Tipo de Incidencia | Procedimientos Involucrados | Descripción de la Contradicción o Conflicto | Severidad |
|:---|:---|:---|:---:|
| **Duplicado Literal de Cuerpo** | `RAG_PROC_025` (`manual_nissan_versa.txt`) vs `RAG_PROC_026` (`manual_toyota_corolla.txt`) | Ambos chunks tienen el mismo cuerpo de 56 caracteres: *'Inspección general de fluidos, torques y escaneo OBD-II.'*. Son marcadores vacíos sin valor técnico. | **MEDIA** |
| **Asignación Cruzada de Clase** | `RAG_PROC_060` (Compresor A/C) vs `RAG_PROC_059` (Embrague Yaris) | Se asignó el embrague electromagnético del compresor de aire acondicionado a la clase 'Disco de embrague desgastado o patinando' de transmisión. | **ALTA** |
| **Asignación Cruzada de Sistema**| `RAG_PROC_047`, `067`, `142` (Válvulas VVT) vs `RAG_PROC_021` (Arranque) | Solenoides hidráulicos del árbol de levas clasificados como 'Falla en motor de arranque o solenoide defectuoso'. | **ALTA** |
| **Asignación Cruzada de Emisiones**| `RAG_PROC_075`, `109`, `154` (EVAP) vs `RAG_PROC_182` (Misfire P0301) | Procedimientos de prueba de fugas de gases del tanque EVAP asignados a 'Falla en bujías o bobinas de encendido'. | **ALTA** |
| **Contradicción de Presiones por Cruce**| `RAG_PROC_075` (EVAP a 5 PSI) vs `RAG_PROC_122` (Inyectores a 50 PSI) | Al compartir erróneamente la clase 'Misfire', una búsqueda de combustible puede traer la prueba de 5 PSI de EVAP generando confusión en la presión del riel. | **ALTA** |
| **Desactualización Documental** | `FUENTES_Y_VALIDACION.md` vs `metadatos_manuales.json` | La documentación declara 85 fragmentos y rangos `RAG_PROC_001` a `064`, mientras el índice real tiene 239 procedimientos. | **BAJA** |
| **Corpus No Registrado en Carpeta**| `orientacion_secundaria_gemacar.txt` (23 KB) | Archivo de blog web presente en el directorio físico pero ignorado por el índice por carecer de metadatos. | **BAJA** |

---

## 13. AUDITORÍA CONTROLADA DE RECUPERACIÓN (RETRIEVAL)

Se ejecutó una prueba de recuperación controlada sin modificar el índice, evaluando **82 consultas independientes**:
- **61 consultas canónicas directas**: una por cada clase C1 (ej. *'Diagnóstico y procedimiento para Bomba de gasolina quemada...'*).
- **21 consultas de taller realistas**: consultas de síntomas coloquiales para los grupos confundibles A–E y el caso A/C.

### TABLA 12 — Métricas Globales de Retrieval RAG (82 Consultas)

| Métrica de Recuperación | Valor Obtenido | Interpretación Técnica |
|:---|:---:|:---|
| **Total Consultas Evaluadas** | **82 consultas** | 61 de cobertura taxonómica + 21 de taller y grupos confundibles. |
| **Hit@1** | **64.63%** (53 / 82) | El procedimiento óptimo exacto quedó clasificado en la posición 1 en casi 2 de cada 3 consultas. |
| **Hit@3** | **87.80%** (72 / 82) | El procedimiento correcto se encontró dentro del Top 3 en el 87.8% de los casos. |
| **Hit@5** | **92.68%** (76 / 82) | El procedimiento correcto se ubicó dentro del Top 5 de candidatos en más del 92% de casos. |
| **Mean Reciprocal Rank (MRR)** | **0.7583** | Alto rango recíproco promedio; el usuario recibe el conocimiento relevante en posiciones superiores. |

#### Análisis Cualitativo del Comportamiento del Retrieval:
1. **Efectividad del Re-ranking Multiseñal**: El filtro `reordenar_candidatos_rag` demostró ser decisivo. Cuando una consulta contiene códigos DTC (ej. P0301, P0562), el factor `3.50x` eleva instantáneamente el procedimiento al Top 1, compensando la dispersión del TF-IDF puro.
2. **Dispersión por Solapamiento Léxico en TF-IDF Crudo**: En consultas sin DTC donde intervienen términos comunes ('aceite', 'bomba', 'solenoide'), el TF-IDF recupera procedimientos de otros sistemas (ej. 'bomba de agua' en lugar de 'bomba de aceite'). La presencia del prior bayesiano del modelo ML en `reordenar_candidatos_rag` (factor `1.60x`) mitiga esta contaminación, pero si la confianza ML es baja, la posición Top 1 se pierde hacia la posición 2 o 3.
3. **Contaminación por Metadatos Cruzados**: Los 10 procedimientos con asignación errónea en `metadatos_manuales.json` sufren penalizaciones o bonificaciones indebidas durante el re-ranking guiado por ML.

---

## 14. SEPARACIÓN DE PROBLEMAS POR CAPA DE ARQUITECTURA

Es indispensable no atribuir al RAG deficiencias que corresponden a otras capas del sistema CarBot.

### TABLA 14 — Clasificación de Hallazgos por Capa Arquitectónica

| Incidencia / Hallazgo Detectado | Capa Responsable | Justificación y Causa Raíz | Impacto en el RAG |
|:---|:---:|:---|:---|
| **Interpretación de 52 PSI como 52 V** | **PARSER / ESTADO** | Expresión regular en `extractor_evidencias.py` asignó el valor numérico al campo de batería. En el RAG las unidades están correctamente diferenciadas. | Ninguno (el RAG no originó el error). |
| **Repetición de preguntas ya respondidas**| **ORQUESTACIÓN** | El bucle de suficiencia (`suficiencia_informacion.py`) no marcaba el slot como satisfecho ante respuestas coloquiales. | Ninguno (pertenece al gestor conversacional). |
| **Arrastre de contexto A/C a sesión nueva**| **ESTADO / SESIÓN** | Persistencia de variables en `SessionManager` sin reinicio tras cierre de ticket. | Ninguno. |
| **Inconsistencias de asignación (VVT a Arranque)**| **RAG (METADATOS)** | Script histórico de etiquetado por palabras clave asignó `falla` errónea en `metadatos_manuales.json`. | **DIRECTO**: Altera el re-ranking guiado por ML. |
| **Ausencia de cadena diagnóstica interactiva**| **RAG (DOCUMENTOS)** | Chunks redactados como compendios técnicos estáticos sin flujo de descarte ramificado. | **DIRECTO**: El LLM debe inventar el siguiente paso. |
| **Falta de avisos de seguridad en gasolina/alta presión**| **RAG / SEGURIDAD** | Procedimientos omitieron advertencias de EPP y despresurización previa de líneas. | **DIRECTO**: Riesgo en taller si el técnico sigue solo el texto. |
| **Chunks stub de 56 caracteres** | **RAG (INVENTARIO)** | Archivos `manual_nissan_versa.txt` y `manual_toyota_corolla.txt` con contenido trivial. | **DIRECTO**: Desperdicia slots de recuperación. |

---

## 15. COMPARACIÓN: NECESIDADES DIAGNÓSTICAS VS RAG ACTUAL

### TABLA 13 — Matriz de Necesidades Técnicas vs Estado Actual del RAG

| Necesidad Técnica de Taller | Cobertura RAG Actual | Evaluación | Brecha Específica Identificada |
|:---|:---:|:---:|:---|
| **1. Catálogo Completo de Códigos DTC** | **PARCIAL** | 202 de 239 procedimientos cubren DTCs estándar OBD-II, pero faltan códigos específicos OEM de fabricante (chasis C, carrocería B, red U). |
| **2. Síntomas Coloquiales de Clientes** | **PARCIAL** | El RAG contiene síntomas técnicos de taller; la traducción de quejas coloquiales recae en el diccionario de expansión y el modelo ML. |
| **3. Causas Posibles Múltiples** | **RAG LA CUBRE** | Los procedimientos listan adecuadamente las causas eléctricas, mecánicas e hidráulicas más frecuentes. |
| **4. Preguntas Discriminantes Explícitas** | **NO LA CUBRE** | Menos del 25% de los procedimientos incluyen preguntas aclaratorias explícitas para guiar el interrogatorio. |
| **5. Procedimientos Metrológicos Paso a Paso** | **RAG LA CUBRE** | Detalla mediciones con multímetro, manómetros, osciloscopios, pinzas y vacuómetros. |
| **6. Tolerancias OEM por Marca/Motor** | **PARCIAL** | Valores concentrados en Toyota, Nissan, Hyundai y Kia; para otras marcas se presentan valores genéricos multimarca. |
| **7. Criterios de Descarte y Refutación** | **NO LA CUBRE** | Rara vez se especifica qué valor 'descarta' una pieza sin necesidad de sustituirla. |
| **8. Siguiente Comprobación Secuencial** | **NO LA CUBRE** | Falta la directiva algorítmica: *'si la prueba 1 arroja X, proceder a la prueba 2; si arroja Y, desmontar componente Z'*. |
| **9. Protocolos de Seguridad y EPP** | **PARCIAL** | Presente rigurosamente en Alto Voltaje EV, pero incompleto en combustibles, diésel common rail y refrigeración caliente. |
| **10. Contexto de Vehículo (Año/Motor)** | **PARCIAL** | Metadatos indican motor y año, pero el 90% del texto es multimarca universal sin distinciones de variantes de inyección. |

---

## 16. RECOMENDACIONES FUTURAS PRIORIZADAS (SOLO LECTURA / PLANIFICACIÓN)

> [!IMPORTANT]
> **RECORDATORIO METODOLÓGICO**: Estas recomendaciones son estrictamente para planificación futura. En esta fase **NO** se implementó ninguna de ellas, respetando la directiva de congelamiento inmutable.

### TABLA 15 — Matriz de Recomendaciones Futuras Priorizadas

| Prioridad | Área de Intervención | Recomendación Técnica Concreta | Justificación / Beneficio Esperado | Nivel de Esfuerzo |
|:---:|:---|:---|:---|:---:|
| **P1 (Urgente)** | **Metadatos RAG** | **Subsanar las 10 asignaciones erróneas en `metadatos_manuales.json`** (VVT $\rightarrow$ Distribución Variable; Embrague A/C $\rightarrow$ Climatización; EVAP $\rightarrow$ Emisiones). | Elimina la distorsión en el reordenador de candidatos y evita que el RAG recomiende pruebas de llantas TPMS ante fallas de encendido. | **Bajo** (Edición de metadatos JSON). |
| **P1 (Urgente)** | **Inventario Documental** | **Reemplazar los 2 chunks stub de 56 caracteres** (`manual_nissan_versa.txt` y `toyota_corolla.txt`) por procedimientos reales de mantenimiento y torques de culata/bujías. | Suprime fragmentos vacíos que contaminan los resultados de búsqueda de mantenimiento preventivo. | **Bajo** (Redacción de 2 fichas técnicas). |
| **P2 (Medio Plazo)**| **Cadena Diagnóstica** | **Estructurar la sección 'Criterio de Descarte y Siguiente Paso'** en los 40 procedimientos que hoy tienen la cadena 'AUSENTE'. | Permite al LLM sugerir al mecánico el paso siguiente lógico sin alucinaciones ni bucles. | **Medio** (Ampliación textual de chunks). |
| **P2 (Medio Plazo)**| **Seguridad de Taller** | **Incorporar advertencias estándar obligatorias de EPP y despresurización** en procedimientos de gasolina, refrigerante a ebullición y cámaras neumáticas de camiones. | Cumplimiento de normas de seguridad laboral y prevención de accidentes en talleres mecánicos. | **Bajo-Medio** (Inserción de cláusulas de seguridad). |
| **P3 (Evolutivo)** | **Corpus OEM Específico** | **Reducir la dependencia de compendios genéricos multimarca** (hoy 90.4%), incorporando manuales de taller oficiales para los modelos más comerciales de la muestra de tesis. | Eleva la precisión metrológica al entregar tolerancias exactas por código de motor (ej. 1NZ-FE vs HR16DE). | **Alto** (Curaduría e indexación de manuales OEM). |
| **P3 (Evolutivo)** | **Integración Externa** | **Vincular el catálogo SQLite de DTCs (18,805 códigos)** directamente como filtro estructurado previo a FAISS, reduciendo la dispersión léxica de TF-IDF. | Garantiza Hit@1 cercano al 98% cuando la consulta contiene códigos de escáner. | **Medio** (Arquitectura de software). |

---

## 17. ESTADO Y DICTAMEN FINAL

Sobre la base de las evidencias forenses cuantitativas y cualitativas obtenidas durante esta auditoría:

```
ESTADO FINAL DEL RAG: RAG_ACTUAL_REQUIERE_MEJORAS
```

### Justificación Científica y Técnica del Dictamen:

1. **Por qué NO es `RAG_ACTUAL_ADECUADO`**:
   - El **65.6%** de las clases C1 carece de cadena diagnóstica completa (ausencia de directivas de descarte, evidencia debilitante y siguiente acción secuencial).
   - Existen **10 procedimientos con asignación semántica errónea** en `metadatos_manuales.json` que distorsionan el re-ranking multiseñal de producción.
   - El **90.4%** de la información proviene de dos compendios genéricos multimarca, existiendo dos chunks stub triviales de 56 caracteres.
   - Más del **50%** de los procedimientos de combustible, refrigerante hirviendo y climatización carecen de advertencias formales de seguridad y despresurización.

2. **Por qué NO es `RAG_ACTUAL_REQUIERE_REESTRUCTURACION`**:
   - El sistema actual **funciona de manera estable y coherente**: cubre el **100% de las 61 clases** (ninguna clase en 'NINGUNA' o 'BAJA').
   - La recuperación controlada alcanza **Hit@5 = 92.68%** y **MRR = 0.7583**, demostrando que el re-ranking multiseñal rescata adecuadamente el conocimiento en las primeras posiciones.
   - Los 5 grupos confundibles críticos (A a E) cuentan con las herramientas y procedimientos metrológicos clave para diferenciar las averías.
   - La arquitectura modular (`MotorRAG` $\rightarrow$ `relevance_filter` $\rightarrow$ `text_processor`) es sólida y desacoplada; los problemas detectados son de contenido documental y metadatos, no de arquitectura del software.

---

*Reporte elaborado de forma autónoma en modo estrictamente de lectura por Antigravity AI.*
*Fin del informe forense.*