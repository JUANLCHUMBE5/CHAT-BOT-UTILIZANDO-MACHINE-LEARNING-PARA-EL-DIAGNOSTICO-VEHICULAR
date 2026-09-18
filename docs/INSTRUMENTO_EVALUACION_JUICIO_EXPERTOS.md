# Instrumento de Validación por Juicio de Expertos — Calidad Diagnóstica CarBot

Este documento constituye el **Instrumento Formal de Juicio de Expertos** para la evaluación cuantitativa y cualitativa del sistema **CarBot**, diseñado para su inclusión en la memoria y anexos metodológicos de la tesis universitaria.

---

## 1. Ficha Técnica del Instrumento

| Elemento Metodológico | Descripción |
| :--- | :--- |
| **Título del Instrumento** | Ficha de Evaluación de la Calidad Diagnóstica y Respaldo Técnico Vehicular |
| **Objetivo** | Evaluar la pertinencia, precisión, utilidad metrológica y ausencia de alucinaciones en los diagnósticos generados por el asistente CarBot (Linear SVM + RAG + LLM). |
| **Población de Jueces** | Ingenieros Mecánicos / Mecatrónicos y Mecánicos Jefes de Taller automotriz con experiencia profesional demostrable $\ge 5$ años en diagnóstico de taller. |
| **Tipo de Aplicación** | Rúbrica analítica multidimensional con escala de Likert de 5 niveles. |
| **Dimensiones Evaluadas** | 4 dimensiones clave: $D_1$ (Correctitud Técnica), $D_2$ (Relevancia Metrológica), $D_3$ (Diagnóstico Diferencial) y $D_4$ (Delimitación Epistémica y Anti-Alucinación). |
| **Criterio de Validación** | Coeficiente de Validez de Contenido ($V$ de Aiken) con umbral mínimo de aceptación $V \ge 0.80$. |

---

## 2. Operacionalización de Dimensiones y Criterios de Evaluación

Cada caso generado por el sistema se evalúa en cuatro dimensiones ponderadas ($0\% - 100\%$ o Escala 1 a 5):

### Dimensión 1 ($D_1$): Correctitud Técnica y Coherencia Diagnóstica
- **Pregunta guía**: *¿La hipótesis diagnóstica principal (Top 1) identifica con exactitud la causa física de la avería vehicular y respeta la autoridad de los códigos DTC ingresados?*
- **Criterios específicos**:
  - **Identificación de Causa Raíz (50 pts)**: La hipótesis principal emitida coincide con la falla real comprobada en taller.
  - **Autoridad Instrumental DTC (30 pts)**: Si el caso contiene un código OBD-II oficial (ej. `P0301`, `P0841`), la respuesta prioriza el componente electrónico directamente vinculado.
  - **Estructura Técnica Canónica (20 pts)**: La respuesta respeta estrictamente el formato de taller en tres bloques: 
    1. *Posible avería identificada*.
    2. *Procedimiento de verificación técnica*.
    3. *Nivel de gravedad y tiempo estimado de intervención*.

### Dimensión 2 ($D_2$): Relevancia del Procedimiento Técnico y Metrología
- **Pregunta guía**: *¿El procedimiento recuperado del catálogo OEM es específico, metrológicamente cuantificable y adecuado a la naturaleza de la avería?*
- **Criterios específicos**:
  - **Relevancia del Manual OEM (40 pts)**: El procedimiento técnico recuperado por el motor RAG corresponde a la avería exacta y no a componentes ajenos.
  - **Regla Metodológica de No-Escaneo para Averías Mecánicas (40 pts)**: 
    - Para averías mecánicas puras sin gestión electrónica (desbalanceo de ruedas, discos alabeados, desgaste de pastillas, holguras de suspensión, embrague patinando), el sistema **NUNCA debe sugerir escáner OBD-II**.
    - La primera prueba sugerida debe ser siempre **física o metrológica** (reloj comparador para alabeo $\le 0.04$ mm, equilibradora dinámica $\le 5$ g, palpador de holgura $\le 1.5$ mm, prueba de calado en 4ta marcha a 2500 RPM).
  - **Pasos Estructurados de Inspección (20 pts)**: Pasos numerados secuenciales y lógicos previos al desmontaje.

### Dimensión 3 ($D_3$): Sustento en Evidencia y Diagnóstico Diferencial
- **Pregunta guía**: *¿El sistema ofrece alternativas diagnósticas transparentes para que el mecánico compare probabilidades y descarte causas secundarias?*
- **Criterios específicos**:
  - **Transparencia Probabilística (40 pts)**: Presentación visible de las hipótesis competidoras (Top 1, Top 2 y Top 3 de probabilidades ML).
  - **Criterio de Descarte Diferencial (40 pts)**: Inclusión explícita de instrucciones para discriminar entre la hipótesis principal y la alternativa (ej. cómo distinguir alabeo de discos vs desbalanceo de neumáticos).
  - **Pruebas Previas al Reemplazo (20 pts)**: Énfasis en verificar antes de comprar o cambiar repuestos.

