# AUDITORÍA FORENSE DE TAXONOMÍA, SPLIT Y RESULTADOS C1
**Sistema:** CarBot — Chatbot Diagnóstico Vehicular con Machine Learning  
**Fecha:** 17 de Septiembre de 2026  
**Fase:** 10 — Etapa 3.1  
**Estado:** `AUDITORIA_FORENSE_COMPLETADA`

---

## 1. Verificación Inicial de Hashes Criptográficos e Inmutabilidad

Antes de cualquier análisis, se verificó la integridad criptográfica byte a byte de los artefactos congelados:

| Componente | Archivo / Recurso | SHA-256 Esperado | SHA-256 Calculado | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Línea Base Fase 8.3** | 19 artefactos en `reporte_fase8_3_congelado.json` | 19/19 hashes registrados | 19/19 hashes coincidentes | **INMUTABLE (100%)** |
| **TRAIN10** | `machine_learning/data/fase10/train10_v1.csv` | `ec407886b48d66c4d9be6fc8b72decf605f4f94ac1af0575d9c4fa0db005e92b` | `ec407886b48d66c4d9be6fc8b72decf605f4f94ac1af0575d9c4fa0db005e92b` | **COINCIDENTE** |
| **DEV10** | `machine_learning/data/fase10/dev10_v1.csv` | `b44a752ca58fb4e27c7d9167198747e076d0c3cd5c4b07eaa03919777d1fd2b6` | `b44a752ca58fb4e27c7d9167198747e076d0c3cd5c4b07eaa03919777d1fd2b6` | **COINCIDENTE** |
| **TEST10 Ciego** | `machine_learning/data/fase10/test10_fase10_blind_v1.csv` | `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c` | `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c` | **LOCKED_BLIND_TEST** |

*Nota de Seguridad:* TEST10 permaneció 100% blindado y cerrado. Se verificó únicamente su secuencia de bytes (0 lecturas de texto, 0 consultas, 0 inferencias).

---

## 2. Investigación Central: Origen de las "Etiquetas Sospechosas" del Reporte C1

### 2.1 El Problema Detectado
En el documento `REPORTE_FASE10_ETAPA3_C1.md` (Sección 7.A), se listaron bajo *"Top 10 Clases con Mayor Ganancia en F1-Score"* etiquetas como:
- `Cremallera de direccion asistida electrica (EPS) o sensor de torque`
- `Fallo en modulo de control electronico (PCM / ECM / BCM)`
- `Falla en sensor de angulo de direccion (SAS) o calibracion ESP`
- `Falla en modulo de freno de mano electrico (EPB) o motor de pinza`
- `Valvula moduladora ABS o sensor de presion de frenos de aire (Camiones)`
- `Falla en suspension neumatica (compresor, balonas o valvulas)`
- `Desgaste de zapatas o tambores de freno trasero`

