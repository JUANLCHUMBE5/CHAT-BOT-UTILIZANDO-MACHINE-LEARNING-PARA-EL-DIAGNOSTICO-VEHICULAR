# REPORTE TÉCNICO EXPERIMENTAL — FASE 10 (ETAPA 3.2)
## Saneamiento del Macro-Sistema y Validación de Macrofix C1

**Fecha**: 17 de Septiembre de 2026  
**Módulo**: Machine Learning — Clasificador Nivel 1 (Macro-Sistemas Vehiculares)  
**Estado**: `C1_MACROFIX_VALIDATED`  

---

## 1. Resumen Ejecutivo y Diagnóstico Forense

En la auditoría forense (Etapa 3.1) se confirmó un único defecto estructural en los datasets experimentales de Fase 10: la columna `macro_sistema` del componente original de `train10_v1.csv` y `dev10_v1.csv` había heredado directamente los valores de la columna histórica `"sistema"`, generando:
- **480 registros con valor `NaN`**;
- **22 cadenas históricas heterogéneas** (e.g. `'Carrocería y Confort'`, `'Frenos Neumáticos'`, `'nan'`);
- **24 clases target en el modelo de macro-sistemas C1 original**, con una degradación artificial del modelo a 35.94% de accuracy y 13.01% de Macro F1 sobre la taxonomía canónica.

Simultáneamente, la auditoría confirmó que **el clasificador de fallas de 61 clases (`modelo_diagnostico_c1.pkl`) y el vectorizador (`vectorizador_c1.pkl`) eran 100% válidos**, habiendo sido entrenados sobre la columna canónica `clase_objetivo`.

En esta Etapa 3.2 se ejecutó el saneamiento integral y controlado:
1. Se mapearon las 61 clases de fallas a los **7 macro-sistemas canónicos** oficiales vía `FALLA_A_SISTEMA`.
2. Se generaron las réplicas derivadas `train10_v1_1_macrofix.csv` y `dev10_v1_1_macrofix.csv`, manteniendo intactas todas las demás columnas.
3. Se conservaron inalterados los modelos originales y se reentrenó **exclusivamente el clasificador de macro-sistemas**, versionado como `modelo_sistema_c1_macrofix.pkl`.
4. El nuevo modelo macrofix alcanzó en DEV10 un **96.46% de Accuracy** y **94.90% de Macro F1**, reduciendo los errores de 1,105 a solo 61 casos sobre 1,725 registros.

---

## 2. Inmutabilidad de Artefactos Críticos

| Componente | Archivo | SHA-256 Verificado | Estado |
| :--- | :--- | :--- | :---: |
| **Fase 8.3 (Línea Base)** | 19 artefactos en `machine_learning/` y `backend/` | Hashes de `reporte_fase8_3_congelado.json` | **19/19 INTACTOS** |
| **C1 Vectorizador** | `machine_learning/training/fase10/candidates/C1/vectorizador_c1.pkl` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | **INTACTO** |
| **C1 Clasificador Fallas** | `machine_learning/training/fase10/candidates/C1/modelo_diagnostico_c1.pkl` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | **INTACTO** |
| **C1 Macro Original** | `machine_learning/training/fase10/candidates/C1/modelo_sistema_c1.pkl` | `4b0ba7778b88d4c9657b54a01c34a2110c73e0404fa3a36db5fa9d1c9ef0d68f` | **PRESERVADO** |
| **TEST10 Ciego** | `machine_learning/data/fase10/test10_fase10_blind_v1.csv` | `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c` | **LOCKED (0 PREDS)** |
| **Archivos de Producción** | `backend/src/` y `frontend/src/` | No modificados | **0 MODIFICADOS** |

---

## 3. Auditoría de Taxonomía y Generación de Datasets Derivados

### A. Mapeo Canónico 61 a 7 (`MAPEO_CANONICO_61_A_7.csv`)

Se verificó exhaustivamente el diccionario canónico del proyecto `FALLA_A_SISTEMA`:
- Clases cubiertas: **61 / 61** (100%).
- Clases sin mapeo: **0**.
- Clases con mapeo ambiguo o múltiple: **0**.
- Macro-sistemas resultantes: **7 exactamente**.
- Distribución de clases por macro-sistema:
  - `MOTOR`: 26 clases
  - `TRANSMISION`: 8 clases
  - `FRENOS`: 7 clases
  - `ELECTRICO`: 7 clases
  - `CARROCERIA_NEUMATICA`: 7 clases
  - `SUSPENSION_CHASIS`: 5 clases
  - `CLIMATIZACION`: 1 clase

### B. Datasets Derivados Generados

Se crearon las versiones derivadas sin sobreescribir los archivos v1:

1. `train10_v1_1_macrofix.csv`:
   - Registros: 6,904
   - Clases de falla: 61
   - Macro-sistemas: 7 (0 NaN, 0 valores históricos)
   - SHA-256: `71d67e1109e9de0cafa86640d9fd04045b6809f912d342eb706f836d114c326c`
2. `dev10_v1_1_macrofix.csv`:
   - Registros: 1,725
   - Clases de falla: 61
   - Macro-sistemas: 7 (0 NaN, 0 valores históricos)
   - SHA-256: `2b5aba4f21bb32f848eca639ea933600f43502544a20acee84c54c638f85ee16`

**Verificación de Integridad de Columnas**:
Se compararon fila por fila todas las columnas excepto `macro_sistema` (`id`, `id_grupo`, `texto_usuario`, `clase_objetivo`, `source`, `nivel`, etc.): **coincidencia del 100%**. La única modificación fue la corrección de `macro_sistema`.

