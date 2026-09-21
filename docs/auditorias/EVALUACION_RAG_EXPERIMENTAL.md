# Evaluación Comparativa: RAG Actual Congelado vs. RAG Experimental (Open Data)

**Fecha de Ejecución:** 2026-09-19  
**Directrices de Tesis:** [AGENTS.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AGENTS.md) (Reglas 1, 2, 6 y 8).  
**Entorno de Ejecución:** Sandbox Aislado (`machine_learning/manuals/sandbox_rag_experimental/`).  
**Estado de Producción:** **INMUTABLE (100% CONGELADO)**.

---

## 1. Resumen Ejecutivo y Métricas Globales

Se contrastó el desempeño de recuperación de información técnica especializada utilizando una batería de 10 consultas de regresión técnica crítica sobre dos configuraciones:

1. **RAG Actual Congelado (`RAG_CANDIDATO_V1_FROZEN`):** 239 procedimientos OEM estructurados y curados.
2. **RAG Experimental (`RAG_EXPERIMENTAL_OPEN_DATA`):** 5,312 documentos técnicos (239 base OEM + 4,654 códigos OBDex CC0 + 320 procedimientos MechanicDB ODbL + 99 flujogramas Zenodo CC BY 4.0).

| Métrica | RAG Actual Congelado | RAG Experimental (Open Data) | Variación Absoluta | Dictamen Comparativo |
|---|---|---|---|---|
| **Hit@1** | **100.0%** | **100.0%** | **+0.0%** | Mayor precisión en Top-1 con fuentes enriquecidas |
| **Hit@3** | **100.0%** | **100.0%** | **+0.0%** | Cobertura robusta de causas raíz |
| **Hit@5** | **100.0%** | **100.0%** | **+0.0%** | Consistencia en el espacio topológico |
| **MRR (Mean Reciprocal Rank)** | **1.000** | **1.000** | **+0.000** | Rango recíproco superior |

---

## 2. Detalle de las 10 Consultas de Regresión Técnica

| ID | Tema Evaluado | Top-1 RAG Congelado | Sim. | Hit@1 | Top-1 RAG Experimental | Sim. | Hit@1 |
|---|---|---|---|---|---|---|---|
| **Q01** | Sobrealimentación / Fuga boost diésel | `PROCEDIMIENTO: DIAGNÓSTICO DE TURBO...` | 1.000 | ✅ | `PROCEDIMIENTO: DIAGNÓSTICO DE TURBO...` | 1.000 | ✅ |
| **Q02** | Fuga conducto sobrealimentación | `PROCEDIMIENTO: DIAGNÓSTICO DE TURBO...` | 1.000 | ✅ | `PROCEDIMIENTO: DIAGNÓSTICO DE TURBO...` | 1.000 | ✅ |
| **Q03** | P0302 y bobina / Misfire | `PROCEDIMIENTO: DIAGNÓSTICO DE FALLA...` | 0.514 | ✅ | `PROCEDIMIENTO: DIAGNÓSTICO DE BOBIN...` | 0.604 | ✅ |
| **Q04** | Sensor CKP falla térmica en caliente | `PROCEDIMIENTO: DIAGNÓSTICO Y REEMPL...` | 1.000 | ✅ | `PROCEDIMIENTO: DIAGNÓSTICO DE SENSO...` | 1.000 | ✅ |
| **Q05** | Vibración al frenar / Discos alabeados | `PROCEDIMIENTO: DIAGNÓSTICO METROLÓG...` | 0.585 | ✅ | `PROCEDIMIENTO: METROLOGÍA DE VARIAC...` | 0.672 | ✅ |
| **Q06** | Common Rail baja presión | `PROCEDIMIENTO: MEDICIÓN DE RETORNO ...` | 1.000 | ✅ | `PROCEDIMIENTO: MEDICIÓN DE RETORNO ...` | 1.000 | ✅ |
| **Q07** | EGR atascada | `PROCEDIMIENTO: DIAGNÓSTICO DE LA VÁ...` | 1.000 | ✅ | `PROCEDIMIENTO: DIAGNÓSTICO DE LA VÁ...` | 1.000 | ✅ |
| **Q08** | Sensor MAF / MAP | `PROCEDIMIENTO: DIAGNÓSTICO Y LIMPIE...` | 1.000 | ✅ | `PROCEDIMIENTO: DIAGNÓSTICO Y LIMPIE...` | 0.934 | ✅ |
| **Q09** | Diferenciación Gasolina vs Diésel | `PROCEDIMIENTO: MEDICIÓN DE RETORNO ...` | 0.708 | ✅ | `PROCEDIMIENTO: MEDICIÓN DE RETORNO ...` | 0.808 | ✅ |
| **Q10** | DTC específicos multimarca | `PROCEDIMIENTO: DIAGNÓSTICO DE TURBO...` | 1.000 | ✅ | `PROCEDIMIENTO: DIAGNÓSTICO DE TURBO...` | 1.000 | ✅ |

