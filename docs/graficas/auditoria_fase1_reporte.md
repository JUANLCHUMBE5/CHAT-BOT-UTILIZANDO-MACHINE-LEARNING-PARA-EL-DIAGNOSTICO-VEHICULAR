# REPORTE DE AUDITORÍA FASE 1: DATASET Y CLASIFICADOR LINEAR SVM (48 CLASES)

**Fecha:** 2026-09-15  
**Proyecto:** CarBot - Clasificador Vehicular Multiclase (Tesis UCV 2026)  
**Modelo:** Linear SVM con Calibración Sigmoidea (Platt) y Vectorización TF-IDF (word n-grams 1-2)  
**Dataset Auditado:** `machine_learning/data/dataset_sintomas_limpio.csv` (4,959 registros limpios)

---

## 1. RESUMEN EJECUTIVO DE MÉTRICAS GLOBALES

- **Total de Casos en Dataset:** 4,959 casos
- **Total de Clases Canónicas:** 48 clases
- **Familias Sintomáticas Únicas (sin fuga):** 3,602 grupos
- **Duplicados Exactos de Síntoma:** 0 (0.00%)
- **Duplicados Síntoma + Falla:** 0 (0.00%)
- **Etiquetas Contradictorias:** 0 (0.00%)
- **Partición:** StratifiedGroupKFold (80% Train = 3,968 casos | 20% Test = 991 casos)
- **Train Accuracy:** **99.85%**
- **Holdout Test Accuracy:** **93.14%** (923 aciertos / 68 errores)
- **Macro Precision:** **0.94**
- **Macro Recall:** **0.92**
- **Macro F1-Score:** **0.92**
- **Pares de Confusión en Test:** 48 pares

---

## 2. DISTRIBUCIÓN DEL DATASET (4,959 REGISTROS POR CLASE)

| N° | Clase / Falla Automotriz | Total Registros | % del Dataset | Casos en Test (20%) |
| :---: | :--- | :---: | :---: | :---: |
| 1 | Falla en bujias o bobinas de encendido (misfire) | 301 | 6.07% | 60 |
| 2 | Falla en sensor de oxigeno o mezcla rica | 221 | 4.46% | 44 |
| 3 | Bateria descargada o bornes sulfatados | 217 | 4.38% | 43 |
| 4 | Cuerpo de aceleracion o valvula IAC sucia | 184 | 3.71% | 37 |
| 5 | Desgaste de pastillas y zapatas de freno | 183 | 3.69% | 36 |
| 6 | Alternador defectuoso o placa de diodos quemada | 181 | 3.65% | 36 |
| 7 | Llantas desbalanceadas o desalineadas | 178 | 3.59% | 36 |
| 8 | Juntas homocineticas o palieres danados | 158 | 3.19% | 32 |
| 9 | Amortiguadores reventados o bujes de suspension gastados | 156 | 3.15% | 31 |
| 10 | Inyectores sucios o filtro de combustible obstruido | 149 | 3.00% | 30 |
| 11 | Bomba de gasolina quemada o con baja presion | 145 | 2.92% | 29 |
| 12 | Fuga hidraulica o aire en el sistema de frenos | 140 | 2.82% | 28 |
| 13 | Empaque de culata soplado o danado | 133 | 2.68% | 26 |
| 14 | Consumo de aceite por desgaste de anillos o retenes | 122 | 2.46% | 24 |
| 15 | Falla en termostato o motoventilador de radiador | 122 | 2.46% | 24 |
| 16 | Discos de freno alabeados o desgastados | 120 | 2.42% | 24 |
| 17 | Cremallera de direccion asistida con holgura o fuga | 113 | 2.28% | 22 |
| 18 | Disco de embrague desgastado o patinando | 106 | 2.14% | 21 |
| 19 | Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado | 101 | 2.04% | 20 |
| 20 | Falla en compresor de aire acondicionado o fuga de gas R134a | 101 | 2.04% | 20 |
| 21 | Baja presion de aceite o bomba de aceite defectuosa | 97 | 1.96% | 19 |
| 22 | Faja o cadena de distribucion destensada o con salto de punto | 94 | 1.90% | 19 |
| 23 | Fallo en inversor de corriente IGBT o motor electrico (EV) | 92 | 1.86% | 18 |
| 24 | Falla en bombin o bomba hidraulica de embrague | 87 | 1.75% | 18 |
| 25 | Fuga en mangueras de intercooler o turbocompresor danado | 86 | 1.73% | 17 |
| 26 | Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos) | 84 | 1.69% | 17 |
| 27 | Elevalunas electrico o guaya de alzacristales rota o trabada | 84 | 1.69% | 17 |
| 28 | Falta o degradacion de aceite de caja de cambios | 81 | 1.63% | 16 |
| 29 | Rodajes de caja mecanica o diferencial gastados | 81 | 1.63% | 16 |
| 30 | Fuga en mangueras de refrigerante o radiador picado | 75 | 1.51% | 15 |
| 31 | Falla en servofreno (booster) o linea de vacio | 69 | 1.39% | 13 |
| 32 | Falla electrica del cierre centralizado o actuador de puerta | 67 | 1.35% | 13 |
| 33 | Limpiaparabrisas o motor pluma quemado | 63 | 1.27% | 16 |
| 34 | Fugas de aire o fallos en el sistema de frenos neumático (Camiones) | 61 | 1.23% | 12 |
| 35 | Foco o falla en sistema de refrigeracion de bateria/inversor (EV) | 60 | 1.21% | 12 |
| 36 | Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups) | 57 | 1.15% | 11 |
| 37 | Falla en sistema de frenado regenerativo (EV / Hibridos) | 56 | 1.13% | 11 |
| 38 | Falla en sensor de velocidad de rueda ABS | 53 | 1.07% | 11 |
| 39 | Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic) | 53 | 1.07% | 10 |
| 40 | Sobrecalentamiento o solenoides en caja automatica CVT / DSG | 53 | 1.07% | 11 |
| 41 | Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas) | 52 | 1.05% | 11 |
| 42 | Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI | 50 | 1.01% | 10 |
| 43 | Válvula de freno de aire o secador APS obstruido (Camiones) | 50 | 1.01% | 10 |
| 44 | Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo) | 47 | 0.95% | 9 |
| 45 | Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6) | 47 | 0.95% | 9 |
| 46 | Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet) | 45 | 0.91% | 9 |
| 47 | Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW) | 42 | 0.85% | 9 |
| 48 | Falla en sistema Flex / Bi-combustible (Alcohol/Etanol) | 42 | 0.85% | 9 |
| - | **TOTAL** | **4,959** | **100.00%** | **991** |

