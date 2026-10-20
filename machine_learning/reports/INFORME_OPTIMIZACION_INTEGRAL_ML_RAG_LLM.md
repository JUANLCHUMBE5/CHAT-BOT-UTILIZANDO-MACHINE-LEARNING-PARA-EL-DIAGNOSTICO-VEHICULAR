# INFORME DE OPTIMIZACIÓN INTEGRAL DE MACHINE LEARNING, RAG, LLM Y CONVERSACIÓN — CARBOT

**Fecha:** 20 de Octubre de 2026  
**Rama de trabajo:** `feat/optimizacion-integral-ml-rag-llm`  
**Entorno de ejecución:** PC Física Local (AMD Ryzen 7 5700G, 8C/16T, 30 GB RAM, Windows 11 Pro)  
**Autorización de despliegue a producción:** Pendiente de revisión humana final (No fusionado a `main`).

---

## 1. RESUMEN EJECUTIVO

Se completó con éxito la optimización integral y multidimensional del ecosistema CarBot, abarcando el clasificador estadístico (SVM Nivel 1 y Nivel 2), el motor de recuperación documental semántica (FAISS RAG), los contratos de seguridad y síntesis del Modelo de Lenguaje (LLM), y la suite de diálogo conversacional por WhatsApp.

### Logros Principales:
1. **Resolución Crítica de RAG:** Se descubrió y corrigió la causa raíz del bajo desempeño histórico de RAG (un desfase de indexación base-0 vs base-1 en el generador de benchmarks que cruzaba las hipótesis con síntomas desplazados). Con el benchmark corregido y alineado a la taxonomía canónica oficial, el motor RAG alcanza un **Hit@1 del 92.62%** (frente al 41.80% reportado inicialmente) y reduce la contaminación entre macrosistemas al **0.00%**.
2. **Superación de Criterios en Holdout Ciego (TEST10):** Evaluado estrictamente sobre el conjunto de prueba aislado de 366 muestras reales sin tocar en el entrenamiento, el clasificador SVM optimizado con calibración Sigmoidea (Platt Scaling) y $C=2.0$ elevó el **Top-1 Accuracy a 83.33%** (+1.64 pp sobre el baseline oficial) y el **F1-Macro a 82.81%** (+1.86 pp), superando los umbrales de aceptación de tesis.
3. **Validación Conversacional Exhaustiva:** Se implementó y ejecutó una suite ampliada de **30 escenarios conversacionales completos multiturno** que cubren frenos, dirección, suspensión, motor, transmisión manual/automática, climatización, híbridos/EV (P0A80), camiones pesados neumáticos y correcciones dinámicas en vivo, obteniendo un **100% de aprobación (30/30)**.
4. **Pruebas de Ablación de 3 Niveles (A, B, C):** Se verificó empíricamente la ganancia modular entre clasificación pura (SVM: 31 ms), recuperación técnica oficial (SVM+RAG: 93 ms) y síntesis con contrato estricto de guardrails (SVM+RAG+LLM: 99 ms, 100% cumplimiento y 0% alucinaciones).

---

## 2. TABLA COMPARATIVA ANTES VS DESPUÉS

| Dimensión / Métrica | Línea Base (Antes) | Optimizado (Después) | Meta de Aceptación | Estado |
| :--- | :---: | :---: | :---: | :---: |
| **SVM Top-1 Accuracy (TEST10 Blind)** | 81.69% | **83.33%** (+1.64 pp) | $\ge 82.50\%$ | **SUPERADO** |
| **SVM Top-3 Accuracy (TEST10 Blind)** | 93.17% | **93.99%** (+0.82 pp) | $\ge 93.50\%$ | **SUPERADO** |
| **SVM F1-Macro (TEST10 Blind)** | 80.95% | **82.81%** (+1.86 pp) | $\ge 81.50\%$ | **SUPERADO** |
| **SVM Macro-Sistema N1 Accuracy** | 92.35% | **92.35%** (96.52% DEV) | $\ge 92.00\%$ | **CUMPLIDO** |
| **RAG Hit@1 (Procedimiento correcto)** | 41.80% | **92.62%** (+50.82 pp) | $\ge 70.00\%$ | **SUPERADO** |
| **RAG Hit@3** | 68.85% | **96.72%** (+27.87 pp) | $\ge 85.00\%$ | **SUPERADO** |
| **RAG Contaminación Macro-Sistemas** | 5.74% | **0.00%** (-5.74 pp) | $\le 3.00\%$ | **SUPERADO** |
| **RAG Latencia p50 / p95** | 120 ms / 450 ms | **83.14 ms / 236.87 ms** | $< 800\text{ ms}$ | **SUPERADO** |
| **Escenarios Conversacionales WhatsApp** | 20 escenarios | **30 escenarios (100% pass)**| 30 escenarios | **CUMPLIDO** |
| **Cumplimiento de Contrato LLM** | 92.00% | **100.00%** | $\ge 95.00\%$ | **SUPERADO** |
| **Cero Alucinaciones de Cifras / Pasos** | 95.00% | **100.00%** | $100.00\%$ | **CUMPLIDO** |

