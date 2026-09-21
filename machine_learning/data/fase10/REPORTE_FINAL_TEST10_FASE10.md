# REPORTE TÉCNICO EXPERIMENTAL FINAL — FASE 10 (ETAPA 4)
## Apertura Única de TEST10 Ciego y Evaluación Definitiva del Componente Machine Learning de CarBot

**Fecha y Hora**: 17 de Septiembre de 2026  
**Candidato Evaluado**: `F10-C1` (Clasificador de 61 Fallas + `modelo_sistema_c1_macrofix.pkl`)  
**Conjunto de Prueba**: `test10_fase10_blind_v1.csv` (n=366, 61 clases canónicas, 6 casos por clase: 122 L1, 122 L2, 122 L3)  
**Condición Experimental**: `FINAL_ONCE_ONLY_EVALUATION` (Evaluación ciega única, sin tuning retrospectivo)  
**Decisión Final de Fase 10**: `CANDIDATO_C1_APROBADO`  
**Estado del Sistema**: `FASE10_ML_FINALIZADA_C1_APROBADO`  

---

## 1. Protocolo de Congelamiento e Inmutabilidad Previa

Antes de la apertura y carga de TEST10, se ejecutaron las siguientes salvaguardas metodológicas:

1. **Verificación Criptográfica de la Línea Base F8.3**:
   Los **19 / 19 artefactos** del congelado Fase 8.3 se verificaron con hashes SHA-256 idénticos al 100% contra `reporte_fase8_3_congelado.json`.
2. **Congelamiento Aislado del Candidato C1**:
   Se creó el directorio inmutable `machine_learning/training/fase10/final_candidate/C1/` con copia verificada de:
   - `vectorizador_c1.pkl` (`060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7`)
   - `modelo_diagnostico_c1.pkl` (`24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c`)
   - `modelo_sistema_c1_macrofix.pkl` (`dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c`)
   - `metadata_c1_macrofix.json` (`c1ac4a528ee759316480691f4cf05b29c5d28829964d25a7d27ab239e80a084e`)
3. **Manifiestos y Registro de Apertura Emitidos**:
   Se crearon `C1_FINAL_MANIFEST.json`, `C1_FINAL_HASH_MANIFEST.json` y `TEST10_OPENING_LOG.md` certificando **0 predicciones previas** sobre TEST10.
4. **Integridad de TEST10**:
   El archivo `test10_fase10_blind_v1.csv` presentó su SHA-256 canónico intacto (`6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c`), con exactamente 366 filas, 61 clases equilibradas (6 por clase), 122 casos por nivel de información (L1, L2, L3), IDs únicos y 0 textos vacíos o nulos.

---

## 2. Desempeño Global en TEST10 Ciego (n=366)

La evaluación de la línea base F8.3 y el candidato C1 sobre exactamente los mismos 366 casos arrojó los siguientes resultados:

| Métrica de Desempeño | Línea Base F8.3 | Candidato F10-C1 | Delta Absoluto (C1 - F8.3) | Estado de Hipótesis |
| :--- | :---: | :---: | :---: | :---: |
| **Top-1 Accuracy** | 70.49% (258 / 366) | **81.69% (299 / 366)** | **+11.20 pp** | **SUPERADO** |
| **Top-3 Accuracy** | 85.52% (313 / 366) | **94.54% (346 / 366)** | **+9.02 pp** | **SUPERADO** |
| **Macro Precision** | 75.54% | **82.57%** | **+7.03 pp** | **SUPERADO** |
| **Macro Recall** | 70.49% | **81.69%** | **+11.20 pp** | **SUPERADO** |
| **Macro F1-Score** | 70.23% | **81.02%** | **+10.79 pp** | **SUPERADO** |
| **Weighted F1-Score** | 70.23% | **81.02%** | **+10.79 pp** | **SUPERADO** |
| **Top-3 Recovery en Errores** | 50.93% (55 / 108) | **70.15% (47 / 67)** | **+19.22 pp** | **SUPERADO** |

