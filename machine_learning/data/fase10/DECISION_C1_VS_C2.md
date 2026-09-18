# DOCUMENTO TÉCNICO DE DECISIÓN EXPERIMENTAL — C1 vs C2
## Evaluación Metodológica de Candidato de Fase 10 — CarBot

**Fecha**: 17 de Septiembre de 2026  
**Candidato Evaluado**: `F10-C1` (Clasificador 61 Fallas congelado + `modelo_sistema_c1_macrofix.pkl`)  
**Estado de Decisión**: `RECOMENDAR_CONGELAR_C1`  

---

## 1. Declaración de Decisión

Tras el análisis exhaustivo, forense y cuantitativo de los 1,725 registros de DEV10, los 144 errores en datos sintéticos no vistos, la matriz de confusión 61x61, la taxonomía de errores por nivel (L1/L2/L3), los casos contrastivos y los benchmarks históricos independientes, **se concluye formalmente**:

> **DECISIÓN: RUTA A — RECOMENDAR CONGELAR C1**  
> No existe evidencia técnica suficiente ni justificación metodológica que respalde la creación de un modelo intermedio C2 antes de la evaluación única e independiente sobre TEST10.
> 
> Los errores remanentes en C1 corresponden predominantemente a **ambigüedad clínica deliberada de nivel L1 (40.28%)**, **hipótesis diagnósticas legítimas recuperadas en Top-3 (34.72%)**, y **acoples mecánicos/eléctricos estrechos**, los cuales están concebidos por diseño para ser discriminados por el auto-interrogador conversacional de CarBot y no mediante sobreajuste del clasificador base.

---

## 2. Matriz de Evidencia Científica y Justificación

### A. Naturaleza de los Errores Sintéticos (Budget de Errores n=144)
En el conjunto sintético no visto (n=488, 344 aciertos, 144 errores):
- **75.00% de los errores (108 / 144)** corresponden a dos categorías benignas:
  1. `AMBIGUO_L1` (58 casos, 40.28%): Descripciones deliberadamente imprecisas (e.g. *"mi carro tiembla en ralentí"*) donde forzar una predicción Top-1 específica sin diálogo previo violaría los principios de la medicina vehicular.
  2. `TOP3_COMPATIBLE` (50 casos, 34.72%): Casos de niveles L2 y L3 donde la falla real está presente en el Top-3 del modelo con alta plausibilidad física.
- **En total, 92 de los 144 errores (63.89%)** tienen la clase correcta dentro del Top-3.
- La precisión Top-3 en datos sintéticos no vistos alcanza un contundente **89.34%** (y **95.63% en L2**, **94.54% en L3**).

### B. Ausencia de Patrones de Falla Sistémicos o Concentrados
- En los datos sintéticos no vistos, **ningún par de confusión específico supera una frecuencia de 3 casos** en todo el split de DEV10.
- No existen "agujeros negros" donde una clase absorba masivamente a otra. Los errores son dispersos y están limitados a componentes adyacentes (e.g. consumo de aceite por anillos vs pérdida de compresión por anillos gastados; empaque de culata vs fuga en manguera de radiador).
- En casos contrastivos (n=257), C1 redujo los errores hacia la clase trampa de 20.2% a solo **14.0%**, alcanzando un **94.55% en Top-3**.

### C. Superioridad Demostrada de C1 sobre F8.3 en Unseen Data
- En el subconjunto sintético no visto por ambos modelos (n=488):
  - **Top-1**: C1 (70.49%) supera a F8.3 (59.63%) por **+10.86 puntos porcentuales**.
  - **Top-3**: C1 (89.34%) supera a F8.3 (79.51%) por **+9.84 puntos porcentuales**.
  - **Macro F1**: C1 (70.14%) supera a F8.3 (59.50%) por **+10.65 puntos porcentuales**.
- Al analizar las 61 clases individuales en datos no vistos:
  - C1 **mejora claramente en 37 clases** (con ganancias de hasta +47.5% en F1).
  - C1 empeora de forma relevante ($\Delta \text{F1} \le -15\%$ con $n \ge 8$) en **solo 3 clases** (GDI, frenos camiones, limpiaparabrisas), en las cuales el Top-3 mantiene recuperada la clase real.

### D. Consistencia en Benchmarks Históricos Independientes
El candidato C1 supera a la línea base F8.3 en todas las pruebas históricas preexistentes:
- **TEST-100**: 86.0% vs 79.0% (**+7.0 pp**)
- **DEV-60**: 90.0% vs 85.0% (**+5.0 pp**)
- **G2 (Jerga Mecánica)**: 78.0% vs 72.0% (**+6.0 pp**)
- **G1 (Estrés Multimarca)**: 90.0% vs 90.0% (mantenido)

### E. Macro-Sistema Completamente Saneado
Con la incorporación del modelo `modelo_sistema_c1_macrofix.pkl`:
- La exactitud de macro-sistema subió de 35.94% a **96.46%** en DEV10 (Macro F1 = **94.90%**).
- La confusión de macro-sistema ya no interfiere en el enrutamiento primario del diagnóstico.

---

## 3. Análisis de Riesgo Metodológico: ¿Por qué NO Crear C2?

1. **Riesgo de Sobreajuste a DEV10**:
   Diseñar un "C2" modificando hiperparámetros o inyectando datos adicionales para arreglar los 8 errores de L3 o las 3 clases degradadas implicaría ajustar el modelo a las particularidades de DEV10, destruyendo su condición de conjunto de validación imparcial.
2. **Riesgo de Olvido Catastrófico en las 37 Clases Ganadoras**:
   Cualquier rebalanceo de pesos o ajuste fino arriesgaría perjudicar el sobresaliente avance de +10.8% obtenido en las 37 clases que mejoraron sustancialmente.
3. **Rol de la Capa Conversacional**:
   CarBot no es un clasificador aislado de un solo tiro; es un sistema dialógico. Los errores L1 con confianza baja (media 0.6018) están diseñados para activar el auto-interrogador y formular preguntas de descarte al mecánico, elevando la precisión final hacia los niveles de Top-3 (89.34% - 95.63%).
4. **Respeto a la Integridad de TEST10**:
   El protocolo experimental exige evaluar el verdadero potencial del corpus Fase 10 de manera limpia sobre TEST10 ciego.

---

## 4. Hoja de Ruta Inmediata

1. **Mantener Congelado C1**: Clasificador de 61 fallas (`modelo_diagnostico_c1.pkl`), vectorizador (`vectorizador_c1.pkl`) y clasificador de macro-sistemas saneado (`modelo_sistema_c1_macrofix.pkl`).
2. **Mantener TEST10 Bloqueado**: No abrir ni evaluar TEST10 hasta la autorización explícita de la Etapa 4.
3. **Deuda Técnica Registrada**: La optimización de orquestación para casos de carga con A/C (`ORQUESTADOR_AC_CONTEXT_SWITCH`) se abordará en una etapa de backend posterior, sin alterar el modelo ML.
