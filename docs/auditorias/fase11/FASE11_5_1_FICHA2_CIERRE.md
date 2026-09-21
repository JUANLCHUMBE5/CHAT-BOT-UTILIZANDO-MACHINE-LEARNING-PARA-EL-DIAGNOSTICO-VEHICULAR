# Fase 11.5.1 - Cierre metodológico de Ficha 2

**Fecha:** 2026-09-19  
**Estado final:** `FASE11_5_1_FICHA2_CERRADA`

## 1. Documentos revisados

Se revisaron el documento principal de tesis, anexos, matriz de consistencia, documentación técnica de proyecto y reportes previos de Fase 11.5:

- `C:\Users\leonc\OneDrive\Pictures\AnyDesk\LIMA-NORTE_PI_LEON_POMA.docx`
- `C:\Users\leonc\Downloads\Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`
- `C:\Users\leonc\Downloads\Matriz_de_consistencia_Tesis_Leon_Poma.docx`
- `C:\Users\leonc\Downloads\Matriz_de_consistencia_resumida_Leon_Poma.docx`
- `docs/proyecto/historial_y_evaluacion.md`
- `docs/auditorias/fase11/TESIS_INSTRUMENTOS_DATA_MAPPING.md`
- `docs/auditorias/fase11/FASE11_5_THESIS_DATA_AUDIT.md`
- `docs/auditorias/fase11/FASE11_5_REPORTE_FINAL.md`

## 2. Referencia documental a los 8 campos

La evidencia suficiente aparece en `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, sección E: "Registro de síntomas y diagnósticos". La nota metodológica indica que un registro completo requiere que los 8 campos obligatorios estén completos.

## 3. Ocho campos confirmados

1. Código de registro.
2. Fecha de atención.
3. Datos generales del vehículo.
4. Síntomas reportados.
5. Descripción del síntoma.
6. Sistema afectado probable.
7. Diagnóstico confirmado por el mecánico.
8. Tiempo de atención registrado.

## 4. Evidencia documental

La matriz completa está en `docs/auditorias/fase11/FICHA2_8_CAMPOS_AUDITORIA.md`.

## 5. Mapeo a PostgreSQL

| Campo Ficha 2 | Mapeo CarBot |
|---|---|
| Código de registro | `validaciones_taller.item` |
| Fecha de atención | `validaciones_taller.fecha` |
| Datos generales del vehículo | `placa_enmascarada`, `placa_hash`, `marca_modelo` |
| Síntomas reportados | `validaciones_taller.sintoma` |
| Descripción del síntoma | `validaciones_taller.sintoma` |
| Sistema afectado probable | `validaciones_taller.sistema_afectado_probable` |
| Diagnóstico confirmado por el mecánico | `validaciones_taller.falla_real` |
| Tiempo de atención registrado | `validaciones_taller.tiempo_diagnostico_minutos` |

Campos nuevos:

- `sistema_afectado_probable`
- `cantidad_campos_completos`
- `detalles_campos`

## 6. Mapeo a API

`CasoValidacionDTO` y `CrearCasoValidacionDTO` incorporan:

- `sistema_afectado_probable`
- `cantidad_campos_completos`
- `detalles_campos`

El backend calcula `campos_completos` a partir de los 8 criterios; no depende únicamente de un booleano manual.

## 7. Mapeo a frontend

El formulario de validación agrega el campo "Sistema afectado probable". El modal de detalle puede mostrar `detalles_campos` cuando la API lo devuelve.

## 8. Mapeo a CSV

El CSV oficial `exportar-fichas-anexo2-csv` agrega:

- `Ficha2_Cantidad_Campos_Completos`
- `Ficha2_Campo1_Codigo_Registro`
- `Ficha2_Campo2_Fecha_Atencion`
- `Ficha2_Campo3_Datos_Generales_Vehiculo`
- `Ficha2_Campo4_Sintomas_Reportados`
- `Ficha2_Campo5_Descripcion_Sintoma`
- `Ficha2_Campo6_Sistema_Afectado_Probable`
- `Ficha2_Campo7_Diagnostico_Confirmado`
- `Ficha2_Campo8_Tiempo_Atencion_Registrado`

La sanitización contra CSV injection se mantiene mediante `_sanitizar_campo_csv`.

## 9. Regla exacta de `campos_completos`

```text
campos_completos =
  campo_1 AND campo_2 AND campo_3 AND campo_4
  AND campo_5 AND campo_6 AND campo_7 AND campo_8
