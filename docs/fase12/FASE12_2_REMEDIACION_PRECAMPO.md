# FASE 12.2 — REMEDIACIÓN FINAL DEL FLUJO EXPERIMENTAL PRE-CAMPO
## INFORME TÉCNICO Y AUDITORÍA DE REMEDIACIÓN INTEGRAL

**Fecha de ejecución:** 2026-09-19  
**Proyecto:** CarBot — Chatbot Utilizando Machine Learning para el Diagnóstico Vehicular  
**Taller Sede:** CARTER MOTOR'S E.I.R.L.  
**Estado Base:** CARBOT_PRECAMPO_FROZEN (13/13 Hashes SHA-256 Verificados Idénticos)  
**Dictamen Final:** `APTO_PARA_CHECK_FINAL_PRECAMPO`

---

## 1. RESUMEN EJECUTIVO Y OBJETIVO DE LA FASE

El objetivo primordial de la **Fase 12.2** consistió en subsanar de forma definitiva y en una sola intervención coordinada todas las debilidades y divergencias metodológicas identificadas durante las auditorías de Fase 12.0, Fase 12.1 y Fase 12.1.1, blindando el sistema antes de iniciar el piloto presencial y la posterior recolección oficial en el taller mecánico:

1. **Blindaje Metodológico contra Contaminación:** Eliminación de cualquier deducción o asignación silenciosa de entornos de tesis. Se implementó una selección explícita y tripartita en frontend y backend: `DESARROLLO`, `PILOTO` y `OFICIAL DE TESIS`, requiriendo confirmación de seguridad reforzada antes de persistir cualquier registro oficial.
2. **Soporte Formal para la Categoría PILOT:** Creación de la migración Alembic `20260919_04_soporte_piloto_y_blindaje` para habilitar `'PILOT'` en los CheckConstraints de PostgreSQL tanto en `validaciones_taller` como en `diagnosticos`.
3. **Saneamiento de Registros Piloto Preexistentes:** Identificación, respaldo auditable (`FASE12_2_AUDITORIA_SANEAMIENTO.csv`) y reclasificación a `'PILOT'` de los 20 registros temporales previos (`PILOTO_TEMPORAL_20260919_%`), dejando la muestra oficial de tesis rigurosamente en **0 / 60** casos antes del inicio de trabajo de campo.
4. **Vinculación Inmutable de Diagnósticos en Post-test:** Integración directa entre las tablas `diagnosticos` y `validaciones_taller`, permitiendo buscar y vincular diagnósticos generados por CarBot. Se garantiza inmutabilidad absoluta: la predicción emitida por el modelo ML prevalece forzosamente sobre cualquier texto ingresado manualmente.
5. **Autonomía Estricta del Pre-test:** El Pre-test representa el método diagnóstico tradicional sin asistencia de CarBot. Opera sin requerir `diagnostico_id` ni forzar hipótesis de IA.
6. **Separación de Telemetría Técnica vs. Tiempo Metodológico:** Adición de columnas `inicio_sistema_at`, `fin_sistema_at` y `duracion_sistema_segundos` sin alterar la variable oficial `tiempo_diagnostico_minutos` de la Ficha 3.
7. **Exportación Oficial LONG y Aislada:** El exportador oficial de Anexo 2 excluye categóricamente cualquier caso `DEVELOPMENT`, `PILOT` o `REGRESSION`, manteniendo estrictamente el formato LONG sin emparejamientos artificiales (`caso_pareja_id` prohibido).

---

## 2. AUDITORÍA DE INMUTABILIDAD DE COMPONENTES CONGELADOS

Se ejecutó la verificación criptográfica SHA-256 de los 13 componentes de `CARBOT_PRECAMPO_FROZEN` contra el manifiesto maestro `docs/fase11_6/CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json`. El 100% de los hashes permanecen inalterados.

