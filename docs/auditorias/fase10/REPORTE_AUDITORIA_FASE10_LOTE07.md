# REPORTE DE AUDITORÍA FASE 10 — LOTE 07 (TRANSMISIÓN)
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — 100% CONFORME (BLOQUEO DE ENTRENAMIENTO ACTIVO)  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_07.csv` (320 registros, 8 clases de TRANSMISIÓN)  
**Archivo de Auditoría:** `fase10_auditoria_lote07.csv`

---

## 1. Verificación de Inmutabilidad de Fase 8.3

En estricto cumplimiento de las reglas metodológicas de la tesis, se verificó el manifiesto oficial de inmutabilidad criptográfica SHA-256 de los 19 artefactos canónicos antes y durante el procesamiento:

- **Artefactos congelados:** 19/19
- **Hashes coincidentes:** 19/19 (100%)
- **Discrepancias:** 0
- **Modelos de producción modificados:** 0 (Ninguno)
- **Vectorizador modificado:** 0 (Ninguno)
- **RAG / FAISS modificado:** 0 (Ninguno)

---

## 2. Auditoría Estructural del Lote 07

| Parámetro Evaluado | Requisito Formal | Valor Observado | Estado |
|---|---|---|:---:|
| **Codificación de archivo** | UTF-8 estricto | UTF-8 sin BOM, decodificación limpia | **CONFORME** |
| **Total registros** | 320 registros | 320 filas | **CONFORME** |
| **Columnas requeridas** | 16 columnas específicas | 16 columnas canónicas | **CONFORME** |
| **Cobertura de clases** | 8 clases canónicas (34 a 41) | 8 clases canónicas de TRANSMISIÓN | **CONFORME** |
| **Balance por clase** | 40 registros por clase | 40 registros por clase (exacto) | **CONFORME** |
| **Distribución por nivel** | 80 L1 / 120 L2 / 120 L3 | 80 L1 (25.0%) / 120 L2 (37.5%) / 120 L3 (37.5%) | **CONFORME** |
| **Balance nivel por clase** | 10 L1, 15 L2, 15 L3 | 10 L1, 15 L2, 15 L3 por cada una de las 8 clases | **CONFORME** |
| **Unicidad de IDs** | F10-L07-0001 a F10-L07-0320 | 320 IDs únicos sin colisiones | **CONFORME** |
| **Macro-Sistema** | Coincidir con `TRANSMISION` | 320/320 registros asignados a `TRANSMISION` | **CONFORME** |
| **Fuente** | `SINTETICO_IA` | 320/320 registros etiquetados `SINTETICO_IA` | **CONFORME** |

### Clases Incluidas en el Lote 07:
1. `Disco de embrague desgastado o patinando` (Clase 34): 40 registros (10 L1, 15 L2, 15 L3)
2. `Falla en bombin o bomba hidraulica de embrague` (Clase 35): 40 registros (10 L1, 15 L2, 15 L3)
3. `Falta o degradacion de aceite de caja de cambios` (Clase 36): 40 registros (10 L1, 15 L2, 15 L3)
4. `Rodajes de caja mecanica o diferencial gastados` (Clase 37): 40 registros (10 L1, 15 L2, 15 L3)
5. `Sobrecalentamiento o solenoides en caja automatica CVT / DSG` (Clase 38): 40 registros (10 L1, 15 L2, 15 L3)
6. `Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)` (Clase 39): 40 registros (10 L1, 15 L2, 15 L3)
7. `Desgaste en collarin de empuje o crapodina de embrague` (Clase 40): 40 registros (10 L1, 15 L2, 15 L3)
8. `Rodajes de transmision manual o eje primario gastados` (Clase 41): 40 registros (10 L1, 15 L2, 15 L3)

---

## 3. Auditoría de DTC y Casos Contrastivos

### A. Regla Reforzada de DTC
- **Total de registros con DTC:** 25 (7.8% del lote total)
- **DTC en nivel L1:** **0** (Prohibición absoluta cumplida al 100%; `requiere_pregunta = SI` en los 80 casos L1)
- **DTC en nivel L2:** **9**
- **DTC en nivel L3:** **16**
- **Casos L2/L3 SIN DTC:** **215** (89.6% de L2/L3 se basan estrictamente en síntomas acústicos, cinemáticos, térmicos y metrológicos de transmisión, previniendo sobreajuste por atajos de DTC)
- **Validación Sintáctica Regex (`^[PBCU][0-9A-Fa-f]{4}$`):** 100% de los códigos cumplen el estándar SAE J2012 / OBD-II.
- **Distribución de DTC por Clase:**
  - Clase 34 (Disco patinando): 1 DTC (`P0811` - Patinamiento excesivo de embrague)
  - Clase 35 (Bombín/bomba embrague): 0 DTC (sistema hidráulico manual sin monitoreo electrónico)
  - Clase 36 (Aceite de caja): 0 DTC (lubricación mecánica pura sin sensor de calidad de valvulina)
  - Clase 37 (Rodajes diferencial): 0 DTC (desgaste tribológico puramente mecánico)
  - Clase 38 (CVT / DSG): 14 DTCs (`P0746`, `P0841`, `P0846`, `P0711`, `P17BF`, `P189C`, `P0700`, `P2714`, `P0730`)
  - Clase 39 (Caja robotizada): 10 DTCs (`P0840`, `P0845`, `P0942`, `P0919`, `P1773`, `P0810`)
  - Clase 40 (Collarín de empuje): 0 DTC (cojinete axial mecánico en campana)
  - Clase 41 (Eje primario caja manual): 0 DTC (rodamientos de soporte en carcasas de caja manual)

### B. Casos Contrastivos
- **Total contrastivos (`es_contrastivo=SI`):** 172 registros (53.8% del lote)
- **Validación taxonómica:** 100% de las etiquetas `clase_contrastiva` coinciden con las 61 canónicas del proyecto.
- **Colisiones directas (`clase_contrastiva == clase_objetivo`):** 0 colisiones.
- **Contrastes Fundamentales Implementados:**
  - **34 vs 35 vs 40:** Diferenciación entre disco que patina bajo aceleración (RPM se disparan sin ganar velocidad y con olor a ferodo) frente a falla hidráulica (pedal bajo/esponjoso que impide desacoplar y hace rascar marchas) frente a collarín desgastado (chillido metálico estridente únicamente al pisar el pedal).
  - **40 vs 41:** Regla acústica fundamental:
    - *Collarín (Clase 40):* Silencioso con pedal suelto en neutro; chilla o vibra al pisar el pedal de embrague (bajo carga axial).
    - *Eje primario (Clase 41):* Ruge o zumba en neutro con pedal suelto (eje girando); se silencia por completo al pisar el pedal de embrague a fondo (eje primario se detiene).
  - **37 vs 41:** Diferencial zumba o aúlla en movimiento proporcional a la velocidad y carga de arrastre/retención (drive/coast); silencioso con carro detenido en ralentí. Eje primario zumba con vehículo detenido en neutro y varía con RPM de motor.
  - **37 vs Rodamiento de maza / rueda:** Diferencial varía al acelerar vs soltar gas; rodamiento de rueda cambia de tono o intensidad al transferir peso en curvas pronunciadas a izquierda/derecha.
  - **38 vs 39:** Cajas automáticas CVT/DSG (variadores continuos con solenoides de polea o transmisiones de doble embrague electrohidráulico mecatrónico) frente a cajas robotizadas manuales monodisco con actuador robótico exterior (Dualogic / I-Motion / Easytronic) con aviso característico "Hacer controlar cambio", caída involuntaria a Neutral (N) y electrobomba de presurización de 45-50 bar.

---

## 4. Auditoría de Duplicados, Near-Duplicates y Fuga (Leakage)

Se confrontaron los 320 textos del Lote 07 contra un corpus consolidado de **7,801 registros de referencia**:
- Lotes previos Fase 10 (L01 a L06 = 1320 casos)
- TRAIN canónico (`dataset_sintomas_limpio.csv` = 2,481 casos)
- DEV-60 (`benchmark_dev_60_casos.py`)
- TEST Ciego 100 (`benchmark_test_ciego_100.py`)
- Benchmarks G1 y G2 (`benchmark_v4_g1_casos.py`, `benchmark_v4_g2_casos.py`)
- Muestra de campo real de 60 casos de taller de la tesis (`casos_reales_mecanicos_evaluacion.csv`)

### Métricas de Similitud Vectorial (TF-IDF sublinear unigrama/bigrama):
| Métrica | Umbral Máximo Permitido | Valor Observado en Lote 07 | Estado |
|---|:---:|:---:|:---:|
| **Duplicados exactos intra-lote** | 0 | 0 | **CONFORME** |
| **Duplicados exactos inter-referencias** | 0 | 0 | **CONFORME** |
| **Similitud máxima intra-lote** | < 0.90 | **0.3318** | **CONFORME** |
| **Similitud máxima contra referencias (leakage)** | < 0.88 | **0.6647** | **CONFORME** |
| **Near-duplicates detectados** | 0 | 0 | **CONFORME** |

---

## 5. Validación Especial de Aislamiento de Arquitectura (Sección 27)

Se implementó un analizador semántico estricto de arquitectura para garantizar la pureza ingenieril de cada subsistema de transmisión:
- **CVT (Transmisión Variable Continua):** Solo poleas cónicas variadoras, correa/faja de empuje metálica (Bosch pushbelt), fluidos específicos (NS-2, NS-3) y solenoides de presión secundaria. 0 menciones a embragues dobles o cajas robotizadas.
- **DSG (Caja de Doble Embrague):** Mecatrónica hidráulica integrada (DQ200 seca / DQ250 húmeda), paquetes de embrague concéntricos/paralelos K1/K2, horquillas selectoras internas y fallas de acumulador mecatrónico (`P17BF`). 0 menciones a variadores ni pedales de embrague de conductor.
- **Robotizada (Dualogic / I-Motion / Easytronic):** Caja mecánica convencional monodisco adaptada con grupo actuador electrohidráulico o electromecánico, bomba de alta presión de apertura por puerta del conductor, acumulador de nitrógeno tipo pera, fluido Tutela CS Speed, caídas a Neutral (N) en detenciones y aprendizaje de punto de contacto (kiss point). 0 pedales de embrague atribuibles al conductor y 0 componentes de CVT o doble embrague DSG.
- **Manual Pura (Clases 34, 35, 36, 37, 40, 41):** Conjuntos tradicionales con pedal de embrague operado por el conductor, disco de fricción, prensa de diafragma, collarín mecánico de bolas/csc, cilindro emisor/receptor, piñonería helicoidal y sincronizadores de bronce.
- **Resultado de la validación:** **0 inconsistencias o mezclas erróneas de arquitectura**.

---

## 6. Auditoría Técnica Manual / Semántica (Muestra de 46 Casos)

Se realizó una revisión manual detallada sobre una muestra estratificada de 46 casos (40 base: 5 por cada una de las 8 clases + 2 extra Clase 38 + 2 extra Clase 39 + 2 extra contraste 37 vs 41):

1. **Clase 34 (Disco de embrague desgastado o patinando):**
   - `F10-L07-0001` (L1): En subida el carro acelera en vacío y el motor ruge pero el auto apenas avanza; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0011` (L2): En 4ta marcha a 80 km/h al pisar a fondo las RPM suben de 2200 a 4000 sin aumento de velocidad y con olor a ferodo; contrasta con collarín. Conforme.
   - `F10-L07-0012` (L2): Prueba en 3ra marcha con freno de mano calado: motor no se apaga y sigue encendido patinando; contrasta con bombín. Conforme.
   - `F10-L07-0026` (L3): Medición metrológica: forro de fricción gastado a 0.2 mm por encima de los remaches de cobre con disco nominal quemado; contrasta con bombín. Conforme.
   - `F10-L07-0036` (L3): Pick-up con DTC `P0811` por desacople cinemático en sensor de velocidad de salida vs RPM de cigüeñal bajo carga de 900 kg. Conforme.

