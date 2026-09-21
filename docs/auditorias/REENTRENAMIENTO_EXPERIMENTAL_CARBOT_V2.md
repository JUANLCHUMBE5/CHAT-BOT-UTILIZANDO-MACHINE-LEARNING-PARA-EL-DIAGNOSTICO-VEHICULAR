# Auditoría y Evaluación Experimental — CarBot ML + RAG V2

**Fecha:** 2026-09-19  
**Entorno:** Experimental Aislado (`machine_learning/experimentos/carbot_v2/`)  
**Versión de Referencia Productiva:** `CARBOT_PRECAMPO_FROZEN` (FASE 11.6.4 / 12.3)  
**Blindaje Criptográfico:** `ARTEFACTOS PRODUCCIÓN MODIFICADOS: 0`  

---

## Veredictos Finales y Dictamen de la Fase Experimental

- **Veredicto Machine Learning:** `SVM_V2_MEJORA_PARCIAL`  
- **Veredicto RAG / Base Documental:** `RAG_V2_EMPEORA`  
- **Recomendación Estratégica General:** `MANTENER_ACTUAL`  
- **Política de Despliegue:** **PROHIBICIÓN ESTRICTA DE DESPLIEGUE**. Ningún modelo ni índice experimental reemplazará los artefactos congelados de tesis.

---

## 1. Inventario y Auditoría de Fuentes Externas Analizadas

- **Total Registros Externos Auditados:** 75,843
- **Fuentes Incluidas:**
  - *Indecopi Perú:* 914 alertas oficiales de seguridad y llamados a revisión vehicular (2012–2026).
  - *NHTSA Recalls:* 35,000 campañas oficiales de llamados a revisión con componente y defecto tipificado.
  - *NHTSA Complaints:* 20,000 quejas de usuarios filtradas técnicamente (para lenguaje y vocabulario).
  - *Open Datasets Normalizados:* 19,929 registros (Zenodo 15626055, MechanicDB Public, OBDex, DTC Database, EngineFaultDB).

## 2. Clasificación Forense por Categoría de Uso

| Categoría de Uso | Cantidad de Registros | Porcentaje | Tratamiento y Destino |
|---|---|---|---|
| **`RAG_TECHNICAL`** | 49,749 | 65.6% | Indexación documental técnica (DTCs, manuales, boletines). |
| **`RAG_SYMPTOM_LANGUAGE`** | 20,000 | 26.4% | Quejas de consumidores NHTSA (`ground_truth=false`, no ML). |
| **`ML_REVIEW_REQUIRED`** | 3,344 | 4.4% | Casos ambiguos o con confianza 0.70-0.84 (bloqueados para training). |
| **`ML_HIGH_CONFIDENCE`** | 2,250 | 3.0% | Relación síntoma -> falla verificada (confianza >= 0.85). |
| **`TELEMETRY_ONLY`** | 500 | 0.7% | Series temporales de sensores sin narrativa clínica (no apto NLP). |
| **`EVALUATION_ONLY`** | 0 | 0.0% | Casos piloto reservados para evaluación histórica. |

## 3. Ensamblaje del Dataset C1-V2 Experimental y Capping Balanceado

- **Dataset Base C1 (Intocado):** 6,904 registros (distribución balanceada de 61 clases).
- **Candidatos ML High Confidence Totales:** 2,250 registros.
- **Criterio de Capping Anti-Dominancia (Regla 8):** Máximo 30 ejemplos nuevos por clase para impedir que fuentes externas distorsionen el prior bayesiano de la SVM.
- **Candidatos Externos Seleccionados e Incorporados:** 337 registros.
- **Dataset Final C1-V2 Experimental:** 7,241 registros.
- **Partición Anti-Leakage Agrupada:** Train = 6,090 (84.1%), Validation = 1,151 (15.9%). Agrupados por `id_grupo` / `source_record_id`.

## 4. Métricas Comparativas: SVM Actual vs SVM V2 Experimental

Evaluados sobre **exactamente el mismo banco ciego** `test10_fase10_blind_v1.csv` (n=366 casos, 61 clases, 6 casos/clase balanceado, 0% leakage):

| Métrica Global | SVM Actual (Fase 10) | SVM V2 Experimental | Delta Experimental | Interpretación |
|---|---|---|---|---|
| **Accuracy (Top-1)** | `0.8169` | `0.8142` | `-0.0027` | Ligera variación (-1 caso de 366). |
| **Macro Precision** | `0.8241` | `0.8315` | `+0.0074` | **+0.74% de mayor certidumbre** en hipótesis afirmativas. |
| **Macro Recall** | `0.8169` | `0.8142` | `-0.0027` | Cobertura global conservada. |
| **Macro F1-Score** | `0.8095` | `0.8107` | `+0.0012` | **Supera baseline (+0.12%)**. |
| **Weighted F1-Score** | `0.8095` | `0.8107` | `+0.0012` | **Supera baseline (+0.12%)**. |
| **Top-3 Accuracy** | `0.9317` | `0.9344` | `+0.0027` | **Supera baseline (+0.27%)** (diagnóstico diferencial ampliado). |
| **Latencia Inferencia** | `0.21 ms` | `0.21 ms` | `0.00 ms` | Inferencia ultrarrápida idéntica en microsegundos. |

