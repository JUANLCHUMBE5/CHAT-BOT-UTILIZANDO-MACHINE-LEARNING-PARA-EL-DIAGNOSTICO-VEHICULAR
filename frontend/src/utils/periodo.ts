export interface Periodo { fecha_desde?: string; fecha_hasta?: string }

export function periodoDias(dias: number, ahora = new Date()): Periodo {
  const fin = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Lima', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(ahora);
  const inicio = new Date(`${fin}T12:00:00Z`);
  inicio.setUTCDate(inicio.getUTCDate() - dias + 1);
  return { fecha_desde: inicio.toISOString().slice(0, 10), fecha_hasta: fin };
}

export function limitesDiagnosticos(periodo: Periodo) {
  const fin = periodo.fecha_hasta ? new Date(`${periodo.fecha_hasta}T00:00:00-05:00`) : null;
  if (fin) fin.setUTCDate(fin.getUTCDate() + 1);
  return {
    fecha_desde: periodo.fecha_desde ? `${periodo.fecha_desde}T00:00:00-05:00` : undefined,
    fecha_hasta: fin?.toISOString(),
  };
}
