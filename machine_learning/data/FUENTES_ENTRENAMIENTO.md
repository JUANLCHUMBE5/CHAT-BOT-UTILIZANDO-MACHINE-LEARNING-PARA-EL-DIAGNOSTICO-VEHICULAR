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

Las guias de GemaCar sobre fallas comunes y perdida de potencia se organizaron
en `candidatos_revision/gemacar_sintomas_causas_candidatas.csv`. Son una fuente
web secundaria, multicausa y sin licencia abierta declarada. Por ello se usan
como candidatos de revision y conocimiento RAG secundario. Cinco relaciones
univocas alimentan un entrenamiento experimental aislado, pero no se incorporan
al modelo operativo hasta contar con autorizacion, validacion mecanica, casos
reales confirmados y una mejora demostrada en el holdout.

## Regla de evaluacion

El holdout se separa exclusivamente del dataset base antes de incorporar datos
externos. El modelo enriquecido se conserva solo si mejora F1 macro, mantiene la
exactitud, no degrada materialmente la calibracion y ninguna clase pierde mas de
0.10 de F1 frente al modelo base.

## Experimento auditado del 4 de septiembre de 2026

`training/entrenar_fuentes_auditadas.py` compara la base con/sin los 33 registros
Zenodo ya existentes y TF-IDF de palabras con/sin caracteres. No incorpora
nuevos casos de Internet sin revisión y no duplica la fuente preexistente.
Los externos se excluyen si coinciden con una familia normalizada de la base.
El vocabulario y la calibración se ajustan dentro de particiones agrupadas.

La selección se realiza mediante validación cruzada sobre desarrollo; la reserva
histórica solo se utiliza después para comparar. No es una evaluación externa
nueva. El candidato queda aislado aunque mejore el promedio: se exige revisar
calibración, clases débiles y casos reales nuevos antes de plantear su publicación.

Kaggle Car Diagnostic Agent queda excluido por licencia `Unknown` y procedencia
no corroborada; UCI APS Scania contiene sensores, no síntomas textuales, y el
dataset textual de Scania publicado en el estudio de 2023 no es público.
