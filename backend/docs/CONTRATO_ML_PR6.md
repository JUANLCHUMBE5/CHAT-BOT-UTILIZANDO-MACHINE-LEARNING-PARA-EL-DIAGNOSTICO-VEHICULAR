# Contrato diagnóstico PR #6

- `raw_svm_score`: salida `predict_proba` original del SVM calibrado; no margen `decision_function`.
- `calibrated_probability` y `statistical_probability`: probabilidad original, solo si existe.
- `operational_score`: puntuación transformada por jerarquía, DTC y temperatura. No calibrada nuevamente.
- `prediction_source`, `class_id`, `model_version`, `taxonomy_version`: trazabilidad; no confundir reglas con SVM.
- Para reglas: probabilidad estadística `null`. `probabilidad` permanece como score numérico heredado
  para no romper los consumidores actuales; NO se debe renderizar como porcentaje estadístico.
- Frontend pendiente (no modificado): types/domain.ts y DiagnosticoMlSection.tsx deben leer
  `statistical_probability` y mostrar «sin probabilidad estadística» si es null; `operational_score`
  solo se presenta como score. No asumir que 0% demuestra imposibilidad de una falla.

La taxonomía fuente pertenece a ML. El Backend empaqueta una copia generada del contrato Python
con manifest SHA256. Si existe una fuente externa diferente, falla explícitamente. No hay fallback
con clases ni funciones divergentes. La copia no contiene modelos ni índices; ambos consumidores
usan las mismas 61 clases y la misma semántica. No editar manualmente la copia generada.

El benchmark v2 usa fixtures sintéticos versionados y verificados, igualdad de etiqueta y cinco
variantes. Alex requiere fixture externo autorizado y su hash; reproduce todos sus turnos en
memoria, no los concatena. Esa reproducción NO es E2E de webhook/cola/PostgreSQL ni validación
física de la referencia. Los grupos observados no son un holdout independiente ni muestra oficial.
Resultados v1 y v2 no son directamente comparables por el cambio explícito del evaluador.

metadata_c1_macrofix.json tiene hash 6192633d156db24d8d4548077c20336f961141f3b8afc473f24b0542b0dc40f8
igual en runtime y training/fase10/final_candidate/C1. El manifiesto histórico declara otro hash.
No se modificó ese archivo ni el manifiesto para silenciar la discrepancia. Procedencia histórica:
introducido por e0597fb8, luego integrado desde los historiales anteriores del proyecto.
Los hashes binarios SVM/TF-IDF/FAISS permanecen congelados.

El Backend independiente conserva sus archivos de persistencia, migraciones y worker.
Las correcciones recientes de SystemWorker del integrador no se incorporan automáticamente en
su main 58ab3473: no afirmar equivalencia de despliegue entre ambos repositorios.
No desplegar ni fusionar hasta CI y E2E reales aprobados; Docker ausente es bloqueo, no aprobación.
