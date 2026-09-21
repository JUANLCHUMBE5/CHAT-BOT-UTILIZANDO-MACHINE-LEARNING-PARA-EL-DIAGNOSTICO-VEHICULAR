# FASE 11 — ETAPA 2: REGISTRO DETALLADO DE CAMBIOS DE CÓDIGO (CODE CHANGES)
**CarBot — Sistema de Diagnóstico Automotriz con Machine Learning & RAG**

---

## Resumen Ejecutivo de Modificaciones

En la Etapa 2 de Fase 11 se implementaron correcciones quirúrgicas y modulares dirigidas exclusivamente a subsanar los defectos identificados en la línea base `FASE11_BASELINE_E2E_V1`:
1. **Resolución de Conmutación de Contexto A/C (`ORQUESTADOR_AC_CONTEXT_SWITCH` / `DEF_F11_004`)**:
   - Distinción semántica clara entre queja principal de Climatización (`CLIMATIZACION`) vs. condición operacional de carga para el motor (`MOTOR`).
   - Prevención de descarte de síntomas al acumular turnos (`CASE_092` y `CASE_093`).
2. **Política y Banners de Seguridad Crítica (`DEF_F11_005` a `DEF_F11_009`)**:
   - Implementación de `PoliticaSeguridad` para 5 condiciones vehiculares de riesgo inminente (Frenos, Presión de Aceite en Cero, Fuga de Combustible, Sobrecalentamiento Severo con Vapor, Alta Tensión EV/Híbridos).
3. **Refinamiento del Auto-Interrogador Técnico (`DEF_F11_001`, `DEF_F11_002`, `DEF_F11_003`)**:
   - Detección de síntomas difusos no calificados (`hace un ruido`, `se siente raro al manejar`, `pierde fuerza`), emitiendo auto-preguntas dinámicas basadas en hipótesis diferenciales sin loops y sin alterar el umbral global de 0.70.
4. **Preservación Estricta de Modelos e Invariantes**:
   - **0%** de modificación en modelos ML, vectorizador TF-IDF, calibración de confianza, datasets (TRAIN/DEV/TEST10/FIELD), índice FAISS y corpus RAG.
   - 100% inmutabilidad criptográfica confirmada (19/19 F8.3, 3/3 C1).

---

## Archivos Modificados y Nuevos Creados

### 1. `backend/src/core/diagnostico/politica_seguridad.py` (NUEVO ARCHIVO)
- **Propósito**: Capa centralizada e independiente para evaluar severidad de riesgos y anteponer banners de advertencia enfáticos al inicio de la respuesta diagnóstica.
- **Líneas añadidas**: 148 líneas.
- **Componentes clave**:
  - `SeveridadSeguridad` (Enum: `CRITICAL_STOP`, `URGENT_INSPECTION`, `NORMAL_DIAGNOSTIC`).
  - Patrones deterministas regex: `PATRON_FRENO_CRITICO`, `PATRON_ACEITE_CRITICO`, `PATRON_COMBUSTIBLE_CRITICO`, `PATRON_TEMPERATURA_CRITICA`, `PATRON_ALTA_TENSION`.
  - Banners estandarizados: `BANNER_FRENO`, `BANNER_ACEITE`, `BANNER_COMBUSTIBLE`, `BANNER_TEMPERATURA`, `BANNER_HV`.
  - Métodos: `evaluar_severidad(texto_usuario, diagnostico_ml)` y `enriquecer_respuesta_seguridad(...)` que también sanea posibles instrucciones peligrosas (como mandar a usuarios inexpertos a reparar alta tensión con guantes).

---

### 2. `backend/src/core/conversacion/detector_polaridad.py`
- **Propósito**: Reconocer expresiones de quejas de climatización con polaridad positiva y negativa para el extractor de hechos.
- **Líneas modificadas**: 97–115.
- **Detalle del cambio**:
  - Añadida definición canónica `"falla de climatización / aire acondicionado no enfría"` a `DEFINICIONES_SINTOMAS`.
  - Patrones regex afirmativos: `no enfría`, `solo enfría`, `enfría poco/nada`, `deja de enfriar`, `sale aire caliente/tibio`, `compresor no entra/acopla`, `fuga de gas r134a`.
  - Patrones regex negativos: `aire acondicionado enfría bien`, `clima enfría bien`, `enfría normal`.

---

### 3. `backend/src/core/conversacion/extractor_hechos.py`
- **Propósito**: Diferenciar semánticamente si el A/C es la avería primaria de climatización o un modificador de carga motor.
- **Líneas modificadas**: 271–316.
- **Detalle del cambio**:
  - Si el usuario reporta `es_queja_climatizacion`: se registra `sintoma_climatizacion` (`aire acondicionado no enfría / sale aire caliente`) y se asigna `estado.dominio_probable = "CLIMATIZACION"`.
  - Si únicamente se menciona encendido de A/C (`tiene_mencion_ac`) sin queja de falta de frío: se registra `modificador_ac = "A/C encendido"` manteniendo el dominio `MOTOR`.

