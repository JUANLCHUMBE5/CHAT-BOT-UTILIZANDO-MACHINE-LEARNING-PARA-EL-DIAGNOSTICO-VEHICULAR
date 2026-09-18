# REPORTE DE PREPARACIÓN EXPERIMENTAL CONTROLADA — FASE 10 (ETAPA 2)
## CarBot: Generación y Congelamiento de TRAIN10, DEV10 y TEST10 Ciego

**Fecha**: 17 de Septiembre de 2026  
**Entorno**: Antigravity IDE / Python 3.14  
**Estado Final**: `PREPARACION_EXPERIMENTAL_FASE10_APROBADA`  

---

## 1. Verificación Inicial y Final de Inmutabilidad de Fase 8.3

Se ejecutó la verificación mediante `scratch/verify_immutability.py` tanto al inicio del proceso como al concluir todas las operaciones de particionamiento y generación de artefactos.

| Componente Auditado | Ruta de Archivo | Hash SHA-256 Registrado | Estado Inicial | Estado Final |
| :--- | :--- | :--- | :---: | :---: |
| `dataset_train` | `machine_learning/data/dataset_sintomas_limpio.csv` | `c94d6e7b88ef72ea20f7be1bbb3d5a61484f33d992dcb52c6b285306f1c52626` | INMUTABLE | INMUTABLE |
| `benchmark_dev_60` | `machine_learning/data/benchmark_dev_60_casos.py` | `113b5f190758346ad4775d7e7c4f420e6e7ea8a4ff82dc528c31cb1c79e61fd4` | INMUTABLE | INMUTABLE |
| `modelo_diagnostico_falla_prod`| `backend/src/infrastructure/ml/modelo_diagnostico.pkl` | `3d8199595b69bb0170a4a83685672ea3d2f9cb0e104f05ea5bf45b103e3b3c3b` | INMUTABLE | INMUTABLE |
| `modelo_sistema_prod` | `backend/src/infrastructure/ml/modelo_sistema.pkl` | `22d11492e9576664d4bf5aa50454316dffef828cb0f7dbbcaaa79326e5a0e5b7` | INMUTABLE | INMUTABLE |
| `vectorizador_tfidf_prod` | `backend/src/infrastructure/ml/vectorizador_tfidf.pkl` | `8b8e8c3b3571fe969443743c3aebfc70eb351119b9bc8676bfaf945037d2f928` | INMUTABLE | INMUTABLE |
| `modelo_diagnostico_candidata` | `machine_learning/models/fase8_candidata/modelo_diagnostico.pkl` | `3d8199595b69bb0170a4a83685672ea3d2f9cb0e104f05ea5bf45b103e3b3c3b` | INMUTABLE | INMUTABLE |
| `modelo_sistema_candidata` | `machine_learning/models/fase8_candidata/modelo_sistema.pkl` | `22d11492e9576664d4bf5aa50454316dffef828cb0f7dbbcaaa79326e5a0e5b7` | INMUTABLE | INMUTABLE |
| `vectorizador_tfidf_candidata` | `machine_learning/models/fase8_candidata/vectorizador_tfidf.pkl` | `8b8e8c3b3571fe969443743c3aebfc70eb351119b9bc8676bfaf945037d2f928` | INMUTABLE | INMUTABLE |
| `corpus_metadatos_rag` | `machine_learning/data/fase8_corpus_metadata.json` | `2f0684477522efb6d19f564fb32eb34bf74534f378038bfe43818e6ca6f50b4d` | INMUTABLE | INMUTABLE |
| `indice_faiss` | `machine_learning/data/fase8_faiss.index` | `757c4b006a8995f4c478a87b320bc69cfa74ffca35f1ffb2fecdafffe6937e28` | INMUTABLE | INMUTABLE |
| `adaptador_modelo_ml` | `backend/src/infrastructure/ml/adaptador_modelo_ml.py` | `014d3e6f6f9f5c5bd60cb1056a29ec12d2ebdf4061a99a77b7ee38c1c4e12c19` | INMUTABLE | INMUTABLE |
| `motor_rag` | `backend/src/infrastructure/rag/motor_rag.py` | `eaa316a87ecaa1be4cf7806f0aeebcf4c4c23c6c06834d5ea3bc815dc3df4ce1` | INMUTABLE | INMUTABLE |
| `rag_relevance_filter` | `backend/src/infrastructure/rag/rag_relevance_filter.py` | `fa3d6aef13639bc337e75e9fca2e21b8bbfaf32b6e15d86241a502ef0efce263` | INMUTABLE | INMUTABLE |
| `auto_interrogador` | `backend/src/core/diagnostico/auto_interrogador.py` | `2e746e498facea34559beaa8f52feee0bebc3a2d59666cf776999b7941fa98a2` | INMUTABLE | INMUTABLE |
| `politica_fusion` | `backend/src/core/diagnostico/politica_fusion.py` | `073b97fe07c8891823194a6d1369cfb358e658a5c317544062145b8cae6a6449` | INMUTABLE | INMUTABLE |
| `prompt_builder` | `backend/src/infrastructure/gemini/prompt_builder.py` | `e0b26f32f278bb10906a256a2818610ebcb15ecb99ca868ee3a436577fc4e877` | INMUTABLE | INMUTABLE |
| `text_processor` | `backend/src/core/diagnostico/text_processor.py` | `f7075605f6a0e32560ce0f6d50ffeb23e80cba0c9a72b508f75a666e66e2c315` | INMUTABLE | INMUTABLE |
| `taxonomia_sistemas` | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `561e95c952effcd04396ef1a5e1cf490f89839958784d80a13d706a77bb28e93` | INMUTABLE | INMUTABLE |
| `gestor_diagnostico` | `backend/src/core/diagnostico/gestor_diagnostico.py` | `66bead0526763314cfb5c3eb699a2fe9559c5d15cb0b11a43a0d5c02dc2c07ef` | INMUTABLE | INMUTABLE |

