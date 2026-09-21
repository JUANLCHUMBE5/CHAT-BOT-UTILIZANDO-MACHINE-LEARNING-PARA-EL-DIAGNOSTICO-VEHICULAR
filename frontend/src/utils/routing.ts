import type { UsuarioSesion } from '../types';

export type AppRoute =
  | '/login'
  | '/inicio'
  | '/gestion'
  | '/proyecto'
  | '/personas'
  | '/diagnosticos'
  | '/validacion'
  | '/fichas';

/**
 * Solo las cuentas administrativas pueden navegar por el panel web.
 */
export const getValidRoute = (path: string, user: UsuarioSesion | null): AppRoute => {
  if (!user || !['administrador', 'admin'].includes(user.rol)) return '/login';
  if (path === '/login' || path === '/' || path === '/resumen') return '/inicio';
  // Redirecciones unificadas a Gestión (Personas, Diagnósticos, Mecánicos, Solicitudes)
  if (['/gestion', '/personas', '/diagnosticos', '/mecanicos', '/clientes', '/solicitudes'].includes(path)) {
    return '/gestion';
  }
  // Módulo Proyecto CarBot (Tesis, Fichas, Modelo IA, Arquitectura)
  if (['/proyecto', '/tesis', '/modelo', '/arquitectura'].includes(path)) {
    return '/proyecto';
  }
  if (['/fichas', '/validacion'].includes(path)) {
    return '/inicio';
  }
  if (path === '/inicio') return '/inicio';
  return '/inicio';
};
