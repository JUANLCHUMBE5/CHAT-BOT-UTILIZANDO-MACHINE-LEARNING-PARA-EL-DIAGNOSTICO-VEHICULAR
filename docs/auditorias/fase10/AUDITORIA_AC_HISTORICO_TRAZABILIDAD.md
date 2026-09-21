# AUDITORÍA FORENSE: TRAZABILIDAD DEL CASO HISTÓRICO DE CLIMATIZACIÓN (A/C)

## 1. Contexto y Pregunta de Auditoría

En la validación del modelo candidato C1 vs. la línea base F8.3, se reportó que al evaluar consultas directas y aisladas sobre fallas de aire acondicionado (ej. *"Prendo el boton A/C del aire acondicionado sale aire tibio ambiente y no enfria nada..."* o *"Toyota Corolla 2017 aire acondicionado no enfria en cabina, compresor acopla pero presion de baja y alta estan igualadas en 70 PSI"*), tanto F8.3 como C1 clasifican la falla con más del **95% a 99.8% de confianza** hacia:
`Falla en compresor de aire acondicionado o fuga de gas R134a` (Macro: `CLIMATIZACION`).

Sin embargo, existía el reporte histórico de que en un caso conversacional real de taller, la falla fue atribuida a averías de motor (`O2 / mezcla rica`, `Bomba de gasolina quemada o con baja presión`, o `Inyectores sucios o filtro de combustible obstruido`).

Esta auditoría reconstruye la cadena de procesamiento completa para determinar la causa raíz de dicho comportamiento.

---

## 2. Reconstrucción de la Cadena de Procesamiento

Se auditaron los componentes del pipeline en `backend/src/core/`:
- Sanitizador (`src/core/sanitizer.py`: `sanitizar_prompt_usuario`)
- Normalizador jerga (`src/core/diagnostico/text_processor.py`: `normalizar_jerga_peruana`)
- Purificador semántico (`src/core/diagnostico/semantic_purifier.py`: `purificar_sintoma_para_vectorizador_ml`)
- Gestor de sesión y hechos (`src/core/session_manager.py`: `obtener_sintoma_completo`)
- Sintetizador clínico (`src/core/conversacion/sintetizador_consulta.py`: `SintetizadorConsulta.sintetizar`)
- Segmentador de casos (`src/core/conversacion/segmentador_casos.py`: `SegmentadorCasos.evaluar_transicion`)

### Comparativa de Trazabilidad por Escenario

#### Escenario A: Consulta Aislada Directa (Cotidiana o Técnica)
1. **Texto Original del Usuario:**
   *"Prendo el boton A/C del aire acondicionado sale aire tibio ambiente y no enfria nada parece ventilador comun y corriente."*
2. **Texto Sanitizado:**
   *"Prendo el boton A/C del aire acondicionado sale aire tibio ambiente y no enfria nada parece ventilador comun y corriente."*
3. **Texto Normalizado:**
   *"prendo el boton a/c del aire acondicionado sale aire tibio ambiente y no enfria nada parece ventilador comun y corriente."*
4. **Purificado para ML:**
   *"prendo el boton a/c del aire acondicionado sale aire tibio ambiente y no enfria nada parece ventilador comun y corriente."*
5. **Predicción del Modelo:**
   - **F8.3 Top-1:** `Falla en compresor de aire acondicionado o fuga de gas R134a` (**98.4%**) [Macro: `CLIMATIZACION`]
   - **C1 Top-1:** `Falla en compresor de aire acondicionado o fuga de gas R134a` (**95.5%**) [Macro: `CLIMATIZACION`]
6. **Conclusión Escenario A:** El clasificador supervisado Linear SVM + TF-IDF predice CLIMATIZACIÓN de forma contundente y sin ambigüedad.

---

#### Escenario B: Interacción Multi-turno con Síntomas de Motor Previos (Evidencia Documentada: Piloto Fase 9.2, CASO 02)
En el registro histórico `backend/tests/fase9/resultados_piloto_fase9_2.json` (Caso 02 - Chevrolet Sail), el mecánico interactuó en varios turnos:
- **Turno 1:** *"Chevrolet Sail 2018"*
- **Turno 2:** *"pierde fuerza"*
- **Turno 3:** *"en subida"*
  - En este punto, el orquestador diagnosticó:
    1. *Bomba de gasolina quemada o con baja presión* (57.4%)
    2. *Falla en bujías o bobinas de encendido (misfire)* (27.7%)
    3. *Inyectores sucios o filtro de combustible obstruido* (14.9%)
