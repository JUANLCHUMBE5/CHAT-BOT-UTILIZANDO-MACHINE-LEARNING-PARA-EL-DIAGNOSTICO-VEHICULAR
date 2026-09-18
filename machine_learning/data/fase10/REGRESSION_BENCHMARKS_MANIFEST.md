# Manifiesto de Benchmarks Externos y Regresiones Históricas — CarBot

Este documento formaliza el inventario de todos los conjuntos de evaluación histórica, benchmarks externos y casos reales de validación de CarBot.

> [!CAUTION]
> **REGLA METODOLÓGICA ESTRICTA (INVARIANTE DE TESIS)**:
> Todos los conjuntos listados a continuación tienen la condición de **`prohibido_entrenamiento = SI`**.
> Ninguno de estos casos ha sido incorporado ni debe incorporarse jamás a `TRAIN10`, `DEV10`, `TEST10` ni a ningún conjunto de ajuste, calibración o fine-tuning. Su propósito exclusivo es la evaluación comparativa externa y la verificación post-entrenamiento para garantizar la integridad académica y evitar sobreajuste (*data leakage*).

---

## 1. Inventario de Benchmarks

| Benchmark / Regresión | Ubicación / Archivo Canónico | Cantidad de Casos | Tipo de Muestra | Propósito y Uso Futuro | Prohibido Entrenamiento | Confirmación en Pool TRAIN10/DEV10 |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| **TEST-100 Histórico** | `machine_learning/data/benchmark_test_ciego_100.py` | 100 | Sintético calibrado | Evaluación ciega histórica comparativa frente a líneas base previas (Fase 7 / Fase 8). | **SI** | 0 casos incorporados (0% contaminación) |
| **DEV-60 Histórico** | `machine_learning/data/benchmark_dev_60_casos.py` | 60 | Sintético representativo | Medición histórica de desempeño inicial de desarrollo (Fase 8). | **SI** | 0 casos incorporados (0% contaminación) |
| **G1 (Estrés Multimarca)** | `scripts/benchmark_v4_g1_casos.py` | 50 | Sintético complejo | Prueba de estrés multimarca con ambigüedad léxica controlada y fallas acopladas. | **SI** | 0 casos incorporados (0% contaminación) |
| **G2 (Casos Límite y Jerga)** | `scripts/benchmark_v4_g2_casos.py` | 50 | Coloquial / Taller | Evaluación de resistencia a jerga mecánica latinoamericana y descripciones imprecisas. | **SI** | 0 casos incorporados (0% contaminación) |
| **FIELD-60 / Casos Reales Taller** | `machine_learning/data/casos_reales_mecanicos_evaluacion.csv` | 32 (avance actual a 60) | **Empírica Real** | **Muestra Oficial de Tesis**: Casos reales recopilados físicamente con mecánicos en taller para evaluación pretest y postest. | **SI** | 0 casos incorporados (0% contaminación) |
| **Regresión Histórica A/C** | `docs/graficas/reporte_evaluacion_v4_100_casos.json` (casos 1329, 2685) | 6 | Reporte técnico histórico | Verificación de no-regresión para Climatización vs Motor (evitar falsa alarma en refrigeración). | **SI** | 0 casos incorporados (0% contaminación) |
| **Regresiones Mecánicas Puras** | `backend/tests/test_repaso_averias_mecanicas_vs_dtc.py` | 20 | Taller físico | Validación de que averías mecánicas sin control electrónico nunca sugieran escaneo DTC. | **SI** | 0 casos incorporados (0% contaminación) |

---

## 2. Protocolo de Evaluación Posterior

1. **Aislamiento Total**: Ningún script de entrenamiento (`fit()`, `fit_transform()`, `GridSearchCV`) puede tener acceso a los archivos anteriores.
2. **Evaluación Comparativa Externa**: Solo tras finalizar el entrenamiento del candidato de Fase 10 (en la Etapa 3), se ejecutarán los scripts de evaluación externa para comparar:
   - Desempeño en **TEST-100 histórico** (Fase 8.3 baseline vs Fase 10 candidato).
   - Desempeño en **G1 / G2** (robustez ante ambigüedad y jerga).
   - Desempeño en **FIELD-60** (métricas oficiales de tesis).
   - Verificación de no-regresión en el caso de **A/C histórico** y averías mecánicas puras.
3. **Auditoría Cruzada**: La auditoría ejecutada en la Etapa 2 (`auditar_y_congelar_test10.py` y `generar_splits_train_dev10.py`) confirmó formalmente que **ninguno** de estos registros colisiona léxica o semánticamente con `TRAIN10`, `DEV10` ni `TEST10`.
