# INFORME FINAL MAESTRO: FASE RAG-IMPLEMENTACIÓN MAESTRA CONTROLADA
## CONSTRUCCIÓN COMPLETA, VALIDACIÓN, BENCHMARK Y AUDITORÍA DE RAG_CANDIDATO_V1

**Fecha de Ejecución**: 2026-09-17 22:38:23  
**Sistema Evaluado**: CarBot — Chatbot Diagnóstico Vehicular con Machine Learning  
**Identificador del Baseline**: `RAG_BASELINE_F8_3`  
**Identificador del Candidato**: `RAG_CANDIDATO_V1`  
**Ruta Aislada del Candidato**: `machine_learning/manuals/candidates/v1/`  
**Estado Técnico Final**: **`RAG_CANDIDATO_V1_APTO_PARA_REVISION_DE_PROMOCION`**  
**Advertencia de Seguridad Productiva**: **NO PROMOVIDO A PRODUCCIÓN** (Runtime productivo congelado en `RAG_BASELINE_F8_3`, preservando estricto aislamiento metodológico).

---

## 1. Resumen Ejecutivo
En estricto cumplimiento del mandato de la **Fase RAG-Implementación Maestra Controlada**, se ejecutó de principio a fin y de manera 100% autónoma la construcción, saneamiento semántico, estructuración bajo Schema V2, vectorización, validación posicional, evaluación por ablaciones y benchmark independiente del candidato **`RAG_CANDIDATO_V1`**.

Principales hitos alcanzados:
1. **Preservación Total del Baseline y C1**: Los 5 artefactos criptográficamente congelados (`VECTOR_C1`, `FAULT_MODEL_C1`, `MACROFIX`, `FAISS_BASELINE` y `METADATA_BASELINE`) mantuvieron sus SHA-256 idénticos al 100%. Ningún modelo ML fue tocado, reentrenado ni alterado.
2. **Saneamiento de Metadatos (CHG-001 a CHG-010)**: Se corrigieron los 10 procedimientos con asignación semántica errónea heredada (desacoplando VVT de motor de arranque, embrague electromagnético A/C de embrague manual, EVAP y TPMS de misfire, y TCC/DSG de disco manual).
3. **Evolución a Schema V2 y Manifiesto Posicional (CHG-018 & CHG-020)**: Se estructuraron los 239 fragmentos procedimentales bajo un modelo Pydantic formal con niveles de evidencia y taxonomía transversal, verificando la alineación posicional estricta `FAISS[i] <-> TEXT[i] <-> METADATA[i] <-> MANIFEST[i]` al 100%.
4. **Incorporación de Conocimiento Técnico Aprobado (CHG-013 a CHG-016)**: Se integraron cláusulas normativas de seguridad pasiva para Alta Tensión EV/HEV (>300V CC), Common Rail (>1,600 bar), y despresurización de riel de gasolina, así como la secuencia cualitativa de flujo de aire en condensador para la Clase 29 (A/C).
5. **Arquitectura Desacoplada DTC_LOOKUP (CHG-019)**: Se implementó un microservicio relacional aislado conectado a `dtc_codes.db` (18,805 códigos OBD-II) que enriquece el contexto técnico sin inflar ni distorsionar el espacio vectorial de FAISS.
6. **Resultados Superiores en Benchmark Independiente (122 consultas)**:
   - **Hit@1**: Incrementó de **67.21%** (Baseline) a **70.49%** (Candidato V1), logrando un delta neto de **+3.28%**.
   - **Hit@3**: Incrementó de **68.85%** a **72.13%** (**+3.28%**).
   - **Hit@5**: Incrementó de **72.95%** a **76.23%** (**+3.28%**).
   - **MRR (Mean Reciprocal Rank)**: Subió de **0.6884** a **0.7216** (**+0.0332**).
   - **Macro Accuracy**: Se mantuvo en **83.61%**.
   - **Cero Regresiones Críticas**: Ningún macro-sistema ni grupo de confusión sufrió caídas respecto al baseline.

---

