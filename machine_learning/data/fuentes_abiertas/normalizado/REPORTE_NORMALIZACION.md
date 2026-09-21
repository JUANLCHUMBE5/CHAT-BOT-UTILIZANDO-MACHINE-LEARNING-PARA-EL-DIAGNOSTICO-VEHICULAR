# Reporte de Normalización y Creación de Capa Canónica

**Fecha de ejecución:** 2026-09-19  
**Ubicación:** `machine_learning/data/fuentes_abiertas/normalizado/`  
**Directrices aplicadas:** [AGENTS.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AGENTS.md) (Reglas 1, 2 y 6).

---

## 1. Métricas Globales de la Capa Normalizada

| Métrica | Valor | Descripción |
|---|---|---|
| **Registros Originales Totales Evaluados** | **82947** | Suma bruta de todas las fuentes sin deduplicar |
| **Registros Normalizados Finales** | **19929** | Esquema canónico 26 campos |
| **Duplicados Cruzados Absorbidos** | **4449** | DTCs coincidentes entre OBDex, Wal33D y mytrile |
| **Registros Incompletos / Descartados** | **320** | Registros sin síntoma ni causa (filtrados) |
| **Fuentes Originales Modificadas** | **0 (READ-ONLY ESTRICTO)** | Ningún archivo original fue alterado |

---

## 2. Clasificación por Uso Recomendado (`recommended_use`)

| Valor de `recommended_use` | Cantidad | Porcentaje | Propósito en CarBot |
|---|---|---|---|
| **RAG** | **5073** | 25.5% | Procedimientos, causas raíz y flujogramas para base vectorial |
| **DTC** | **14356** | 72.0% | Base de definiciones y lookup rápido OBD-II |
| **TELEMETRY** | **500** | 2.5% | Muestra de señales de sensores para validación de protocolo |
| **ML_CANDIDATE** | **0** | 0.0% | Se mantiene en 0 para evitar contaminación antes de la auditoría |
| **DO_NOT_USE** | **0** | 0.0% | Datos irrelevantes excluidos antes de la capa canónica |

---

## 3. Distribución por Fuente Canónica

| Fuente | Registros Canónicos | Licencia | Aporte Técnico Principal |
|---|---|---|---|
| **OBDex** | **4654** | CC0 1.0 | 4,654 códigos enriquecidos con causas y componentes |
| **DTC Database (Wal33D)** | **14356** | MIT | Códigos específicos por fabricante (Toyota, Nissan, etc.) |
| **obd-trouble-codes (mytrile)** | **0** | MIT | Códigos universales complementarios |
| **MechanicDB Public** | **320** | ODbL | Procedimientos de taller ordenados por eficacia |
| **Automotive Faults (Zenodo)** | **99** | CC BY 4.0 | Pasos diagnósticos y fallas de componentes físicos |
| **EngineFaultDB** | **500** | Académica | Telemetría de sensores en régimen de falla |

---

## 4. Clasificación por Motorización (Combustible)

| Combustible Detectado | Cantidad | Observación Metodológica |
|---|---|---|
| **GASOLINA** | **970** | Exclusivos para motores de encendido por chispa |
| **DIESEL** | **229** | Exclusivos para motores Common Rail / Diésel |
| **AMBOS / UNIVERSAL** | **18730** | Sistemas comunes (frenos, suspensión, chasis, sensores estándar) |

---

## 5. Integridad de Hashes de Producción
Se confirma que los 13 componentes de producción (`CARBOT_PRECAMPO_FROZEN`) continúan inalterados.
