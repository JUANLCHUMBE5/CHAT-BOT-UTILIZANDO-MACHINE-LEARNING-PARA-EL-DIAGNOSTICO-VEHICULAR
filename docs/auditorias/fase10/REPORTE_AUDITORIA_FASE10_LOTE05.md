# REPORTE DE AUDITORÍA FASE 10 — LOTE 05
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — 100% CONFORME (BLOQUEO DE ENTRENAMIENTO ACTIVO)  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_05.csv` (240 registros, 6 clases)  
**Archivo de Auditoría:** `fase10_auditoria_lote05.csv`

---

## 1. Verificación de Inmutabilidad de Fase 8.3

En estricto cumplimiento de las reglas metodológicas de la tesis, se verificó el manifiesto oficial de inmutabilidad criptográfica SHA-256 de los 19 artefactos canónicos:

- **Artefactos congelados:** 19/19
- **Hashes coincidentes:** 19/19 (100%)
- **Discrepancias:** 0
- **Modelos de producción modificados:** 0 (Ninguno)
- **Vectorizador modificado:** 0 (Ninguno)
- **RAG / FAISS modificado:** 0 (Ninguno)

---

## 2. Auditoría Estructural del Lote 05

| Parámetro Evaluado | Requisito Formal | Valor Observado | Estado |
|---|---|---|:---:|
| **Codificación de archivo** | UTF-8 estricto | UTF-8 sin BOM, decodificación limpia | **CONFORME** |
| **Total registros** | 240 registros | 240 filas | **CONFORME** |
| **Columnas requeridas** | 16 columnas específicas | 16 columnas canónicas | **CONFORME** |
| **Cobertura de clases** | 6 clases canónicas (21 a 26) | 6 clases canónicas | **CONFORME** |
| **Balance por clase** | 40 registros por clase | 40 registros por clase (exacto) | **CONFORME** |
| **Distribución por nivel** | 60 L1 / 90 L2 / 90 L3 | 60 L1 (25%) / 90 L2 (37.5%) / 90 L3 (37.5%) | **CONFORME** |
| **Balance nivel por clase** | 10 L1, 15 L2, 15 L3 | 10 L1, 15 L2, 15 L3 por cada una de las 6 clases | **CONFORME** |
| **Unicidad de IDs** | F10-L05-0001 a F10-L05-0240 | 240 IDs únicos sin colisiones | **CONFORME** |
| **Macro-Sistema** | Coincidir con `MOTOR` | 240/240 registros asignados a `MOTOR` | **CONFORME** |
| **Fuente** | `SINTETICO_IA` | 240/240 registros etiquetados `SINTETICO_IA` | **CONFORME** |

### Clases Incluidas en el Lote 05:
1. `Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)`: 40 registros (10 L1, 15 L2, 15 L3)
2. `Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)`: 40 registros (10 L1, 15 L2, 15 L3)
3. `Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)`: 40 registros (10 L1, 15 L2, 15 L3)
4. `Falla en regulador de presion de combustible o diafragma roto`: 40 registros (10 L1, 15 L2, 15 L3)
5. `Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)`: 40 registros (10 L1, 15 L2, 15 L3)
6. `Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados`: 40 registros (10 L1, 15 L2, 15 L3)

---

## 3. Auditoría de DTC y Casos Contrastivos

### A. Regla Reforzada de DTC
- **Total de registros con DTC:** 105 (43.8% del lote)
- **DTC en nivel L1:** **0** (Prohibición absoluta cumplida al 100%)
- **DTC en nivel L2:** **45**
- **DTC en nivel L3:** **60**
- **Validación Sintáctica Regex (`^[PBCU][0-9A-Fa-f]{4}$`):** 100% de los códigos cumplen el estándar SAE J2012.
- **Validación Semántica / Técnica:** 100% compatibles con la falla descrita y su contexto mecánico.
- **DTC por clase:**
  - Clase 21 (CKP/CMP): 19 casos (`P0016`, `P0017`, `P0335`, `P0336`, `P0339`, `P0340`, `P0341`)
  - Clase 22 (EVAP): 18 casos (`P0440`, `P0441`, `P0442`, `P0443`, `P0446`, `P0455`, `P0456`)
  - Clase 23 (Catalizador): 16 casos (`P0420`, `P0430`)
  - Clase 24 (Regulador presión): 11 casos (`P0171`, `P0172`)
  - Clase 25 (Inyector individual): 29 casos (`P0201`, `P0202`, `P0203`, `P0204`, `P0301`, `P0302`)
  - Clase 26 (Pérdida compresión): 12 casos (`P0301`, `P0302`, `P0303`, `P0304`)

### B. Casos Contrastivos
- **Total contrastivos (`es_contrastivo=SI`):** 128 registros
- **Validación taxonómica:** 100% de las etiquetas `clase_contrastiva` coinciden con las 61 canónicas.
- **Colisiones directas (`clase_contrastiva == clase_objetivo`):** 0 colisiones.
- **Contrastes implementados:**
  - Clase 21 vs: Faja/cadena destensada, VVT, Motor de arranque, Bomba de gasolina, Misfire encendido.
  - Clase 22 vs: Sensor de oxígeno/mezcla rica, Regulador de presión, Inyectores sucios, Flex fuel.
  - Clase 23 vs: Catalizador ineficiente vs obstruido, Sensor O2/mezcla, DPF Diesel, Descarbonización GDI, Fuga intercooler.
  - Clase 24 vs: Bomba de gasolina baja presión, Inyectores sucios, Módulo FSCM/PEM, Common Rail Diesel, Sensor O2.
  - Clase 25 vs: Misfire encendido (bujías/bobinas), Inyectores sucios general, Bomba de gasolina, Compresión mecánica.
  - Clase 26 vs: Misfire encendido, Inyector cortado, Faja con salto de punto, Desgaste de anillos vs válvulas pisadas (prueba húmeda).

---

## 4. Auditoría de Duplicados, Near-Duplicates y Fuga (Leakage)

Se compararon los 240 textos contra un total de **7,281 registros de referencia**:
- Lotes previos Fase 10 (Lote 01, Lote 02, Lote 03, Lote 04 = 800 casos)
- TRAIN canónico (`dataset_sintomas_limpio.csv` = 2,481 casos)
- DEV-60 (`benchmark_dev_60_casos.py`)
- TEST Ciego 100 (`benchmark_test_ciego_100.py`)
- Benchmarks G1 y G2 (`benchmark_v4_g1_casos.py`, `benchmark_v4_g2_casos.py`)
- Muestra de campo real de 60 casos de la tesis (`casos_reales_mecanicos_evaluacion.csv`)

### Resultados:
| Métrica | Umbral Máximo | Valor Observado | Estado |
|---|:---:|:---:|:---:|
| **Duplicados exactos intra-lote** | 0 | 0 | **CONFORME** |
| **Duplicados exactos inter-referencias** | 0 | 0 | **CONFORME** |
| **Similitud máxima intra-lote** | < 0.90 | **0.4071** | **CONFORME** |
| **Similitud máxima contra referencias (leakage)** | < 0.88 | **0.5793** | **CONFORME** |
| **Near-duplicates detectados** | 0 | 0 | **CONFORME** |

---

## 5. Auditoría Técnica Manual / Semántica (Muestra de 30 Registros)

Se auditó de forma manual y semántica una muestra estratificada de 5 casos por clase (1 L1, 2 L2, 2 L3), totalizando 30 registros:

1. **Clase 21 (CKP / CMP):**
   - `F10-L05-0001` (L1): Síntoma ambiguo de arranque prolongado en caliente; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L05-0011` (L2): DTC P0335 con motor que gira pero tacómetro no marca RPM y bomba no ceba; contrasta con Bomba de gasolina. Conforme.
   - `F10-L05-0015` (L2): Sensor CKP inductivo con entrehierro fuera de tolerancia (1.8 mm); contrasta con faja de distribución. Conforme.
   - `F10-L05-0026` (L3): Oscilograma de 2 canales muestra dientes deformados en la rueda fónica (60-2); señal cuadrada de CMP correcta pero CKP desfasada. Conforme.
   - `F10-L05-0037` (L3): Falla térmica a 82°C en CKP tipo Hall (corte de señal a 0V); al enfriar con spray refrigerante recupera pulso de 5V instantáneamente. Conforme.

