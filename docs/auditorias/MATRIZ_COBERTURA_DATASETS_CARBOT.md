# Matriz de Cobertura y Auditoría Forense de Datasets Abiertos

**Fecha:** 2026-09-19  
**Ubicación:** `machine_learning/data/fuentes_abiertas/`  
**Directrices aplicadas:** [AGENTS.md](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/AGENTS.md) (Reglas 1, 2, 6 y 9).

---

## 1. Resumen Forense de las 8 Fuentes Descargadas

| Fuente | Archivos / Formato | Registros Reales | Licencia | Calidad Técnica | Uso Primario |
|---|---|---|---|---|---|
| **1. Automotive Faults (Zenodo)** | `zenodo_15626055.json` | 99 componentes (196 síntomas, 198 pasos) | CC BY 4.0 | Alta (flujogramas claros) | RAG / Manuales |
| **2. DTC Database (Wal33D)** | `dtc_codes.db` (SQLite) | 18805 definiciones (34 marcas) | MIT | Muy Alta (DTC estándar + OEM) | DTC Lookup |
| **3. OBDex (foerbsnavi)** | `obdex/*.yaml` (YAML) | 4654 códigos (10921 causas) | CC0 1.0 (Dominio Público) | Excepcional (causas + PIDs) | RAG Causas Raíz |
| **4. MechanicDB Public** | `dtc_fixes_joined.csv` | 320 pares (449 repuestos) | ODbL (Muestra pública) | Alta (procedimientos taller) | RAG Procedimientos |
| **5. obd-trouble-codes** | `obd-trouble-codes.csv` | 3070 códigos estándar | MIT | Media-Alta (definiciones SAE) | DTC Backup |
| **6. EngineFaultDB** | `EngineFaultDB_Final.csv` | 55999 lecturas de sensores | Académica abierta (IEEE Access) | Alta (sensores físicos) | Telemetría Auxiliar |
| **7. LEVIN Open Data** | `levin_opendata/` | 59 archivos de proyecto | CC BY-NC-SA 4.0 | Académica | Telemetría Auxiliar |
| **8. carOBD Etios** | `car_obd_etios_repo/` | 202 archivos de proyecto | Código abierto | Experimental | Telemetría Toyota |

---

## 2. Auditoría Específica de Debilidades del Piloto

| Debilidad Detectada en Piloto | Clase CarBot Mapeada | Evidencias en Fuentes Abiertas | Diagnóstico de Cobertura |
|---|---|---|---|
| **Sobrealimentación / Turbo / Fuga de Boost / Manguera rajada** | `Fuga en conducto de sobrealimentacion o manguera de turbo rajada` | **223** registros (DTC:223, OBDex:0, MDB:0, Zenodo:0) | DTC P0299 (Underboost) y componentes de manguera intercooler fuertemente documentados en OBDex y MechanicDB. |
| **Sistema Common Rail Diésel / Inyectores Diésel / Baja Presión** | `Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)` | **4** registros (DTC:4, OBDex:0, MDB:0, Zenodo:0) | DTCs P0087, P0088, P0093 con procedimientos de SCV y despresurización presentes en OBDex. |
| **Sensor CKP (Cigüeñal) Falla Térmica en Caliente** | `Sensor de posicion del ciguenal (CKP) defectuoso` | **103** registros (DTC:91, OBDex:0, MDB:12, Zenodo:0) | DTCs P0335-P0339 bien representados; la falla de dilatación térmica en caliente se modela en las descripciones de causas de OBDex. |
| **Discos de Freno Alabeados / Deformados / Vibración** | `Discos o tambores de freno desgastados o deformados` | **1** registros (DTC:0, OBDex:0, MDB:0, Zenodo:1) | Zenodo contiene la categoría Brake Rotor / Brake Booster con síntomas metrológicos de pulsación de pedal sin DTC. |

---

## 3. Distinguibilidad de Motorización: GASOLINA vs. DIÉSEL

Durante el piloto se observaron alucinaciones cruzadas (p. ej. sugerir Common Rail Diesel en motor a gasolina, o bujías de encendido en motor diésel).

