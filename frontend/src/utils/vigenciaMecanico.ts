import type { Mecanico } from '../types';

export interface VigenciaMecanicoInfo {
  estadoVisual: 'activo' | 'por_vencer' | 'vencido' | 'bloqueado' | 'inactivo';
  etiquetaEstado: string;
  badgeStyle: { bg: string; color: string; border: string };
  diasRestantes: number;
  fechaExpiracionStr: string;
}

/**
 * Regla de vigencia de acceso técnico para mecánicos de taller:
 * - Se asume una vigencia estándar de 90 días naturales desde la fecha de registro o última actualización.
 * - Si el usuario está bloqueado: Estado 'BLOQUEADO' (Prioridad máxima de seguridad).
 * - Si el usuario no está activo: Estado 'INACTIVO'.
 * - Si los días restantes <= 0: Estado 'VENCIDO'. Evita mostrar 'ACTIVO + 0 días'.
 * - Si los días restantes están entre 1 y 15: Estado 'POR VENCER'.
 * - Si los días restantes > 15: Estado 'ACTIVO'.
 */
export function calcularVigenciaMecanico(m: Mecanico): VigenciaMecanicoInfo {
  const baseDateStr = m.fecha_registro || m.ultimo_acceso;
  const baseDate = baseDateStr ? new Date(baseDateStr) : new Date();
  // 90 días naturales desde la fecha base
  const fechaExp = new Date(baseDate.getTime() + 90 * 24 * 60 * 60 * 1000);
  const hoy = new Date();
  const diffMs = fechaExp.getTime() - hoy.getTime();
  const diasRestantes = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  const fechaExpiracionStr = !isNaN(fechaExp.getTime())
    ? fechaExp.toLocaleDateString('es-PE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      })
    : 'No definida';

  if (m.bloqueado) {
    return {
      estadoVisual: 'bloqueado',
      etiquetaEstado: 'BLOQUEADO',
      badgeStyle: { bg: '#fee2e2', color: '#b91c1c', border: '#fca5a5' },
      diasRestantes: Math.max(0, diasRestantes),
      fechaExpiracionStr,
    };
  }

  if (!m.activo) {
    return {
      estadoVisual: 'inactivo',
      etiquetaEstado: 'INACTIVO',
      badgeStyle: { bg: '#f1f5f9', color: '#64748b', border: '#cbd5e1' },
      diasRestantes: Math.max(0, diasRestantes),
      fechaExpiracionStr,
    };
  }

  if (diasRestantes <= 0) {
    return {
      estadoVisual: 'vencido',
      etiquetaEstado: 'VENCIDO',
      badgeStyle: { bg: '#fef3c7', color: '#b45309', border: '#fcd34d' },
      diasRestantes: 0,
      fechaExpiracionStr,
    };
  }

  if (diasRestantes <= 15) {
    return {
      estadoVisual: 'por_vencer',
      etiquetaEstado: `POR VENCER (${diasRestantes}d)`,
      badgeStyle: { bg: '#fffbeb', color: '#d97706', border: '#fde68a' },
      diasRestantes,
      fechaExpiracionStr,
    };
  }

  return {
    estadoVisual: 'activo',
    etiquetaEstado: 'ACTIVO',
    badgeStyle: { bg: '#dcfce7', color: '#15803d', border: '#86efac' },
    diasRestantes,
    fechaExpiracionStr,
  };
}