**Resultado**: **19 / 19 artefactos idénticos e inalterados (100% de inmutabilidad preservada)**.

---

## 2. Auditoría del Snapshot del Corpus Fase 10

- **Archivo Original**: `machine_learning/data/fase10/dataset_fase10_master_v1_2440.csv`
- **Hash SHA-256 Esperado**: `a645c7198faf7d3fad0af9cb681477f75e5f72292e09c442d899c286073bb232`
- **Hash SHA-256 Encontrado**: `a645c7198faf7d3fad0af9cb681477f75e5f72292e09c442d899c286073bb232`
- **Coincidencia Exacta**: **SÍ**
- **Dimensiones**: 2440 filas, 61 clases canónicas (exactamente 40 registros por clase).
- **Distribución de Especificidad**: L1 = 610, L2 = 915, L3 = 915.
- **Linaje e IDs**: 2440 IDs únicos (`F10-0001` a `F10-2440`), 2440 grupos únicos (`G-0001` a `G-2440`).

---

## 3. Investigación y Resolución de la Categoría "COLOQUIAL"

### A. Diagnóstico de la Anomalía
En la auditoría global de Fase 10 se detectaron 153 registros etiquetados con `tipo_lenguaje = "COLOQUIAL"`.
La investigación reveló:
- **Lotes Afectados**: Lote 09 (52 registros), Lote 10 (66 registros), Lote 11 (35 registros).
- **Clases Afectadas**: 15 clases pertenecientes a los macro-sistemas `ELECTRICO`, `CLIMATIZACION` y `CARROCERIA_CONFORT`.
- **Distribución por Nivel**: L1 = 118 registros, L2 = 35 registros, L3 = 0 registros.
- **Causa Raíz**: En los scripts generadores auxiliares de dichos lotes (`lote09_*.py`, `lote10_*.py`, `lote11_*.py`), el desarrollador utilizó el término `COLOQUIAL` como sinónimo descriptivo directo de `COTIDIANO`.
- **Revisión Semántica de Muestra (30 registros)**: Los textos correspondían genuinamente a expresiones coloquiales de usuarios finales y conductores cotidianos (e.g. *"no echa aire frio"*, *"se bajaron las luces de golpe"*). No existía divergencia de significado con `COTIDIANO`.
- **Dependencia del Pipeline**: El pipeline de inferencia no condiciona su vectorización a `tipo_lenguaje`, pero la taxonomía canónica exige consistencia en los 5 registros autorizados: `COTIDIANO`, `TALLER`, `TECNICO`, `WHATSAPP`, `ERROR_ORTOGRAFICO`.