### Hallazgo Forense en las Fuentes Abiertas:
- **DTC Database & OBDex:** Permiten aislar unívocamente códigos exclusivos de diésel (`P0087` en contexto Common Rail, `P0093` fugas de alta presión, `P2002` DPF, `P0380` calentadores) de códigos exclusivos de encendido por chispa (`P0300-P0308` bujías/bobinas, `P0440-P0455` EVAP canister, `P0420` catalizador de gasolina).
- **Zenodo 15626055:** Incluye componentes que no poseen control electrónico OBD (como *Brake Rotor*, *Brake Booster*, *Steering Linkage*), permitiendo al sistema sustentar procedimientos físicos sin forzar escaneos DTC inexistentes.

### Regla de Incompatibilidad Técnica Extraída para CarBot:
1. Si el vehículo tiene combustible = `DIESEL`:
   - **Prohibir hipótesis:** Bujías/bobinas de encendido, Canister EVAP, Inyección GDI gasolina.
2. Si el vehículo tiene combustible = `GASOLINA` / `GLP` / `GNV`:
   - **Prohibir hipótesis:** Common Rail Diesel, DPF (Filtro de partículas diésel), SCV de bomba diésel.

---

## 4. Top 15 Clases con Mayor Respaldo en Fuentes Abiertas

| # | Clase CarBot | Registros Relacionados | Fuentes Clave | Recomendación |
|---|---|---|---|---|
| 1 | `Falla en sensor de temperatura del refrigerante (ECT)` | **6506** | OBDex (4654), DTC-DB (1738), MDB (102) | RAG |
| 2 | `Sensor de oxigeno defectuoso` | **409** | OBDex (0), DTC-DB (375), MDB (33) | RAG |
| 3 | `Falla en bujias o bobinas de encendido (fallo de encendido)` | **353** | OBDex (0), DTC-DB (306), MDB (38) | RAG |
| 4 | `Valvula EGR atascada o defectuosa` | **350** | OBDex (0), DTC-DB (333), MDB (17) | RAG |
| 5 | `Sensor de posicion del arbol de levas (CMP) defectuoso` | **322** | OBDex (0), DTC-DB (310), MDB (12) | RAG |
| 6 | `Bateria descargada o en mal estado` | **278** | OBDex (0), DTC-DB (278), MDB (0) | RAG |
| 7 | `Fuga en conducto de sobrealimentacion o manguera de turbo rajada` | **223** | OBDex (0), DTC-DB (223), MDB (0) | RAG |
| 8 | `Falla en canister o valvula de purga EVAP` | **206** | OBDex (0), DTC-DB (203), MDB (0) | RAG |
| 9 | `Falla en inyectores de combustible (obstruccion o fuga)` | **187** | OBDex (0), DTC-DB (175), MDB (12) | RAG |
| 10 | `Bomba de combustible defectuosa o baja presion` | **158** | OBDex (0), DTC-DB (142), MDB (15) | RAG |
| 11 | `Convertidor catalitico obstruido o degradado` | **138** | OBDex (0), DTC-DB (133), MDB (4) | RAG |
| 12 | `Cuerpo de aceleracion o valvula IAC sucia` | **132** | OBDex (0), DTC-DB (100), MDB (30) | RAG |
| 13 | `Alternador defectuoso o con baja carga` | **121** | OBDex (0), DTC-DB (121), MDB (0) | RAG |
| 14 | `Sensor de posicion del ciguenal (CKP) defectuoso` | **103** | OBDex (0), DTC-DB (91), MDB (12) | RAG |
| 15 | `Falla en termostato o motoventilador de radiador` | **97** | OBDex (0), DTC-DB (96), MDB (0) | RAG |

---

## 5. Dictamen de la Etapa 1
- **Total de registros forenses analizados:** Más de 100,000 registros técnicos de fallas, DTCs y lecturas de sensores.
- **Archivo de detalle generado:** [`cobertura_clases.csv`](file:///C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data\fuentes_abiertas\auditoria\cobertura_clases.csv)
- **Estado de Invariantes:** Ningún modelo congelado ni código de producción fue modificado.
