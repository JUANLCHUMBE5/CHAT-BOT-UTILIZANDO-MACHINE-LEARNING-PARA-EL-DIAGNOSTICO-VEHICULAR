# Organización Modular del Módulo de Machine Learning (CarBot)

Este directorio estructura los procesos de Machine Learning y evaluación RAG siguiendo una jerarquía modular por responsabilidad única:

## 1. `pipeline/` — Pipelines Oficiales de Tesis y Producción
Contiene los scripts oficiales para entrenamiento, evaluación rigurosa del corpus RAG y generación de fichas del Anexo 2:
- **`entrenar_y_comparar_modelos.py`**: Entrenamiento del clasificador multiclase vehicular (**Linear SVM con vectorización TF-IDF**), validación cruzada estratificada (5-fold CV), cálculo de F1-macro y exportación de `modelo_diagnostico.joblib`.
- **`evaluar_rag_riguroso.py`**: Evaluación de precisión y relevancia del motor RAG sobre el corpus de manuales OEM.
- **`generar_tablas_fichas_anexo2.py`**: Generación de las tablas metodológicas del instrumento de medición de tesis.
- **`analizar_resultados_tesis.py`**: Análisis comparativo de métricas de desempeño.
- **`probar_recuperacion_rag.py`**: Verificación puntual de recuperación vectorial y similitud semántica.

## 2. `datasets/` — Generación, Curación y Aumento de Datos
Contiene los scripts encargados de construir, depurar y balancear los conjuntos de datos:
- **`generar_dataset.py`**: Construcción del dataset base sintetizado y estructurado bajo la taxonomía de 48 fallas canónicas.
- **`generar_dataset_aumento_taller.py`**: Aumento de datos con jerga mecánica peruana y variaciones coloquiales de taller.
- **`limpiar_dataset_taxonomia.py`**: Depuración y validación cruzada contra el catálogo de taxonomía automotriz.
- **`generar_metadatos_reales.py`**: Cálculo de hashes SHA-256 y metadatos de procedencia para el corpus de manuales OEM.
- **`generar_tracker_excel.py`**: Exportación y estructuración del registro de pruebas de taller.

## 3. `experiments/` — Experimentos Exploratorios y Auditorías
Aísla las versiones previas, pruebas de concepto y pipelines de auditoría de datasets externos:
- **`entrenar_modelo.py`**: Versión exploratoria inicial previa a la estandarización de Linear SVM.
- **`entrenar_fuentes_auditadas.py`**: Evaluación de impacto de fuentes académicas externas (Zenodo, etc.).
- **`entrenar_experimento_extendido.py`**: Evalúa el aumento lingüístico sintético con holdout y validación cruzada agrupados por familia. El candidato queda aislado y nunca se promueve automáticamente.
- **`entrenar_experimento_gemacar.py`**: Evaluación del dataset GeMaCar.
- **`evaluar_modelo_externo.py`**: Pruebas de generalización con datos fuera de distribución.
- **`preparar_candidatos_*.py`**: Filtrado y traducción de casos externos hacia español vehicular peruano.

## Admisión de correcciones reales

`pipeline/preparar_correcciones_taller.py` recibe la exportación de validaciones y solo genera candidatos cuando el caso está verificado, posee método y evidencia física, responsable y fecha. El resultado sigue requiriendo revisión ML; una respuesta `NO` de WhatsApp nunca modifica por sí sola el modelo operativo.

> **Nota de compatibilidad**: Los scripts en la raíz de `training/` actúan como puntos de entrada y fachadas hacia los submódulos correspondientes para no romper scripts de consola ni automatizaciones existentes.