## 5. Dinámica de Clases: Mejoras vs Retrocesos

- **Clases con Mejora Neta de F1:** 16
- **Clases con Retroceso de F1:** 16
- **Clases Estables:** 29

### Top Clases con Mejora Significativa en SVM V2

| Clase CarBot | F1 Baseline | F1 V2 | Delta F1 | Factor Causal |
|---|---|---|---|---|
| **Alternador defectuoso o placa de diodos quemada** | `0.727` | `0.923` | `+0.196` | Incorporación de fallas documentadas y procedimientos de taller reales. |
| **Amortiguadores reventados o bujes de suspension gastados** | `0.727` | `0.800` | `+0.073` | Incorporación de fallas documentadas y procedimientos de taller reales. |
| **Bateria descargada o bornes sulfatados** | `0.769` | `0.800` | `+0.031` | Incorporación de fallas documentadas y procedimientos de taller reales. |
| **Bomba de gasolina quemada o con baja presion** | `0.667` | `0.769` | `+0.103` | Incorporación de fallas documentadas y procedimientos de taller reales. |
| **Caliper de freno trabado o mordaza pegada (piston agarrotado)** | `0.833` | `0.909` | `+0.076` | Incorporación de fallas documentadas y procedimientos de taller reales. |
| **Consumo de aceite por desgaste de anillos o retenes** | `0.857` | `0.923` | `+0.066` | Incorporación de fallas documentadas y procedimientos de taller reales. |

### Top Clases con Retroceso en SVM V2

| Clase CarBot | F1 Baseline | F1 V2 | Delta F1 | Factor Causal |
|---|---|---|---|---|
| **Baja presion de aceite o bomba de aceite defectuosa** | `0.833` | `0.769` | `-0.064` | Interferencia de vocabulario administrativo de recalls externos. |
| **Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)** | `0.909` | `0.800` | `-0.109` | Interferencia de vocabulario administrativo de recalls externos. |
| **Cuerpo de aceleracion o valvula IAC sucia** | `0.727` | `0.667` | `-0.061` | Interferencia de vocabulario administrativo de recalls externos. |
| **Desgaste de pastillas y zapatas de freno** | `0.615` | `0.571` | `-0.044` | Interferencia de vocabulario administrativo de recalls externos. |
| **Discos de freno alabeados o desgastados** | `0.909` | `0.769` | `-0.140` | Interferencia de vocabulario administrativo de recalls externos. |

## 6. Experimento con Filtro y Reranking de Combustible (Gasolina / Diésel)

- **Principio Físico:** Exclusión de hipótesis termodinámicamente incompatibles (e.g. Diésel prediciendo bujías/bobinas/GDI; Gasolina prediciendo Common Rail/DPF).
- **Incompatibilidad sin Filtro:** `0.27%` de hipótesis contradictorias en Top-3.
- **Incompatibilidad con Filtro:** `0.00%` (0 anomalías físicas).
- **Efecto en Top-3 con Filtro Activo:** Incrementa a `0.9394` (93.94%) y Macro-F1 a `0.8137`.

## 7. Comparación del Motor RAG: Actual (Frozen) vs V2 (19,924 Chunks)

Evaluación cuantitativa sobre 18 tópicos técnicos vehiculares independientes (CKP, CMP, misfire, bobinas, discos freno, booster, alternador, MAF, MAP, EGR, DPF, Common Rail, turbo, intercooler, fugas admisión, fugas boost, sobrecalentamiento, bomba combustible):

| Métrica RAG | RAG Actual (Manuales OEM) | RAG V2 (Externos + Recalls) | Delta | Análisis Técnico |
|---|---|---|---|---|
| **Hit@1** | `0.8333` (83.3%) | `0.6667` (66.7%) | `-16.6%` | RAG Actual es superior en precisión inicial. |
| **Hit@3** | `0.9444` (94.4%) | `0.7778` (77.8%) | `-16.6%` | Manuales OEM contienen mayor especificidad de procedimiento. |
| **Hit@5** | `0.9444` (94.4%) | `0.7778` (77.8%) | `-16.6%` | RAG V2 sufre de dilución semántica por recalls masivos. |
| **MRR (Mean Reciprocal Rank)** | `0.8704` | `0.7130` | `-0.1574` | **RAG Actual supera contundentemente a RAG V2**. |

> **Hallazgo Metodológico Clave:** Incorporar masivamente recalls administrativos dentro del corpus FAISS degrada la precisión técnica de taller porque genera ruido textual que desplaza los manuales de servicio estructurados (OEM). Se ratifica la Regla Metodológica 6: *El corpus RAG debe reservarse exclusivamente para manuales técnicos de fabricantes*.

## 8. Estudio de Ablación 5-Way (Configuraciones A - E)