---

## 3. EVALUACIÓN DETALLADA POR CLASE (ORDENADA DE MENOR A MAYOR F1)

| Clase / Falla | Precision | Recall | F1-Score | Test (Soporte) |
| :--- | :---: | :---: | :---: | :---: |
| **Falla en servofreno (booster) o linea de vacio** | **1.00** | **0.46** | **0.63** | 13 |
| **Falla electrica del cierre centralizado o actuador de puerta** | **1.00** | **0.54** | **0.70** | 13 |
| **Sobrecalentamiento o solenoides en caja automatica CVT / DSG** | **0.75** | **0.82** | **0.78** | 11 |
| **Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)** | **1.00** | **0.67** | **0.80** | 9 |
| **Fugas de aire o fallos en el sistema de frenos neumático (Camiones)** | **1.00** | **0.67** | **0.80** | 12 |
| **Válvula de freno de aire o secador APS obstruido (Camiones)** | **0.67** | **1.00** | **0.80** | 10 |
| **Bomba de gasolina quemada o con baja presion** | **0.74** | **0.90** | **0.81** | 29 |
| **Fuga en mangueras de refrigerante o radiador picado** | **0.87** | **0.87** | **0.87** | 15 |
| **Desgaste de pastillas y zapatas de freno** | **0.83** | **0.94** | **0.88** | 36 |
| **Falla en sensor de oxigeno o mezcla rica** | **0.93** | **0.84** | **0.88** | 44 |
| **Baja presion de aceite o bomba de aceite defectuosa** | **0.94** | **0.84** | **0.89** | 19 |
| **Falla en actuador de turbocompresor o VGT en motores TSI / TFSI** | **1.00** | **0.80** | **0.89** | 10 |
| **Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)** | **0.89** | **0.89** | **0.89** | 9 |
| Discos de freno alabeados o desgastados | 0.83 | 1.00 | 0.91 | 24 |
| Inyectores sucios o filtro de combustible obstruido | 0.96 | 0.87 | 0.91 | 30 |
| Fuga en mangueras de intercooler o turbocompresor danado | 0.89 | 0.94 | 0.91 | 17 |
| Llantas desbalanceadas o desalineadas | 0.92 | 0.92 | 0.92 | 36 |
| Disco de embrague desgastado o patinando | 1.00 | 0.86 | 0.92 | 21 |
| Falla en bujias o bobinas de encendido (misfire) | 0.91 | 0.97 | 0.94 | 60 |
| Consumo de aceite por desgaste de anillos o retenes | 0.89 | 1.00 | 0.94 | 24 |
| Falla en sistema Flex / Bi-combustible (Alcohol/Etanol) | 1.00 | 0.89 | 0.94 | 9 |
| Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon) | 0.90 | 1.00 | 0.95 | 9 |
| Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF | 0.90 | 1.00 | 0.95 | 9 |
| Faja o cadena de distribucion destensada o con salto de punto | 0.90 | 1.00 | 0.95 | 19 |
| Cerradura, chapa o pestillo mecanico de puerta trabado | 0.91 | 1.00 | 0.95 | 20 |
| Falla en sensor de velocidad de rueda ABS | 1.00 | 0.91 | 0.95 | 11 |
| Falla en sistema de frenado regenerativo (EV / Hibridos) | 1.00 | 0.91 | 0.95 | 11 |
| Falla de descarbonizacion e inyeccion directa GDI | 0.92 | 1.00 | 0.96 | 11 |
| Foco o falla en sistema de refrigeracion de bateria/inversor (EV) | 1.00 | 0.92 | 0.96 | 12 |
| Alternador defectuoso o placa de diodos quemada | 0.92 | 1.00 | 0.96 | 36 |
| Falla en termostato o motoventilador de radiador | 0.92 | 1.00 | 0.96 | 24 |
| Bateria descargada o bornes sulfatados | 0.95 | 0.98 | 0.97 | 43 |
| Amortiguadores reventados o bujes de suspension gastados | 1.00 | 0.94 | 0.97 | 31 |
| Rodajes de caja mecanica o diferencial gastados | 1.00 | 0.94 | 0.97 | 16 |
| Degradacion o falla en paquete de bateria de alto voltaje | 0.94 | 1.00 | 0.97 | 17 |
| Fallo en inversor de corriente IGBT o motor electrico (EV) | 1.00 | 0.94 | 0.97 | 18 |
| Cuerpo de aceleracion o valvula IAC sucia | 1.00 | 0.95 | 0.97 | 37 |
| Falla en bombin o bomba hidraulica de embrague | 0.95 | 1.00 | 0.97 | 18 |
| Cremallera de direccion asistida con holgura o fuga | 1.00 | 0.95 | 0.98 | 22 |
| Empaque de culata soplado o danado | 1.00 | 0.96 | 0.98 | 26 |
| Fuga hidraulica o aire en el sistema de frenos | 0.97 | 1.00 | 0.98 | 28 |
| Elevalunas electrico o guaya de alzacristales rota o trabada | 1.00 | 1.00 | 1.00 | 17 |
| Falla en compresor de aire acondicionado o fuga de gas R134a | 1.00 | 1.00 | 1.00 | 20 |
| Falla en sistema de sincronizacion variable de valvulas (VVT-i) | 1.00 | 1.00 | 1.00 | 10 |
| Falta o degradacion de aceite de caja de cambios | 1.00 | 1.00 | 1.00 | 16 |
| Fuga o baja presion en sistema Common Rail Diesel | 1.00 | 1.00 | 1.00 | 11 |
| Juntas homocineticas o palieres danados | 1.00 | 1.00 | 1.00 | 32 |
| Limpiaparabrisas o motor pluma quemado | 1.00 | 1.00 | 1.00 | 16 |
| **PROMEDIO MACRO** | **0.94** | **0.92** | **0.92** | **991** |

