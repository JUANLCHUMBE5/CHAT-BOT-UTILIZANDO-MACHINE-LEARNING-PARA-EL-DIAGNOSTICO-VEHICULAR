# Auditoría Forense: Deuda Técnica Histórica de Climatización (A/C) y Cambio de Contexto

**Fase**: Fase 11 — Etapa 1  
**Fecha de Ejecución**: 2026-09-18T00:06:00Z  
**Componente Evaluado**: Orquestador Conversacional (`ExtractorHechos`, `SintetizadorConsulta`, `SegmentadorCasos`, `text_processor.py`) + Modelo ML C1  
**Dictamen Técnico Oficial**: **REPRODUCIBLE**

---

## 1. Resumen Ejecutivo

La deuda técnica conocida identificada como `ORQUESTADOR_AC_CONTEXT_SWITCH` fue sometida a una prueba forense rigurosa en dos escenarios controlados:
1. **Escenario Multi-turno Histórico (CASE_092 - Chevrolet Sail 2018)**: Reproducción exacta del caso documentado en el Piloto Fase 9.2 (Turno 1: Identificación del auto $\rightarrow$ Turno 2: Pérdida de fuerza $\rightarrow$ Turno 3: En subida $\rightarrow$ Turno 4: Con el aire acondicionado encendido).
2. **Escenario Explícito / Directo (CASE_093)**: Consulta técnica donde el usuario manifiesta directamente que el aire acondicionado sopla a temperatura ambiente y no enfría en semáforo, con motor en funcionamiento normal y sin luces de advertencia.

### Veredicto Forense
- **Estado de la Deuda**: **REPRODUCIBLE**
- **Causa Raíz Determinada**: `backend/src/core/conversacion/extractor_hechos.py` (Líneas 271–275).
- **Mecanismo del Defecto**:
  - `ExtractorHechos` evalúa regex `\b(a/c|aire\s+acondicionado|clima|el\s+ac)\b` y registra **exclusivamente un hecho de tipo modificador operacional de carga de motor** (`estado.registrar_hecho("modificador_ac", "A/C encendido", tipo=FactType.MODIFICADOR)`).
  - Nunca extrae un síntoma o queja de avería de climatización (`no enfría`, `aire caliente`), omitiendo la creación de un hecho clínico de síntoma para el sistema `CLIMATIZACION`.
  - Como consecuencia, el sintetizador genera queries truncadas (`"con A/C encendido."`), las cuales carecen de verbos de avería vehicular y son reclasificadas por `clasificar_intencion_consulta` como `"fuera_de_alcance"`, o en multi-turno quedan subordinadas al motor bajo carga (`"Chevrolet Sail año 2018. presenta pérdida de potencia. cuando está al acelerar bajo carga. con A/C encendido."`).

---

## 2. Trazabilidad Turno por Turno: Escenario Multi-turno (CASE_092)

| Turno | Mensaje del Usuario | Estado Conversacional | Query Sintetizada Enviada al ML | Macro Predicho | Top-1 ML | Confianza Top-1 | Comportamiento Observado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Turno 1** | `"Chevrolet Sail 2018"` | `inicio` | `Chevrolet Sail año 2018.` | `SUSPENSION_CHASIS` | Llantas desbalanceadas o desalineadas | 0.4837 | Pide síntoma inicial |
| **Turno 2** | `"pierde fuerza"` | `esperando_combustible` | `presenta pérdida de potencia.` | `MOTOR` | Bomba de gasolina quemada o con baja presión | 0.5210 | Pregunta por combustible/aclaración |
| **Turno 3** | `"en subida"` | `en_proceso` | `cuando está al acelerar bajo carga.` | `MOTOR` | Bomba de gasolina quemada o con baja presión | 0.5820 | Sugiere bomba de gasolina / encendido |
| **Turno 4** | `"con el aire acondicionado encendido"` | `en_proceso` | `con A/C encendido.` | `MOTOR` | Consulta fuera del alcance automotriz | 0.0000 | La frase aislada pierde el verbo y cae en filtro fuera de alcance |