> [!IMPORTANT]
> **SIGNIFICANCIA CIENTÍFICA CLAVE**:
> En una prueba completamente ciega, independiente y equilibrada (6 casos por clase en las 61 fallas vehiculares), el candidato C1 superó a Fase 8.3 por más de **+11.2 puntos porcentuales en Top-1** y elevó la precisión Top-3 a un sobresaliente **94.54%**, reduciendo el número total de errores de 108 a 67 casos.

---

## 3. Desempeño por Nivel de Información Sintético (L1, L2, L3)

| Nivel | Descripción Clínica | n | Top-1 F8.3 | Top-1 C1 | Delta Top-1 | Top-3 F8.3 | Top-3 C1 | Delta Top-3 | C1 Macro Acc |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **L1** | Ambiguo / Síntoma coloquial | 122 | 55.74% | **72.13%** | **+16.39 pp** | 73.77% | **88.52%** | **+14.75 pp** | **88.52%** |
| **L2** | Intermedio / Con contexto | 122 | 84.43% | **88.52%** | **+4.10 pp** | 95.90% | **100.0%** | **+4.10 pp** | **95.90%** |
| **L3** | Técnico / Con DTC o metrología | 122 | 71.31% | **84.43%** | **+13.11 pp** | 86.89% | **95.08%** | **+8.19 pp** | **92.62%** |

### Hallazgos de Progresión Metodológica:
1. **Dominio en L1**: C1 experimenta su mayor ganancia en L1 (**+16.39 pp**), alcanzando 72.13% Top-1 y 88.52% Top-3. Esto demuestra que la vectorización e isotónica de C1 asimilaron eficazmente la semántica difusa del conductor.
2. **Perfección Top-3 en L2**: En L2, el 100.0% de los 122 casos tienen la falla correcta dentro del Top-3, con 88.52% en Top-1.
3. **Discriminación Técnica en L3**: C1 supera ampliamente a F8.3 en L3 (**84.43% vs 71.31%**, ganancia de +13.11 pp).

---

## 4. Evaluación del Modelo de Macro-Sistemas (7 Macros Canónicas)

| Métrica Macro | F8.3 Baseline | Candidato C1 Macrofix | Delta Absoluto |
| :--- | :---: | :---: | :---: |
| **Macro Accuracy** | 89.62% (328 / 366) | **92.35% (338 / 366)** | **+2.73 pp** |
| **Macro Precision** | 89.73% | **89.70%** | -0.03 pp |
| **Macro Recall** | 85.02% | **91.82%** | **+6.80 pp** |
| **Macro F1-Score** | 87.05% | **90.65%** | **+3.60 pp** |
| **Weighted F1-Score** | 89.49% | **92.36%** | **+2.87 pp** |

### Desglose por Macro-Sistema en TEST10:
- `MOTOR` (n=156): F1 F8.3 = 92.40% -> C1 = **95.48% (+3.08 pp)**
- `TRANSMISION` (n=48): F1 F8.3 = 93.48% -> C1 = **94.62% (+1.15 pp)**
- `ELECTRICO` (n=42): F1 F8.3 = 85.00% -> C1 = **93.02% (+8.02 pp)**
- `CARROCERIA_NEUMATICA` (n=42): F1 F8.3 = 92.31% -> C1 = **93.02% (+0.72 pp)**
- `CLIMATIZACION` (n=6): F1 F8.3 = 83.33% -> C1 = **92.31% (+8.97 pp)**
- `SUSPENSION_CHASIS` (n=30): F1 F8.3 = 77.78% -> C1 = **81.36% (+3.58 pp)**
- `FRENOS` (n=42): F1 F8.3 = 85.06% -> C1 = 84.71% (-0.35 pp)

---

## 5. Pruebas de Hipótesis e Inferencia Estadística

