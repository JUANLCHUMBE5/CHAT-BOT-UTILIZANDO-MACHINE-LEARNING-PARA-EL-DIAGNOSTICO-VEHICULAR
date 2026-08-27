import type {
  ActualizarEstadoDiagnosticoDTO,
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

function readStoredSession(): UsuarioSesion | null {
  try {
    const raw = localStorage.getItem('carbot_session');
    return raw ? JSON.parse(raw) as UsuarioSesion : null;
  } catch {
    return null;
  }
}

function notifyExpiredSession(): void {
  localStorage.removeItem('carbot_session');
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

async function renewAccessToken(): Promise<string> {
  if (refreshInProgress) return refreshInProgress;

  refreshInProgress = (async () => {
    const session = readStoredSession();
    if (!session?.refreshToken) throw new Error('La sesión no dispone de renovación automática.');

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: session.refreshToken }),
    });
    if (!response.ok) throw new Error('No se pudo renovar la sesión.');

    const tokens = await response.json() as TokenResponseDTO;
    const updatedSession: UsuarioSesion = {
      ...session,
      token: tokens.access_token,
      refreshToken: tokens.refresh_token,
    };
    localStorage.setItem('carbot_session', JSON.stringify(updatedSession));
    window.dispatchEvent(new CustomEvent<UsuarioSesion>(SESSION_UPDATED_EVENT, { detail: updatedSession }));
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
    const token = accessToken || readStoredSession()?.token;
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return fetch(input, { ...init, headers });
  };

  const response = await execute();
  if (response.status !== 401) return response;

  const renewedToken = await renewAccessToken();
  return execute(renewedToken);
}

export function getAuthHeaders(): Record<string, string> {
  const sessionStr = localStorage.getItem('carbot_session');
  if (sessionStr) {
    try {
      const session: UsuarioSesion = JSON.parse(sessionStr);
      if (session?.token) {
        return {
          'Authorization': `Bearer ${session.token}`,
          'Content-Type': 'application/json',
        };
      }
    } catch {
      // fallback
    }
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
  async login(payload: LoginRequestDTO): Promise<TokenResponseDTO> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Credenciales inválidas'));
    }
    return await res.json();
  }

  async cambiarPassword(
    token: string,
    passwordActual: string,
    passwordNuevo: string,
  ): Promise<{ mensaje: string; access_token: string; refresh_token: string }> {
    const res = await fetch(`${API_BASE_URL}/auth/cambiar-password`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        password_actual: passwordActual,
        password_nuevo: passwordNuevo,
      }),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo cambiar la contraseña'));
    }
    return await res.json();
  }

  async getResumenMetricas(fechaInicio?: string, fechaFin?: string): Promise<ResumenMetricas> {
    const url = new URL(`${API_BASE_URL}/metricas/resumen`);
    if (fechaInicio) url.searchParams.append('fecha_inicio', fechaInicio);
    if (fechaFin) url.searchParams.append('fecha_fin', fechaFin);

    const res = await authFetch(url.toString(), {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error consultando métricas en PostgreSQL'));
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

  async eliminarMecanico(id: string): Promise<{ mensaje: string }> {
    const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/revocar-acceso`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo regresar el usuario a cliente'));
    }
    return await res.json();
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
  }): Promise<Diagnostico[]> {
    const url = new URL(`${API_BASE_URL}/diagnostico/historial`);
    if (params) {
      if (params.busqueda) url.searchParams.append('busqueda', params.busqueda);
      if (params.estado) url.searchParams.append('estado', params.estado);
      if (params.modo) url.searchParams.append('modo', params.modo);
      if (params.mecanico_id) url.searchParams.append('mecanico_id', params.mecanico_id);
      if (params.limite !== undefined) url.searchParams.append('limite', params.limite.toString());
      if (params.offset !== undefined) url.searchParams.append('offset', params.offset.toString());
    }

    const res = await authFetch(url.toString(), {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error consultando diagnósticos en PostgreSQL'));
    }
    return await res.json();
  }

  async actualizarEstadoDiagnostico(
    dto: ActualizarEstadoDiagnosticoDTO
  ): Promise<{ mensaje: string }> {
    const res = await authFetch(`${API_BASE_URL}/diagnostico/${dto.diagnostico_id}/confirmar`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        nuevo_estado: dto.nuevo_estado,
        notas_mecanico: dto.notas_mecanico,
      }),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'No se pudo confirmar el diagnóstico en PostgreSQL'));
    }
    return await res.json();
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

  // ==========================================
  // VALIDACIÓN REAL DE TALLER & TRACKER TESIS
  // ==========================================

  async getCasosValidacion(params?: {
    fase?: string;
    marca?: string;
    acierto?: number;
    busqueda?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; skip: number; limit: number; casos: CasoValidacionDTO[] }> {
    const url = new URL(`${API_BASE_URL}/validacion-taller`);
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

  async getMetricasValidacion(): Promise<MetricasValidacionDTO> {
    const res = await authFetch(`${API_BASE_URL}/validacion-taller/metricas`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error al obtener métricas de validación'));
    }
    return await res.json();
  }

  async crearCasoValidacion(dto: CrearCasoValidacionDTO): Promise<CasoValidacionDTO> {
    const res = await authFetch(`${API_BASE_URL}/validacion-taller`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dto),
    });
    if (!res.ok) {
      throw new Error(await extractErrorMessage(res, 'Error al registrar caso de validación'));
    }
    return await res.json();
  }

  getExportarTrackerCsvUrl(): string {
    return `${API_BASE_URL}/validacion-taller/exportar-csv`;
  }
}

export const apiService = new ApiService();