- **Turno 4 (El usuario introduce mención de A/C):**
  - **Texto original del usuario:** *"con el aire acondicionado encendido"*
  - **Comportamiento del orquestador conversacional:**
    En lugar de abrir un nuevo caso diagnóstico, el sistema extrajo el hecho estructurado como un **modificador de carga de motor** (`modificador_ac = "A/C encendido"`).
  - **Query Acumulada / Sintetizada por Conversación:**
    `"Chevrolet Sail año 2018. presenta pérdida de potencia. cuando está al acelerar bajo carga. con A/C encendido."`
  - **Input Final Enviado al Vectorizador ML:**
    `"chevrolet sail año 2018. presenta pérdida de potencia. cuando está al acelerar bajo carga. con a/c encendido."`
  - **Predicción de F8.3:**
    1. *Falla en bujías o bobinas de encendido (misfire)* (**56.3%**)
    2. *Bomba de gasolina quemada o con baja presión* (**31.2%**)
    3. *Inyectores sucios o filtro de combustible obstruido* (**4.9%**)
  - **Predicción de C1:**
    1. *Bomba de gasolina quemada o con baja presión* (**59.2%**)
    2. *Falla en bujías o bobinas de encendido (misfire)* (**22.7%**)
    3. *Inyectores sucios o filtro de combustible obstruido* (**8.5%**)

---

#### Escenario C: Contaminación Cruzada por Fallo de Segmentación (Evidencia Histórica Fase 9.9 - Fase 9.10)
Tal como se documentó formalmente en `reporte_fase9_10_segmentacion_casos.md` y `reporte_fase9_12_motor_transmision.md`:
1. **Mecanismo:** Antes de la introducción de `SegmentadorCasos` (Fase 9.10), si una sesión previa de WhatsApp contenía quejas de motor (mezcla rica, humo negro, sensor de oxígeno) y el usuario cambiaba de tema hacia el aire acondicionado en el mismo hilo de chat, los hechos del caso anterior **no se limpiaban**.
2. **Query Sintetizada Resultante:**
   `"Kia con humo negro y consumo alto. Scanner marca mezcla rica. Prendo el aire acondicionado y no enfria sale aire tibio."`
3. **Resultado al pasar por ML:**
   - La masa de n-gramas de motor (`humo negro`, `consumo alto`, `mezcla rica`, `scanner`) compite directamente con los términos de climatización (`aire acondicionado`, `no enfria`, `aire tibio`).
   - En F8.3, `Falla en sensor de oxigeno o mezcla rica` obtuvo **50.4%**, relegando `Falla en compresor de aire acondicionado` al segundo lugar con **48.4%**, acompañado de `Inyectores sucios` y `Bomba de gasolina`.

---

## 3. Dictamen Forense

| Pregunta de Auditoría | Respuesta Forense | Evidencia Documental |
| :--- | :--- | :--- |
| **¿El modelo Linear SVM falla al clasificar textos de A/C aislados?** | **NO** (Top-1 > 95% en F8.3 y C1) | Pruebas directas de regresión en `scratch/probar_caso_ac_forense.py` y `evaluacion_v4_100_casos.json`. |
| **¿El preprocesador de texto o sanitizador altera la semántica de A/C?** | **NO** (Preserva tokens literales A/C, tibio, compresor) | Funciones `sanitizar_prompt_usuario` y `normalizar_jerga_peruana`. |
| **¿Existe evidencia documental de la causa del fallo histórico?** | **SÍ, REPRODUCIBLE CON EVIDENCIA DOCUMENTADA** | `resultados_piloto_fase9_2.json` (Caso 02) y `reporte_fase9_10_segmentacion_casos.md`. |
| **Causa Raíz Identificada:** | **Contaminación de hechos conversacionales multi-turno y categorización de A/C como modificador de carga de motor.** | En sesiones activas donde existía una queja motriz previa, el orquestador concatenaba la condición `con A/C encendido` como contexto de sobreesfuerzo del motor, provocando que el clasificador diagnosticara el sistema de combustible/encendido (`O2 / mezcla rica`, `Bomba de gasolina`, `Inyectores`). |
