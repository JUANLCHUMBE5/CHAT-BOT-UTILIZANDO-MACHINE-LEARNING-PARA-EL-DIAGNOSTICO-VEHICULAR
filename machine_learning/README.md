# Machine Learning y RAG

Este módulo contiene el ciclo de vida de datos y conocimiento técnico; no es
otro servidor web.

- `data/`: datasets, plantillas y reportes de calidad.
- `manuals/`: corpus referencial indexado por el motor RAG.
- `models/`: artefactos entrenados y métricas versionadas.
- `training/`: preparación, entrenamiento y evaluación reproducible.

El backend consume estos artefactos mediante los puntos de entrada canónicos
`backend/src/infrastructure/ml/` y `backend/src/infrastructure/rag/`. Los
archivos históricos `modelo_ml.py` y `motor_rag.py` se conservan como
implementación compatible durante la reorganización.
