# CIERRE EXPERIMENTAL Y APERTURA DE TRABAJO DE CAMPO
**CARBOT — TESIS DE GRADO 2026**  
**Fecha de emisión:** 20 de Septiembre de 2026  
**Documento Maestro:** INFORME INTEGRAL DE GOBERNANZA, CIERRE EXPERIMENTAL Y PREPARACIÓN DE CAMPO  
**Estado Operacional:** APTO_PARA_PILOTO_PRESENCIAL  

---

## 1. RESUMEN EJECUTIVO Y ESTADO DE CONGELAMIENTO

El presente informe certifica la culminación formal de todas las actividades exploratorias y experimentales de laboratorio (Fases V2, V2.1 y V2.2) y establece la preparación operativa definitiva del sistema **CarBot** para la ejecución del piloto presencial y la subsiguiente recolección de datos en taller.

### Certificación de Invariantes:
- **Taxonomía Oficial Confirmada:** 61 clases vehiculares y 7 macro-sistemas automotrices.
- **Modelo Oficial de Tesis:** `CARBOT_PRECAMPO_FROZEN` (Linear SVM con vectorización TF-IDF).
- **Módulo RAG Oficial:** Corpus RAG OEM Frozen (FAISS indexado con manuales técnicos de taller, MRR = 0.8704).
- **Optimización de Modelos:** `DETENER_OPTIMIZACION_ML_PRECAMPO = TRUE` (Cierre estricto sin reentrenamientos adicionales).
- **Artefactos Productivos:** 13/13 archivos auditados por hash SHA-256 con 0 alteraciones (`PRODUCTION_ARTIFACTS_MODIFIED = 0`).

---

## 2. CIERRE Y ARCHIVADO FORMAL DE VERSIONES EXPERIMENTALES

Los tres entornos de desarrollo exploratorio quedan clasificados como `EXPERIMENTAL_ARCHIVED`:
1. `machine_learning/experimentos/carbot_v2/`
   - *Veredicto:* `SVM_V2_MEJORA_PARCIAL` / `RAG_V2_EMPEORA` (Descartado RAG V2 tras caída de MRR de 0.8704 a 0.7130).
2. `machine_learning/experimentos/carbot_v2_1/`
   - *Veredicto:* `V2_1_MEJORA_PARCIAL` (Efectiva mitigación de incompatibilidades de combustible pero sobreajustado a bancos específicos).
3. `machine_learning/experimentos/carbot_v2_2/`
   - *Veredicto:* `RESULTADO_EXPERIMENTAL_PROMETEDOR_SIN_SIGNIFICANCIA_ESTADISTICA`.
   - V2.2-A demostró mejoras técnicas en pares contrastivos causales (45% a 70%), pero no superó con significancia estadística al modelo congelado en el conjunto global de pruebas.
   - **Estatus de V2.2-A:** `CANDIDATO_EXPERIMENTAL_POST_TESIS` (Preservado para publicaciones futuras post-sustentación).

---

## 3. FE DE ERRATAS DOCUMENTAL Y RECONCILIACIÓN DE VEREDICTOS V2.2

Se emitió el documento formal `docs/auditorias/CIERRE_EXPERIMENTAL_V2_2_Y_FE_ERRATAS.md` para corregir y reconciliar cualquier inconsistencia entre los términos preliminares `V2_2_MEJORA_PARCIAL` y `V2_2_CANDIDATO_FUERTE`:
- V2.2-A alcanzó Top-1 promedio de 89.25% y Macro-F1 de 88.89% en los 3 bancos ciegos (732 casos), frente a 87.70% y 86.78% del modelo Frozen.
- No obstante, la prueba estadística pareada de McNemar sobre los desacuerdos arrojó $p = 0.16898 \approx 0.1690 > 0.05$.
- En consecuencia, la decisión operacional de la investigación es ratificar incondicionalmente a `CARBOT_PRECAMPO_FROZEN` como el único clasificador en producción para la tesis.

---

