# REPORTE DE AUDITORÍA FASE 10 — LOTE 08 (SUSPENSIÓN Y CHASIS)
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — 100% CONFORME (BLOQUEO DE ENTRENAMIENTO ACTIVO)  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_08.csv` (200 registros, 5 clases de SUSPENSION_CHASIS)  
**Archivo de Auditoría:** `fase10_auditoria_lote08.csv`

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

## 2. Auditoría Estructural del Lote 08

| Parámetro Evaluado | Requisito Formal | Valor Observado | Estado |
|---|---|---|:---:|
| **Codificación de archivo** | UTF-8 estricto | UTF-8 sin BOM, decodificación limpia | **CONFORME** |
| **Total registros** | 200 registros | 200 filas | **CONFORME** |
| **Columnas requeridas** | 16 columnas específicas | 16 columnas canónicas | **CONFORME** |
| **Cobertura de clases** | 5 clases canónicas (42 a 46) | 5 clases canónicas de SUSPENSION_CHASIS | **CONFORME** |
| **Balance por clase** | 40 registros por clase | 40 registros por clase (exacto) | **CONFORME** |
| **Distribución por nivel** | 50 L1 / 75 L2 / 75 L3 | 50 L1 (25.0%) / 75 L2 (37.5%) / 75 L3 (37.5%) | **CONFORME** |
| **Balance nivel por clase** | 10 L1, 15 L2, 15 L3 | 10 L1, 15 L2, 15 L3 por cada una de las 5 clases | **CONFORME** |
| **Unicidad de IDs** | F10-L08-0001 a F10-L08-0200 | 200 IDs únicos sin colisiones | **CONFORME** |
| **Macro-Sistema** | Coincidir con `SUSPENSION_CHASIS` | 200/200 registros asignados a `SUSPENSION_CHASIS` | **CONFORME** |
| **Fuente** | `SINTETICO_IA` | 200/200 registros etiquetados `SINTETICO_IA` | **CONFORME** |

### Clases Incluidas en el Lote 08:
1. `Amortiguadores reventados o bujes de suspension gastados` (Clase 42): 40 registros (10 L1, 15 L2, 15 L3)
2. `Juntas homocineticas o palieres danados` (Clase 43): 40 registros (10 L1, 15 L2, 15 L3)
3. `Llantas desbalanceadas o desalineadas` (Clase 44): 40 registros (10 L1, 15 L2, 15 L3)
4. `Cremallera de direccion asistida con holgura o fuga` (Clase 45): 40 registros (10 L1, 15 L2, 15 L3)
5. `Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)` (Clase 46): 40 registros (10 L1, 15 L2, 15 L3)

---

## 3. Auditoría de DTC y Casos Contrastivos

### A. Regla Reforzada de DTC
- **Total de registros con DTC:** 7 (3.5% del lote total, acorde a la naturaleza predominantemente mecánica del sistema)
- **DTC en nivel L1:** **0** (Prohibición absoluta cumplida al 100%; `requiere_pregunta = SI` en los 50 casos L1)
- **DTC en nivel L2:** **3**
- **DTC en nivel L3:** **4**
- **Casos L2/L3 SIN DTC:** **143** (95.3% de L2/L3 se basan estrictamente en condiciones operativas mecánicas, cinemáticas, metrológicas y de transferencia de peso, previniendo atajos de aprendizaje)
- **Validación Sintáctica Regex (`^[PBCU][0-9A-Fa-f]{4}$`):** 100% de los códigos cumplen el estándar SAE J2012 / OBD-II.
- **Distribución de DTC por Clase:**
  - Clase 42 (Amortiguadores / Bujes): 0 DTC (sistema mecánico y elastomérico puro)
  - Clase 43 (Homocinéticas / Palieres): 0 DTC (transmisión mecánica articulada)
  - Clase 44 (Llantas desbalanceadas / desalineadas): 0 DTC (geometría y balanceo dinámico)
  - Clase 45 (Cremallera de dirección asistida): 5 DTCs (`C1511`, `C1512`, `C1521`, `C1532` en sistemas EPS/EHPS)
  - Clase 46 (Rodamiento de maza): 2 DTCs (`C0035`, `C0040` por desacople o daño de pista magnética ABS integrada)

### B. Casos Contrastivos
- **Total contrastivos (`es_contrastivo=SI`):** 142 registros (71.0% del lote)
- **Validación taxonómica:** 100% de las etiquetas `clase_contrastiva` coinciden con las 61 canónicas del proyecto.
- **Colisiones directas (`clase_contrastiva == clase_objetivo`):** 0 colisiones.
- **Contrastes Fundamentales Implementados:**
  - **42 vs 44:** Golpe sordo o cascabeleo al circular sobre baches, rompemuelles o calzadas irregulares frente a vibración rítmica del volante generada estrictamente a velocidad constante en calzada lisa.
  - **42 vs 45:** Golpeteo en tren delantero por bujes cuarteados (con desplazamiento longitudinal de rueda al frenar) frente a holgura o juego muerto en el volante al zigzaguear en detenido o golpeteo transmitido directamente a la columna de dirección.
  - **43 vs 46:** Chasquido discontinuo metálico (`clic-clic-clic` o `trac-trac`) en homocinética exterior que aparece únicamente al doblar cerrado con tracción/par de aceleración frente a zumbido grave continuo tipo turbina en rodamiento de maza que se manifiesta en línea recta y cambia según transferencia de carga lateral.
  - **43 vs 44:** Sacudida transversal de la trompa del auto producida por la junta trípode interior bajo aceleración fuerte que desaparece instantáneamente al soltar gas o engranar neutro frente a desbalanceo de neumáticos que persiste idéntico a esa velocidad tanto acelerando como en neutro.
  - **44 vs 28 (Llantas vs Discos alabeados):** Distinción canónica de tesis: vibración de volante o carrocería en rango de velocidad (85–110 km/h) rodando en crucero SIN pisar el freno frente a vibración pulsátil generada ÚNICAMENTE al presionar el pedal de freno.
  - **46 vs 37 (Rodamiento de rueda vs Rodajes de diferencial):** El diferencial aúlla y varía de tono acústico entre aceleración y retención (drive vs coast); el rodamiento de rueda zumba idéntico acelerando, soltando el acelerador o rodando en punto muerto a velocidad.
  - **46 vs 41 (Rodamiento de rueda vs Eje primario de caja):** El eje primario zumba con el auto detenido en ralentí con embrague acoplado y se silencia al presionar el pedal; el rodamiento de rueda solo zumba cuando el vehículo rueda físicamente en la pista.

---

## 4. Auditoría de Duplicados, Near-Duplicates y Fuga (Leakage)

Se confrontaron los 200 textos del Lote 08 contra un corpus consolidado de **8,121 registros de referencia**:
- Lotes previos Fase 10 (L01 a L07 = 1640 casos)
- TRAIN canónico (`dataset_sintomas_limpio.csv` = 2,481 casos)
- DEV-60 (`benchmark_dev_60_casos.py`)
- TEST Ciego 100 (`benchmark_test_ciego_100.py`)
- Benchmarks G1 y G2 (`benchmark_v4_g1_casos.py`, `benchmark_v4_g2_casos.py`)
- Muestra de campo real de 60 casos de taller de la tesis (`casos_reales_mecanicos_evaluacion.csv`)

### Métricas de Similitud Vectorial (TF-IDF sublinear unigrama/bigrama):
| Métrica | Umbral Máximo Permitido | Valor Observado en Lote 08 | Estado |
|---|:---:|:---:|:---:|
| **Duplicados exactos intra-lote** | 0 | 0 | **CONFORME** |
| **Duplicados exactos inter-referencias** | 0 | 0 | **CONFORME** |
| **Similitud máxima intra-lote** | < 0.90 | **0.3728** | **CONFORME** |
| **Similitud máxima contra referencias (leakage)** | < 0.88 | **0.5688** | **CONFORME** |
| **Near-duplicates detectados** | 0 | 0 | **CONFORME** |

---

## 5. Validación Especial de Condición Operacional y Arquitectura (Secciones 27 y 28)

- **Condición Operacional (Sección 27):** 100% de los registros L2 y L3 incorporan variables operacionales explícitas (velocidades en km/h, comportamiento en curvas vs rectas, tracción vs neutro, estados de bache/asfalto, aceleración vs inercia, mediciones metrológicas de alineación/balanceo/holguras). Cero síntomas abstractos o descontextualizados.
- **Arquitectura de Dirección (Sección 28):**
  - **Sistemas Hidráulicos Puros:** Fugas de fluido ATF Dexron III o CHF 11S en retenes, fuelles inflados de aceite, chirrido de bomba hidráulica en topes de cremallera.
  - **Sistemas Eléctricos EPS Puros:** Holguras de casquillo de teflón, golpeteo de barra en adoquines, descalibración de sensor de torque (`C1511`), cortes por sobrecorriente de motorreductor (`C1532`). **0 casos de fugas hidráulicas atribuidas a sistemas EPS eléctricos puros**.
  - **Sistemas Electrohidráulicos EHPS:** Electrobomba con motor sumergido (`C1521`) y circuito presurizado asistido.
- **Resultado de la validación:** **0 inconsistencias o mezclas erróneas de arquitectura**.

---

## 6. Auditoría Técnica Manual / Semántica (Muestra de 33 Casos)

Se realizó una revisión manual exhaustiva sobre 33 casos estratificados (25 base: 5 por cada una de las 5 clases + 3 extra Clase 43 + 3 extra Clase 46 + 2 extra contraste Clase 44 vs 28):

1. **Clase 42 (Amortiguadores reventados o bujes de suspensión gastados):**
   - `F10-L08-0001` (L1): Golpe seco en bache o rompemuelles; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L08-0011` (L2): Golpe sordo a 30 km/h en bache que no vibra en pista lisa a 100 km/h; contrasta con desbalanceo de llantas. Conforme.
   - `F10-L08-0012` (L2): Amortiguador delantero con fuga de aceite y rebote triple en resaltos; contrasta con caliper trabado. Conforme.
   - `F10-L08-0026` (L3): Banco Eusama acusa adherencia de 24% y desequilibrio del 52% con fuga en vástago cromado rayado. Conforme.
   - `F10-L08-0027` (L3): Barra de palanca en fosa constata desgarro de silentblock con juego radial de 6.2 mm y desplazamiento longitudinal de 15 mm al frenar. Conforme.