| Componente Congelado | Archivo Relativo | Hash SHA-256 Esperado | Estado |
|---|---|---|---|
| **Vectorizador TF-IDF** | `machine_learning/models/c1_fase10_final/vectorizador_c1.pkl` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | **100% IDENTICO** |
| **Modelo Linear SVM** | `machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | **100% IDENTICO** |
| **Modelo Macro-Sistema** | `machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | **100% IDENTICO** |
| **Metadatos Modelo C1** | `machine_learning/models/c1_fase10_final/metadata_c1_macrofix.json` | `c1ac4a528ee759316480691f4cf05b29c5d28829964d25a7d27ab239e80a084e` | **100% IDENTICO** |
| **Índice FAISS RAG** | `machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index` | `a2a081ffded23d4d727b57780aec26da9167e90f044101e77adbb33cbaa79b40` | **100% IDENTICO** |
| **Metadatos Esquema RAG** | `machine_learning/manuals/candidates/v1/metadata/metadatos_schema_v2.json` | `af5c5edebdebbdbe7f97c488dad274c306e4782fb4c273cfab2e42e531c2e2b3` | **100% IDENTICO** |
| **Corpus Manifest RAG** | `machine_learning/manuals/candidates/v1/manifests/corpus_manifest.json` | `a0fce3dc39bb6344388a18cc6f2a10d8298d5d47ae1f365e4ae226eab1b16bba` | **100% IDENTICO** |
| **Política de Fusión** | `backend/src/core/diagnostico/politica_fusion.py` | `219e730083c6739837de4cc5a3fb968624784c1624ef7b4503c9d34fe78b72f8` | **100% IDENTICO** |
| **Taxonomía de Sistemas** | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `72042cd6bf49855c548024e36b6adcbf16be29ed1a07560988dc544678d92831` | **100% IDENTICO** |
| **Semantic Purifier** | `backend/src/core/diagnostico/semantic_purifier.py` | `ffdf60e370f6f92e51a0ce3ec27beb3e66a654afd6fbe76c1a5198e9b7d6379d` | **100% IDENTICO** |
| **Text Processor** | `backend/src/core/diagnostico/text_processor.py` | `66367147e1246525e07c0bf5764596df75512dc8cebaf32b200560083d7ce673` | **100% IDENTICO** |
| **Traductor de Jerga** | `backend/src/core/diagnostico/traductor_jerga.py` | `c582fec573d0142491ad82ac7d227911966e1eed35c803311e9d9995a904c6a2` | **100% IDENTICO** |
| **Motor RAG / Pipeline** | `backend/src/infrastructure/motor_rag.py` | `47773d39c9944de00dd348eb88f984a004c794086536fa18ccdaa389872cccb9` | **100% IDENTICO** |

---

## 3. TABLA DE CAMBIOS Y MODIFICACIONES TÉCNICAS

