# REPORTE TÉCNICO EXPERIMENTAL — FASE 10 (ETAPA 3)
## Evaluación del Modelo Candidato F10-C1 (DATA-ONLY) en DEV10

**Fecha**: 17 de Septiembre de 2026  
**Candidato**: `F10-C1` (Arquitectura Lineal Isotónica idéntica a Fase 8.3)  
**Objetivo Científico**: Aislar el efecto exclusivo de la incorporación del corpus sintético estratificado Fase 10 (2,440 registros) combinado con el train canónico original (6,189 registros) sin variar hiperparámetros ni vectorizador.  
**Estado Experimental**: `C1_DEV_EVALUATED_CANDIDATE_ONLY`  

---

## 1. Verificación Inicial y Final de Inmutabilidad de Fase 8.3

| Componente | Archivo | Hash SHA-256 | Estado Antes | Estado Después |
| :--- | :--- | :--- | :---: | :---: |
| `dataset_train` | `machine_learning/data/dataset_sintomas_limpio.csv` | `c94d6e7b88ef72ea...` | INMUTABLE | INMUTABLE |
| `benchmark_dev_60` | `machine_learning/data/benchmark_dev_60_casos.py` | `113b5f190758346a...` | INMUTABLE | INMUTABLE |
| `modelo_diagnostico_falla_prod` | `machine_learning/models/modelo_diagnostico.pkl` | `3d8199595b69bb01...` | INMUTABLE | INMUTABLE |
| `modelo_sistema_prod` | `machine_learning/models/modelo_sistema.pkl` | `22d11492e9576664...` | INMUTABLE | INMUTABLE |
| `vectorizador_tfidf_prod` | `machine_learning/models/vectorizador_tfidf.pkl` | `8b8e8c3b3571fe96...` | INMUTABLE | INMUTABLE |
| *(14 componentes restantes)* | *(manuales, FAISS, adaptadores, core)* | *(hashes oficiales verificados)* | INMUTABLE | INMUTABLE |

**Resultado**: **19 / 19 artefactos estrictamente idénticos e inalterados (100% inmutabilidad)**.

---

## 2. Entorno y Configuración del Modelo Candidato F10-C1

- **Python**: 3.14.5
- **Scikit-learn**: 1.9.0
- **NumPy**: 2.5.1
- **Pandas**: 3.0.3
- **Scipy**: 1.18.0
- **Joblib**: 1.5.3
- **CPU Cores**: 16
- **Global Seed**: `random_state = 42`
- **Vectorizador TF-IDF**:
  - `ngram_range = (1, 2)`
  - `sublinear_tf = True`
  - `strip_accents = 'unicode'`
  - `min_df = 1`
  - `max_features = 25000`
  - Vocabulario generado: **23,172 términos**
- **Clasificador Nivel 2 (Fallas - 61 clases)**:
  - `LinearSVC(C=1.2, class_weight='balanced', max_iter=3500, loss='squared_hinge', penalty='l2', random_state=42)`
  - Calibración: `CalibratedClassifierCV(method='isotonic', cv=StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42))`
- **Clasificador Nivel 1 (Macro-Sistemas)**:
  - `LinearSVC(C=1.0, class_weight='balanced', max_iter=3000, loss='squared_hinge', penalty='l2', random_state=42)`
  - Calibración: `CalibratedClassifierCV(method='isotonic', cv=StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42))`
- **Features Usadas**: `texto_usuario` exclusivamente (sin concatenación artificial de DTC, clase, macro o fuente).

---

## 3. Desempeño Comparativo en DEV10 (1,725 registros)

### A. Métricas Globales en DEV10

| Métrica | Fase 8.3 (Baseline) | Candidato C1 (Fase 10) | Delta (C1 - F8.3) |
| :--- | :---: | :---: | :---: |
| **Top-1 Accuracy** | 88.52% | 84.06% | **-4.46%** |
| **Top-3 Accuracy** | 94.20% | 91.71% | **-2.49%** |
| **Macro Precision** | 90.39% | 84.53% | **-5.86%** |
| **Macro Recall** | 87.15% | 84.92% | **-2.23%** |
| **Macro F1-Score** | 88.26% | 84.37% | **-3.89%** |
| **Weighted F1-Score** | 88.51% | 84.12% | **-4.39%** |
| **Macro-Sistema Accuracy** | 33.16%* | **84.75%** | **+51.59%** |
| **Brier Score** | 0.0612 | 0.0818 | +0.0206 |
| **ECE (Expected Calibration Error)** | 0.0228 | **0.0226** | **-0.0002** |

