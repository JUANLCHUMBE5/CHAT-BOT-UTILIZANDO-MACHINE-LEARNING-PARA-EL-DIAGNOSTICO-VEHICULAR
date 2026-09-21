# Fase 11.5.2 - Validacion E2E de instrumentos de tesis

Estado final: **FASE11_5_2_E2E_APROBADA_PENDIENTE_WHATSAPP_MANUAL**

Fecha de cierre tecnico: 2026-09-19.

## 1. Estado de migracion

Se inspeccionaron y aplicaron migraciones no destructivas:

- `20260919_02`: trazabilidad auditable de Ficha 2.
- `20260919_03`: subcampos independientes para descripcion del sintoma y datos generales del vehiculo.

Correccion realizada: el `revision ID` inicial de `20260919_02_ficha2_trazabilidad_8_campos` excedia el limite `VARCHAR(32)` de `alembic_version.version_num`; se redujo a `20260919_02`.

Estado Alembic:

- `carbot_db`: `20260919_03`.
- `carbot_test`: `20260919_03`.

## 2. Schema PostgreSQL comprobado

Columnas verificadas fisicamente en `validaciones_taller`:

- `sistema_afectado_probable`
- `cantidad_campos_completos`
- `detalles_campos`
- `descripcion_sintoma`
- `vehiculo_anio`
- `vehiculo_kilometraje`
- `vehiculo_combustible`
- `vehiculo_transmision`

## 3. Flujo PRE auditado

El PRE-test representa diagnostico tradicional sin CarBot. El DTO permite `fase=Pre-test` y no exige `conversacion_id` ni `diagnostico_id`.

Campos cubiertos:

- Ficha 1: hipotesis inicial del mecanico, falla confirmada y acierto.
- Ficha 2: ocho criterios oficiales.
- Ficha 3: tiempo de diagnostico en minutos.

## 4. Flujo POST auditado

El POST-test permite registrar:

- prediccion CarBot / Linear SVM;
- sistema afectado probable;
- diagnostico fisico confirmado;
- resultado correcto o incorrecto;
- tiempo de atencion;
- `conversacion_id` y `diagnostico_id` cuando existan.

La prediccion de CarBot no se autodeclara correcta: el campo decisivo sigue siendo el diagnostico confirmado por el mecanico.

## 5. Persistencia campo por campo

Prueba automatizada `test_persistencia_e2e_development_y_exclusion_oficial`:

- crea taller temporal;
- crea caso `DEVELOPMENT`;
- persiste via servicio/repositorio;
- consulta PostgreSQL columna por columna;
- recupera mediante servicio;
- verifica que las metricas oficiales no cambian.

No se insertaron `THESIS_PRETEST` ni `THESIS_POSTTEST` ficticios.

## 6. Validacion de Ficha 1 - PPCF

Formula mantenida:

`PPCF = predicciones correctas / total predicciones realizadas * 100`

Fixture controlado:

- PRE: 4 casos, 2 correctos = 50.00%.
- POST: 4 casos, 3 correctos = 75.00%.

Resultado: **PASS**.

## 7. Validacion de los 8 campos de Ficha 2

Los ocho campos oficiales son:

1. Codigo de registro.
2. Fecha de atencion.
3. Datos generales del vehiculo.
4. Sintomas reportados.
5. Descripcion del sintoma.
6. Sistema afectado probable.
7. Diagnostico confirmado por el mecanico.
8. Tiempo de atencion registrado.

Regla:

- 8/8 = `campos_completos = 1`.
- 7/8 o menos = `campos_completos = 0`.

Casos probados:

- 8/8: PASS.
- 7/8: PASS.
- 1/8: PASS.
- 0/8: PASS.

`detalles_campos` registra `campo_1` a `campo_8` con `completo=true/false`.

## 8. Sintomas reportados vs descripcion del sintoma

Se encontro discrepancia: ambos valores se estaban alimentando desde `sintoma`.

Correccion:

- `sintoma`: sintomas reportados/listado.
- `descripcion_sintoma`: descripcion narrativa independiente.

Si `sintoma` existe pero `descripcion_sintoma` esta vacio:

- campo 4 = completo.
- campo 5 = incompleto.

## 9. Datos generales del vehiculo

Segun Anexo 2, el bloque incluye:

- marca/modelo;
- año;
- kilometraje aproximado;
- tipo de combustible;
- tipo de transmision.

Correccion:

- se agregaron `vehiculo_anio`, `vehiculo_kilometraje`, `vehiculo_combustible`, `vehiculo_transmision`;
- el criterio 3 solo se considera completo si todos los subcampos estan presentes.

## 10. Validacion de Ficha 2 - RDC

Formula mantenida:

`RDC = registros completos / total registros evaluados * 100`

Fixture controlado:

- PRE: 4 registros, 2 completos = 50.00%.
- POST: 4 registros, 3 completos = 75.00%.

Resultado: **PASS**.

## 11. Validacion de Ficha 3 - TPRD

Formula mantenida:

`TPRD = suma de tiempos de diagnostico / total diagnosticos evaluados`

Fixture controlado:

- PRE: 20, 30, 40, 50 min = 35.00 min.
- POST: 10, 15, 20, 15 min = 15.00 min.