### 2.2 Hallazgo Forense y Causa Raíz
1. **En los Datasets y Modelos:** Ninguna de esas etiquetas existe como target en `train10_v1.csv`, `dev10_v1.csv`, `modelo_diagnostico.pkl` (F8.3) ni `modelo_diagnostico_c1.pkl` (C1).
2. **En el Script de Entrenamiento (`scratch/entrenar_y_evaluar_fase10_c1.py`):** El script se ejecutó en background (`task-2133`). El cálculo se realizó sobre `FALLA_A_SISTEMA` (las 61 clases canónicas).
3. **En el Archivo de Salida Métrico (`fase10_c1_metrics_by_class.csv`):** Contiene **exactamente 61 filas**, todas con nombres canónicos.
4. **En el Log Real del Proceso (`task-2133.log` líneas 125-136):**
   El script imprimió a stdout:
   ```text
   Top 10 Clases con Mayor Ganancia en F1-Score:
     + 7.8% F1 (F8.3: 85.7% -> C1: 93.5%) | Falla en termostato o motoventilador de radiador (n=32)
     + 7.1% F1 (F8.3: 82.3% -> C1: 89.5%) | Falla en sistema de frenado regenerativo (EV / Hibridos) (n=19)
     + 6.3% F1 (F8.3: 88.9% -> C1: 95.2%) | Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208) (n=20)
     + 5.2% F1 (F8.3: 88.9% -> C1: 94.1%) | Falla en bombin o bomba hidraulica de embrague (n=25)
     + 4.9% F1 (F8.3: 84.0% -> C1: 88.9%) | Fallo en inversor de corriente IGBT o motor electrico (EV) (n=26)
     + 4.8% F1 (F8.3: 82.3% -> C1: 87.2%) | Desgaste en collarin de empuje o crapodina de embrague (n=20)
     + 4.1% F1 (F8.3: 88.9% -> C1: 93.0%) | Rodajes de transmision manual o eje primario gastados (n=20)
     + 4.1% F1 (F8.3: 93.9% -> C1: 98.0%) | Válvula de freno de aire o secador APS obstruido (Camiones) (n=24)
     + 3.8% F1 (F8.3: 85.7% -> C1: 89.5%) | Foco o falla en sistema de refrigeracion de bateria/inversor (EV) (n=20)
     + 2.8% F1 (F8.3: 88.9% -> C1: 91.7%) | Elevalunas electrico o guaya de alzacristales rota o trabada (n=25)
   ```
5. **Causa del Error:** En el mensaje de finalización del proceso recibido por el agente previo, la salida de stdout estuvo truncada (`<truncated 157 lines>`). El agente no leyó `task-2133.log` ni `fase10_c1_metrics_by_class.csv`, sino que al redactar `REPORTE_FASE10_ETAPA3_C1.md` alucinó los nombres de las clases basándose libremente en descripciones técnicas de los generadores sintéticos de Fase 10.
6. **Conclusión:** Las etiquetas sospechosas fueron introducidas **únicamente en la redacción del reporte Markdown**. El pipeline, los datasets y los binarios se mantuvieron 100% fieles a la taxonomía canónica.

---

## 3. Extracción y Comparación Literal de Taxonomías

Se extrajeron las etiquetas únicas de las 7 fuentes del sistema:
1. `TRAIN_ORIGINAL`: 61 clases en `dataset_sintomas_limpio.csv`
2. `FASE10`: 61 clases en `dataset_fase10_master_v1_1_2440.csv`
3. `TRAIN10`: 61 clases en `train10_v1.csv`
4. `DEV10`: 61 clases en `dev10_v1.csv`
5. `F8.3`: 61 clases en `modelo_diagnostico.pkl`
6. `C1`: 61 clases en `modelo_diagnostico_c1.pkl`
7. `CODIGO`: 61 clases en `FALLA_A_SISTEMA` (`taxonomia_sistemas.py`)

### Resultados de la Comparación de Conjuntos (Diferencias Literales)
```text
TRAIN_ORIGINAL - FASE10 = 0 diferencias
FASE10 - TRAIN_ORIGINAL = 0 diferencias
TRAIN10 - FASE10        = 0 diferencias
FASE10 - TRAIN10        = 0 diferencias
DEV10 - FASE10          = 0 diferencias
FASE10 - DEV10          = 0 diferencias
F8.3 - FASE10           = 0 diferencias
FASE10 - F8.3           = 0 diferencias
C1 - FASE10             = 0 diferencias
FASE10 - C1             = 0 diferencias
CODIGO - FASE10         = 0 diferencias
FASE10 - CODIGO         = 0 diferencias
```
**¿Son todas exactamente iguales literalmente?: SÍ.**  
No existen 2 taxonomías de 61 ni sustitución de clases: existe **una única taxonomía canónica de 61 clases**, preservada al 100% en todas las fuentes.

---

## 4. Auditoría de Macro-Sistemas (`CARROCERIA_NEUMATICA` vs. `CARROCERIA_CONFORT`)

