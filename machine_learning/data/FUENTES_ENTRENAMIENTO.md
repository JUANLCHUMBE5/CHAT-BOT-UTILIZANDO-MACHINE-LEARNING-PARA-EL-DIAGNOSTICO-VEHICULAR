# Fuentes de entrenamiento y reglas de admision

## Dataset base del proyecto

- Archivo: `dataset_sintomas_limpio.csv`
- Registros: 2861
- Uso: entrenamiento principal y evaluacion agrupada por familias de sintomas.

## Fuente academica externa admitida

- Publicacion: *Automotive Fault Diagnosis Dataset*
- DOI: https://doi.org/10.5281/zenodo.15626055
- Licencia: CC BY 4.0
- Archivo original: `fuentes_abiertas/zenodo_15626055.json`
- MD5 esperado: `cb44431ef6b32f6ea9cf00dbe35f020c`
- Casos originales: 99
- Casos admitidos: 33

Los casos se conservan completos, uniendo sus sintomas relacionados. Solo se
admiten fallas que ya existen en la taxonomia de CarBot, tienen traduccion
completa y no presentan un mapeo ambiguo. Estos registros cuentan con auditoria
de taxonomia, pero no equivalen a reparaciones confirmadas por el taller.

El script `training/preparar_dataset_externo_entrenamiento.py` descarga, verifica
y reproduce el archivo `dataset_externo_auditado.csv`.

## Fuentes excluidas del clasificador

Los reclamos de NHTSA no se usan como etiquetas de falla ni como reparaciones
confirmadas. Un reclamo describe lo reportado por una persona y puede carecer de
diagnostico tecnico. En una futura integracion se podra usar NHTSA como evidencia
separada para recalls, investigaciones o contexto RAG, siempre identificando su
procedencia y sin alterar la prediccion del modelo.

## Regla de evaluacion

El holdout se separa exclusivamente del dataset base antes de incorporar datos
externos. El modelo enriquecido se conserva solo si mejora F1 macro, mantiene la
exactitud, no degrada materialmente la calibracion y ninguna clase pierde mas de
0.10 de F1 frente al modelo base.
