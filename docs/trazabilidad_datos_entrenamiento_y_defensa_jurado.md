# Trazabilidad de datos de CarBot y respuesta para el jurado

Fecha de actualización: 15 de agosto de 2026

## Respuesta breve recomendada

> El clasificador se entrenó con 2,861 registros base sometidos a limpieza y
> agrupación por familias de síntomas. Después se evaluó una fuente académica de
> Zenodo con DOI y licencia CC BY 4.0. De 99 casos completos se admitieron 33 que
> tenían traducción completa, correspondencia no ambigua con la taxonomía y
> consistencia de código. Los datos externos participaron solo en entrenamiento;
> el holdout de 570 casos se separó previamente del dataset base. La comparación
> mejoró el F1 macro de 95.49 % a 95.95 %, por lo que se conservó el modelo
> enriquecido. Esto no reemplaza la validación externa con reparaciones reales.

## Datos verificables vigentes

- Dataset base: 2,861 muestras.
- Clases canónicas: 48.
- Sistemas automotrices: 14.
- Familias de síntomas: 1,541.
- Fuente Zenodo: 99 casos completos.
- Casos externos admitidos: 33.
- Descartes: 53 sin mapeo, 12 ambiguos y 1 duplicado.
- Dataset final de entrenamiento: 2,894 registros.
- Holdout sin datos externos: 570 registros.
- F1 macro del modelo seleccionado: 95.95 %.
- Modelo aprobado para diagnóstico autónomo: no.

El reporte de limpieza original termina en 2,751 filas. Las 110 filas añadidas
después conservan síntoma y falla, pero tienen pendientes los campos de código,
sistema y severidad. Esta limitación debe declararse y corregirse antes de cerrar
el linaje taxonómico del dataset.

## Procedencia externa

- Nombre: *Automotive Fault Diagnosis Dataset*.
- DOI: https://doi.org/10.5281/zenodo.15626055
- Licencia: CC BY 4.0.
- MD5: `cb44431ef6b32f6ea9cf00dbe35f020c`.
- Preparación: `machine_learning/training/preparar_dataset_externo_entrenamiento.py`.
- Dataset auditado: `machine_learning/data/dataset_externo_auditado.csv`.
- Reporte: `machine_learning/data/reporte_dataset_externo.json`.

Los 196 síntomas traducidos individualmente continúan como bandeja histórica de
candidatos. No se entrenó con las filas aplanadas porque podían perder la
relación entre síntomas y producir etiquetas contradictorias. La integración
vigente usa 33 casos completos, conserva juntos los síntomas relacionados y los
marca como `AUDITADO_TAXONOMIA_NO_CASO_TALLER`.

## Separación de conjuntos

1. El holdout se separa únicamente del dataset base.
2. La selección de algoritmo y validación cruzada usan el entrenamiento base.
3. Se compara un ajuste base contra otro enriquecido sobre el mismo holdout.
4. El externo se conserva solo si mejora F1 macro y respeta las barreras de
   exactitud, calibración y variación por clase.
5. Después de seleccionar, el artefacto final se ajusta con base más externo.

Esto evita presentar como mejora el simple hecho de evaluar al modelo con casos
que ya vio.

## Qué no se debe afirmar

- No decir que los datos Zenodo son casos del taller o casos peruanos.
- No decir que la auditoría de taxonomía equivale a confirmación mecánica.
- No llamar reparación confirmada a una queja de NHTSA.
- No llamar validación externa a pruebas sintéticas.
- No decir que el modelo está listo para diagnóstico autónomo.

## Validación externa real pendiente

Un caso real debe registrar el síntoma antes de mostrar la predicción, confirmar
la falla mediante inspección, escáner o medición, conservar evidencia privada y
permanecer fuera del entrenamiento usado para evaluarlo. La plantilla está en
`machine_learning/data/plantilla_evaluacion_externa.csv` y la evaluación se
ejecuta con `machine_learning/training/evaluar_modelo_externo.py`.

## Evidencias para la defensa

- `machine_learning/data/FUENTES_ENTRENAMIENTO.md`.
- `machine_learning/data/reporte_calidad_dataset.json`.
- `machine_learning/data/reporte_dataset_externo.json`.
- `machine_learning/models/metricas_modelo.json`.
- `machine_learning/models/metricas_externas.json`.
- `docs/graficas/matriz_confusion_ml.png`.
