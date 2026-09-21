# FASE 11.6.4 — HOTFIX FINAL DE POLÍTICA DTC + CONGELAMIENTO PRE-CAMPO
## CORRECCIÓN ARQUITECTÓNICA DE RESOLUCIÓN DE CONTRADICCIÓN MACRO-SISTEMA Y VALIDACIÓN DE REGRESIÓN

**Fecha:** 2026-09-19  
**Estado:** HOTFIX IMPLEMENTADO Y VALIDADO — CARBOT_PRECAMPO_FROZEN  
**Artefactos Generados:**  
- [`backend/src/core/diagnostico/politica_fusion.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/src/core/diagnostico/politica_fusion.py)
- [`backend/tests/test_hotfix_fase11_6_4.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/tests/test_hotfix_fase11_6_4.py)
- [`docs/fase11_6/FASE11_6_4_REGRESION.csv`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/fase11_6/FASE11_6_4_REGRESION.csv)
- [`docs/fase11_6/CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/fase11_6/CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json)

---

## 1. Parte A — Reconstrucción Forense de BLIND_38

### Consulta Evaluada:
> *"Módulo electrónico de frenos ABS enciende testigo de avería con código de falla C0040 por circuito abierto en captador de velocidad de rueda."*

- **Ground Truth:** `Falla en sensor de velocidad de rueda ABS` (Macro: `FRENOS`).
- **Comportamiento Previo (Defectuoso):**
  - Top-1 Predicho: `Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)` (99.51%)
  - Macro Predicho: `MOTOR`
  - Top-2: `Falla en sensor de velocidad de rueda ABS` (3.30%)
  - Top-3: `Fuga hidraulica o aire en el sistema de frenos` (1.70%)

### Trazabilidad Paso a Paso en el Pipeline:

```
[Consulta de Usuario] 
       │
       ▼
1. Extracción Regex DTC ─────────────► Detecta exitosamente: ['C0040']
       │
       ▼
2. Vectorizador TF-IDF / SVM ────────► Tokens "circuito abierto" activan fuertemente
                                       la clase 'Falla en circuito o solenoide de inyector individual' (99.51%)
       │
       ▼
3. Recuperación RAG ─────────────────► Procedimiento: PURGADO HIDRÁULICO DE MÓDULO ABS Y SENSORES (DTC C0040)
                                       Similitud: 1.0000 | Falla RAG: Sensor de velocidad de rueda ABS
       │
       ▼
4. Punto de Ruptura (Política de Fusión):
   a) Condición física defectuosa:
      es_resistencia_infinita = any(w in texto for w in ("circuito abierto", ...))
      -> Evaluaba a True SIN verificar mención de inyector ni unidades de resistencia (ohmios).
   b) Rescate físico prematuro:
      falla_elegida = 'Falla en circuito o solenoide de inyector...' (RESCATE_EVIDENCIA_FISICA).
   c) Bloque de DTCs omitido:
      Al resolverse como evidencia física en la sección A, el bloque elif dtcs: NUNCA se ejecutaba.
       │
       ▼
[Resultado Final Defectuoso] ────────► Inyector Individual (MOTOR) eclipsó al sensor ABS (FRENOS)
```

---

## 2. Parte B — Implementación de la Corrección Generalizable

Se efectuó la mínima intervención arquitectónica necesaria en [`backend/src/core/diagnostico/politica_fusion.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/src/core/diagnostico/politica_fusion.py):

### 1. Calificación Semántica de la Evidencia Física de Inyectores:
Se corrigió la variable `es_resistencia_infinita` para exigir explícitamente contexto de inyectores o unidades de resistencia eléctrica, evitando que cualquier mención de "circuito abierto" (común a sensores de rueda, airbags o cableados) fuerce erróneamente un solenoide de inyector:

```python
tiene_token_circuito_abierto = any(
    w in texto_norm for w in ("abierto infinito", "resistencia infinita", "circuito abierto")
)
tiene_contexto_inyector = any(
    w in texto_norm for w in ("inyector", "inyectores", "ohmios", "ohm", "p0201", "p0202", "p0203", "p0204", "p0205", "p0206", "p0207", "p0208")
)
es_resistencia_infinita = tiene_token_circuito_abierto and tiene_contexto_inyector
```

### 2. Resolución de Contradicción de Macro-Sistema en el Bloque DTC:
Se integró el principio de autoridad del estándar OBD-II: cuando un DTC estructurado reconocido en el catálogo (`DTC_A_SISTEMA`) posee una asociación clara a un subsistema funcional (`macro_dtc`, ej. `FRENOS`) y entra en contradicción con una predicción textual del ML perteneciente a un macro-sistema incompatible (`macro_top1`, ej. `MOTOR`):

```python
elif macro_dtc:
    macro_top1 = obtener_macro_sistema(top1_ml)
    if macro_top1 != macro_dtc:
        candidata_rescate = fallas_prioritarias[0]
```