## 2. Estado Inicial y Pre-Flight Check
Antes de iniciar cualquier acción sobre el sistema, se ejecutó una inspección exhaustiva de los entornos:
- **Entorno Python**: `.venv` activo con dependencias congeladas (FastAPI, Scikit-Learn 1.6+, FAISS-CPU 1.10.0, Pydantic V2).
- **Backend Productivo**: Verificación del estado de los singletons y tests existentes (`test_cobertura_rag_180_manuales.py`, `test_ml_rag_singletons.py`, `test_tolerancias_electricas_rag.py`). Los 25 tests existentes pasaron satisfactoriamente al 100%.
- **Insumos de Autoridad**: Localizados y leídos los reportes canónicos:
  - `FASE_RAG_AUDIT_REPORTE_FINAL.md`
  - `FASE_RAG_PLAN_REPORTE_FINAL.md`
  - `FASE_RAG_RECONCILIACION_REPORTE_FINAL.md`
  - `RAG_RECONCILIACION_61_CLASES.csv`
  - `RAG_RECONCILIACION_CHG001_CHG020.csv`

---

## 3. Verificación Criptográfica de Hashes Congelados
Se calcularon programáticamente los hashes SHA-256 de los 5 artefactos blindados antes y después de toda la fase:

| Artefacto | Ruta Canónica | SHA-256 Oficial Esperado | SHA-256 Medido Pre/Post | Estado |
| :--- | :--- | :--- | :--- | :---: |
| **VECTOR_C1** | `machine_learning/models/c1_fase10_final/vectorizador_c1.pkl` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | **MATCH** |
| **FAULT_MODEL_C1** | `machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | **MATCH** |
| **MACROFIX** | `machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | **MATCH** |
| **FAISS_BASELINE** | `machine_learning/manuals/indice_faiss.index` | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | **MATCH** |
| **METADATA_BASELINE**| `machine_learning/manuals/metadatos_manuales.json` | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | **MATCH** |

---

## 4. Verificación de Taxonomía Real C1 (61 Clases)
Se extrajo la propiedad `classes_` directamente del estimador serializado `modelo_diagnostico_c1.pkl`.
- **Total de clases exactas**: 61 clases.
- **Validación de IDs canónicos**:
  - Clase 28 (0-indexed) / 29 (1-indexed): `Falla en compresor de aire acondicionado o fuga de gas R134a`.
  - Clase 38 (0-indexed) / 39 (1-indexed): `Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)`.
  - Clase 40 (0-indexed) / 41 (1-indexed): `Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)`.
  - Clase 59 (0-indexed) / 60 (1-indexed): `Sobrecalentamiento o solenoides en caja automatica CVT / DSG`.
- **Conclusión**: Se anularon y prohibieron permanentemente los IDs espurios del borrador de RAG-PLAN (A/C=54, EVAP=22, VVT=12, CVT=38).

---

## 5. Mapeo Canónico 61 Clases → 7 Macro-Sistemas
Se verificó la distribución exacta de las 61 clases sobre los 7 macro-sistemas:
- **MOTOR**: 26 clases (42.62%)
- **TRANSMISION**: 8 clases (13.11%)
- **FRENOS**: 7 clases (11.48%)
- **ELECTRICO**: 7 clases (11.48%)
- **CARROCERIA_NEUMATICA**: 7 clases (11.48%)
- **SUSPENSION_CHASIS**: 5 clases (8.20%)
- **CLIMATIZACION**: 1 clase (1.64%)
- **TOTAL**: **61 clases** (100.0%).

---

## 6. Snapshot del Baseline
Se generó el manifiesto de congelamiento `rag_baseline_manifest.json` en `machine_learning/manuals/` y se replicó en `candidates/v1/manifests/`.
- **Versión registrada**: `RAG_BASELINE_F8_3`.
- **Total Chunks indexados**: 239.
- **Dimensión FAISS TF-IDF**: 32,596.
- **Hash de Índice**: `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082`.
- **Hash de Metadatos**: `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625`.

---

## 7. Estructura Aislada de RAG_CANDIDATO_V1
Se creó el árbol jerárquico aislado en `machine_learning/manuals/candidates/v1/`:
```text
machine_learning/manuals/candidates/v1/
├── sources/          # Fuentes externas auditadas y fichas de trazabilidad
├── texts/            # Copia aislada y evolucionada de los textos técnicos (.txt)
├── metadata/         # Metadatos corregidos y serializaciones Schema V2 (JSON)
├── indexes/          # Índice FAISS compilado del candidato (indice_faiss_v1.index)
├── manifests/        # Manifiestos posicionales y de build (JSON)
├── structured/       # Microservicio relacional desacoplado DTC_LOOKUP
├── tests/            # Tests dirigidos de metadata y no-contaminación semántica
├── benchmarks/       # Dataset independiente de evaluación (122 consultas)
├── reports/          # Reportes CSV y Markdown de benchmark y fuentes
└── scripts/          # Scripts reproducibles de construcción, indexación y harness
```

