import type { Diagnostico, ResumenMetricas, MetricasCola } from '../../types';
import {
  API_BASE_URL,
  authFetch,
  getAuthHeaders,
  extractErrorMessage,
} from './client';

export async function getResumenMetricas(
  fechaInicio?: string,
  fechaFin?: string,
  todo = false,
): Promise<ResumenMetricas> {
  const url = new URL(`${API_BASE_URL}/metricas/resumen`);
  if (fechaInicio) url.searchParams.append('fecha_inicio', fechaInicio);
  if (fechaFin) url.searchParams.append('fecha_fin', fechaFin);
  if (todo) url.searchParams.set('todo', 'true');

  const res = await authFetch(url.toString(), {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error consultando métricas en PostgreSQL'));
  }
  return (await res.json()) as ResumenMetricas;
}

export async function getMetricasColas(): Promise<MetricasCola> {
  const res = await authFetch(`${API_BASE_URL}/metricas/colas`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error consultando el estado de las colas'));
  }
  return (await res.json()) as MetricasCola;
}

export async function getDiagnosticos(params?: {
  busqueda?: string;
  estado?: string;
  modo?: string;
  mecanico_id?: string;
  limite?: number;
  offset?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
}): Promise<{ items: Diagnostico[]; total: number }> {
  const url = new URL(`${API_BASE_URL}/diagnostico/historial`);
  if (params) {
    if (params.busqueda) url.searchParams.append('busqueda', params.busqueda);
    if (params.estado) url.searchParams.append('estado', params.estado);
    if (params.modo) url.searchParams.append('modo', params.modo);
    if (params.mecanico_id) url.searchParams.append('mecanico_id', params.mecanico_id);
    if (params.limite !== undefined) url.searchParams.append('limite', params.limite.toString());
    if (params.offset !== undefined) url.searchParams.append('offset', params.offset.toString());
    if (params.fecha_desde) url.searchParams.append('fecha_desde', params.fecha_desde);
    if (params.fecha_hasta) url.searchParams.append('fecha_hasta', params.fecha_hasta);
  }

  const res = await authFetch(url.toString(), {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error consultando diagnósticos en PostgreSQL'));
  }
  const items = (await res.json()) as Diagnostico[];
  const totalHeader = Number(res.headers.get('X-Total-Count'));
  return {
    items,
    total: Number.isFinite(totalHeader) ? totalHeader : items.length,
  };
}

export async function getConversacionDiagnostico(diagnosticoId: string): Promise<import('../../types').MensajeConversacion[]> {
  const res = await authFetch(`${API_BASE_URL}/diagnostico/${diagnosticoId}/conversacion`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error consultando conversación del diagnóstico'));
  }
  return (await res.json()) as import('../../types').MensajeConversacion[];
}

export async function getHistorialVehiculoPorPlaca(placa: string): Promise<{ placa: string; vehiculo_id?: string; diagnosticos: Diagnostico[] }> {
  const res = await authFetch(`${API_BASE_URL}/diagnostico/vehiculos/${encodeURIComponent(placa)}/historial`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(await extractErrorMessage(res, 'No se pudo consultar el historial del vehículo'));
  return (await res.json()) as { placa: string; vehiculo_id?: string; diagnosticos: Diagnostico[] };
}
