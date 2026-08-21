# Machine Learning y RAG

Este módulo contiene el ciclo de vida de datos y conocimiento técnico; no es
otro servidor web.

- `data/`: datasets, plantillas y reportes de calidad.
- `manuals/`: corpus referencial indexado por el motor RAG.
- `models/`: artefactos entrenados y métricas versionadas.
- `training/`: preparación, entrenamiento y evaluación reproducible.

El backend consume estos artefactos mediante
`backend/src/infrastructure/modelo_ml.py` y
`backend/src/infrastructure/motor_rag.py`.