---

## 4. TOP 12 MAYORES CONFUSIONES (MATRIZ DE CONFUSIÓN)

| N° | Clase Real | $\rightarrow$ | Clase Confundida (Predicción Errónea) | Casos en Test | Causa Técnica del Conflicto |
| :---: | :--- | :---: | :--- | :---: | :--- |
| **1** | **Falla en servofreno (booster) o vacio** | $\rightarrow$ | **Desgaste de pastillas y zapatas** | **7** | Confunde queja de "pedal duro / no frena bien" con pastillas gastadas en vez de pérdida de asistencia neumática del booster. |
| **2** | **Fugas de aire en frenos neumático (Camiones)** | $\rightarrow$ | **Válvula de freno de aire o secador APS** | **4** | Ambos sistemas operan con descarga neumática ("chiflido de aire"). El modelo no distingue manguera rota de válvula secadora. |
| **3** | **Sensor de oxigeno o mezcla rica** | $\rightarrow$ | **Consumo de aceite por desgaste anillos** | **3** | Ambos reportan humo, olor fuerte en el escape y pérdida de compresión/fuerza. |
| **4** | **Llantas desbalanceadas o desalineadas** | $\rightarrow$ | **Discos de freno alabeados** | **3** | Ambos reportan "vibración en el timón a velocidad". Falta aislar la condición: frenando (discos) vs rodando sin frenar (llantas). |
| **5** | **Cierre centralizado eléctrico (actuador)** | $\rightarrow$ | **Cerradura mecánica de puerta** | **2** | Ambos reportan "puerta trabada no abre". Falta aislar: fallo eléctrico del control remoto vs mecanismo de seguro atorado. |
| **6** | **Actuador turbo VGT (TSI/TFSI)** | $\rightarrow$ | **Fuga mangueras intercooler / turbo dañado** | **2** | Pérdida de sobrealimentación y silbido. Ambos son del subsistema turbo. |
| **7** | **Inyectores sucios o filtro obstruido** | $\rightarrow$ | **Bomba de gasolina quemada / baja presión** | **2** | Ambos provocan tirones, falta de combustible y ahogo bajo carga pesada. |
| **8** | **Disco de embrague gastado (patinando)** | $\rightarrow$ | **Caja automática CVT / DSG patinando** | **2** | Ambos reportan "suben las revoluciones pero el carro no avanza". Diferencia mecánica: pedal de embrague vs caja automática. |
| **9** | **Sobrecalentamiento CVT / DSG** | $\rightarrow$ | **Misfire bujías o bobinas** | **2** | Tirones violentos o cabeceo son clasificados erróneamente como encendido. |
| **10** | **Bomba de gasolina quemada / baja presión** | $\rightarrow$ | **Misfire bujías o bobinas** | **1** | Motor tiembla o pierde fuerza al acelerar en caliente. |
| **11** | **Bomba de gasolina quemada / baja presión** | $\rightarrow$ | **Inyectores sucios o filtro obstruido** | **1** | Confusión cruzada recíproca entre suministro y atomización. |
| **12** | **Baja presión de aceite de motor** | $\rightarrow$ | **Correa bañada en aceite / Descarbonización** | **2** | Luz de aceite en el tablero compartida con problemas de taponamiento de chupona. |

