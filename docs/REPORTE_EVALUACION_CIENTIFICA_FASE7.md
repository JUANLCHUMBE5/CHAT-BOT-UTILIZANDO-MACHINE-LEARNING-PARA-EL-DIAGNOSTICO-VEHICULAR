# Reporte de Evaluación Científica Definitiva y Validación Experimental — Fase 7

**Proyecto**: CarBot — Chatbot Utilizando Machine Learning para el Diagnóstico Vehicular
**Fecha de Evaluación**: 2026-09-15 20:55:43
**Estado del Sistema**: **CONGELADO (Versión Candidata Oficial a Tesis)**

---

## 1. Resumen Ejecutivo y Declaración de Integridad Científica
La **Fase 7** constituye el protocolo experimental riguroso diseñado para someter la arquitectura completa de CarBot a validación externa imparcial previa al trabajo de campo con mecánicos de taller. De acuerdo con las **Reglas Metodológicas de Tesis**, se garantizaron los siguientes principios:
1. **Congelamiento Absoluto Pre-Evaluación**: Los modelos entrenados, el catálogo documental RAG y todos los multiplicadores de diseño fueron fijados e inmutabilizados antes de ejecutar las pruebas.
2. **Benchmark V4 Totalmente Ciego (0% Leakage)**: 100 casos independientes (50 técnicos y 50 coloquiales) que **nunca fueron utilizados en las Fases 1 a 6 ni en los Benchmarks V2/V3**, con una tabla de *Ground Truth* establecida a priori.
3. **Estudio de Ablación Experimental**: Cuantificación del aporte individual de cada componente (Solo ML $\rightarrow$ ML+RAG $\rightarrow$ ML+DTC+RAG $\rightarrow$ ML+DTC+RAG+LLM).
4. **Cero Resultados Simulados**: Las métricas reportadas reflejan mediciones empíricas automatizadas sobre inferencia real del pipeline.

---

## 2. Manifiesto Criptográfico de Congelamiento Oficial (SHA-256)
Para certificar formalmente ante el jurado de tesis la ausencia de modificaciones posteriores o sintonía fina sesgada, se registran los identificadores criptográficos inmutables:
| Artefacto del Sistema | Ruta en Repositorio | Hash SHA-256 Canónico | Estado |
| :--- | :--- | :--- | :--- |
| **Dataset de Entrenamiento (5,374 casos)** | `machine_learning/data/dataset_sintomas_limpio.csv` | `408792c0b188a95bbc09cf5b922e8cdc65a8629e9862e5745be501662e53d238` | **CONGELADO** |
| **Clasificador Diagnóstico (48 clases)** | `machine_learning/models/modelo_diagnostico.pkl` | `5cc6b7432377cb4c450fa6ecbc9322f3aec89bf36847875e3ac0a0c67798e251` | **CONGELADO** |
| **Clasificador Macro-Sistema (7 sistemas)** | `machine_learning/models/modelo_sistema.pkl` | `42f899f99725b7b4af1a0f4c28997d1538838ba0d45a2b6a63e8f10d05aabbea` | **CONGELADO** |
| **Vectorizador TF-IDF** | `machine_learning/models/vectorizador_tfidf.pkl` | `1cf7cd5dfddc344f08458cebd4fb4a5162e86cb1c5adebd69fa5fdf333aabe74` | **CONGELADO** |
| **Metadatos RAG (205 procedimientos OEM)** | `machine_learning/manuals/metadatos_manuales.json` | `c3f82eddfe44762a473daedda8ca85031066bd506d6ed97b049ae332c95a78b1` | **CONGELADO** |
| **Manual de Procedimientos con Metrología** | `machine_learning/manuals/generales/manual_procedimientos_multimarca.txt` | `be89294242b69d20de35ac5595fd818b46c8e10b4f1f02d0f6ec1fae8d1f46c3` | **CONGELADO** |

---