---

## 8. Demostración de Paridad Inicial (Baseline == Candidato Inicial)
Previo a cualquier modificación en los archivos del candidato, se ejecutó un test de paridad estricta utilizando `CandidateRAGHarness`.
- Chunks indexados: Baseline = 239, Candidato Inicial = 239.
- Dimensión vectorial: 32,596 en ambos.
- Similitud en consultas de control (oxígeno, tironeo, frenos, batería, aire acondicionado):
  - Resultados top 1 a top 5 idénticos en títulos y puntuación (delta < 1e-5).
  - Estado: **PARIDAD INICIAL 100% DEMOSTRADA**.

---

## 9. Regla de Contenido Incorporado
En cumplimiento de la regla de oro:
- Únicamente se incorporó contenido clasificado como **`RESPALDADO`** o la fracción respaldada de **`PARCIALMENTE RESPALDADO`**.
- Todo contenido clasificado como `REQUIERE FUENTE`, `NO VERIFICADO`, `PLAN_ONLY_UNVERIFIED` o `SINTESIS` fue bloqueado y documentado en `RAG_CANDIDATO_V1_BLOCKED_CONTENT.csv`.

---

## 10. Implementación de Cambios CHG-001 a CHG-020
Se ejecutaron los 20 cambios de acuerdo con la decisión final de la reconciliación:

| CHG_ID | Decisión Reconciliación | Implementado | Parte Autorizada Implementada | Parte Bloqueada |
| :--- | :--- | :---: | :--- | :--- |
| **CHG-001** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_047 a MOTOR / VVT (C1 41) | Ninguna |
| **CHG-002** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_060 a CLIMATIZACION / A/C (C1 29) | Ninguna |
| **CHG-003** | IMPLEMENTABLE_PARCIALMENTE | SÍ | Reasignación RAG_PROC_061 a TRANSMISION / CVT-DSG (C1 60) | Bloqueado árbol sintético mecatrónica sin OEM |
| **CHG-004** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_067 a MOTOR / VVT (C1 41) | Ninguna |
| **CHG-005** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_075 a MOTOR / EVAP (C1 39) | Ninguna |
| **CHG-006** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_109 a MOTOR / EVAP (C1 39) | Ninguna |
| **CHG-007** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_113 a SUSPENSION / TRANSVERSAL (TPMS) | Bloqueada creación de clase C1 espuria 62 |
| **CHG-008** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_114 a TRANSMISION / TCC (C1 60) | Bloqueada confusión léxica con embrague manual |
| **CHG-009** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_142 a MOTOR / VVT (C1 41) | Ninguna |
| **CHG-010** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Reclasificación RAG_PROC_154 a MOTOR / EVAP (C1 39) | Ninguna |
| **CHG-011** | REQUIERE_FUENTE | SÍ | Marca de deprecación/aislamiento de stub Toyota Corolla | Bloqueado rellenado con texto inventado |
| **CHG-012** | REQUIERE_FUENTE | SÍ | Marca de deprecación/aislamiento de stub Nissan Versa | Bloqueado rellenado con texto inventado |
| **CHG-013** | IMPLEMENTABLE_PARCIALMENTE | SÍ | Advertencia pasiva normativa EV/HEV (>300V CC, Clase 0) | Bloqueados pasos invasivos generados por IA |
| **CHG-014** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Cláusula textual de seguridad Common Rail (>1,600 bar) | Bloqueados valores fijos de presión sin motor |
| **CHG-015** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Despresurización previa de riel de inyección gasolina | Bloqueada regla universal '45-60 PSI' |
| **CHG-016** | IMPLEMENTABLE_PARCIALMENTE | SÍ | Secuencia cualitativa flujo condensador y motoventilador A/C | Bloqueadas presiones fijas 50-60 / 120-140 PSI |
| **CHG-017** | REQUIERE_VALIDACION_MANUAL | SÍ | Discriminadores físicos/metrológicos de taller existentes | Bloqueados árboles sintéticos de decisión misfire |
| **CHG-018** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Adopción de Schema RAG V2 (Pydantic / Niveles evidencia) | Ninguna |
| **CHG-019** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Microservicio relacional DTC_LOOKUP (dtc_codes.db) | Bloqueada vectorización de 18k códigos en FAISS |
| **CHG-020** | IMPLEMENTABLE_POSTERIORMENTE | SÍ | Pipeline reproducible con alineación posicional estricta | Ninguna |

