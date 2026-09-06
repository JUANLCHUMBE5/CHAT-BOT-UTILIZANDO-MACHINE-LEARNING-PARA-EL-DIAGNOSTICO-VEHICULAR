import type {
  AprobarSolicitudResponseDTO,
  CasoValidacionDTO,
  Cliente,
  CrearCasoValidacionDTO,
  Diagnostico,
  LoginRequestDTO,
  Mecanico,
  MecanicoCreateDTO,
  MecanicoResponseDTO,
  MecanicoUpdateDTO,
  MecanicoRol,
  MetricasValidacionDTO,
  MetricasCola,
  ResumenMetricas,
  SolicitudAcceso,
  TokenResponseDTO,
  UsuarioSesion,
} from '../types';

const API_ORIGIN_OR_BASE = ((import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const API_BASE_URL = API_ORIGIN_OR_BASE.endsWith('/api/v1')
  ? API_ORIGIN_OR_BASE
  : `${API_ORIGIN_OR_BASE}/api/v1`;

export const SESSION_UPDATED_EVENT = 'carbot:session-updated';
export const SESSION_EXPIRED_EVENT = 'carbot:session-expired';

let refreshInProgress: Promise<string> | null = null;
let accessTokenInMemory: string | null = null;

function readStoredSession(): UsuarioSesion | null {
  try {
    const raw = localStorage.getItem('carbot_session');
    return raw ? JSON.parse(raw) as UsuarioSesion : null;
  } catch {
    return null;
  }
}

function notifyExpiredSession(): void {
  accessTokenInMemory = null;
  localStorage.removeItem('carbot_session');
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

async function renewAccessToken(): Promise<string> {
  if (refreshInProgress) return refreshInProgress;

  refreshInProgress = (async () => {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    if (!response.ok) throw new Error('No se pudo renovar la sesión.');

    const tokens = await response.json() as TokenResponseDTO;
    accessTokenInMemory = tokens.access_token;
    const session = readStoredSession();
    if (session) {
      window.dispatchEvent(new CustomEvent<UsuarioSesion>(SESSION_UPDATED_EVENT, { detail: session }));
    }
    return tokens.access_token;
  })().catch((error: unknown) => {
    notifyExpiredSession();
    throw error;
  }).finally(() => {
    refreshInProgress = null;
  });

  return refreshInProgress;
}

async function authFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const execute = (accessToken?: string) => {
    const headers = new Headers(init.headers);
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    const token = accessToken || accessTokenInMemory;
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return fetch(input, { ...init, headers });
  };

  const response = await execute();
  if (response.status !== 401) return response;

  const renewedToken = await renewAccessToken();
  return execute(renewedToken);
}

export function getAuthHeaders(): Record<string, string> {
  if (accessTokenInMemory) {
    return {
      'Authorization': `Bearer ${accessTokenInMemory}`,
      'Content-Type': 'application/json',
    };
  }
  return { 'Content-Type': 'application/json' };
}

export function enmascararIdentificadorSensible(valor: string, tipo: 'placa' | 'telefono'): string {
  if (!valor) return '';
  if (tipo === 'placa') {
    const limpia = valor.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
    if (limpia.length >= 6) {
      return `${limpia.slice(0, 3)}-***`;
    }
    return '***-***';
  } else {
    const ultimos4 = valor.slice(-4);
    return `+51 *** *** ${ultimos4}`;
  }
}

async function extractErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const errorData = await res.json();
    if (typeof errorData?.detail === 'string') return errorData.detail;
    if (Array.isArray(errorData?.detail)) {
      return errorData.detail
        .map((e: unknown) => (typeof e === 'object' && e !== null && 'msg' in e ? String((e as { msg: unknown }).msg) : String(e)))
        .join(', ');
    }
    if (typeof errorData?.message === 'string') return errorData.message;
    return fallback;
  } catch {
    return fallback;
  }
}

class ApiService {
  setAccessToken(token: string | null): void {
    accessTokenInMemory = token;
  }

