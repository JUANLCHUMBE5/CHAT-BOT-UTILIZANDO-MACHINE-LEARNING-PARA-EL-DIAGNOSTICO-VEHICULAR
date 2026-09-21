# Distribución y Expansión Controlada de Clases — Dataset C1-V2 Experimental

**Fecha:** 2026-09-19  
**Norma Operacional:** Regla 8 de Capping Balanceado y Prevención de Dominancia Externa  

## 1. Resumen Global

- **Registros Originales C1:** 6,904
- **Registros Externos Verificados Incorporados:** 337
- **Total Dataset C1-V2:** 7,241
- **Partición Train:** 6,090 (84.1%)
- **Partición Val:** 1,151 (15.9%)

## 2. Tabla de Crecimiento por Clase

| Clase CarBot | C1 Original | Candidatos Ext. | Seleccionados | Total V2 | Crecimiento (%) |
|---|---|---|---|---|---|
| **Alternador defectuoso o placa de diodos quemada** | 176 | 32 | 30 | 206 | +17.0% |
| **Amortiguadores reventados o bujes de suspension gastados** | 157 | 18 | 18 | 175 | +11.5% |
| **Baja presion de aceite o bomba de aceite defectuosa** | 114 | 0 | 0 | 114 | +0.0% |
| **Bateria descargada o bornes sulfatados** | 205 | 91 | 30 | 235 | +14.6% |
| **Bomba de gasolina quemada o con baja presion** | 172 | 71 | 30 | 202 | +17.4% |
| **Caliper de freno trabado o mordaza pegada (piston agarrotado)** | 82 | 0 | 0 | 82 | +0.0% |
| **Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado** | 113 | 0 | 0 | 113 | +0.0% |
| **Consumo de aceite por desgaste de anillos o retenes** | 130 | 0 | 0 | 130 | +0.0% |
| **Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)** | 84 | 12 | 12 | 96 | +14.3% |
| **Cremallera de direccion asistida con holgura o fuga** | 131 | 55 | 30 | 161 | +22.9% |
| **Cuerpo de aceleracion o valvula IAC sucia** | 179 | 20 | 20 | 199 | +11.2% |
| **Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)** | 99 | 0 | 0 | 99 | +0.0% |
| **Desgaste de pastillas y zapatas de freno** | 191 | 4 | 4 | 195 | +2.1% |
| **Desgaste en collarin de empuje o crapodina de embrague** | 82 | 0 | 0 | 82 | +0.0% |
| **Disco de embrague desgastado o patinando** | 125 | 34 | 30 | 155 | +24.0% |
| **Discos de freno alabeados o desgastados** | 156 | 18 | 18 | 174 | +11.5% |
| **Elevalunas electrico o guaya de alzacristales rota o trabada** | 99 | 0 | 0 | 99 | +0.0% |
| **Empaque de culata soplado o danado** | 139 | 0 | 0 | 139 | +0.0% |
| **Faja o cadena de distribucion destensada o con salto de punto** | 119 | 0 | 0 | 119 | +0.0% |
| **Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)** | 70 | 0 | 0 | 70 | +0.0% |
| **Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)** | 74 | 0 | 0 | 74 | +0.0% |
| **Falla electrica del cierre centralizado o actuador de puerta** | 114 | 0 | 0 | 114 | +0.0% |
| **Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)** | 80 | 0 | 0 | 80 | +0.0% |
| **Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI** | 72 | 0 | 0 | 72 | +0.0% |
| **Falla en bombin o bomba hidraulica de embrague** | 102 | 0 | 0 | 102 | +0.0% |
| **Falla en bujias o bobinas de encendido (misfire)** | 273 | 3 | 3 | 276 | +1.1% |
| **Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)** | 85 | 0 | 0 | 85 | +0.0% |
| **Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)** | 82 | 0 | 0 | 82 | +0.0% |
| **Falla en compresor de aire acondicionado o fuga de gas R134a** | 113 | 0 | 0 | 113 | +0.0% |
| **Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)** | 69 | 0 | 0 | 69 | +0.0% |
| **Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)** | 68 | 0 | 0 | 68 | +0.0% |
| **Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)** | 82 | 4 | 4 | 86 | +4.9% |
| **Falla en regulador de presion de combustible o diafragma roto** | 82 | 0 | 0 | 82 | +0.0% |
| **Falla en sensor de oxigeno o mezcla rica** | 208 | 7 | 7 | 215 | +3.4% |
| **Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)** | 88 | 0 | 0 | 88 | +0.0% |
| **Falla en sensor de velocidad de rueda ABS** | 75 | 1 | 1 | 76 | +1.3% |
| **Falla en servofreno (booster) o linea de vacio** | 127 | 0 | 0 | 127 | +0.0% |
| **Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)** | 66 | 0 | 0 | 66 | +0.0% |
| **Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)** | 84 | 1 | 1 | 85 | +1.2% |
| **Falla en sistema de frenado regenerativo (EV / Hibridos)** | 77 | 0 | 0 | 77 | +0.0% |
| **Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)** | 74 | 0 | 0 | 74 | +0.0% |
| **Falla en termostato o motoventilador de radiador** | 130 | 34 | 30 | 160 | +23.1% |
| **Fallo en inversor de corriente IGBT o motor electrico (EV)** | 106 | 0 | 0 | 106 | +0.0% |
| **Falta o degradacion de aceite de caja de cambios** | 109 | 0 | 0 | 109 | +0.0% |
| **Foco o falla en sistema de refrigeracion de bateria/inversor (EV)** | 80 | 0 | 0 | 80 | +0.0% |
| **Fuga en mangueras de intercooler o turbocompresor danado** | 101 | 2 | 2 | 103 | +2.0% |
| **Fuga en mangueras de refrigerante o radiador picado** | 92 | 7 | 7 | 99 | +7.6% |
| **Fuga hidraulica o aire en el sistema de frenos** | 144 | 44 | 30 | 174 | +20.8% |
| **Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)** | 78 | 0 | 0 | 78 | +0.0% |
| **Fuga parasita de corriente en reposo (consumo nocturno de bateria)** | 81 | 0 | 0 | 81 | +0.0% |
| **Fugas de aire o fallos en el sistema de frenos neumático (Camiones)** | 108 | 0 | 0 | 108 | +0.0% |
| **Inyectores sucios o filtro de combustible obstruido** | 151 | 30 | 30 | 181 | +19.9% |
| **Juntas homocineticas o palieres danados** | 179 | 0 | 0 | 179 | +0.0% |
| **Limpiaparabrisas o motor pluma quemado** | 79 | 0 | 0 | 79 | +0.0% |
| **Llantas desbalanceadas o desalineadas** | 194 | 0 | 0 | 194 | +0.0% |
| **Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados** | 82 | 0 | 0 | 82 | +0.0% |
| **Rodajes de caja mecanica o diferencial gastados** | 105 | 0 | 0 | 105 | +0.0% |
| **Rodajes de transmision manual o eje primario gastados** | 80 | 0 | 0 | 80 | +0.0% |
| **Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)** | 81 | 0 | 0 | 81 | +0.0% |
| **Sobrecalentamiento o solenoides en caja automatica CVT / DSG** | 110 | 0 | 0 | 110 | +0.0% |
| **Válvula de freno de aire o secador APS obstruido (Camiones)** | 96 | 0 | 0 | 96 | +0.0% |
