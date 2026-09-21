import type {
  CasoValidacionDTO,
  CrearCasoValidacionDTO,
  MetricasValidacionDTO,
} from '../../types';
import {
  API_BASE_URL,
  authFetch,
  getAuthHeaders,
  extractErrorMessage,
} from './client';

export async function getCasosValidacion(params?: {
  fecha_desde?: string;
  fecha_hasta?: string;
  fase?: string;
  tipo_registro?: string;
  estado_registro?: string;
  marca?: string;
  acierto?: number;
  busqueda?: string;
  skip?: number;
  limit?: number;
}): Promise<{ total: number; skip: number; limit: number; casos: CasoValidacionDTO[] }> {
  const url = new URL(`${API_BASE_URL}/validacion-taller`);
  if (params?.fecha_desde) url.searchParams.set('fecha_desde', params.fecha_desde);
  if (params?.fecha_hasta) url.searchParams.set('fecha_hasta', params.fecha_hasta);
  if (params?.fase) url.searchParams.append('fase', params.fase);
  if (params?.tipo_registro) url.searchParams.append('tipo_registro', params.tipo_registro);
  if (params?.estado_registro) url.searchParams.append('estado_registro', params.estado_registro);
  if (params?.marca) url.searchParams.append('marca', params.marca);
  if (params?.acierto !== undefined) url.searchParams.append('acierto', String(params.acierto));
  if (params?.busqueda) url.searchParams.append('busqueda', params.busqueda);
  if (params?.skip !== undefined) url.searchParams.append('skip', String(params.skip));
  if (params?.limit !== undefined) url.searchParams.append('limit', String(params.limit));

  const res = await authFetch(url.toString(), {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error al obtener casos de validación de taller'));
  }
  return (await res.json()) as { total: number; skip: number; limit: number; casos: CasoValidacionDTO[] };
}

export async function getMetricasValidacion(
  periodo: { fecha_desde?: string; fecha_hasta?: string } = {},
): Promise<MetricasValidacionDTO> {
  const url = new URL(`${API_BASE_URL}/validacion-taller/metricas`);
  for (const [key, value] of Object.entries(periodo)) if (value) url.searchParams.set(key, value);
  const res = await authFetch(url.toString(), {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error al obtener métricas de validación'));
  }
  return (await res.json()) as MetricasValidacionDTO;
}

export async function crearCasoValidacion(dto: CrearCasoValidacionDTO): Promise<CasoValidacionDTO> {
  const { chatbot_prediccion: prediccion_inicial, ...datos } = dto;
  const res = await authFetch(`${API_BASE_URL}/validacion-taller`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ...datos, prediccion_inicial }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error al registrar caso de validación'));
  }
  return (await res.json()) as CasoValidacionDTO;
}

export function getExportarTrackerCsvUrl(): string {
  return `${API_BASE_URL}/validacion-taller/exportar-csv`;
}

export async function descargarValidacionCsv(periodo: { fecha_desde?: string; fecha_hasta?: string }): Promise<void> {
  const url = new URL(getExportarTrackerCsvUrl());
  for (const [key, value] of Object.entries(periodo)) if (value) url.searchParams.set(key, value);
  const res = await authFetch(url.toString(), { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(await extractErrorMessage(res, 'No se pudo exportar el período'));
  const href = URL.createObjectURL(await res.blob());
  const link = document.createElement('a');
  link.href = href;
  link.download = 'validacion-carbot.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}

export function getExportarFichasAnexo2CsvUrl(): string {
  return `${API_BASE_URL}/validacion-taller/exportar-fichas-anexo2-csv`;
}

export async function descargarFichasAnexo2Csv(periodo: { fecha_desde?: string; fecha_hasta?: string }): Promise<void> {
  const url = new URL(getExportarFichasAnexo2CsvUrl());
  for (const [key, value] of Object.entries(periodo)) if (value) url.searchParams.set(key, value);
  const res = await authFetch(url.toString(), { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(await extractErrorMessage(res, 'No se pudo exportar el Anexo 2 oficial'));
  const href = URL.createObjectURL(await res.blob());
  const link = document.createElement('a');
  link.href = href;
  link.download = `anexo2_fichas_oficiales_taller_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}