### C. Distribución de Registros en Datasets Saneados

| Macro-Sistema Canónico | N° Clases | Registros TRAIN10 Macrofix | % TRAIN10 | Registros DEV10 Macrofix | % DEV10 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MOTOR** | 26 | 2,868 | 41.54% | 717 | 41.57% |
| **FRENOS** | 7 | 844 | 12.22% | 211 | 12.23% |
| **ELECTRICO** | 7 | 832 | 12.05% | 208 | 12.06% |
| **TRANSMISION** | 8 | 796 | 11.53% | 199 | 11.54% |
| **SUSPENSION_CHASIS** | 5 | 740 | 10.72% | 185 | 10.72% |
| **CARROCERIA_NEUMATICA** | 7 | 712 | 10.31% | 177 | 10.26% |
| **CLIMATIZACION** | 1 | 112 | 1.62% | 28 | 1.62% |
| **TOTAL** | **61** | **6,904** | **100.0%** | **1,725** | **100.0%** |

---

## 4. Entrenamiento y Validación de `modelo_sistema_c1_macrofix.pkl`

- **Hiperparámetros**:
  - Algoritmo: `LinearSVC(C=1.0, class_weight='balanced', max_iter=3000, random_state=42)`
  - Calibración: `CalibratedClassifierCV(method='isotonic', cv=StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42))` sobre `id_grupo`
  - Entrada: TF-IDF de `vectorizador_c1.pkl` (25,000 max features) sobre `texto_usuario`
  - Target: `macro_sistema` (7 clases)
- **Validación de clases resultantes**:
  - `classes_`: `['CARROCERIA_NEUMATICA', 'CLIMATIZACION', 'ELECTRICO', 'FRENOS', 'MOTOR', 'SUSPENSION_CHASIS', 'TRANSMISION']`
  - Exactamente 7 valores. 0 valores espurios.
- **Artefactos Guardados**:
  - `modelo_sistema_c1_macrofix.pkl` (SHA-256: `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c`)
  - `metadata_c1_macrofix.json`

---

## 5. Resultados Comparativos y Desempeño en DEV10

### A. Diagnóstico Comparativo: Modelo Anterior vs Macrofix

| Indicador | Macro C1 Antiguo | Modelo Macrofix C1 | Diferencia |
| :--- | :---: | :---: | :---: |
| **Accuracy en DEV10** | 35.94% | **96.46%** | **+60.52%** |
| **Macro Precision** | 13.91% | **96.09%** | **+82.18%** |
| **Macro Recall** | 13.06% | **93.88%** | **+80.82%** |
| **Macro F1-Score** | 13.01% | **94.90%** | **+81.89%** |
| **Weighted F1-Score** | 35.88% | **96.44%** | **+60.56%** |
| **Targets del Modelo** | 24 clases (incluía NaN) | **7 clases canónicas** | Saneado |
| **Errores de Clasificación** | 1,105 / 1,725 | **61 / 1,725** | **-1,044 errores** |

### B. Desempeño por Macro-Sistema en DEV10 (`fase10_c1_macrofix_metrics.csv`)

| Macro-Sistema | Support | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| **MOTOR** | 717 | 0.9725 | 0.9861 | **0.9792** |
| **ELECTRICO** | 208 | 0.9619 | 0.9712 | **0.9665** |
| **CARROCERIA_NEUMATICA** | 177 | 0.9714 | 0.9605 | **0.9659** |
| **FRENOS** | 211 | 0.9533 | 0.9668 | **0.9600** |
| **SUSPENSION_CHASIS** | 185 | 0.9511 | 0.9459 | **0.9485** |
| **TRANSMISION** | 199 | 0.9581 | 0.9196 | **0.9385** |
| **CLIMATIZACION** | 28 | 0.9583 | 0.8214 | **0.8846** |

### C. Desempeño por Fuente (Original vs Sintético)

- **ORIGINAL** (n=1,237):
  - Accuracy = **98.54%**
  - Macro F1 = **98.53%**
- **SINTÉTICO** (n=488):
  - Accuracy = **91.19%**
  - Macro F1 = **84.02%**

### D. Desempeño por Nivel de Información Sintético (L1, L2, L3)

- **L1 (Ambiguo, n=122)**: Accuracy = **86.89%** | Macro F1 = **80.16%**
- **L2 (Intermedio, n=183)**: Accuracy = **93.44%** | Macro F1 = **86.70%**
- **L3 (Técnico, n=183)**: Accuracy = **91.80%** | Macro F1 = **83.86%**

> **Observación sobre L1**: En el clasificador de fallas detallado de 61 clases, L1 alcanza 52.46% de Top-1 debido a la ambigüedad deliberada del motivo de consulta del cliente. No obstante, el clasificador de Macro-Sistemas rescata el contexto con **86.89% de precisión**, garantizando que el sistema identifique correctamente el sistema vehicular general antes de disparar el auto-interrogador.

### E. Evaluación Específica de CLIMATIZACION (n=28)

- Total casos en DEV10: 28
- Aciertos: 23 (**82.14% de Accuracy**, Precision = 95.83%, F1 = 88.46%)
- Confusiones observadas (5 casos):
  - `CARROCERIA_NEUMATICA`: 2 casos
  - `MOTOR`: 2 casos
  - `ELECTRICO`: 1 caso

---

## 6. Manifest y Trazabilidad

Se generó `MACROFIX_MANIFEST.json` documentando los hashes criptográficos de origen y destino, asegurando la reproducibilidad total del experimento.
