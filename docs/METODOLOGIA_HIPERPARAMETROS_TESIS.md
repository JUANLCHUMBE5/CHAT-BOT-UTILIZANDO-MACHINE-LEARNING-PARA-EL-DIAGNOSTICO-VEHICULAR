# Metodología de Validación y Justificación de Hiperparámetros de Diseño — CarBot

Este documento establece la justificación teórica, matemática y metodológica de los hiperparámetros de diseño del sistema CarBot, asegurando la reproducibilidad, la integridad académica y la defensa sólida ante el jurado de tesis.

---

## 1. Justificación de la Comparabilidad de Modelos (Holdout Jerárquico vs. Modelo Preliminar)

### 1.1 Naturaleza de la Métrica: 95.01% (Preliminar) vs. 93.07% (Jerárquico V3)
En las etapas iniciales de la investigación, el prototipo clasificaba únicamente **13 averías genéricas** con un conjunto de entrenamiento reducido de 4,959 registros simplificados. Sobre ese espacio de etiquetas restringido, el clasificador monocapa reportaba un Accuracy en holdout del **95.01%**.

En la **Fase 5 y 6**, la arquitectura se expandió para abarcar la realidad operativa completa del taller automotriz:
- **Espacio de salida multiclase**: Se incrementó de 13 clases a **48 averías especializadas** (un incremento de más del 269% en complejidad combinatoria).
- **Taxonomía jerárquica en dos niveles**:
  - **Nivel 1 (Macro-Sistemas)**: 7 categorías vehiculares (`MOTOR`, `FRENOS`, `TRANSMISION`, `SUSPENSION_CHASIS`, `ELECTRICO`, `CLIMATIZACION`, `CARROCERIA_NEUMATICA`).
  - **Nivel 2 (Fallas Específicas)**: 48 clases de fallas mecánicas y electromecánicas.
- **Dataset Canónico Expandido**: 5,374 casos reales con cadenas causales y casos de contraste frontera.

### 1.2 Declaración Metodológica para la Tesis
> [!IMPORTANT]
> **Aclaración para el Jurado**:
> No debe presentarse la transición 95.01% $\rightarrow$ 93.07% como una degradación o mejora directa unidimensional, debido a que el espacio de clases cambió cualitativa y cuantitativamente ($13 \rightarrow 48$ clases). En un espacio de 48 clases con fallas limítrofes (ej. *desbalanceo de ruedas* vs. *alabeo de discos*; *desfase de distribución* vs. *falla de sensor CKP*), un **Accuracy de 93.07% en holdout interno**, un **98.71% en Macro-Sistema** y un **Top-3 Accuracy del 98.71%** representa una capacidad de discriminación diagnóstica sustancialmente superior para el mecánico de taller.

---

## 2. Justificación de los Hiperparámetros de Diseño

Todos los hiperparámetros fueron determinados mediante validación cruzada y análisis de error en el conjunto de desarrollo (*validation set*), **nunca ajustados mirando los benchmarks externos ciegos (V2 o V3)**, garantizando la ausencia de fuga de información (*data leakage*).

### 2.1 Ponderación Jerárquica Suave: Exponente $\gamma = 0.65$
La probabilidad combinada de una falla $F_i$ perteneciente al macro-sistema $S_k$ se calcula mediante:

$$P_{\text{comb}}(F_i) = P(F_i) \times [P(S_k)]^{\gamma}$$

- **Justificación**: Si se utilizara un producto Bayesiano estricto ($\gamma = 1.0$), una ligera incertidumbre en la clasificación del macro-sistema (por ejemplo, si el síntoma comparte vibración entre chasis y frenos con $P(S_k) = 0.50$) castigaría excesivamente las probabilidades del Nivel 2.
- **Optimización empírica en validación**:
  - $\gamma = 1.0$: Sobre-penalización de averías con síntomas compartidos.
  - $\gamma = 0.0$: Pérdida del beneficio jerárquico; anomalías entre sistemas cruzados (ej. sensor de oxígeno compitiendo con pastillas de freno).
  - $\gamma = 0.65$: Suprime con certeza $>95\%$ las opciones absurdas fuera de sistema, mientras conserva la competencia sutil entre fallas pertenecientes al mismo subsistema.

### 2.2 Multiplicador de Autoridad DTC: Factor $2.5\times$
Cuando el texto o el escáner del mecánico reporta un código DTC oficial (ej. `P0301`, `P0841`, `P0420`):