No se usa `tiempo_inferencia_ml_ms` como TPRD.

Resultado: **PASS**.

## 12. Validacion del CSV

El CSV permite reconstruir:

- PPCF;
- RDC;
- TPRD;
- estados individuales de Ficha 2;
- fase, fecha, item y tipo de registro;
- campos de conversacion/diagnostico cuando existan.

La sanitizacion anti CSV injection se conserva para valores que inician con `=`, `+`, `-`, `@`, tab o retorno.

Resultado: **PASS**.

## 13. Aislamiento DEVELOPMENT y REGRESSION

Los indicadores oficiales filtran:

- `estado_registro = 'verificado'`;
- `tipo_registro in ('THESIS_PRETEST', 'THESIS_POSTTEST')`.

Fixtures `DEVELOPMENT` no alteraron:

- PPCF oficial;
- RDC oficial;
- TPRD oficial;
- N oficial.

Resultado: **PASS**.

## 14. Comparabilidad PRE/POST

PRE y POST comparten las mismas formulas y campos metodologicos. La diferencia es operativa:

- PRE: diagnostico tradicional, sin obligar conversacion CarBot.
- POST: diagnostico asistido, con trazabilidad CarBot cuando corresponda.

Resultado: **PASS**.

## 15. Integridad C1/RAG

Hashes SHA-256 verificados:

- `vectorizador_c1.pkl`: MATCH.
- `modelo_diagnostico_c1.pkl`: MATCH.
- `modelo_sistema_c1_macrofix.pkl`: MATCH.
- `indice_faiss_v1.index`: MATCH.
- `metadatos_manuales_v1.json`: MATCH.

No se modifico ni reentreno ML, TF-IDF, RAG ni FAISS.

## 16. Tests ejecutados

- Fase 11.5: 7 passed.
- Fase 11.5.1: 4 passed.
- Fase 11.5.2: 6 passed.
- Total fase: 17 passed.
- Ruff backend: PASS.
- Frontend `npm run verify`: PASS.
- Alembic current/head: PASS.

## 17. Estado frontend

El formulario de validacion ahora permite capturar:

- descripcion del sintoma;
- año;
- kilometraje;
- combustible;
- transmision;
- sistema afectado probable.

El modal de detalle muestra:

- Ficha 1;
- Ficha 2 con X/8 y detalle auditable;
- Ficha 3;
- conversacion y diagnostico vinculados cuando existan.

## 18. Discrepancias encontradas

1. `descripcion_sintoma` no existia como dato independiente.
2. `datos_generales_vehiculo` se estaba reduciendo a `marca_modelo`.
3. `carbot_test` estaba desfasada de `carbot_db` y no tenia las migraciones nuevas.
4. Existen 1930 registros antiguos en `carbot_db` con `tipo_registro='THESIS_POSTTEST'` y `estado_registro='borrador'`.

Los registros antiguos no se eliminaron ni se modificaron. Como estan en borrador, no entran a indicadores oficiales, pero deben revisarse antes del trabajo de campo si se desea una muestra completamente limpia.

Muestra de registros reportados:

- `375e85ce-fdc3-4632-ad7c-4144191317c7`
- `21aefabc-aa2c-4045-92ef-e1a5ddc76bfd`
- `360aca12-8679-4456-beaf-06fcff6ada5d`

## 19. Correcciones realizadas

- Migracion `20260919_03`.
- DTOs backend con subcampos oficiales.
- Modelo SQLAlchemy actualizado.
- Repositorio/servicio actualizados.
- Frontend actualizado.
- Test E2E agregado.
- Matriz de pruebas agregada.

## 20. Archivos modificados

- `backend/alembic/versions/20260919_02_ficha2_trazabilidad_8_campos.py`
- `backend/alembic/versions/20260919_03_ficha2_subcampos_vehiculo.py`
- `backend/src/application/services/validacion_taller.py`
- `backend/src/infrastructure/database/models/validation.py`
- `backend/src/infrastructure/database/repositories/validacion_taller_repository.py`
- `backend/src/interfaces/api/v1/dtos/validacion.py`
- `backend/src/interfaces/api/v1/endpoints/validacion_taller.py`
- `backend/tests/test_fase11_5_2_instrumentos_e2e.py`
- `frontend/src/components/views/validacion/ValidacionNuevoCasoModal.tsx`
- `frontend/src/components/views/validacion/ValidacionCasosTable.tsx`
- `frontend/src/hooks/useValidacionTaller.ts`
- `frontend/src/types/api.ts`
- `docs/auditorias/fase11/FASE11_5_2_TEST_MATRIX.csv`
- `docs/auditorias/fase11/FASE11_5_2_VALIDACION_E2E_INSTRUMENTOS.md`

## 21. Estado final

CarBot queda tecnicamente preparado para iniciar la recoleccion Pre-test/Post-test desde el punto de vista de:

- persistencia;
- trazabilidad;
- calculo PPCF/RDC/TPRD;
- separacion PRE/POST;
- aislamiento DEVELOPMENT/REGRESSION;
- integridad ML/RAG.

Pendiente: prueba manual real por WhatsApp y decision sobre los registros antiguos en borrador marcados como `THESIS_POSTTEST`.
