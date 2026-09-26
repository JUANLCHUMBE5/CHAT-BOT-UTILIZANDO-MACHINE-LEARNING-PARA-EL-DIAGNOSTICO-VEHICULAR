# Despliegue de backend con el repositorio ML separado

Este repositorio requiere el directorio `machine_learning` del repositorio
`carbot-machine-learning`. Los artefactos de modelo y el corpus RAG se montan
en modo solo lectura; no se copian dentro de la imagen del backend.

En el servidor, deje ambos repositorios como directorios hermanos:

```text
/opt/carbot/
  carbot-backend/
  carbot-machine-learning/
```

Desde `carbot-backend`, copie `.env.production.example` a `.env`, complete los
secretos de producción y confirme que `ML_HOST_PATH` apunta al directorio
hermano. Después ejecute:

```bash
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml ps
curl http://127.0.0.1:8000/health/live
```

El puerto 8000 queda limitado a `127.0.0.1`. Publique HTTPS mediante un proxy
inverso (por ejemplo Caddy o Nginx) antes de configurar el webhook de WhatsApp.
Nunca suba el archivo `.env` ni las claves del proveedor al repositorio.
