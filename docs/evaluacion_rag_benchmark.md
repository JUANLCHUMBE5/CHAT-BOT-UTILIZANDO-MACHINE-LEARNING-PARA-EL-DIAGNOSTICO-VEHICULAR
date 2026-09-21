# Evaluación y Benchmark Interno del Subsistema RAG Multimarca (Tesis UCV 2026)

## 1. Propósito y Alcance del Benchmark

Este documento describe la metodología, resultados y consideraciones epistemológicas del banco de pruebas interno implementado para evaluar el motor RAG multimarca (*Retrieval-Augmented Generation*) en CarBot.

- **Objetivo**: Verificar que el motor de indexación TF-IDF + FAISS (*IndexFlatIP*) recupere los procedimientos de diagnóstico automotriz correspondientes ante consultas técnicas especializadas dentro de dominio, y clasifique como *Coincidencia baja* aquellas consultas ajenas al dominio automotriz.
- **Configuración de Producción Evaluada**:
  - **Umbral de Similitud Coseno ($S_{min}$)**: `0.25`
  - **Dimensión de Vectores TF-IDF**: 8,908 características
  - **Métrica de Similitud**: Inner Product normalizado L2 ($\cos(\theta)$)
  - **Corpus Indexado**: 64 procedimientos técnicos estructurados en `machine_learning/manuals/`.

---

## 2. Banco de Pruebas Controlado (N = 10)

El benchmark interno formal implementado en `machine_learning/training/evaluar_rag_riguroso.py` evalúa los siguientes casos de prueba:

### A. Casos Positivos Dentro de Dominio Automotriz

| N° | Consulta de Entrada | Sistema / Falla Evaluada | Procedimiento Esperado | Similitud Obtenida | Resultado |
| :--- | :--- | :--- | :--- | :---: | :---: |
| 1 | *Toyota Prius bateria de alto voltaje inversor error p0a80 celdas desbalanceadas* | Híbrido / Batería HV | Batería de Alto Voltaje e Inversor Toyota Prius | `0.3076` | **OK** |
| 2 | *Toyota Yaris pedal de embrague no desembraga bombin y plato de presion* | Transmisión / Embrague | Reemplazo Kit Embrague y Bombín Toyota Yaris | `0.2842` | **OK** |
| 3 | *Nissan Sentra transmision automatica CVT sobrecalentamiento solenoide p0700* | Transmisión CVT | Diagnóstico y Servicio CVT Nissan Sentra | `0.2849` | **OK** |
| 4 | *Sistema de conversion a GNV GLP 5ta generacion calibracion rampa inyectores reductor* | Gas Vehicular GNV/GLP | Calibración y Diagnóstico GNV/GLP 5ta Gen | `0.3031` | **OK** |
| 5 | *Hyundai Accent cuerpo de aceleracion mariposa electronica tps p2135* | Inyección / Admisión | Cuerpo de Aceleración Electrónico Hyundai Accent | `0.2756` | **OK** |
| 6 | *Kia Rio valvula solenoide ocv sincronizacion variable vvt cascabeleo p0011* | Motor / VVT | Válvula Solenoide OCV Kia Rio | `0.3064` | **OK** |
| 7 | *Frenos de aire neumaticos valvula secador camiones Scania Volvo compresor* | Frenos Neumáticos | Frenos de Aire Neumáticos en Camiones | `0.3514` | **OK** |

### B. Casos Negativos Fuera de Dominio (Rechazo Estricto)

| N° | Consulta Fuera de Dominio | Comportamiento Esperado | Similitud Obtenida | Clasificación | Resultado |
| :--- | :--- | :--- | :---: | :---: | :---: |
| 8 | *receta casera para preparar pastel de chocolate con fresas* | $S < 0.25$ (Rechazo) | `0.0000` | *Coincidencia baja* | **OK** |
| 9 | *lavadora samsung digital no centrifuga ni bota el agua en el ciclo* | $S < 0.25$ (Rechazo) | `0.0486` | *Coincidencia baja* | **OK** |
| 10 | *vuelos baratos y reservas de hotel en cusco machu picchu* | $S < 0.25$ (Rechazo) | `0.0000` | *Coincidencia baja* | **OK** |

---

## 3. Métricas Obtenidas en el Banco de Pruebas

$$\text{Precision@1} = \frac{7}{7} = 100.0\%$$
$$\text{Tasa de Rechazo Fuera de Dominio} = \frac{3}{3} = 100.0\%$$
$$\text{Efectividad en Casos de Prueba Controlados} = \frac{10}{10} = 100.0\%$$

---

## 4. Declaración de Limitaciones Metodológicas y Defensa ante Jurado

> [!WARNING]
> **Aclaración Científica de Tesis:**
> 1. **Tamaño Muestral y Sesgo de Diseño**: Este benchmark interno consta de $N=10$ casos diseñados por el equipo de investigación para validar las rutas críticas del vectorizador y el diccionario de acrónimos DTC.
> 2. **Validez Interna vs. Validez Externa**: La tasa de 10/10 demuestra la coherencia algorítmica del subsistema RAG ante consultas estructuradas de prueba, pero **no constituye una prueba de 100% de efectividad general ante consultas del mundo real** con jerga coloquial imprevista, faltas ortográficas graves o síntomas cruzados complejos.
> 3. **Propuesta para Trabajo Futuro**: Para una evaluación estadística exhaustiva, se recomienda conformar un corpus ciego de evaluación con al menos $N=150$ consultas redactadas libremente por mecánicos independientes de distintos talleres.