2. **Clase 22 (EVAP):**
   - `F10-L05-0041` (L1): Olor a gasolina cerca de rueda trasera al dejar bajo el sol; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L05-0051` (L2): Dificultad de arranque inmediatamente después de tanquear combustible (ahogo por purga abierta); contrasta con Regulador de presión. Conforme.
   - `F10-L05-0055` (L2): DTC P0441; válvula de purga atascada abierta comunicando vacío directo del múltiple al tanque; contrasta con Sensor O2. Conforme.
   - `F10-L05-0066` (L3): Prueba con máquina de humo a 1 psi revela fuga en sello de tapa de combustible con DTC P0456; canister seco y solenoide de purga hermético con vacío de 22 inHg. Conforme.
   - `F10-L05-0077` (L3): Monitoreo de sensor FTP (Fuel Tank Pressure) con escáner: presión no retiene vacío tras prueba de despresurización con DTC P0455 (fuga mayor en manguera de venteo del canister). Conforme.

3. **Clase 23 (Convertidor Catalítico):**
   - `F10-L05-0081` (L1): Check Engine prendido en tablero sin falla perceptible de potencia; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L05-0091` (L2): DTC P0420 con sensor O2 downstream (banco 1 sensor 2) oscilando en espejo con el upstream (0.1V a 0.8V); potencia normal y escape libre; contrasta con Sensor O2. Conforme.
   - `F10-L05-0095` (L2): Catalizador taponado físicamente; motor no pasa de 2500 rpm con silbido por empaque y contrapresión de 4.0 psi; contrasta con Catalizador ineficiente. Conforme.
   - `F10-L05-0106` (L3): Pirómetro infrarrojo mide entrada a 380°C y salida a 355°C (delta negativo = catalizador inactivo/muerto) con P0420; combustible y encendido comprobados sin fallas. Conforme.
   - `F10-L05-0117` (L3): Prueba de contrapresión con manómetro en orificio de sensor O2 delantero registra 6.5 psi a 3000 rpm (especificación < 1.25 psi); al retirar el tubo frontal el motor recupera potencia plena instantáneamente. Conforme.

