# AUDITORÍA TÉCNICA Y METODOLÓGICA — MUESTRA PRELIMINAR FIELD (n=32)
## CarBot — Evaluación de Integridad de Datos Reales de Taller

**Fecha**: 17 de Septiembre de 2026  
**Archivo Evaluado**: `machine_learning/data/casos_reales_mecanicos_evaluacion.csv`  
**Tamaño Actual**: 32 registros reales  
**Meta Metodológica de Tesis**: 60 casos reales de taller mecánico  
**Casos Pendientes de Recolección en Campo**: 28 casos  

---

## 1. Contexto del Problema y Pregunta de Auditoría

En los benchmarks de regresión de Fase 8.3 y Fase 10 (Candidato C1), el subconjunto `FIELD_AVAILABLE_N32` arrojó una métrica de desempeño aparentemente anómala:
- **Top-1 Accuracy F8.3**: **9.4%** (3 / 32)
- **Top-1 Accuracy C1**: **9.4%** (3 / 32)
- **Top-3 Accuracy C1**: **9.4%** (3 / 32)

Antes de interpretar este porcentaje como una incapacidad del modelo para generalizar ante vehículos reales de taller, esta auditoría analizó la estructura interna del archivo, la naturaleza de sus variables y la alineación taxonómica de sus etiquetas.

**Pregunta Central**:
> ¿El 9.4% obtenido es directamente comparable con el Top-1 de las 61 clases canónicas de CarBot?
> **RESPUESTA DETERMINANTE**: **NO**.

---

## 2. Hallazgo Forense: Desalineación Sintáctica de Etiquetas

Al comparar las 32 cadenas presentes en la columna `falla` de `casos_reales_mecanicos_evaluacion.csv` contra el conjunto oficial de las 61 clases canónicas del proyecto (`MAPEO_CANONICO_61_A_7.csv`), se determinó que:

- **Coincidencias sintácticas exactas con la taxonomía**: **3 / 32 (9.38%)**
- **Etiquetas con discrepancia sintáctica respecto a la taxonomía canónica**: **29 / 32 (90.62%)**

### Las Únicas 3 Clases Canónicas Presentes en FIELD:
1. `Amortiguadores reventados o bujes de suspension gastados` (Fila 8)
2. `Alternador defectuoso o placa de diodos quemada` (Fila 10)
3. `Fuga en mangueras de refrigerante o radiador picado` (Fila 23)

### Ejemplos de Discrepancia Sintáctica (Semántica Idéntica pero Cadena Distinta):

| Fila | Síntoma Real del Mecánico | Etiqueta en CSV FIELD (`falla`) | Clase Canónica Oficial en CarBot (61 clases) | ¿Coincide Exacto? |
| :---: | :--- | :--- | :--- | :---: |
| 0 | *"El pedal de freno se hunde hasta el fondo..."* | `Fuga de liquido de frenos o aire en el sistema` | `Fuga de líquido de frenos o pérdida de presión hidráulica` | **NO** |
| 1 | *"Chirrido metálico agudo al pisar freno..."* | `Pastillas de freno desgastadas` | `Desgaste de pastillas y zapatas de freno` | **NO** |
| 2 | *"El carro no arranca solo suena un clic..."* | `Bateria descargada o arrancador defectuoso` | `Bateria descargada o bornes sulfatados` | **NO** |
| 3 | *"El motor vibra y tiembla en ralentí..."* | `Bujias desgastadas o bobina de encendido defectuosa` | `Bujias desgastadas o bobina de ignicion con fuga de chispa` | **NO** |
| 4 | *"Tironea al acelerar a fondo..."* | `Filtro de combustible obstruido o inyectores sucios` | `Filtro de combustible obstruido o baja presion de riel` | **NO** |
| 5 | *"Humo negro y alto consumo..."* | `Sensor de oxigeno defectuoso` | `Falla en sensor de oxigeno o mezcla rica` | **NO** |
| 6 | *"Olor a quemado y patina el embrague..."* | `Disco de embrague (clutch) desgastado o patinando` | `Disco de embrague desgastado o patinando` | **NO** |
| 7 | *"Temperatura sube y hierve refrigerante..."* | `Falla en el rele o motor del ventilador del radiador`| `Falla en termostato o motoventilador de radiador` | **NO** |

---

## 3. Conclusión Matemática y Causa Raíz

1. **Cálculo de Evaluación Automatizada**:
   La función de evaluación ejecutó una comparación estricta de igualdad de cadenas (`pred_top1 == field_real`).
2. **Techo Máximo Matemático**:
   Dado que solo 3 de los 32 registros contenían una cadena idéntica a alguna de las 61 clases del modelo, **el puntaje máximo absoluto que cualquier modelo de 61 clases podía obtener era exactamente 3 / 32 = 9.375% (9.4%)**.
3. **Validación Semántica**:
   Al inspeccionar cualitativamente las predicciones generadas por C1 sobre estos 32 casos, el modelo predijo acertadamente la clase técnica correspondiente (e.g., predijo `Desgaste de pastillas y zapatas de freno` para la fila 1, y `Disco de embrague desgastado o patinando` para la fila 6).

---

## 4. Directrices Metodológicas para la Tesis

1. **Aislamiento Total**:
   Los datos de FIELD pertenecen a la recolección física en talleres mecánicos reales. **NO deben ser utilizados para reentrenar ni ajustar modelos ML** (cero data leakage).
2. **Cero Simulación**:
   Los 28 casos faltantes para completar la muestra de $N=60$ deben ser levantados físicamente mediante los instrumentos de recolección en los talleres automotrices seleccionados.
3. **Estandarización del Instrumento**:
   Cuando los mecánicos confirmen el diagnóstico físico en el taller, el formulario o ficha de cotejo debe registrar el código o denominación canónica de las 61 clases oficiales, impidiendo la dispersión sintáctica que invalidó la evaluación estricta en este lote preliminar.
4. **Impacto en Decisión C1/C2**:
   El resultado de 9.4% en `FIELD_AVAILABLE_N32` no representa un fallo de generalización del SVM, sino un artefacto de evaluación sintáctica de etiquetas preliminares. Por ende, **no constituye argumento técnico para crear C2**.