$$P_{\text{dtc}}(F_i) = \min(1.0, P_{\text{comb}}(F_i) \times 2.5) \quad \text{si } F_i \in \text{Candidatos}(DTC)$$

- **Justificación de Ingeniería**: Un código OBD-II no es una percepción subjetiva del usuario, sino una lectura electrónica digital generada por la ECU con umbrales de diagnóstico validados por norma SAE J1939 / ISO 14229. El multiplicador $2.5\times$ garantiza que el clasificador pondere la evidencia instrumental por encima de la ambigüedad del lenguaje coloquial, fijando el macro-sistema con certidumbre $\ge 92\%$.

### 2.3 Regla de Incertidumbre y Margen Top 1 – Top 2: Umbral Canónico $\Delta \ge 10\%$
Un error común en asistentes automotrices es evaluar únicamente si $\text{Top 1} \ge 50\%$.
En CarBot, se evalúa tanto la confianza absoluta como el **margen diferencial canónico**:

$$\Delta = P(\text{Top 1}) - P(\text{Top 2})$$

- **Valor Canónico Unificado**: $\Delta \ge 10\%$ (`margen >= 0.10`).
- **Condición de No-Interrupción**: El sistema responde directamente sin repreguntar si:
  $$P(\text{Top 1}) \ge 70\% \quad \lor \quad (P(\text{Top 1}) \ge 50\% \land \Delta \ge 10\%)$$
- **Caso A (Ambiguo)**: $\text{Top 1} = 51\%$, $\text{Top 2} = 48\%$ ($\Delta = 3\% < 10\%$). Las dos hipótesis están prácticamente empatadas. El sistema activa el **auto-interrogador técnico** con opciones estructuradas para discriminar la causa física.
- **Caso B (Asertivo)**: $\text{Top 1} = 52\%$, $\text{Top 2} = 14\%$ ($\Delta = 38\% \ge 10\%$). Existe una separación neta; el sistema emite el diagnóstico sin interrumpir al mecánico con preguntas redundantes.
- **Regla de Bypass por DTC**: Si existe un código DTC confirmado en el mensaje, la ambigüedad queda descartada electrónicamente y no se requiere repreguntar.

### 2.4 Multiplicadores de Reordenamiento Multiseñal en RAG
El motor RAG no depende exclusivamente de la similitud semántica coseno cruda de embeddings en FAISS, ya que descripciones sintomáticas ambiguas (ej. "el carro vibra a 90 km/h") pueden arrojar alta similitud tanto con manuales de discos de freno como con manuales de balanceo de ruedas.
Para garantizar precisión metrológica, el reordenador multiseñal ajusta el score base según las siguientes reglas probabilísticas pre-calibradas:

| Señal de Ajuste | Factor Multiplicador | Justificación Técnica de Taller |
| :--- | :--- | :--- |
| **Coincidencia directa con DTC activo** | $\times 3.00$ | Máxima prioridad documental: el manual OEM específico del código OBD-II debe encabezar la recuperación. |
| **Coincidencia con Macro-Sistema ML** | $\times 1.60$ | Alinea la recuperación con el sistema vehicular validado por el clasificador Nivel 1. |
| **Coincidencia con Falla Top-1 ML** | $\times 2.20$ | Impulsa el procedimiento técnico específico correspondiente a la hipótesis diagnóstica principal. |
| **Coincidencia con Falla Top-2 ML** | $\times 1.50$ | Permite recuperar el procedimiento alternativo para el diagnóstico diferencial. |
| **Coincidencia con Falla Top-3 ML** | $\times 1.25$ | Mantiene relevancia en casos complejos multiavería. |
| **Incompatibilidad de Macro-Sistema** | $\times 0.20$ | **Supresión cruzada**: penaliza severamente manuales de sistemas no compatibles (ej. climatización cuando la falla es en frenos), eliminando falsos positivos. |

---

## 3. Protocolo de Evaluación y Separación de Conjuntos

```
                      UNIVERSO DE DATOS DE TALLER
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
  DATASET CANÓNICO                                  BENCHMARKS CIEGOS
   (5,374 registros)                                 (100 casos cada uno)
         │                                                   │
   ┌─────┴───────────────┐                             ┌─────┴───────────────┐
   ▼                     ▼                             ▼                     ▼
Entrenamiento         Validación                  Benchmark V2          Benchmark V3
  (80% = 4,299)       Holdout                    (Diagnóstico de     (Validación Ciega
                      (20% = 1,075)                 Línea Base)          Definitiva)
                         │
                         ├── Holdout Falla: 92.98%
                         ├── Holdout Sistema: 98.71%
                         └── Holdout Combinado: 93.07%
```