| Configuración | Top-1 | Top-3 | Macro-F1 | RAG MRR | Incomp. Comb. | Latencia Promedio |
|---|---|---|---|---|---|---|
| **A (SVM Actual + RAG Actual)** | `0.8169` | `0.9317` | `0.8095` | `0.8704` | `0.27%` | `12.71 ms` |
| **B (SVM V2 + RAG Actual)** | `0.8142` | `0.9344` | `0.8107` | `0.8704` | `0.27%` | `12.71 ms` |
| **C (SVM Actual + RAG V2)** | `0.8169` | `0.9317` | `0.8095` | `0.7130` | `0.27%` | `14.31 ms` |
| **D (SVM V2 + RAG V2)** | `0.8142` | `0.9344` | `0.8107` | `0.7130` | `0.27%` | `14.31 ms` |
| **E (SVM V2 + RAG V2 + Filtro Combustible)** | `0.8115` | `0.9394` | `0.8137` | `0.7130` | `0.00%` | `14.51 ms` |

## 9. Propuesta de Expansión Sintética Posterior (Sin Generación)

Conforme a la Sección 17, se identificaron 36 clases deficitarias en C1 que se beneficiarían de una futura fase de síntesis clínica controlada:

| Clase Deficitaria | Muestras Actuales | Faltante para Balance (n=120) | Recomendación Técnica |
|---|---|---|---|
| **Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)** | 66 | +54 | Generar 54 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)** | 68 | +52 | Generar 52 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)** | 69 | +51 | Generar 51 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)** | 70 | +50 | Generar 50 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI** | 72 | +48 | Generar 48 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)** | 74 | +46 | Generar 46 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)** | 74 | +46 | Generar 46 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla en sensor de velocidad de rueda ABS** | 75 | +45 | Generar 45 casos con variaciones dialectales peruanas y confirmacion física |
| **Falla en sistema de frenado regenerativo (EV / Hibridos)** | 77 | +43 | Generar 43 casos con variaciones dialectales peruanas y confirmacion física |
| **Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)** | 78 | +42 | Generar 42 casos con variaciones dialectales peruanas y confirmacion física |

## 10. Verificación Criptográfica Final de Blindaje de Producción

Recálculo directo SHA-256 de los 13 artefactos operacionales del manifiesto congelado:

| Componente | Ruta Relativa | Hash Pre / Esperado | Hash Post Calculado | Estado Blindaje |
|---|---|---|---|---|
| **`vectorizador_tfidf`** | `machine_learning/models/c1_fase10_final/vectorizador_c1.pkl` | `060d0728733499d2...` | `060d0728733499d2...` | ✅ INTACTO |
| **`modelo_svm_diagnostico`** | `machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl` | `24747fb7d3d46522...` | `24747fb7d3d46522...` | ✅ INTACTO |
| **`modelo_macro_sistema`** | `machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl` | `dec3ba707ff000b3...` | `dec3ba707ff000b3...` | ✅ INTACTO |
| **`metadata_modelo_c1`** | `machine_learning/models/c1_fase10_final/metadata_c1_macrofix.json` | `c1ac4a528ee75931...` | `c1ac4a528ee75931...` | ✅ INTACTO |
| **`indice_faiss_rag`** | `machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index` | `a2a081ffded23d4d...` | `a2a081ffded23d4d...` | ✅ INTACTO |
| **`metadatos_procedimientos_rag`** | `machine_learning/manuals/candidates/v1/metadata/metadatos_schema_v2.json` | `af5c5edebdebbdbe...` | `af5c5edebdebbdbe...` | ✅ INTACTO |
| **`corpus_manifest_rag`** | `machine_learning/manuals/candidates/v1/manifests/corpus_manifest.json` | `a0fce3dc39bb6344...` | `a0fce3dc39bb6344...` | ✅ INTACTO |
| **`politica_fusion`** | `backend/src/core/diagnostico/politica_fusion.py` | `219e730083c67398...` | `219e730083c67398...` | ✅ INTACTO |
| **`taxonomia_sistemas`** | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `72042cd6bf49855c...` | `72042cd6bf49855c...` | ✅ INTACTO |
| **`semantic_purifier`** | `backend/src/core/diagnostico/semantic_purifier.py` | `ffdf60e370f6f92e...` | `ffdf60e370f6f92e...` | ✅ INTACTO |
| **`text_processor`** | `backend/src/core/diagnostico/text_processor.py` | `66367147e1246525...` | `66367147e1246525...` | ✅ INTACTO |
| **`traductor_jerga`** | `backend/src/core/traductor_jerga.py` | `c582fec573d01424...` | `c582fec573d01424...` | ✅ INTACTO |
| **`motor_rag`** | `backend/src/infrastructure/motor_rag.py` | `47773d39c9944de0...` | `47773d39c9944de0...` | ✅ INTACTO |

**Resultado Final de Blindaje:** `ARTEFACTOS PRODUCCIÓN MODIFICADOS: 0`  
**Estado de Certificación:** **BLINDAJE OPERACIONAL 100% CUMPLIDO. INTEGRIDAD CRIPTOGRÁFICA PRESERVADA.**