2. **Clase 35 (Falla en bombín o bomba hidráulica de embrague):**
   - `F10-L07-0041` (L1): El pedal de embrague se queda pegado en el piso y no sube solo; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0051` (L2): Pedal se va al fondo con resistencia nula por cubeta primaria desgastada en cilindro emisor con mancha en alfombra; contrasta con disco patinando. Conforme.
   - `F10-L07-0052` (L2): Cambios rascan al intentar entrar con motor encendido pero entran suaves con motor apagado; contrasta con aceite de caja. Conforme.
   - `F10-L07-0066` (L3): Manómetro hidráulico en línea de bombín registra caída de 38 a 4 bar en 10 s por bypass interno de retén primario EPDM. Conforme.
   - `F10-L07-0075` (L3): Líquido DOT 4 emulsionado y turbio en bombín esclavo con carrera efectiva de solo 4 mm vs 13 mm nominales. Conforme.

3. **Clase 36 (Falta o degradación de aceite de caja de cambios):**
   - `F10-L07-0081` (L1): Los cambios están duros y raspan al meterlos por las mañanas frías; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0091` (L2): Raspe metálico en 2da y 3ra con aceite de transmisión negro y olor a azufre quemado tras 140,000 km; contrasta con bombín. Conforme.
   - `F10-L07-0092` (L2): Drenaje de caja manual arroja apenas 650 ml de valvulina de los 2.1 litros estipulados por fuga en retén de semieje. Conforme.
   - `F10-L07-0106` (L3): Análisis tribológico de lubricante acusa viscosidad cinemática a 40°C de 31 cSt (degradada vs 75 cSt) con 480 ppm de bronce de sincronizadores. Conforme.
   - `F10-L07-0112` (L3): Tapón magnético de drenaje saturado con erizo de 8 gramos de limalla de acero por marcha en seco. Conforme.