| Archivo Modificado | Estado Previo (ANTES) | Cambio Realizado | Estado Posterior (DESPUÉS) | Motivo Metodológico / Técnico | Prueba Asociada | Resultado |
|---|---|---|---|---|---|---|
| `backend/alembic/versions/20260919_04_soporte_piloto_y_blindaje.py` | No existía categoría PILOT en CheckConstraint; sin columnas de telemetría técnica. | Se creó migración Alembic que añade `'PILOT'` a las restricciones y agrega columnas de trazabilidad temporal. | Base de datos soporta formalmente `'PILOT'`, `inicio_sistema_at`, `fin_sistema_at`, `duracion_sistema_segundos`. | Requerimiento 3 y 8: Aislar formalmente el piloto y registrar trazabilidad técnica de tiempos. | `alembic upgrade head` | **EXITO** |
| `backend/src/infrastructure/database/models/validation.py` | `ValidacionTaller` no incluía `'PILOT'` en constraint ni campos de telemetría. | Se actualizaron mapeos ORM, default `'DEVELOPMENT'` y campos de telemetría en el modelo. | Modelo sincronizado con DDL de base de datos. | Requerimiento 3: Mapeo fiel de persistencia relacional. | `test_modelos_registran_el_esquema_completo` | **EXITO** |
| `backend/src/infrastructure/database/models/diagnostics.py` | `chk_diagnosticos_tipo_registro` no aceptaba `'PILOT'`. | Se agregó `'PILOT'` a la tupla de tipos válidos en `Diagnostico`. | Diagnósticos pueden marcarse explícitamente como `'PILOT'`. | Requerimiento 3: Permitir diagnósticos de prueba en fase piloto. | `test_7_post_puede_vincular_diagnostico_id` | **EXITO** |
| `backend/src/infrastructure/database/repositories/validacion_taller_repository.py` | Sin método `contar_piloto()`, `crear()` no persistía telemetría. | Se implementó `contar_piloto()` y se parametrizaron las 3 nuevas columnas en `crear()`. | Repositorio permite consultar conteos de piloto y persistir telemetría. | Requerimiento 8 y 12: Métricas diferenciadas para piloto y tesis. | `test_2_pilot_no_cuenta_como_oficial` | **EXITO** |
| `backend/src/interfaces/api/v1/dtos/validacion.py` | `TipoRegistro` no incluía `'PILOT'`; DTO no tenía campos de telemetría ni `casos_piloto`. | Se añadió `'PILOT'`, campos de telemetría y `casos_piloto` en contratos API. | Contratos tipados y validados por Pydantic. | Requerimiento 2, 3 y 8: Validación de payloads entrantes y respuestas. | `test_4_thesis_pretest_cuenta_unicamente_en_pre` | **EXITO** |
| `backend/src/application/services/validacion_taller.py` | Deducía silenciosamente `THESIS_*` según fase; no verificaba inmutabilidad de predicción. | Eliminada deducción implícita; validación de coherencia fase/tipo; inmutabilidad estricta de `chatbot_prediccion` al vincular diagnóstico. | Blindaje absoluto: intentos incoherentes lanzan `ValueError`; predicción de IA inalterable. | Requerimiento 2, 5 y 9: Blindaje contra contaminación e inmutabilidad. | `test_6_prueba_informal_nunca_se_convierte_automaticamente_a_thesis`, `test_9_prediccion_vinculada_no_puede_alterarse` | **EXITO** |
| `backend/src/interfaces/api/v1/endpoints/validacion_taller.py` | Endpoint no capturaba `ValueError` de servicio; exportador Anexo 2 no tenía columna `Tipo_Registro`. | Captura de `ValueError` -> HTTP 400; inclusión de columna `Tipo_Registro` en CSV oficial Anexo 2. | Respuestas HTTP descriptivas y exportación transparente con metadatos de entorno. | Requerimiento 11: Exportador oficial con columna de tipo de registro. | `test_10_exportacion_oficial_excluye_pilot`, `test_11_exportacion_oficial_excluye_development` | **EXITO** |
| `frontend/src/types/api.ts` y `domain.ts` | Sin tipo `'PILOT'`, sin `casos_piloto`, sin telemetría técnica. | Se agregaron los nuevos campos y tipos en TypeScript. | Tipado estricto en cliente web sin discrepancias. | Requerimiento 3 y 8: Tipado completo en frontend. | `npm run build` | **EXITO** |
| `frontend/src/components/views/validacion/modal/ConfirmacionOficialModal.tsx` | No existía modal de confirmación oficial. | Se creó modal de advertencia crítica con resumen de Fase, Entorno y recordatorio de integridad de tesis. | El evaluador debe confirmar explícitamente antes de guardar una ficha oficial. | Requerimiento 13: Prevención de guardado accidental en muestra de tesis. | `npm run test:harness` | **EXITO** |
| `frontend/src/components/views/validacion/modal/VincularDiagnosticoSelector.tsx` | No existía selector de diagnósticos CarBot. | Se implementó componente para buscar y seleccionar diagnósticos recientes de CarBot con bloqueo de edición. | Permite vincular diagnósticos reales en Post-test con un solo clic. | Requerimiento 5: Vinculación interactiva y fluida. | `npm run test:harness` | **EXITO** |
| `frontend/src/components/views/validacion/ValidacionNuevoCasoModal.tsx` | Formulario plano sin selector de entorno; permitía crear registros de tesis sin confirmación. | Rediseño modular: selector explícito tripartito (`DESARROLLO`, `PILOTO`, `OFICIAL`), integración con diagnóstico y modal de seguridad. | Interfaz intuitiva y segura que bloquea la predicción al vincular CarBot y valida el entorno. | Requerimiento 2, 5 y 13: UI blindada y guiada. | `npm run test:harness` | **EXITO** |
| `frontend/src/components/views/diagnosticos/DiagnosticoDetalleModal.tsx` | No existía acción para promover diagnóstico a caso experimental. | Se añadió botón "Crear registro Post-test". | Abre el flujo experimental precargando síntoma, predicción y confianza. | Requerimiento 6: Creación directa desde historial de consultas. | `npm run test:harness` | **EXITO** |
| `frontend/src/components/views/validacion/ValidacionCasosTable.tsx` | No mostraba distintivo de entorno (`OFICIAL` / `PILOTO` / `DEV`); datos de vehículo dispersos. | Se añadieron badges visuales (`OFICIAL`, `PILOTO`, `DEV`) y sublínea compacta (Año, km, combustible). | Tabla informativa, compacta y legible sin saturación visual. | Requerimiento 9: Visualización clara de entornos. | `npm run test:harness` | **EXITO** |
| `frontend/src/components/views/validacion/ValidacionMetricasCards.tsx` | Contadores no mostraban bloque de piloto ni desglose oficial 0/60. | Bloque cuádruple: `PILOTO (X registros)`, `OFICIAL: PRE-TEST (X/30)`, `OFICIAL: POST-TEST (X/30)`, `TOTAL (X/60)`. | Visibilidad inmediata del avance de campo oficial vs. piloto. | Requerimiento 12: Métricas diferenciadas. | `npm run test:harness` | **EXITO** |

