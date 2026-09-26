# Importación de revisión mecánica NHTSA

Este experimento convierte el Excel `outputs/revision_mecanica_nhtsa_90_casos.xlsx`
en un dataset experimental, sin modificar el modelo canónico ni el corpus RAG oficial.

## Regla de admisión

Solo se admiten registros que cumplan todos los requisitos:

1. `Estado de revisión = reviewed_by_mechanic`.
2. Etiqueta final incluida en la taxonomía limpia de CarBot.
3. Revisor identificado.
4. Confianza `high` o `medium`.
5. No duplicar el mismo texto con la misma etiqueta.

Los casos `ambiguous`, `rejected`, `pending_mechanical_review` o de confianza baja
se documentan como descarte y no se usan para reentrenar.

## Ejecución

```powershell
.\.venv\Scripts\python.exe machine_learning\experiments\nhtsa_review\preparar_dataset_revisado.py
```

El resultado se crea dentro de `output/` únicamente cuando haya casos válidos.
El siguiente paso será separar grupos por vehículo y entrenar un candidato aislado
con Linear SVM + TF-IDF. La promoción sigue pendiente de evaluación comparativa.

## Entrenamiento candidato (después de la importación)

Primero se puede verificar el estado sin entrenar:

```powershell
.\.venv\Scripts\python.exe machine_learning\experiments\nhtsa_review\entrenar_candidato_aislado.py --check
```

Cuando haya al menos 30 casos válidos y una separación por vehículo con prueba
independiente, se ejecuta:

```powershell
.\.venv\Scripts\python.exe machine_learning\experiments\nhtsa_review\entrenar_candidato_aislado.py
```

Los modelos, vectorizador, matriz de confusión, métricas y hashes se guardan
solamente en `candidate_artifacts/`. No se sobrescriben los artefactos oficiales.
