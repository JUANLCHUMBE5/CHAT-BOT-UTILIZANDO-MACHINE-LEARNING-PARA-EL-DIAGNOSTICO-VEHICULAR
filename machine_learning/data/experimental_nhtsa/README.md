# Datos Experimentales NHTSA (National Highway Traffic Safety Administration)

## 1. Origen y Contexto de los Datos
- **Fuente Oficial**: Banco Documental Público NHTSA (EE.UU.).
- **Períodos procesados**: 2020-2024 y 2025-2026.
- **Fecha de procesamiento**: 2026-09-25.
- **Carpetas de origen**:
  - `COMPLAINTS_RECEIVED_2020-2024` y `COMPLAINTS_RECEIVED_2025-2026`
  - `TSBS_RECEIVED_2020-2024` y `TSBS_RECEIVED_2025-2026`

## 2. Métricas de Registros Procesados
- **Quejas de consumidores (NHTSA Complaints)**:
  - Total leídas: `616,217`
  - Total conservadas tras filtrado técnico: `386,786`
  - Descartadas: `229,431`
- **Boletines de Servicio Técnico (NHTSA TSBs)**:
  - Total leídos: `1,811,858`
  - Total conservados tras filtrado técnico: `1,811,139`
  - Descartados: `719`

## 3. Política de Privacidad y Eliminación de Identificadores (PII)
Se aplicó una purga estricta en streaming. Los siguientes campos fueron **completamente eliminados**:
- VIN (Vehicle Identification Number)
- Ciudad y Estado de residencia del usuario
- Número de reporte ODI (Office of Defects Investigation)
- Nombres, teléfonos y correos electrónicos (redactados por regex en el cuerpo narrativo)
- Ningún dato de carácter personal está presente en los archivos `.jsonl`.

## 4. Estado de los Datos y Advertencias Metodológicas
- **Quejas NO son diagnósticos confirmados**:
  - Cada queja tiene `label: null` y `label_status: "needs_mechanical_review"`.
  - La descripción del propietario es subjetiva y nunca debe asumirse como ground truth hasta que un mecánico automotriz calificado la valide físicamente.
  - `content_type` prioriza descripciones con síntomas y mantiene campañas o reclamos administrativos fuera del lote inicial de revisión; no asigna una falla.
- **TSBs son candidatos para RAG**:
  - Solo documentos cuyo tipo es `Service Bulletin` o `Repair Instructions` conservan `rag_status: "candidate_requires_license_review"`; los demás quedan explícitamente excluidos como no procedimentales.
  - **No están indexados en FAISS**. Primero deben someterse a análisis de licencia comercial OEM, detección de duplicados y comprobación de procedimientos metrológicos.
- **Modelo Congelado Intacto**:
  - El modelo actual (Linear SVM multiclase con vectorizador TF-IDF) **NO ha sido modificado ni reentrenado**.
  - Los artefactos `.pkl`, los benchmarks de tesis y el corpus RAG oficial permanecen estrictamente inalterados.
