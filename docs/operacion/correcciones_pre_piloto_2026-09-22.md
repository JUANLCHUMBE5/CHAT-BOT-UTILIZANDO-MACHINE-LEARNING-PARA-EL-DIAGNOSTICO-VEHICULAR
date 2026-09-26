# Correcciones previas al piloto — 22 de septiembre de 2026

## Cambios

- El orquestador comprueba que el gestor de sesión exista antes de cargar contexto o finalizar un caso.
- Se completó el simulador de diagnóstico de la regresión 9.15. La prueba de Plan B controla explícitamente la suficiencia; una prueba adicional ejercita la decisión real de diagnóstico sin gestor de sesión.
- `/health/ready` exige un heartbeat reciente del worker de sistema cuando PostgreSQL está habilitado. Conserva `/health/live` como prueba de vida para evitar bloquear el arranque del worker en Compose, que depende de la API.
- API y worker de Compose respetan `ENVIRONMENT`; desarrollo sigue siendo el valor por defecto. Para producción debe establecerse `ENVIRONMENT=production` y superar las validaciones de seguridad existentes.
- Se corrigieron el import de Decimal, importaciones de pruebas y dos advertencias del frontend.

## Alcance operativo

## Validación ejecutada

- 34 pruebas: aislamiento motor/transmisión, compatibilidad de preguntas, continuidad, colas, seguridad HTTP y disponibilidad del worker.
- 97 pruebas adicionales: paridad WhatsApp, respuestas contextuales, integridad conversacional, coherencia operativa, Plan B, negaciones, seguridad y salud de Gemini.
- Total seleccionado: 131 aprobadas. No equivale a la suite completa ni a una prueba física de WhatsApp. Persisten advertencias de dependencias en pytest.
- Ruff: sin errores en `src`, `tests` y `main.py`.
- Frontend: `npm run verify` aprobado, sin advertencias de lint.
- `docker compose config --quiet` y `git diff --check`: aprobados.

## Pendiente operativo

Estos cambios no acreditan entrega física en WhatsApp, disponibilidad permanente ni exactitud diagnóstica en taller. El heartbeat acredita actividad del worker de sistema; no prueba una llamada exitosa a Meta o Gemini ni garantiza el éxito de cada trabajo.

Antes de desplegar: configurar HTTPS, hosts y orígenes explícitos, secretos, almacenamiento compartido y respaldo. Revisar exposición de los puertos de PostgreSQL y Redis. Verificar texto, audio, cambio de caso y respuesta degradada con usuarios autorizados en modo PILOTO.

No se modificaron modelos, datasets, calibración, corpus RAG ni FAISS. No se reiniciaron procesos ni se publicó el cambio.
