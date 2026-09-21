# Entrenamiento experimental con fuentes auditadas

Fecha local: 4 de septiembre de 2026 (Lima).

## Resultado y alcance

Se entrenaron y compararon cuatro configuraciones sin sustituir los artefactos
operativos ni modificar PostgreSQL, WhatsApp o el corpus RAG. Se conservaron los
2 861 registros base y los 33 casos académicos de Zenodo previamente admitidos:
**no se incorporaron nuevos casos externos respecto al dataset preexistente**.
El aporte de esta ejecución es la comparación controlada, la representación
adicional por caracteres y una calibración agrupada más estricta.

| Configuración | F1 macro medio, validación cruzada de 4 particiones |
| --- | ---: |
| Palabras, base | 96,47 % |
| Palabras, base + Zenodo | 96,77 % |
| Palabras y caracteres, base | 96,93 % |
| Palabras y caracteres, base + Zenodo | 97,07 % |

La última configuración se seleccionó por validación cruzada, no usando la
reserva final para elegir. Evaluación posterior sobre 570 registros reservados:

| Métrica | Referencia reentrenada, solo base | Candidato seleccionado |
| --- | ---: | ---: |
| Exactitud | 97,37 % | 98,07 % |
| F1 macro | 96,30 % | 96,90 % |
| Error de calibración ECE (menor es mejor) | 0,1288 | 0,1068 |

La referencia es una comparación nueva bajo el mismo procedimiento, **no una
evaluación del modelo operativo**. Este último ya pudo ver esos registros al
entrenarse. La reserva también fue utilizada en experimentos anteriores: no
debe presentarse como evidencia externa nueva ni como resultado pre/post de tesis.

## Por qué no se publicó

- ECE 0,1068, superior al límite 0,10.
- F1 de 0,20 en `Bomba de gasolina quemada o con baja presion` (9 ejemplos).
- Algunas clases solo tienen 4 ejemplos reservados; el mínimo requerido es 5.
- Falta evaluación con nuevos casos confirmados por mecánicos, con procedencia
  documentada y separados del entrenamiento y de la selección del modelo.
- El candidato es un pipeline que recibe texto; el backend operativo usa dos
  artefactos separados. No debe copiarse sobre el modelo operativo: requiere
  adaptación, pruebas de integración y control de versiones antes de publicarlo.

Un promedio alto no demuestra seguridad diagnóstica. Las predicciones siguen
siendo hipótesis sujetas a revisión física, no fallas confirmadas.

## Admisión de fuentes

- [Zenodo](https://zenodo.org/records/15626055): CC BY 4.0; fuente original con
  checksum verificado. Se usaron los 33 casos con equivalencia taxonómica y
  traducción ya auditadas. No representan reparaciones confirmadas en el taller local.
- [NHTSA](https://www.nhtsa.gov/nhtsa-datasets-and-apis): las quejas reales no
  prueban la causa. No se descargaron ni etiquetaron automáticamente para entrenar.
- [Kaggle Car Diagnostic Agent](https://www.kaggle.com/datasets/samsonmagana/ml-for-car-diagnostic-agent-ai-assistant):
  licencia publicada como `Unknown`; procedencia no corroborada. Excluido.
- [UCI APS Scania](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks):
  datos numéricos, incompatibles con la entrada textual actual. Excluido.
- [Estudio textual de Scania](https://link.springer.com/article/10.1007/s10994-023-06398-7):
  dataset no público. Referencia académica, no fuente de entrenamiento.
- GemaCar: permanece fuera de este experimento por falta de licencia abierta
  declarada y validación mecánica. No se modificaron derivados anteriores.

## Controles y reproducción

Desde `machine_learning/`:

```powershell
../.venv/Scripts/python.exe -m training.entrenar_fuentes_auditadas
```

Cada ejecución crea una carpeta nueva bajo `models/experimentos/`; rechaza
salidas existentes o externas. Conserva el pipeline completo, las particiones,
los externos admitidos, métricas por clase y hashes de entradas y artefactos.
El vocabulario se aprende dentro de cada partición de calibración. Se excluyen
externos que coincidan con familias normalizadas del dataset base y duplicados
ambiguos. La normalización no garantiza detectar toda paráfrasis semántica.

Ejecución final: `fuentes_auditadas_20260905T044122188822Z` (identificador UTC).
Su `reporte.json` contiene los bloqueos explícitos de producción. La primera
ejecución exploratoria se conserva, sin sobrescribirla.

Validaciones: Ruff sin errores; 28 pruebas aprobadas de entrenamiento, evaluación
externa, intención y jerga. Verificación SHA-256: modelo, vectorizador y métricas
operativos intactos. No se enviaron mensajes ni se hicieron pruebas de WhatsApp real.

Siguiente prioridad: reunir casos confirmados de bomba/presión de combustible y
otras clases débiles, revisar su mapeo y evaluar en un conjunto independiente.
No mezclar las fichas reservadas para medir el impacto de la tesis con el entrenamiento.
