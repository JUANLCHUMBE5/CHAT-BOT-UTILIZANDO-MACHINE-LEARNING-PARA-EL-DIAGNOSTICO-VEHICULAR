# Trazabilidad de datos de CarBot y respuesta para el jurado

## Respuesta breve recomendada

> El modelo se entrenó con un conjunto de síntomas automotrices sometido a
> limpieza, cuarentena de registros defectuosos y unificación mediante una
> taxonomía estable de fallas. Cada artefacto conserva su reporte de calidad.
> Para ampliar el vocabulario se evaluó una fuente abierta de Zenodo bajo
> licencia CC BY 4.0. Sus síntomas se conservaron con el texto original, DOI y
> licencia, y se tradujeron al español técnico usado en Perú. Esos candidatos
> no se incorporan automáticamente: deben ser revisados por un mecánico antes
> del reentrenamiento. La validación externa real todavía está pendiente y se
> mantendrá separada del entrenamiento para evitar fuga de información.

## Datos verificables actualmente

- Registros iniciales auditados: **18,982**.
- Dataset limpio vigente: **2,751 muestras**, **48 clases canónicas** y
  **14 sistemas automotrices**.
- Registros en cuarentena: **16,231**. Incluyen etiquetas OBD-II genéricas,
  pares defectuosos y clases que no permiten afirmar una falla concreta.
- Duplicados exactos eliminados en la última limpieza: **0**.
- Fuente externa preparada: **196 síntomas** de 99 registros.
- Traducciones a español técnico peruano: **196**.
- Síntomas con mapeo canónico propuesto: **80**.
- Correspondencias marcadas como ambiguas: **12**.
- Síntomas pendientes de crear una clase o descartar: **104**.

Los 196 síntomas externos están en una bandeja de candidatos y **no forman
parte del entrenamiento vigente** mientras `validado_por_mecanico` sea `NO`.

## Procedencia de la ampliación externa

- Nombre: *Automotive Faults Dataset for Diagnostic and Maintenance Systems*.
- Repositorio: Zenodo.
- DOI: https://doi.org/10.5281/zenodo.15626055
- Licencia: Creative Commons Attribution 4.0 International (CC BY 4.0).
- Integridad comprobada mediante MD5:
  `cb44431ef6b32f6ea9cf00dbe35f020c`.

La fuente se utilizó como material candidato y no como validación peruana.
El proceso reproducible está en `machine_learning/training/preparar_candidatos_zenodo.py` y
`machine_learning/training/traducir_candidatos_es_peru.py`.

## Adaptación lingüística para talleres de LATAM y Perú

El sistema normaliza nombres regionales sin cambiar el significado técnico.
Por ejemplo:

| Variante regional | Forma normalizada para Perú |
|---|---|
| balata, fricción | pastilla de freno |
| cloche, croche, clutch | embrague |
| marcha, burro de arranque, motor de partida | motor de arranque |
| rulemán, balero | rodamiento |
| mofle, mufla, exosto | silenciador de escape |
| banda o correa de tiempo | faja de distribución |

Las equivalencias ambiguas no se fuerzan. Por ejemplo, `cardán`, `palier` y
`semi-eje` pueden designar componentes diferentes según el vehículo.

## Diferencia entre entrenamiento, prueba sintética y validación externa

1. **Entrenamiento:** datos usados para ajustar el clasificador.
2. **Prueba sintética de cobertura:** frases generadas o controladas para
   encontrar errores del software y clases débiles. El archivo
   `machine_learning/data/evaluacion_sintetica_cobertura.csv` pertenece a esta categoría.
3. **Validación externa real:** casos que el modelo no vio, confirmados mediante
   inspección o prueba de taller y respaldados por órdenes, actas o fotografías.

Una prueba sintética nunca debe presentarse como orden de trabajo, caso real ni
validación efectuada por mecánicos. Por esa razón se retiraron del repositorio
público los JSON generados que simulaban órdenes `OT-2026-*`, y las evidencias
reales futuras se excluyen de Git para proteger datos del taller y sus clientes.

## Cómo se realizará la validación externa real

1. Registrar el síntoma antes de conocer la predicción del modelo.
2. Confirmar la falla mediante inspección, medición, escáner o procedimiento
   técnico documentado.
3. Asignar un identificador interno al mecánico, sin publicar DNI ni teléfono.
4. Guardar la evidencia en almacenamiento privado y referenciarla desde la
   plantilla `machine_learning/data/plantilla_evaluacion_externa.csv`.
5. Mantener esos casos fuera del entrenamiento.
6. Ejecutar `machine_learning/training/evaluar_modelo_externo.py` y reportar F1 por clase,
   exactitud, cobertura, solapamientos y bloqueos de producción.

## Evidencias que se pueden mostrar al jurado

- `machine_learning/data/reporte_calidad_dataset.json`.
- `machine_learning/data/candidatos_revision/zenodo_15626055_reporte.json`.
- `machine_learning/data/candidatos_revision/zenodo_15626055_es_peru.csv`.
- `docs/notas/fuentes_externas_entrenamiento.md`.
- `machine_learning/models/metricas_modelo.json` para resultados internos.
- `machine_learning/models/metricas_externas.json` para comprobar que la producción permanece
  bloqueada hasta obtener validación externa real.

## Qué no se debe afirmar

- No afirmar que los 196 síntomas de Zenodo son casos peruanos.
- No afirmar que una frase traducida ya fue validada por un mecánico.
- No llamar "casos reales" a datos generados para cobertura.
- No asegurar que el modelo está validado para producción mientras
  `aprobado_produccion` sea `false`.

