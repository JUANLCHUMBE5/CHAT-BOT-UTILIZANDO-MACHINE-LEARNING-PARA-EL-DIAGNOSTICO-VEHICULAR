import type { TokenResponseDTO, UsuarioSesion } from '../../types';

const API_ORIGIN_OR_BASE = ((import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api/v1').replace(/\/$/, '');
export const API_BASE_URL = API_ORIGIN_OR_BASE.endsWith('/api/v1')
  ? API_ORIGIN_OR_BASE
  : `${API_ORIGIN_OR_BASE}/api/v1`;

export const SESSION_UPDATED_EVENT = 'carbot:session-updated';
export const SESSION_EXPIRED_EVENT = 'carbot:session-expired';

let refreshInProgress: Promise<string> | null = null;
let accessTokenInMemory: string | null = null;

export function getAccessTokenInMemory(): string | null {
  return accessTokenInMemory;
}

export function setAccessTokenInMemory(token: string | null): void {
  accessTokenInMemory = token;
}

export function readStoredSession(): UsuarioSesion | null {
  try {
    const raw = localStorage.getItem('carbot_session');
    return raw ? (JSON.parse(raw) as UsuarioSesion) : null;
  } catch {
    return null;
  }
}

export function notifyExpiredSession(): void {
  accessTokenInMemory = null;
  localStorage.removeItem('carbot_session');
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

export async function renewAccessToken(): Promise<string> {
  if (refreshInProgress) return refreshInProgress;

  refreshInProgress = (async () => {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        notifyExpiredSession();
      }
      throw new Error(`Error ${response.status}: No se pudo renovar la sesión.`);
    }

    const tokens = (await response.json()) as TokenResponseDTO;
    accessTokenInMemory = tokens.access_token;
    const session = readStoredSession();
    if (session) {
      window.dispatchEvent(new CustomEvent<UsuarioSesion>(SESSION_UPDATED_EVENT, { detail: session }));
    }
    return tokens.access_token;
  })().finally(() => {
    refreshInProgress = null;
  });

  return refreshInProgress;
}

export async function authFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
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

export async function extractErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const errorData = await res.json();
    if (typeof errorData?.detail === 'string') return errorData.detail;
    if (Array.isArray(errorData?.detail)) {
      return errorData.detail
        .map((e: unknown) =>
          typeof e === 'object' && e !== null && 'msg' in e ? String((e as { msg: unknown }).msg) : String(e),
        )
        .join(', ');
    }
    if (typeof errorData?.message === 'string') return errorData.message;
    return fallback;
  } catch {
    return fallback;
  }
}