4. **Clase 37 (Rodajes de caja mecánica o diferencial gastados):**
   - `F10-L07-0121` (L1): Se escucha un aullido en la parte baja cuando el auto rueda en pista rápida; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0131` (L2): Zumbido sordo entre 60 y 90 km/h que aumenta al pisar el acelerador y se apaga al soltar gas; contrasta con rodamiento de rueda. Conforme.
   - `F10-L07-0132` (L2): En neutro detenido no suena nada; al rodar en carretera aúlla el diferencial; contrasta con eje primario. Conforme.
   - `F10-L07-0146` (L3): Reloj comparador registra juego radial de 0.45 mm en corona de diferencial y precarga de rodamientos cónicos en 0 Nm con picaduras spalling. Conforme.
   - `F10-L07-0153` (L3): Prueba con acelerómetros triaxiales en puente trasero acusa 8.4 mm/s RMS a frecuencia de engrane de 420 Hz modulada por rotación de piñón de ataque. Conforme.
   - *(Extra Contraste 37 vs 41)* `F10-L07-0134` (L2): Aullido en retención descendiendo pendiente a 70 km/h que desaparece en ralentí; contrasta estrictamente con eje primario. Conforme.

5. **Clase 38 (Sobrecalentamiento o solenoides en caja automática CVT / DSG):**
   - `F10-L07-0161` (L1): En la caja automática parpadea una llave inglesa y pierde fuerza en subida; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0171` (L2): CVT con DTC `P0841` y tironeos en aceleración con fluido degradado oscuro; contrasta con aceite manual. Conforme.
   - `F10-L07-0172` (L2): DSG DQ200 con DTC `P17BF` parpadeando indicador de marcha y perdiendo pares por fuga en acumulador de mecatrónica. Conforme.
   - `F10-L07-0186` (L3): CVT Jatco con `P0846` y `P0746`: presión secundaria cae a 0.6 MPa vs 2.8 MPa con correa metálica rayada. Conforme.
   - `F10-L07-0187` (L3): DSG DQ250 con sobretemperatura de embrague K1 (148°C) con tirones violentos en 1ra y reversa. Conforme.
   - *(Extra CVT)* `F10-L07-0162` (L1): Sentón y retraso de 3 segundos para que la caja CVT enganche la marcha D. Conforme.
   - *(Extra DSG)* `F10-L07-0163` (L1): La transmisión de doble embrague da tirones al pasar de 1ra a 2da. Conforme.