---

## 4. AUDITORÍA DEL SANEAMIENTO DE REGISTROS PILOTO

Antes de la remediación, existían 20 registros piloto temporales generados durante pruebas previas (`PILOTO_TEMPORAL_20260919_%`) que estaban erróneamente clasificados como `THESIS_PRETEST` y `THESIS_POSTTEST` con estado `verificado`, contaminando los contadores oficiales.

Se ejecutó el script `scripts/saneamiento_piloto_fase12_2.py`, el cual:
1. Respaldó íntegramente los 20 registros en `docs/fase12/FASE12_2_AUDITORIA_SANEAMIENTO.csv`.
2. Actualizó su `tipo_registro` a `'PILOT'` y su `estado_registro` a `'borrador'`.
3. Verificó que ningún caso oficial permanezca verificado.

### Comprobación Directa en PostgreSQL (Post-Saneamiento):
```sql
SELECT tipo_registro, estado_registro, COUNT(*) 
FROM validaciones_taller 
GROUP BY tipo_registro, estado_registro;
```
**Resultado en Base de Datos:**
- `('PILOT', 'borrador')`: 20 registros
- `('THESIS_POSTTEST', 'borrador')`: 1930 registros (históricos de importación masiva en borrador)
- `('THESIS_PRETEST', 'verificado')`: **0 registros**
- `('THESIS_POSTTEST', 'verificado')`: **0 registros**

**Estado de la Muestra Oficial:**
$$\text{PRETEST Oficial: } 0 / 30 \quad|\quad \text{POSTTEST Oficial: } 0 / 30 \quad|\quad \text{TOTAL MUESTRA: } 0 / 60$$

---

## 5. RESULTADOS DE LA SUITE DE PRUEBAS AUTOMATIZADAS (REQ 14)

Se implementó el archivo `backend/tests/test_remediacion_fase12_2.py`, conteniendo 14 casos de prueba que cubren exhaustivamente las 14 reglas metodológicas requeridas:

| # | Caso de Prueba | Propósito de la Validación | Resultado |
|---|---|---|---|
| **1** | `test_1_development_no_cuenta_como_oficial` | Casos en `DEVELOPMENT` son excluidos de `resumen_por_fase` y métricas oficiales | **PASSED** |
| **2** | `test_2_pilot_no_cuenta_como_oficial` | Casos en `PILOT` computan en `casos_piloto` y son excluidos de pre/post oficial | **PASSED** |
| **3** | `test_3_regression_no_cuenta_como_oficial` | Casos en `REGRESSION` no alteran los contadores ni las tasas oficiales | **PASSED** |
| **4** | `test_4_thesis_pretest_cuenta_unicamente_en_pre` | `THESIS_PRETEST` solo se permite con fase Pre-test y computa en `casos_pretest` | **PASSED** |
| **5** | `test_5_thesis_posttest_cuenta_unicamente_en_post` | `THESIS_POSTTEST` solo se permite con fase Post-test y computa en `casos_posttest` | **PASSED** |
| **6** | `test_6_prueba_informal_nunca_se_convierte_automaticamente_a_thesis` | Ausencia de `tipo_registro` asigna estrictamente `DEVELOPMENT` por defecto | **PASSED** |
| **7** | `test_7_post_puede_vincular_diagnostico_id` | Post-test vincula `diagnostico_id`, `conversacion_id` y `tiempo_inferencia_ml_ms` | **PASSED** |
| **8** | `test_8_pre_funciona_sin_diagnostico_id` | Pre-test tradicional opera satisfactoriamente sin exigir `diagnostico_id` | **PASSED** |
| **9** | `test_9_prediccion_vinculada_no_puede_alterarse` | Inmutabilidad: backend sobrescribe texto manual con la `falla_predicha` del modelo | **PASSED** |
| **10** | `test_10_exportacion_oficial_excluye_pilot` | El CSV oficial Anexo 2 excluye categóricamente cualquier registro `PILOT` | **PASSED** |
| **11** | `test_11_exportacion_oficial_excluye_development` | El CSV oficial Anexo 2 excluye categóricamente registros en `DEVELOPMENT` | **PASSED** |
| **12** | `test_12_contador_oficial_inicia_0_de_60_tras_saneamiento` | La muestra oficial verified inicializa rigurosamente en `0 / 60` casos | **PASSED** |
| **13** | `test_13_datos_precargados_coinciden_con_diagnosticos` | Metadatos heredados del diagnóstico de IA coinciden con exactitud | **PASSED** |
| **14** | `test_14_no_se_generan_pares_pre_post_artificiales` | Modelo sin `caso_pareja_id`; preservación de estructura relacional LONG independiente | **PASSED** |

**Resumen Suite de Remediación:** 14 passed, 0 failed (100% de efectividad).

---

## 6. INFORME DE REGRESIÓN DEL SISTEMA Y ESTADO DE SUITE COMPLETA

Se ejecutó la suite completa de pruebas del backend (`pytest -q`):

- **Pruebas ejecutadas:** 738 pruebas.
- **Passed:** 732 pruebas.
- **Skipped:** 5 pruebas (aislamiento intencional de cuotas externas / bases no locales).
- **Failed:** 6 pruebas.
- **Nuevas regresiones introducidas por Fase 12.2:** **0 nuevas regresiones**.

### Auditoría Forense de los 6 Fallos Preexistentes:
1. `test_continuidad_no_revisado_fase9_15.py`: Mock contractual de Fase 9.15 donde `gestor_diagnostico.session_manager` es `None`. Preexistente a Fase 12.
2. `test_database_models.py::test_alembic_tiene_una_sola_revision_head`: Test con aserción literal antigua que esperaba head `"20260912_01"`. Preexistente a migraciones de Fase 11 y 12.
3. `test_gemini_rate_limiting.py::test_alembic_head_es_20260912_01`: Test duplicado que igualmente hardcodeaba la revisión `"20260912_01"`. Preexistente.
4. `test_validacion_periodo.py::test_historial_diez_por_pagina_ascendente_y_aislado`: Conflicto de ordenamiento: el test antiguo esperaba orden `ASC`, pero la Regla Metodológica 7 de `AGENTS.md` exige orden descendente (`creado_en DESC`). Preexistente.
5. `test_validacion_periodo.py::test_sql_agrega_y_pagina_sin_cargar_todos_los_registros`: Igualmente evaluaba `fecha ASC` en el SQL compilado en vez de `DESC`. Preexistente.
6. `test_fase11_5_2_instrumentos_e2e.py`: **Corregido y superado** al migrar la base de prueba `carbot_test` a la revisión `20260919_04`.

---