2. **Clase 43 (Juntas homocinéticas o palieres dañados):**
   - `F10-L08-0041` (L1): Trac-trac-trac rápido al girar cerrado a la derecha con acelerador pisado; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L08-0051` (L2): Matraca de 5 a 6 clics por segundo en 2da acelerando al girar cerrado que silencia en recta; contrasta con rodamiento. Conforme.
   - `F10-L08-0053` (L2): Vibración transversal entre 70 y 90 km/h bajo aceleración que cesa en neutro; contrasta con llantas desbalanceadas. Conforme.
   - `F10-L08-0066` (L3): Radio de giro de 5.5 m a 120 Nm acusa golpeteo de 84 dBA a 4.8 Hz en homocinética exterior con fuelle desgarrado. Conforme.
   - `F10-L08-0067` (L3): Oscilación lateral de 2.4 mm a 18 Hz bajo par motor que cesa al soltar gas por pistas de tulipán marcadas 1.1 mm. Conforme.
   - *(Extra Homocinéticas)* `F10-L08-0042` (L1): Chasquido continuo en rueda al doblar esquinas acelerando. Conforme.
   - *(Extra Homocinéticas)* `F10-L08-0043` (L1): Vibración en trompa al acelerar en subida bajo carga. Conforme.
   - *(Extra Homocinéticas)* `F10-L08-0044` (L1): Sonido de matraca metálica al girar timón para estacionar. Conforme.

3. **Clase 44 (Llantas desbalanceadas o desalineadas):**
   - `F10-L08-0081` (L1): Volante empieza a temblar fuerte a más de 80 km/h en carretera; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L08-0091` (L2): Vibración oscilatoria entre 85 y 105 km/h que no ocurre al frenar ni por debajo de 70; contrasta con discos alabeados. Conforme.
   - `F10-L08-0092` (L2): Vehículo deriva 2 m a la derecha en 5 s a 100 km/h con volante desfasado 10°; contrasta con caliper trabado. Conforme.
   - `F10-L08-0106` (L3): Balanceadora dinámica registra 45g exterior y 25g interior; contrapesos reducen amplitud de 3.8 a 0.2 m/s2 sin vibrar al frenar. Conforme.
   - `F10-L08-0107` (L3): Alineadora 3D CCD mide divergencia de -0°54' y desequilibrio de camber de 1°48' con deriva de 3.5 m en 100 m. Conforme.
   - *(Extra Contraste 44 vs 28)* `F10-L08-0097` (L2): Vibración idéntica a 95 km/h acelerando o en neutro con frenado parejo sin pulsaciones. Conforme.
   - *(Extra Contraste 44 vs 28)* `F10-L08-0109` (L3): Corolla con temblor de timón a 90 km/h que desaparece a 70 y 120 km/h y frena parejo sin vibrar. Conforme.