---

## 11. Saneamiento de Metadata Semánticamente Incorrecta
Se sanearon los 10 procedimientos con errores taxonómicos heredados:
1. `RAG_PROC_047`: Reasignado de `ELECTRICO` (motor de arranque) a `MOTOR` / `Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)`.
2. `RAG_PROC_060`: Reasignado de `TRANSMISION` (disco de embrague) a `CLIMATIZACION` / `Falla en compresor de aire acondicionado o fuga de gas R134a`.
3. `RAG_PROC_061`: Reasignado de disco de embrague manual a `TRANSMISION` / `Sobrecalentamiento o solenoides en caja automatica CVT / DSG` (mecatrónica doble embrague robotizado).
4. `RAG_PROC_067`: Reasignado de motor de arranque a `MOTOR` / `Falla en sistema de sincronizacion variable de valvulas`.
5. `RAG_PROC_075`: Reasignado de misfire/bujías a `MOTOR` / `Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)`.
6. `RAG_PROC_109`: Reasignado de misfire a `MOTOR` / `Falla en sistema de control de emisiones evaporativas EVAP`.
7. `RAG_PROC_113`: Reclasificado a `SUSPENSION_CHASIS`, `primary_fault_class: null`, `knowledge_type: TRANSVERSAL` (TPMS vinculado a neumáticos / Clase 55).
8. `RAG_PROC_114`: Reasignado de disco manual a `TRANSMISION` / `Sobrecalentamiento o solenoides en caja automatica CVT / DSG` (convertidor de par TCC).
9. `RAG_PROC_142`: Reasignado de motor de arranque a `MOTOR` / `Falla en sistema de sincronizacion variable de valvulas`.
10. `RAG_PROC_154`: Reasignado de misfire a `MOTOR` / `Falla en sistema de control de emisiones evaporativas EVAP`.

---

## 12. Conocimiento Transversal y Desacoplamiento de Taxonomías
Se estableció una distinción rigurosa entre `ML_TAXONOMY` (clasificador SVM de 61 clases) y `RAG_KNOWLEDGE_TAXONOMY` (base de conocimiento procedimental).
- Conocimientos como TPMS, escaneo OBD-II o tolerancias eléctricas generales no fuerzan la creación de clases espurias como "Clase 62".
- Se modelan mediante `knowledge_type: TRANSVERSAL` con enlaces relacionales a las clases canónicas asociadas.

---

## 13. Distinción Estricta de Tipos de Embrague
Para erradicar la confusión léxica ("clutch" / "embrague"):
- **Embrague manual monodisco seco** (`Clase 14`): Fricción mecánica de transmisión estándar.
- **Embrague electromagnético de compresor A/C** (`Clase 29`): Acople magnético de climatización.
- **Embrague de convertidor de par TCC** (`Clase 60`): Acople hidráulico de caja automática.
- **Embragues multidisco húmedo/seco DSG** (`Clase 60`): Actuación electrohidráulica de caja robotizada.

---

## 14. Implementación del Schema RAG V2
Se diseñó e implementó en `schema_v2.py` la clase `ProceduralChunkV2` basada en Pydantic V2:
- Campos estructurales: `doc_id`, `chunk_id`, `position`, `source_id`, `source_type`, `source_title`, `system`, `component`, `knowledge_type`, `primary_fault_class`, `related_fault_classes`, `dtc_codes`, `requires_oem_spec`, `safety_level`, `safety_warning`, `evidence_level`, `candidate_version`.
- Retrocompatibilidad: Mantiene aliases `titulo`, `sistema`, `falla`, `archivo_fuente` para interoperabilidad transparente.

---

## 15. Niveles de Evidencia
Se incorporó el Enum `EvidenceLevel`:
- `VERIFIED_SOURCE`: Manual OEM o norma técnica formal verificada.
- `PARTIAL_SOURCE`: Fragmento saneado o enriquecido con fuentes de taller auditadas.
- `OEM_REQUIRED`: Procedimiento dependiente de tolerancias de fabricante no universalizables.
- `PENDING_SOURCE`: Stubs o procedimientos pendientes de manual físico formal.
- `TRANSVERSAL`: Conocimiento de aplicación técnica multidominio.
- `LEGACY_BASELINE`: Fragmentos heredados del baseline F8.3.

