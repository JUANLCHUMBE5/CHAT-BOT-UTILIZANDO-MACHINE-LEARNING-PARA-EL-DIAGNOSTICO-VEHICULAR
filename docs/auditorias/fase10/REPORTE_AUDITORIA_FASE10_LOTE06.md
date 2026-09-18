# REPORTE DE AUDITORÍA FASE 10 — LOTE 06 (FRENOS)
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — 100% CONFORME (BLOQUEO DE ENTRENAMIENTO ACTIVO)  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_06.csv` (280 registros, 7 clases de FRENOS)  
**Archivo de Auditoría:** `fase10_auditoria_lote06.csv`

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

## 2. Auditoría Estructural del Lote 06

| Parámetro Evaluado | Requisito Formal | Valor Observado | Estado |
|---|---|---|:---:|
| **Codificación de archivo** | UTF-8 estricto | UTF-8 sin BOM, decodificación limpia | **CONFORME** |
| **Total registros** | 280 registros | 280 filas | **CONFORME** |
| **Columnas requeridas** | 16 columnas específicas | 16 columnas canónicas | **CONFORME** |
| **Cobertura de clases** | 7 clases canónicas (27 a 33) | 7 clases canónicas | **CONFORME** |
| **Balance por clase** | 40 registros por clase | 40 registros por clase (exacto) | **CONFORME** |
| **Distribución por nivel** | 70 L1 / 105 L2 / 105 L3 | 70 L1 (25%) / 105 L2 (37.5%) / 105 L3 (37.5%) | **CONFORME** |
| **Balance nivel por clase** | 10 L1, 15 L2, 15 L3 | 10 L1, 15 L2, 15 L3 por cada una de las 7 clases | **CONFORME** |
| **Unicidad de IDs** | F10-L06-0001 a F10-L06-0280 | 280 IDs únicos sin colisiones | **CONFORME** |
| **Macro-Sistema** | Coincidir con `FRENOS` | 280/280 registros asignados a `FRENOS` | **CONFORME** |
| **Fuente** | `SINTETICO_IA` | 280/280 registros etiquetados `SINTETICO_IA` | **CONFORME** |

### Clases Incluidas en el Lote 06:
1. `Desgaste de pastillas y zapatas de freno`: 40 registros (10 L1, 15 L2, 15 L3)
2. `Discos de freno alabeados o desgastados`: 40 registros (10 L1, 15 L2, 15 L3)
3. `Falla en servofreno (booster) o linea de vacio`: 40 registros (10 L1, 15 L2, 15 L3)
4. `Fuga hidraulica o aire en el sistema de frenos`: 40 registros (10 L1, 15 L2, 15 L3)
5. `Falla en sensor de velocidad de rueda ABS`: 40 registros (10 L1, 15 L2, 15 L3)
6. `Falla en sistema de frenado regenerativo (EV / Hibridos)`: 40 registros (10 L1, 15 L2, 15 L3)
7. `Caliper de freno trabado o mordaza pegada (piston agarrotado)`: 40 registros (10 L1, 15 L2, 15 L3)

---

## 3. Auditoría de DTC y Casos Contrastivos

### A. Regla Reforzada de DTC
- **Total de registros con DTC:** 32 (11.4% del lote)
- **DTC en nivel L1:** **0** (Prohibición absoluta cumplida al 100%; `requiere_pregunta = SI` en los 70 casos L1)
- **DTC en nivel L2:** **11**
- **DTC en nivel L3:** **21**
- **Casos L2/L3 SIN DTC:** **178** (84.8% de L2/L3 se basan estrictamente en síntomas, comportamientos mecánicos, térmicos y metrológicos, previniendo sobreajuste o atajos en el modelo)
- **Validación Sintáctica Regex (`^[PBCU][0-9A-Fa-f]{4}$`):** 100% de los códigos cumplen el estándar SAE J2012.
- **Validación Semántica / Técnica:** 100% compatibles con la falla descrita y su contexto automotriz:
  - Clase 27 (Pastillas/Zapatas): 0 DTC (sistema mecánico puro con desgaste acústico o visual)
  - Clase 28 (Discos alabeados): 0 DTC (falla metrológica y mecánica sin sensor electrónico de alabeo)
  - Clase 29 (Servofreno / Booster): 6 DTCs (`P0171`, `P0555`, `P0556`, `C1246`)
  - Clase 30 (Fuga / Aire): 0 DTC (sistema hidráulico de circuito cerrado convencional)
  - Clase 31 (Sensor ABS): 11 DTCs (`C0035`, `C0040`, `C0045`, `C0050`)
  - Clase 32 (Frenado regenerativo EV/Híbridos): 14 DTCs (`C1203`, `C1241`, `C1256`, `C1259`, `C1345`, `C1391`)
  - Clase 33 (Caliper trabado): 1 DTC (`C100D` en actuador de freno de estacionamiento electromecánico EPB)

### B. Casos Contrastivos
- **Total contrastivos (`es_contrastivo=SI`):** 140 registros
- **Validación taxonómica:** 100% de las etiquetas `clase_contrastiva` coinciden exactamente con las 61 canónicas.
- **Colisiones directas (`clase_contrastiva == clase_objetivo`):** 0 colisiones.
- **Contrastes implementados:**
  - Clase 27 vs: Discos de freno alabeados, Caliper de freno trabado, Fuga hidráulica o aire.
  - Clase 28 vs: Llantas desbalanceadas o desalineadas (distinción fundamental: vibración AL FRENAR vs en marcha continua a velocidad sin tocar el pedal), Desgaste de pastillas, Caliper de freno trabado.
  - Clase 29 vs: Fuga hidráulica o aire (distinción fundamental: PEDAL DURO que exige fuerza extrema vs PEDAL ESPONJOSO que se hunde), Sensor de oxígeno / mezcla rica (P0171 por entrada de aire falso vía booster).
  - Clase 30 vs: Servofreno / booster, Desgaste de pastillas, Caliper trabado, Sensor ABS.
  - Clase 31 vs: Discos de freno alabeados (falso disparo trepidante de ABS vs pulsación mecánica de rotor), Llantas desbalanceadas, Frenado regenerativo.
  - Clase 32 vs: Sensor de velocidad de rueda ABS, Desgaste de pastillas, Degradación de batería de alta tensión (diferenciando limitación por batería al 100% SoC que no es avería), Fallo de inversor IGBT.
  - Clase 33 vs: Llantas desalineadas (vehículo jala hacia un lado al rodar por arrastre térmico con rueda a 245°C vs geometría de dirección), Discos alabeados, Desgaste de pastillas (desgaste asimétrico 100% interior vs exterior intacta).

---

## 4. Auditoría de Duplicados, Near-Duplicates y Fuga (Leakage)

Se compararon los 280 textos contra un total de **7,521 registros de referencia**:
- Lotes previos Fase 10 (L01 a L05 = 1040 casos)
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
| **Similitud máxima intra-lote** | < 0.90 | **0.5390** | **CONFORME** |
| **Similitud máxima contra referencias (leakage)** | < 0.88 | **0.6353** | **CONFORME** |
| **Near-duplicates detectados** | 0 | 0 | **CONFORME** |

---

## 5. Auditoría Técnica Manual / Semántica (Muestra de 38 Registros)

Se auditó de forma manual y semántica una muestra estratificada de 5 casos por clase (1 L1, 2 L2, 2 L3) más 3 casos adicionales de la Clase 32 (Frenado regenerativo), totalizando 38 registros:

1. **Clase 27 (Desgaste de pastillas y zapatas):**
   - `F10-L06-0001` (L1): Chillido agudo al pisar el freno suavemente; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L06-0011` (L2): Chillido estridente a baja velocidad con nivel de líquido bajo en depósito por compensación normal; contrasta con fuga. Conforme.
   - `F10-L06-0015` (L2): Sonido chirriante agudo en rueda delantera derecha sin pulsación en pedal; contrasta con disco alabeado. Conforme.
   - `F10-L06-0026` (L3): Medición con micrómetro de pastillas a 1.2 mm y chapa avisadora en contacto con disco nominal de 24.2 mm sin rebaba. Conforme.
   - `F10-L06-0037` (L3): Prueba en frenómetro de rodillos acusa eficacia de 42% por cristalización vidriosa de zapatas traseras tras pendiente. Conforme.

