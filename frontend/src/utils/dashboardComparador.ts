/**
 * Utilidades matemáticas y de fechas para comparativas del Dashboard Operativo.
 * Trabaja en zona horaria America/Lima para coincidencia exacta con el taller.
 */

export type DashboardPreset = 'hoy' | '7dias' | 'esteMes' | 'custom';

export interface RangoFechas {
  inicio: string; // YYYY-MM-DD
  fin: string;    // YYYY-MM-DD
}

export interface PeriodosComparativa {
  actual: RangoFechas;
  anterior: RangoFechas | null;
  etiquetaActual: string;
  etiquetaAnterior: string;
}

export interface VariacionResultado {
  porcentaje: number;
  texto: string;
  positiva: boolean;
  neutra?: boolean;
}

const getFechaLima = (fecha: Date = new Date()): string => {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Lima',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(fecha);
};

const parsearFechaUtc = (fechaStr: string): Date => {
  return new Date(`${fechaStr}T12:00:00Z`);
};

const restarDias = (fechaStr: string, dias: number): string => {
  const d = parsearFechaUtc(fechaStr);
  d.setUTCDate(d.getUTCDate() - dias);
  return d.toISOString().slice(0, 10);
};

/**
 * Calcula los rangos de fechas exactos para el período actual y el anterior.
 */
export function obtenerPeriodosComparativa(
  preset: DashboardPreset,
  customInicio?: string,
  customFin?: string,
  referencia: Date = new Date()
): PeriodosComparativa {
  const hoy = getFechaLima(referencia);

  if (preset === 'hoy') {
    const ayer = restarDias(hoy, 1);
    return {
      actual: { inicio: hoy, fin: hoy },
      anterior: { inicio: ayer, fin: ayer },
      etiquetaActual: 'Hoy',
      etiquetaAnterior: 'Ayer',
    };
  }

  if (preset === '7dias') {
    const inicioActual = restarDias(hoy, 6);
    const finAnterior = restarDias(inicioActual, 1);
    const inicioAnterior = restarDias(finAnterior, 6);
    return {
      actual: { inicio: inicioActual, fin: hoy },
      anterior: { inicio: inicioAnterior, fin: finAnterior },
      etiquetaActual: 'Últimos 7 días',
      etiquetaAnterior: '7 días previos',
    };
  }

  if (preset === 'esteMes') {
    const [yearStr, monthStr, dayStr] = hoy.split('-');
    const anio = parseInt(yearStr, 10);
    const mes = parseInt(monthStr, 10); // 1-12
    const dia = parseInt(dayStr, 10);

    const inicioActual = `${yearStr}-${monthStr}-01`;

    // Mes anterior
    const mesAnt = mes === 1 ? 12 : mes - 1;
    const anioAnt = mes === 1 ? anio - 1 : anio;
    const mesAntStr = String(mesAnt).padStart(2, '0');
    const inicioAnterior = `${anioAnt}-${mesAntStr}-01`;

    // Último día del mes anterior para no desbordar
    const ultimoDiaMesAnt = new Date(Date.UTC(anioAnt, mesAnt, 0)).getUTCDate();
    const diaAnt = Math.min(dia, ultimoDiaMesAnt);
    const finAnterior = `${anioAnt}-${mesAntStr}-${String(diaAnt).padStart(2, '0')}`;

    return {
      actual: { inicio: inicioActual, fin: hoy },
      anterior: { inicio: inicioAnterior, fin: finAnterior },
      etiquetaActual: 'Este mes',
      etiquetaAnterior: 'Mes anterior (mismo corte)',
    };
  }

  // Custom range
  if (customInicio && customFin) {
    const dInicio = parsearFechaUtc(customInicio);
    const dFin = parsearFechaUtc(customFin);
    const diffMs = dFin.getTime() - dInicio.getTime();
    const dias = Math.max(1, Math.round(diffMs / (1000 * 60 * 60 * 24)) + 1);

    const finAnterior = restarDias(customInicio, 1);
    const inicioAnterior = restarDias(finAnterior, dias - 1);

    return {
      actual: { inicio: customInicio, fin: customFin },
      anterior: { inicio: inicioAnterior, fin: finAnterior },
      etiquetaActual: `${customInicio} a ${customFin}`,
      etiquetaAnterior: `${inicioAnterior} a ${finAnterior}`,
    };
  }

  // Fallback si no hay fechas custom
  return {
    actual: { inicio: hoy, fin: hoy },
    anterior: null,
    etiquetaActual: 'Personalizado',
    etiquetaAnterior: 'Sin período anterior',
  };
}

/**
 * Calcula la variación porcentual entre dos valores.
 * Para métricas donde un aumento es positivo (ej. vehículos atendidos, completados).
 */
export function calcularVariacion(
  actual: number,
  anterior: number | null | undefined
): VariacionResultado {
  if (anterior === null || anterior === undefined) {
    return { porcentaje: 0, texto: 'Sin período anterior', positiva: true, neutra: true };
  }
  if (anterior === 0 && actual === 0) {
    return { porcentaje: 0, texto: '0.0%', positiva: true, neutra: true };
  }
  if (anterior === 0 && actual > 0) {
    return { porcentaje: 100, texto: `+${actual} nuevos`, positiva: true };
  }
  if (anterior > 0 && actual === 0) {
    return { porcentaje: -100, texto: '-100%', positiva: false };
  }

  const diff = actual - anterior;
  const pct = (diff / anterior) * 100;
  const signo = pct >= 0 ? '+' : '';
  return {
    porcentaje: pct,
    texto: `${signo}${pct.toFixed(1)}%`,
    positiva: pct >= 0,
    neutra: Math.abs(pct) < 0.01,
  };
}

/**
 * Variación semántica para diagnósticos pendientes.
 * Si los pendientes disminuyen, es positivo (se atendió el trabajo acumulado).
 * Si aumentan, es advertencia.
 */
export function calcularVariacionPendientes(
  actual: number,
  anterior: number | null | undefined
): VariacionResultado {
  if (anterior === null || anterior === undefined) {
    return { porcentaje: 0, texto: 'Sin período anterior', positiva: true, neutra: true };
  }
  if (anterior === 0 && actual === 0) {
    return { porcentaje: 0, texto: 'Sin pendientes', positiva: true, neutra: true };
  }
  if (anterior === 0 && actual > 0) {
    return { porcentaje: 100, texto: `+${actual} acumulados`, positiva: false };
  }

  const diff = actual - anterior;
  const pct = (diff / anterior) * 100;
  const signo = pct >= 0 ? '+' : '';
  return {
    porcentaje: pct,
    texto: `${signo}${pct.toFixed(1)}%`,
    // Menos pendientes es positivo para el taller
    positiva: pct <= 0,
    neutra: Math.abs(pct) < 0.01,
  };
}
