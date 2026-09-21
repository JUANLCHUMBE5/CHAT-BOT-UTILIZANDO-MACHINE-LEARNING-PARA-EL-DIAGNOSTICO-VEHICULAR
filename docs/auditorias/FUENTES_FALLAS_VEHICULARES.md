# Inventario Técnico y Licencias: Banco Documental Perú + NHTSA

**Fecha de Generación:** 2026-09-19  
**Directrices de Tesis:** [AGENTS.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AGENTS.md) (Regla 1, 2 y 9).

---

## 1. Inventario de Fuentes Primarias Utilizadas

| Fuente | URL Oficial | Cobertura Temporal | Registros | Licencia / Condiciones | Hash SHA-256 (Archivo Descargado) |
|---|---|---|---|---|---|
| **INDECOPI (Alertas Raw)** | `https://www.alertasdeconsumo.gob.pe/` | 2012–2026 | 914 alertas | Información Pública de Seguridad (Perú) | `3ece474bec480ad7ae103c09c697a5dc96acc72feabd6f850d2003b06694b9a6` |
| **INDECOPI (Detalle Consolidado)** | `https://servicios.indecopi.gob.pe/alerta-consumo-api/` | 2012–2026 | 914 alertas | Información Pública de Seguridad (Perú) | `e169abe47c4edcf1c017f0590072f067dd7dbf93d5210061edf2a102c4532aec` |
| **NHTSA Recalls Pre-2010** | `https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_PRE_2010.zip` | 1966–2009 | 81,715 | US Public Domain (Government Work) | `3c185d43a9948e271ef6aec7de8a8195f7567ebd606f1d521f964c54c344d1c8` |
| **NHTSA Recalls Post-2010** | `https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip` | 2010–2026 | 245,336 | US Public Domain (Government Work) | `57418cb9a91462aa300595b73c73ff4d3b9a57473bd5e8a81600c4ff965bf8aa` |
| **NHTSA Complaints 2025–2026** | `https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2025-2026.zip` | 2025–2026 | 195,389 | US Public Domain (Government Work) | `a0ee79ddd1fff2bda1ab86941c6143dc06899cd62bda1c0a3a05876623cf2ead` |
| **NHTSA Complaints 2020–2024** | `https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip` | 2020–2024 | 418,884 | US Public Domain (Government Work) | `63ac4efd021d41292c38bab87afc792dcc3b56475729ea81a1b61c67a35b0c0b` |
| **NHTSA Complaints 2015–2019** | `https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2015-2019.zip` | 2015–2019 | 489,809 | US Public Domain (Government Work) | `e5e989aed1bae5630d86d17b6738d5a5d9a0619b975bafcab1b8ea012c7b01aa` |
| **NHTSA Complaints 2010–2014** | `https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2010-2014.zip` | 2010–2014 | 392,970 | US Public Domain (Government Work) | `fd9c4d3e741e72b249335c0e23150efcf12bef966c68b1a0b065ccefda08831c` |
| **NHTSA Complaints 2005–2009** | `https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2005-2009.zip` | 2005–2009 | 236,170 | US Public Domain (Government Work) | `e2aaa1064743e0c259f70cc43524b3c2fc437f9574ba4972331688c40872e6af` |
| **NHTSA Complaints 2000–2004** | `https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2000-2004.zip` | 2000–2004 | 321,349 | US Public Domain (Government Work) | `47e29a88c4e129e9fc30967794e264e1680a16bec6c946902b51c18c71493533` |

---

## 2. Archivos Canónicos Normalizados Generados

| Archivo Generado | Ubicación | Formato | Registros | Uso Permitido |
|---|---|---|---|---|
| `PERU_VEHICLE_FAILURES.jsonl` | `machine_learning/data/fuentes_abiertas/fallas_vehiculares/normalizado/` | JSONL | 914 | RAG / Respaldo de Defectos en Perú |
| `PERU_VEHICLE_FAILURES.csv` | `machine_learning/data/fuentes_abiertas/fallas_vehiculares/normalizado/` | CSV | 914 | Auditoría y Análisis Tabular |
| `NHTSA_RECALLS_2000_2026.jsonl` | `machine_learning/data/fuentes_abiertas/fallas_vehiculares/normalizado/` | JSONL | 178,556 | RAG / Causas de Ingeniería OEM |
| `NHTSA_VEHICLE_COMPLAINTS_2000_2026.jsonl` | `machine_learning/data/fuentes_abiertas/fallas_vehiculares/normalizado/` | JSONL | 210,000 | Vocabulario Sintomático (No Ground Truth) |
| `VEHICLE_FAILURE_KNOWLEDGE_2000_2026.jsonl` | `machine_learning/data/fuentes_abiertas/fallas_vehiculares/normalizado/` | JSONL | 389,470 | Banco Maestro Unificado |
| `VOCABULARIO_SINTOMAS_REALES.csv` | `machine_learning/data/fuentes_abiertas/fallas_vehiculares/normalizado/` | CSV | 16 clústeres | Expansión Semántica y Diccionario |
| `COBERTURA_48_CLASES_PERU_NHTSA.csv` | `machine_learning/data/fuentes_abiertas/fallas_vehiculares/normalizado/` | CSV | 48 clases | Matriz de Cobertura CarBot |

---

## 3. Condiciones de Uso y Metodología de Tesis
1. Los datos de **INDECOPI** son públicos de acuerdo con la Ley de Transparencia del Perú y se utilizan estrictamente con fines de investigación académica de seguridad automotriz.
2. Los datos de **NHTSA** son de dominio público según la normativa federal de los Estados Unidos (17 U.S.C. § 105).
3. **Invariante de Tesis:** Ningún dato descargado ha sido insertado en las tablas oficiales pretest/posttest de CARTER MOTOR'S (`CARBOT_PRECAMPO_FROZEN`).
