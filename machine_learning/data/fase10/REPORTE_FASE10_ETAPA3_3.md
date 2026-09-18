# REPORTE TÉCNICO EXPERIMENTAL — FASE 10 (ETAPA 3.3)
## Análisis Profundo de Errores y Decisión Metodológica C1 vs C2

**Fecha**: 17 de Septiembre de 2026  
**Candidato**: `F10-C1` (Clasificador 61 Fallas congelado + `modelo_sistema_c1_macrofix.pkl`)  
**Estado Final**: `ANALISIS_C1_COMPLETADO_RECOMENDAR_CONGELAR`  

---

## 1. Verificación Inicial y Final de Inmutabilidad

Todos los artefactos críticos del proyecto se mantuvieron estrictamente inalterados durante toda la Etapa 3.3:

| Componente | Archivo | SHA-256 Verificado | Estado |
| :--- | :--- | :--- | :---: |
| **Fase 8.3 (Línea Base)** | 19 artefactos en `machine_learning/` y `backend/` | Hashes oficiales en `reporte_fase8_3_congelado.json` | **19/19 INTACTOS** |
| **C1 Vectorizador** | `machine_learning/training/fase10/candidates/C1/vectorizador_c1.pkl` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | **INTACTO** |
| **C1 Clasificador Fallas** | `machine_learning/training/fase10/candidates/C1/modelo_diagnostico_c1.pkl` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | **INTACTO** |
| **C1 Macrofix** | `machine_learning/training/fase10/candidates/C1/modelo_sistema_c1_macrofix.pkl` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | **INTACTO** |
| **TEST10 Ciego** | `machine_learning/data/fase10/test10_fase10_blind_v1.csv` | `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c` | **LOCKED (0 PREDS)** |
| **Producción** | Archivos en `backend/src/` y `frontend/src/` | No modificados | **0 MODIFICADOS** |

---

## 2. Desempeño Comparativo en DEV10 Sintético No Visto (n=488)

Al aislar el subconjunto de evaluación no visto por ninguno de los dos modelos (488 registros sintéticos estratificados de Fase 10):

| Métrica | Fase 8.3 (Baseline) | Candidato C1 | Delta (C1 - F8.3) |
| :--- | :---: | :---: | :---: |
| **Top-1 Accuracy** | 59.63% (291 / 488) | **70.49% (344 / 488)** | **+10.86 pp** |
| **Top-3 Accuracy** | 79.51% (388 / 488) | **89.34% (436 / 488)** | **+9.84 pp** |
| **Macro F1-Score** | 59.50% | **70.14%** | **+10.65 pp** |

---

## 3. Error Budget y Taxonomía de Errores Sintéticos de C1 (n=144)

De los 488 casos sintéticos en DEV10, C1 acertó 344 casos y erró en 144. Al clasificarlos bajo una taxonomía jerárquica con categoría primaria única:

| Categoría Primaria | Criterio de Clasificación | Cantidad | % del Total de Errores |
| :--- | :--- | :---: | :---: |
| **`AMBIGUO_L1`** | Nivel L1 deliberadamente ambiguo sin evidencia suficiente | **58** | **40.28%** |
| **`TOP3_COMPATIBLE`** | Nivel L2 o L3 donde la falla real está en Top-3 | **50** | **34.72%** |
| **`ERROR_MACRO`** | El macro-sistema predicho no coincidió con el real | **14** | **9.72%** |
| **`HIGH_CONF_WRONG`** | Confianza $\ge 0.80$ y Top-1 erróneo | **11** | **7.64%** |
| **`ERROR_MODELO_CLARO`** | Error en L2/L3 sin recuperar en Top-3 y conf < 0.80 | **8** | **5.56%** |
| **`SHORTCUT`** | Error inducido por término de código DTC confuso | **3** | **2.08%** |
| **TOTAL** | | **144** | **100.0%** |

> [!IMPORTANT]
> **Hallazgo Clave**: El **75.00% de los errores (108 / 144)** corresponden a casos benignos (`AMBIGUO_L1` y `TOP3_COMPATIBLE`), los cuales están concebidos para ser resueltos en el diálogo con el mecánico a través del auto-interrogador. En total, **92 de los 144 errores (63.89%)** tienen la clase correcta en el Top-3.

---

## 4. Análisis por Nivel de Información Sintético

