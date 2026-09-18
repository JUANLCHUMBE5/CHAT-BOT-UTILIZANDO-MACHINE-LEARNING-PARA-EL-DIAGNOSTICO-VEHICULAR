# Fase 9.12 — Auditoría cross-system MOTOR → TRANSMISIÓN

**Fecha local de auditoría:** 16 de septiembre de 2026  
**Alcance:** mensaje físico de WhatsApp, PostgreSQL, segmentación, ML congelado 8.3,
compatibilidad/fusión, caché, RAG y runtime.  
**Restricción respetada:** no se modificaron ni reentrenaron ML, TF-IDF, TRAIN,
calibración, RAG, FAISS ni benchmarks congelados. Se detiene antes de Fase 10.

## 1. Conclusión ejecutiva

La **primera divergencia** ocurrió en `SegmentadorCasos`, antes del ML. El mensaje nuevo fue
detectado correctamente como dominio `TRANSMISION`, pero se mantuvo el caso de motor porque
la expresión interna **“y cuando entra da un golpe”** coincidió con el conector genérico
`y cuando`, considerado erróneamente evidencia de síntomas coexistentes.

El mensaje RAW aislado produce macro-sistema **TRANSMISION (64.64 %)** y una primera hipótesis
de transmisión. Por tanto, **este incidente no justifica reentrenamiento**.

## 2. Traza forense real

| Campo | Evidencia recuperada |
|---|---|
| `meta_message_id` | `wamid.HBgLNTE5NTUwOTUxNDcVAgASGBYzRUIwNTlGMEQwN0QwOUExRERCQ0EzAA==` |
| `conversation_id` | `f7a37e2d-efe8-4c26-9b62-9f4103e7b094` |
| recepción | `2026-09-17 04:04:02.757281+00:00` (`2026-09-16 23:04:02`, Lima) |
| `case_id` anterior | `2521e354-0adc-44d1-9345-ecf7c404c6c5` |
| `case_id` después | `2521e354-0adc-44d1-9345-ecf7c404c6c5` — no cambió |
| estado anterior | `MARCHA` |
| estado detectado actual | `MARCHA` |
| dominio anterior | `MARCHA_MOTOR` |
| dominio actual detectado | `TRANSMISION` |
| decisión | `MANTENER_CASO` |
| motivo | `SINTOMAS_COEXISTENTES: MARCHA_MOTOR_CON_TRANSMISION` |

### Mensaje RAW

> Hola, tengo un problema con mi carro automático. Cuando pongo la palanca en D entra normal,
> pero cuando paso a R demora unos segundos en enganchar. A veces tengo que acelerar un poquito
> para que recién entre la reversa y cuando entra da un golpe. Hacia adelante los cambios se
> sienten normales. No aparece ninguna luz de advertencia en el tablero y todavía no he revisado nada.

### Hechos antes del mensaje

- `temperatura=frío`
- `condicion_operacion=al acelerar bajo carga`
- `sintoma_pérdida_de_potencia=pérdida de potencia`
- `sintoma_funcionamiento_irregular_misfire=funcionamiento irregular / misfire`

### Hechos extraídos del mensaje durante el incidente

- `sintoma_ruido_anómalo=ruido anómalo`
- `comportamiento_ambiguo=a veces (tentativo)`

No se extrajeron la demora de acople ni el golpe al engranar reversa. La consulta enviada al ML fue:

```text
a Gasolina. presenta pérdida de potencia, funcionamiento irregular / misfire, ruido anómalo.
cuando está al acelerar bajo carga. ocurre en frío.
```

## 3. RAW → ML y consulta contaminada → ML

### A. Mensaje RAW exacto, inferencia aislada

- Macro RAW: `TRANSMISION 64.6417 %`, `ELECTRICO 31.9325 %`,
  `SUSPENSION_CHASIS 2.2834 %`, `FRENOS 1.1423 %`.
- Top 3 jerárquico:
  1. Falta o degradación de aceite de caja de cambios — `54.1803 %`.
  2. Batería descargada o bornes sulfatados — `21.2628 %`.
  3. Falla en bombín o bomba hidráulica de embrague — `15.8145 %`.

### B. Consulta exacta que recibió el ML en WhatsApp

- Macro RAW: `MOTOR 99.4521 %`, `TRANSMISION 0.3667 %`,
  `SUSPENSION_CHASIS 0.1813 %`.
- Top 10 ML Nivel 2 RAW:
  1. Bomba de gasolina — `41.3382 %`
  2. Bujías/bobinas — `21.1627 %`
  3. Aceite de caja — `12.6475 %`
  4. Descarbonización GDI — `7.6872 %`
  5. Baja presión Common Rail — `5.7589 %`
  6. Faja/cadena de distribución — `3.5585 %`
  7. Inyectores/filtro — `3.2342 %`
  8. Sensor de oxígeno/mezcla rica — `3.1568 %`
  9. Consumo de aceite — `0.3785 %`
  10. VVT — `0.2692 %`