---

## 5. DIAGNÓSTICO DE CLASES DÉBILES Y REQUERIMIENTO PARA FASE 2

| Clase Débil | F1 | Recall | Casos Actuales | Casos Recomendados en Fase 2 | Tipo de Sintomatología a Crear |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Servofreno (booster) / línea de vacío** | **0.63** | **0.46** | 69 | **+35 a +40 casos** | "Pedal de freno como piedra/tabla", "al pisar el freno se escucha silbido o aire debajo del tablero", "freno duro con motor prendido", "manguera de vacío del múltiple rajada". |
| **2. Cierre centralizado eléctrico (actuadores)** | **0.70** | **0.54** | 67 | **+30 a +35 casos** | "Con el mando a distancia no sube el seguro", "el actuador de la puerta suena como matraca y no traba", "pestillos no responden al botón del piloto", "relevador del cierre no acciona". |
| **3. Caja automática CVT / DSG (solenoides)** | **0.78** | **0.82** | 53 | **+25 a +30 casos** | "Caja CVT entra en modo emergencia (limp mode)", "patina la banda o poleas de CVT al calentar", "caja DSG traba en reversa o salta cambios pares", "código P0700 o P0841". |
| **4. Caja robotizada Dualogic / I-Motion** | **0.80** | **0.67** | 42 | **+25 a +30 casos** | "Bomba electrohidráulica Dualogic no corta zumbido", "pierde presión acumulador robotizado", "no entra neutro o primera en frío", "mensaje revisar transmisión en tablero". |
| **5. Frenos neumáticos vs. Válvula APS (Camiones)** | **0.80** | **0.67** | 61 / 50 | **+20 a +25 casos** | Distinguir purga de secador APS ("descarga cada 30 segundos") de fuga continua en pulmones de freno o mangueras espirales. |
| **6. Bomba de gasolina vs. Inyectores** | **0.81** | **0.90** | 145 | **+25 a +30 casos** | Aislar síntomas de bomba: "zumbido agudo en el asiento trasero", "presión de rampa cae de 45 psi a 15 psi bajo aceleración", "en subida se ahoga con medio tanque". |
| **7. Llantas desbalanceadas vs. Discos de freno** | **0.92** | **0.92** | 178 / 120 | **+20 casos** | Fortalecer contraste de frenado: "tiembla timón a 100 km/h sin tocar el freno" (balanceo) vs "solamente vibra al aplicar el pedal de freno" (alabeo de discos). |