2. **Clase 28 (Discos de freno alabeados o desgastados):**
   - `F10-L06-0041` (L1): Volante vibra fuerte únicamente al pisar el freno a velocidad; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L06-0051` (L2): Vibración severa en volante al frenar entre 80 y 110 km/h; al soltar el freno a 100 km/h rueda sedita; contrasta con llantas desbalanceadas. Conforme.
   - `F10-L06-0055` (L2): Medición de disco con micrómetro en 19.4 mm por debajo del grabado de descarte MIN TH 20.0 mm. Conforme.
   - `F10-L06-0066` (L3): Reloj comparador con base magnética registra runout de 0.14 mm en disco con descentramiento de maza en 0.01 mm normal. Conforme.
   - `F10-L06-0077` (L3): Medición de variación de espesor (DTV) en 8 puntos con micrómetro digital registra delta de 0.030 mm (máx OEM 0.012 mm). Conforme.

3. **Clase 29 (Servofreno / Booster / Línea de vacío):**
   - `F10-L06-0081` (L1): Pedal durísimo como una piedra que exige pararse con ambas piernas; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L06-0091` (L2): Silbido fuerte de fuga de aire en cabina bajo el tablero al pisar freno con DTC P0171 por mezcla pobre. Conforme.
   - `F10-L06-0095` (L2): Válvula check antirretorno trabada cerrada impidiendo generación de depresión en el servofreno. Conforme.
   - `F10-L06-0106` (L3): Vacuómetro en T registra caída de 19 a 4 inHg al pisar freno con STFT en +25% y P0171 por diafragma roto. Conforme.
   - `F10-L06-0117` (L3): Bomba de vacío mecánica en alternador entrega solo 4 inHg vs 22 inHg por rotura de paleta interna de grafito. Conforme.

