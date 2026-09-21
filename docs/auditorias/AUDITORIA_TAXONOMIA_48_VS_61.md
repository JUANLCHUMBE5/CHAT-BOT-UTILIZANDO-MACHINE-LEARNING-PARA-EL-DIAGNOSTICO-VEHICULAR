# Auditoría Forense de Taxonomía: 48 vs 61 Clases en CarBot

**Fecha:** 2026-09-19  
**Estado de Runtime:** **100% CONSISTENTE (61 CLASES)**  
**Dictamen:** `TAXONOMIA_VIGENTE_CONFIRMADA_61_CLASES`  

---

## 1. Hallazgo Forense y Trazabilidad Histórica

La investigación documental y de código fuente resolvió de manera definitiva el origen de ambas cifras:

1. **La cifra de 48 clases es HISTÓRICA (Fase 7 / Fase 8):**
   - En Fase 7 (modelo `2.2.0-external-audited`, registrado en `machine_learning/models/fase7_baseline/metricas_jerarquicas.json` y `metricas_modelo.json`), el sistema operaba con un catálogo cerrado de **48 clases**.
   - El inventario inicial de fuentes abiertas (`machine_learning/data/fuentes_abiertas/auditoria/cobertura_clases.csv`) fue construido tomando como referencia ese reporte histórico.

2. **La cifra de 61 clases es la VIGENTE OPERACIONAL (Fase 10 / Fase 11.6.4 / Fase 12.3 / CARBOT_PRECAMPO_FROZEN):**
   - Durante la Fase 10 (documentada en `AUDITORIA_TAXONOMIA_61_FASE10.csv`), la taxonomía se expandió técnicamente con **13 clases canónicas adicionales** indispensables para el parque automotor moderno:
     - *Vehículos Híbridos / Eléctricos (EV):* Batería de alto voltaje, inversor IGBT, refrigeración de batería, frenado regenerativo (4 clases).
     - *Nuevas Tecnologías de Motor:* Inyección directa GDI, actuador turbocompresor VGT en motores alemanes TSI/TFSI, correa bañada en aceite Ford 1.0 Dragon / GM Turbo, módulo de combustible FSCM/PEM, sistema Flex alcohol/etanol, filtro DPF/FAP y AdBlue DEF Euro 5/6 (6 clases).
     - *Sistemas Neumáticos y Carrocería Pesada:* Fuga de aire/frenos neumáticos, secador APS camiones, actuador Maxi-Brake (3 clases).
   - **Total exacto: 48 + 13 = 61 clases canónicas.**

## 2. Matriz de Coherencia Criptográfica y de Runtime

| Fuente / Componente | Ruta Relativa | Número de Clases | Fecha / Fase | Estado | Interpretación |
|---|---|---|---|---|---|
| **Linear SVM Congelado** | `machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl` | **61** | Fase 10 / 11.6 | ✅ VIGENTE | Modelo en producción predice exactamente 61 clases. |
| **Taxonomía Backend** | `backend/src/core/diagnostico/taxonomia_sistemas.py` | **61** | Fase 10 / 11.6 | ✅ VIGENTE | Diccionario `TAXONOMIA_MACRO_SISTEMAS` define 61 clases en 7 sistemas. |
| **Dataset C1 Productivo** | `machine_learning/data/fase10/train10_v1_1_macrofix.csv` | **61** | Fase 10 | ✅ VIGENTE | Dataset base de entrenamiento tiene 61 clases. |
| **Banco Ciego Oficial** | `machine_learning/data/fase10/test10_fase10_blind_v1.csv` | **61** | Fase 10 | ✅ VIGENTE | 366 muestras balanceadas (6 por clase para las 61 clases). |
| **Auditoría Formal Fase 10** | `machine_learning/data/fase10/auditoria_etapa31/AUDITORIA_TAXONOMIA_61_FASE10.csv` | **61** | Fase 10 | ✅ VIGENTE | Catálogo maestro de 61 clases auditadas 1-a-1. |
| **Reporte Métricas Fase 7** | `machine_learning/models/fase7_baseline/metricas_jerarquicas.json` | **48** | Fase 7 | ⚠️ HISTÓRICO | Versión previa obsoleta anterior a la incorporación de EV/GDI/Camiones. |
| **Auditoría Open Data Inicial** | `machine_learning/data/fuentes_abiertas/auditoria/cobertura_clases.csv` | **48** | Fase 8 | ⚠️ HISTÓRICO | Reporte preliminar basado en la versión antigua de 48 clases. |

## 3. Conclusión y Decisión Metodológica

- **Inconsistencia en Runtime:** **NINGUNA (0% de discrepancia)**. El modelo, el vectorizador, el backend, el dataset de entrenamiento y el banco de evaluación operan de forma 100% sincrónica sobre las **61 clases**.
- **Decisión Operacional:** El experimento V2.1 se ejecutará de forma exclusiva y rigurosa sobre las **61 clases canónicas**, asegurando total comparabilidad con el baseline congelado.
