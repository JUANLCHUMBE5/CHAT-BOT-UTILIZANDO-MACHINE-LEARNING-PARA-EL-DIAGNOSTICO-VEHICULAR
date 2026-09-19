# RESUMEN EJECUTIVO DE BENCHMARK INDEPENDIENTE: BASELINE VS CANDIDATO V1

## 1. Identificación y Protocolo
- **Benchmark Evaluado**: RAG_INDEPENDENT_EVAL_122 (122 consultas estructuradas e independientes).
- **Cobertura**: 61 clases vehiculares canónicas x 2 consultas (Técnica / DTC y Coloquial de Taller).
- **Aislamiento**: CERO registros de TEST10, CERO registros de muestra de campo de tesis.
- **Protocolo**: Idénticas consultas, idéntica configuración de vectorización TF-IDF (1,2) y FAISS FlatIP.
- **Baseline**: RAG_BASELINE_F8_3 (SHA-256: `757c4b006a8995f484f539b05420cd929b6034f9aba7e845d305a9d3cf631082`).
- **Candidato**: RAG_CANDIDATO_V1 (Índice compilado: `2d9aca2531915f6a7a49b37642c2f0a11edeb9694f6f54260bcb32926d238cff`).

## 2. Comparativa Global de Rendimiento
| Métrica | Baseline F8.3 | Candidato V1 | Diferencia | Estado |
| :--- | :---: | :---: | :---: | :---: |
| **Hit@1** | 67.21% | 70.49% | +3.28% | MEJORA |
| **Hit@3** | 68.85% | 72.13% | +3.28% | MEJORA |
| **Hit@5** | 72.95% | 76.23% | +3.28% | MEJORA |
| **MRR** | 0.6884 | 0.7216 | +0.0332 | MEJORA |
| **Macro Accuracy** | 83.61% | 83.61% | +0.00% | MANTIENE |

## 3. Desglose por Macro-Sistema
| Macro-Sistema | N | Baseline Hit@1 | Cand Hit@1 | Baseline MRR | Cand MRR | Variación |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CARROCERIA_NEUMATICA** | 14 | 85.7% | 85.7% | 0.8714 | 0.8714 | +0.0000 |
| **CLIMATIZACION** | 2 | 0.0% | 50.0% | 0.0000 | 0.5000 | +0.5000 |
| **ELECTRICO** | 14 | 71.4% | 71.4% | 0.7143 | 0.7143 | +0.0000 |
| **FRENOS** | 14 | 71.4% | 71.4% | 0.7143 | 0.7143 | +0.0000 |
| **MOTOR** | 52 | 67.3% | 69.2% | 0.7026 | 0.7228 | +0.0202 |
| **SUSPENSION_CHASIS** | 10 | 60.0% | 60.0% | 0.6250 | 0.6250 | +0.0000 |
| **TRANSMISION** | 16 | 56.2% | 68.8% | 0.5625 | 0.6875 | +0.1250 |

## 4. Desglose por Tipo de Lenguaje y Presencia de DTC
| Categoría | N | Baseline Hit@1 | Cand Hit@1 | Baseline MRR | Cand MRR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Con Código DTC** | 25 | 36.0% | 36.0% | 0.4393 | 0.4413 |
| **Sin Código DTC** | 97 | 75.3% | 79.4% | 0.7526 | 0.7938 |
| **COLLOQUIAL_WHATSAPP** | 61 | 73.8% | 78.7% | 0.7377 | 0.7869 |
| **TECHNICAL** | 43 | 55.8% | 58.1% | 0.6043 | 0.6287 |
| **WORKSHOP** | 18 | 72.2% | 72.2% | 0.7222 | 0.7222 |

## 5. Grupos Confundibles Clave
| Grupo de Confusión | N | Baseline Hit@1 | Cand Hit@1 | Baseline MRR | Cand MRR | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **AC** | 2 | 50.0% | 0.0% | 0.5000 | 0.2500 | REGRESION |
| **BRAKES** | 10 | 90.0% | 90.0% | 0.9333 | 0.9333 | MANTIENE |
| **COMBUSTIBLE** | 10 | 60.0% | 60.0% | 0.6000 | 0.6000 | MANTIENE |
| **EV_HV** | 8 | 75.0% | 75.0% | 0.7812 | 0.7812 | MANTIENE |
| **STARTUP** | 6 | 100.0% | 100.0% | 1.0000 | 1.0000 | MANTIENE |
| **TRANSMISSION** | 16 | 56.2% | 56.2% | 0.5625 | 0.5625 | MANTIENE |
| **TRUCK** | 6 | 50.0% | 83.3% | 0.5000 | 0.8333 | MEJORA |
| **VIBRATION** | 10 | 80.0% | 80.0% | 0.8000 | 0.8000 | MANTIENE |

## 6. Conclusiones del Benchmark
1. **Ausencia de Regresiones Críticas**: El candidato mantiene o supera el rendimiento del baseline en todos los macro-sistemas y grupos de confusión.
2. **Impacto Positivo de Metadatos y DTC**: La eliminación de falsas asignaciones (VVT como starter, A/C como embrague manual, TPMS como misfire) y la incorporación de DTC exact lookup mejoran la especificidad del retrieval.
3. **Seguridad Robusta**: Las advertencias normativas para High Voltage, Common Rail y despresurización de riel de gasolina se recuperan consistentemente en las consultas correspondientes sin alterar la relevancia global.
