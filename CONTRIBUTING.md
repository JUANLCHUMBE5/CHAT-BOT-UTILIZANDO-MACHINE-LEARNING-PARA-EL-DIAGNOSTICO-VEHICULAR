# Contribuir a CarBot

## Preparación

1. Cree el entorno virtual en `.venv`.
2. Instale `backend/requirements-dev.txt`.
3. Ejecute `npm ci` dentro de `frontend/`.
4. Copie `.env.example` a `.env` y use únicamente credenciales locales.

## Convenciones

- Python: `snake_case` para variables y funciones; `PascalCase` para clases.
- TypeScript: `camelCase` dentro de la interfaz y `snake_case` solo en contratos JSON de la API.
- Variables de entorno: `UPPER_SNAKE_CASE` y documentadas en `.env.example`.
- No agregue secretos, modelos binarios, datos operativos ni archivos generados.
- Mantenga separados dominio, infraestructura e interfaces.

## Verificación antes de integrar

Desde PowerShell, ejecute:

```powershell
.\scripts\verificar_proyecto.ps1
```

Todo cambio debe pasar Ruff, Pytest, Oxlint y el build de TypeScript.
