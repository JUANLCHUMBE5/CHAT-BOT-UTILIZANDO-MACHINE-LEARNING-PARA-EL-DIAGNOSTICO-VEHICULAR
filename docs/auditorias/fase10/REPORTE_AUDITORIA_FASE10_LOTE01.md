# REPORTE DE AUDITORÍA FASE 10 — LOTE 01
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — BLOQUEO DE ENTRENAMIENTO DEFINITIVO ACTIVO  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_01.csv` (200 registros, 5 clases)

---

## 1. Etapa 0 — Verificación del Estado del Proyecto e Inmutabilidad (PRE-FASE 10)

En estricto cumplimiento del principio de reproducibilidad e integridad académica de la tesis, se ejecutó una auditoría criptográfica SHA-256 de todos los artefactos canónicos del sistema antes de procesar el nuevo lote:

### Tabla de Certificación de los 19 Artefactos Canónicos (Fase 8.3)

| # | Componente Canónico | Ruta en Repositorio | Hash SHA-256 Oficial | Estado de Integridad |
|:---:|---|---|---|:---:|
| 1 | `dataset_train` | `machine_learning/data/dataset_sintomas_limpio.csv` | `c94d6e7b88ef72ea20f7be1bbb3d5a61484f33d992dcb52c6b285306f1c52626` | **INMUTABLE (OK)** |
| 2 | `benchmark_dev_60` | `machine_learning/data/benchmark_dev_60_casos.py` | `113b5f190758346ab65200daae921b29251871fb842c95f6f2c288750e75592b` | **INMUTABLE (OK)** |
| 3 | `modelo_diagnostico_falla_prod` | `machine_learning/models/modelo_diagnostico.pkl` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | **INMUTABLE (OK)** |
| 4 | `modelo_sistema_prod` | `machine_learning/models/modelo_sistema.pkl` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | **INMUTABLE (OK)** |
| 5 | `vectorizador_tfidf_prod` | `machine_learning/models/vectorizador_tfidf.pkl` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | **INMUTABLE (OK)** |
| 6 | `modelo_diagnostico_candidata` | `machine_learning/models/fase8_candidata/modelo_diagnostico.pkl` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | **INMUTABLE (OK)** |
| 7 | `modelo_sistema_candidata` | `machine_learning/models/fase8_candidata/modelo_sistema.pkl` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | **INMUTABLE (OK)** |
| 8 | `vectorizador_tfidf_candidata` | `machine_learning/models/fase8_candidata/vectorizador_tfidf.pkl` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | **INMUTABLE (OK)** |
| 9 | `corpus_metadatos_rag` | `machine_learning/manuals/metadatos_manuales.json` | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | **INMUTABLE (OK)** |
| 10 | `indice_faiss` | `machine_learning/manuals/indice_faiss.index` | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | **INMUTABLE (OK)** |
| 11 | `adaptador_modelo_ml` | `backend/src/infrastructure/modelo_ml.py` | `014d3e6f6f9f5c5bc5e6223e748566ce6a1ecdb70842df7afc7037c51b6a5eb4` | **INMUTABLE (OK)** |
| 12 | `motor_rag` | `backend/src/infrastructure/motor_rag.py` | `eaa316a87ecaa1be9b6702d9807d44ae6cb8a87bc4ce7154c83d6fc09c1c5a3c` | **INMUTABLE (OK)** |
| 13 | `rag_relevance_filter` | `backend/src/infrastructure/rag/relevance_filter.py` | `fa3d6aef13639bc38bfe5a1360e13276912c97bababdf94954fc53ee7e2c49cc` | **INMUTABLE (OK)** |
| 14 | `auto_interrogador` | `backend/src/core/diagnostico/auto_interrogador.py` | `2e746e498facea34009641c239edf09fbaca1eaaa6771477e666ac2b213be9c2` | **INMUTABLE (OK)** |
| 15 | `politica_fusion` | `backend/src/core/diagnostico/politica_fusion.py` | `073b97fe07c8891807ac63a23994c42dabb17f71062f7af1469a8627d7789c83` | **INMUTABLE (OK)** |
| 16 | `prompt_builder` | `backend/src/core/diagnostico/prompt_builder.py` | `e0b26f32f278bb108126a31242f4eacd100308e517b99095fbc0c422090c33d2` | **INMUTABLE (OK)** |
| 17 | `text_processor` | `backend/src/core/diagnostico/text_processor.py` | `f7075605f6a0e32512cfe24cb5cc4ffb01cf72cc1ca1dd1cba3cbadf77d3216e` | **INMUTABLE (OK)** |
| 18 | `taxonomia_sistemas` | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `561e95c952effcd002850e484830e0515a2469c152fc7af9933b17e0483f716d` | **INMUTABLE (OK)** |
| 19 | `gestor_diagnostico` | `backend/src/core/gestor_diagnostico.py` | `66bead052676331496a0e737ebe0ab1e6927027e6e19c73c32a43fbe57752330` | **INMUTABLE (OK)** |

**Conclusión Etapa 0:** 19/19 artefactos congelados 100% idénticos e intactos. Cero discrepancias.

---

## 2. Etapa 1 — Auditoría Estructural del Archivo `dataset_fase10_lote_01.csv`

| Parámetro Evaluado | Requisito Esperado | Valor Observado | Estado |
|---|---|---|:---:|
| Codificación de archivo | UTF-8 estricto | UTF-8 sin BOM, decodificación limpia | **CONFORME** |
| Total registros | 200 registros | 200 filas | **CONFORME** |
| Columnas requeridas | 16 columnas específicas | 16 columnas exactas | **CONFORME** |
| Cobertura de clases | 5 clases | 5 clases | **CONFORME** |
| Balance por clase | 40 registros por clase | 40 registros por clase (exacto) | **CONFORME** |
| Distribución por nivel | 50 L1 / 75 L2 / 75 L3 | 50 L1 (25%) / 75 L2 (37.5%) / 75 L3 (37.5%) | **CONFORME** |
| Unicidad de identificadores | IDs únicos (F10-L01-0001 a 0200) | 200 IDs únicos sin colisiones | **CONFORME** |
| Coherencia Taxonómica | Pertenecer a `modelo.classes_` (61) | 5/5 clases presentes en el catálogo canónico | **CONFORME** |
| Coherencia Macro-Sistema | Coincidir con `FALLA_A_SISTEMA` | 200/200 registros asignados a `MOTOR` | **CONFORME** |

### Clases Incluidas en el Lote 01:
1. `Falla en bujias o bobinas de encendido (misfire)`: 40 registros
2. `Bomba de gasolina quemada o con baja presion`: 40 registros
3. `Inyectores sucios o filtro de combustible obstruido`: 40 registros
4. `Falla en sensor de oxigeno o mezcla rica`: 40 registros
5. `Cuerpo de aceleracion o valvula IAC sucia`: 40 registros

---

## 3. Etapa 2 — Auditoría de Calidad Técnica, Semántica y Detección de Fugas (Leakage)

Se realizó un análisis combinando análisis léxico, normalización fonética y cálculo matricial de similitud TF-IDF/coseno contra:
- Corpus del propio lote (similitud intra-lote).
- Dataset TRAIN canónico (`dataset_sintomas_limpio.csv`: 2,481 muestras).
- DEV 60 histórico (`benchmark_dev_60_casos.py`).
- Benchmark TEST Ciego 100 (`benchmark_test_ciego_100.py`).
- Benchmarks G1 y G2 (`benchmark_v4_g1_casos.py`, `benchmark_v4_g2_casos.py`).
- Muestra de campo real de 60 casos (`casos_reales_mecanicos_evaluacion.csv`).

### Resumen Global de Clasificación de Registros:

| Estado | Cantidad | Porcentaje | Acción Requerida |
|---|:---:|:---:|---|
| **APROBADO** | **185** | **92.5%** | Preseleccionados para consolidación en corpus maestro Fase 10. |
| **REVISAR** | **11** | **5.5%** | Corrección de artefactos agramaticales de plantillas sintéticas. |
| **RECHAZADO** | **4** | **2.0%** | Exclusión inmediata por contradicción de etiquetado en duplicados exactos. |
| **Total** | **200** | **100.0%** | Auditoría integral completada. |

---

## 4. Detalle de Problemas Encontrados y Hallazgos Críticos

### A. Registros Rechazados (4 casos — Duplicados Exactos con Etiquetas Contradictorias)
Se identificó una colisión donde el mismo texto de usuario fue asignado a dos clases diagnósticas diferentes:

1. **`F10-L01-0001` vs `F10-L01-0081`:**
   - Texto: *"Mi carro tironea."*
   - `F10-L01-0001` etiqueta: `Falla en bujias o bobinas de encendido (misfire)`
   - `F10-L01-0081` etiqueta: `Inyectores sucios o filtro de combustible obstruido`
   - **Impacto:** Si ambas muestras entraran a entrenamiento, generarían ruido y degradarían la frontera de decisión del clasificador lineal SVM.
2. **`F10-L01-0006` vs `F10-L01-0086`:**
   - Texto: *"Hola, el motor tironea."*
   - `F10-L01-0006` etiqueta: `Falla en bujias o bobinas de encendido (misfire)`
   - `F10-L01-0086` etiqueta: `Inyectores sucios o filtro de combustible obstruido`

### B. Registros para Revisar (11 casos — Artefactos Agramaticales de Plantilla)
La generación sintética concatenó plantillas fijas con cadenas nominales o verbales desalineadas:

| ID | Texto Observado | Defecto Semántico / Plantilla |
|---|---|---|
| `F10-L01-0008` | *"El carro comenzó a motor tiembla."* | Fusión forzada de plantilla con frase verbal no conjugada. |
| `F10-L01-0012` | *"Cuando voy al acelerar fuerte, el motor ratea..."* | Construcción anómala "al acelerar fuerte" como locución adverbial forzada. |
| `F10-L01-0017` | *"Cuando está al acelerar fuerte, ratea..."* | Mismo patrón repetitivo de plantilla. |
| `F10-L01-0048` | *"El caro comenzó a se queda sin potencia."* | Fusión agramatical con error ortográfico inducido ("El caro comenzó a..."). |
| `F10-L01-0055` | *"Al manejar despues de manejar un rato..."* | Redundancia sintética evidente. |
| `F10-L01-0088` | *"El carro comenzó a ralenti irregular."* | Fusión agramatical de plantilla. |
| `F10-L01-0095` | *"Al manejar despues de varias horas parado..."* | Redacción incoherente (el auto no maneja estando parado). |
| `F10-L01-0128` | *"El carro comenzó a sale humo oscuro."* | Fusión agramatical ("comenzó a sale..."). |
| `F10-L01-0135` | *"Al manejar despues de calentar..."* | Frase incompleta de plantilla. |
| `F10-L01-0168` | *"El carro comenzó a rpm suben y bajan."* | Fusión agramatical de plantilla. |
| `F10-L01-0172` | *"Cuando voy en semaforo..."* | Locución forzada no natural. |

### C. Auditoría de Fuga hacia Benchmarks (Leakage)
- **Leakage con TEST Ciego 100:** **0 registros** (similitud máxima < 0.68).
- **Leakage con DEV 60:** **0 registros** (similitud máxima < 0.71).
- **Leakage con Casos Reales de Tesis (60 casos):** **0 registros** (similitud máxima < 0.62).
- **Conclusión:** El Lote 01 se encuentra completamente libre de contaminación contra los conjuntos de prueba y validación de campo.

### D. Calidad de Casos Contrastivos y Códigos DTC
- **Casos Contrastivos:** Todos los casos marcados con `es_contrastivo = SI` especifican una clase contrastiva válida perteneciente al catálogo de 61 clases (e.g. `Bomba de gasolina quemada...` vs `Falla en regulador...`, `Misfire` vs `IAC sucia`, `Inyectores` vs `Bomba`).
- **Códigos DTC:** Los códigos utilizados (`P0300`, `P0303`, `P0230`, `P0231`, `P0201`, `P0204`, `P0133`, `P0172`, `P0506`, `P0507`) son 100% estándar, válidos y pertinentes a sus clases de falla. No se hallaron códigos DTC asignados erróneamente a síntomas L1.

---

## 5. Detección de la Segunda Revisión (`dataset_fase10_lote_01 (1).csv`)

Durante la inspección de fuentes, se localizó y analizó la revisión posterior descargada a las 14:38 (`dataset_fase10_lote_01 (1).csv`, provista también en el mensaje del usuario):
- **Registros:** 200 filas exactas.
- **Resultado de auditoría:** **200 APROBADO (100%)**, 0 REVISAR, 0 RECHAZADO.
- **Mejoras clave:**
  - Se eliminaron los duplicados exactos entre Misfire e Inyectores.
  - Se reescribieron los textos sintéticos forzados por redacciones naturales de taller y lenguaje cotidiano.
  - Cero duplicados exactos y cero fugas contra los benchmarks.

---

## 6. Etapa 3 — Bloqueo Obligatorio de Entrenamiento Definitivo

En cumplimiento estricto de las directivas metodológicas:

> **REGLA DE SALVAGUARDA DE FASE 10:**  
> Al disponer únicamente del Lote 01 (5 de las 61 clases del sistema, cobertura de 8.2%), **QUEDA TERMINANTEMENTE PROHIBIDO**:
> 1. Generar un modelo definitivo o promocionar candidatos a producción.
> 2. Modificar o sobrescribir el dataset canónico `dataset_sintomas_limpio.csv`.
> 3. Entrenar sobre conjuntos desbalanceados que sesgarían el clasificador SVM.

Cualquier prueba técnica ejecutada antes de completar el corpus de 61 clases se catalogará estrictamente como **`EXPERIMENTAL_PARCIAL`** en aislamiento total de los artefactos de producción.

---

## 7. Preparación de la Arquitectura de Fase 10

Se implementó el pipeline modular en [`machine_learning/training/fase10/pipeline_fase10.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/machine_learning/training/fase10/pipeline_fase10.py) con las siguientes capacidades:

