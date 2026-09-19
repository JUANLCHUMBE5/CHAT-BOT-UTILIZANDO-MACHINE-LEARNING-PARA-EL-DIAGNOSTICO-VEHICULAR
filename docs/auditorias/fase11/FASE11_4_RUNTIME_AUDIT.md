# FASE 11.4 Runtime Audit

## Pipeline real auditado

Ruta principal revisada:

WhatsApp webhook -> `backend/src/interfaces/api/v1/endpoints/webhook.py` -> `backend/src/core/services/webhook/diagnostic_workflow.py` -> `OrquestadorConversacion` -> `ExtractorHechos` -> `SegmentadorCasos` -> `EvaluadorSuficiencia` -> `SintetizadorConsulta` -> C1 ML -> RAG -> generacion de respuesta.

## Version runtime

- `APP_VERSION`: `11.4.0`
- `ORCHESTRATOR_VERSION`: `11.4.0`
- `CODE_BUILD_ID`: dinamico, calculado en `backend/src/core/version.py` sobre modulos conversacionales criticos.

## Diferencia test vs runtime

La suite 11.3 probaba el orquestador con frases normalizadas, pero los fallos reales incluian variantes no cubiertas:

- "demora bastante en encender" no coincidia con el patron anterior.
- "no se prende ninguna luz" no coincidia con la negacion del testigo.
- "otro vehiculo + sintomas" se trataba como reset/prompt o como caso ambiguo, no como transicion consumible.
- En Windows/logs algunos textos pueden llegar con `?` en lugar de tildes; ahora el segmentador normaliza antes de decidir.

## RAG activo

No se reconstruyo RAG.

Hashes observados:

- `machine_learning/manuals/indice_faiss.index`: `757C4B006A8995F484F539B05420CD929B6034F9ABA7E845D305A9D3CF631082`
- `machine_learning/manuals/metadatos_manuales.json`: `2F0684477522EFB67F2B8FBE0E14E5B39CC31BF01423CBAFC621A3BC33D76625`
- `machine_learning/manuals/rag_baseline_manifest.json`: `C955C731D363A05D155533D5B3D69C54A1A96E319B26E4962D8A0FE963CCC695`

## C1 congelado

No se modifico C1, TF-IDF ni Macrofix.

- `vectorizador_c1.pkl`: `060D0728733499D263F76408B2E99DDB5A56E5DD0F3A006BFA51548397AA96C7`
- `modelo_diagnostico_c1.pkl`: `24747FB7D3D465227EFBD1376084886B92E5333DD12F0E1B380C0C612585608C`
- `modelo_sistema_c1_macrofix.pkl`: `DEC3BA707FF000B34C9368935EBE14C30439475910EA82F846CC8E3B9C85930C`
- `metadata_c1_macrofix.json`: `C1AC4A528EE759316480691F4CF05B29C5D28829964D25A7D27AB239E80A084E`

## Bloqueos

No se ejecuto webhook real contra Meta/WhatsApp por depender de credenciales y servicios externos. Estado: `ENVIRONMENT_BLOCKED` para staging real externo.
