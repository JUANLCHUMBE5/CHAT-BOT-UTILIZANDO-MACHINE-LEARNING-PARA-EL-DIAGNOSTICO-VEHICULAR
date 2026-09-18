# REPORTE DE AUDITORÍA FASE 10 — LOTE 11 (FRENOS NEUMÁTICOS - CAMIONES)
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — 100% CONFORME (BLOQUEO DE ENTRENAMIENTO ACTIVO)  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_11.csv` (120 registros, 3 clases)  
**Archivo de Auditoría:** `fase10_auditoria_lote11.csv`

---

## 1. Verificación Estructural y de Taxonomía

| Parámetro | Requisito | Observado | Estado |
|---|---|---|:---:|
| **Total registros** | 120 | 120 | **CONFORME** |
| **Estructura** | 16 columnas canónicas | 16 columnas | **CONFORME** |
| **Clases cubiertas** | 3 clases canónicas (59 a 61) | Clases 59 a 61 | **CONFORME** |
| **Balance numérico** | 40 registros por clase | 40 exactos por clase | **CONFORME** |
| **Distribución niveles** | 30 L1 / 45 L2 / 45 L3 | 30 L1 / 45 L2 / 45 L3 | **CONFORME** |
| **Unicidad IDs** | F10-L11-0001 a F10-L11-0120 | 120 IDs únicos | **CONFORME** |
| **Macros** | CARROCERIA_NEUMATICA (59, 60, 61) | Coincidencia 100% | **CONFORME** |

---

## 2. Auditoría de Dominio de Camiones Pesados y Seguridad Crítica

- **Dominio Obligatorio:** 100% de los casos pertenecen a sistemas de aire comprimido de vehículos pesados (calderines, compresores bicilíndricos, secadores APS/APU coalescentes, válvulas Treadle E-6, actuadores de resorte combinados tipo 30/30 Maxi-Brake, ajustadores slack adjuster y levas S-cam).
- **Seguridad Crítica:** Cero instrucciones de anulación temeraria, manipulación insegura en carretera o circular sin presión de seguridad. Desarmes de cámaras Maxi-Brake contextualizados en jaula de seguridad certificada o uso de perno caging bolt bajo procedimiento técnico de taller.
- **Diferenciación frente a vehículos ligeros:** Claramente contrastados frente a Clase 27 (fuga de líquido hidráulico DOT) y Clase 31 (caliper hidráulico agarrotado).

---

## 3. Auditoría de DTC y Casos Contrastivos

- **Total con DTC:** 0 / 120 (0.0% — Cumplimiento estricto: la evidencia física, manométrica y neumática es prioritaria en camiones)
- **DTC L1:** 0 (Prohibición absoluta cumplida; 30/30 requiere_pregunta = SI)
- **DTC L2/L3:** 0 (Evidencia neumática 100% pura: bar, psi, L/min, ultrasonido, punto de rocío, metrología de carrera)
- **Casos Contrastivos (`es_contrastivo=SI`):** 58 registros (48.3% del lote con contrastes técnicos de alta resolución: 59 vs 60, 59 vs 61, 60 vs 61, y contra sistemas hidráulicos livianos)

---

## 4. Auditoría de Duplicados y Leakage (8,801 Referencias Cotejadas)

| Métrica | Umbral Máximo | Observado | Estado |
|---|:---:|:---:|:---:|
| **Duplicados exactos intra-lote** | 0 | 0 | **CONFORME** |
| **Duplicados exactos contra referencias** | 0 | 0 | **CONFORME** |
| **Similitud máxima intra-lote** | < 0.90 | **0.4175** | **CONFORME** |
| **Similitud máxima contra referencias (leakage)** | < 0.88 | **0.4482** | **CONFORME** |

---

## 5. Muestreo Semántico Estratificado (25 Casos Auditados)

| ID | Clase | Nivel | Contrastivo | Resumen Técnico / Medición | Veredicto |
|---|---|:---:|:---:|---|:---:|
| `F10-L11-0001` | Fugas de aire o fallos en el sis... | L1 | `NO` | El camion pierde aire de los tanques muy rapido al frenar. | **APROBADO** |
| `F10-L11-0011` | Fugas de aire o fallos en el sis... | L2 | `Fuga hidraulica o aire...` | En tractocamion con frenos de aire puro, al pisar el pedal de freno se escucha escape masi... | **APROBADO** |
| `F10-L11-0012` | Fugas de aire o fallos en el sis... | L2 | `Falla en actuador de r...` | Las mangueras espiraladas rojas y azules de conexion al semirremolque (manitas glad hands)... | **APROBADO** |
| `F10-L11-0013` | Fugas de aire o fallos en el sis... | L2 | `Válvula de freno de ai...` | El compresor bicilindrico de aire de 360 cc tarda 12 minutos en subir de 50 a 100 psi en r... | **APROBADO** |
| `F10-L11-0015` | Fugas de aire o fallos en el sis... | L2 | `Caliper de freno traba...` | Tubería de aire de poliamida de 12 mm en el chasis rozo contra la cardan sufriendo un cort... | **APROBADO** |
| `F10-L11-0016` | Fugas de aire o fallos en el sis... | L2 | `Válvula de freno de ai...` | Al desacoplar la manguera de suministro de aire del semirremolque la valvula de proteccion... | **APROBADO** |
| `F10-L11-0018` | Fugas de aire o fallos en el sis... | L2 | `Falla en actuador de r...` | Fuga de aire constante por la valvula rele trasera de frenos tipo R-12; al soltar el pedal... | **APROBADO** |
| `F10-L11-0020` | Fugas de aire o fallos en el sis... | L2 | `Válvula de freno de ai...` | Al pisar el freno de servicio en camion de 3 ejes el aire escapa hacia la linea de emergen... | **APROBADO** |
| `F10-L11-0021` | Fugas de aire o fallos en el sis... | L2 | `Fuga hidraulica o aire...` | El acople rapido de la suspension neumatica se solto y comparte linea con el deposito auxi... | **APROBADO** |
| `F10-L11-0022` | Fugas de aire o fallos en el sis... | L2 | `Falla en actuador de r...` | Manometro de cabina marca 120 psi estables en marcha pero al frenar cae inmediatamente a 7... | **APROBADO** |
| `F10-L11-0024` | Fugas de aire o fallos en el sis... | L2 | `Caliper de freno traba...` | Diagnostico en modulo EBS de camion pesado referente a discrepancia de presion en circuito... | **APROBADO** |
| `F10-L11-0026` | Fugas de aire o fallos en el sis... | L3 | `Válvula de freno de ai...` | Auditoria de presion segun estandar DOT en camion Freightliner: presion inicial de 125 psi... | **APROBADO** |
| `F10-L11-0027` | Fugas de aire o fallos en el sis... | L3 | `Válvula de freno de ai...` | Diagnostico de tiempo de recuperacion neumática en tractocamion: con motor a 1800 rpm el c... | **APROBADO** |
| `F10-L11-0041` | Válvula de freno de aire o secad... | L1 | `NO` | El secador de aire de mi camion escupe agua con aceite cada rato. | **APROBADO** |
| `F10-L11-0051` | Válvula de freno de aire o secad... | L2 | `Fugas de aire o fallos...` | La valvula de purga del secador de aire Wabco estornuda cada 15 segundos en ralentí, arroj... | **APROBADO** |
| `F10-L11-0052` | Válvula de freno de aire o secad... | L2 | `Falla en actuador de r...` | Al abrir la valvula de drenaje manual del calderin humedo se expulsan 300 ml de emulsion d... | **APROBADO** |
| `F10-L11-0062` | Válvula de freno de aire o secad... | L2 | `Falla en actuador de r...` | Se observa emulsion blanquecina densa en las valvulas de escape rapido del chasis debido a... | **APROBADO** |
| `F10-L11-0063` | Válvula de freno de aire o secad... | L2 | `Falla en actuador de r...` | Al presionar la perilla amarilla del freno de mano el camion demora 20 segundos en liberar... | **APROBADO** |
| `F10-L11-0066` | Válvula de freno de aire o secad... | L3 | `Fugas de aire o fallos...` | Diagnostico de unidad secadora de aire Bendix AD-IS con manometros patron: el gobernador i... | **APROBADO** |
| `F10-L11-0067` | Válvula de freno de aire o secad... | L3 | `NO` | Analisis fisicoquimico de condensado en calderin de regeneracion de 5 Litros: contenido de... | **APROBADO** |
| `F10-L11-0081` | Falla en actuador de resorte o c... | L1 | `NO` | Una rueda del camion se quedo totalmente amarrada y no avanza. | **APROBADO** |
| `F10-L11-0091` | Falla en actuador de resorte o c... | L2 | `Fugas de aire o fallos...` | Con el sistema neumatico cargado a 120 psi, al presionar la perilla amarilla de liberacion... | **APROBADO** |
| `F10-L11-0092` | Falla en actuador de resorte o c... | L2 | `Fugas de aire o fallos...` | Al liberar el freno de parqueo se escucha un torrente de aire saliendo por el agujero de d... | **APROBADO** |
| `F10-L11-0106` | Falla en actuador de resorte o c... | L3 | `Fugas de aire o fallos...` | Diagnostico metrologico de camara combinada resorte-servicio Tipo 30/30 (T30/30) en tracto... | **APROBADO** |
| `F10-L11-0107` | Falla en actuador de resorte o c... | L3 | `Fugas de aire o fallos...` | Evaluacion de estanqueidad interna en camara doble de freno sellada: al aplicar 8.0 bar al... | **APROBADO** |

---

## 6. Dictamen de Aprobación y Consolidación

- **Resultado de Auditoría Lote 11:** 120 / 120 registros APROBADOS (0 REVISAR, 0 RECHAZADOS).
- **Inmutabilidad Fase 8.3:** 19 / 19 hashes verificados intactos.
- **Autorización de Consolidación:** El Lote 11 cumple con todas las directrices técnicas, metodológicas y operacionales para ser consolidado en el Dataset Master de Fase 10, completando los 2,440 registros (61/61 clases).