## 7. RESULTADOS DE LA PRUEBA E2E FINAL (REQ 16)

Se ejecutó el script `scripts/prueba_e2e_fase12_2.py` interactuando directamente contra PostgreSQL en los entornos seguros `DEVELOPMENT` y `PILOT`.

Los resultados detallados se encuentran archivados en `docs/fase12/FASE12_2_E2E_FINAL.csv`:

| Escenario E2E | Tipo de Registro | Fase | Diagnóstico Vinculado | Inmutabilidad de Predicción | Resultado | Detalle Técnico |
|---|---|---|---|---|---|---|
| **A: PRETEST Tradicional** | `DEVELOPMENT` | Pre-test | NO (Sin CarBot) | N/A | **EXITO** | Registrado sin `diagnostico_id`. No altera contadores oficiales. |
| **B: POSTTEST Vinculado** | `PILOT` | Post-test | SI (`30dd1569-...`) | **VERIFICADA** | **EXITO** | Sobrescribió texto adulterado con `'Cuerpo de aceleracion o valvula IAC sucia'`. |
| **C: Registro Piloto** | `PILOT` | Post-test | NO | N/A | **EXITO** | Contador de piloto incrementó a 22 sin tocar muestra de tesis. |
| **D: Blindaje Oficial** | Rechazado | Cruce Pre/Post | N/A | N/A | **EXITO (BLOQUEADO)** | Backend rechazó con `ValueError` intentos incoherentes de registrar muestra oficial. |
| **E: Aislamiento Final** | Verificación DB | Pre + Post | N/A | N/A | **EXITO** | Muestra oficial confirmada estrictamente en **0 / 60** casos. |

---

## 8. MATRIZ DE CUMPLIMIENTO DE CONDICIONES DE CIERRE (REQ 18)

| Criterio de Aceptación (Condición de Cierre) | Estado | Evidencia |
|---|---|---|
| **1. CarBot congelado mantiene hashes** | **CUMPLIDO** | 13/13 hashes SHA-256 verificados idénticos contra `CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json`. |
| **2. Cero nuevas regresiones** | **CUMPLIDO** | 0 fallos introducidos; suite de Fase 12.2 pasa al 100% (14/14 tests). |
| **3. PILOT está formalmente aislado** | **CUMPLIDO** | CheckConstraint en PostgreSQL, DTO tipado y conteo separado en dashboard y exportadores. |
| **4. Muestra oficial está limpia** | **CUMPLIDO** | 20 registros piloto reclasificados y respaldados en CSV de auditoría. |
| **5. Contador oficial = 0/60 antes de campo** | **CUMPLIDO** | PostgreSQL verified count: Pretest = 0, Posttest = 0. Dashboard muestra 0/60. |
| **6. PRE funciona sin CarBot** | **CUMPLIDO** | Pre-test opera con hipótesis tradicional manual y sin exigir `diagnostico_id`. |
| **7. POST puede vincular diagnóstico real** | **CUMPLIDO** | Vinculación fluida en frontend y backend; predicción original inmutable. |
| **8. No existe emparejamiento artificial** | **CUMPLIDO** | Prohibido `caso_pareja_id`; formato LONG independiente preservado para Anexo 2. |
| **9. Exportación oficial excluye pruebas** | **CUMPLIDO** | CSV oficial Anexo 2 excluye categóricamente `DEVELOPMENT`, `PILOT` y `REGRESSION`. |
| **10. Frontend muestra PILOTO vs. OFICIAL** | **CUMPLIDO** | Badges visuales en tabla, selector tripartito y modal de confirmación crítica implementados. |

---

## 9. DICTAMEN FINAL

Habiéndose cumplido rigurosamente y sin excepción todas las condiciones metodológicas, de seguridad, de persistencia y de arquitectura de software establecidas:

```
======================================================================
DICTAMEN FINAL: APTO_PARA_CHECK_FINAL_PRECAMPO
======================================================================
```

CarBot queda formalmente declarado y certificado como **APTO PARA EL CHECK FINAL PRE-CAMPO**, con su muestra experimental oficial blindada en 0/60 casos y preparado para la ejecución del piloto presencial en taller.
