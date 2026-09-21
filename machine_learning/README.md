# Machine Learning y RAG

Este módulo contiene el ciclo de vida de datos y conocimiento técnico; no es
otro servidor web.

- `data/`: datasets, plantillas y reportes de calidad.
- `manuals/`: corpus referencial indexado por el motor RAG.
- `models/`: artefactos entrenados y métricas versionadas.
- `training/`: preparación, entrenamiento y evaluación reproducible.

Las guías web GemaCar se procesan en dos salidas separadas: cinco relaciones
unívocas alimentan un modelo experimental en `models/experimentos/gemacar/`, y
las 26 agrupaciones multicausa se indexan en RAG como fuente secundaria no
validada. El experimento nunca reemplaza el modelo operativo solo por haberse
entrenado; debe superar las métricas y la validación del taller.

El backend consume estos artefactos mediante los puntos de entrada canónicos
`backend/src/infrastructure/ml/` y `backend/src/infrastructure/rag/`. Los
archivos históricos `modelo_ml.py` y `motor_rag.py` se conservan como
implementación compatible durante la reorganización.

## Entrenamiento experimental auditado

Desde esta carpeta, ejecute
`../.venv/Scripts/python.exe -m training.entrenar_fuentes_auditadas`.
Compara cuatro variantes de TF-IDF/SVM calibrado (palabras/caracteres, con/sin
Zenodo) y escribe una ejecución nueva en `models/experimentos/`. No publica
modelos ni modifica RAG. La calibración y la evaluación separan familias de
síntomas; el reporte incluye bloqueos de producción y hashes verificables.

Resultados y límites de la ejecución del 4 de septiembre de 2026:
`docs/proyecto/entrenamiento_fuentes_auditadas_2026-09-04.md` en la raíz del repositorio.