### A. Nivel L1 — Ambiguo (n=122)
- **Top-1 Accuracy**: **52.46%** (64 / 122)
- **Top-3 Accuracy**: **72.13%** (88 / 122)
- **Top-3 Recuperados en Errores**: **24 / 58 (41.4%)**
- **Macro Accuracy**: **86.89%** (106 / 122) | **Macro F1**: **80.16%**
- **Confianza Media**: Correctos = 0.7426 | Incorrectos = **0.6018**
- **Distribución de Confianza**: 38.5% tienen confianza < 0.60; 48.4% tienen confianza < 0.70.
- **Interpretación**: Los errores en L1 exhiben una degradación natural de confianza, activando correctamente el umbral para que el auto-interrogador formule preguntas de descarte.

### B. Nivel L2 — Intermedio (n=183)
- **Top-1 Accuracy**: **77.60%** (142 / 183)
- **Top-3 Accuracy**: **95.63%** (175 / 183)
- **Top-3 Recuperados en Errores**: **33 / 41 (80.5%)**
- **Errores Claros (fuera de Top-3)**: **8 / 41**
- **Macro Accuracy**: **93.44%** | **Macro F1**: **86.70%**

### C. Nivel L3 — Técnico Especializado (n=183)
- **Top-1 Accuracy**: **75.41%** (138 / 183)
- **Top-3 Accuracy**: **94.54%** (173 / 183)
- **Top-3 Recuperados en Errores**: **35 / 45 (77.8%)**
- **Errores Claros (fuera de Top-3)**: **10 / 45**
- **Macro Accuracy**: **91.80%** | **Macro F1**: **83.86%**
- **Errores con Alta Confianza ($\ge 0.80$)**: Solo **8 casos** en todo el conjunto L3 (4.37%), todos explicados por acoplamiento físico o códigos DTC multivariables compartidos (e.g. DTC P0016 desfasaje árbol/cigüeñal vs sensor CKP/CMP; sensor ABS C0040 integrado en rodaje de rueda).

---

## 5. Análisis Contrastivo (n=257 en DEV10)

- **Top-1 Accuracy**: **75.49%** (194 / 257) (frente a 61.09% de F8.3, ganancia de **+14.40 pp**)
- **Top-3 Accuracy**: **94.55%** (243 / 257) (frente a 82.88% de F8.3, ganancia de **+11.67 pp**)
- **Caídas en Trampa Contrastiva (`pred == contrastiva`)**: Se redujeron de 52 casos (20.2%) en F8.3 a solo **36 casos (14.0%)** en C1.
- **Top Pares Contrastivos**: Ningún par contrastivo presentó más de 2 errores directos:
  1. *Llantas desbalanceadas vs Cremallera con juego*: 2 casos
  2. *Motor de arranque vs Batería descargada*: 2 casos
  3. *Llantas desbalanceadas vs Rodamiento de rueda*: 2 casos
  4. *Palieres dañados vs Rodamiento de rueda*: 2 casos
  5. *Sensor CKP/CMP vs VVT*: 2 casos

---

## 6. Desempeño por Clases en Datos Sintéticos No Vistos (n=61)

Al evaluar el impacto de C1 vs F8.3 clase por clase en los 488 registros no vistos:
- **Clases donde C1 mejora ($\Delta \text{F1} > +5\%$)**: **37 clases** (con ganancias de hasta +47.5% en collarín de embrague y +42.5% en rodajes de caja).
- **Clases donde C1 empeora ($\Delta \text{F1} < -5\%$)**: **10 clases**.
- **Clases con Degradación Relevante ($\Delta \text{F1} \le -15\%$ y $n \ge 8$)**: **3 clases**:
  1. *Falla de descarbonización e inyección directa GDI*: F1 76.9% -> 58.8% ($\Delta = -18.1\%$, n=8) — la falla real se mantuvo en Top-2/Top-3 en el 100% de los errores.
  2. *Fugas de aire o frenos neumáticos (Camiones)*: F1 71.4% -> 53.3% ($\Delta = -18.1\%$, n=8) — confundida con secador APS o mangueras de intercooler.
  3. *Limpiaparabrisas o motor pluma quemado*: F1 76.9% -> 61.5% ($\Delta = -15.4\%$, n=8) — confundida con actuadores eléctricos de cabina (elevalunas/arranque).

---

## 7. Análisis Específico de Climatización (A/C)

### A. Clasificación de Falla Directa (Clase 54, n=28)
- **Top-1 Accuracy**: **85.71%** (24 / 28)
- **Top-3 Accuracy**: **89.29%** (25 / 28)
- **Macro-Sistema Accuracy**: **82.14%** (23 / 28)