  async login(payload: LoginRequestDTO): Promise<TokenResponseDTO> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Credenciales inválidas'));
    }
    const tokens = await res.json() as TokenResponseDTO;
    accessTokenInMemory = tokens.access_token;
    return tokens;
  }

  async cambiarPassword(
    token: string,
    passwordActual: string,
    passwordNuevo: string,
  ): Promise<{ mensaje: string; access_token: string; refresh_token?: string }> {
    const res = await fetch(`${API_BASE_URL}/auth/cambiar-password`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        password_actual: passwordActual,
        password_nuevo: passwordNuevo,
      }),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo cambiar la contraseña'));
    }
    const tokens = await res.json() as { mensaje: string; access_token: string; refresh_token?: string };
    accessTokenInMemory = tokens.access_token;
    return tokens;
  }

  async logout(): Promise<void> {
    try {
      const headers = new Headers();
      if (accessTokenInMemory) headers.set('Authorization', `Bearer ${accessTokenInMemory}`);
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers,
        credentials: 'include',
      });
    } finally {
      accessTokenInMemory = null;
    }
  }

  async getResumenMetricas(fechaInicio?: string, fechaFin?: string, todo = false): Promise<ResumenMetricas> {
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
    return await res.json();
  }

  async getMetricasColas(): Promise<MetricasCola> {
    const res = await authFetch(`${API_BASE_URL}/metricas/colas`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error consultando el estado de las colas'));
    }
    return await res.json();
  }

  async getMecanicos(): Promise<Mecanico[]> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error consultando mecánicos en PostgreSQL'));
    }
    return await res.json();
  }

  async registrarMecanico(data: MecanicoCreateDTO): Promise<Mecanico> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo registrar el mecánico en PostgreSQL'));
    }
    return await res.json();
  }

  async actualizarMecanico(id: string, data: MecanicoUpdateDTO): Promise<MecanicoResponseDTO> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo actualizar el perfil del mecánico'));
    }
    return await res.json();
  }

  async toggleActivarMecanico(id: string): Promise<Mecanico> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/activar`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo actualizar el estado del mecánico'));
    }
    return await res.json();
  }

  async toggleBloquearMecanico(id: string): Promise<Mecanico> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/bloquear`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo bloquear el mecánico'));
    }
    return await res.json();
  }

  async revocarAccesoMecanico(id: string): Promise<{ mensaje: string }> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/revocar-acceso`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo revocar el acceso técnico del mecánico'));
    }
    return await res.json();
  }

  async eliminarMecanico(id: string): Promise<{ mensaje: string }> {
    return this.revocarAccesoMecanico(id);
  }

  async cambiarRolMecanico(id: string, nuevo_rol: MecanicoRol, password?: string): Promise<Mecanico> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/rol`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ nuevo_rol, password }),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo cambiar el rol del mecánico'));
    }
    return await res.json();
  }

  async getDiagnosticos(params?: {
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
    const items = await res.json() as Diagnostico[];
    const totalHeader = Number(res.headers.get('X-Total-Count'));
    return {
      items,
      total: Number.isFinite(totalHeader) ? totalHeader : items.length,
    };
  }

  // ==========================================
  // CLIENTES Y SOLICITUDES DE ACCESO
  // ==========================================

  async getClientes(busqueda?: string): Promise<Cliente[]> {
    const url = new URL(`${API_BASE_URL}/clientes`);
    if (busqueda) {
      url.searchParams.append('busqueda', busqueda);
    }
    const res = await authFetch(url.toString(), {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error consultando clientes en PostgreSQL'));
    }
    return await res.json();
  }

  async toggleBloquearCliente(id: string): Promise<{ mensaje: string; bloqueado: boolean }> {
    const res = await authFetch(`${API_BASE_URL}/clientes/${id}/bloquear`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo actualizar el estado del cliente'));
    }
    return await res.json();
  }

  async getSolicitudesAcceso(estado?: string): Promise<SolicitudAcceso[]> {
    const url = new URL(`${API_BASE_URL}/clientes/solicitudes/listar`);
    if (estado) {
      url.searchParams.append('estado', estado);
    }
    const res = await authFetch(url.toString(), {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error consultando solicitudes de acceso'));
    }
    return await res.json();
  }

  async aprobarSolicitudAcceso(id: string): Promise<AprobarSolicitudResponseDTO> {
    const res = await authFetch(`${API_BASE_URL}/clientes/solicitudes/${id}/aprobar`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo aprobar la solicitud'));
    }
    return await res.json();
  }

  async rechazarSolicitudAcceso(id: string, motivo?: string): Promise<{ mensaje: string }> {
    const res = await authFetch(`${API_BASE_URL}/clientes/solicitudes/${id}/rechazar`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ motivo }),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo rechazar la solicitud'));
    }
    return await res.json();
  }

  async getHealthReady(): Promise<{
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

  async getTrabajosFallidos(limite: number = 20): Promise<Array<{ id: string; tipo: string; payload: Record<string, unknown>; error?: string; reintentos: number; creado_en: string }>> {
    const res = await authFetch(`${API_BASE_URL}/metricas/trabajos/fallidos?limite=${limite}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      return [];
    }
    return await res.json();
  }

  async reintentarTrabajoFallido(trabajoId: string): Promise<{ status: string; trabajo_id: string }> {
    const res = await authFetch(`${API_BASE_URL}/metricas/trabajos/${trabajoId}/reintentar`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error al reintentar trabajo fallido'));
    }
    return await res.json();
  }

  // ==========================================
  // VALIDACIÓN REAL DE TALLER & TRACKER TESIS
  // ==========================================

  async getCasosValidacion(params?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    fase?: string;
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
    return await res.json();
  }

  async getMetricasValidacion(periodo: { fecha_desde?: string; fecha_hasta?: string } = {}): Promise<MetricasValidacionDTO> {
    const url = new URL(`${API_BASE_URL}/validacion-taller/metricas`);
    for (const [key, value] of Object.entries(periodo)) if (value) url.searchParams.set(key, value);
    const res = await authFetch(url.toString(), {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error al obtener métricas de validación'));
    }
    return await res.json();
  }

  async crearCasoValidacion(dto: CrearCasoValidacionDTO): Promise<CasoValidacionDTO> {
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
    return await res.json();
  }

  getExportarTrackerCsvUrl(): string {
    return `${API_BASE_URL}/validacion-taller/exportar-csv`;
  }

  async descargarValidacionCsv(periodo: { fecha_desde?: string; fecha_hasta?: string }) {
    const url = new URL(this.getExportarTrackerCsvUrl());
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
}

export const apiService = new ApiService();