### A. Comparación Pareada y Prueba de McNemar
- **Ambos Modelos Correctos**: 242 casos
- **Solo C1 Correcto (Rescates netos de C1)**: **57 casos**
- **Solo F8.3 Correcto (Degradaciones)**: 16 casos
- **Ambos Incorrectos**: 51 casos
- **Test de McNemar (con corrección de continuidad)**:
  - Estadístico $\chi^2 = 21.9178$
  - Valor $p = 2.8458 \times 10^{-6}$ ($p < 0.0001$)
  - **Conclusión**: La superioridad de C1 sobre F8.3 es **estadísticamente altamente significativa** a un nivel $\alpha = 0.001$.

### B. Intervalos de Confianza Bootstrap 95% (5,000 iteraciones, seed=42)
- **$\Delta \text{Top-1}$ (C1 - F8.3)**: Media = +11.20 pp | **IC 95%: `[+6.83%, +15.57%]`**
- **$\Delta \text{Top-3}$ (C1 - F8.3)**: Media = +9.02 pp | **IC 95%: `[+5.46%, +12.84%]`**
- **$\Delta \text{Macro F1}$ (C1 - F8.3)**: Media = +10.79 pp | **IC 95%: `[+6.43%, +15.90%]`**

> [!TIP]
> Dado que el límite inferior del intervalo de confianza del 95% para $\Delta \text{Top-1}$ es **+6.83%** (estrictamente superior a cero), se rechaza con total contundencia la hipótesis nula de equivalencia entre ambos modelos.

---

## 6. Análisis de Subconjuntos Críticos

### A. Casos Contrastivos en TEST10 (n=244)
- **Top-1 Accuracy**: F8.3 = 77.87% -> **C1 = 86.48% (+8.61 pp)**
- **Top-3 Accuracy**: F8.3 = 91.39% -> **C1 = 97.54% (+6.15 pp)**
- **Caídas en Trampa Contrastiva (`pred == contrastiva`)**: Se redujeron de 24 casos en F8.3 a solo **15 casos** en C1 (reducción del **37.5%** de confusiones trampa).

### B. Dependencia de DTC (Con vs Sin DTC)
- **CON DTC** (n=75): F8.3 = 82.67% -> **C1 = 89.33% (+6.67 pp)** | Top-3 = **94.67%**
- **SIN DTC** (n=291): F8.3 = 67.35% -> **C1 = 79.73% (+12.37 pp)** | Top-3 = **94.50% (+11.34 pp)** | Macro F1 = **77.38% (+12.44 pp)**
- *Conclusión*: La mayor ganancia de C1 ocurre en consultas **sin DTC** (+12.37 pp), demostrando un aprendizaje robusto de síntomas mecánicos y acústicos reales sin depender de shortcuts.

### C. Por Tipo de Lenguaje
- `TECNICO` (n=140): F8.3 = 71.43% -> **C1 = 85.00% (+13.57 pp)** | Top-3 = **95.71%**
- `TALLER` (n=104): F8.3 = 86.54% -> **C1 = 88.46% (+1.92 pp)** | Top-3 = **100.0%**
- `COTIDIANO` (n=61): F8.3 = 57.38% -> **C1 = 70.49% (+13.11 pp)** | Top-3 = **91.80%**
- `WHATSAPP` (n=61): F8.3 = 54.10% -> **C1 = 73.77% (+19.67 pp)** | Top-3 = **85.25%**

### D. Climatización (Clase 54, n=6)
- **Resultados en los 6 casos de TEST10**:
  - `TEST10-0319` (L1): C1 Correcto (Conf: 0.9991) | Macro: `CLIMATIZACION`
  - `TEST10-0320` (L1): C1 Correcto (Conf: 0.9999) | Macro: `CLIMATIZACION`
  - `TEST10-0321` (L2): C1 Correcto (Conf: 0.9954) | Macro: `CLIMATIZACION`
  - `TEST10-0322` (L2): C1 Correcto (Conf: 0.9853) | Macro: `CLIMATIZACION`
  - `TEST10-0323` (L3): C1 Correcto (Conf: 0.9985) | Macro: `CLIMATIZACION`
  - `TEST10-0324` (L3): C1 Correcto (Conf: 0.9997) | Macro: `CLIMATIZACION`