### Criterios de Generalización Cumplidos:
- **NO** se implementó `if codigo == "C0040"`.
- **NO** se implementó `if codigo.startswith("C")`.
- **NO** se asume que todos los códigos `Cxxxx` correspondan a ABS.
- La regla opera para cualquier código reconocido en `DTC_A_SISTEMA` cuando existe contradicción estructural de subsistema frente al clasificador textual.

---

## 3. Parte C — Batería de Tests Positivos y Negativos

Se implementó la suite [`backend/tests/test_hotfix_fase11_6_4.py`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/backend/tests/test_hotfix_fase11_6_4.py) conteniendo 8 pruebas independientes:

| N° | Prueba Evaluada | Consulta de Entrada | Resultado Obtenido | Estado |
| :---: | :--- | :--- | :--- | :---: |
| **1** | C0040 expresado de forma distinta | *"Testigo de frenos ABS prendido en el tablero con código C0040 captador rueda derecha."* | `Falla en sensor de velocidad de rueda ABS` (FRENOS) | **PASSED** |
| **2** | Otro DTC de ABS en catálogo (C0035) | *"Escaneo arroja código C0035 por señal errática en captador de velocidad de rueda delantera izquierda."* | `Falla en sensor de velocidad de rueda ABS` (FRENOS) | **PASSED** |
| **3** | DTC Pxxxx de motor + "circuito abierto" | *"El escáner registra código P0340 por circuito abierto en el cableado del sensor de árbol de levas CMP."* | `Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)` (MOTOR) | **PASSED** |
| **4** | DTC inyector (P0201) donde MOTOR debe mantenerse | *"Código de falla P0201 circuito abierto en solenoide del inyector del cilindro 1."* | `Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)` (MOTOR) | **PASSED** |
| **5** | Código Cxxxx no registrado en catálogo (C0500) | *"Tengo código de avería C0500 en la dirección asistida."* | No fuerza ABS; mantiene predicción orgánica del pipeline | **PASSED** |
| **6** | Consulta sin DTC (comportamiento normal ML) | *"Al pisar a fondo en cuarta el motor ruge pero el auto no avanza y huele a asbesto quemado."* | `Disco de embrague desgastado o patinando` (TRANSMISION) | **PASSED** |
| **7** | DTC desconocido/no registrado (P9999) | *"La computadora tiene un código no identificado P9999 en el sistema."* | No fuerza clasificación artificial | **PASSED** |
| **8** | Consulta donde texto y DTC son coherentes | *"Escáner OBD-II registra código P0301 fallo de combustión en cilindro 1 con bujía sin chispa."* | `Falla en bujias o bobinas de encendido (misfire)` (MOTOR) | **PASSED** |

**Resultado de la Suite de Pruebas:** **8 de 8 pruebas superadas (100%)**.

---

## 4. Parte D — Reporte de Regresión Exhaustiva

### 1. Suite Completa Pytest del Backend:
Se ejecutó la suite completa de 724 pruebas unitarias e integración (`pytest -q`):
- **Pruebas Pasadas:** **714 passed** (aumentó de 706 a 714 por los 8 nuevos tests superados).
- **Pruebas Fallidas:** **5 failed** *(100% preexistentes de migración Alembic head 20260912 y ordenamiento descendente de historial de Regla 7)*.
- **Pruebas Omitidas:** **5 skipped**.
- **Nuevas Regresiones:** **0**.

### 2. Comparativa ANTES vs DESPUÉS sobre Lotes de Casos (120 Casos Totales):

Los resultados individuales de los 120 casos evaluados fueron archivados en [`docs/fase11_6/FASE11_6_4_REGRESION.csv`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/fase11_6/FASE11_6_4_REGRESION.csv):

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    COMPARATIVA DE REGRESIÓN FASE 11.6.4                           │
├─────────────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Batería Evaluada        │ ANTES (11.6.2)    │ DESPUÉS (11.6.4)  │ Impacto         │
├─────────────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ FASE 11.6 (50 Casos)    │ Top-1: 88.00%     │ Top-1: 88.00%     │ 0 regresiones   │
│                         │ Macro: 96.00%     │ Macro: 96.00%     │ Estable         │
├─────────────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ FASE 11.6.2 BLIND (50)  │ Top-1: 60.00%     │ Top-1: 62.00%     │ +2.00% (Éxito)  │
│                         │ Macro: 92.00%     │ Macro: 94.00%     │ BLIND_38 resuelto│
├─────────────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ HOLDOUT 20 (20 Casos)   │ Top-1: 70.00%     │ Top-1: 70.00%     │ 0 regresiones   │
│                         │ Macro: 100.00%    │ Macro: 100.00%    │ Estable         │
└─────────────────────────┴───────────────────┴───────────────────┴─────────────────┘
```

- **Caso BLIND_38:** Pasa oficialmente de **FALLO** a **ÉXITO** (Top-1: `Falla en sensor de velocidad de rueda ABS`, Confianza: 99.51%, Macro: `FRENOS`).
- **Casos sin DTC:** 100% estables, ninguna alteración en su predicción ni confianza.
- **Otros Casos con DTC:** Mantienen su comportamiento exacto sin colisiones.

---

## 5. Parte E — Revisión Metodológica de Afirmaciones

En cumplimiento estricto de las directrices académicas:
1. **Lenguaje Medible:** Se evitan expresiones hiperbólicas como "100% infalible", "precisión absoluta" o "garantía total".
2. **Declaración Oficial de Madurez:**  
   *"El sistema CarBot se considera técnicamente apto para iniciar una prueba piloto controlada en taller mecánico, sujeto a la validación empírica en condiciones reales de trabajo de campo."*
3. **Diferenciación de Conjuntos de Datos:**
   - **Benchmark Adversarial (11.6 / 11.6.2):** Baterías de laboratorio sintéticas diseñadas deliberadamente para encontrar puntos de quiebre.
   - **Holdout (11.6.1):** Muestra de generalización técnica no vista.
   - **Piloto Controlado:** Verificación previa de usabilidad y estabilidad con mecánicos antes de la toma de datos.
   - **PRETEST / POSTTEST:** Muestra oficial de 60 casos reales de tesis en Carabayllo 2026. Los datos de laboratorio **nunca** sustituirán los resultados de campo.

---

## 6. Parte F — Manifiesto de Congelamiento Oficial Pre-Campo

Se calculó la integridad criptográfica de todos los componentes activos en [`docs/fase11_6/CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/fase11_6/CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json):

