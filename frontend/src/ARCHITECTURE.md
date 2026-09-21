# Arquitectura del frontend

El frontend adopta una organización **modular por funcionalidades**:

- `features/`: expone cada capacidad funcional de la aplicación (autenticación,
  panel, gestión y proyecto).
- `shared/`: expone infraestructura reutilizable sin lógica propia de una
  funcionalidad (API, layout, navegación y tipos comunes).
- `components/`, `hooks/`, `services/` y `utils/`: conservan temporalmente la
  implementación existente para asegurar una migración compatible.

Los nuevos consumidores deben importar desde `features/*` o `shared/*`. Las
rutas anteriores se mantienen mientras sus implementaciones se trasladan en
fases pequeñas y verificables.

Las operaciones nuevas se agrupan por funcionalidad (`features/*/api`). El
cliente histórico `services/api.ts` conserva el transporte común y la
compatibilidad mientras cada dominio se extrae. Los hooks consumen estas APIs
de funcionalidad, evitando acoplar la interfaz directamente al transporte.

La sesión persistida contiene solo información visual del usuario. El access
token vive en memoria y el refresh token pertenece a una cookie `HttpOnly` que
JavaScript no puede leer.
