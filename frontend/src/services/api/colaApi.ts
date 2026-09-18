import {
  API_BASE_URL,
  authFetch,
  getAuthHeaders,
  extractErrorMessage,
} from './client';

export async function getHealthReady(): Promise<{
  status: 'ready' | 'not_ready' | 'offline';
  componentes?: {
    postgresql?: boolean;
    worker_gemini_iniciado?: boolean;
    gemini_disponible?: boolean;
    gemini_estado?: 'sin_api_key' | 'no_verificado' | 'disponible' | 'degradado' | 'degradado_sin_cuota';
    gemini_ultima_verificacion?: string | null;
    gemini_ultimo_exito?: string | null;
    gemini_ultimo_codigo_http?: number | null;
    gemini_ultimo_error?: string | null;
    modelo_ml?: boolean;
    rag?: boolean;
  };
}> {
  try {
    const rootOrigin = API_BASE_URL.replace(/\/api\/v1\/?$/, '');
    const res = await fetch(`${rootOrigin}/health/ready`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (res.status === 200) {
      const data = await res.json().catch(() => ({ status: 'ready' }));
      return { status: 'ready', componentes: data.componentes };
    } else if (res.status === 503) {
      const data = await res.json().catch(() => ({ status: 'not_ready' }));
      return { status: 'not_ready', componentes: data.componentes };
    }
    return { status: 'not_ready' };
  } catch {
    return { status: 'offline' };
  }
}

export async function getTrabajosFallidos(
  limite: number = 20,
): Promise<Array<{ id: string; tipo: string; payload: Record<string, unknown>; error?: string; reintentos: number; creado_en: string }>> {
  const res = await authFetch(`${API_BASE_URL}/metricas/trabajos/fallidos?limite=${limite}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    return [];
  }
  return (await res.json()) as Array<{ id: string; tipo: string; payload: Record<string, unknown>; error?: string; reintentos: number; creado_en: string }>;
}

export async function reintentarTrabajoFallido(trabajoId: string): Promise<{ status: string; trabajo_id: string }> {
  const res = await authFetch(`${API_BASE_URL}/metricas/trabajos/${trabajoId}/reintentar`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error al reintentar trabajo fallido'));
  }
  return (await res.json()) as { status: string; trabajo_id: string };
}