Se auditó la procedencia de los macro-sistemas en cada fuente:
- **Backend (`FALLA_A_SISTEMA`):** Define exactamente **7 macro-sistemas**:
  `MOTOR` (26), `FRENOS` (7), `TRANSMISION` (8), `SUSPENSION_CHASIS` (5), `ELECTRICO` (7), `CLIMATIZACION` (1), `CARROCERIA_NEUMATICA` (7).
- **Fase 8.3 (`modelo_sistema.pkl`):** Entrenado sobre esos **7 macro-sistemas** canónicos.
- **Dataset Original (`dataset_sintomas_limpio.csv`):** Contenía una columna `sistema` desnormalizada con **480 valores NaN** y 22 cadenas históricas dispares (`Carrocería y Confort`, `Frenos Neumáticos`, `Motor`, etc.).
- **Fase 10 Corpus (`dataset_fase10_master_v1_1_2440.csv`):** Estandarizó las clases 55–61 bajo `CARROCERIA_NEUMATICA` (coincidiendo con `FALLA_A_SISTEMA`).
- **Defecto en la Construcción de TRAIN10/DEV10 (`generar_splits_train_dev10.py`):**
  El script copió `df_orig_prep["macro_sistema"] = df_orig["sistema"]` de forma directa sin mapear las fallas originales mediante `FALLA_A_SISTEMA`.
  - Como resultado, `train10_v1.csv` heredó 374 NaNs y 23 etiquetas heterogéneas en la columna `macro_sistema`.
  - El modelo `modelo_sistema_c1.pkl` se ajustó sobre 24 clases (incluyendo `"nan"`), lo que distorsionó la precisión macro del modelo jerárquico secundario, aunque no alteró la clasificación de fallas de 61 clases.

---

## 5. Auditoría de DEV10 Original y Explicación del 99.92% de F8.3

El reporte C1 indicó que F8.3 obtuvo **99.92% de Top-1** sobre los 1,237 registros originales de DEV10.
- **Auditoría Forense:** Se comprobó si esos 1,237 registros existían en el conjunto de entrenamiento de F8.3.
- **Resultado:**
  - `exact_seen_by_f83_train`: **1,237 de 1,237 (100.00%)**
  - `truly_unseen_by_f83`: **0 de 1,237 (0.00%)**
- **Explicación Científica:** F8.3 fue entrenado en la Fase 8 sobre la **totalidad de los 6,189 registros** de `dataset_sintomas_limpio.csv`. Al evaluar F8.3 sobre los 1,237 registros de DEV10, se estaba midiendo **memorización de entrenamiento** (train accuracy), no generalización.
- **Contraste con C1:** El modelo C1 fue entrenado únicamente sobre los 4,952 registros originales de TRAIN10 (el 80%). Los 1,237 registros de DEV10 fueron **rigurosamente no vistos por C1**. Su 89.41% de Top-1 refleja generalización genuina sobre datos no vistos de taller.

---

## 6. Auditoría del Agrupamiento por Raíz Sintomática (`norm_g`)

Se auditaron los 4,832 grupos generados mediante `norm_g` sobre los 6,189 registros originales:
- Grupos con 1 registro: **4,463 (92.36%)**
- Grupos con >1 registro: **369 (7.64%)**
- Tamaño máximo de grupo: **17 registros**
- Grupos multi-clase: **0 (100% pureza de clase)**
- Grupos compartidos entre TRAIN10 y DEV10: **0 (cero colisiones de id_grupo)**
- **Near-Duplicates Cruzando el Split:**
  - Se detectaron **327 registros en DEV10** que poseen al menos un par en TRAIN10 con similitud de coseno TF-IDF $\ge 0.88$ (correspondientes a 318 pares con el mismo target).
  - Al aislar los 910 registros originales estrictamente limpios de near-duplicates, C1 obtiene **87.58% Top-1** y **83.69% Macro F1**.

---

## 7. Reinterpretación Desglosada de Métricas Globales (C1 vs. F8.3)

Al descomponer DEV10 (n=1,725) en sus fuentes reales, eliminando la distorsión del 99.92% de datos memorizados por F8.3:

