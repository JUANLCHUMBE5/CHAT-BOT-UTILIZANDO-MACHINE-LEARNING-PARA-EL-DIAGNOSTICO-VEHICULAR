# REPORTE DE AUDITORÍA FASE 10 — LOTE 10 (CLIMATIZACIÓN Y CARROCERÍA)
**Pipeline Controlado de Reentrenamiento, RAG y Validación de CarBot**

**Fecha de ejecución:** 2026-09-17  
**Estado:** AUDITORÍA COMPLETADA — 100% CONFORME (BLOQUEO DE ENTRENAMIENTO ACTIVO)  
**Artefactos Congelados Fase 8.3:** 100% INMUTABLES (19/19 Hashes Verificados)  
**Archivo Auditado:** `dataset_fase10_lote_10.csv` (200 registros, 5 clases)  
**Archivo de Auditoría:** `fase10_auditoria_lote10.csv`

---

## 1. Verificación Estructural y de Taxonomía

| Parámetro | Requisito | Observado | Estado |
|---|---|---|:---:|
| **Total registros** | 200 | 200 | **CONFORME** |
| **Estructura** | 16 columnas canónicas | 16 columnas | **CONFORME** |
| **Clases cubiertas** | 5 clases canónicas (54 a 58) | Clases 54 a 58 | **CONFORME** |
| **Balance numérico** | 40 registros por clase | 40 exactos por clase | **CONFORME** |
| **Distribución niveles** | 50 L1 / 75 L2 / 75 L3 | 50 L1 / 75 L2 / 75 L3 | **CONFORME** |
| **Unicidad IDs** | F10-L10-0001 a F10-L10-0200 | 200 IDs únicos | **CONFORME** |
| **Macros** | CLIMATIZACION (54), CARROCERIA_NEUMATICA (55-58) | Coincidencia 100% | **CONFORME** |

---

## 2. Auditoría de DTC y Casos Contrastivos

- **Total con DTC:** 17 / 200 (8.5%)
- **DTC L1:** 0 (Prohibición absoluta cumplida; 50/50 requiere_pregunta = SI)
- **DTC L2:** 5
- **DTC L3:** 12
- **L2/L3 sin DTC:** 133 / 150 (88.7% sin DTC)
- **Casos Contrastivos (`es_contrastivo=SI`):** 81 registros (100% con etiquetas canónicas válidas, 0 colisiones directas)

---

## 3. Auditoría de Duplicados y Leakage (8,601 Referencias Cotejadas)

| Métrica | Umbral Máximo | Observado | Estado |
|---|:---:|:---:|:---:|
| **Duplicados exactos intra-lote** | 0 | 0 | **CONFORME** |
| **Duplicados exactos contra referencias** | 0 | 0 | **CONFORME** |
| **Similitud máxima intra-lote** | < 0.90 | **0.3566** | **CONFORME** |
| **Similitud máxima contra referencias (leakage)** | < 0.88 | **0.5670** | **CONFORME** |

---

## 4. Auditoría Especial de Clase 54 (Climatización del Habitáculo)

- 40 / 40 registros revisados en detalle.
- Cero confusión con sobrecalentamiento de motor o circuito de refrigerante de motor térmico.
- Cobertura balanceada de presiones de gas (R134a/R1234yf), fugas por sellos de compresor, condensador perforado, evaporador, embragues electromagnéticos abiertos y compresores de desplazamiento variable PWM.
- Independencia total frente al caso histórico fallido (utilizado exclusivamente como regresión externa).

---

## 5. Muestreo Semántico Estratificado (38 Casos Auditados)

