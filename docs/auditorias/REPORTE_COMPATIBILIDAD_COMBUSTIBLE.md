# Auditoría y Control de Compatibilidad de Combustible — CarBot 48 Clases

**Fecha:** 2026-09-19  
**Norma Operacional:** Regla 5 de Auditoría Experimental CarBot  

## 1. Resumen de Distribución de Compatibilidad

- **Total Clases Auditadas:** 48
- **Exclusivas GASOLINE:** 7 (14.6%)
- **Exclusivas DIESEL:** 1 (2.1%)
- **Compatibles con Ambos (BOTH):** 40 (83.3%)
- **Indeterminadas (UNKNOWN):** 0 (0.0% - Sin forzar conversiones artificiales)

## 2. Reglas de Exclusión Termodinámica y Mecánica

| Clase CarBot | Compatibilidad | Fundamento Técnico y Físico | Relevancia en Taller |
|---|---|---|---|
| **Alternador defectuoso o con baja carga** | `BOTH` | Sistema de generación y rectificación trifásica común a vehículos gasolina y diésel. | Crítica. |
| **Amortiguadores desgastados o con fuga** | `BOTH` | Elementos de amortiguación hidráulica y neumática del chasis. | Crítica. |
| **Bajo nivel de liquido de transmision o fuga** | `BOTH` | Lubricante de transmisión manual o fluído ATF en automáticas. | Alta. |
| **Bateria descargada o en mal estado** | `BOTH` | Subsistema de acumulación eléctrica de 12V/24V universal en todo vehículo automotor. | Crítica. |
| **Bomba de agua defectuosa** | `BOTH` | Bomba centrífuga mecánica o eléctrica de refrigeración común. | Alta. |
| **Bomba de combustible defectuosa o baja presion** | `GASOLINE` | En CarBot tipificada como bomba de gasolina sumergida en tanque (baja presión 3-4 bar). En diésel se clasifica en Common Rail (alta presión >1600 bar). | Alta. |
| **Bomba principal de freno defectuosa** | `BOTH` | Cilindro maestro tándem hidráulico universal. | Crítica. |
| **Consumo de aceite por desgaste de anillos o retenes** | `BOTH` | Desgaste tribológico en cilindros y guías de válvulas común a gasolina y diésel. | Alta. |
| **Convertidor catalitico obstruido o degradado** | `GASOLINE` | Monitoreo DTC P0420/P0430 exclusivo para catalizadores de 3 vías de gasolina. El diésel utiliza catalizador de oxidación diésel (DOC) y filtro DPF. | Alta. |
| **Cuerpo de aceleracion o valvula IAC sucia** | `GASOLINE` | El ralentí controlado por válvula IAC y estrangulamiento por mariposa es característico de motores de gasolina. El diésel no regula potencia por estrangulación de aire (posee mariposa solo para apagado suave EGR). | Alta. |
| **Desalineacion o desbalanceo de ruedas** | `BOTH` | Geometría vehicular de tren delantero y conjunto llanta-neumático. | Crítica. |
| **Desgaste de pastillas o zapatas de freno** | `BOTH` | Sistema de fricción de frenado independiente del tren motriz. | Crítica. |
| **Desgaste en junta homocinetica (palier)** | `BOTH` | Semiejes de tracción y juntas homocinéticas Rzeppa o trípode. | Crítica. |
| **Desgaste en rotulas o terminales de direccion** | `BOTH` | Componentes cinemáticos de suspensión y dirección. | Crítica. |
| **Discos o tambores de freno desgastados o deformados** | `BOTH` | Material de fricción y disipación térmica en ruedas independiente del combustible. | Crítica. |
| **Embrague desgastado o patinando (transmision manual)** | `BOTH` | Conjunto plato, disco y collarín en cajas de cambio manuales. | Crítica. |
| **Falla en bujias o bobinas de encendido (fallo de encendido)** | `GASOLINE` | Los motores diésel operan por autoignición por compresión y no poseen bujías de chispa ni bobinas de encendido (utilizan bujías de incandescencia / calentadores para arranque en frío). | Crítica. Evita sugerir cambio de bobinas/bujías a camionetas o camiones diésel. |
| **Falla en cableado o sulfatacion de tierras de chasis** | `BOTH` | Conexiones de masa de chasis y mazos eléctricos. | Alta. |
| **Falla en canister o valvula de purga EVAP** | `GASOLINE` | El sistema EVAP captura vapores volátiles de gasolina. El combustible diésel tiene bajísima volatilidad a temperatura ambiente y los vehículos diésel no equipan canister EVAP. | Muy alta. Ningún diésel tiene código P0440/P0442 de EVAP. |
| **Falla en compresor o fuga de gas de aire acondicionado** | `BOTH` | Circuito frigorífico R134a/R1234yf de confort en habitáculo. | Alta. |
| **Falla en inyectores de combustible (obstruccion o fuga)** | `BOTH` | Tanto gasolina (MPFI/GDI) como diésel (Common Rail/bomba inyectora) cuentan con inyectores electromagnéticos o piezoeléctricos. | Alta. |
| **Falla en relay o fusible del sistema de encendido/inyeccion** | `BOTH` | Distribución eléctrica mediante relés y fusibles de potencia en caja BSM/IPDM/fusiblera. | Alta. |
| **Falla en sensor de detonacion (Knock Sensor)** | `GASOLINE` | Sensor piezoeléctrico para detección de autoencendido prematuro/pistoneo en motores de gasolina. En diésel la combustión es por autoignición natural. | Alta. |
| **Falla en sensor de pedal de freno o embrague** | `BOTH` | Interruptores de posición de pedal para corte de inyección, control crucero y luces. | Media. |
| **Falla en sensor de posicion del acelerador (TPS)** | `BOTH` | Ambos tipos de motorización moderna utilizan sensor de posición de acelerador (pedal o mariposa electrónica). | Media. |
| **Falla en sensor de temperatura del refrigerante (ECT)** | `BOTH` | Termistor NTC presente en el circuito de refrigeración de cualquier motor de combustión. | Alta. |
| **Falla en sensor de velocidad del vehiculo (VSS)** | `BOTH` | Sensor de transmisión o ruedas para cálculo de odometría y velocímetro. | Alta. |
| **Falla en solenoides de transmision automatica** | `BOTH` | Cuerpo valvular electrohidráulico en transmisiones automáticas. | Alta. |
| **Falla en termostato o motoventilador de radiador** | `BOTH` | Sistema térmico de regulación de temperatura del refrigerante universal. | Alta. |
| **Falla en valvula PCV** | `BOTH` | Ventilación positiva del cárter (PCV en gasolina, separador de vapores de aceite / blow-by en diésel). | Media. |
| **Filtro de aire obstruido o sucio** | `BOTH` | Elemento de filtrado de aire de admisión universal. | Alta. |
| **Filtro de cabina obstruido o ventilador defectuoso** | `BOTH` | Sistema de ventilación y climatización HVAC del habitáculo. | Media. |
| **Filtro de combustible obstruido** | `BOTH` | Ambos sistemas requieren filtración de combustible (especialmente crítico en diésel con trampa de agua). | Alta. |
| **Fuga de aceite de motor (empaquetadura o reten)** | `BOTH` | Retenes de cigüeñal, empaquetaduras de carter y tapa de balancines presentes en todo motor. | Alta. |
| **Fuga de liquido de frenos o aire en el circuito** | `BOTH` | Circuito hidráulico DOT 3/4 o neumático independiente del tipo de combustible. | Crítica. |
| **Fuga de liquido refrigerante (manguera, radiador o bomba de agua)** | `BOTH` | Circuito hidráulico de enfriamiento presurizado común a todos los motores. | Alta. |
| **Fuga de vacio en el multiple de admision** | `GASOLINE` | En gasolina la mariposa genera vacío significativo en el múltiple. Los diésel no generan vacío de admisión por mariposa (requieren depresor/bomba de vacío para el servofreno). | Alta. |
| **Fuga en conducto de sobrealimentacion o manguera de turbo rajada** | `BOTH` | Mangueras de intercooler y conductos de presión turbo presentes en gasolina turbo y diésel turbo. | Crítica. |
| **Fuga en sistema de escape o silenciador roto** | `BOTH` | Línea de escape de gases posterior al colector de escape. | Media. |
| **Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)** | `DIESEL` | Sistema de inyección por acumulador de ultra alta presión (1600-2500 bar) con bomba de alta presión diésel (CP1/CP3/CP4) y válvula SCV/DRV. | Crítica. Incompatible con vehículos livianos convencionales a gasolina. |
| **Motor de arranque defectuoso o solenoide pegado** | `BOTH` | Motor de arranque eléctrico de corriente continua común a ambas tecnologías. | Crítica. |
| **Sensor de flujo de masa de aire (MAF) defectuoso o sucio** | `BOTH` | Equipado ampliamente en motores gasolina y diésel modernos para cálculo de carga y control de EGR. | Alta. |
| **Sensor de oxigeno defectuoso** | `BOTH` | Obligatorio en gasolina y presente como sensor lambda de banda ancha en diésel Euro 5 y Euro 6. | Alta. |
| **Sensor de posicion del arbol de levas (CMP) defectuoso** | `BOTH` | Indispensable para inyección secuencial tanto en motores diésel como gasolina. | Crítica. |
| **Sensor de posicion del ciguenal (CKP) defectuoso** | `BOTH` | Sensor inductivo o Hall universal e indispensable para sincronización en cualquier motor de combustión interna. | Crítica. |
| **Sensor de presion absoluta del multiple (MAP) defectuoso** | `BOTH` | Utilizado en motores atmosféricos y turboalimentados de gasolina y diésel para medir presión absoluta y boost. | Alta. |
| **Soporte de motor o transmision roto o vencido** | `BOTH` | Soportes elastoméricos o hidráulicos de absorción vibratoria. | Alta. |
| **Valvula EGR atascada o defectuosa** | `BOTH` | La recirculación de gases de escape para control de NOx se emplea ampliamente en motores diésel y gasolina. | Muy alta. |

## 3. Matriz de Incompatibilidades a Penalizar en Diagnóstico

Cualquier consulta donde el mecánico declare explícitamente el tipo de combustible aplicará la siguiente penalización rígida:

1. **Vehículo DIESEL:**
   - Se bloquean hipótesis de: `bujías`, `bobinas de encendido`, `GDI`, `canister EVAP`, `bomba de gasolina`, `válvula IAC`.
2. **Vehículo GASOLINE:**
   - Se bloquean hipótesis de: `Common Rail Diesel`, `filtro de partículas DPF/FAP`, `válvula SCV`, `bomba CP3/CP4`, `AdBlue/DEF`.
3. **Vehículo con combustible NO ESPECIFICADO (UNKNOWN):**
   - Se mantiene la distribución probabilística pura de la SVM sin sesgo forzado.
