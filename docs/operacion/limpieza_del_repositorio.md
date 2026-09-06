# Limpieza del repositorio antes del despliegue

Se conserva `docs/` como carpeta principal de documentación. Los archivos raíz
`README.md`, `AGENTS.md`, `CONTRIBUTING.md` y `SECURITY.md` permanecen en sus rutas
convencionales porque orientan a desarrolladores y herramientas.

## Qué se conserva

- `backend/`, `frontend/`, `machine_learning/`: código, pruebas y recursos del sistema.
- `infrastructure/`, `scripts/`, `.github/`: despliegue, automatizaciones y CI.
- `.venv/`, `frontend/node_modules/`: dependencias locales necesarias; no se distribuyen en Docker.
- `frontend/dist/`: compilación web para distribución, no código sobrante.
- `.env`: configuración local; no se publica ni se incluye en la imagen.
- Datasets, corpus RAG y modelos: no se borran como parte de una limpieza de cachés.

## Temporales

`scripts/limpiar_temporales.ps1` muestra primero una vista previa. Para aplicar:

```powershell
./scripts/limpiar_temporales.ps1 -Aplicar
```

Solo retira `.codex_tmp`, `tmp` y cachés Python/Ruff/Pytest en ubicaciones
conocidas. No mueve archivos versionados ni enlaces. Los archivos se trasladan
a `CarBot-respaldos-limpieza` dentro de Documentos del usuario, fuera del proyecto.
Cada ejecución incluye un `manifiesto.json` con rutas originales y hashes SHA-256.
Para recuperar, consulte ese manifiesto y restaure únicamente los archivos
necesarios, sin sobrescribir versiones actuales.

Git y Docker excluyen estos temporales. Las capturas del harness visual se
generan en el directorio temporal del sistema operativo y su ubicación se
muestra al terminar. Las cachés pueden reaparecer durante el desarrollo;
no son una parte funcional adicional de la arquitectura.

## Ejecución del 5 de septiembre de 2026

- 37 carpetas temporales retiradas; 278 archivos respaldados y verificados.
- 93 archivos protegidos sin cambios, incluyendo `.env`, documentación,
  datasets, corpus y artefactos ML.
- Frontend: lint, compilación de producción y harness aprobados.
- Backend: 28 pruebas seleccionadas aprobadas; no es una validación integral del despliegue.

Esta limpieza **no convierte el Compose actual en un despliegue productivo**.
Actualmente declara `ENVIRONMENT: development`. Antes de publicar se debe
revisar configuración, HTTPS, secretos, exposición de PostgreSQL/Redis, backups
y el funcionamiento real WhatsApp → API → worker → respuesta. No se modificó
esa configuración ni se desplegó el sistema durante esta limpieza.
