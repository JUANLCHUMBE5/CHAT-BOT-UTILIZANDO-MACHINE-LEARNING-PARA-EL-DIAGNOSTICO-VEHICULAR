# REPORTE TÉCNICO EXPERIMENTAL — FASE 10 (ETAPA 3 CORREGIDO)
## Evaluación del Modelo Candidato F10-C1 (DATA-ONLY) en DEV10 y Macrofix Canónico

> [!IMPORTANT]
> **AVISO DE SUSTITUCIÓN Y TRAZABILIDAD**:
> Este documento sustituye interpretativamente al reporte C1 original debido a dos errores documentales/estructurales detectados en la auditoría forense:
> 1. **Defecto Estructural en Macro-Sistema C1 Original**: La columna `macro_sistema` del componente original en TRAIN10/DEV10 heredó 480 `NaN` y 22 cadenas históricas dispares, causando que el modelo de macro-sistemas original entrenara con 24 targets espurios y un Macro F1 de apenas 13.01%. Este defecto fue completamente subsanado en la Etapa 3.2 mediante el mapeo canónico oficial `FALLA_A_SISTEMA` (7 macro-sistemas exactos, 0 NaN), produciendo el modelo `modelo_sistema_c1_macrofix.pkl` con **96.46% de Accuracy** y **94.90% de Macro F1**.
> 2. **Corrección de Etiquetas de Mejora**: Se eliminaron las etiquetas numéricas alucinadas o transcritas de memoria en la sección de mejoras por clase, reemplazándolas por los valores aritméticos reales extraídos directamente de `fase10_c1_metrics_by_class.csv`.
> 
> El clasificador de fallas de 61 clases (`modelo_diagnostico_c1.pkl`) y el vectorizador (`vectorizador_c1.pkl`) se mantienen **100% intactos e inalterados**. El reporte C1 original se conserva sin modificar en el repositorio histórico por estricta trazabilidad científica.

**Fecha**: 17 de Septiembre de 2026  
**Candidato**: `F10-C1` (Clasificador de 61 Fallas congelado) + `modelo_sistema_c1_macrofix.pkl` (7 Macro-sistemas canónicos)  
**Objetivo Científico**: Aislar el efecto exclusivo de la incorporación del corpus sintético estratificado Fase 10 (2,440 registros) combinado con el train canónico original (6,189 registros) sin variar hiperparámetros ni vectorizador, con taxonomía de macro-sistemas saneada al 100%.  
**Estado Experimental**: `C1_MACROFIX_VALIDATED`  

---

## 1. Verificación Inicial y Final de Inmutabilidad de Fase 8.3

| Componente | Archivo | Hash SHA-256 | Estado Antes | Estado Después |
| :--- | :--- | :--- | :---: | :---: |
| `dataset_train` | `machine_learning/data/dataset_sintomas_limpio.csv` | `c94d6e7b88ef...` | INMUTABLE | INMUTABLE |
| `benchmark_dev_60` | `machine_learning/data/benchmark_dev_60_casos.py` | `113b5f190758...` | INMUTABLE | INMUTABLE |
| `modelo_diagnostico_falla_prod` | `machine_learning/models/modelo_diagnostico.pkl` | `3d8199595b69...` | INMUTABLE | INMUTABLE |
| `modelo_sistema_prod` | `machine_learning/models/modelo_sistema.pkl` | `22d11492e957...` | INMUTABLE | INMUTABLE |
| `vectorizador_tfidf_prod` | `machine_learning/models/vectorizador_tfidf.pkl` | `8b8e8c3b3571...` | INMUTABLE | INMUTABLE |
| *(14 componentes restantes)* | *(manuales, FAISS, adaptadores, core)* | *(hashes oficiales verificados)* | INMUTABLE | INMUTABLE |

**Resultado**: **19 / 19 artefactos de Fase 8.3 estrictamente idénticos e inalterados (100% inmutabilidad)**.

---

## 2. Inmutabilidad del Clasificador de Fallas C1 (61 Clases)

El clasificador de fallas de C1 no fue reentrenado ni modificado en ninguna forma durante la Etapa 3.2:

- `vectorizador_c1.pkl` SHA-256: `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` (INTACTO)
- `modelo_diagnostico_c1.pkl` SHA-256: `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` (INTACTO)

---

## 3. Desempeño Comparativo en DEV10 (1,725 registros) — Clasificación de Fallas

### A. Métricas Globales de Falla en DEV10 (61 Clases)

