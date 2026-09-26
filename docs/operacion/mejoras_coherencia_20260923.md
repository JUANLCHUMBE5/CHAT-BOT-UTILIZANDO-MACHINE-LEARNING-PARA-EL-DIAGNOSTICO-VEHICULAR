# Mejoras de coherencia diagnóstica — 23/09/2026

Se priorizan candidatos existentes por evidencia física explícita de suspensión y por queja de acoplamiento de transmisión. Las probabilidades originales no se incrementan; el DTO conserva `predicciones_ml_raw` y `motivo_prioridad`. Esto es mejora de reglas del pipeline, no reentrenamiento ni mejora medida del clasificador aislado.

Antes del RAG se aplica la prioridad para evitar buscar por una hipótesis incompatible. Después de la fusión se rechazan documentos con otra falla declarada o transmisión manual/automática incompatible. Si no existe evidencia aplicable, la respuesta lo comunica sin simular una fuente OEM. El filtro no sustituye una validación exhaustiva marca/modelo/año/motor.

El prompt solicita brevedad y evita especificaciones numéricas no verificadas. Una guarda sustituye respuestas extensas o con unidades técnicas por orientación breve. También se aplica cuando no hay documento válido, evitando instrucciones de seguir un manual inexistente. No garantiza detección de toda forma posible de especificación o contradicción del LLM.

La comprobación explícita de caída de tensión con arranque mediante batería auxiliar evita repetir el mismo descarte.

## Evidencia

- Baseline: `prueba_mecanicos_20260922.json`: 7/10 familias correctas en primera respuesta, 2 prioridades incorrectas y 1 aclaración.
- Repetición corregida: `prueba_mecanicos_20260922_mejorado.json`: 10/10 familias esperadas, Gemini usado en los diez; respuestas de 332–1197 caracteres. Son los mismos casos utilizados para ajustar el flujo: **regresión, no validación independiente ni precisión de campo**.
- Comprobación posterior: `prueba_mecanicos_20260923_final.json`: suspensión y transmisión priorizadas; documento incompatible rechazado. Gemini agotó tiempo de espera en ambos y se activó modo degradado. Esta evidencia precede al último ajuste de presentación del fallback sin documento, validado por prueba unitaria.
- Pruebas: lote inicial de 45 aprobado; 18 pruebas históricas 11.6 aprobadas; lote ampliado de 77 aprobado; módulo final de coherencia con 16 pruebas aprobado. Hay solapamiento entre lotes: no sumar como pruebas únicas.
- Ruff aprobado. Los cuatro archivos del manifiesto canónico C1 conservaron sus hashes. No se editaron modelos, corpus, FAISS ni registros oficiales.

## Límites

Pendiente una muestra nueva de consultas, evaluación de pieza específica, conversaciones completas y entrega física por WhatsApp. Las reglas de prioridad tienen alcance acotado y conservador; no acreditan 80% de precisión general. No se realizó commit ni push.
