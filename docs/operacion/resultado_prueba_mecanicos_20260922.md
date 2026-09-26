# Sondeo funcional ML + RAG + LLM — 22/09/2026

Diez consultas sintéticas escritas como mecánico, con expectativas definidas antes de ejecutar. Varias incluyen hallazgos físicos explícitos, por lo que constituyen un sondeo relativamente favorable, no un benchmark ciego ni validación en taller. No se comprobó su independencia del entrenamiento.

Se ejecutó `GestorDiagnostico.procesar_consulta_texto` con modelos, RAG y Gemini reales. No se ejecutó el webhook, el envío de WhatsApp, la cola externa ni el orquestador conversacional completo. PostgreSQL y escritura del tracker se deshabilitaron en este proceso de prueba. No se alteraron datos oficiales ni artefactos ML/RAG. El uso de Gemini consume la cuota configurada.

## Resultados

| Caso | Hipótesis principal | Evaluación por familia |
|---|---|---|
| Vibración al frenar, alabeo medido | Discos alabeados | Compatible |
| Misfire que cambia al intercambiar bobina | Bujías/bobinas | Compatible |
| Testigo de batería, tensión baja en marcha | Alternador | Compatible |
| Clics de arranque y caída de tensión | Solicita aclaración | Pendiente |
| RPM suben sin aumentar velocidad, caja manual | Embrague | Compatible |
| Calienta detenido, ventilador no gira | Termostato/motoventilador | Compatible por familia |
| Golpeteo en baches, rótula con juego y buje roto | Llantas desbalanceadas/desalineadas | Prioridad incorrecta |
| Tac-tac al girar, guardapolvo roto | Homocinéticas | Compatible |
| A/C no enfría, fuga y baja presión | Compresor/fuga de gas | Compatible por familia |
| Automático demora en R y entra con golpe | Cuerpo de aceleración/IAC | Prioridad incompatible |

- Primera hipótesis compatible: 7/10 (70%). Dos prioridades incorrectas y una aclaración pendiente.
- La familia esperada aparece en las tres alternativas de 10/10, incluyendo la aclaración. Este criterio amplio NO significa 100% de exactitud de pieza ni de diagnóstico final.
- ML + RAG + Gemini completaron 9/10 casos. El caso de arranque quedó en aclaración, sin RAG/LLM.
- Los nueve resultados completos tardaron aproximadamente 3–5 segundos en este proceso local; no son tiempos de entrega WhatsApp.

## Hallazgos

1. Transmisión: primera hipótesis IAC 41.98%, aceite de caja 37.7%, batería 20.3%. RAG recuperó cuerpo de aceleración. Gemini reconoció mejor concordancia de transmisión, pero conservó la hipótesis incompatible y describió limpieza de admisión. La coherencia entre clasificación, documento y recomendación no está garantizada.
2. Suspensión: prioriza llantas aunque el texto explicita holgura de rótula y buje roto. Gemini reconoce la contradicción, pero mezcla procedimientos de alineación.
3. Especificaciones: aparecen torques y tolerancias sin marca/modelo/año confirmado. Recuperar un texto no demuestra aplicabilidad OEM al vehículo consultado.
4. Respuestas del procesador de 2,929–4,245 caracteres en los casos completos. No se verificó aquí la compactación posterior del canal WhatsApp.
5. El caso de arranque pide una opción que ya está descrita en el mensaje: posible aclaración redundante a contrastar en el orquestador WhatsApp.

## Decisión

No se alcanzó la meta de 80% en primera respuesta en este sondeo. Tampoco se acreditó precisión de campo. Antes de producción deben auditarse las prioridades y compatibilidad RAG, controlar especificaciones por vehículo y probar conversaciones completas. No se reentrenó ni corrigió el modelo a partir de estos resultados.

Evidencia completa: `prueba_mecanicos_20260922.json`. Ejecutor: `scripts/prueba_mecanicos_20260922.py`.
