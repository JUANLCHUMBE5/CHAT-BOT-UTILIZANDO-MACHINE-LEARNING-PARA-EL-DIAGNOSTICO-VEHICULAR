# Proyecto: administración profesional de CarBot

Estado: completado y validado el 15 de agosto de 2026.

La descripción funcional completa está en
[`docs/ESTADO_FINAL_CARBOT.md`](docs/ESTADO_FINAL_CARBOT.md) y el registro de la
revisión en
[`docs/REGISTRO_CAMBIOS_2026-08-15.md`](docs/REGISTRO_CAMBIOS_2026-08-15.md).

## Funcionalidad de perfiles y permisos

- `PUT /api/v1/mecanicos/{mecanico_id}` actualiza nombre, teléfono y, solamente
  para cuentas administrativas, contraseña.
- El cambio de teléfono recalcula HMAC, conserva los últimos cuatro dígitos y
  vuelve a cifrar el destinatario necesario para WhatsApp.
- Se detectan colisiones de teléfono mediante HTTP 409.
- Las contraseñas administrativas exigen 12 caracteres, mayúscula, minúscula y
  número, y se almacenan con PBKDF2-HMAC-SHA256.
- Cada edición registra auditoría de campos modificados sin guardar secretos.
- Solo administradores pueden editar administradores o conceder ese rol.
- El último administrador activo no puede bloquearse, desactivarse ni degradarse.
- Los mecánicos no reciben contraseña ni acceso al panel; trabajan por WhatsApp.
- El modal de edición incluye validación inmediata, carga, confirmación y
  mensajes de éxito o error integrados.

## Componentes principales

- Backend: `backend/src/interfaces/api/v1/endpoints/mecanicos.py`.
- Repositorio: `backend/src/infrastructure/database/repositories/usuario_repository.py`.
- Frontend: `frontend/src/components/views/personas/EquipoTallerTab.tsx`.
- Cliente HTTP: `frontend/src/services/api.ts`.
- Contratos: `frontend/src/types/api.ts` y `frontend/src/types/domain.ts`.
- Pruebas backend: `backend/tests/test_mecanicos_profile_edit.py`.
- Arnés frontend: `frontend/test_profile_edit_harness.js`.

## Resultado

La administración de perfiles, jerarquías, privacidad de números y trazabilidad
está implementada. La política definitiva separa las credenciales del panel de
la autorización técnica de WhatsApp.
