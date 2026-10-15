# Auditoría de Compatibilidad de Datasets Abiertos para CarBot

**Fecha de ejecución:** 2026-10-03
**Ubicación de almacenamiento:** `machine_learning/data/fuentes_abiertas/`  
**Directrices metodológicas aplicadas:** [AGENTS.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AGENTS.md) (Reglas 1, 2, 6 y 9).

---

## 1. Inventario Físico de Datasets Descargados

| # | Dataset | Formato / Tamaño | Registros Clave | Licencia | Uso Recomendado en CarBot |
|---|---|---|---|---|---|
| 1 | **Automotive Faults Dataset (Zenodo)** | JSON (57.5 KB) | 99 componentes, 196 síntomas, 198 procedimientos | CC BY 4.0 | DISPONIBLE — RAG / procedimientos candidatos |
| 2 | **DTC Database (Wal33D)** | SQLite (3.11 MB) | {'dtc_definitions': 18805, 'statistics': 34} | MIT | DISPONIBLE — lookup offline DTC |
| 3 | **OBDex (foerbsnavi)** | YAML (212761 líneas) | Familias P0xxx, B0xxx, C0xxx con PIDs y causas | CC0 (dominio público) | DISPONIBLE — enriquecimiento RAG candidato |
| 4 | **MechanicDB Public Sample** | CSV (NO DESCARGADO pares DTC-procedimiento) | NO DESCARGADO procedimientos, NO DESCARGADO repuestos | ODbL | NO DESCARGADO — requiere revisión de licencia |
| 5 | **obd-trouble-codes (mytrile)** | CSV / JSON / SQLite (NO DESCARGADO códigos) | NO DESCARGADO definiciones estándar | MIT | NO DESCARGADO — lookup complementario |
| 6 | **EngineFaultDB (Leo-Thomas)** | CSV (NO DESCARGADO MB) | NO DESCARGADO lecturas de sensores | Académico | NO DESCARGADO — telemetría auxiliar, no clasificación textual |

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