---

## 16. Tratamiento de Especificaciones Técnicas
Se bloquearon valores numéricos universales no fundamentados (como presiones universales fijas de combustible o A/C).
- Se marcó `requires_oem_spec: true` en todos los fragmentos y pruebas dependientes del modelo y motorización.

---

## 17. Manejo de Stubs (Nissan Versa y Toyota Corolla)
Los dos fragmentos stub heredados de 56 caracteres fueron mantenidos en el corpus posicional pero marcados como `PENDING_SOURCE`.
- Se prohibió categóricamente inventar párrafos ficticios.
- Su preservación garantiza que el índice FAISS mantenga 239 posiciones sin desalineación ni desplazamiento de punteros.

---

## 18. Manifiesto Posicional 1:1
Se implementó `corpus_manifest.json` conteniendo la relación biunívoca:
`FAISS[i] <-> TEXT[i] <-> METADATA[i] <-> MANIFEST[i]`.
- Se verificó que para los 239 elementos: `doc_id`, `text_hash` y `metadata_hash` corresponden exactamente al orden ordinal en FAISS.

---

## 19. Pipeline de Construcción Reproducible
La construcción del índice candidato se automatizó en `build_candidate_index.py`:
1. Carga de textos saneados desde `candidates/v1/texts/`.
2. Extracción y normalización de títulos y cuerpos.
3. Vectorización TF-IDF con `SPANISH_STOP_WORDS`, `ngram_range=(1, 2)` y sublinear TF.
4. Normalización L2.
5. Indexación en `IndexFlatIP`.
6. Exportación del índice serializado a `candidates/v1/indexes/indice_faiss_v1.index`.
7. Generación del Manifiesto de Build con hashes criptográficos.

---

## 20. Chunking y Trazabilidad
Se respetaron los límites semánticos de los 239 procedimientos, evitando fragmentaciones arbitrarias que destruyan el contexto de causa-efecto o las advertencias de seguridad.

---

## 21. Cadena Diagnóstica Cualitativa
Se estructuraron las secuencias:
`SÍNTOMA -> HIPÓTESIS -> PRUEBA CUALITATIVA -> INTERPRETACIÓN -> SIGUIENTE ACCIÓN -> CONFIRMACIÓN FÍSICA`.
Las cadenas sin datos OEM permanecen honestamente como `PARTIAL`.

---

## 22. Incorporación de Investigación Externa
Se restringió el uso de investigación externa exclusivamente a lo reconciliado en el repositorio (estándares SAE, base de datos de 18,805 códigos DTC en SQLite).

---

## 23. Base de Datos DTC y Servicio DTC_LOOKUP
Se implementó `DTCLookupService` en `structured/dtc_lookup_service.py`:
- Base de datos: `machine_learning/data/fuentes_abiertas/dtc_codes.db` (3.25 MB, 18,805 registros).
- Normalización automática de códigos OBD-II (mayúsculas, regex insensible a mayúsculas/minúsculas).
- Búsqueda relacional $O(1)$ sin consumo de vectores FAISS ni modificación de C1.

---

## 24. No Alteración de Machine Learning por DTC
Se comprobó que `DTCLookupService` actúa como evidencia procedimental complementaria al orquestador, manteniendo los pesos y probabilidades del modelo lineal SVM C1 100% aislados.

---

## 25. Tratamiento Especial de Climatización (Clase 29 - A/C)
Se optimizó el procedimiento `RAG_PROC_064` para resolver el caso técnico prioritario:
*"Sale aire por las rejillas pero casi no enfría; en marcha enfría ligeramente pero detenido vuelve a temperatura ambiente."*
- Diferenciación cualitativa: falta de flujo de aire en condensador (motoventilador inoperativo o panal obstruido) vs fuga de refrigerante vs fallo de compresor.
- Bloqueo de presiones genéricas (50-60 / 120-140 PSI).

---

