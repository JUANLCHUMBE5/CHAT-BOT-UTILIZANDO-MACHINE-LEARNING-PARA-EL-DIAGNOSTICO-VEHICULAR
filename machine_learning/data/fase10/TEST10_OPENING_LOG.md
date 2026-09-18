# REGISTRO OFICIAL DE APERTURA DE TEST10
## Fase 10 — Protocolo de Apertura Única e Inmutable de Evaluación Ciega

**Fecha y Hora UTC**: 2026-09-17T23:46:00Z  
**Archivo de Prueba**: `machine_learning/data/fase10/test10_fase10_blind_v1.csv`  
**Hash SHA-256 de TEST10**: `6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c`  
**Estado Anterior**: `LOCKED_BLIND_TEST`  
**Predicciones Previas sobre TEST10**: **0 (Cero consultas o inferencias ejecutadas)**  

---

## 1. Identificación del Candidato Congelado

- **Candidato**: `F10-C1`
- **Ubicación Congelada**: `machine_learning/training/fase10/final_candidate/C1/`
- **Hash Modelo Falla (`modelo_diagnostico_c1.pkl`)**: `24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c`
- **Hash Vectorizador (`vectorizador_c1.pkl`)**: `060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7`
- **Hash Macro-Sistema (`modelo_sistema_c1_macrofix.pkl`)**: `dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c`
- **Estado del Candidato**: `FROZEN_BEFORE_TEST10`

---

## 2. Motivo y Reglas Metodológicas de la Apertura

- **Motivo Oficial**: `FINAL_ONCE_ONLY_EVALUATION`
- **Regla de No Re-Entrenamiento**: A partir de este momento, TEST10 se considera **ABIERTO**. Sus datos, textos, códigos o etiquetas no podrán ser utilizados retrospectivamente para reajustar hiperparámetros, realizar GridSearch, inyectar refuerzo sintético o entrenar un candidato alternativo C2.
- **Carácter Definitivo**: La evaluación que se ejecutará a continuación sobre los 366 casos de TEST10 constituye la **evaluación final definitiva** del componente de Machine Learning de Fase 10 para contrastar la hipótesis científica frente a la línea base Fase 8.3.
