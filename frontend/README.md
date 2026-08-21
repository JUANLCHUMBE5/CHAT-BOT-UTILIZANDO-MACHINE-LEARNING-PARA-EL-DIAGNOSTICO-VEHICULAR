# Frontend administrativo

Panel web de CarBot construido con React, TypeScript y Vite. Su uso está
restringido a administradores; los mecánicos trabajan mediante WhatsApp.

## Organización

- `src/components/common/`: componentes reutilizables.
- `src/components/layout/`: estructura visual y navegación.
- `src/components/views/`: pantallas funcionales.
- `src/hooks/`: carga y estado por dominio.
- `src/services/`: cliente de la API REST.
- `src/types/`: contratos y tipos TypeScript.
- `src/utils/`: navegación, errores y utilidades puras.
- `tests/harness/`: comprobaciones ligeras de contratos y permisos.

## Comandos

```powershell
npm run dev
npm run verify
npm run preview
```

En desarrollo, Vite redirige `/api` hacia `http://127.0.0.1:8000`. Para otros
entornos se utiliza `VITE_API_BASE_URL`, documentada en `.env.example`.