1. **`AuditorLoteFase10`:** Valida automáticamente lotes entrantes (`dataset_fase10_lote_02.csv`, `03`, etc.) bajo las mismas reglas de calidad.
2. **`GestorMasterFase10`:** Almacena los registros aprobados en un dataset maestro aislado:  
   `machine_learning/data/fase10/dataset_fase10_master.csv`  
   Conservando trazabilidad de: `source_dataset`, `source_row_id`, `id_grupo`, `source_type`, `specificity_level`, `synthetic_or_original`.
3. **`PoliticaEntrenamientoFase10`:** Aplica bloqueo programático si la cobertura de clases es menor a 61.

---

## 8. Recomendaciones para el Lote 02

Para la generación del Lote 02 y lotes subsiguientes:
1. **Evitar sintaxis de plantilla fija:** En lugar de concatenar `"comenzó a + [síntoma_raw]"`, utilizar verbos conjugados y construcciones reales de usuarios (*"de pronto empezó a temblar", "noto que el motor se jalona"*).
2. **Evitar síntomas idénticos ultra-cortos compartidos entre clases vecinas:** Frases de una sola palabra o dos como *"Mi carro tironea"* no deben asignarse como verdad absoluta a una sola clase si no incluyen un diferenciador contextual L2/L3.
3. **Mantener la consistencia en IDs y grupos:** Asegurar que cada grupo `id_grupo` agrupe las variantes y paráfrasis del mismo escenario para el futuro GroupSplit.
4. **Priorizar clases de sistemas no cubiertos:** Dirigir el Lote 02 hacia macro-sistemas como `FRENOS`, `TRANSMISION` y `SUSPENSION_CHASIS`.