- Top 3 jerárquico: bomba de gasolina `56.2882 %`, bujías/bobinas `24.3749 %`,
  descarbonización GDI `6.8737 %`.

### C. Reglas posteriores y respuesta

La palabra heredada `misfire` activó la especialización de encendido y elevó bujías/bobinas a
`70 %`. La política de fusión asignó el diferencial restante a bomba de gasolina (`19.5 %`).
Compatibilidad no excluyó ninguna hipótesis.

- RAG query de entrada: la consulta contaminada mostrada arriba, con macro `MOTOR` y Top ML motor.
- RAG recuperado: procedimiento de presión/caudal de combustible bajo carga (`similitud 0.5216`).
- Top final: bujías/bobinas `70 %`; bomba de gasolina `19.5 %`.
- Respuesta final: repitió esos dos porcentajes y la prueba de chispa del turno anterior.

## 4. Auditoría de reutilización

- **Caché:** `MISS` por evidencia determinista. La clave anterior fue
  `29445991...504c`; la del incidente `21d3af1b...3c2`. La API se reinició 48 segundos
  antes del incidente, por lo que su caché estaba nueva. `desde_cache` no se persistió.
- **Respuesta anterior:** no fue copiada por caché. La coincidencia 70/20 se reprodujo por
  la consulta contaminada, el token `misfire` y la política de fusión.
- **Persistencia:** mensaje de entrada y salida sí existen; no existe una fila nueva en
  `diagnosticos`, `trabajos_gemini` ni `auditoria` para este turno. Es una brecha de trazabilidad.
- **Worker:** no intervino en esta respuesta; la salida se produjo en `0.76 s` por la API síncrona.

## 5. Runtime

- API: confirmado en vivo y por hora de inicio: `APP_VERSION 9.11.0`,
  `ORCHESTRATOR_VERSION 9.11.0`, `CODE_BUILD_ID 9b6fedc24bb51ec1`, PID `6116`,
  inicio `2026-09-17 04:03:14+00:00`.
- Worker: PID `26988`, inicio `2026-09-17 03:23:19+00:00`, heartbeat activo durante el
  incidente. Inició después de escribirse el código 9.11. No obstante, la tabla de workers
  no persiste versión/build; por ello su build histórico se considera **evidencia fuerte pero
  no confirmación retrospectiva criptográfica**.

## 6. Corrección aplicada después de identificar la divergencia

1. `estado_operativo` continúa siendo `MARCHA`; el dominio se evalúa independientemente como
   `TRANSMISION`.
2. Se amplió la detección conceptual de transmisión y climatización sin depender solo de
   `D`, `R` o `reversa`.
3. Un marcador de nueva queja principal tiene prioridad sobre conectores internos.
4. Solo `además`, `también`, `junto con` y equivalentes inequívocos mantienen síntomas relacionados.
5. El extractor registra `reversa demora en enganchar`, `reversa entra con golpe` y
   `condicion_operacion=al seleccionar reversa`.
6. Se versionó la corrección como `APP_VERSION 9.12.0`, `ORCHESTRATOR_VERSION 9.12.0`,
   `CODE_BUILD_ID dfc3c025481865db`. El build ahora incorpora el contenido completo de
   `models.py`, `orquestador_conversacion.py`, `segmentador_casos.py` y `extractor_hechos.py`.

Consulta resultante en la reproducción seca:

```text
a Gasolina. presenta reversa demora en enganchar, reversa entra con golpe, ruido anómalo.
cuando está al seleccionar reversa.
```

Esta consulta produce macro `TRANSMISION 64.4780 %` y Top 1 `Falta o degradación de aceite de
caja de cambios 95.2740 %`. Es una hipótesis preliminar, no una confirmación física.

La API recargó como Fase 9.12 (PID `22816`). El worker 9.11 fue detenido y sustituido por el
worker PID `26240`, iniciado a `2026-09-17 04:21:41+00:00`, con heartbeat activo y el mismo
código 9.12. La base todavía no guarda versión/build en `workers_sistema`; esa limitación de
auditoría permanece documentada.

## 7. Regresión e inmutabilidad

- Regresiones agregadas: MOTOR→TRANSMISIÓN, TRANSMISIÓN→MOTOR, FRENOS→SUSPENSIÓN,
  ELÉCTRICO→CLIMATIZACIÓN y controles de síntomas relacionados en un mismo caso.
- Ruff: sin errores.
- Suite conversacional Fases 9.5–9.12: **74 passed**.
- Manifiesto canónico Fase 8.3: **19/19 hashes coincidentes**.
- El manifiesto no fue regenerado ni sobrescrito.

## 8. Resultado

```text
RAW → dominio TRANSMISION
segmentación defectuosa → MANTENER_CASO
case_id reutilizado → hechos MOTOR heredados
consulta ML contaminada → macro MOTOR
regla misfire + fusión → 70 % / 19.5 %
respuesta → prueba de chispa incorrecta para la nueva queja
```

**Causa raíz:** segmentación cross-system basada en un conector demasiado amplio, seguida por
extracción insuficiente de hechos de transmisión. **No fue un fallo primario del ML congelado.**
