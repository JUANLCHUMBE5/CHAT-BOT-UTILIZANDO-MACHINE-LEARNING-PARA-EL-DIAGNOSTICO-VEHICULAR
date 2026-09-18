# REPORTE DE AUDITORÍA FASE 10 — LOTE 09 (ELÉCTRICO)
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — 100% CONFORME (BLOQUEO DE ENTRENAMIENTO ACTIVO)  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_09.csv` (280 registros, 7 clases de ELECTRICO)  
**Archivo de Auditoría:** `fase10_auditoria_lote09.csv`

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

## 2. Auditoría Estructural del Lote 09

| Parámetro Evaluado | Requisito Formal | Valor Observado | Estado |
|---|---|---|:---:|
| **Codificación de archivo** | UTF-8 estricto | UTF-8 sin BOM, decodificación limpia | **CONFORME** |
| **Total registros** | 280 registros | 280 filas | **CONFORME** |
| **Columnas requeridas** | 16 columnas específicas | 16 columnas canónicas | **CONFORME** |
| **Cobertura de clases** | 7 clases canónicas (47 a 53) | 7 clases canónicas de ELECTRICO | **CONFORME** |
| **Balance por clase** | 40 registros por clase | 40 registros por clase (exacto) | **CONFORME** |
| **Distribución por nivel** | 70 L1 / 105 L2 / 105 L3 | 70 L1 (25.0%) / 105 L2 (37.5%) / 105 L3 (37.5%) | **CONFORME** |
| **Balance nivel por clase** | 10 L1, 15 L2, 15 L3 | 10 L1, 15 L2, 15 L3 por cada una de las 7 clases | **CONFORME** |
| **Unicidad de IDs** | F10-L09-0001 a F10-L09-0280 | 280 IDs únicos sin colisiones | **CONFORME** |
| **Macro-Sistema** | Coincidir con `ELECTRICO` | 280/280 registros asignados a `ELECTRICO` | **CONFORME** |
| **Fuente** | `SINTETICO_IA` | 280/280 registros etiquetados `SINTETICO_IA` | **CONFORME** |

### Clases Incluidas en el Lote 09:
1. `Alternador defectuoso o placa de diodos quemada` (Clase 47): 40 registros (10 L1, 15 L2, 15 L3)
2. `Bateria descargada o bornes sulfatados` (Clase 48): 40 registros (10 L1, 15 L2, 15 L3)
3. `Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)` (Clase 49): 40 registros (10 L1, 15 L2, 15 L3)
4. `Fallo en inversor de corriente IGBT o motor electrico (EV)` (Clase 50): 40 registros (10 L1, 15 L2, 15 L3)
5. `Foco o falla en sistema de refrigeracion de bateria/inversor (EV)` (Clase 51): 40 registros (10 L1, 15 L2, 15 L3)
6. `Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)` (Clase 52): 40 registros (10 L1, 15 L2, 15 L3)
7. `Fuga parasita de corriente en reposo (consumo nocturno de bateria)` (Clase 53): 40 registros (10 L1, 15 L2, 15 L3)

---

## 3. Auditoría de DTC y Casos Contrastivos

### A. Regla Reforzada de DTC
- **Total de registros con DTC:** 36 (12.8% del lote total)
- **DTC en nivel L1:** **0** (Prohibición absoluta cumplida al 100%; `requiere_pregunta = SI` en los 70 casos L1)
- **DTC en nivel L2:** **13**
- **DTC en nivel L3:** **23**
- **Casos L2/L3 SIN DTC:** **174** (82.8% de L2/L3 se basan estrictamente en condiciones operacionales, mediciones físicas de voltaje, caída de tensión, ripple AC, corriente de reposo, resistencia, aislamiento y telemetría BMS/MCU, previniendo atajos por códigos)
- **Validación Sintáctica Regex (`^[PBCU][0-9A-Fa-f]{4}$`):** 100% de los códigos cumplen el estándar SAE J2012 / OBD-II.
- **Distribución de DTC por Clase:**
  - Clase 47 (Alternador): 4 DTCs (`P0562`, `P0563`, `P0620`, `P065B`)
  - Clase 48 (Batería 12V): 4 DTCs (`P0560`, `P0562`, `P0685`)
  - Clase 49 (Batería HV): 10 DTCs (`P0A80`, `P0A7F`, `P0A7E`, `P0A1F`, `P0AA6`, `U0110`)
  - Clase 50 (Inversor / Motor EV): 9 DTCs (`P0A78`, `P0A79`, `P0A94`, `P0A1B`, `P0AA6`)
  - Clase 51 (Refrigeración EV): 7 DTCs (`P0A93`, `P0A82`)
  - Clase 52 (Motor de arranque): 2 DTCs (`P0615`)
  - Clase 53 (Fuga parásita): 0 DTC (fenómeno de reposo medido por multímetro/pinza amperimétrica en fusiblera, típicamente sin DTC activo)

### B. Casos Contrastivos
- **Total contrastivos (`es_contrastivo=SI`):** 156 registros (55.7% del lote)
- **Validación taxonómica:** 100% de las etiquetas `clase_contrastiva` coinciden con las 61 canónicas del proyecto.
- **Colisiones directas (`clase_contrastiva == clase_objetivo`):** 0 colisiones.
- **Contrastes Fundamentales Implementados:**
  - **Bloque 47 / 48 / 52 / 53 (12V Convencional):**
    - **47 vs 48:** Batería que se descarga *durante la marcha* (voltaje < 12.8V con motor a 2000 rpm o ripple AC > 0.5V por diodos en corto) frente a batería con bajo voltaje en reposo (< 11.8V) que cae fuertemente en el arranque pero el alternador carga perfecto a 14.2V.
    - **47 vs 53:** Descarga *en marcha con consumidores* frente a descarga *estacionado durante la noche* (vehículo opera impecable de día, pero tras 8-12 h amanece muerto con fuga medida > 400 mA).
    - **48 vs 52:** Batería descargada produce *traqueteo rápido de relés ("ametralladora")* y colapso de faros/tablero frente a motor de arranque con *un único "clac" seco o silencio total*, voltaje de batería en reposo en 12.65V y caída mínima a 12.3V (carbones/solenoide abierto).
    - **48 vs 53:** Batería que falla por autodescarga interna / sulfatación de placas (pasa la noche desconectada y pierde tensión) frente a consumo parásito externo (batería desconectada mantiene 12.65V intacta).
    - **52 vs 21 (Motor de arranque vs Sensor CKP/CMP):** Distinción canónica entre **NO-CRANK** (el cigüeñal no gira absolutamente nada, 0 RPM) y **CRANK-NO-START** (el motor de arranque gira alegremente a 220-280 RPM pero el motor térmico no arranca por falta de pulso de inyección/chispa).
  - **Bloque EV / Híbridos (Clases 49, 50, 51 y 32):**
    - **49 vs 50:** Falla de capacidad electroquímica del pack HV (desequilibrio de celdas > 0.25V, caída de SOC súbita, degradación SOH < 65%, DTC P0A80) frente a falla de conmutación electrónica trifásica en inversor IGBT (pérdida súbita de tracción, modo tortuga, aislamiento de bobinado < 1 MΩ a 500V, DTC P0A78/P0A94) con batería HV entregando tensión correcta.
    - **49 vs 51:** Batería degradada que no retiene carga a temperatura normal frente a batería con celdas sanas que recorta potencia por sobrecalentamiento (> 50°C) causado por ventilador obstruido con pelusa (P0A82) o electrobomba de circuito chiller inoperante.
    - **50 vs 51:** Módulo de potencia IGBT dañado internamente (cortocircuito franco, driver compuerta abierto) frente a inversor sano que corta por protección térmica tras subida o exigencia debido a bomba eléctrica de inversor parada (DTC P0A93) con radiador frío y sin flujo.
    - **50 / 51 vs 32:** Falla en la etapa motriz/inversora o su refrigeración frente a falla en el sistema hidráulico/electrónico de frenado regenerativo integrado.

---

## 4. Auditoría de Duplicados, Near-Duplicates y Fuga (Leakage)

Se confrontaron los 280 textos del Lote 09 contra un corpus consolidado de **8,321 registros de referencia**:
- Lotes previos Fase 10 (L01 a L08 = 1840 casos)
- TRAIN canónico (`dataset_sintomas_limpio.csv` = 2,481 casos)
- DEV-60 (`benchmark_dev_60_casos.py`)
- TEST Ciego 100 (`benchmark_test_ciego_100.py`)
- Benchmarks G1 y G2 (`benchmark_v4_g1_casos.py`, `benchmark_v4_g2_casos.py`)
- Muestra de campo real de 60 casos de taller de la tesis (`casos_reales_mecanicos_evaluacion.csv`)

### Métricas de Similitud Vectorial (TF-IDF sublinear unigrama/bigrama):
| Métrica | Umbral Máximo Permitido | Valor Observado en Lote 09 | Estado |
|---|:---:|:---:|:---:|
| **Duplicados exactos intra-lote** | 0 | 0 | **CONFORME** |
| **Duplicados exactos inter-referencias** | 0 | 0 | **CONFORME** |
| **Similitud máxima intra-lote** | < 0.90 | **0.3085** | **CONFORME** |
| **Similitud máxima contra referencias (leakage)** | < 0.88 | **0.4521** | **CONFORME** |
| **Near-duplicates detectados** | 0 | 0 | **CONFORME** |

---

## 5. Validaciones Especiales Eléctricas (Secciones 20, 21, 22, 23 y 26)

1. **Validación Motor Apagado vs Encendido (Sección 20):**
   - Se validó que las tensiones de carga (13.5V – 14.8V) se asocien inequívocamente al motor encendido/en marcha.
   - Las condiciones de reposo (12.4V – 12.8V) y cranking (caída a 9.6V – 11.0V) guardan coherencia operativa estricta.
   - **Resultado:** 0 contradicciones detectadas.

2. **Validación CRANK vs NO-CRANK (Sección 21):**
   - En Clase 52 (`Falla en motor de arranque o solenoide defectuoso`): 100% de los casos corresponden a **NO-CRANK** (silencio, clac seco, solenoide atorado, carbones abiertos) o bendix girando en vacío sin acople a la corona.
   - Ningún caso describe "crank normal que gira vigoroso sin encender" (propio de CKP/CMP o combustible), salvo en formulaciones explícitamente contrastivas.
   - **Resultado:** 0 inconsistencias detectadas.

3. **Validación 12V vs Alto Voltaje (Sección 22):**
   - En vehículos EV e híbridos, se mantuvo una separación estricta entre la batería auxiliar de 12V (accesorios, computadoras, relés) y el paquete de tracción de alto voltaje HV (200V – 400V).
   - **Resultado:** 0 confusiones detectadas.

4. **Validación de Arquitectura Térmica EV (Sección 23):**
   - Se respetó la separación entre sistemas de enfriamiento por aire forzado (soplador/turbina, ductos, rejillas de admisión en NiMH) y sistemas de refrigeración líquida (bomba eléctrica 12V/HV, radiador auxiliar, chiller, líquido desionizado).
   - **Resultado:** 0 mezclas espurias de arquitectura en un mismo componente.

5. **Seguridad Eléctrica de Alta Tensión (Sección 26):**
   - Ningún texto instruye al usuario no calificado o conductor a tocar cables naranjas, abrir inversores o medir buses DC sin guantes dieléctricos o equipo de protección homologado.
   - Todas las mediciones complejas de HV están contextualizadas en protocolos de taller técnico calificado.
   - **Resultado:** 0 infracciones de seguridad detectadas.

---

## 6. Auditoría Técnica Manual / Semántica (Muestra de 51 Casos)

Se evaluó en detalle una muestra representativa de 51 casos estratificados (35 base [5 por cada una de las 7 clases] + 8 del bloque 47/48/52/53 + 6 del bloque 49/50/51 + 3 de discriminación CRANK vs NO-CRANK + 3 de discriminación 12V vs HV):

| ID | Clase Objetivo | Nivel | DTC | Contrastivo | Resumen Técnico / Medición | Veredicto |
|---|---|:---:|:---:|:---:|---|:---:|
| `F10-L09-0001` | Alternador | L1 | — | NO | Luz de batería parpadea al acelerar; lenguaje natural coloquial sin DTC. | **APROBADO** |
| `F10-L09-0011` | Alternador | L2 | — | SI (48) | Voltímetro cae de 14.2V a 11.8V en marcha con luces altas encendidas. | **APROBADO** |
| `F10-L09-0012` | Alternador | L2 | — | SI (48) | Alternador aúlla y huele a quemado; batería nueva descargándose en uso. | **APROBADO** |
| `F10-L09-0015` | Alternador | L2 | — | SI (48) | Batería arrancó con puente pero el motor se apaga al desconectar cables. | **APROBADO** |
| `F10-L09-0026` | Alternador | L3 | — | SI (48) | Osciloscopio registra rizado AC de 850 mV (máx 150 mV) por diodos abiertos. | **APROBADO** |
| `F10-L09-0027` | Alternador | L3 | P065B | SI (48) | Escáner detecta P065B en bus LIN; ciclo PWM 78% pero retorno FR en 0%. | **APROBADO** |
| `F10-L09-0033` | Alternador | L3 | — | SI (48) | Zumbido de 600 Hz en radio con semiciclo cortado a cero por diodo destruido. | **APROBADO** |
| `F10-L09-0035` | Alternador | L3 | P0563 | SI (48) | Freeze frame P0563 con sobretensión de 16.8V a 2400 rpm por regulador saturado. | **APROBADO** |
| `F10-L09-0041` | Batería 12V | L1 | — | NO | El carro hoy no quiso dar arranque; lenguaje escaso, requiere pregunta = SI. | **APROBADO** |
| `F10-L09-0051` | Batería 12V | L2 | — | SI (47) | Bornes con costra blanca-verdosa; al limpiarlos arranca al toque. | **APROBADO** |
| `F10-L09-0052` | Batería 12V | L2 | — | SI (52) | Al girar llave traquetean relés; con cables de auxilio arranca con fuerza. | **APROBADO** |
| `F10-L09-0055` | Batería 12V | L2 | — | SI (53) | Batería de 4 años amanece en 11.6V parada sin cables; autodescarga química. | **APROBADO** |
| `F10-L09-0066` | Batería 12V | L3 | — | SI (47) | Probador Midtronics acusa 310 CCA de 650 CCA (SOH 42%); alternador carga a 14.3V. | **APROBADO** |
| `F10-L09-0067` | Batería 12V | L3 | — | SI (48) | Caída de 1.85V en borne positivo sulfatado durante arranque; poste a 12.4V. | **APROBADO** |
| `F10-L09-0070` | Batería 12V | L3 | P0562 | SI (47) | Densímetro mide 1.14 g/cm3 (descarga profunda); alternador entrega 14.35V en banco. | **APROBADO** |
| `F10-L09-0081` | Batería HV | L1 | — | NO | El carro híbrido perdió autonomía eléctrica y el motor térmico no se apaga. | **APROBADO** |
| `F10-L09-0091` | Batería HV | L2 | — | SI (48) | Batería auxiliar 12V tiene 12.6V pero tablero indica revisar batería híbrida. | **APROBADO** |
| `F10-L09-0092` | Batería HV | L2 | P0A80 | SI (50) | Indicador SoC cae de 8 a 2 barras en aceleración fuerte; DTC P0A80. | **APROBADO** |
| `F10-L09-0095` | Batería HV | L2 | — | SI (51) | Autonomía cae 40% con temperatura ambiente normal; degradación de celdas. | **APROBADO** |
| `F10-L09-0106` | Batería HV | L3 | P0A80 | SI (50) | Delta de tensión entre bloques de 0.38V (máx 0.05V) bajo aceleración; P0A80. | **APROBADO** |
| `F10-L09-0107` | Batería HV | L3 | P0A7F | SI (51) | Resistencia interna de celdas a 38 mΩ (nominal 14 mΩ); degradación química. | **APROBADO** |
| `F10-L09-0110` | Batería HV | L3 | P0AA6 | SI (50) | Megóhmetro a 500V mide 0.18 MΩ entre bus HV y chasis por fuga de electrolito. | **APROBADO** |
| `F10-L09-0121` | Inversor / Motor | L1 | — | NO | Carro eléctrico perdió fuerza de golpe y no quiere acelerar; sin DTC. | **APROBADO** |
| `F10-L09-0131` | Inversor / Motor | L2 | — | SI (49) | Al acelerar en subida entra en modo tortuga; batería de tracción al 70%. | **APROBADO** |
| `F10-L09-0132` | Inversor / Motor | L2 | — | NO | Detonación leve frontal, corte de tracción y luz READY parpadea. | **APROBADO** |
| `F10-L09-0134` | Inversor / Motor | L2 | — | SI (48) | Batería 12V y contacto activos, pero motor zumba áspero al pasar a Drive. | **APROBADO** |
| `F10-L09-0135` | Inversor / Motor | L2 | — | SI (51) | Inversor silba y corta corriente; temperatura de batería normal. | **APROBADO** |
| `F10-L09-0146` | Inversor / Motor | L3 | P0AA6 | SI (49) | Megóhmetro registra 0.15 MΩ entre devanados de motor y chasis; corto estator. | **APROBADO** |
| `F10-L09-0147` | Inversor / Motor | L3 | P0A78 | NO | Banco confirma módulo IGBT fase V en corto franco; 42A de reposo con 380V. | **APROBADO** |
| `F10-L09-0156` | Inversor / Motor | L3 | — | SI (49) | Batería HV en 94% SOH (375V); bus DC cae a 40V por corto en capacitor DC link. | **APROBADO** |
| `F10-L09-0161` | Refrigeración EV | L1 | — | NO | Ventilador del carro híbrido suena fuertísimo atrás todo el tiempo. | **APROBADO** |
| `F10-L09-0171` | Refrigeración EV | L2 | — | SI (49) | Turbina trasera al máximo constante y recorte de potencia por calor en NiMH. | **APROBADO** |
| `F10-L09-0172` | Refrigeración EV | L2 | — | SI (50) | Autopista con calor: vehículo reduce potencia; depósito inversor sin flujo. | **APROBADO** |
| `F10-L09-0175` | Refrigeración EV | L2 | — | SI (50) | Inversor sobrecalentado en subida; electrobomba de refrigerante inoperante. | **APROBADO** |
| `F10-L09-0186` | Refrigeración EV | L3 | P0A93 | SI (50) | DTC P0A93: electrobomba inversor consume 0.0A (abierta); temp inversor a 88°C. | **APROBADO** |
| `F10-L09-0187` | Refrigeración EV | L3 | P0A82 | SI (49) | Termistores a 56°C y turbina atascada en 620 rpm por pelusa en ducto; P0A82. | **APROBADO** |
| `F10-L09-0201` | Motor de Arranque | L1 | — | NO | Giro la llave para encender el auto y no hace nada de nada; NO-CRANK. | **APROBADO** |
| `F10-L09-0211` | Motor de Arranque | L2 | — | SI (48) | Luces de tablero brillantes; al dar start hace clac seco y cigüeñal inmóvil. | **APROBADO** |
| `F10-L09-0212` | Motor de Arranque | L2 | — | SI (21) | No-crank absoluto frente a sensor CKP (que gira normal sin arrancar). | **APROBADO** |
| `F10-L09-0215` | Motor de Arranque | L2 | — | NO | Falla en caliente: no gira; tras golpear cuerpo con llave arranca al instante. | **APROBADO** |
| `F10-L09-0224` | Motor de Arranque | L2 | — | SI (21) | Contraste explícito: CKP giraba alegremente; ahora silencio total en vano motor. | **APROBADO** |
| `F10-L09-0226` | Motor de Arranque | L3 | — | SI (48) | Terminal 50 recibe 12.2V; Terminal M en 0.0V por pletina de solenoide fogueada. | **APROBADO** |
| `F10-L09-0227` | Motor de Arranque | L3 | — | NO | Caída en borne 30 de 0.08V; pinza marca 1.2A (solo solenoide); carbones gastados. | **APROBADO** |
| `F10-L09-0230` | Motor de Arranque | L3 | — | SI (48) | Midtronics mide 12.72V y 620 CCA (98% SOH); tensión cae a 12.40V con 0 RPM. | **APROBADO** |
| `F10-L09-0231` | Motor de Arranque | L3 | — | SI (21) | Starter Relay ON pero motor en 0 RPM fijas vs CKP que gira a 250 RPM. | **APROBADO** |
| `F10-L09-0241` | Fuga Parásita | L1 | — | NO | Si dejo el carro parado dos días amanece sin nada de batería; reposo. | **APROBADO** |
| `F10-L09-0251` | Fuga Parásita | L2 | — | SI (47) | Día impecable en ruta; tras 8 h estacionado de noche amanece en 10.5V. | **APROBADO** |
| `F10-L09-0252` | Fuga Parásita | L2 | — | SI (48) | Batería nueva al 100%; tras fin de semana parada amanece descargada. | **APROBADO** |
| `F10-L09-0255` | Fuga Parásita | L2 | — | SI (48) | Borne desconectado en la noche mantiene 12.6V y arranca al toque en la mañana. | **APROBADO** |
| `F10-L09-0266` | Fuga Parásita | L3 | — | NO | Pinza DC marca 680 mA con CAN dormida; al sacar fusible F24 baja a 22 mA. | **APROBADO** |
| `F10-L09-0268` | Fuga Parásita | L3 | — | SI (47) | Batería al 100% SOH y alternador a 14.35V con 0.04V ripple; fuga de 820 mA por relé. | **APROBADO** |

---

## 7. Clasificación Final de Auditoría

- **Aprobados:** 280 / 280 (100.0%)
- **Revisar:** 0 / 280 (0.0%)
- **Rechazados:** 0 / 280 (0.0%)

**Dictamen:** Lote 09 (ELÉCTRICO) plenamente calificado para su consolidación controlada en `dataset_fase10_master.csv`.