```

- 8/8 -> `campos_completos = 1`
- 7/8 o menos -> `campos_completos = 0`
- `RDC = SUM(campos_completos) / COUNT(registros_evaluados) x 100`

## 10. Pruebas realizadas

- `.\.venv\Scripts\python.exe -m pytest -q backend\tests\test_fase11_5_thesis_and_diagnostic.py`
  - Resultado: `7 passed`
  - Valida aislamiento Fase 11.5, hashes C1/RAG y no contaminación de métricas.

Pruebas nuevas esperadas:

- `backend/tests/test_fase11_5_1_ficha2_campos.py`
  - 8/8 -> completo.
  - 7/8 -> incompleto.
  - 0/8 -> incompleto.
  - cálculo PRE/POST separado por fase.

## 11. Aislamiento DEVELOPMENT / REGRESSION

Se mantiene la regla de repositorio: solo `THESIS_PRETEST` y `THESIS_POSTTEST` con estado `verificado` entran a métricas oficiales. `DEVELOPMENT` y `REGRESSION` quedan excluidos.

## 12. Comparabilidad PRE/POST

Los 8 criterios se aplican a ambos momentos:

- Pre-test: registro tradicional sin CarBot.
- Post-test: registro asistido por CarBot.

Ningún campo exige una capacidad exclusiva del chatbot; por tanto, la comparación RDC es metodológicamente comparable.

## 13. Estado de hashes C1/RAG

La suite de Fase 11.5 validó hashes estrictos:

- `vectorizador_c1.pkl`: OK.
- `modelo_diagnostico_c1.pkl`: OK.
- `modelo_sistema_c1_macrofix.pkl`: OK.
- `indice_faiss_v1.index`: OK.
- `metadatos_manuales_v1.json`: OK.

No se reentrenó C1, no se modificó TF-IDF, no se reconstruyó FAISS y no se alteró RAG.

## 14. Archivos modificados

- `backend/src/infrastructure/database/models/validation.py`
- `backend/src/interfaces/api/v1/dtos/validacion.py`
- `backend/src/application/services/validacion_taller.py`
- `backend/src/infrastructure/database/repositories/validacion_taller_repository.py`
- `backend/src/interfaces/api/v1/endpoints/validacion_taller.py`
- `backend/alembic/versions/20260919_02_ficha2_trazabilidad_8_campos.py`
- `backend/tests/test_fase11_5_1_ficha2_campos.py`
- `frontend/src/types/api.ts`
- `frontend/src/hooks/useValidacionTaller.ts`
- `frontend/src/components/views/validacion/ValidacionNuevoCasoModal.tsx`
- `frontend/src/components/views/validacion/ValidacionCasosTable.tsx`
- `docs/auditorias/fase11/FICHA2_8_CAMPOS_AUDITORIA.md`
- `docs/auditorias/fase11/FASE11_5_1_FICHA2_CIERRE.md`

## 15. Migraciones realizadas

Creada:

- `20260919_02_ficha2_trazabilidad_8_campos.py`

Pendiente de aplicar en cada entorno con:

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

## 16. Resultado final

La definición documental de los 8 campos fue confirmada y el software fue ajustado para adaptarse al instrumento de investigación, no al revés.

**Resultado:** `FASE11_5_1_FICHA2_CERRADA`