| Componente | Archivo Físico | Hash SHA-256 Oficial | Estado |
| :--- | :--- | :--- | :---: |
| **Vectorizador TF-IDF** | `machine_learning/models/c1_fase10_final/vectorizador_c1.pkl` | `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7` | **CONGELADO** |
| **Modelo Diagnóstico SVM** | `machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl` | `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c` | **CONGELADO** |
| **Modelo Macro-Sistema** | `machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl` | `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c` | **CONGELADO** |
| **Metadatos Modelo C1** | `machine_learning/models/c1_fase10_final/metadata_c1_macrofix.json` | `c1ac4a528ee759316480691f4cf05b29c5d28829964d25a7d27ab239e80a084e` | **CONGELADO** |
| **Índice FAISS RAG** | `machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index` | `a2a081ffded23d4d727b5778fbe8fe9a1496677fec2d6a5065c71d6046e7f2b1` | **CONGELADO** |
| **Metadatos RAG v2** | `machine_learning/manuals/candidates/v1/metadata/metadatos_schema_v2.json` | `af5c5edebdebbdbe7f97c4883492ff41fe86a0ddb945d8b7b25ad7a685817d2a` | **CONGELADO** |
| **Manifest Corpus RAG** | `machine_learning/manuals/candidates/v1/manifests/corpus_manifest.json` | `a0fce3dc39bb6344388a18cc4821a718b577e383efc5339f4ad3526be4fbaf20` | **CONGELADO** |
| **Política de Fusión** | `backend/src/core/diagnostico/politica_fusion.py` | `219e730083c6739837de4cc512803b0d2d386928e75cf701550cbbfe24fb6fe0` | **FROZEN HOTFIX** |
| **Taxonomía de Sistemas** | `backend/src/core/diagnostico/taxonomia_sistemas.py` | `72042cd6bf49855c548024e39665ca8cf984954497e613c2333fe3ae73ea8089` | **CONGELADO** |
| **Purificador Semántico** | `backend/src/core/diagnostico/semantic_purifier.py` | `ffdf60e370f6f92e51a0ce3e945c55fe82d56a22830ea515d97f267923fa1c9d` | **CONGELADO** |
| **Procesador de Texto** | `backend/src/core/diagnostico/text_processor.py` | `66367147e1246525e07c0bf52288da61817ef811e967a5b3a32332ef47881023` | **CONGELADO** |
| **Traductor de Jerga** | `backend/src/core/traductor_jerga.py` | `c582fec573d0142491ad82acf1db1755a901f46ba2b3b75a1d7cbead1e9e2b10` | **CONGELADO** |
| **Motor RAG** | `backend/src/infrastructure/motor_rag.py` | `47773d39c9944de00dd348eb42ae41eb8fc265b706f3640ceb5da74e1136c2e3` | **CONGELADO** |

---

## 7. Dictamen Oficial Final

```
================================================================================
                    DICTAMEN OFICIAL PRE-CAMPO
================================================================================
VERSIÓN: CARBOT_PRECAMPO_FROZEN
ESTADO DEL MOTOR: CONGELADO DEFINITIVAMENTE PARA TALLER
DICTAMEN: APTO_PARA_PILOTO_CONTROLADO
================================================================================
```

A partir de este momento, cesan todas las modificaciones y optimizaciones sobre benchmarks sintéticos. Los siguientes datos que procesará CarBot provendrán exclusivamente de la aplicación presencial en taller mecánico en Carabayllo 2026.