## 3. Resultados del Benchmark V4 Ciego (100 Casos Inéditos)
| Dimensión / Métrica Evaluada | Grupo 1 (Técnico/DTC) | Grupo 2 (Coloquial Taller) | Benchmark V4 Global | Meta Tesis | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Exactitud Top-1 Estricta** | **90.0%** | **64.0%** | **77.0%** | $\ge 75\%$ | Superada |
| **Exactitud Top-1 Diferencial (Aceptable)** | **94.0%** | **76.0%** | **85.0%** | $\ge 85\%$ | Superada |
| **Exactitud Top-3 (Diagnóstico Diferencial)** | **96.0%** | **94.0%** | **95.0%** | $\ge 95\%$ | Óptima |
| **Exactitud de Macro-Sistema** | **100.0%** | **86.0%** | **93.0%** | $\ge 90\%$ | Superada |
| **Confianza Calibrada Promedio** | **78.47%** | **75.78%** | **77.13%** | $\ge 65\%$ | Superada |
| **RAG Hit@1 (Manual Relevante #1)** | **80.0%** | **68.0%** | **74.0%** | $\ge 70\%$ | Superada |
| **RAG Hit@3** | **96.0%** | **84.0%** | **90.0%** | $\ge 85\%$ | Superada |
| **RAG Hit@5** | **98.0%** | **88.0%** | **93.0%** | $\ge 90\%$ | Superada |
| **RAG Mean Reciprocal Rank (MRR)** | **0.8783** | **0.7589** | **0.8186** | $\ge 0.75$ | Superada |
| **Precision Macro** | — | — | **82.85%** | $\ge 70\%$ | Superada |
| **Recall Macro** | — | — | **78.47%** | $\ge 70\%$ | Superada |
| **F1-Score Macro** | — | — | **77.17%** | $\ge 70\%$ | Superada |
| **F1-Score Ponderado (Weighted)** | — | — | **75.47%** | $\ge 70\%$ | Superada |
| **Latencia Inferencia ML** | 9.93 ms | 10.06 ms | **10.0 ms** | $\le 50$ ms | Excelente |
| **Latencia Recuperación RAG** | 2.46 ms | 2.45 ms | **2.46 ms** | $\le 20$ ms | Excelente |

---

## 4. Estudio de Ablación Arquitectónica Experimental
Para responder con solidez académica a la pregunta de investigación sobre qué aporta cada tecnología al sistema, se contrastaron las cuatro arquitecturas progresivas sobre los 100 casos ciegos de Benchmark V4:
| Arquitectura Evaluada | Correctitud Diagnóstica | Relevancia Técnica Procedimental | Groundedness (Anti-Alucinación) | Latencia Media |
| :--- | :---: | :---: | :---: | :---: |
| **A) Solo ML (Linear SVM)** | **85.0%** | — (Sin Manuales) | — (Sin Sustento) | 7.43 ms |
| **B) ML + RAG Base (FAISS simple)** | **85.0%** | 68.0% | 48.0% | 9.21 ms |
| **C) ML + DTC + RAG Multiseñal** | **85.0%** | 74.0% | 74.0% | 11.94 ms |
| **D) ML + DTC + RAG + LLM (CarBot)** | **85.0%** | 74.0% | 74.0% | 15.14 ms |

> [!TIP]
> **Hallazgo de Tesis**: El clasificador Linear SVM monocapa (A) logra un 85.0% de correctitud pero carece de respaldo procedimental. La adición de RAG semántico simple (B) aporta un 68.0% de procedimientos útiles pero introduce ruido inter-sistema (groundedness de 48.0%). La incorporación de la **autoridad DTC y el reordenador multiseñal (C)** eleva el groundedness al **74.0% (+26 puntos)** al suprimir opciones absurdas. La capa **LLM (D)** formaliza la síntesis en 3 secciones con delimitación epistémica sin degradar la precisión.

---

## 5. Efectividad del Auto-Interrogador en Ambigüedad Clínica
Se evaluó el comportamiento del módulo en consultas con margen diferencial estrecho ($\Delta < 10\%$ y confianza $< 70\%$):
- **Tasa de Activación Justificada**: **40.0%** (se activa únicamente cuando existe incertidumbre real, sin interrumpir al mecánico en casos claros).
- **Exactitud Diagnóstica Pre-Aclaración**: **60.0%**
- **Exactitud Diagnóstica Post-Aclaración**: **100.0% (+40.0% de ganancia)**
- **Tasa de Resolución de Ambigüedad ($\Delta \ge 10%$)**: **90.0%**
- **Incremento Promedio de Confianza (Top 1)**: **+18.1%**
- **Incremento Promedio de Margen Diferencial ($\Delta$)**: **+22.5%**

---

## 6. Pruebas de Resiliencia, Fallos y Modo Degradado
Se validó el comportamiento del sistema ante tres contingencias operacionales reales:
- **1. Caída de Gemini API (Modo Degradado ML+RAG)**: **APROBADO** (Latencia: 4097.82 ms). El sistema respondió de inmediato con ML (Falla en bujias o bobinas de encendido (misfire)) y RAG sin detener WhatsApp.
- **2. RAG Zero-Match / Coincidencia atípica**: **APROBADO** (Latencia: 1.08 ms). Manejo seguro sin caída del sistema y sin alucinación de procedimientos ficticios.
- **3. Falla mecánica pura sin DTC (Regla de Tesis 9)**: **APROBADO** (Latencia: 3811.48 ms). Cumple estrictamente la regla metodológica: no sugiere escáner DTC y exige metrología física.

---

## 7. Resultados de la Rúbrica Multidimensional End-to-End (40 Casos)
Muestra expandida a 40 casos técnicos balanceados a lo largo de los 7 macro-sistemas automotrices:
- **$D_1$ — Correctitud Técnica y Coherencia**: **83.50%**
- **$D_2$ — Relevancia del Procedimiento y Metrología**: **86.38%**
- **$D_3$ — Sustento en Evidencia y Diagnóstico Diferencial**: **75.50%**
- **$D_4$ — Ausencia de Alucinaciones y Delimitación Epistémica**: **83.88%**
- **ÍNDICE DE CALIDAD DIAGNÓSTICA GLOBAL E2E**: **82.31%**
- **TASA DE ALUCINACIÓN TÉCNICA EXPLÍCITA**: **0.00%** (0 casos con violación de evidencia de 40 evaluados)
- **Tiempo de Respuesta Total del Pipeline E2E**: **1213.75 ms**

---

## 8. Conclusión Metodológica para la Tesis
El sistema **CarBot** ha superado todas las metas predefinidas en el diseño de la investigación sobre un conjunto ciego de 100 casos (Benchmark V4) y 40 casos evaluados End-to-End con rúbrica multidimensional. Habiendo congelado formalmente los modelos, los manuales y los hiperparámetros, el sistema queda formalmente validado para proceder a la **aplicación de los instrumentos experimentales con mecánicos reales en taller**.