| ID | Clase | Nivel | DTC | Contrastivo | Resumen Técnico / Medición | Veredicto |
|---|---|:---:|:---:|:---:|---|:---:|
| F10-L10-0001 | Falla en compresor de aire acondicionado o fuga de gas R134a | L1 | — | NO | Prendo el aire del auto pero solo bota aire tibio por las rejillas. | **APROBADO** |
| F10-L10-0006 | Falla en compresor de aire acondicionado o fuga de gas R134a | L1 | — | NO | Sale aire por las ventilas pero no enfria el habitaculo. | **APROBADO** |
| F10-L10-0007 | Falla en compresor de aire acondicionado o fuga de gas R134a | L1 | — | NO | Se escucha un chillido constante adelante cuando activo el interruptor del AC. | **APROBADO** |
| F10-L10-0008 | Falla en compresor de aire acondicionado o fuga de gas R134a | L1 | — | NO | El enfriamiento del coche se corta a los pocos minutos de prenderlo. | **APROBADO** |
| F10-L10-0009 | Falla en compresor de aire acondicionado o fuga de gas R134a | L1 | — | NO | Noto manchas verdes fosforescentes en unas mangueras del sistema de aire. | **APROBADO** |
| F10-L10-0010 | Falla en compresor de aire acondicionado o fuga de gas R134a | L1 | — | NO | El auto no enfria adentro cuando estoy en el trafico. | **APROBADO** |
| F10-L10-0011 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | SI (Falla en termostato o motoventilador de radiador) | Al encender el boton A/C el ventilador del habitaculo sopla con fuerza pero el aire sale a 28°C... | **APROBADO** |
| F10-L10-0012 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | SI (Falla en termostato o motoventilador de radiador) | El sistema de aire acondicionado enfria algo cuando voy a 90 km/h en autopista, pero al detener... | **APROBADO** |
| F10-L10-0013 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | SI (Falla en termostato o motoventilador de radiador) | Se observa fuga de refrigerante con aceite en la union del condensador frontal; la aguja de tem... | **APROBADO** |
| F10-L10-0014 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | NO | Al oprimir el boton A/C la luz testigo verde enciende pero el embrague electromagnetico del com... | **APROBADO** |
| F10-L10-0015 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | SI (Alternador defectuoso o placa de diodos quemada) | El compresor de climatizacion acopla y desacopla ciclicamente cada 4 segundos; el aire dentro d... | **APROBADO** |
| F10-L10-0016 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | B1422 | NO | Escaneo del modulo de climatizacion HVAC detecta codigo B1422 relativo a circuito del embrague ... | **APROBADO** |
| F10-L10-0017 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | NO | Se escucha un siseo prolongado de gas evaporandose tras la guantera durante 20 segundos cada ve... | **APROBADO** |
| F10-L10-0018 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | SI (Alternador defectuoso o placa de diodos quemada) | Al activar el aire acondicionado el motor vibra fuertemente y emite un chillido agudo de faja; ... | **APROBADO** |
| F10-L10-0019 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | SI (Foco o falla en sistema de refrigeracion de bateria/inversor (EV)) | Vehiculo hibrido reporta inoperatividad de enfriamiento en cabina; la bateria de alto voltaje y... | **APROBADO** |
| F10-L10-0020 | Falla en compresor de aire acondicionado o fuga de gas R134a | L2 | — | SI (Falla en sensor de oxigeno o mezcla rica) | El termometro colocado en la rejilla central marca 22°C con el A/C al maximo y soplador en velo... | **APROBADO** |
| F10-L10-0026 | Falla en compresor de aire acondicionado o fuga de gas R134a | L3 | — | SI (Falla en termostato o motoventilador de radiador) | Conexion de manometros manifold en tomas de servicio R134a a 1500 rpm: linea de baja marca 12 p... | **APROBADO** |
| F10-L10-0027 | Falla en compresor de aire acondicionado o fuga de gas R134a | L3 | — | SI (Falla en termostato o motoventilador de radiador) | Diagnostico de climatizacion automotriz: prueba de presion estatica con motor apagado arroja 15... | **APROBADO** |
| F10-L10-0041 | Falla electrica del cierre centralizado o actuador de puerta | L1 | — | NO | Una de las puertas no echa seguro cuando aprieto el control. | **APROBADO** |
| F10-L10-0051 | Falla electrica del cierre centralizado o actuador de puerta | L2 | — | SI (Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado) | Al presionar el boton de bloqueo en el control remoto tres puertas aseguran de inmediato, pero ... | **APROBADO** |
| F10-L10-0052 | Falla electrica del cierre centralizado o actuador de puerta | L2 | — | SI (Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado) | Con la llave manual la cerradura gira suave y abre el cerrojo sin resistencia, pero el microswi... | **APROBADO** |
| F10-L10-0066 | Falla electrica del cierre centralizado o actuador de puerta | L3 | — | SI (Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado) | Diagnostico de sistema de cierre centralizado con osciloscopio automotriz: al pulsar el comando... | **APROBADO** |
| F10-L10-0067 | Falla electrica del cierre centralizado o actuador de puerta | L3 | — | NO | Medicion de caida de tension en circuito de masa de actuadores de puerta: con punta logica y vo... | **APROBADO** |
| F10-L10-0081 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | L1 | — | NO | La puerta del chofer rebota cuando la intento cerrar suave. | **APROBADO** |
| F10-L10-0091 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | L2 | — | SI (Falla electrica del cierre centralizado o actuador de puerta) | El pestillo electrico acciona y suena con fuerza al presionar el mando, pero la puerta rebota c... | **APROBADO** |
| F10-L10-0092 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | L2 | — | SI (Falla electrica del cierre centralizado o actuador de puerta) | La cerradura quedo totalmente bloqueada mecanicamente por grasa solidificada y polvo acumulado;... | **APROBADO** |
| F10-L10-0106 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | L3 | — | SI (Falla electrica del cierre centralizado o actuador de puerta) | Evaluacion metrologica de alineacion de carroceria y cerradura: el perno cerradero (striker) de... | **APROBADO** |
| F10-L10-0107 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | L3 | — | SI (Falla electrica del cierre centralizado o actuador de puerta) | Diagnostico mecanico de cerradura de puerta: desmontaje de conjunto de chapa revela resorte esp... | **APROBADO** |
| F10-L10-0121 | Elevalunas electrico o guaya de alzacristales rota o trabada | L1 | — | NO | El vidrio de la ventana del conductor no quiere subir. | **APROBADO** |
| F10-L10-0131 | Elevalunas electrico o guaya de alzacristales rota o trabada | L2 | — | NO | Al presionar el boton del alzacristales se escucha claramente el giro del motor electrico dentr... | **APROBADO** |
| F10-L10-0132 | Elevalunas electrico o guaya de alzacristales rota o trabada | L2 | — | SI (Bateria descargada o bornes sulfatados) | La ventana del conductor sube torcida hacia adelante y se atasca a 10 cm del marco superior; la... | **APROBADO** |
| F10-L10-0146 | Elevalunas electrico o guaya de alzacristales rota o trabada | L3 | — | SI (Bateria descargada o bornes sulfatados) | Diagnostico de consumo de corriente en motor alzacristales: pinza amperimetrica acopla en cable... | **APROBADO** |
| F10-L10-0147 | Elevalunas electrico o guaya de alzacristales rota o trabada | L3 | — | NO | Medicion con voltimetro automotriz en conectores de motor de elevalunas: al presionar tecla en ... | **APROBADO** |
| F10-L10-0161 | Limpiaparabrisas o motor pluma quemado | L1 | — | NO | Las plumillas del limpiaparabrisas no se mueven para nada. | **APROBADO** |
| F10-L10-0171 | Limpiaparabrisas o motor pluma quemado | L2 | — | NO | Con la palanca de mando en velocidad 1 y 2 no hay reaccion; al seleccionar velocidad 3 maxima l... | **APROBADO** |
| F10-L10-0172 | Limpiaparabrisas o motor pluma quemado | L2 | — | NO | Al activar los limpiaparabrisas el motor emite un zumbido continuo pero los brazos no se mueven... | **APROBADO** |
| F10-L10-0186 | Limpiaparabrisas o motor pluma quemado | L3 | — | SI (Alternador defectuoso o placa de diodos quemada) | Diagnostico de motor de limpiaparabrisas con pinza amperimetrica: en velocidad baja (Low) el co... | **APROBADO** |
| F10-L10-0187 | Limpiaparabrisas o motor pluma quemado | L3 | — | NO | Inspeccion de sistema de parada automatica (Park Switch): medicion de continuidad con multimetr... | **APROBADO** |

---

## 6. Dictamen Final de Auditoría Lote 10

- **Aprobados:** 200 / 200 (100.0%)
- **Revisar:** 0 / 200 (0.0%)
- **Rechazados:** 0 / 200 (0.0%)

**Dictamen:** Lote 10 plenamente calificado para su consolidación controlada en `dataset_fase10_master.csv`.