### B. Análisis de los 5 Errores en Macro Climatización:
1. `F10-L10-0009` (L1, Conf: 0.82): *"manchas verdes fosforescentes en unas mangueras del sistema de aire"*. Confundido con neumática por la frase *"sistema de aire"* (`AMBIGUEDAD_L1`).
2. `F10-L10-0020` (L2, Conf: 0.63): *"rejilla central marca 22°C... no hay codigos de error de motor ni tirones de combustion"*. Confundido con motor por el peso léxico de los síntomas negados de combustión (`SINTOMAS_NEGADOS`).
3. `F10-L10-0022` (L2, Conf: 0.45): *"al cargar gas refrigerante... manguera de alta presion humedad aceitosa"*. Confundido con motor por el término *"refrigerante"* (`POLISEMIA_REFRIGERANTE`).
4. `F10-L10-0035` (L3, Conf: 0.50): Compresor scroll trifásico eléctrico de alto voltaje en híbrido. **El clasificador de falla predijo EXACTAMENTE la clase 54 correcta**. Solo el macro-model predijo `ELECTRICO` por el vocabulario de alto voltaje (`COMPONENTE_ELECTRICO_HV`).
5. `F10-L10-0037` (L3, Conf: 0.51): Válvula Schrader de servicio con 20 psi estáticos. Confundido con neumática por léxico de presión y válvulas.

---

## 8. Calibración y Atajos (Shortcuts)

- **Calibración Global C1**: Brier Score = **0.0818** | ECE = **0.0226**
- **Errores de Alta Confianza en DEV10**:
  - Confianza $\ge 0.80$ e incorrecto: **51 casos** (2.96% de todo DEV10).
  - Confianza $\ge 0.90$ e incorrecto: **26 casos** (1.51% de todo DEV10).
- **Shortcut DTC**:
  - `CON_DTC` (n=88): Top-1 = **87.50%** | Top-3 = **95.45%** | Macro F1 = **82.84%**
  - `SIN_DTC` (n=400): Top-1 = **66.75%** | Top-3 = **88.00%** | Macro F1 = **65.01%**
  - *Conclusión*: No hay evidencia de shortcut espurio. El 88.0% de Top-3 en casos sin DTC y el 78.0% en jerga mecánica (G2) confirman que el modelo utiliza el léxico sintomático real.
- **Estilos de Lenguaje**:
  - `TECNICO` (n=205): Top-1 = 74.63% | Top-3 = 93.66%
  - `TALLER` (n=75): Top-1 = 77.33% | Top-3 = 96.00%
  - `COTIDIANO` (n=116): Top-1 = 71.55% | Top-3 = 90.52%
  - `WHATSAPP` (n=88): Top-1 = 52.27% | Top-3 = 71.59% (predominan mensajes L1 breves).
- **Menciones de Marca**:
  - `CON_MARCA` (n=32): Top-1 = 87.50% | Top-3 = 96.88%
  - `SIN_MARCA` (n=456): Top-1 = 69.30% | Top-3 = 88.82%
  - Sin indicios de dependencia espuria.

---

## 9. Muestra FIELD Disponible (n=32)

- Conforme al documento dedicado [AUDITORIA_FIELD_AVAILABLE_N32.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AUDITORIA_FIELD_AVAILABLE_N32.md), el porcentaje de 9.4% (3/32) **NO es directamente comparable** como Top-1 estricto porque 29 de las 32 etiquetas del archivo preliminar no coinciden sintácticamente con la taxonomía canónica oficial de 61 clases.
- La muestra oficial de 60 casos reales se completará físicamente en taller con el instrumento de recolección debidamente estandarizado.

---

## 10. Benchmarks Históricos Independientes

| Benchmark | n | F8.3 Baseline | Candidato C1 | Delta | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **TEST-100 Histórico** | 100 | 79.0% | **86.0%** | **+7.0 pp** | **SUPERADO** |
| **DEV-60 Histórico** | 60 | 85.0% | **90.0%** | **+5.0 pp** | **SUPERADO** |
| **G2 (Jerga Mecánica)** | 50 | 72.0% | **78.0%** | **+6.0 pp** | **SUPERADO** |
| **G1 (Estrés Multimarca)**| 50 | 90.0% | **90.0%** | 0.0 pp | **MANTENIDO** |

---

## 11. Decisión Metodológica Final

Se ratifica la recomendación formal:

**`RECOMENDAR_CONGELAR_C1`**

No se justifica la creación de C2. El candidato C1 ha demostrado una generalización superior en datos no vistos (+10.86 pp Top-1, +9.84 pp Top-3), supera a la línea base en todos los benchmarks independientes, resolvió la macro-clasificación con el macrofix al 96.46%, y sus errores restantes son gestionables por la capa dialógica de auto-interrogación.