4. **Clase 24 (Regulador de Presión de Combustible):**
   - `F10-L05-0121` (L1): Humo negro al arrancar y olor fuerte a nafta en el escape; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L05-0131` (L2): Manguera de vacío del regulador con combustible líquido succionado hacia el múltiple; mezcla súper rica (STFT -25%); contrasta con Inyectores sucios. Conforme.
   - `F10-L05-0135` (L2): Presión en riel en 75 psi excesiva (especificación 43 psi) por resorte trabado en regulador de retorno; bujías carbonizadas; contrasta con Bomba de combustible. Conforme.
   - `F10-L05-0146` (L3): Manómetro mecánico marca caída inmediata de 45 psi a 0 psi al cortar contacto; prueba con pinzamiento de manguera de retorno retiene presión descartando check de bomba e inyectores. Conforme.
   - `F10-L05-0157` (L3): Prueba de diafragma con bomba de vacío Mityvac: no retiene 15 inHg de depresión y gotea gasolina por el puerto de prueba; regulador perforado. Conforme.

5. **Clase 25 (Circuito o Solenoide de Inyector Individual):**
   - `F10-L05-0161` (L1): Motor tiembla fuerte en ralentí trabajando en 3 cilindros; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L05-0171` (L2): DTC P0201 de circuito de inyector 1 abierto; bujía y bobina con chispa potente de 30 kV pero cilindro inactivo; contrasta con Falla de encendido. Conforme.
   - `F10-L05-0175` (L2): DTC P0202; inyector funciona en frío pero a 85°C la bobina dilata y abre el circuito térmicamente; contrasta con Pérdida de compresión. Conforme.
   - `F10-L05-0186` (L3): Osciloscopio con pinza amperimétrica registra 0.0 A en inyector 1 (inyector 2 consume 1.1 A con pico de 65V); resistencia interna infinita (circuito abierto) con chispa de 32 kV impecable. Conforme.
   - `F10-L05-0197` (L3): Análisis de retardo de cierre electromecánico (inflexión de corriente): inyector 1 demora 3.2 ms vs 1.2 ms OEM por degradación de resorte y magnetización residual. Conforme.

6. **Clase 26 (Pérdida de Compresión en Cilindro):**
   - `F10-L05-0201` (L1): Motor tiembla en ralentí y suena desparejo al girar en arranque; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L05-0211` (L2): Cilindro 3 marca 40 psi en seco; prueba húmeda con aceite no sube nada (se mantiene en 40 psi), confirmando válvula pisada vs anillos. Conforme.
   - `F10-L05-0215` (L2): Motor a gas GLP con holgura de taqués en 0.00 mm por recesión de asiento; válvula no sella al dilatar en caliente; contrasta con VVT. Conforme.
   - `F10-L05-0226` (L3): DTC P0303 con chispa de 28 kV e inyector activo; compresión seca 45 psi, húmeda 45 psi; detector de fugas a 90 psi revela 80% de pérdida por múltiple de escape (válvula quemada). Conforme.
   - `F10-L05-0237` (L3): Prueba de fugas neumática con 100 psi en cilindro 2 acusa 70% de escape por múltiple de admisión; con balancines retirados la válvula no asienta por carbonilla dura compactada en el chaflán. Conforme.

---

## 6. Clasificación Final de Auditoría

- **Aprobados:** 240 / 240 (100.0%)
- **Revisar:** 0 / 240 (0.0%)
- **Rechazados:** 0 / 240 (0.0%)

**Dictamen:** Lote 05 plenamente calificado para su consolidación controlada en `dataset_fase10_master.csv`.