### B. Decisión Metodológica (CASO A)
Se aplicó normalización de etiqueta: **`COLOQUIAL -> COTIDIANO`**.
- Ningún texto de usuario, clase, nivel, `id_grupo`, síntoma o evidencia fue alterado.
- Para proteger la inmutabilidad del snapshot original `v1`, se creó la versión derivada:
  - **Archivo**: `machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv`
  - **SHA-256**: `6ccb8873092da94f5a5415303f07b8caf50a8f3850605b9c2b17b5d96ab1d445`
  - **Log de Modificaciones**: `machine_learning/data/fase10/fase10_reporte_normalizacion_coloquial.csv` (153 filas registradas con ID y trazabilidad).

---

## 4. Auditoría del Train Canónico Original y Capa de Trazabilidad

- **Archivo Original**: `machine_learning/data/dataset_sintomas_limpio.csv`
- **Hash SHA-256**: `c94d6e7b88ef72ea20f7be1bbb3d5a61484f33d992dcb52c6b285306f1c52626`
- **Total Filas**: 6189 registros.
- **Total Clases**: 61 clases canónicas.
- **Duplicados Exactos**: 0.
- **Capa de Trazabilidad Construida**:
  - Para evitar *leakage* por paráfrasis históricas, se aplicó el extractor de raíz sintomática `norm_g()`, agrupando las 6,189 filas en **4,832 grupos homogéneos de paráfrasis** (`G-ORIG-0001` a `G-ORIG-4832`).
  - Columnas añadidas en la copia derivada de trabajo:
    - `id`: `ORIG-0001` a `ORIG-6189`.
    - `id_grupo`: `G-ORIG-xxxx`.
    - `source_dataset`: `dataset_sintomas_limpio.csv`.
    - `source_row_id`: `0` a `6188`.
    - `source_type`: `ORIGINAL`.
    - `synthetic_or_original`: `ORIGINAL`.
    - `specificity_level`: `ORIGINAL_NO_ESTRATIFICADO`.

---

## 5. Pool de Desarrollo y Detección de Colisiones Pre-Split

- **Composición del Pool**:
  - Original derivado: 6,189 filas.
  - Fase 10 auditado: 2,440 filas.
  - **Total Inicial**: **8,629 registros**.
- **Auditoría Pre-Split Original vs Fase 10**:
  - Duplicados exactos: 0.
  - Duplicados normalizados: 0.
  - Similitud máxima combinada (TF-IDF): `0.7332` (muy inferior al umbral de colisión `0.88`).
  - Conflictos de etiqueta: 0.

---

## 6. Generación y Validación de los Splits TRAIN10 / DEV10

Se implementó una partición controlada respetando el principio: **`GROUP INTEGRITY > PERFECT STRATIFICATION`**.