4. **Clase 45 (Cremallera de dirección asistida con holgura o fuga):**
   - `F10-L08-0121` (L1): Timón con juego muerto central y golpecito al moverlo; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L08-0131` (L2): Fuga de ATF por retenes laterales con guardapolvos inflados; contrasta con fuga de frenos. Conforme.
   - `F10-L08-0132` (L2): EPS con DTC `C1511` por endurecimiento en maniobras lentas; contrasta con bujes de suspensión. Conforme.
   - `F10-L08-0146` (L3): Banco de presión acusa caída de 105 a 32 bar al solicitar tope con 350 ml de ATF acumulado en fuelle por retén gastado. Conforme.
   - `F10-L08-0147` (L3): Yaris EPS con DTC `C1511`: sensor de torque a 3.82 V (nominal 2.50 V) con desfase de 4.8 Nm en reposo que dispara relé de seguridad. Conforme.

5. **Clase 46 (Rodamiento de maza o rodaje de rueda picado):**
   - `F10-L08-0161` (L1): Zumbido grave tipo avión bimotor que aumenta con la velocidad; `requiere_pregunta=SI`, sin DTC. Conforme.
   - `F10-L08-0171` (L2): Zumbido a partir de 60 km/h que aumenta al doblar a la derecha (cargando rueda izquierda) y disminuye a la izquierda; contrasta con diferencial. Conforme.
   - `F10-L08-0172` (L2): A 90 km/h en autopista el zumbido se mantiene idéntico en neutro o con embrague pisado; no varía con RPM de motor; contrasta con eje primario. Conforme.
   - `F10-L08-0186` (L3): Sonómetro FFT acusa resonancia en 385 Hz a 80 km/h que sube a 87 dBA en curva derecha y cae a 61 dBA a la izquierda e idéntico en neutro. Conforme.
   - `F10-L08-0195` (L3): DTC `C0040` por descentramiento de 0.28 mm en maza picada que separa intermitentemente el anillo fónico del sensor ABS. Conforme.
   - *(Extra Rodamientos)* `F10-L08-0162` (L1): Rueda delantera zumba fuertísimo en carretera desde 60 km/h. Conforme.
   - *(Extra Rodamientos)* `F10-L08-0163` (L1): Bramido sordo constante en rueda derecha en línea recta. Conforme.
   - *(Extra Rodamientos)* `F10-L08-0164` (L1): Zumbido que cambia de tono al doblar en curvas de carretera. Conforme.

---

## 7. Clasificación Final de Auditoría

- **Aprobados:** 200 / 200 (100.0%)
- **Revisar:** 0 / 200 (0.0%)
- **Rechazados:** 0 / 200 (0.0%)

**Dictamen:** Lote 08 (SUSPENSIÓN Y CHASIS) plenamente calificado para su consolidación controlada en `dataset_fase10_master.csv`.