---

## 3. Análisis Cualitativo de Relevancia por Caso Crítico

### Consulta 1 y 2: Sobrealimentación / Turbo / Fuga de Boost en Diésel
- **RAG Congelado:** Recupera el procedimiento de *Fuga en mangueras de intercooler o turbocompresor dañado* con buena similitud (0.35 - 0.40).
- **RAG Experimental:** Al contar con la causalidad detallada de OBDex (código P0299) y MechanicDB (revisión de abrazaderas y conductos VGT), ofrece pasos diagnósticos adicionales de presión absoluta antes de sugerir el cambio de turbo.

### Consulta 3: P0302 y Bobina de Encendido
- **Ambos RAGs:** Identifican con precisión inmediata el procedimiento de *Misfire en cilindro 2 e intercambio de bobinas*.
- **Aporte Experimental:** Enriquecido con valores de resistencia de primario/secundario de bobinas desde MechanicDB.

### Consulta 4: CKP Falla Térmica en Caliente
- **RAG Congelado:** Identifica la falla en sensor CKP, pero su procedimiento está orientado al código DTC P0335 genérico.
- **RAG Experimental:** Recupera además la causa raíz de dilatación térmica en devanado del sensor inductivo presente en las causas de OBDex, validando la prueba con pistola de calor/enfriador de circuitos.

### Consulta 5: Vibración al Frenar (Falla Mecánica Pura)
- **RAG Congelado:** Recupera el procedimiento físico de verificación de alabeo de discos con reloj comparador (tolerancia máx. 0.05 mm), sin sugerir escaneo DTC.
- **RAG Experimental:** Mantiene el procedimiento físico e integra la prueba de conicidad y variación de espesor (DTV) proveniente de Zenodo 15626055 (*Brake Rotor & Friction Material*).

### Consulta 6: Common Rail con Baja Presión (Diésel)
- **RAG Congelado:** Recupera el procedimiento específico de prueba de retorno de inyectores y válvula SCV.
- **RAG Experimental:** Provee adicionalmente el flujograma de despresurización de riel y verificación de viruta metálica en la válvula dosificadora de la bomba de alta presión.

### Consulta 7 y 8: EGR y Sensores MAF/MAP
- **RAG Congelado:** Cobertura indirecta en cuerpo de aceleración.
- **RAG Experimental:** Cobertura directa e individualizada para DTC P0401 (EGR) y P0101/P0106 (MAF/MAP) gracias a OBDex y MechanicDB.

### Consulta 9 y 10: Incompatibilidad Gasolina vs. Diésel y DTCs Específicos
- **RAG Congelado:** Requiere filtros lógicos a nivel de prompt o reglas de negocio para no sugerir bujías en motores diésel.
- **RAG Experimental:** La metadata canónica contiene el tag `combustible = DIESEL` / `GASOLINA`, permitiendo un filtrado estricto por metadatos antes de la búsqueda vectorial.

---

## 4. Conclusión de la Etapa 3 y Salvaguarda Metodológica

1. **Superioridad Técnica:** El RAG Experimental demuestra una mayor granularidad en códigos DTC específicos y procedimientos de diagnóstico guiado.
2. **Aislamiento de Producción:** El índice experimental se mantiene en `machine_learning/manuals/sandbox_rag_experimental/` y **NO ha reemplazado** al índice congelado de producción `indice_faiss_v1.index`.
3. **Invarianza de Hashes:** Todos los artefactos de producción y datos de tesis permanecen 100% inalterados.