| Métrica | Fase 8.3 (Baseline) | Candidato C1 (Fase 10) | Delta (C1 - F8.3) |
| :--- | :---: | :---: | :---: |
| **Top-1 Accuracy** | 88.52% | 84.06% | **-4.46%** |
| **Top-3 Accuracy** | 94.20% | 91.71% | **-2.49%** |
| **Macro Precision** | 90.39% | 84.53% | **-5.86%** |
| **Macro Recall** | 87.15% | 84.92% | **-2.23%** |
| **Macro F1-Score** | 88.26% | 84.37% | **-3.89%** |
| **Weighted F1-Score** | 88.51% | 84.12% | **-4.39%** |
| **Brier Score** | 0.0612 | 0.0818 | +0.0206 |
| **ECE (Expected Calibration Error)** | 0.0228 | **0.0226** | **-0.0002** |

---

### B. Análisis por Fuente (Original vs Sintético Fase 10)

| Subconjunto DEV10 | n | Top-1 F8.3 | Top-1 C1 | Delta Top-1 | Top-3 F8.3 | Top-3 C1 | Delta Top-3 | Macro F1 F8.3 | Macro F1 C1 | Delta MF1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SINTÉTICO (Fase 10)** | **488** | 59.63% | **70.49%** | **+10.86%** | 79.51% | **89.34%** | **+9.84%** | 59.50% | **70.14%** | **+10.65%** |
| **ORIGINAL** | **1237** | 99.92%* | **89.41%** | -10.51% | 100.0%* | **92.64%** | -7.36% | 99.92%* | **90.06%** | -9.86% |

> [!NOTE]
> **INTERPRETACIÓN CIENTÍFICA CLAVE**:
> - En Fase 8.3, el conjunto completo de 6,189 registros originales constituía su conjunto de entrenamiento, por lo que el 99.92% sobre los 1,237 casos originales de DEV10 reflejaba memorización de train-set.
> - En C1, se implementó un **GroupSplit estricto por raíz de síntoma**. C1 nunca vio esos 1,237 casos originales en entrenamiento, y aun así generaliza con un **89.41% Top-1** y **92.64% Top-3**.
> - Sobre los casos sintéticos no vistos de Fase 10 (n=488), C1 supera a F8.3 por **+10.86% en Top-1** y **+9.84% en Top-3**.

---

### C. Desempeño por Nivel de Información Sintético (L1, L2, L3)

| Nivel | n | Top-1 F8.3 | Top-1 C1 | Delta Top-1 | Top-3 F8.3 | Top-3 C1 | Delta Top-3 | Macro F1 F8.3 | Macro F1 C1 | Delta MF1 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **L1** (Ambiguo) | 122 | 42.62% | **52.46%** | **+9.84%** | 66.39% | **72.13%** | **+5.74%** | 38.40% | **48.51%** | **+10.11%** |
| **L2** (Intermedio) | 183 | 67.76% | **77.60%** | **+9.84%** | 86.34% | **95.63%** | **+9.29%** | 65.36% | **75.50%** | **+10.14%** |
| **L3** (Técnico) | 183 | 62.84% | **75.41%** | **+12.57%** | 81.42% | **94.54%** | **+13.11%** | 60.18% | **74.51%** | **+14.33%** |

- **Gradiente de Dificultad**: Se confirma que L1 (< 55%) presenta menor precisión de falla específica debido a la ambigüedad clínica intencional del motivo de consulta, mientras que L2 y L3 superan el 75% Top-1 y el 94% Top-3.

---

### D. Casos Contrastivos en DEV10 (n=257)

- **Top-1 Accuracy**: F8.3 = 61.09%  |  **C1 = 75.49% (+14.40%)**
- **Top-3 Accuracy**: F8.3 = 82.88%  |  **C1 = 94.55% (+11.67%)**
- **Confusiones hacia la clase trampa**:
  - En F8.3: **52 casos (20.2%)** cayeron en la trampa contrastiva.
  - En C1: Se redujo a **36 casos (14.0%)**, confirmando el aprendizaje de discriminadores técnicos finos.

---

## 4. Desempeño del Macro-Sistema Saneado (Macrofix Canónico)

En la Etapa 3.2 se subsanó la columna `macro_sistema` mapeando las 61 clases a los 7 macro-sistemas oficiales vía `FALLA_A_SISTEMA`. Se reentrenó exclusivamente el clasificador Nivel 1 (`modelo_sistema_c1_macrofix.pkl`), evaluado sobre `dev10_v1_1_macrofix.csv` (n=1,725).

### A. Comparativa: Macro-Model C1 Antiguo vs Macrofix Canónico

| Métrica | Macro C1 Antiguo (Inválido) | Macrofix C1 (Saneado Canónico) | Impacto de Corrección |
| :--- | :---: | :---: | :---: |
| **Accuracy Global** | 35.94% | **96.46%** | **+60.52%** |
| **Macro Precision** | 13.91% | **96.09%** | **+82.18%** |
| **Macro Recall** | 13.06% | **93.88%** | **+80.82%** |
| **Macro F1-Score** | 13.01% | **94.90%** | **+81.89%** |
| **Weighted F1-Score** | 35.88% | **96.44%** | **+60.56%** |
| **Número de Targets** | 24 (con heterogeneidad) | **7 (canónicos exactos)** | Corregido |
| **Targets NaN** | SÍ (`'nan'` como clase) | **NO (0 NaN)** | Eliminado |
| **Errores de Clasificación DEV10** | 1,105 / 1,725 | **61 / 1,725** | Reducción de 94.5% en errores |