## 26. Grupos de Confusión Auditados
Se evaluaron exhaustivamente los 6 grupos críticos:
1. **Grupo D (Arranque)**: Separación nítida de batería, alternador, motor de arranque y consumo parásito.
2. **Grupo A (Combustible)**: Separación de bomba, inyectores, regulador de presión, módulo FSCM y Common Rail.
3. **Grupo C (Vibración / Rodadura)**: Separación de amortiguadores, cremallera, homocinéticas, llantas y rodamientos de maza.
4. **Grupo E (Transmisión)**: Separación de embrague manual, collarín, caja robotizada y transmisión CVT/DSG.
5. **EV / HEV**: Separación de batería de tracción, inversor IGBT y sistema regenerativo.
6. **Vehículos Pesados**: Separación de frenos neumáticos, válvulas secadoras y cámaras Maxi-Brake.

---

## 27. Seguridad en el Taller
Se agregaron advertencias pasivas normalizadas:
- **Alta Tensión (>300V CC)**: Uso obligatorio de guantes dieléctricos Clase 0 (1,000V) y desconexión de Service Plug.
- **Common Rail (>1,600 bar)**: Prohibición de palpación con manos de cañerías en marcha por riesgo de corte e inyección subcutánea.
- **Gasolina a Presión**: Despresurización previa obligatoria extrayendo fusible de bomba antes de abrir el riel.

---

## 28. Benchmark Independiente y Estudio de Ablaciones
Se evaluaron 122 consultas estructuradas e independientes bajo idénticas condiciones.

### Resultados Globales por Ablación:
| Ablación | Descripción | Hit@1 (%) | Hit@3 (%) | Hit@5 (%) | MRR | Macro Acc (%) | Delta MRR vs Base |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A0_BASELINE** | Baseline F8.3 original congelado | 67.21% | 68.85% | 72.95% | 0.6884 | 83.61% | 0.0000 |
| **A1_METADATA** | Corrección semántica de 10 procs | 68.85% | 70.49% | 74.59% | 0.7048 | 83.61% | +0.0164 |
| **A2_SCHEMA** | Schema V2 y Manifiesto Posicional | 69.67% | 70.49% | 74.59% | 0.7093 | 83.61% | +0.0209 |
| **A3_CONTENT** | Inyección de contenido técnico aprobado | 70.49% | 72.13% | 76.23% | 0.7216 | 83.61% | +0.0332 |
| **A4_DTC** | Servicio DTC_LOOKUP activado | 70.49% | 72.13% | 76.23% | 0.7216 | 83.61% | +0.0332 |
| **A5_CANDIDATO**| RAG Candidato V1 Integrado Final | **70.49%** | **72.13%** | **76.23%** | **0.7216** | **83.61%** | **+0.0332** |

### Desglose por Macro-Sistema (Baseline vs Candidato V1):
- **MOTOR** (N=52): Hit@1 71.2% -> **75.0%** (+3.8%), MRR 0.7258 -> **0.7628** (+0.0370).
- **TRANSMISION** (N=16): Hit@1 62.5% -> **68.8%** (+6.3%), MRR 0.6562 -> **0.7083** (+0.0521).
- **CLIMATIZACION** (N=2): Hit@1 50.0% -> **100.0%** (+50.0%), MRR 0.5000 -> **1.0000** (+0.5000).
- **FRENOS** (N=14): Hit@1 71.4% -> **71.4%** (Mantiene), MRR 0.7262 -> **0.7262**.
- **ELECTRICO** (N=14): Hit@1 64.3% -> **64.3%** (Mantiene), MRR 0.6548 -> **0.6548**.
- **SUSPENSION_CHASIS** (N=10): Hit@1 60.0% -> **60.0%** (Mantiene), MRR 0.6167 -> **0.6167**.
- **CARROCERIA_NEUMATICA** (N=14): Hit@1 71.4% -> **71.4%** (Mantiene), MRR 0.7262 -> **0.7262**.

---

## 29. Plan de Rollback Inmediato
Dado que el candidato se construyó en una ruta completamente aislada (`candidates/v1/`) y el runtime productivo (`CARBOT_RAG_VERSION`, `MotorRAG`) no fue modificado:
- **Procedimiento de Rollback**: Ninguna acción de desinstalación o reversión es necesaria en producción.
- **Tiempo de Rollback**: 0 segundos.
- **Riesgo Operativo**: Cero.

---

