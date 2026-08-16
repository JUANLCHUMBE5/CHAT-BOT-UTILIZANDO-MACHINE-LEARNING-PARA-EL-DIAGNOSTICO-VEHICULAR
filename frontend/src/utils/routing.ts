import type { UsuarioSesion } from '../types';

export type AppRoute = '/login' | '/inicio' | '/personas' | '/diagnosticos';

/**
 * Solo las cuentas administrativas pueden navegar por el panel web.
 */
export const getValidRoute = (path: string, user: UsuarioSesion | null): AppRoute => {
  if (!user || !['administrador', 'admin'].includes(user.rol)) return '/login';
  if (path === '/login' || path === '/' || path === '/resumen') return '/inicio';
  if (path === '/clientes' || path === '/mecanicos') return '/personas';
  if (['/inicio', '/personas', '/diagnosticos'].includes(path)) return path as AppRoute;
  return '/inicio';
};
