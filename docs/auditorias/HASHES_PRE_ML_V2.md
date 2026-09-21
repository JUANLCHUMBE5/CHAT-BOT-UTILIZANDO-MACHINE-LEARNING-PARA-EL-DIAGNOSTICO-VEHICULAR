# Registro Forense de Blindaje: Hashes Pre-Entrenamiento ML V2

**Fecha de Cálculo:** 2026-09-19 22:40:12  
**Manifiesto Operacional Vigente:** [`CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/fase11_6/CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json)  
**Versión de Referencia:** `CARBOT_PRECAMPO_FROZEN` (`FASE_11_6_4`)  
**Estado de Blindaje:** **APROBADO (13/13 COINCIDEN - 100% INTACTO)**

---

## 1. Tabla de Verificación Criptográfica SHA-256

| Componente | Ruta Relativa | Hash Esperado en Manifiesto | Hash Actual Calculado | Tamaño (Bytes) | Estado |
|---|---|---|---|---|---|
| **`vectorizador_tfidf`** | `machine_learning/models/c1_fase10_final/vectorizador_c1.pkl` | `060d0728733499d2...` | `060d0728733499d2...` | 264,089 | ✅ INTACTO |
| **`modelo_svm_diagnostico`** | `machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl` | `24747fb7d3d46522...` | `24747fb7d3d46522...` | 23,710,300 | ✅ INTACTO |
| **`modelo_macro_sistema`** | `machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl` | `dec3ba707ff000b3...` | `dec3ba707ff000b3...` | 4,532,678 | ✅ INTACTO |
| **`metadata_modelo_c1`** | `machine_learning/models/c1_fase10_final/metadata_c1_macrofix.json` | `c1ac4a528ee75931...` | `c1ac4a528ee75931...` | 1,134 | ✅ INTACTO |
| **`indice_faiss_rag`** | `machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index` | `a2a081ffded23d4d...` | `a2a081ffded23d4d...` | 31,268,893 | ✅ INTACTO |
| **`metadatos_procedimientos_rag`** | `machine_learning/manuals/candidates/v1/metadata/metadatos_schema_v2.json` | `af5c5edebdebbdbe...` | `af5c5edebdebbdbe...` | 523,538 | ✅ INTACTO |
| **`corpus_manifest_rag`** | `machine_learning/manuals/candidates/v1/manifests/corpus_manifest.json` | `a0fce3dc39bb6344...` | `a0fce3dc39bb6344...` | 152,096 | ✅ INTACTO |
| **`politica_fusion`** | `backend/src/core/diagnostico/politica_fusion.py` | `219e730083c67398...` | `219e730083c67398...` | 24,308 | ✅ INTACTO |
| **`taxonomia_sistemas`** | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `72042cd6bf49855c...` | `72042cd6bf49855c...` | 12,477 | ✅ INTACTO |
| **`semantic_purifier`** | `backend/src/core/diagnostico/semantic_purifier.py` | `ffdf60e370f6f92e...` | `ffdf60e370f6f92e...` | 6,186 | ✅ INTACTO |
| **`text_processor`** | `backend/src/core/diagnostico/text_processor.py` | `66367147e1246525...` | `66367147e1246525...` | 43,119 | ✅ INTACTO |
| **`traductor_jerga`** | `backend/src/core/traductor_jerga.py` | `c582fec573d01424...` | `c582fec573d01424...` | 7,977 | ✅ INTACTO |
| **`motor_rag`** | `backend/src/infrastructure/motor_rag.py` | `47773d39c9944de0...` | `47773d39c9944de0...` | 34,604 | ✅ INTACTO |

---

## 2. Declaración de Blindaje Operacional

1. Los 13 artefactos protegidos de producción han sido certificados como **READ-ONLY**.
2. Cualquier reentrenamiento, vectorización o construcción de índice FAISS en la fase experimental se ejecutará exclusivamente dentro de:
   - `machine_learning/experimentos/carbot_v2/`
3. Ningún archivo con los nombres canónicos de producción (`modelo_diagnostico_c1.pkl`, `vectorizador_c1.pkl`, `modelo_sistema_c1_macrofix.pkl`, `indice_faiss_v1.index`) será sobreescrito.
4. Al finalizar la fase experimental se comprobará que `HASH_PRE == HASH_POST`. Si algún hash cambia, la fase será invalidada de inmediato.