## 4. AUDITORÍA DEFINITIVA DE DATOS SINTÉTICOS

Se certifica el recuento exacto de datos sintéticos contrastado con los artefactos del repositorio:
- `SYNTHETIC_GENERATED_TOTAL = 140` (Generados exclusivamente en Fase V2.2 para 14 clases con déficit en laboratorio).
- `SYNTHETIC_USED_V2_2_A = 0` (V2.2-A fue entrenado con 7,119 muestras puramente reales y contrastivas técnicas, sin ningún dato sintético).
- `SYNTHETIC_USED_V2_2_B = 70` (Incorporó 70 sintéticos en experimentación offline).
- `SYNTHETIC_USED_V2_2_C = 140` (Incorporó 140 sintéticos en experimentación offline).
- `SYNTHETIC_USED_IN_THESIS_PRODUCTION = 0` (El modelo productivo `CARBOT_PRECAMPO_FROZEN` contiene 0 sintéticos).
- `SYNTHETIC_USED_IN_OFFICIAL_PREPOST = 0` (La base de datos oficial prohíbe sintéticos y solo registra casos reales de taller).

---

## 5. CORRECCIÓN METODOLÓGICA DE LA PRUEBA DE MCNEMAR

Se rectifica la interpretación estadística en los reportes técnicos:
- **Naturaleza del test:** Dado que ambos modelos clasificaron exactamente los mismos 732 ítems de los bancos de prueba, las observaciones son **pareadas por caso**.
- **Resultado:** $p = 0.1690$ al nivel $\alpha = 0.05$.
- **Interpretación rigurosa:** No se encontró evidencia estadísticamente significativa para rechazar la hipótesis nula de igual tasa de acierto.
- **Aclaración epistemológica:** No se afirma "equivalencia demostrada" (la ausencia de significancia no prueba equivalencia bioestadística TOST), sino insuficiencia de evidencia para justificar un cambio en el clasificador congelado.

---

## 6. ESTADO DE BASE DE DATOS Y CONTADORES OFICIALES

Consulta directa a la base de datos PostgreSQL (`ValidacionTaller`):
```text
PRE_OFICIAL = 0 / 30
POST_OFICIAL = 0 / 30
TOTAL_OFICIAL = 0 / 60
```
- Los 1,930 registros históricos previos generados en pruebas de integración se encuentran auditados bajo `estado_registro = 'borrador'`, `origen_clave = NULL` y están **100% aislados y excluidos** de los contadores y de la exportación oficial.
- La muestra oficial de 60 casos se mantiene en cero absoluto previo al inicio del trabajo de campo.

---

## 7. SIMULACIÓN DE CASOS PRE-CAMPO (SUITE A - G)

Mediante el script automatizado `scripts/fase13/simulacion_casos_precampo.py` se validaron satisfactoriamente las 7 pruebas de gobernanza:
- **CASO A (PRE tradicional completo):** Superado. Registro en entorno `PILOT` sin requerir CarBot ni `diagnostico_id`.
- **CASO B (POST asistido completo):** Superado. Registro en `PILOT` vinculado a CarBot con inmutabilidad y telemetría completa.
- **CASO C (Registro incompleto):** Superado. Registro sin evidencia técnica fue automáticamente degradado a `borrador`.
- **CASO D (Intento de adulterar predicción CarBot):** Superado. El backend rechazó la alteración enviada y preservó la predicción original.
- **CASO E (Intento de exportar PILOT como oficial):** Superado. Registros piloto son estrictamente omitidos del export oficial.
- **CASO F (Fase y tipo incompatibles):** Superado. Bloqueo con `ValueError` ante mezclas como `THESIS_PRETEST` con `Post-test`.
- **CASO G (Omisión de entorno):** Superado. Asignación automática por defecto a `DEVELOPMENT`, jamás a `THESIS_*`.
- **Teardown:** Limpieza completa de filas de prueba, restaurando los contadores oficiales a 0/60.

---