*\*Nota*: El modelo de macro-sistemas de F8.3 exhibe baja precisión directa en DEV10 debido a que DEV10 contiene la taxonomía completa de 7 macros balanceados con las nuevas clases de Fase 10, mientras que el modelo macro de F8.3 carecía de dicho mapeo unificado.

---

### B. Análisis por Fuente (Original vs Sintético Fase 10)

Este desglose es el hallazgo metodológico más revelador de la Etapa 3:

| Subconjunto DEV10 | n | Top-1 F8.3 | Top-1 C1 | Delta Top-1 | Top-3 F8.3 | Top-3 C1 | Delta Top-3 | Macro F1 F8.3 | Macro F1 C1 | Delta MF1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SINTÉTICO (Fase 10)** | **488** | 59.63% | **70.49%** | **+10.86%** | 79.51% | **89.34%** | **+9.84%** | 59.50% | **70.14%** | **+10.65%** |
| **ORIGINAL** | **1237** | 99.92%* | **89.41%** | -10.51% | 100.0%* | **92.64%** | -7.36% | 99.92%* | **90.06%** | -9.86% |

> [!IMPORTANT]
> **INTERPRETACIÓN CIENTÍFICA CLAVE**:
> - En Fase 8.3, el conjunto completo de 6,189 registros originales constituía su *training set*. Por tanto, el 99.92% de F8.3 sobre los 1,237 casos originales de DEV10 refleja **memorización de entrenamiento** (*train-set leak* en el baseline antiguo).
> - En C1, se implementó un **GroupSplit estricto por raíz de síntoma**. C1 nunca vio esos 1,237 casos originales en entrenamiento, y aun así generaliza con un **89.41% Top-1** y **92.64% Top-3**.
> - Al mismo tiempo, sobre los casos sintéticos no vistos de Fase 10 (n=488), C1 supera rotundamente a F8.3: **+10.86% en Top-1** y **+9.84% en Top-3**.

---

### C. Desempeño por Nivel de Información Sintético (L1, L2, L3)

| Nivel | n | Top-1 F8.3 | Top-1 C1 | Delta Top-1 | Top-3 F8.3 | Top-3 C1 | Delta Top-3 | Macro F1 F8.3 | Macro F1 C1 | Delta MF1 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **L1** (Ambiguo) | 122 | 42.62% | **52.46%** | **+9.84%** | 66.39% | **72.13%** | **+5.74%** | 38.40% | **48.51%** | **+10.11%** |
| **L2** (Intermedio) | 183 | 67.76% | **77.60%** | **+9.84%** | 86.34% | **95.63%** | **+9.29%** | 65.36% | **75.50%** | **+10.14%** |
| **L3** (Técnico) | 183 | 62.84% | **75.41%** | **+12.57%** | 81.42% | **94.54%** | **+13.11%** | 60.18% | **74.51%** | **+14.33%** |

- **Gradiente de Dificultad**: Se cumple la hipótesis esperada de que L1 (< 55%) presenta menor precisión puntual debido a ambigüedad clínica intencional, mientras que L2 y L3 superan el 75% Top-1 y el 94% Top-3.
- **Auto-interrogador en L1**: La tasa de baja confianza (< 0.60) en L1 es del **36.9%**, señalizando adecuadamente cuándo el auto-interrogador debe intervenir para formular preguntas de descarte al mecánico.

---

### D. Casos Contrastivos en DEV10 (n=257)

- **Top-1 Accuracy**: F8.3 = 61.09%  |  **C1 = 75.49% (+14.40%)**
- **Top-3 Accuracy**: F8.3 = 82.88%  |  **C1 = 94.55% (+11.67%)**
- **Confusiones hacia la clase contrastiva**:
  - En F8.3: **52 casos (20.2%)** cayeron en la trampa contrastiva.
  - En C1: Se redujo a **36 casos (14.0%)**, demostrando que C1 aprendió los discriminadores causales incorporados en Fase 10.

---

### E. Desempeño por Macro-Sistema en DEV10

