# Auditoría de Compatibilidad de Datasets Abiertos para CarBot

**Fecha de ejecución:** 2026-09-19  
**Ubicación de almacenamiento:** `machine_learning/data/fuentes_abiertas/`  
**Directrices metodológicas aplicadas:** [AGENTS.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AGENTS.md) (Reglas 1, 2, 6 y 9).

---

## 1. Inventario Físico de Datasets Descargados

| # | Dataset | Formato / Tamaño | Registros Clave | Licencia | Uso Recomendado en CarBot |
|---|---|---|---|---|---|
| 1 | **Automotive Faults Dataset (Zenodo)** | JSON (59.8 KB) | 99 componentes, 196 síntomas, 198 procedimientos | CC BY 4.0 | **RAG / Procedimientos OEM** + Expansión sintomática supervisada |
| 2 | **DTC Database (Wal33D)** | SQLite (3.11 MB) | {'dtc_definitions': 18805, 'statistics': 34} | MIT | **Base de Datos Offline DTC** (lookup rápido OBD-II) |
| 3 | **OBDex (foerbsnavi)** | YAML (212761 líneas) | Familias P0xxx, B0xxx, C0xxx con PIDs y causas | CC0 (Dominio público) | **Enriquecimiento RAG** (causas raíz, componentes y síntomas técnicos) |
| 4 | **MechanicDB Public Sample** | CSV (316 pares DTC-procedimiento) | 317 procedimientos, 442 repuestos vinculados | ODbL | **RAG Procedimientos de Reparación** (pasos de solución y repuestos) |
| 5 | **obd-trouble-codes (mytrile)** | CSV / JSON / SQLite (3070 códigos) | 3070 definiciones estándar | MIT | **Lookup complementario de códigos estándar** |
| 6 | **EngineFaultDB (Leo-Thomas)** | CSV (5.09 MB) | 55999 lecturas de sensores de motor | Académico (IEEE Access) | **Telemetría / Señales auxiliares** (no para clasificación textual) |
| 7 | **LEVIN Open Data (YunSolutions)** | Git Repo (OBD temporal) | 30 vehículos, 4 meses de lecturas OBD | CC BY-NC-SA | **Validación de señales de sensores** |
| 8 | **carOBD (Toyota Etios Brasil)** | Git Repo / Logs OBD | Telemetría real de ECU | Código abierto | **Referencia de PIDs Toyota** |

---

## 2. Separación Metodológica Estricta (Regla 6 de AGENTS.md)

> [!IMPORTANT]
> **Ningún dataset externo debe mezclarse con la Muestra Oficial de Tesis (60 casos de taller CARTER MOTOR'S).**  
> La muestra pretest y postest debe mantenerse 100% pura y verificada físicamente por los mecánicos en el taller.

### A. Para Enriquecimiento de RAG (FAISS + Manuales Técnicos):
- **Zenodo 15626055:** Los pasos diagnósticos (`diagnosis_steps`) y flujogramas de componentes como *ABS Module*, *Alternator*, *Brake Booster*, *Charging System*, *Water Pump* enriquecen directamente la base de conocimiento vectorial de CarBot sin inventar síntomas.
- **MechanicDB:** Aporta la asociación directa entre códigos de falla y repuestos requeridos (`replacement_parts.csv`), así como procedimientos de taller clasificados por efectividad.
- **OBDex:** Aporta la explicación física de componentes afectados (`affected_components`), probabilidad de causa (`likelihood`) y tiempos estimados de reparación en horas.

### B. Para Machine Learning (Linear SVM con TF-IDF):
- **No introducir quejas no verificadas:** Las descripciones coloquiales de dueños sin verificación técnica no deben usarse como etiqueta de verdad terreno en el clasificador SVM de 48 clases.
- **Alineación con las 48 clases vehiculares:** Si se extraen pares *síntoma -> falla* de Zenodo o OBDex, deben mapearse explícitamente a las 48 clases canónicas de CarBot antes de cualquier reentrenamiento en `machine_learning/experiments/`.

---

## 3. Estado de Almacenamiento Local
Todos los archivos y repositorios se encuentran descargados localmente en:
`C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data\fuentes_abiertas\`