| Subconjunto DEV10 | n | F8.3 Top-1 | C1 Top-1 | Delta Top-1 | F8.3 Top-3 | C1 Top-3 | Delta Top-3 | F8.3 Macro F1 | C1 Macro F1 | Delta MF1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DEV10 Global (Aparente)** | 1725 | 88.52% | 84.06% | -4.46% | 94.20% | 91.71% | -2.49% | 88.26% | 84.37% | -3.89% |
| **Original Visto por F8.3 (Total)** | 1237 | 99.92% | 89.41% | -10.51% | 100.00% | 92.64% | -7.36% | 99.92% | 90.06% | -9.86% |
| *— Original con Near-Duplicate* | 327 | 100.00% | 94.50% | -5.50% | 100.00% | 95.11% | -4.89% | 100.00% | 94.49% | -5.51% |
| *— Original Limpio Sin Near-Duplicate* | 910 | 99.89% | 87.58% | -12.31% | 100.00% | 91.76% | -8.24% | 99.91% | 83.69% | -16.22% |
| **Sintético Fase 10 (No Visto por Ambos)** | **488** | **59.63%** | **70.49%** | **+10.86%** | **79.51%** | **89.34%** | **+9.84%** | **59.50%** | **70.14%** | **+10.65%** |
| *— Sintético L1 (Coloquial)* | 122 | 42.62% | 52.46% | +9.84% | 66.39% | 72.13% | +5.74% | 38.40% | 48.51% | +10.11% |
| *— Sintético L2 (Taller/Semi-técnico)* | 183 | 67.76% | 77.60% | +9.84% | 86.34% | 95.63% | +9.29% | 65.36% | 75.50% | +10.14% |
| *— Sintético L3 (Metrológico/DTC)* | 183 | 62.84% | 75.41% | +12.57% | 81.42% | 94.54% | +13.11% | 60.18% | 74.51% | +14.33% |

*Interpretación:*
En el único subconjunto de DEV10 que representa una evaluación ciega e independiente para ambos modelos (el corpus sintético Fase 10, n=488), **C1 supera a F8.3 por más de 10 puntos porcentuales** en Top-1 (+10.86%), Top-3 (+9.84%) y Macro F1 (+10.65%).

---

## 8. Trazabilidad del Caso Histórico de Climatización (A/C)

- **Evaluación Directa:** Al evaluar frases de A/C aisladas, tanto F8.3 como C1 predicen `Falla en compresor de aire acondicionado o fuga de gas R134a` con >95% de confianza.
- **Causa del Fallo Histórico:** Ocurrió dentro de sesiones conversacionales multi-turno (`resultados_piloto_fase9_2.json`, Caso 02) donde quejas previas de motor (pérdida de potencia, humo negro) se acumulaban en `SintetizadorConsulta`. La frase *"con el aire acondicionado encendido"* se interpretaba como un modificador de sobreesfuerzo del motor y no como un caso nuevo de climatización, provocando diagnósticos de mezcla/combustible. El problema fue resuelto en las Fases 9.10–9.13 con el `SegmentadorCasos`.

---

## 9. Auditoría del Dataset FIELD

- **Archivo Real:** `machine_learning/data/casos_reales_mecanicos_evaluacion.csv`
- **Filas Reales:** **32 registros** (no 60).
- **Razón Metodológica:** De acuerdo con la Regla de Tesis 2 de `AGENTS.md`, el trabajo de campo se encuentra en desarrollo con un avance real de 32 de 60 casos verificados en taller. Los 28 restantes corresponden a la muestra pendiente de recopilación física por los mecánicos.

---

## 10. Conclusión y Estado

La auditoría forense descarta cualquier ruptura en la taxonomía de 61 clases. Las métricas de C1 son matemáticamente válidas bajo la taxonomía canónica; la discrepancia en el reporte anterior fue un error de transcripción/alucinación del agente al redactar la sección 7.A tras una salida truncada en consola.