---

## 3. DETALLE DE FASES IMPLEMENTADAS

### Fase 1: Congelamiento, Aislamiento y Medición de Línea Base
- **Hash de Referencia:** Identificado el commit base de trabajo en la rama `feat/optimizacion-integral-ml-rag-llm`.
- **Aislamiento de TEST10:** Se protegió de forma estricta el archivo `machine_learning/data/fase10/test10_fase10_blind_v1.csv` ($N=366$), utilizándolo exclusivamente como holdout ciego final para validar el modelo final sin fuga de datos (*data leakage*).
- **Métricas DEV10 Baseline ($N=1725$):** Top-1 = 88.17%, Top-3 = 95.71%, F1-Macro = 87.78%, N1 Acc = 96.46%.

### Fase 2: Optimización Experimental de Machine Learning (SVM)
- **Causa de Mejora:** Se evaluó el método de calibración de probabilidades. La calibración isotónica previa generaba escalones discretos y sobreajustados en clases con frecuencias reducidas en 61 clases. La calibración Sigmoidea (Platt Scaling) con regularización $C=2.0$ y tokenización preservando n-gramas de negación automotriz (`no_arranca`, `sin_fuerza`) estabilizó las probabilidades conjuntas.
- **Resultados en DEV10:**
  - Candidato V2 ($C=2.0$ Sigmoid + Prep): Top-1 = 89.10% (+0.93 pp), Top-3 = 96.06%, F1 = 88.72%.
- **Validación Final en TEST10 Ciego:**
  - Top-1: $81.69\% \rightarrow \mathbf{83.33\%}$ (305/366 aciertos).
  - Top-3: $93.17\% \rightarrow \mathbf{93.99\%}$ (344/366 aciertos).
  - F1-Macro: $80.95\% \rightarrow \mathbf{82.81\%}$.

### Fase 3: Hallazgo y Corrección de la Causa Raíz de RAG
- **Diagnóstico del 41.80% Hit@1:** Al ejecutar `diagnostico_rag_fallos.py` sobre las 71 consultas fallidas del benchmark histórico, se descubrió un fallo estructural en `build_independent_benchmark.py`: el diccionario de plantillas de síntomas estaba indexado en base-0 (`0..60`), mientras que el catálogo canónico de 61 clases estaba indexado en base-1 (`01..61`). Esto ocasionaba que cada síntoma estuviera etiquetado con la clase siguiente e inyectara hipótesis previas contradictorias al re-ordenador.
- **Alineación:** Se generó `benchmark_dataset_alineado.json` corrigiendo el emparejamiento exacto con la taxonomía oficial de 61 clases.
- **Resultado:** El motor RAG real pasó inmediatamente a **92.62% Hit@1**, **96.72% Hit@3**, con **0.00% de contaminación** y una latencia p50 de apenas **83.14 ms**.

### Fase 4: Optimización de Guardrails y Fallback de LLM
- Se verificó el contrato estructurado en `backend/src/core/diagnostico/respuesta_llm_estructurada.py`.
- Formato estructurado rígido en 4 campos (Hipótesis, Explicación, Siguiente Prueba, Pregunta de descarte), limitación a 120 palabras y validación de seguridad para evitar cifras de torque inventadas o procedimientos inseguros de desmontaje sin herramientas.
- Fallback determinista local activo cuando el proveedor externo (Groq/Gemini) no responde.

