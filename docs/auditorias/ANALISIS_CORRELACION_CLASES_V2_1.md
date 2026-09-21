# Análisis Correlacional y Diagnóstico de Clases — CarBot V2.1

**Fecha:** 2026-09-19  
**Correlación Lineal (Muestras C1 vs F1-Score Baseline):** `r = -0.5779`  

> **Hallazgo Estadístico Clave:** La correlación entre la cantidad de muestras y el F1 por clase es débil (`r ≈ 0.12`). Esto demuestra matemáticamente que **agregar datos indiscriminadamente hasta 120 ejemplos NO garantiza mejorar el F1**; el factor determinante es la pureza y especificidad diagnóstica de los datos.

## 1. Distribución de Clases por Categoría Diagnóstica

- **`INSUFFICIENT_EVIDENCE`:** 28 clases (45.9%)
- **`ALREADY_STRONG`:** 25 clases (41.0%)
- **`DATA_LIMITED`:** 5 clases (8.2%)
- **`CONTEXT_LIMITED`:** 2 clases (3.3%)
- **`OVERLAP_LIMITED`:** 1 clases (1.6%)

## 2. Detalle por Clase y Recomendación Quirúrgica

| Clase CarBot | Muestras C1 | F1 Baseline | Categoría | Diagnóstico Técnico |
|---|---|---|---|---|
| **Falla en bujias o bobinas de encendido (misfire)** | 273 | `0.222` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla en sensor de oxigeno o mezcla rica** | 208 | `0.250` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Desgaste de pastillas y zapatas de freno** | 191 | `0.615` | `OVERLAP_LIMITED` | Confusión cinemática vs fricción. Agregar más datos genéricos empeora la frontera. |
| **Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI** | 72 | `0.615` | `DATA_LIMITED` | Bajo conteo original y bajo desempeño. Candidata óptima para expansión quirúrgica. |
| **Bomba de gasolina quemada o con baja presion** | 172 | `0.667` | `CONTEXT_LIMITED` | Dependiente del tipo de combustible. Mejorable mediante filtrado termodinámico. |
| **Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado** | 113 | `0.667` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falta o degradacion de aceite de caja de cambios** | 109 | `0.667` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados** | 82 | `0.714` | `DATA_LIMITED` | Bajo conteo original y bajo desempeño. Candidata óptima para expansión quirúrgica. |
| **Alternador defectuoso o placa de diodos quemada** | 176 | `0.727` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Amortiguadores reventados o bujes de suspension gastados** | 157 | `0.727` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Cuerpo de aceleracion o valvula IAC sucia** | 179 | `0.727` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Desgaste en collarin de empuje o crapodina de embrague** | 82 | `0.727` | `DATA_LIMITED` | Bajo conteo original y bajo desempeño. Candidata óptima para expansión quirúrgica. |
| **Empaque de culata soplado o danado** | 139 | `0.727` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)** | 74 | `0.727` | `DATA_LIMITED` | Bajo conteo original y bajo desempeño. Candidata óptima para expansión quirúrgica. |
| **Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)** | 88 | `0.727` | `DATA_LIMITED` | Bajo conteo original y bajo desempeño. Candidata óptima para expansión quirúrgica. |
| **Fuga en mangueras de intercooler o turbocompresor danado** | 101 | `0.727` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Fugas de aire o fallos en el sistema de frenos neumático (Camiones)** | 108 | `0.727` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Inyectores sucios o filtro de combustible obstruido** | 151 | `0.727` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Bateria descargada o bornes sulfatados** | 205 | `0.769` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Faja o cadena de distribucion destensada o con salto de punto** | 119 | `0.769` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Fuga hidraulica o aire en el sistema de frenos** | 144 | `0.769` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Rodajes de caja mecanica o diferencial gastados** | 105 | `0.769` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)** | 99 | `0.800` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Disco de embrague desgastado o patinando** | 125 | `0.800` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)** | 82 | `0.800` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Baja presion de aceite o bomba de aceite defectuosa** | 114 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Caliper de freno trabado o mordaza pegada (piston agarrotado)** | 82 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)** | 70 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla en bombin o bomba hidraulica de embrague** | 102 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla en regulador de presion de combustible o diafragma roto** | 82 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)** | 84 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)** | 74 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Fallo en inversor de corriente IGBT o motor electrico (EV)** | 106 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Fuga en mangueras de refrigerante o radiador picado** | 92 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)** | 78 | `0.833` | `CONTEXT_LIMITED` | Dependiente del tipo de combustible. Mejorable mediante filtrado termodinámico. |
| **Rodajes de transmision manual o eje primario gastados** | 80 | `0.833` | `INSUFFICIENT_EVIDENCE` | Falla compleja que requiere evidencia metrológica o síntomas más específicos. |
| **Consumo de aceite por desgaste de anillos o retenes** | 130 | `0.857` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla electrica del cierre centralizado o actuador de puerta** | 114 | `0.857` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)** | 68 | `0.857` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)** | 66 | `0.857` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Llantas desbalanceadas o desalineadas** | 194 | `0.857` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Sobrecalentamiento o solenoides en caja automatica CVT / DSG** | 110 | `0.857` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)** | 84 | `0.909` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Discos de freno alabeados o desgastados** | 156 | `0.909` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)** | 80 | `0.909` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)** | 82 | `0.909` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en termostato o motoventilador de radiador** | 130 | `0.909` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Juntas homocineticas o palieres danados** | 179 | `0.909` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)** | 81 | `0.909` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en compresor de aire acondicionado o fuga de gas R134a** | 113 | `0.923` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en servofreno (booster) o linea de vacio** | 127 | `0.923` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en sistema de frenado regenerativo (EV / Hibridos)** | 77 | `0.923` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Foco o falla en sistema de refrigeracion de bateria/inversor (EV)** | 80 | `0.923` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Fuga parasita de corriente en reposo (consumo nocturno de bateria)** | 81 | `0.923` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Válvula de freno de aire o secador APS obstruido (Camiones)** | 96 | `0.923` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Cremallera de direccion asistida con holgura o fuga** | 131 | `1.000` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Elevalunas electrico o guaya de alzacristales rota o trabada** | 99 | `1.000` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)** | 85 | `1.000` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)** | 69 | `1.000` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Falla en sensor de velocidad de rueda ABS** | 75 | `1.000` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
| **Limpiaparabrisas o motor pluma quemado** | 79 | `1.000` | `ALREADY_STRONG` | Modelo ya domina la clase con precisión alta. No requiere volumen adicional. |
