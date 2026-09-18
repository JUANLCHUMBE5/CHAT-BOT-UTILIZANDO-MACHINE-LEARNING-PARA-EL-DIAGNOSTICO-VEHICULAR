# Verificación Aritmética y Metodológica Final: 50 Casos de Taller vs. Ground Truth

**Fase:** Fase 7 - Auditoría Científica Independiente por Capas (Pipeline y Modelos 100% Congelados)
**Reglas Metodológicas Estrictas:**
- **Top-1 ML:** Evalúa únicamente la clase predicha en primera posición por el SVM.
- **Top-3 ML:** Evalúa exclusivamente las 3 clases de salida del SVM; RAG, LLM y auto-interrogador no pueden convertir un fallo ML en acierto Top-3.
- **E2E (Estricto / Diferencial / Incorrecto):** Evalúa el diagnóstico final recibido por el mecánico tras ML+DTC+RAG+LLM+Auto-interrogador. RAG puede mejorar E2E, pero nunca Top-3 ML.
- **Macro-Sistema:** Exactitud del macro-dominio vehicular asignado.
- **Auto-Interrogador:** Evalúa la decisión de flujo (activación oportuna en ambigüedad y derivación directa en consultas claras).

## 1. Resumen Aritmético Consolidado por Capas (N = 50)

| Capa Evaluada | Conteo Exacto | Porcentaje (%) | Criterio Metodológico Estricto |
|---|:---:|:---:|---|
| **Top1_ML_correcto** | **23 / 50** | **46.00%** | Acierto unívoco de la clase Top-1 del Linear SVM con la causa esperada. |
| **Top3_ML_correcto** | **27 / 50** | **54.00%** | Causa esperada presente en las tres clases ML puras (sin auxilio de RAG). |
| **E2E_estricto** | **24 / 50** | **48.00%** | Hipótesis principal entregada al usuario coincide con la causa esperada. |
| **E2E_diferencial** | **5 / 50** | **10.00%** | Causa esperada entregada explícitamente en el diagnóstico diferencial o procedimiento RAG. |
| **E2E_incorrecto** | **21 / 50** | **42.00%** | Causa esperada no entregada al usuario o fallo en activación interactiva (G1_50). |
| **E2E_global (estricto + diferencial)** | **29 / 50** | **58.00%** | Tasa total de casos donde el mecánico recibió la hipótesis correcta. |
| **macro_correcto** | **44 / 50** | **88.00%** | Macro-sistema automotriz correctamente identificado. |
| **interrogador_correcto** | **48 / 50** | **96.00%** | Decisión de flujo correcta (activó en ambigüedad / no activó en datos claros). |

## 2. Matriz Final Caso por Caso (50 Filas Auditadas)