### Dimensión 4 ($D_4$): Ausencia de Alucinaciones y Delimitación Epistémica
- **Pregunta guía**: *¿El modelo delimita con honestidad el alcance de sus predicciones estadísticas sin inventar tolerancias ni certezas absolutas?*
- **Criterios específicos**:
  - **Reconocimiento Epistémico (40 pts)**: El sistema declara explícitamente que la salida de Machine Learning es una *hipótesis probabilística orientativa* que debe ser confirmada físicamente por el profesional en taller.
  - **Cero Certezas Absolutas Infundadas (30 pts)**: Ausencia total de afirmaciones temerarias como *"falla 100% segura"* o *"cambie el repuesto de inmediato sin revisar"*.
  - **Groundedness Documental RAG (30 pts)**: Todos los valores de torque, voltaje y tolerancias metrológicas provienen textualmente de los manuales OEM indexados, sin datos inventados por el LLM.

---

## 3. Escala Likert de Evaluación y Conversión Matemática

Para la calificación por parte de los jueces expertos, se emplea la siguiente escala ordinal:

| Nivel Likert | Descripción Cualitativa | Equivalencia Porcentual | Puntuación Asignada |
| :---: | :--- | :---: | :---: |
| **5** | **Excelente**: Cumple rigurosamente el estándar técnico de taller, sin fallas ni alucinaciones. | $90\% - 100\%$ | 5 puntos |
| **4** | **Bueno**: Diagnóstico y procedimiento correctos con omisiones menores de estilo. | $75\% - 89\%$ | 4 puntos |
| **3** | **Aceptable**: Diagnóstico orientativo correcto, pero requiere precisión metrológica. | $60\% - 74\%$ | 3 puntos |
| **2** | **Deficiente**: Procedimiento poco aplicable o confusión parcial entre sistemas. | $40\% - 59\%$ | 2 puntos |
| **1** | **Muy Deficiente**: Diagnóstico incorrecto, alucinación técnica o violación de reglas. | $< 40\%$ | 1 punto |

### Puntuación Global de Calidad por Caso ($S_i$):
$$S_i = \frac{D_1 + D_2 + D_3 + D_4}{4}$$

---

## 4. Fórmula de Validez de Contenido ($V$ de Aiken)

Para cuantificar el grado de concordancia y validez de contenido entre los jueces expertos sobre la pertinencia de cada criterio evaluado:

$$V = \frac{S}{n(c - 1)}$$

Donde:
- $S = \sum (r_i - l)$: Suma de las diferencias entre la calificación asignada por cada juez ($r_i$) y la calificación más baja de la escala ($l = 1$).
- $n$: Número total de jueces expertos participantes (mínimo 3 a 5 jueces independientes).
- $c$: Número total de niveles en la escala de calificación ($c = 5$).

> [!NOTE]
> Valores de $V \ge 0.80$ indican una validez de contenido óptima y estadísticamente significativa ($\alpha = 0.05$).

---

## 5. Matriz de Juicio de Expertos (Muestra de 20 Casos Representativos)

| Caso ID | Consulta Vehicular Resumida | $D_1$ (1-5) | $D_2$ (1-5) | $D_3$ (1-5) | $D_4$ (1-5) | Global (%) | Observaciones del Experto |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **E2E_01** | Toyota Yaris 2018 — Misfire P0301 | | | | | | |
| **E2E_02** | Nissan Versa 2019 — Ralentí inestable IAC | | | | | | |
| **E2E_03** | Kia Rio 2017 — Culata soplada / burbujas | | | | | | |
| **E2E_04** | Toyota Corolla — Alabeo de discos (Mecánica) | | | | | | |
| **E2E_05** | Hyundai Accent — Pastillas de freno calientes | | | | | | |
| **E2E_06** | Nissan Sentra — Pedal esponjoso / purga | | | | | | |
| **E2E_07** | Chevrolet Sail — Embrague patinando (Mecánica) | | | | | | |
| **E2E_08** | Nissan Qashqai — Transmisión CVT DTC P0841 | | | | | | |
| **E2E_09** | Fiat Siena — Caja robotizada Dualogic | | | | | | |
| **E2E_10** | Toyota Yaris — Amortiguadores reventados | | | | | | |
| **E2E_11** | Kia Rio — Juntas homocinéticas / trac-trac | | | | | | |
| **E2E_12** | Hyundai Elantra — Balanceo de llantas a 100 | | | | | | |
| **E2E_13** | Chevrolet Cruze — Alternador / 11.7V en marcha | | | | | | |
| **E2E_14** | Suzuki Swift — Batería descargada / chasquido | | | | | | |
| **E2E_15** | Nissan Tiida — Compresor A/C no acopla | | | | | | |
| **E2E_16** | Camión Volvo — Freno de aire neumático | | | | | | |
| **E2E_17** | Toyota Etios — Bomba de combustible zumbido | | | | | | |
| **E2E_18** | Hyundai Elantra — Catalizador DTC P0420 | | | | | | |
| **E2E_19** | Toyota Corolla — Distribución salto de punto | | | | | | |
| **E2E_20** | Kia Rio — Cremallera de dirección holgura | | | | | | |

---

## 6. Declaración de Conformidad del Juez Experto

Yo, ____________________________________________________, identificado con DNI/CIP N° ___________________, de profesión ___________________________________, con ______ años de ejercicio profesional en el área automotriz, certifico haber evaluado las respuestas emitidas por el sistema CarBot bajo los criterios técnicos y metrológicos descritos en este instrumento.

**Fecha**: _____ / _____ / 2026  
**Firma del Evaluador Experto**: ___________________________
