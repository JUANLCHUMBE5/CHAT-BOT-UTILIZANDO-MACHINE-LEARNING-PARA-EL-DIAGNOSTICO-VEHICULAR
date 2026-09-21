# CIERRE EXPERIMENTAL V2 / V2.1 / V2.2 Y FE DE ERRATAS METODOLÓGICA
**CARBOT — TESIS DE GRADO 2026**  
**Fecha de emisión:** 20 de Septiembre de 2026  
**Estado:** DOCUMENTO OFICIAL DE CIERRE Y FE DE ERRATAS  
**Clasificación:** AUDITORÍA METODOLÓGICA Y GOBERNANZA ML  

---

## 1. DECLARACIÓN DE CIERRE Y ARCHIVADO DE ENTORNOS EXPERIMENTALES

Se declara formal e irrevocablemente el cierre del ciclo de experimentación y reentrenamiento previo al trabajo de campo. Los siguientes tres directorios de experimentación quedan catalogados bajo el estado:

```text
ESTADO FORMAL: EXPERIMENTAL_ARCHIVED
```

- `machine_learning/experimentos/carbot_v2/`
- `machine_learning/experimentos/carbot_v2_1/`
- `machine_learning/experimentos/carbot_v2_2/`

### Directrices de Gobernanza:
1. **Preservación estricta:** Ninguno de los directorios anteriores ha sido eliminado ni movido de su ubicación física en el repositorio, garantizando el 100% de reproducibilidad y trazabilidad académica ante jurado o auditoría técnica.
2. **Aislamiento de runtime:** Ningún artefacto, modelo serializado (`.joblib`), vectorizador TF-IDF ni base vectorial RAG generados dentro de estos directorios ha sido inyectado ni referenciado en el entorno productivo de CarBot.
3. **Decisión oficial de tesis:**
   ```text
   DECISIÓN OPERACIONAL: MANTENER_CARBOT_PRECAMPO_FROZEN
   ```
4. **Calificación de versiones experimentales:**
   - **V2:** `SVM_V2_MEJORA_PARCIAL` / `RAG_V2_EMPEORA` (RAG V2 degradó MRR de 0.8704 a 0.7130; descartado).
   - **V2.1:** `V2_1_MEJORA_PARCIAL` (Depuración de datos y control de combustible efectivos, pero con overfitting a banco sintético y caída en generalización externa).
   - **V2.2:** `RESULTADO_EXPERIMENTAL_PROMETEDOR_SIN_SIGNIFICANCIA_ESTADISTICA` (Mejora sensiblemente en pares contrastivos adversariales de 45% a 70%, pero el test pareado McNemar contra el modelo congelado arrojó $p = 0.1690 > 0.05$, insuficiente para justificar una sustitución en tesis).
   - **V2.2-A:** Catalogado formal y exclusivamente como:
     ```text
     ESTADO V2.2-A: CANDIDATO_EXPERIMENTAL_POST_TESIS
     ```

---

## 2. FE DE ERRATAS: DISCREPANCIA DE VEREDICTOS V2.2

En revisiones preliminares de la Fase V2.2 coexistieron dos términos en reportes y borradores técnicos:
- `V2_2_MEJORA_PARCIAL`
- `V2_2_CANDIDATO_FUERTE`

A fin de mantener la integridad documental histórica sin alterar destructivamente los registros previos, la presente **Nota de Cierre y Fe de Erratas** unifica y formaliza el criterio científico definitivo:

1. **Fundamento empírico:** El modelo experimental V2.2-A demostró mejoras puntuales muy valiosas en entornos de laboratorio:
   - Elevó la precisión en pares contrastivos causales (adversariales) del 45.0% al 70.0%.
   - Redujo a 0.00% las incompatibilidades de combustible mediante soft-reranking contextual.
   - Alcanzó Top-1 de 83.06% en Banco 1 (vs. 81.69% Frozen) y 94.54% en Banco 3 (vs. 90.71% Frozen).
2. **Limitación inferencial:** En la evaluación simultánea y pareada sobre la totalidad de los 732 casos de prueba de los tres bancos ciegos, el modelo Frozen obtuvo 21 desaciertos favorables (ganancias) mientras que V2.2-A obtuvo 32 desaciertos favorables. La prueba exacta de McNemar resultó en $p = 0.16898 \approx 0.1690$.
3. **Resolución metodológica:** Al nivel de significancia prefijado $\alpha = 0.05$, $p = 0.1690$ indica que la diferencia entre ambos clasificadores no es estadísticamente significativa. Por tanto, no existe evidencia científica concluyente que justifique alterar la arquitectura ya congelada, validada por juicio de expertos y vinculada a la operacionalización de la tesis.
4. **Veredicto unificado:** Se ratifica que V2.2-A es un **Candidato Experimental Post-Tesis**, mientras que el sistema oficial para la recolección de campo de la tesis es estricta e invariablemente **CARBOT_PRECAMPO_FROZEN**.

---

## 3. AUDITORÍA Y ACLARACIÓN DEFINITIVA DE DATOS SINTÉTICOS