## 8. AUDITORÍA DE INTERFAZ FRONTEND (UI)

- **Inspección de Componentes:** En `ValidacionNuevoCasoModal.tsx`, `ValidacionMetricasCards.tsx` y `ConfirmacionOficialModal.tsx`:
  - Selector visible con 3 botones estilizados: `DESARROLLO / PRUEBA`, `PILOTO (Presencial)` y `OFICIAL DE TESIS (N=60)`.
  - Modal de confirmación con escudo rojo (`ShieldAlert`) para impedir la creación accidental de registros oficiales.
  - Bloqueo de solo lectura (`readOnly`) en el campo de predicción al vincular un diagnóstico de CarBot.
  - Contadores visuales visibles: `0 / 60 registros oficiales` y leyenda metodológica visible de trabajo de campo en proceso.
- **Declaración sobre Navegador Automatizado:**  
  *Se declara explícitamente que la sesión automática CDP de subagente de navegador sufrió timeout por configuración local; por consiguiente, la auditoría visual fue certificada mediante análisis exhaustivo de código TSX/React y queda programada la confirmación visual presencial en el primer hito del piloto en taller.*

---

## 9. MATRIZ DE TRAZABILIDAD Y FORMATO LONG

Se formalizó la matriz metodológica en `docs/auditorias/MATRIZ_TRAZABILIDAD_INSTRUMENTO_SISTEMA.md`:
- **Variable Independiente:** Indicador 1 (Síntomas), Indicador 2 (Procesamiento) e Indicador 3 (Exactitud Linear SVM).
- **Variable Dependiente:** Ficha 1 (Acierto PPCF), Ficha 2 (Completitud PRDC - 8 campos) y Ficha 3 (Tiempo TPRD - `tiempo_diagnostico_minutos`).
- **Separación de Tiempos:** El tiempo metodológico (`tiempo_diagnostico_minutos`) es la variable oficial de tesis medida por el observador; la telemetría del sistema (`tiempo_inferencia_ml_ms`) es una métrica de rendimiento auxiliar de software.
- **Diseño de Observaciones Independientes:**
  - 30 registros Pre-test + 30 registros Post-test = 60 filas en formato **LONG**.
  - No existe `caso_pareja_id` ni emparejamiento ficticio de vehículos distintos.
  - Alerta metodológica: `PENDIENTE_CONFIRMACION_ASESOR_ESTADISTICO = TRUE`.

---

## 10. PROTOCOLOS OPERATIVOS DE CAMPO

Se generaron los tres manuales operativos para el taller:
1. `docs/campo/CHECKLIST_INICIO_TRABAJO_CAMPO.md`: Guía de verificación para antes, durante y al final de cada jornada.
2. `docs/campo/PROTOCOLO_RECOLECCION_PRETEST.md`: 12 pasos secuenciales para el diagnóstico tradicional (sin CarBot).
3. `docs/campo/PROTOCOLO_RECOLECCION_POSTTEST.md`: 12 pasos secuenciales para el diagnóstico asistido por CarBot.

---

## 11. AUDITORÍA CRIPTOGRÁFICA FINAL (HASHES SHA-256)

Ejecución de `scripts/audit_hashes_fase12_3.py` contra `CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json`:
- **Total artefactos auditados:** 13
- **Artefactos coincidentes:** 13
- **Artefactos modificados:** 0
- **Resultado:** `HASH_PRE == HASH_POST` (Integridad 100% preservada).

---

## 12. VEREDICTO FINAL DE FASE 13

```text
============================================================
VEREDICTO FINAL: APTO_PARA_PILOTO_PRESENCIAL
ACCION INMEDIATA: PILOTO_PRESENCIAL_REAL
============================================================
```

*Nota Metodológica:* El sistema no se declara `APTO_PARA_RECOLECCION_OFICIAL` hasta que el piloto presencial en taller (5 a 10 casos en entorno `PILOT`) haya sido ejecutado satisfactoriamente por los mecánicos y el observador técnico.
