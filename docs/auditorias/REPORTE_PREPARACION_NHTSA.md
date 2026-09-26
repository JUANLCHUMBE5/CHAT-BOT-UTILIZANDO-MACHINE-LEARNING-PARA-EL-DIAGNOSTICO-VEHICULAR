# Reporte de Auditoría: Preparación y Filtrado de Datos NHTSA (2020–2026)

**Fecha de ejecución**: 2026-09-25 22:03:31  
**Directorio experimental**: `machine_learning/data/experimental_nhtsa/`  
**Estado metodológico**: Aislamiento estricto (Modelo congelado intacto, sin indexación RAG).

---

## 1. Cantidad de Archivos Fuente Leídos
Se procesaron **4 archivos TSV** mediante lectura por streaming (búfer de línea, codificación UTF-8):
- `COMPLAINTS_RECEIVED_2020-2024.txt` (311.56 MB)
- `COMPLAINTS_RECEIVED_2025-2026.txt` (170.84 MB)
- `TSBS_RECEIVED_2020-2024.txt` (819.71 MB)
- `TSBS_RECEIVED_2025-2026.txt` (372.79 MB)

---

## 2. Resumen General de Registros y Filtrado Técnico

| Categoría | Total Originales | Total Filtrados (Conservados) | Registros Descartados | Tasa de Retención |
| :--- | :--- | :--- | :--- | :--- |
| **Quejas NHTSA (Complaints)** | 616,217 | 386,786 | 229,431 | 62.77% |
| **Boletines Técnicos (TSBs)** | 1,811,858 | 1,811,139 | 719 | 99.96% |
| **TOTAL CONSOLIDADO** | **2,428,075** | **2,197,925** | **230,150** | **90.52%** |

Control de estructura: se excluyeron **36 filas** cuya narrativa contenía el marcador de una segunda queja ODI. Se descartaron porque no es posible separar registros fusionados sin alterar la evidencia fuente.

---

## 3. Conteo de Registros por Sistema Vehicular

Distribución exacta de los registros conservados según los 8 sistemas vehiculares requeridos:

| Sistema Vehicular | Quejas (Complaints) | Boletines (TSB) | Total Sistema |
| :--- | :--- | :--- | :--- |
| **frenos** | 42,847 | 81,469 | **124,316** |
| **motor** | 134,523 | 545,042 | **679,565** |
| **transmisión** | 61,695 | 194,872 | **256,567** |
| **suspensión** | 29,523 | 173,351 | **202,874** |
| **dirección** | 38,929 | 61,968 | **100,897** |
| **climatización** | 612 | 19,321 | **19,933** |
| **eléctrico** | 77,492 | 716,425 | **793,917** |
| **DPF/diésel** | 1,165 | 17,929 | **19,094** |

---

## 4. Auditoría de Privacidad y Verificación de Ausencia de VIN
Se verificó formalmente la exclusión de VIN, ciudad, estado, ODI ID y datos personales:
- En las quejas: columnas de identificación omitidas; campos numéricos y ubicaciones suprimidas.
- En el texto descriptivo: expresiones regulares de 17 caracteres alfanuméricos enmascaradas con `[VIN_REDACTED]`.
- En los TSB: exclusión de metadatos administrativos.

### Auditoría Automatizada Completa (todos los registros generados):
- **`nhtsa_complaints_unlabeled.jsonl`**:
  - Muestra evaluada: 386,786 registros
  - Claves 'vin' encontradas en JSON: `0`
  - VINs expuestos no redactados en texto: `0`
  - Direcciones postales expuestas en texto: `0`
  - Estado: **LIMPIO (0 VINs/direcciones)**
- **`nhtsa_tsbs_rag_candidates.jsonl`**:
  - Muestra evaluada: 1,811,139 registros
  - Claves 'vin' encontradas en JSON: `0`
  - VINs expuestos no redactados en texto: `0`
  - Direcciones postales expuestas en texto: `0`
  - Estado: **LIMPIO (0 VINs/direcciones)**

---

## 5. Comprobación de Integridad de los Modelos Congelados
Verificación criptográfica SHA-256 de los artefactos oficiales del proyecto antes y después de la ejecución:

| Artefacto Congelado | Hash SHA-256 Pre-Ejecución | Hash SHA-256 Post-Ejecución | Estado de Integridad |
| :--- | :--- | :--- | :--- |
| `modelo_diagnostico.pkl` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | ✅ INTACTO |
| `modelo_sistema.pkl` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | ✅ INTACTO |
| `vectorizador_tfidf.pkl` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | ✅ INTACTO |
| `modelo_diagnostico.pkl` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | `3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd` | ✅ INTACTO |
| `modelo_sistema.pkl` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | `22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27` | ✅ INTACTO |
| `vectorizador_tfidf.pkl` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | `8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104` | ✅ INTACTO |
| `dataset_sintomas.csv` | `0e2ba71de7fe6792c98c53b45971f9bc007d0ad4965cc8c7f9c4f13c69163648` | `0e2ba71de7fe6792c98c53b45971f9bc007d0ad4965cc8c7f9c4f13c69163648` | ✅ INTACTO |

**Conclusión de Integridad**: ✅ Todos los modelos congelados, vectorizadores TF-IDF y datasets oficiales permanecen 100% IDÉNTICOS E INTACTOS.

---

## 6. Hash SHA-256 de los Archivos Generados

| Archivo Generado | Hash SHA-256 Oficial |
| :--- | :--- |
| `nhtsa_complaints_unlabeled.jsonl` | `fc687e3360cac87653ca0b25e5ef0285f93e4d57e4112e87819a195962c3e4a2` |
| `nhtsa_tsbs_rag_candidates.jsonl` | `f950aff9ea1f24217ee002c0c1a5af648ab358c595980af90acf9898344ddd6a` |

---

## 7. Próximos Pasos y Condiciones Metodológicas
1. **Quejas (`nhtsa_complaints_unlabeled.jsonl`)**:
   - Requieren muestreo y revisión técnica por un mecánico automotriz (`needs_mechanical_review`) antes de cualquier asignación de etiqueta ground truth.
   - Prohibido su uso directo para reentrenar el Linear SVM actual sin validación presencial de taller.
2. **TSBs (`nhtsa_tsbs_rag_candidates.jsonl`)**:
   - Requieren desduplicación, verificación de licenciamiento y filtrado de contenido metrológico antes de considerar su indexación en FAISS.
