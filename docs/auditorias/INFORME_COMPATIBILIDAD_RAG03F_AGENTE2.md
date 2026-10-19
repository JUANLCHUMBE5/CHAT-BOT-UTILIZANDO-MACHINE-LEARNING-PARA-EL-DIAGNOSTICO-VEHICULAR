# CARBOT — INFORME DE COMPATIBILIDAD Y TRAZABILIDAD DOCUMENTAL (RAG-03F / AGENTE 2)

**Fecha:** 18 de octubre de 2026  
**Rama:** `feat/rag03c3-remediacion-corpus-trazable`  
**Worktree:** `scratch/rag03c3-worktree/`  
**Estado:** IMPLEMENTACIÓN COMPLETADA Y VERIFICADA  
**Gobernanza:** `corpus_validado = False` (Bloqueo preventivo C02 activo)

---

## 1. Resumen Ejecutivo

En cumplimiento de las directivas de la fase **RAG-03F**, el **Agente 2** ha adaptado satisfactoriamente los **17 fragmentos experimentales** y el paquete documental de **256 documentos** al **contrato documental formal unificado** publicado por el Agente 1 (`backend/src/infrastructure/rag/contrato_documental.py`).

### Hitos y Resultados Principales:
1. **Resolución Definitiva de B-INT-02 (Parseo de Páginas):**
   - En la auditoría previa, 15 de los 17 fragmentos (88.2%) fallaban al ser evaluados por `int(pagina)` debido a formatos de cadena complejos (`"5-6"`, `"7, 10, 14"`).
   - Se normalizó el campo `pagina` a un entero positivo (`int > 0`) correspondiente al folio principal verificado en el PDF, y se incorporaron los campos nativos `paginas: List[int]`, `rango_paginas: str` y una matriz estructurada `cifras_trazadas: List[Dict]`.
   - **Tasa de rechazo por formato de página: 0.0% (0 / 17).**
2. **Trazabilidad Metrológica y Cero Invención de Cotas (A08 / C01):**
   - Todas las magnitudes numéricas (torques, presiones, tolerancias de salto y alabeo) coinciden exactamente con la página física del manual o boletín técnico original.
   - Preservada la corrección de seguridad crítica **C01** en Laser Tools 5524 (obligatoriedad de apertura únicamente en frío).
   - Preservadas las delimitaciones de **A08** (cero cotas ficticias en Brembo, Pico y Kia; delimitación estricta a Elantra/Sonata en Hyundai).
3. **Compatibilidad Estructurada en 5 Dimensiones (A03):**
   - Integración formal con `VehiculoConsulta` y `verificar_compatibilidad_estructurada`: consultas con vehículos de marcas opuestas (Toyota Raize, Suzuki S-Presso, Fiat Mobi) o modelos excluidos (Hyundai Tucson) son penalizadas y bloqueadas como `INFORMACION_PARCIAL` con `factor_relevancia <= 0.01` y retención de especificaciones.
4. **Coherencia Matemática Vectorial (<= 1e-6):**
   - Se reconstruyeron los índices temporales FAISS y TF-IDF para Corpus B (256 documentos, dimensión 35,240).
   - Error absoluto máximo L2 entre representación FAISS y TF-IDF: **0.00e+00** ($\le 1.0 \times 10^{-6}$).
5. **Gobernanza y Congelamiento Canónico (C02):**
   - `corpus_validado=False` se mantiene intacto. Ninguna cifra puede ser emitida como autorizada en capa conversacional.
   - Los artefactos de producción v1 (239 documentos, índice y vectorizador congelados) permanecen inalterados con verificación de hash SHA-256 idéntica al manifiesto canónico.
6. **Resultados de la Suite de Pruebas Automáticas:**
   - **10 / 10 pruebas unitarias e integrales superadas con éxito** (`pytest -v test_rag03f_agente2_compatibilidad.py`).

---

## 2. Inventario Técnico de los 17 Fragmentos y Evidencia de Páginas

A continuación se detalla la matriz completa de los 17 fragmentos experimentales autorizados con sus folios físicos, cifras trazadas y condiciones operativas:

| ID Documento | Fabricante / PDF Fuente | Folio Principal (`pagina`) | Folios Totales (`paginas`) | Subsistema / Componente | Cifras y Magnitudes Trazadas | Condición / Advertencia |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `RAG_EXP_BREMBO_001` | Brembo (`brembo_guide_...pdf`) | **5** | `[5]` | Discos de Freno | Tolerancia alabeo: `0.10 mm` | Medición a 10-15 mm del radio exterior con comparador. |
| `RAG_EXP_BREMBO_002` | Brembo (`brembo_guide_...pdf`) | **6** | `[6]` | Buje de Rueda | Tolerancia alabeo buje: `0.05 mm` | Medición de excentricidad radial previa al montaje del disco. |
| `RAG_EXP_BREMBO_003` | Brembo (`brembo_guide_...pdf`) | **7** | `[7]` | Ruedas / Pernos | Par OEM fabricante requerido | Confirmación OEM mandatoria. No aplicar torque genérico. |
| `RAG_EXP_BREMBO_004` | Brembo (`brembo_guide_...pdf`) | **8** | `[8]` | Espesor de Disco | Cota `Min Th` grabada en canto | Verificar grabado perimetral; sustitución si espesor $\le$ Min Th. |
| `RAG_EXP_BREMBO_005` | Brembo (`brembo_guide_...pdf`) | **10** | `[10]` | Pinza y Guías | Procedimiento cualitativo | Limpieza de soportes, inspección de fuelles y deslizamiento. |
| `RAG_EXP_HYUNDAI_001` | Hyundai TSB 14-ST-002-1 | **1** | `[1, 2]` | Acoplador Flexible MDPS | Síntomas de holgura / golpeteo | Aplicable a Elantra/Sonata 2007-2015. No extrapolar a Accent/Kia. |
| `RAG_EXP_HYUNDAI_002` | Hyundai TSB 14-ST-002-1 | **3** | `[3, 4, 5]` | Desmontaje MDPS | Desconexión batería 15 min | Precaución con cable espiral y sensor de par. |
| `RAG_EXP_HYUNDAI_003` | Hyundai TSB 14-ST-002-1 | **3** | `[3, 4, 5, 14]` | Pernos Columna MDPS | `2.9 N.m`, `4.9 N.m`, `9.8-13.7 N.m`, `17.7-19.6 N.m`, `44.1-49.0 N.m` | Torques exactos verificados en Págs. 3, 4, 5 y 14. |
| `RAG_EXP_HYUNDAI_004` | Hyundai TSB 14-ST-002-1 | **12** | `[12, 13]` | Calibración ASP / Sensor Ángulo | Calibración con escáner OEM | Calibración de cero en superficie plana tras centrado de volante. |
| `RAG_EXP_KIA_001` | Kia TSB CHA060 | **1** | `[1, 2]` | Acoplador Flexible C-MDPS | Diagnóstico de holgura | Aplicable a Kia Soul, Optima, Forte, Rio (2010-2015). |
| `RAG_EXP_KIA_002` | Kia TSB CHA060 | **3** | `[3, 4]` | Sustitución Acoplador | Reemplazo físico de estrella | Retirar virutas del engranaje; verificar asiento hermético. |
| `RAG_EXP_KIA_003` | Kia TSB CHA060 | **5** | `[5, 6]` | Calibración GDS / Sensor C-MDPS | Reseteo valores adaptativos | Procedimiento diagnóstico asistido con herramienta oficial GDS. |
| `RAG_EXP_LASER_001` | Laser Tools 5524 | **1** | `[1, 2]` | Detector Fuga Bloque Motor | Viro de reactivo (azul a verde/amarillo) | **C01:** Extracción de tapón exclusivamente en frío. Prohibido en caliente. |
| `RAG_EXP_LASER_002` | Laser Tools 5524 | **2** | `[2]` | Retención de Presión y Válvula | Monitoreo visual de burbujeo | Asegurar cono de goma hermético para evitar falsos positivos. |
| `RAG_EXP_PICO_001` | Pico Technology WPS500X | **8** | `[8]` | Rango 1 Transductor | `-15 a +500 psi` (`-1 a +34.5 bar`) | Compresión de cilindro y arranque de motor. |
| `RAG_EXP_PICO_002` | Pico Technology WPS500X | **9** | `[9]` | Rango 2 Transductor | `-15 a +50 psi` (`-1 a +3.45 bar`) | Presión de combustible y contrapresión de escape. |
| `RAG_EXP_PICO_003` | Pico Technology WPS500X | **10** | `[10]` | Rango 3 Transductor | `-5 a +5 psi` (`-0.34 a +0.34 bar`) | Vacío de admisión y pulsos de cárter. |

---

## 3. Manifiesto Reproducible de Hashes Criptográficos (SHA-256)

El archivo formal `manifiesto_reproducible_rag03f.json` ha sido emitido en `machine_learning/rag/experimentos/rag03c/manifiesto_reproducible_rag03f.json` con los siguientes identificadores unívocos:

### A. PDFs Oficiales Autorizados
| Archivo PDF | Tamaño (Bytes) | Hash SHA-256 |
| :--- | :---: | :--- |
| `brembo_guide_brake_disc_diagnostics.pdf` | 1,198,416 | `ae78db3748db9d2c62a5a885d84056d880a2018a00d90074d637c5b060bab9a1` |
| `hyundai_tsb_mdps_flexible_coupling_replacement.pdf` | 3,159,170 | `3b051b41ae128a2a971f103d8908bc99f1be9720b1d4df5b2699ab8a3967d282` |
| `kia_tsb_cmdps_steering_column_repair.pdf` | 810,480 | `deded09b3e1ecfea115faf2f2c0171a087056c1873f2cd187b2928b3ffa8d0b9` |
| `laser_5524_instrucciones_es.pdf` | 2,291,603 | `513d6c527cc661e92503c7c35fb3c85c981e4af6726ec3bfb56a99e66840b63d` |
| `pico_wps500x_pressure_transducer_manual.pdf` | 390,612 | `3de1537817f51acb803cc77a79ed85a2bb044d2438a6dd4cd12fcb28227af678` |

### B. Artefactos del Paquete Experimental Reconstruido
| Artefacto | Tamaño (Bytes) | Hash SHA-256 |
| :--- | :---: | :--- |
| `fragmentos_data.py` | 17,998 | `f73e5bf0d41872dfd9f826353d9e843ea3f60f089aa14bc8a46f48ea3b9e4ec3` |
| `ejecutar_experimento_rag03c.py` | 14,037 | `ba6f45e7e604f5ca669528f8f01b17d59828236df7a36cb7605d8ce9f836f3ea` |
| `corpus_A_original_239.json` | 399,743 | `4045f28a21ee03c800ea65fe5a6f25cb7eafeffdf934f27521e8d69781604925` |
| `corpus_B_experimental.json` | 446,952 | `585fcba7f96c342f1cf44be495d46816fa8a892b153ff29a14c6e938fcf861ff` |
| `fragmentos_nuevos_5pdfs.json` | 23,281 | `0ee9851fb33aa4a4ca01878d0f1883d29d3b4eb82685c21ec13327d92cc309be` |
| `vectorizador_test_B.joblib` | 741,438 | `e4348a287c9bc3533860bb481fb2b75713ddc76943801f46f428c04ec56ea5e3` |
| `indice_faiss_test_B.index` | 36,086,189 | `9b36077ff0a6f874fa77e2338dbd4c4f34657159ba518173663aebe85e54d3f5` |
| `test_rag03f_agente2_compatibilidad.py` | 16,846 | `cf7d722d57ccf72671b569502a5cf38890e7a2df25983733df6ce64639e7c53e` |

---

## 4. Resultados de Pruebas Unitarias e Integración (10/10 PASSED)

Se ejecutó la suite de compatibilidad en el worktree aislado obteniendo un resultado 100% limpio:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\scratch\rag03c3-worktree
collected 10 items

test_rag03f_agente2_compatibilidad.py::test_fase1_integridad_hashes_5_pdfs PASSED [ 10%]
test_rag03f_agente2_compatibilidad.py::test_fase2_normalizacion_metadatos_17_fragmentos PASSED [ 20%]
test_rag03f_agente2_compatibilidad.py::test_fase2_verificacion_remediacion_c01_y_a08 PASSED [ 30%]
test_rag03f_agente2_compatibilidad.py::test_fase3_compatibilidad_contrato_agente1_todos_los_fragmentos PASSED [ 40%]
test_rag03f_agente2_compatibilidad.py::test_fase3_dictaminar_candidatos_con_corpus_no_validado PASSED [ 50%]
test_rag03f_agente2_compatibilidad.py::test_fase4_casos_documentacion_incompatible PASSED [ 60%]
test_rag03f_agente2_compatibilidad.py::test_fase4_datos_oem_ausentes_no_inventan_cifras PASSED [ 70%]
test_rag03f_agente2_compatibilidad.py::test_fase4_fuentes_con_varias_paginas PASSED [ 80%]
test_rag03f_agente2_compatibilidad.py::test_fase5_coherencia_vectorial_faiss_vs_tfidf PASSED [ 90%]
test_rag03f_agente2_compatibilidad.py::test_fase6_preservacion_modelos_canonicos_v1 PASSED [100%]

======================== 10 passed, 1 warning in 2.46s ========================
```

---

## 5. Declaración de Cumplimiento de Restricciones

- **Aislamiento Estricto:** Todo el trabajo se realizó en el worktree `scratch/rag03c3-worktree/` bajo la rama `feat/rag03c3-remediacion-corpus-trazable`.
- **Inalterabilidad de Otros Agentes:** No se modificó ningún archivo perteneciente al Agente 1 ni al Agente 3.
- **Modelos Canónicos Congelados:** Los índices y vectorizadores de producción `v1` permanecieron intactos, con verificación criptográfica SHA-256.
- **Gobernanza:** `corpus_validado=False` se mantiene activo en todo el sistema.
- **Operaciones Git:** Cero despliegues a VPS, cero pushes a ramas remotas y cero fusiones a `main`.

---
*Fin del informe RAG-03F Agente 2.*