6. **Clase 39 (Falla en caja robotizada Dualogic / I-Motion / Easytronic):**
   - `F10-L07-0201` (L1): La caja robotizada se salta a neutro sola cuando me detengo en el semáforo; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0202` (L1): Sale aviso 'Hacer controlar cambio' y el carro no quiere arrancar en semáforo. Conforme.
   - `F10-L07-0203` (L1): Al abrir la puerta del conductor no se escucha el zumbido de la bomba de presurización de la caja. Conforme.
   - `F10-L07-0211` (L2): Fiat Palio Dualogic salta a N al detenerse; electrobomba no acciona por escobillas gastadas; contrasta con DSG. Conforme.
   - `F10-L07-0212` (L2): VW Gol I-Motion con DTC `P0840`: presión hidráulica cae de 45 a 22 bar en semáforo; contrasta con DSG. Conforme.
   - `F10-L07-0226` (L3): Fiat Grand Siena Dualogic con `P0845` y `P1773`: acumulador de nitrógeno desinflado descarga presión de 48 a 28 bar en solo 6 s. Conforme.
   - `F10-L07-0227` (L3): VW Fox I-Motion con degradación de embrague en 9,200 unidades e imposibilidad de calibración de kiss point por fuga de Tutela CS Speed. Conforme.

7. **Clase 40 (Desgaste en collarín de empuje o crapodina de embrague):**
   - `F10-L07-0241` (L1): Suena un chillido metálico fuerte cada vez que piso el pedal del embrague; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0251` (L2): Chillido agudo de rodamiento seco al pisar el pedal de embrague; en neutro con pedal suelto reina el silencio; contrasta con eje primario. Conforme.
   - `F10-L07-0252` (L2): Vibración áspera en la suela del zapato al pisar el pedal en ralentí; cojinete sin grasa; contrasta con plato opresor. Conforme.
   - `F10-L07-0266` (L3): Sonometría diferencial: en neutro con pedal suelto opera a 48 dBA; al presionar con 50 N de carga sube a 82 dBA en 3.4 kHz confirmando collarín vs primario. Conforme.
   - `F10-L07-0267` (L3): Desarmado revela cojinete gripado con jaula de poliamida derretida que friccionó y cortó 4 dedos de la prensa. Conforme.