Para eliminar cualquier ambigüedad entre datos generados para investigación exploratoria y datos efectivamente incorporados a los pipelines de entrenamiento o producción, se certifica el siguiente inventario contrastado directamente con los archivos fuente del repositorio:

| Métrica / Parámetro | Valor Verificado | Fuente Directa de Comprobación |
| :--- | :---: | :--- |
| **Sintéticos generados en Fase V2.2** (`SYNTHETIC_GENERATED_TOTAL`) | **140** | `machine_learning/experimentos/carbot_v2_2/REPORTE_SINTETICOS_V2_2.csv` (140 filas, 14 clases deficitarias a 10 c/u) |
| **Sintéticos utilizados en V2.2-A** (`SYNTHETIC_USED_V2_2_A`) | **0** | `manifest_v2_2_a.json` (7,119 muestras = 7,099 V2.1-B + 20 contrastivos reales/técnicos, 0 sintéticos) |
| **Sintéticos utilizados en V2.2-B** (`SYNTHETIC_USED_V2_2_B`) | **70** | `manifest_v2_2_b.json` (7,189 muestras = 7,119 + 70 sintéticos lote B) |
| **Sintéticos utilizados en V2.2-C** (`SYNTHETIC_USED_V2_2_C`) | **140** | `manifest_v2_2_c.json` (7,259 muestras = 7,119 + 140 sintéticos lote C) |
| **Sintéticos en producción congelada** (`SYNTHETIC_USED_IN_THESIS_PRODUCTION`) | **0** | `data/processed/dataset_c1_balanceado_v1.csv` & `CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json` |
| **Sintéticos en muestra oficial PRE/POST** (`SYNTHETIC_USED_IN_OFFICIAL_PREPOST`) | **0** | Base de datos PostgreSQL (`ValidacionTaller`), reglas de negocio de backend |

### Declaración de Integridad:
- **0% de datos sintéticos en el clasificador de producción:** El modelo Linear SVM congelado de CarBot fue entrenado exclusivamente con el dataset oficial consolidado C1.
- **0% de datos sintéticos en la muestra de tesis:** La muestra de 60 casos (30 PRE y 30 POST) provendrá exclusivamente de vehículos físicos atendidos en el taller automotriz Carter Motor's E.I.R.L. durante la aplicación del instrumento de campo.

---

## 4. FE DE ERRATAS: INTERPRETACIÓN METODOLÓGICA DE LA PRUEBA DE MCNEMAR

Se rectifica cualquier descripción textual previa que pudiera inducir a confusión estadística respecto a la prueba de McNemar aplicada en la Fase V2.2:

1. **Diseño pareado por caso:**
   Tanto `CARBOT_PRECAMPO_FROZEN` como los candidatos experimentales V2.2 fueron evaluados sobre **los mismos 732 casos de prueba** (Banco 1: 183 casos, Banco 2: 183 casos, Banco 3: 366 casos). Por consiguiente, las observaciones están **estrictamente pareadas por ítem/caso vehicular**.
2. **Propósito de McNemar:**
   La prueba de McNemar es la prueba no paramétrica estándar adecuada para comparar el rendimiento de dos algoritmos de clasificación supervisada evaluados sobre el mismo conjunto de datos de prueba, midiendo la simetría de la tabla de contingencia de desacuerdos ($b$ vs. $c$).
   - Desacuerdos donde Frozen acertó y V2.2 falló ($b$): 21 casos.
   - Desacuerdos donde V2.2 acertó y Frozen falló ($c$): 32 casos.
3. **Interpretación estadística correcta:**
   - Estadístico $\chi^2$ con corrección de continuidad de Edwards: $p = 0.16898$.
   - Dado que $p > 0.05$, **no se rechaza la hipótesis nula ($H_0$)** de proporciones marginales homogéneas de acierto.
   - **Afirmación formal rigurosa:** *"No se encontró evidencia estadísticamente significativa, al nivel de significancia $\alpha = 0.05$, de una diferencia en la tasa de aciertos entre ambos clasificadores sobre la muestra de prueba evaluada"*.
   - **Corrección epistémica:** Queda expresamente prohibido afirmar que "se demostró que ambos modelos son equivalentes", dado que la ausencia de significancia estadística para rechazar $H_0$ no constituye matemáticamente una prueba de equivalencia bioestadística o TOST (Two One-Sided Tests).

---

## 5. DIRECTIVA FORMAL DE DETENCIÓN DE OPTIMIZACIÓN PRE-CAMPO

Queda formalmente asentada la instrucción directiva:

```python
DETENER_OPTIMIZACION_ML_PRECAMPO = True
```

Queda estrictamente prohibido ejecutar de forma automática o inducida:
- Ciclos de entrenamiento V2.3, V2.4 o posteriores.
- Ajustes de hiperparámetros en Linear SVM o vectorizadores TF-IDF.
- Alteraciones en la taxonomía oficial de 61 clases vehiculares y 7 macro-sistemas.
- Generación de nuevos datasets sintéticos o pseudo-sintéticos.
- Modificaciones en los umbrales de confianza (`confidence_threshold = 0.40`).
- Re-indexación o alteración del índice FAISS RAG OEM.

**El proyecto se encuentra cerrado en fase experimental y enfocado al 100% en el trabajo de campo.**