---

### 4. `backend/src/core/conversacion/sintetizador_consulta.py`
- **Propósito**: Garantizar consultas sintetizadas gramaticalmente correctas y evitar redundancia.
- **Líneas modificadas**: 80–120.
- **Detalle del cambio**:
  - Supresión de `con A/C encendido` cuando la queja principal es de climatización (`sintoma_climatizacion`), evitando la frase contradictoria `"no enfría con A/C encendido"`.
  - Conexión limpia de condiciones de operación (`al `, `en `, `deja `).

---

### 5. `backend/src/core/conversacion/diccionario_automotriz.py`
- **Propósito**: Evitar colisión de conceptos entre semáforo en rojo y testigos del tablero.
- **Líneas modificadas**: 52–58.
- **Detalle del cambio**:
  - Desambiguación en `PATRONES_CONDICION`: reemplazado el patrón laxo `luz\s+roja` por `semáforo\s+(?:en\s+)?rojo|luz\s+roja\s+del\s+semáforo`.
  - Evita que `"la luz roja de presión de aceite encendió en el tablero"` sea interpretado erróneamente como vehículo detenido esperando en un semáforo.

---

### 6. `backend/src/core/session_manager.py`
- **Propósito**: Preservar datos vehiculares en conmutación de tema y evitar descarte de síntomas ricos.
- **Líneas modificadas**: 45–55, 69–87.
- **Detalle del cambio**:
  - En `obtener_sintoma_completo()`: verificación de `tiene_sintomas` antes de devolver la consulta sintetizada. Si no se extrajo un síntoma estructurado formal, retorna el texto crudo del usuario (`" ".join(self.sintomas)`), evitando que textos ricos sean truncados a fragmentos de vehículo (`"Toyota."`) o combustible (`"a Gasolina."`).
  - En `finalizar_caso()`: reinicia los síntomas y la avería activa conservando datos del vehículo para diagnósticos multi-falla en la misma sesión.

---

### 7. `backend/src/core/intent_classifier.py`
- **Propósito**: Asegurar que consultas legítimas vehiculares y de climatización no sean marcadas como fuera de alcance.
- **Líneas modificadas**: 21, 30, 42–45, 80–85.
- **Detalle del cambio**:
  - Incorporación de `"perdida"`, `"solo enfria"`, `"temperatura alta"`, `"vapor blanco por el capó"`, `"se siente raro"` en `PATRONES_SINTOMA`.
  - Incorporación de términos `"potencia"`, `"perdida"`, `"climatizacion"`, `"climatización"`, `"manejar"`, `"manejando"`, `"conducir"`, `"conduciendo"`, `"temperatura"`, `"vapor"`, `"capo"`, `"capó"`, `"aguja"` en `TERMINOS_AUTOMOTRICES`.

---

### 8. `backend/src/core/diagnostico/ambiguity_checker.py`
- **Propósito**: Permitir que respuestas de una sola condición u operativas sean reconocidas como continuaciones.
- **Líneas modificadas**: 28–42.
- **Detalle del cambio**:
  - Ampliación de `es_continuacion_contextual` para reconocer condiciones operacionales (`en subida`, `en bajada`, `en pendiente`, `en frío`, `en caliente`, `en ralentí`, `al acelerar`, `al frenar`, `con el aire`, `con a/c`, `con carga`).

---

### 9. `backend/src/core/diagnostico/auto_interrogador.py`
- **Propósito**: Emitir auto-preguntas dinámicas en síntomas difusos o poco caracterizados sin alterar el umbral general.
- **Líneas modificadas**: 160–240.
- **Detalle del cambio**:
  - Inclusión de `es_ruido_difuso` (`hace un ruido`, `suena feo`, `suena raro` sin discriminador acústico ni componente).
  - Inclusión de `es_manejo_difuso` (`se siente raro al manejar`, `comportamiento extraño`).
  - Ampliación de `es_tironeo_difuso` con `"perdida de potencia"`, `"pérdida de potencia"`, `"pierde potencia"`.

---

### 10. `backend/src/core/diagnostico/text_processor.py`
- **Propósito**: Orquestar de forma segura la integración de la política de seguridad y la lógica conversacional.
- **Líneas modificadas**: 312–338, 593–606, 792–805.
- **Detalle del cambio**:
  - Evaluación previa de seguridad en línea 595: si la consulta involucra una condición de riesgo crítico (`CRITICAL_STOP`), se inhibe la interrupción por auto-pregunta para asegurar respuesta inmediata con advertencia.
  - Enriquecimiento de la respuesta final en línea 794: antepone de forma determinista el banner de seguridad sin depender de la creatividad del LLM.
  - Gestión optimizada de continuaciones de turno: evita reinicios de sesión cuando el turno 1 solo aportó datos del vehículo.