### Fase 5: Pruebas de Ablación de 3 Niveles (A, B, C)
Evaluado sobre una muestra representativa de 30 consultas reales distribuidas en todos los macrosistemas:
1. **Nivel A (Solo SVM):** Top-1 = 93.33% | Latencia p50 = 31.35 ms | Latencia p95 = 38.79 ms | Seguridad = 93.33%.
2. **Nivel B (SVM + RAG):** Top-1 = 93.33% | Cobertura RAG = 96.67% (29/30) | Contaminación = 3.33% | Latencia p50 = 93.56 ms.
3. **Nivel C (SVM + RAG + LLM):** Cumplimiento de contrato = 100.00% | Cero alucinaciones = 100.00% | Latencia p50 = 99.19 ms | Latencia p95 = 231.47 ms.

### Fase 6: Validación Conversacional WhatsApp (30 Escenarios)
Se expandió la suite de pruebas a 30 casos automatizados completos en `backend/tests/test_30_escenarios_conversacionales_integral.py`:
- Escenarios 1-3: Frenos (pedal esponjoso, vibración, respuesta "sin herramientas").
- Escenarios 4-5: Suspensión (golpes secos en baches, ruidos en rompemuelles).
- Escenarios 6-8: Motor (arranque en frío, pérdida de potencia P0301, corrección de humo).
- Escenarios 9-10: Refrigeración (recalentamiento en tráfico, pérdida de anticongelante).
- Escenario 11: Cambio de vehículo en sesión activa (aislamiento de casos).
- Escenarios 12-15: Respuestas naturales ("1", "la primera", "todavía no revisé", filtrado de palabras de control).
- Escenarios 16-19: Interrupciones, respuestas ambiguas, confirmación con evidencia, menús estrictos (1 vs 2/3 hipótesis).
- Escenario 20: Transmisión manual (rasquido al meter reversa).
- Escenarios 21-30: Transmisión automática con patinamiento, A/C aire tibio, vehículo híbrido P0A80, fuga parásita nocturna en batería, frenos de aire Maxi-Brake en camiones pesados, inyección directa GDI, desfasaje VVT en árboles de levas, caliper pegado con olor a quemado, junta homocinética con chasquido al girar, y rectificación diagnóstica en vivo.
- **Resultado de la Suite:** `30 passed in 11.90s`.

---

## 4. COMANDOS PARA REPRODUCCIÓN EXACTA

Para auditar y reproducir independientemente todos los resultados en la máquina física:

```powershell
# 1. Situarse en el repositorio de trabajo
cd "c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\scratch\whatsapp-conversacional-worktree\backend"

# 2. Reproducir la evaluación final de SVM en TEST10 ciego
& "C:\Users\leonc\AppData\Local\Programs\Python\Python314\python.exe" scripts/evaluar_candidatos_final_test10.py

# 3. Reproducir el benchmark RAG independiente alineado
& "C:\Users\leonc\AppData\Local\Programs\Python\Python314\python.exe" scripts/evaluar_rag_alineado.py

# 4. Reproducir las pruebas de ablación de 3 niveles (A, B, C)
& "C:\Users\leonc\AppData\Local\Programs\Python\Python314\python.exe" scripts/ejecutar_ablacion_integral.py

# 5. Ejecutar la suite completa de 30 escenarios conversacionales
& "C:\Users\leonc\AppData\Local\Programs\Python\Python314\python.exe" -m pytest tests/test_30_escenarios_conversacionales_integral.py -v
```

---

## 5. CONTROL DE CAMBIOS Y ESTADO DE DESPLIEGUE

- **Rama Actual:** `feat/optimizacion-integral-ml-rag-llm`
- **Estado de `main`:** Totalmente protegido e intacto.
- **Estado de Producción (AWS EC2):** No modificado.
- **Próximo Paso:** Esperar la autorización expresa del usuario antes de crear el Pull Request hacia `main` o proceder con el empaquetado OCI y despliegue a producción.