| ID | Causa Esperada (*Ground Truth*) | Top1_ML | Top3_ML | E2E_estricto | E2E_dif | macro | inter | Diagnóstico Final E2E Entregado |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **G1_01** | Sensor CKP por fatiga térmica | 0 | 0 | 0 | 0 | 1 | 1 | Bujías o bobinas |
| **G1_02** | Bomba de gasolina quemada o baja presión | 0 | 0 | 0 | 0 | 1 | 1 | Fuera de alcance automotriz |
| **G1_03** | Cuerpo de aceleración o válvula IAC | 1 | 1 | 1 | 0 | 1 | 1 | Cuerpo de aceleración o válvula IAC |
| **G1_04** | Inyector con falla térmica (cilindro) | 0 | 0 | 0 | 0 | 1 | 1 | Bujías o bobinas |
| **G1_05** | Falla en bujías o bobinas (misfire P0303) | 1 | 1 | 1 | 0 | 1 | 1 | Bujías o bobinas |
| **G1_06** | Fuga de vacío en múltiple de admisión | 0 | 0 | 0 | 0 | 1 | 1 | Cuerpo de aceleración / IAC |
| **G1_07** | Válvula de purga de cánister EVAP | 0 | 0 | 0 | 0 | 1 | 1 | Falla en sensor de oxígeno o mezcla rica |
| **G1_08** | Fuga o baja presión Common Rail Diesel | 1 | 1 | 1 | 0 | 1 | 1 | Common Rail Diesel |
| **G1_09** | Inyectores goteando en reposo / Sensor ECT | 0 | 0 | 0 | 0 | 1 | 1 | Common Rail Diesel |
| **G1_10** | Faja o cadena de distribución destensada | 1 | 1 | 1 | 0 | 1 | 1 | Faja o cadena de distribución |
| **G1_11** | Convertidor catalítico ineficiente (DTC P0420) | 0 | 0 | 0 | 1 | 1 | 1 | Bujías/bobinas (Reporte RAG: DTC P0420 Catalizador) |
| **G1_12** | Pérdida de compresión válvula/anillos cil 1 | 0 | 0 | 0 | 0 | 1 | 1 | Bujías o bobinas COP |
| **G1_13** | Diafragma del regulador de presión roto | 0 | 0 | 0 | 0 | 1 | 1 | Falla en sensor de oxígeno o mezcla rica |
| **G1_14** | Bomba de gasolina quemada / filtro sumergido | 0 | 0 | 0 | 0 | 1 | 1 | Fuera de alcance automotriz |
| **G1_15** | Falla en circuito de inyector 2 (P0202) | 0 | 0 | 0 | 0 | 1 | 1 | Bujías o bobinas |
| **G1_16** | Fuga interna cilindro maestro / aire frenos | 1 | 1 | 1 | 0 | 1 | 1 | Fuga hidráulica o aire en frenos |
| **G1_17** | Falla en servofreno booster o vacío | 1 | 1 | 1 | 0 | 1 | 1 | Servofreno booster o línea de vacío |
| **G1_18** | Caliper de freno trabado / mordaza pegada | 0 | 0 | 0 | 0 | 1 | 1 | Desgaste de pastillas y zapatas |
| **G1_19** | Discos de freno alabeados o desgastados | 0 | 1 | 0 | 1 | 0 | 1 | Llantas (Diferencial Top-2: Discos alabeados) |
| **G1_20** | Llantas desbalanceadas o desalineadas | 1 | 1 | 1 | 0 | 1 | 1 | Llantas desbalanceadas o desalineadas |
| **G1_21** | Falla en sensor de velocidad de rueda ABS | 1 | 1 | 1 | 0 | 1 | 1 | Sensor de velocidad de rueda ABS |
| **G1_22** | Aire en sistema de frenos tras purga | 0 | 0 | 0 | 0 | 0 | 1 | Consulta fuera del alcance automotriz |
| **G1_23** | Falta o degradación de aceite de caja | 1 | 1 | 1 | 0 | 1 | 1 | Falta o degradación de aceite de caja |
| **G1_24** | Sobrecalentamiento o solenoides CVT | 1 | 1 | 1 | 0 | 1 | 1 | Solenoides en caja automática CVT/DSG |
| **G1_25** | Embrague K1 desgastado caja DSG | 0 | 1 | 0 | 0 | 0 | 1 | Bujías de encendido y misfire |
| **G1_26** | Acumulador de presión caja Dualogic | 1 | 1 | 1 | 0 | 1 | 1 | Caja robotizada Dualogic |
| **G1_27** | Disco de embrague desgastado o patinando | 0 | 0 | 0 | 0 | 0 | 0 | Falla en sensor de oxígeno o mezcla rica |
| **G1_28** | Collarín de empuje / crapodina desgastada | 0 | 0 | 0 | 0 | 1 | 1 | Bombín de embrague (Reporte: Mecatrónica DSG) |
| **G1_29** | Rodajes de caja mecánica (eje primario) | 0 | 0 | 0 | 0 | 1 | 1 | Bombín de embrague |
| **G1_30** | Plato opresor alabeado / embrague zapatea | 1 | 1 | 1 | 0 | 1 | 1 | Disco de embrague desgastado o patinando |
| **G1_31** | Llantas desalineadas tras impacto | 1 | 1 | 1 | 0 | 1 | 1 | Llantas desbalanceadas o desalineadas |
| **G1_32** | Juntas homocinéticas o palieres dañados | 1 | 1 | 1 | 0 | 1 | 1 | Juntas homocinéticas o palieres dañados |
| **G1_33** | Rodamiento de rueda / maza picado | 0 | 0 | 0 | 1 | 1 | 1 | Llantas (Reporte RAG: Rodamientos de Rueda/Maza) |
| **G1_34** | Amortiguadores reventados / bujes | 0 | 0 | 0 | 0 | 1 | 1 | Llantas desbalanceadas o desalineadas |
| **G1_35** | Cremallera de dirección asistida con holgura | 1 | 1 | 1 | 0 | 1 | 1 | Cremallera de dirección asistida |
| **G1_36** | Llantas desalineadas (camber / divergencia) | 1 | 1 | 1 | 0 | 1 | 1 | Llantas desbalanceadas o desalineadas |
| **G1_37** | Motoventilador de radiador quemado | 1 | 1 | 1 | 0 | 1 | 1 | Termostato o motoventilador de radiador |
| **G1_38** | Termostato trabado cerrado | 1 | 1 | 1 | 0 | 1 | 1 | Termostato o motoventilador de radiador |
| **G1_39** | Empaque de culata soplado o dañado | 0 | 1 | 0 | 1 | 1 | 1 | Fuga mangueras (Opción 3 Auto-pregunta: Empaque de culata) |
| **G1_40** | Baja presión de aceite o bomba defectuosa | 1 | 1 | 1 | 0 | 1 | 1 | Baja presión de aceite o bomba defectuosa |
| **G1_41** | Taqués hidráulicos / baja presión de aceite | 1 | 1 | 1 | 0 | 1 | 1 | Baja presión de aceite o bomba defectuosa |
| **G1_42** | Alternador en sobrevoltaje (placa de diodos) | 1 | 1 | 1 | 0 | 1 | 1 | Alternador defectuoso o placa de diodos quemada |
| **G1_43** | Alternador defectuoso (baja carga P0562) | 0 | 1 | 0 | 1 | 1 | 1 | Batería descargada (Diferencial Top-2: Alternador defectuoso) |
| **G1_44** | Motor de arranque o solenoide defectuoso | 0 | 0 | 0 | 0 | 1 | 1 | Batería descargada o bornes sulfatados |
| **G1_45** | Fuga parásita de corriente en reposo | 0 | 0 | 0 | 0 | 1 | 1 | Alternador defectuoso o placa de diodos quemada |
| **G1_46** | Fuga / falla en frenos neumático (compresor) | 1 | 1 | 1 | 0 | 1 | 1 | Fugas de aire / frenos neumático (Camiones) |
| **G1_47** | Válvula de freno de aire o secador APS | 1 | 1 | 1 | 0 | 0 | 1 | Válvula de freno de aire o secador APS obstruido |
| **G1_48** | Cámara Maxi-Brake de freno de aire rota | 0 | 0 | 0 | 0 | 0 | 1 | Bomba de gasolina quemada |
| **G1_49** | Consulta térmica ambigua (Meta: Auto-interrogador) | 0 | 0 | 1 | 0 | 1 | 1 | Auto-pregunta técnica de descarte disparada |
| **G1_50** | Tren delantero difuso (Meta: Auto-interrogador) | 0 | 0 | 0 | 0 | 1 | 0 | Llantas desbalanceadas (Adivinanza sin interrogar) |

**Suma Total de Verificación Aritmética:**
- `Top1_ML_correcto`: 23 / 50
- `Top3_ML_correcto`: 27 / 50
- `E2E_estricto`: 24 / 50
- `E2E_diferencial`: 5 / 50
- `E2E_incorrecto`: 21 / 50 (Comprobación: 24 + 5 + 21 = 50)
- `macro_correcto`: 44 / 50
- `interrogador_correcto`: 48 / 50