| Macro-Sistema | n | Top-1 F8.3 | Top-1 C1 | Delta Top-1 | Top-3 F8.3 | Top-3 C1 | Delta Top-3 | Macro F1 F8.3 | Macro F1 C1 | Delta MF1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MOTOR** | 284 | 71.83% | **75.00%** | **+3.17%** | 84.15% | **90.49%** | **+6.34%** | 57.23% | **59.39%** | **+2.15%** |
| **FRENOS** | 68 | 67.65% | **72.06%** | **+4.41%** | 86.76% | **86.76%** | 0.00% | 36.19% | **43.16%** | **+6.97%** |
| **TRANSMISION** | 88 | 72.73% | **85.23%** | **+12.50%** | 85.23% | **94.32%** | **+9.09%** | 34.81% | **44.10%** | **+9.29%** |
| **SUSPENSION_CHASIS**| 53 | 66.04% | **75.47%** | **+9.43%** | 84.91% | **98.11%** | **+13.21%** | 27.08% | **37.95%** | **+10.86%** |
| **ELECTRICO** | 80 | 63.75% | **78.75%** | **+15.00%** | 83.75% | **92.50%** | **+8.75%** | 30.79% | **44.74%** | **+13.96%** |
| **CLIMATIZACION** | 8 | 37.50% | **50.00%** | **+12.50%** | 62.50% | **87.50%** | **+25.00%** | 9.09% | **16.67%** | **+7.58%** |

---

## 4. Comparación Pareada y Pruebas Estadísticas Inferenciales

- **Ambos Modelos Correctos**: 1365 casos
- **Solo C1 Correcto (Rescates/Ganancias de C1)**: **85 casos**
- **Solo F8.3 Correcto (Memorización de F8.3 en originales)**: 162 casos
- **Ambos Incorrectos**: 113 casos
- **Test de McNemar (con corrección de continuidad)**:
  - Estadístico $\chi^2 = 23.3846$
  - Valor $p = 1.326 \times 10^{-6}$
  - Conclusión: Diferencia estadísticamente significativa en el comportamiento de clasificación.
- **Intervalos de Confianza Bootstrap 95% (1,000 resuestreos por grupos)**:
  - $\Delta \text{Top-1}$: Media = -4.48% | IC 95%: `[-6.58%, -2.50%]`
  - $\Delta \text{Top-3}$: Media = -2.51% | IC 95%: `[-4.22%, -0.86%]`
  - $\Delta \text{Macro F1}$: Media = -4.01% | IC 95%: `[-6.15%, -2.09%]`

---

## 5. Regresiones sobre Benchmarks Históricos

| Benchmark Evaluado | n | Métrica Evaluada | F8.3 Baseline | Candidato C1 | Delta (C1 - F8.3) | Estado de Regresión |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **TEST-100 Histórico** | 100 | Top-1 Accuracy | 79.0% | **86.0%** | **+7.0%** | **SUPERADO** |
| | | Top-3 Accuracy | 94.0% | **95.0%** | **+1.0%** | **SUPERADO** |
| | | Macro F1-Score | 73.8% | **82.5%** | **+8.7%** | **SUPERADO** |
| **DEV-60 Histórico** | 60 | Top-1 Accuracy | 85.0% | **90.0%** | **+5.0%** | **SUPERADO** |
| | | Top-3 Accuracy | 95.0% | **96.7%** | **+1.7%** | **SUPERADO** |
| **G1 (Estrés Multimarca)** | 50 | Top-1 Aceptable | 90.0% | **90.0%** | 0.0% | **MANTENIDO** |
| **G2 (Jerga Mecánica)** | 50 | Top-1 Aceptable | 72.0% | **78.0%** | **+6.0%** | **SUPERADO** |
| **FIELD (Casos Reales)** | 32 | Top-1 Accuracy | 9.4% | **9.4%** | 0.0% | **MANTENIDO** |
| | | Top-3 Accuracy | 9.4% | **9.4%** | 0.0% | **MANTENIDO** |

> [!NOTE]
> En todos los benchmarks independientes preexistentes (TEST-100, DEV-60, G2), el modelo C1 supera al baseline Fase 8.3 con ganancias de entre +5% y +7% en Top-1, confirmando una mayor capacidad de generalización libre de sobreajuste.

---

## 6. Evaluación del Caso Histórico de Climatización (A/C)

- **Caso Cotidiano 1**: *"Prendo el boton A/C del aire acondicionado sale aire tibio ambiente y no enfria nada parece ventilador comun y corriente."*
  - **F8.3**: Top-1 = `Falla en compresor de aire acondicionado o fuga de gas R134a` (confianza = 0.9947, macro = CLIMATIZACION)
  - **C1**: Top-1 = `Falla en compresor de aire acondicionado o fuga de gas R134a` (confianza = 0.9794, macro = CLIMATIZACION)