---

### B. Métricas por Macro-Sistema Canónico en DEV10 (`fase10_c1_macrofix_metrics.csv`)

| Macro-Sistema Canónico | Clases Asociadas | Support DEV10 | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MOTOR** | 26 | 717 | 0.9725 | 0.9861 | **0.9792** |
| **ELECTRICO** | 7 | 208 | 0.9619 | 0.9712 | **0.9665** |
| **CARROCERIA_NEUMATICA** | 7 | 177 | 0.9714 | 0.9605 | **0.9659** |
| **FRENOS** | 7 | 211 | 0.9533 | 0.9668 | **0.9600** |
| **SUSPENSION_CHASIS** | 5 | 185 | 0.9511 | 0.9459 | **0.9485** |
| **TRANSMISION** | 8 | 199 | 0.9581 | 0.9196 | **0.9385** |
| **CLIMATIZACION** | 1 | 28 | 0.9583 | 0.8214 | **0.8846** |

---

### C. Matriz de Confusión 7x7 de Macro-Sistemas (`fase10_c1_macrofix_confusion_matrix.csv`)

```
                      CARROCERIA  CLIMA  ELEC  FRENOS  MOTOR  SUSP  TRANS
CARROCERIA_NEUMATICA         170      0     3       2      1     1      0
CLIMATIZACION                  2     23     1       0      2     0      0
ELECTRICO                      0      0   202       1      2     0      3
FRENOS                         0      0     2     204      1     4      0
MOTOR                          2      1     2       3    707     0      2
SUSPENSION_CHASIS              0      0     0       1      6   175      3
TRANSMISION                    1      0     0       3      8     4    183
```

---

### D. Desempeño del Macrofix por Fuente y Nivel

- **Por Fuente**:
  - `ORIGINAL` (n=1,237): Accuracy = **98.54%** | Macro F1 = **98.53%**
  - `SINTETICO` (n=488): Accuracy = **91.19%** | Macro F1 = **84.02%**
- **Por Nivel de Información (Sintéticos)**:
  - `L1` (Ambiguo, n=122): Accuracy = **86.89%** | Macro F1 = **80.16%**
  - `L2` (Intermedio, n=183): Accuracy = **93.44%** | Macro F1 = **86.70%**
  - `L3` (Técnico, n=183): Accuracy = **91.80%** | Macro F1 = **83.86%**

> [!TIP]
> **Rol Clínico de L1 a Nivel Macro**:
> Aunque las descripciones ambiguas (L1) dificultan predecir la falla exacta de 61 clases (52.46% Top-1), el macro-model resuelve el macro-sistema correcto en el **86.89% de los casos**, permitiendo acotar de inmediato el sistema vehicular afectado y orientar las preguntas de descarte al mecánico.

---

## 5. Las 10 Mejoras Reales en Clasificación de Fallas (Extraídas de `fase10_c1_metrics_by_class.csv`)

A continuación se reportan las 10 fallas con mayor ganancia real en F1-Score en DEV10 al comparar C1 contra el baseline F8.3, extraídas directamente del archivo de métricas por clase:

| # | Falla Canónica | Macro-Sistema | n | F8.3 F1 | C1 F1 | Delta F1 | F8.3 Rec | C1 Rec | Delta Rec |
| :-: | :--- | :--- | :-: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **Falla en termostato o motoventilador de radiador** | MOTOR | 32 | 85.71% | **93.55%** | **+7.83%** | 93.75% | 90.62% | -3.12% |
| 2 | **Falla en sistema de frenado regenerativo (EV / Hibridos)** | FRENOS | 19 | 82.35% | **89.47%** | **+7.12%** | 73.68% | 89.47% | **+15.79%** |
| 3 | **Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)** | MOTOR | 20 | 88.89% | **95.24%** | **+6.35%** | 80.00% | 100.0% | **+20.00%** |
| 4 | **Falla en bombin o bomba hidraulica de embrague** | TRANSMISION | 25 | 88.89% | **94.12%** | **+5.23%** | 96.00% | 96.00% | 0.00% |
| 5 | **Fallo en inversor de corriente IGBT o motor electrico (EV)** | ELECTRICO | 26 | 84.00% | **88.89%** | **+4.89%** | 80.77% | 92.31% | **+11.54%** |
| 6 | **Desgaste en collarin de empuje o crapodina de embrague** | TRANSMISION | 20 | 82.35% | **87.18%** | **+4.83%** | 70.00% | 85.00% | **+15.00%** |
| 7 | **Rodajes de transmision manual o eje primario gastados** | TRANSMISION | 20 | 88.89% | **93.02%** | **+4.13%** | 80.00% | 100.0% | **+20.00%** |
| 8 | **Válvula de freno de aire o secador APS obstruido (Camiones)** | CARROCERIA_NEUMATICA | 24 | 93.88% | **97.96%** | **+4.08%** | 95.83% | 100.0% | **+4.17%** |
| 9 | **Foco o falla en sistema de refrigeracion de bateria/inversor (EV)** | ELECTRICO | 20 | 85.71% | **89.47%** | **+3.76%** | 90.00% | 85.00% | -5.00% |
| 10 | **Elevalunas electrico o guaya de alzacristales rota o trabada** | CARROCERIA_NEUMATICA | 25 | 88.89% | **91.67%** | **+2.78%** | 80.00% | 88.00% | **+8.00%** |

