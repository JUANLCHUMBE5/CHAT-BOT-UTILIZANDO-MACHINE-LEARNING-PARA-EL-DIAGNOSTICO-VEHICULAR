# Reporte Forense de Deduplicación y Anti-Leakage — CarBot V2

**Fecha:** 2026-09-19  
**Norma Operacional:** Regla 6 de Deduplicación y Blindaje de Datos Externos  

## 1. Métricas de Deduplicación Global

- **Registros Mapeados Iniciales:** 75,843
- **Duplicados Exactos Eliminados:** 55,196
- **Duplicados de Campañas / Near-Duplicates Eliminados:** 0
- **Registros Únicos Conservados:** 20,647 (27.2%)

## 2. Aislamiento Cross-Source de DTCs y Documentación Técnica

- **Principio aplicado:** OBDex + DTC Database + obd-trouble-codes describiendo el mismo código DTC no generan múltiples ejemplos ML independientes.
- **Tratamiento:** Se indexan en `RAG_TECHNICAL` preservando metadata unificada y eliminando sobrepeso artificial en el prior de clasificación.

## 3. Garantía Anti-Data-Leakage

- Todo texto normalizado con coincidencia en los casos piloto históricos ha sido segregado a `EVALUATION_ONLY`.
- Las particiones TRAIN/VALIDATION/TEST conservan agrupamiento estricto por `source_record_id` y documento.