- **Método**:
  - Registros Originales: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)` sobre los 4,832 grupos de paráfrasis.
  - Registros Fase 10: `GroupSplit` determinista estratificado por clase y nivel (L1: 8 train / 2 dev; L2: 12 train / 3 dev; L3: 12 train / 3 dev) preservando cada `id_grupo` intacto.

### A. Resultados de la Partición

| Métrica / Atributo | TRAIN10 (`train10_v1.csv`) | DEV10 (`dev10_v1.csv`) | Total Pool Combinado |
| :--- | :---: | :---: | :---: |
| **Total Registros** | **6,904** (80.01%) | **1,725** (19.99%) | 8,629 (100.0%) |
| **Clases Representadas** | 61 / 61 (100%) | 61 / 61 (100%) | 61 / 61 |
| **Registros Originales** | 4,952 | 1,237 | 6,189 |
| **Registros Sintéticos Fase 10** | 1,952 | 488 | 2,440 |
| **Sintéticos L1** | 488 | 122 | 610 |
| **Sintéticos L2** | 732 | 183 | 915 |
| **Sintéticos L3** | 732 | 183 | 915 |
| **Grupos Únicos (`id_grupo`)** | 5,819 (3,867 orig + 1,952 synth) | 1,453 (965 orig + 488 synth) | 7,272 |
| **Hash SHA-256** | `ec407886b48d66c4d9be6fc8b72decf605f4f94ac1af0575d9c4fa0db005e92b` | `b44a752ca58fb4e27c7d9167198747e076d0c3cd5c4b07eaa03919777d1fd2b6` | — |

### B. Validación de Integridad y Aislamiento TRAIN10 vs DEV10
- **Intersección de IDs**: **0**.
- **Intersección de `id_grupo`**: **0**.
- **Duplicados exactos de texto**: **0**.
- **Duplicados normalizados**: **0**.
- **Near-duplicates sintéticos (Fase 10 vs Fase 10 / Fase 10 vs Original)**: **0**.
- **Near-duplicates intra-originales históricos**: 327 pares (procedentes exclusivamente de variaciones de aumento de frases cortas de la base histórica de 6,189 casos, con 318 coincidencias en la misma clase).
- **Archivos Generados**: `train10_v1.csv`, `dev10_v1.csv`, `SPLIT10_MANIFEST.json`, `fase10_auditoria_train_dev.csv`, `fase10_leakage_train_dev.csv`.

---

## 7. Construcción, Auditoría y Congelamiento de TEST10 Ciego

Se construyó un benchmark completamente nuevo e independiente de **366 casos** (6 casos por clase: 2 L1, 2 L2, 2 L3).

### A. Especificaciones Estructurales
- **Total Filas**: 366.
- **Total Clases**: 61 clases exactas (6 casos por clase).
- **Distribución de Niveles**: L1 = 122, L2 = 122, L3 = 122.
- **Códigos DTC en L1**: **0 casos con DTC**.
- **Interacción en L1**: **122 / 122 casos con `requiere_pregunta = "SI"`**.
- **Tipos de Lenguaje**: Balanceado entre `COTIDIANO`, `TALLER`, `TECNICO`, `WHATSAPP` y `ERROR_ORTOGRAFICO`.
- **Casos Contrastivos**: Pares diferenciales representativos en sistemas acoplados (misfire vs inyectores vs compresión; bomba gasolina vs FSCM; VVT vs distribución; catalizador vs sensor O2 vs DPF; booster vs fuga hidráulica; embrague vs caja de cambios; alternador vs batería vs fuga parasitaria; tracción EV vs inversor IGBT vs refrigeración HV).

### B. Auditoría de No-Contaminación contra Todo el Universo (8,927 Referencias)
Se auditó TEST10 contra la totalidad de fuentes del proyecto (Train original 6,189, Fase 10 2,440, DEV-60 histórico, TEST-100 histórico, G1, G2, Casos Reales FIELD y Casos Históricos de A/C):
- **Duplicados Exactos**: **0**.
- **Duplicados Normalizados**: **0**.
- **Máxima Similitud TF-IDF contra el Universo**: `0.7812` (límite de alerta: `0.88`).
- **Similitud Promedio con el Universo**: `0.3165`.
- **Near-duplicates (>= 0.88)**: **0**.
- **Máxima Similitud Intra-TEST10**: `0.3613` (límite de alerta: `0.90`).
- **Reporte de Fuga**: `machine_learning/data/fase10/fase10_leakage_test10.csv` (0 filas registradas).

### C. Auditoría Específica de la Clase 54 (Climatización vs Motor)
Para la clase *Falla en compresor de aire acondicionado o fuga de gas R134a*, se generaron 6 casos independientes:
- `TEST10-0319` (L1, COTIDIANO): Aire tibio por rejillas a máximo frío sin enfriar cabina.
- `TEST10-0320` (L1, WHATSAPP): Ventilador sopla fuerte pero sin clic de compresor ni frío.
- `TEST10-0321` (L2, TALLER): Enfría en autopista pero se calienta en ralentí (fallo motoventilador/condensador vs refrigeración motor).
- `TEST10-0322` (L2, TALLER): Manómetro de baja en vacío (10 psi) y alta en 80 psi por fuga paulatina de gas R134a.
- `TEST10-0323` (L3, TECNICO): Termometría en tobera a 22°C (nominal 5°C-8°C), recalentamiento de evaporador fuera de rango.
- `TEST10-0324` (L3, TECNICO): Detector halógeno acústico en retén de eje de compresor denso denota microfuga; contraste con sensor ECT de motor normal.
- **Similitud Máxima contra Caso Histórico**: `0.4462` (aislamiento garantizado, cero copia del benchmark Corolla ni de reportes previos).

### D. Revisión Semántica del 100%
Se auditó de forma unitaria la totalidad de los 366 casos bajo los criterios de longitud mínima, correspondencia taxonómica estricta con `FALLA_A_SISTEMA`, formato SAE J2012 de códigos DTC, reglas de nivel L1/L2/L3, naturalidad coloquial y ausencia total de pistas artificiales.
- **Casos Auditados**: 366 / 366.
- **Aprobados**: **366 (100.0%)**.
- **Revisar / Rechazados**: **0**.

### E. Congelamiento y Hash
- **Archivo de Benchmark**: `machine_learning/data/fase10/test10_fase10_blind_v1.csv`
- **Hash SHA-256**: `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c`
- **Manifiesto**: `machine_learning/data/fase10/TEST10_MANIFEST.json`
- **Estado**: `LOCKED_BLIND_TEST`.

---

## 8. Inventario de Benchmarks Externos y Regresiones Históricas

Se formalizó el manifiesto `REGRESSION_BENCHMARKS_MANIFEST.md`, ratificando la exclusión obligatoria de entrenamiento para los siguientes conjuntos:
1. **TEST-100 Histórico**: 100 casos (`prohibido_entrenamiento = SI`).
2. **DEV-60 Histórico**: 60 casos (`prohibido_entrenamiento = SI`).
3. **G1 (Estrés Multimarca)**: 50 casos (`prohibido_entrenamiento = SI`).
4. **G2 (Jerga Mecánica)**: 50 casos (`prohibido_entrenamiento = SI`).
5. **FIELD-60 (Muestra Oficial Real)**: 32 casos actuales (`prohibido_entrenamiento = SI`).
6. **Regresión Histórica A/C**: 6 casos (`prohibido_entrenamiento = SI`).
7. **Regresiones Mecánicas Puras**: 20 casos (`prohibido_entrenamiento = SI`).

**Contaminación detectada en TRAIN10 / DEV10**: **0% (0 casos incorporados)**.

---

## 9. Configuración del Futuro Candidato (Etapa 3)

De acuerdo con las restricciones metodológicas, **no se ejecutó ningún entrenamiento (`fit()`), calibración ni optimización de hiperparámetros en esta etapa**.

La arquitectura y pipeline preestablecido para el futuro candidato de Fase 10 es:
- **Modelo Base**: `LinearSVC` (Linear Support Vector Machine multiclase en esquema One-vs-Rest).
- **Vectorizador de Texto**: `TfidfVectorizer` con:
  - `ngram_range = (1, 2)`
  - `lowercase = True`
  - `strip_accents = 'unicode'`
  - `sublinear_tf = True`
  - `min_df = 1`
  - Preservación explícita de negaciones léxicas (sin supresión indiscriminada de stopwords).
- **Objetivo Científico**: Aislar rigurosamente el efecto de la incorporación del corpus estratificado Fase 10 manteniendo idéntica la arquitectura base de Fase 8.3.

---

## 10. Resumen de Artefactos Creados

1. `machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv`
2. `machine_learning/data/fase10/fase10_reporte_normalizacion_coloquial.csv`
3. `machine_learning/data/fase10/train10_v1.csv`
4. `machine_learning/data/fase10/dev10_v1.csv`
5. `machine_learning/data/fase10/test10_fase10_blind_v1.csv`
6. `machine_learning/data/fase10/SPLIT10_MANIFEST.json`
7. `machine_learning/data/fase10/TEST10_MANIFEST.json`
8. `machine_learning/data/fase10/REGRESSION_BENCHMARKS_MANIFEST.md`
9. `machine_learning/data/fase10/fase10_auditoria_train_dev.csv`
10. `machine_learning/data/fase10/fase10_auditoria_test10.csv`
11. `machine_learning/data/fase10/fase10_leakage_train_dev.csv`
12. `machine_learning/data/fase10/fase10_leakage_test10.csv`
13. `machine_learning/data/fase10/REPORTE_PREPARACION_EXPERIMENTAL_FASE10.md`
14. Scripts auxiliares reproducibles en `scratch/`.

---

## 11. Conclusión y Estado Final

Todas las pruebas de integridad, consistencia matemática, no-contaminación y blindaje experimental han sido superadas satisfactoriamente.

**ESTADO FINAL DE LA ETAPA 2**:  
`PREPARACION_EXPERIMENTAL_FASE10_APROBADA`