1. **Entrenamiento y Validación**: Se reservan estrictamente dentro de `machine_learning/data/` para calibrar el modelo Linear SVM con TF-IDF.
2. **Benchmark V2 (100 casos auditados)**: Utilizado para la detección de clases débiles y el análisis de la matriz de confusión externa.
3. **Benchmark V3 (100 casos inéditos)**: Casos de lenguaje real de taller nunca vistos por el modelo ni por el RAG durante el diseño, garantizando una evaluación externa ecológicamente válida.
4. **Benchmark V4 (100 casos nuevos independientes — Fase 7)**: Conjunto de validación totalmente ciego para contrastación experimental definitiva y ablación.

---

## 4. Resumen de Métricas Oficiales de Tesis (Benchmark V3)

| Dimensión de Evaluación | Métrica Obtenida | Meta de Tesis | Estado |
| :--- | :--- | :--- | :--- |
| **Exactitud Top-1 Estricta** | **82.00%** | $\ge 75\%$ | Superada |
| **Exactitud Top-1 Diferencial (Aceptable)** | **93.00%** | $\ge 85\%$ | Superada |
| **Exactitud Top-3 (Cobertura Diagnóstica)** | **100.00%** | $\ge 95\%$ | Óptima (100/100) |
| **Exactitud de Macro-Sistema** | **96.00%** | $\ge 90\%$ | Superada |
| **Confianza Calibrada Promedio** | **74.75%** | $\ge 65\%$ | Superada |
| **RAG Hit@1 (Procedimiento Relevante #1)** | **86.00%** | $\ge 80\%$ | Superada |
| **RAG Hit@3** | **97.00%** | $\ge 90\%$ | Superada |
| **RAG Hit@5** | **100.00%** | $\ge 95\%$ | Óptima (100/100) |
| **RAG Mean Reciprocal Rank (MRR)** | **0.9137** | $\ge 0.85$ | Superada |
| **Latencia de Inferencia ML** | **11.39 ms** | $\le 50$ ms | Excelente |
| **Latencia de Recuperación RAG** | **3.02 ms** | $\le 20$ ms | Excelente |

---

## 5. Manifiesto Criptográfico de Congelamiento Oficial Pre-Evaluación V4 (Candidato a Tesis)

Para garantizar la inmutabilidad de los artefactos y certificar ante el jurado de tesis que no existió fuga de información (*data leakage*) ni manipulación posterior de parámetros, se registran los identificadores criptográficos SHA-256 canónicos:

| Componente del Sistema | Ruta Canónica del Archivo | Identificador SHA-256 (Hash Oficial) | Estado |
| :--- | :--- | :--- | :--- |
| **Dataset Canónico ML (5,374 casos)** | `machine_learning/data/dataset_sintomas_limpio.csv` | `408792c0b188a95bbc09cf5b922e8cdc65a8629e9862e5745be501662e53d238` | **CONGELADO** |
| **Clasificador Diagnóstico (48 clases)** | `machine_learning/models/modelo_diagnostico.pkl` | `5cc6b7432377cb4c450fa6ecbc9322f3aec89bf36847875e3ac0a0c67798e251` | **CONGELADO** |
| **Clasificador Macro-Sistema (7 sistemas)** | `machine_learning/models/modelo_sistema.pkl` | `42f899f99725b7b4af1a0f4c28997d1538838ba0d45a2b6a63e8f10d05aabbea` | **CONGELADO** |
| **Vectorizador Lingüístico TF-IDF** | `machine_learning/models/vectorizador_tfidf.pkl` | `1cf7cd5dfddc344f08458cebd4fb4a5162e86cb1c5adebd69fa5fdf333aabe74` | **CONGELADO** |
| **Catálogo Metadatos RAG (205 docs)** | `machine_learning/manuals/metadatos_manuales.json` | `c3f82eddfe44762a473daedda8ca85031066bd506d6ed97b049ae332c95a78b1` | **CONGELADO** |
| **Corpus OEM Multimarca con Metrología** | `machine_learning/manuals/generales/manual_procedimientos_multimarca.txt` | `be89294242b69d20de35ac5595fd818b46c8e10b4f1f02d0f6ec1fae8d1f46c3` | **CONGELADO** |

> [!NOTE]
> Ningún archivo listado en este manifiesto será modificado durante la ejecución de los benchmarks externos, estudios de ablación o evaluaciones cuali-cuantitativas de la Fase 7.

