# Ejecutar MANUALMENTE. No se ha desplegado esta release.

1. Construir fuera del VPS desde el SHA publicado (Linux amd64), con las etiquetas OCI:

```bash
SHA=$(git rev-parse HEAD)
docker buildx build --platform linux/amd64 -f backend/Dockerfile --label org.opencontainers.image.revision="$SHA" --label org.opencontainers.image.source=https://github.com/JUANLCHUMBE5/CHAT-BOT-UTILIZANDO-MACHINE-LEARNING-PARA-EL-DIAGNOSTICO-VEHICULAR --tag ghcr.io/juanlchumbe5/carbot-backend:$SHA --push .
```

Registrar el digest devuelto. No reutilizar los digests antiguos. Verificar etiqueta revision, arquitectura y arranque aislado de esta imagen antes de continuar. Los 1445 tests corresponden al código validado; no acreditan una imagen nueva todavía no construida.

2. En VPS: mantener TODOS los archivos Compose actuales y el mismo proyecto carbot-backend. Capturar imágenes actuales API y worker con docker inspect; guardar un overlay rollback con esas referencias inmutables y los montajes actuales. No bajar ni recrear PostgreSQL/Redis/frontend/ngrok. No copiar .env.

3. Backup consistente antes de cambios (en el directorio /opt/carbot/carbot-backend, usando el stack existente):

```bash
umask 077
BACKUP=/opt/carbot/backups/pre-main-$(date -u +%Y%m%dT%H%M%SZ).dump
docker exec carbot-backend-postgres-1 sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BACKUP"
test -s "$BACKUP" && sha256sum "$BACKUP"
docker exec -i carbot-backend-postgres-1 pg_restore -l < "$BACKUP" > /dev/null
```

El índice legible no demuestra restaurabilidad: restaurar copia en PostgreSQL16 aislado antes de aprobar. No transferir datos sin cifrado/destino autorizado.

4. Descargar IMAGE=ghcr.io/juanlchumbe5/carbot-backend@sha256:DIGEST_VERIFICADO. Extraer /app/machine_learning de un contenedor detenido de esa imagen a un directorio NUEVO de release; comprobar hashes contra manifiestos. No sobrescribir corpus/modelos productivos anteriores. Overlay api/worker: image=$IMAGE, build: !reset null, command Uvicorn/python -m src.application.jobs.worker, ML_ROOT=/app/machine_learning. Usar volumes: !override manteniendo /opt/carbot/tracker-data:/app/tracker-data y montando el NUEVO paquete ML:/app/machine_learning:ro. Conservar restantes variables, puertos y redes actuales. Validar composición con docker compose config --quiet. No imprimir configuración interpolada.

5. Definir DC con TODOS los Compose existentes indicados por las etiquetas del contenedor más el overlay nuevo. No usar solo el Compose del monorepo: cambiaría los nombres/montajes productivos. Comprobar revisión actual (solo lectura):

```bash
"${DC[@]}" run --rm --no-deps --entrypoint python api -m alembic current
"${DC[@]}" run --rm --no-deps --entrypoint python api -m alembic heads
```

Esta release espera head 20261014_01. Si ya está en head, no migrar. Si está en 20261010_01, aplicar únicamente tras backup restaurado y ventana autorizada:

```bash
"${DC[@]}" run --rm --no-deps --entrypoint python api -m alembic upgrade 20261014_01
"${DC[@]}" up -d --no-deps --no-build api worker
curl --fail --max-time 20 http://127.0.0.1:8000/health/live
curl --fail --max-time 20 http://127.0.0.1:8000/health/ready
```

6. Verificar digest real de ambos contenedores, carga SVM/RAG, jobs, memoria/RAM, acceso frontend y webhook sin enviar WhatsApp ni alterar casos. Si falla: aplicar overlay rollback guardado y up -d --no-deps --no-build api worker. No downgrade ni restauración automática DB. Conservar volúmenes y backups.

BLOQUEO deliberado: no ejecutar pasos 4-6 hasta registrar digest NUEVO, comprobar imagen y validar overlay contra la configuración vigente. El VPS sigue con versión anterior y montaje ML anterior. No está actualizado.