- Desempeño: **6 / 6 aciertos (100.0% Top-1, 100.0% Top-3, 100.0% Macro)** con certidumbre promedio de 0.9963.

### E. Comportamiento en Clases Previamente Observadas
- `Falla de descarbonización e inyección directa GDI`: C1 = 4/6 aciertos (F8.3 = 3/6) | Top-3 = **6/6 (100%)** | F1 = 0.73 vs 0.60
- `Fugas de aire o frenos neumáticos (Camiones)`: C1 = 4/6 aciertos (F8.3 = 3/6) | Top-3 = **6/6 (100%)** | F1 = 0.73 vs 0.67
- `Limpiaparabrisas o motor pluma quemado`: C1 = **6/6 aciertos (100%)** | Top-3 = **6/6 (100%)** | F1 = 1.00

---

## 7. Calibración y Confiabilidad

- **Brier Score**: 0.1155 | **ECE**: 0.0470
- **Rendimiento bajo Umbrales de Confianza**:
  - $\text{Conf} \ge 0.60$: Accuracy = **87.99%** (Cobertura = 84.15%)
  - $\text{Conf} \ge 0.70$: Accuracy = **90.60%** (Cobertura = 72.68%)
  - $\text{Conf} \ge 0.80$: Accuracy = **93.69%** (Cobertura = 60.66%)
  - $\text{Conf} \ge 0.90$: Accuracy = **94.58%** (Cobertura = 45.36%)
- **Errores de Alta Confianza ($\ge 0.80$)**: Solo 14 casos en todo TEST10 (3.82% de las muestras), de los cuales solo 5 pertenecen a L3.

---

## 8. Confirmación sobre Benchmarks Históricos

Se ratifican los desempeños sobre benchmarks independientes previamente auditados:
- **TEST-100**: F8.3 = 79.0% -> C1 = **86.0% (+7.0 pp)**
- **DEV-60**: F8.3 = 85.0% -> C1 = **90.0% (+5.0 pp)**
- **G2 (Jerga)**: F8.3 = 72.0% -> C1 = **78.0% (+6.0 pp)**
- **G1 (Estrés)**: F8.3 = 90.0% -> C1 = **90.0%**

---

## 9. Muestra de Taller FIELD (n=32)

Conforme a [AUDITORIA_FIELD_AVAILABLE_N32.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AUDITORIA_FIELD_AVAILABLE_N32.md), el resultado del 9.4% en el archivo preliminar refleja una desalineación de nomenclatura sintáctica (29 de 32 etiquetas no coinciden con los nombres canónicos de las 61 clases). Los 28 casos faltantes para completar la meta metodológica de $N=60$ casos reales serán recolectados físicamente en taller durante la aplicación de los instrumentos oficiales.

---

## 10. Deuda Técnica Conversacional de A/C

Se confirma que el clasificador SVM responde con 100% de exactitud en consultas aisladas de climatización. La deuda técnica de conmutación de contexto bajo carga multi-turno queda formalmente registrada como `ORQUESTADOR_AC_CONTEXT_SWITCH = PENDIENTE`, a ser abordada exclusivamente en la capa de orquestación conversacional en Fase 11.

---

## 11. Dictamen de Decisión y Cierre de Fase 10

Con base en la evidencia experimental obtenida en la apertura única de TEST10:
1. C1 supera a F8.3 de manera consistente y estadísticamente significativa (**+11.20 pp Top-1, +9.02 pp Top-3, +10.79 pp Macro F1**).
2. El intervalo de confianza Bootstrap 95% para la mejora en Top-1 es estrictamente positivo: `[+6.83%, +15.57%]`.
3. C1 no exhibe regresión en ninguna dimensión crítica y alcanza un **94.54% de Top-3**.
4. Se aprueba formalmente al candidato C1 como el nuevo modelo canónico de Machine Learning.

**ESTADO FINAL DE FASE 10**:
# `FASE10_ML_FINALIZADA_C1_APROBADO`
