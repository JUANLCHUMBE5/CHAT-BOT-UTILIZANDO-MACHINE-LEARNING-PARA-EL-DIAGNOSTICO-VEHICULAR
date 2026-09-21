# Dataset candidato GemaCar

`gemacar_sintomas_causas_candidatas.csv` organiza dos guias web como una base
de conocimiento **multicausa**. Cada fila relaciona un sintoma y una condicion
con una causa posible, una revision inicial, una pregunta de aclaracion y su
trazabilidad.

## Estado y uso permitido

- No forma parte de `dataset_sintomas_limpio.csv`.
- Todos los registros comienzan con `validado_por_mecanico=NO` y
  `apto_entrenamiento=NO`.
- La fuente es secundaria y no declara una licencia abierta de reutilizacion.
- Puede emplearse internamente para revision, taxonomia y preparacion de
  conocimiento RAG, conservando siempre la URL de procedencia.
- No debe presentarse una `causa_candidata` como diagnostico confirmado.

El derivado `dataset_gemacar_experimental.csv` contiene solo cinco grupos
univocos y se usa exclusivamente para entrenar y medir una variante aislada. El
experimento no reemplaza el modelo operativo cuando empeora sus metricas.

El archivo `manuals/generales/orientacion_secundaria_gemacar.txt` contiene 26
secciones multicausa que el RAG indexa con el estado
`fuente_secundaria_no_validada`. Su contenido sirve para orientar preguntas y
pruebas iniciales, no para confirmar piezas.

## Campos de revision

- `estado_mapeo`: indica si existe una equivalencia conservadora con una clase
  actual, si falta una clase o si la relacion es ambigua.
- `decision_revision`: debe cambiarse a `APROBADO`, `CORREGIDO` o `DESCARTADO`
  durante la evaluacion tecnica.
- `observaciones_revision`: registra prueba realizada, correccion y evidencia.
- `codigo_canonico_propuesto`: sugerencia; no sustituye la validacion fisica.

## Flujo antes de entrenar

1. Obtener autorizacion de reutilizacion de la fuente.
2. Hacer revisar cada fila por un mecanico identificado.
3. Registrar el diagnostico y reparacion realmente confirmados en el taller.
4. Convertir solo esos casos reales a ejemplos de una unica clase canonica.
5. Entrenar y comparar contra el holdout sin mezclar datos de evaluacion.

Reproduccion desde la raiz del repositorio:

```powershell
.\.venv\Scripts\python.exe .\machine_learning\training\preparar_candidatos_gemacar.py `
  --fuente-general <fallas-comunes.txt> `
  --fuente-potencia <perdida-potencia.txt>
```

El archivo `gemacar_sintomas_causas_reporte.json` conserva los conteos y los
SHA-256 usados para verificar los textos de origen.