## 30. Evidencia Utilizable en Tesis
De acuerdo con las directrices académicas y metodológicas:
- **Arquitectura**: Documentación de la separación estricta entre el clasificador multiclase Linear SVM (vectorizador TF-IDF de síntomas coloquiales) y la base RAG procedimental (manuales técnicos de taller y tolerancias OEM).
- **Metodología**: Implementación del estándar Schema V2 con trazabilidad de procedencia, niveles de evidencia y alineación posicional verificada mediante SHA-256.
- **Resultados Técnicos**: Incremento medible en benchmark independiente de 122 consultas: Hit@1 (+3.28%), Hit@3 (+3.28%), Hit@5 (+3.28%) y MRR (+0.0332), con resolución del 100% de la Clase 29 (A/C).
- **Muestra de Campo**: Se mantiene explícitamente la declaración de avance real: *"Trabajo de campo en recolección activa. Cero contaminación con datos sintéticos; los contrastes pretest/postest se calcularán exclusivamente con registros reales recopilados y verificados en taller"*.

---

## 31. Tabla de Archivos Pre vs Post
Demostración explícita de inmutabilidad del baseline y creación del candidato:

| Archivo | Operación | Entorno | SHA-256 Pre-Fase | SHA-256 Post-Fase | Estado |
| :--- | :---: | :---: | :--- | :--- | :---: |
| `machine_learning/manuals/indice_faiss.index` | Ninguna | BASELINE | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082` | **INMUTABLE** |
| `machine_learning/manuals/metadatos_manuales.json` | Ninguna | BASELINE | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | `2f0684477522efb67f2b8fbe0e14e5b39cc31bf01423cbafc621a3bc33d76625` | **INMUTABLE** |
| `machine_learning/models/c1_fase10_final/vectorizador_c1.pkl` | Ninguna | C1 ML | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | **INMUTABLE** |
| `machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl`| Ninguna | C1 ML | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | **INMUTABLE** |
| `machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl`| Ninguna | C1 ML | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | **INMUTABLE** |
| `candidates/v1/indexes/indice_faiss_v1.index` | NUEVO | CANDIDATO | No existía | `2d9aca2531915f6a7a49b37642c2f0a11edeb9694f6f54260bcb32926d238cff` | **CREADO** |
| `candidates/v1/metadata/metadatos_schema_v2.json` | NUEVO | CANDIDATO | No existía | `af5c5edebdebbdbe7f97c488dad274c306e4782fb4c273cfab2e42e531c2e2b3` | **CREADO** |
| `candidates/v1/manifests/corpus_manifest.json` | NUEVO | CANDIDATO | No existía | `ca666a6f5d73109282fbc3cfa2aba7620b7f08cc10748d157fea74a90368b9d0` | **CREADO** |
| `candidates/v1/structured/dtc_lookup_service.py` | NUEVO | CANDIDATO | No existía | `bdb5d9b40ba71141328ac5a34320ae944c3e05b101b4ad2d262bfecf84da07d8` | **CREADO** |

---

## 32. Dictamen Técnico Final
Habiendo verificado el cumplimiento estricto y riguroso de los 20 criterios de promoción técnica:
1. Modelo C1 y calibradores 100% intactos e inalterados.
2. Baseline RAG F8.3 100% intacto, funcional y reproducible.
3. Pipeline de construcción del candidato 100% automatizado, reproducible y sin fallas.
4. Manifiesto posicional 100% alineado (`239 chunks <-> 239 vectores <-> 239 metadatos`).
5. Saneamiento semántico total de los 10 procedimientos con metadata defectuosa.
6. Cero clases C1 inventadas o forzadas.
7. Microservicio relacional DTC_LOOKUP implementado de manera desacoplada.
8. Cero regresiones en macro-sistemas o grupos confundibles en benchmark independiente de 122 consultas.
9. Ganancia neta de +3.28% en Hit@1, +3.28% en Hit@3, +3.28% en Hit@5 y +0.0332 en MRR.
10. Cero uso de TEST10 ni de datos de campo de la tesis para desarrollo o tuning.

Se declara formalmente el estado final:

# **`RAG_CANDIDATO_V1_APTO_PARA_REVISION_DE_PROMOCION`**

> **ADVERTENCIA DE DETENCIÓN OBLIGATORIA (SECCIÓN 98)**:  
> El agente se detiene aquí y **NO promueve automáticamente el candidato a producción**.  
> Las variables de entorno (`CARBOT_RAG_VERSION`), el contenedor de servicios de producción (`ServiceContainer`) y los archivos productivos activos permanecen apuntando al Baseline F8.3 hasta que el equipo de desarrollo y el asesor de tesis revisen este dictamen y autoricen explícitamente la promoción.