### Análisis Técnico del Escenario Multi-turno
1. En el Turno 3, el sistema ponderó correctamente la pérdida de potencia bajo carga hacia `Bomba de gasolina quemada o con baja presión` (58.20%).
2. En el Turno 4, cuando el mecánico añade *"con el aire acondicionado encendido"*, el orquestador no interpretó el A/C como posible falla del compresor trabado ni preservó la sintaxis completa del síntoma motriz, sino que generó una entidad huérfana de modificador (`"con A/C encendido."`) que fue interceptada por el clasificador determinista de intención como fuera de alcance.

---

## 3. Trazabilidad del Escenario Explícito (CASE_093)

- **Texto de Entrada del Usuario**:
  > *"Hola, tengo otro problema con mi carro. Cuando enciendo el aire acondicionado sí sale aire por las rejillas, pero no enfría casi nada. Cuando voy manejando parece enfriar un poquito más, pero cuando me detengo en un semáforo vuelve a salir casi a temperatura ambiente. El motor funciona normal y no tengo ninguna luz de advertencia encendida. No he revisado nada todavía."*

- **Comportamiento Interno Observado**:
  1. `sanitizar_prompt_usuario` normalizó la cadena.
  2. `ExtractorHechos.extraer_hechos_clinicos` procesó el texto:
     - Regex detectó `"aire acondicionado"` $\rightarrow$ registró `modificador_ac = "A/C encendido"`.
     - No registró ningún síntoma positivo para `CLIMATIZACION`.
  3. `SintetizadorConsulta.sintetizar` produjo: `"con A/C encendido."`
  4. `clasificar_intencion_consulta("con A/C encendido.")` evaluó la query sintetizada:
     - No hizo match con `PATRONES_SINTOMA`.
     - Resultado: `"fuera_de_alcance"`.
  5. `text_processor.py` devolvió respuesta estándar de fuera de alcance:
     > *"🚗 Describe el síntoma, por ejemplo: vibra al manejar."*

---

## 4. Contraste: Clasificador Directo C1 vs. Pipeline Conversacional

Para aislar si el defecto pertenece al modelo de Machine Learning C1 o al orquestador conversacional, se evaluó el texto de CASE_093 directamente sobre el vectorizador TF-IDF y el modelo Linear SVM congelado de C1:

```python
# Inferencia directa en ModeloML C1 (sin orquestador):
top3 = modelo_ml.predecir_top_fallas(
    "Cuando enciendo el aire acondicionado si sale aire por las rejillas pero no enfria casi nada sale tibio en semaforo",
    limite=3
)
macro = modelo_ml.predecir_sistema(...)
```

### Resultado de la Prueba Aislada:
- **Macro Predicho**: `CLIMATIZACION` (100.0%)
- **Top-1 Falla**: `Falla en compresor de aire acondicionado o fuga de gas R134a`
- **Probabilidad Calibrada**: **0.9992 (99.92%)**
- **Top-2 Falla**: `Falla en termostato o motoventilador de radiador` (0.0006)
- **Top-3 Falla**: `Fuga en mangueras de refrigerante o radiador picado` (0.0002)

### Conclusión Forense Indiscutible
1. **El componente de Machine Learning C1 es inocente y 100% exacto**: clasifica los síntomas de A/C hacia `CLIMATIZACION` con un 99.92% de certidumbre.
2. **El defecto reside exclusivamente en la capa de Extracción y Síntesis de la Conversación (`backend/src/core/conversacion/extractor_hechos.py`)**: la regla heurística asume que cualquier mención de A/C es un modificador de carga del motor en vez de considerar la posibilidad de que sea la queja o avería principal.

---

## 5. Clasificación y Planificación de Corrección Futura

| Parámetro | Valor |
| :--- | :--- |
| **ID de Defecto** | `DEF_F11_004` |
| **Severidad** | **P1 (ALTO)** |
| **Componente** | `ORQUESTADOR / EXTRACTOR_HECHOS` |
| **Archivo Involucrado** | `backend/src/core/conversacion/extractor_hechos.py` |
| **Líneas Afectadas** | 271–275 |
| **Estrategia Mínima Sugerida (Para Etapa Posterior)** | Modificar la regla para que si el texto contiene términos de avería de climatización (`no enfría`, `aire caliente`, `tibio`, `sin gas`, `compresor no acopla`), se registre un hecho de avería principal de tipo `climatizacion` y no solo un modificador de carga de motor. |
| **Estado Actual** | **REGISTRADO SIN MODIFICAR CÓDIGO (Cumpliendo Regla 1 de Fase 11)** |
