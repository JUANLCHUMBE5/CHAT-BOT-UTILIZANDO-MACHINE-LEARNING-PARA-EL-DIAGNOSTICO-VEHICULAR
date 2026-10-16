# Harness integral local

Desde la raíz del monorepositorio, con Docker Desktop Linux y las dependencias frontend existentes:

```powershell
.\scripts\ejecutar-harness-integral.ps1
```

El comando construye imágenes de pruebas locales, crea un proyecto/subred nuevos, congela el backend y frontend del checkout y ejecuta Pytest con cobertura, Ruff, frontend verify, cinco contratos ML, los 80 turnos originales, reinicios de API/worker/Redis/PostgreSQL y diez turnos Yaris ABC123/Sentra XYZ789. Conserva logs y XML en `outputs/harness/<fecha>/`. Falla si alguna etapa falla.

Para reutilizar imágenes locales ya preparadas, configurar `CARBOT_HARNESS_RUNTIME_IMAGE`, `CARBOT_HARNESS_TEST_IMAGE` y ejecutar con `-SkipBuild`. La validación de esta implementación reutiliza las imágenes existentes; no equivale a probar una nueva imagen productiva.

La URL loopback y el nombre del proyecto aparecen al finalizar y en `summary.json`. La web muestra respuestas persistidas, estado, case_id, resultados y cobertura. Nginx solo publica en 127.0.0.1; API/worker/laboratorio permanecen en red interna sin salida. El laboratorio es una aplicación separada; no se registra en main.py y rechaza entornos productivos, dotenv habilitado, credenciales externas y conexiones a bases ajenas.

RAG se monta desde los bytes Git verificados, evitando la conversión CRLF del checkout Windows. No se cambia el índice, corpus original ni hashes esperados. SVM se carga sin reentrenar.

Los datos son sintéticos DEVELOPMENT. No representan validación clínica, validación OEM, LLM real ni resultados oficiales de tesis. Los harness Node y las comprobaciones HTTP no sustituyen automatización de un navegador.

Se conservan contenedores/evidencias. No se ejecuta prune, borrado de volúmenes, push ni despliegue. La infraestructura fallará de forma explícita si falta Docker, Node, el entorno Python local o alguna dependencia ya declarada.

## Laboratorio de la API y fixture numérico

La UI React usa `/api/v1/laboratorio`, distinto del proceso aislado `/lab` de este harness.
El primero requiere `ENABLE_LABORATORY=true`, entorno local/development/test,
`CARBOT_BLOCK_DOTENV=true`, ninguna credencial Gemini/Groq, conexión/origen loopback
y JWT administrativo válido. Producción siempre devuelve 403, aunque el flag esté activo.
Su memoria se separa por taller/usuario autenticado; no escribe fichas oficiales.
No habilitarlo en configuraciones productivas ni usarlo a través de un proxy público.

`caso_22_opcion_la_2` comprueba una selección contextual con varias alternativas.
La entrada antigua de sobrecalentamiento puede producir una única hipótesis y una
intercepción de seguridad: aceptar «la 2» ahí sería un error. La entrada genérica
no cambia el contrato térmico: `test_thermal_coverage_independent_of_numeric_fixture`
verifica la advertencia del radiador a 108 grados por separado, y las regresiones
Codex conservan el rechazo de opciones inexistentes. No se relajan esas expectativas.