4. **Clase 30 (Fuga hidráulica o aire en el sistema):**
   - `F10-L06-0121` (L1): Pedal esponjoso que se va hasta el fondo; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L06-0131` (L2): Pedal se hunde en semáforo pero recupera firmeza al bombear 3 veces; contrasta con booster. Conforme.
   - `F10-L06-0135` (L2): Copela primaria de cilindro maestro con bypass interno que recircula líquido entre cámaras sin pérdida exterior. Conforme.
   - `F10-L06-0146` (L3): Manómetros en 4 ruedas registran caída de 40 a 8 bar bajo presión estática confirmando fuga interna en cilindro maestro. Conforme.
   - `F10-L06-0157` (L3): Desequilibrio del 85% en frenómetro de rodillos por bombín trasero que empapó zapatas con líquido DOT 4. Conforme.

5. **Clase 31 (Sensor de velocidad de rueda ABS):**
   - `F10-L06-0161` (L1): Luz amarilla de ABS encendida fija en el tablero; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L06-0171` (L2): Falso disparo de ABS a menos de 15 km/h en asfalto seco por limalla de hierro saturando la punta del sensor; contrasta con disco alabeado. Conforme.
   - `F10-L06-0175` (L2): Lectura de escáner en vivo acusa rueda trasera izquierda a 0 km/h fija mientras las otras 3 marcan 60 km/h con DTC C0045. Conforme.
   - `F10-L06-0186` (L3): Osciloscopio en sensor activo revela onda cuadrada degradada de 4 a 8 mA vs 7 a 14 mA OEM con DTC C0035. Conforme.
   - `F10-L06-0197` (L3): Tarjeta detectora magnética revela instalación de rodamiento genérico sin encoder de 60 polos magnéticos con C0040. Conforme.

6. **Clase 32 (Frenado regenerativo - EV / Híbridos):**
   - `F10-L06-0201` (L1): Indicador CHG no regenera energía al desacelerar en vehículo híbrido; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L06-0211` (L2): Falla con batería al 50% SoC (descartando limitación normal por batería llena) con aviso 'Check Brake System'. Conforme.
   - `F10-L06-0212` (L2): DTC C1391 por fuga de presión en acumulador con electrobomba encendiendo cada 8 segundos continuamente. Conforme.
   - `F10-L06-0215` (L2): DTC C1203 de pérdida de comunicación CAN entre calculador de frenada e inversor híbrido. Conforme.
   - `F10-L06-0226` (L3): Techstream monitorea ciclo de presurización de 12.2 a 15.5 MPa cada 6 segundos con C1391 por fuga en electroválvula interna. Conforme.
   - `F10-L06-0227` (L3): Kia Niro EV con 55% SoC registra 0 kW de regeneración por discrepancia de correlación superior al 15% en canales de Stroke Sensor con C1203. Conforme.
   - `F10-L06-0230` (L3): Corolla Hybrid con aguja CHG inerte y bomba zumbando continuamente con código C1391. Conforme.
   - `F10-L06-0237` (L3): DTC C1259 de inhibición del sistema regenerativo por límite de corriente de carga ante sobretemperatura de celda 6 (52°C). Conforme.

7. **Clase 33 (Caliper de freno trabado o mordaza pegada):**
   - `F10-L06-0241` (L1): Una sola rueda delantera se calienta tanto que quema al tocar el aro; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L06-0251` (L2): Rueda delantera derecha hirviendo con olor a ferodo quemado; contrasta con pastillas desgastadas. Conforme.
   - `F10-L06-0255` (L2): Desgaste asimétrico extremo: pastilla interior al 100% en el metal mientras la exterior conserva 8 mm intactos por pernos guía doblados. Conforme.
   - `F10-L06-0266` (L3): Termómetro infrarrojo mide disco derecho en 245°C vs izquierdo en 48°C; rueda no gira con 50 Nm y pistón presenta picaduras de 0.3 mm. Conforme.
   - `F10-L06-0277` (L3): Óxido acumulado bajo las láminas shims de acero inoxidable aprisiona mecánicamente la pastilla impidiendo deslizamiento. Conforme.

- **Seguridad en los textos:** 100% de cumplimiento de la Regla 18. Ningún texto promueve maniobras peligrosas ni conducción insegura.

---

## 6. Clasificación Final de Auditoría

- **Aprobados:** 280 / 280 (100.0%)
- **Revisar:** 0 / 280 (0.0%)
- **Rechazados:** 0 / 280 (0.0%)

**Dictamen:** Lote 06 (FRENOS) plenamente calificado para su consolidación controlada en `dataset_fase10_master.csv`.
