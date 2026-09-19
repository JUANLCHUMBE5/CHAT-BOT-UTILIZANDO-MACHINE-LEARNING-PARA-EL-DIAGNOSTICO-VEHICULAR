# FASE 11.4 - Reporte Final

## 1. Resumen ejecutivo

Se corrigio el flujo conversacional real mecanico -> CarBot sin tocar C1, TF-IDF, Macrofix ni RAG. La fase queda como `FASE11_4_APROBADA_CON_OBSERVACIONES` porque las pruebas locales pasan, pero el webhook real Meta/WhatsApp queda pendiente de validacion externa.

## 2. Problemas observados

1. Un caso de arranque en frio recibia una pregunta generica de ralenti/acelerar/freno.
2. Un nuevo vehiculo con sintomas en el mismo mensaje podia caer en reset repetitivo o aclaracion innecesaria.
3. "No se prende ninguna luz" podia contaminar el caso como testigo positivo.
4. "Temperatura del motor empieza a subir" y "perdiendo liquido refrigerante" no siempre quedaban como hechos.

## 3. Causas raiz

- Parser incompleto para variantes naturales de arranque.
- Polaridad insuficiente para negaciones con "se prende".
- Reset tratado como respuesta final aun cuando el mismo mensaje trae sintomas.
- Segmentador sin normalizacion defensiva para tildes/caracteres reemplazados.
- Suficiencia no elevaba como fuerte la combinacion sobrecalentamiento + fuga.

## 4. Correcciones aplicadas

- `extractor_hechos.py`: reconoce "demora bastante/demasiado en encender", "da marcha varios segundos antes de encender" y reinicio con contenido diagnostico.
- `diagnostic_workflow.py`: el webhook solo responde reset si el mensaje no trae sintomas.
- `orquestador_conversacion.py`: misma regla para el pipeline interno.
- `segmentador_casos.py`: normaliza texto antes de detectar nueva queja/caso.
- `detector_polaridad.py`: registra negacion de luz/testigo y extrae sobrecalentamiento/fuga con lenguaje natural.
- `suficiencia_informacion.py`: considera sobrecalentamiento + fuga como evidencia fuerte.
- `version.py`: runtime conversacional actualizado a `11.4.0`.
- `test_real_mechanic_flow.py`: regresiones nuevas de arranque, nuevo vehiculo y reset puro.

## 5. Validaciones

- Fase 11.4 + Fase 11.3: `19 passed`.
- Regresion RAG local disponible: `20 passed`.
- Hashes C1 coinciden con manifiesto congelado.
- RAG no fue reconstruido.

## 6. Archivos modificados

| Archivo | old_sha256 | new_sha256 | Motivo |
|---|---:|---:|---|
| `backend/src/core/conversacion/extractor_hechos.py` | `523546D776D3F709F61A933037F828592F9630508A5B1571DF6A7A14846071C1` | `42D66D10345A581B43806EE1557D9D3A77BF52B8362D114D2332F4E8BB746662` | Arranque y reset con sintomas |
| `backend/src/core/conversacion/detector_polaridad.py` | `075DC3DE284CADF48058B9E7B87EA33DC6B7BFE9DE36DE1FC1643655A837D35D` | `B9DD286D9A69C3B71DA774EE9A6E71AB372024F9444DED82F3EC5FD55F35499C` | Negacion de testigo, temperatura y fuga |
| `backend/src/core/conversacion/orquestador_conversacion.py` | `05BB30D7C26E2FC65A974358124B744AACAFAC3CA329605E61D125E508D39362` | `D42878EF49C470729FBED51A4E09F2153427F2B1566C20901F745F483122E159` | No descartar sintomas en nuevo caso |
| `backend/src/core/services/webhook/diagnostic_workflow.py` | `0D1C9FDDD1F471A33BA1C8D81729D3C11E2E752746E2DB0EF2027FC93C7DA8B0` | `BB043AD481167F2273900A18306EE82AF1B05C948C12B877D9E0D3C78756525A` | Paridad webhook real |
| `backend/src/core/version.py` | `31EE6B4C37343DE00B388BB6F84C2EEDD53FF6DE2FA4769B78DB6DD682D6E319` | `D0788E76ED76E806C7FF19E8000B45E387D544F53A4C9A6FBD3E01933497C028` | Version runtime 11.4.0 |
| `backend/src/core/conversacion/segmentador_casos.py` | `no_capturado_pre_fase` | `035A9167684BE3D304F9EC170E29ED7E75CDB6FEAE071BF685584A33AC9A8703` | Normalizacion de transicion |
| `backend/src/core/conversacion/suficiencia_informacion.py` | `no_capturado_pre_fase` | `F6008B798EE2D20822E21FFB736DA842589AA56F4D40534E6DC88225C0E5ECEB` | Evidencia fuerte temperatura + fuga |
| `backend/tests/fase11_4_conversation_flow/test_real_mechanic_flow.py` | `NEW` | `F556046FB447427C8948B08F1ABC596073FBA68F766FA747F23E7E7452F916EE` | Regresion 11.4 |

## 7. Limitaciones

No se probo contra Meta/WhatsApp real en esta ejecucion por depender del entorno externo. No se uso muestra de tesis, no se entreno C1 y no se reconstruyo RAG.

## 8. Dictamen

`FASE11_4_APROBADA_CON_OBSERVACIONES`