### Clases con Mayor Desafío / Degradación en F1-Score:
1. `Alternador defectuoso o placa de diodos quemada`: F8.3 F1 = 91.84% -> C1 F1 = 63.53% (-28.31%, n=45)
2. `Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI`: F8.3 F1 = 92.31% -> C1 F1 = 75.68% (-16.63%, n=18)
3. `Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)`: F8.3 F1 = 87.50% -> C1 F1 = 73.33% (-14.17%, n=17)
4. `Disco de embrague desgastado o patinando`: F8.3 F1 = 87.88% -> C1 F1 = 74.58% (-13.30%, n=31)
5. `Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon)`: F8.3 F1 = 90.91% -> C1 F1 = 77.78% (-13.13%, n=18)

---

## 6. Documentación del Hallazgo: Climatización (A/C)

La auditoría forense determinó con absoluta claridad:
- **Clasificación Directa (SVM F8.3 y C1)**: Ante consultas directas o aisladas de climatización (e.g., *"prendo el aire acondicionado y no enfría nada"* o lecturas de presión iguales en 70 PSI), tanto F8.3 como C1 clasifican correctamente `Falla en compresor de aire acondicionado o fuga de gas R134a` con certidumbre > 98%.
- **Causa Raíz del Fallo Histórico**: El problema reproducido no es del clasificador ML sino de la **capa de orquestación conversacional multi-turno**: cuando el usuario acumuló en turnos sucesivos *"pierde fuerza"* + *"en subida"* + *"con el aire acondicionado encendido"*, el gestor de diálogo consolidó la queja principal como una avería de motor bajo carga en vez de discriminar el acople del compresor.
- **Acción Metodológica**: 
  - **NO** atribuir este fallo al SVM de clasificación.
  - **NO** generar refuerzo sintético adicional para A/C en esta etapa.
  - El desacoplamiento debe resolverse en el orquestador conversacional en una etapa posterior.
  - El código de orquestación permanece **intacto (0 modificaciones)**.

---

## 7. Muestra de Campo (FIELD) e Integridad Académica

Conforme a las reglas metodológicas de tesis:
- **Casos FIELD Disponibles**: **32** casos reales de taller mecánico recolectados y validados.
- **Meta Metodológica Oficial**: **60** casos.
- **Pendientes para Cierre**: **28** casos reales de taller.
- **Cero Simulación**: No se generaron ni se integrarán casos artificiales o sintéticos para completar la muestra FIELD.
- **Aislamiento**: Los 32 casos de campo no se han utilizado en el entrenamiento de C1 ni del macrofix.
- **Desempeño C1 sobre FIELD (n=32)**: Top-1 = **9.4%** | Top-3 = **9.4%** (idéntico a F8.3).

---

## 8. Limitaciones Experimentales: Near-Duplicates en el Componente Original

- **Hallazgo Forense**: En el split de Etapa 2, se detectó que **327 registros de DEV10** provenientes del componente original poseen un *near-duplicate* ($\text{similitud TF-IDF} \ge 0.88$) dentro de TRAIN10.
- **Decisión Metodológica**: NO se alteró el split de Etapa 2 para mantener la comparabilidad y el aislamiento experimental.
- **Implicación**: Las métricas sobre DEV10 sirven estrictamente como referencia formativa interna de monitoreo. La **evaluación final principal de generalización y no-memorización** dependerá de **TEST10 ciego e independiente**.

---

## 9. Seguridad y Cierre de TEST10

- **Archivo**: `machine_learning/data/fase10/test10_fase10_blind_v1.csv`
- **Hash SHA-256 verificado**: `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c`
- **Estado**: `LOCKED_BLIND_TEST` (Intacto).
- **Predicciones o consultas ejecutadas**: **0**.