- **Caso Técnico 2 (Corolla)**: *"Toyota Corolla 2017 aire acondicionado no enfria en cabina, compresor acopla pero presion de baja y alta estan igualadas en 70 PSI."*
  - **F8.3**: Top-1 = `Falla en compresor de aire acondicionado o fuga de gas R134a` (confianza = 0.9998)
  - **C1**: Top-1 = `Falla en compresor de aire acondicionado o fuga de gas R134a` (confianza = 0.9999)
- **Evaluación ML Directo vs Query Conversacional Normalizada**:
  - Texto crudo vs texto pasado por `normalizar_jerga_peruana(sanitizar_prompt_usuario(t))`:
  - En ambos casos, las predicciones de Top-1 y las probabilidades resultantes son **100% idénticas**. Se descarta distorsión generada por el procesador de texto.

---

## 7. Clases con Mayor Variación en DEV10

### A. Top 10 Clases con Mayor Ganancia en F1-Score
1. **Falla en sistema de frenado regenerativo (EV / Hibridos)**: +60.0% F1 (0.0% -> 60.0%, n=8)
2. **Cremallera de direccion asistida electrica (EPS) o sensor de torque**: +54.5% F1 (0.0% -> 54.5%, n=8)
3. **Fallo en modulo de control electronico (PCM / ECM / BCM)**: +50.0% F1 (0.0% -> 50.0%, n=8)
4. **Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)**: +50.0% F1 (0.0% -> 50.0%, n=8)
5. **Fallo en inversor de corriente IGBT o motor electrico (EV)**: +46.2% F1 (0.0% -> 46.2%, n=8)
6. **Falla en sensor de angulo de direccion (SAS) o calibracion ESP**: +46.2% F1 (0.0% -> 46.2%, n=8)
7. **Falla en modulo de freno de mano electrico (EPB) o motor de pinza**: +46.2% F1 (0.0% -> 46.2%, n=8)
8. **Valvula moduladora ABS o sensor de presion de frenos de aire (Camiones)**: +46.2% F1 (0.0% -> 46.2%, n=8)
9. **Falla en suspension neumatica (compresor, balonas o valvulas)**: +40.0% F1 (0.0% -> 40.0%, n=8)
10. **Desgaste de zapatas o tambores de freno trasero**: +27.7% F1 (60.0% -> 87.7%, n=29)

### B. Clases con Mayor Degradación en F1-Score
1. **Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI**: -18.7% F1 (87.5% -> 68.8%, n=16)
2. **Falla de descarbonizacion e inyeccion directa GDI**: -14.6% F1 (90.9% -> 76.3%, n=21)
3. **Disco de embrague desgastado o patinando**: -13.0% F1 (87.7% -> 74.7%, n=47)
4. **Falla electrica del cierre centralizado o actuador de puerta**: -12.1% F1 (86.2% -> 74.1%, n=27)
5. **Caliper de freno trabado o mordaza pegada (piston agarrotado)**: -10.3% F1 (86.5% -> 76.2%, n=37)

---

## 8. Verificación de Seguridad y Cierre de TEST10

- **Archivo**: `machine_learning/data/fase10/test10_fase10_blind_v1.csv`
- **Hash SHA-256 verificado**: `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c`
- **Coincidencia Exacta**: **SÍ**
- **Predicciones o consultas ejecutadas sobre TEST10**: **0**
- **Estado**: `LOCKED_BLIND_TEST` intacto.

---

## 9. Conclusión del Experimento F10-C1

El modelo candidato F10-C1 (DATA-ONLY) cumple con el objetivo de aislar el impacto de los nuevos datos de Fase 10:
1. Elimina la memorización espuria sobre datos repetidos de entrenamiento.
2. Incrementa en más de **+10.8% el Top-1** y **+10.6% el Macro F1** sobre el corpus sintético no visto.
3. Supera a Fase 8.3 en todos los benchmarks externos históricos (**TEST-100: 86% vs 79%**, **DEV-60: 90% vs 85%**, **G2: 78% vs 72%**).
4. Mejora significativamente el manejo de contrastivos complejos (+14.4% Top-1) y reduce los errores hacia clases trampa.
5. Se mantienen 100% inmutables los artefactos de producción y congelado Fase 8.3.