8. **Clase 41 (Rodajes de transmisión manual o eje primario gastados):**
   - `F10-L07-0281` (L1): La caja zumba feo en neutro y el ruido se apaga cuando piso el embrague; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L07-0291` (L2): Con carro detenido en ralentí zumba en neutro; al pisar el pedal de embrague el eje primario se frena y el ruido cesa; contrasta con collarín. Conforme.
   - `F10-L07-0292` (L2): Ruido que varía con las RPM en punto muerto con embrague acoplado; se calla al desacoplar; contrasta con diferencial. Conforme.
   - `F10-L07-0294` (L2): Ruido en 1ra, 2da, 3ra y 5ta pero disminuye drásticamente en 4ta marcha (directa 1:1) por anulación de carga radial; contrasta con diferencial. Conforme.
   - `F10-L07-0306` (L3): Sonómetro registra 76 dBA en neutro que se desploma a 44 dBA al pisar el embrague; rodamiento 6205 de entrada picado con juego radial de 0.58 mm. Conforme.
   - `F10-L07-0307` (L3): Zumbido en marchas indirectas que desaparece en 4ta directa; micrómetro confirma 0.62 mm de holgura radial en rodaje de entrada. Conforme.
   - *(Extra Contraste 41 vs 37)* `F10-L07-0308` (L3): Prueba de taller en neutro detenido acelerando a 2500 rpm produce aullido que se extingue al pisar embrague; contrasta con diferencial. Conforme.

---

## 7. Clasificación Final de Auditoría

- **Aprobados:** 320 / 320 (100.0%)
- **Revisar:** 0 / 320 (0.0%)
- **Rechazados:** 0 / 320 (0.0%)

**Dictamen:** Lote 07 (TRANSMISIÓN) plenamente calificado y verificado para su consolidación controlada en `dataset_fase10_master.csv`.
